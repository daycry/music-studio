"""Parche mínimo del loader fijado; sin pickle ni escritura en checkpoints.

El método upstream usa el tensor convertido por packages/weights con clave
`tensor`. Se sustituye exclusivamente esa lectura y se conserva la colocación
de dispositivo/dtype. Si el upstream cambia el patrón, falla cerrado.
"""

import hashlib
import inspect
import textwrap
from pathlib import Path

from engine_common import EngineError

LOADER_SHA256 = "22b41692bcb73fead4c831d16eaef3dda56cc995577f2353d763445dae7362e1"


def patch_loader_source(source):
    old = "torch.load(silence_latent_path, weights_only=True)"
    if source.count(old) != 1 or source.count('"silence_latent.pt"') != 1:
        raise ValueError("El loader ACE-Step fijado ha cambiado")
    result = source.replace(
        '"silence_latent.pt"', '"silence_latent.safetensors"'
    ).replace(old, 'safe_load_file(silence_latent_path)["tensor"]')
    if "torch.load(" in result:
        raise ValueError("Lectura pickle upstream adicional no autorizada")
    return result


def verify_components(checkpoints, components):
    root = Path(checkpoints).resolve()
    for component in components:
        directory = root / component["dest_subdir"]
        allowed = set()
        for file in component["files"]:
            safe = file.get("converted", file)
            name = safe.get("dest", file["path"])
            allowed.add(name)
            if file["format"] == "pickle":
                # El original puede conservarse como entrada del conversor,
                # pero el loader sólo ve su safetensors verificado.
                allowed.add(file["path"])
                if "converted" not in file:
                    raise EngineError(
                        "WEIGHTS_MISMATCH", "Peso pickle sin conversión segura"
                    )
            target = directory / name
            if (
                target.is_symlink()
                or not target.resolve().is_relative_to(root)
                or not target.is_file()
            ):
                raise EngineError(
                    "WEIGHTS_MISMATCH", "Falta componente local verificado"
                )
            if target.stat().st_size != safe["bytes"]:
                raise EngineError(
                    "WEIGHTS_MISMATCH", "Tamaño de componente no coincide"
                )
            with target.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != safe["sha256"]:
                raise EngineError("WEIGHTS_MISMATCH", "Hash de componente no coincide")
        for target in directory.rglob("*"):
            if (
                target.is_file()
                and target.suffix
                in {
                    ".py",
                    ".bin",
                    ".pt",
                    ".pth",
                    ".ckpt",
                    ".safetensors",
                    ".gguf",
                    ".onnx",
                }
                and target.relative_to(directory).as_posix() not in allowed
            ):
                raise EngineError(
                    "WEIGHTS_MISMATCH", "Peso o código adicional fuera del lock"
                )


def install_safe_loader():
    from acestep.core.generation.handler import init_service_loader as module
    from safetensors.torch import load_file

    path = Path(module.__file__)
    if hashlib.sha256(path.read_bytes()).hexdigest() != LOADER_SHA256:
        raise EngineError(
            "WEIGHTS_MISMATCH", "Loader upstream distinto de la revisión auditada"
        )
    method = module.InitServiceLoaderMixin._load_main_model_from_checkpoint
    source = patch_loader_source(textwrap.dedent(inspect.getsource(method)))
    namespace = {**vars(module), "safe_load_file": load_file}
    exec(compile(source, str(path), "exec"), namespace)  # noqa: S102 - fuente fijada por SHA-256 antes de compilar
    module.InitServiceLoaderMixin._load_main_model_from_checkpoint = namespace[
        method.__name__
    ]


def enforce_safe_pretrained(dtype=None):
    """El hijo fuerza lectura local safetensors en los cuatro componentes."""
    from diffusers.models import AutoencoderOobleck
    from transformers import AutoModel, AutoModelForCausalLM

    for cls in (AutoModel, AutoModelForCausalLM, AutoencoderOobleck):
        original = cls.from_pretrained

        dtype_key = "torch_dtype" if cls is AutoencoderOobleck else "dtype"

        def safe_pretrained(*args, _original=original, _dtype_key=dtype_key, **kwargs):
            kwargs["use_safetensors"] = True
            kwargs["local_files_only"] = True
            if dtype is not None:
                kwargs.pop("dtype", None)
                kwargs.pop("torch_dtype", None)
                kwargs[_dtype_key] = dtype
            return _original(*args, **kwargs)

        cls.from_pretrained = safe_pretrained
