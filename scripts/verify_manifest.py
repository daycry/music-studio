"""Valida manifiestos v1 y hashes, sin importar pesos ni engines."""

import argparse
import json
import os
import sys
from pathlib import Path

from audio_post import verify_manifest
from audio_post.manifest import _validate


def _norm(value):
    return os.path.normcase(str(value))


def _split(value):
    """Partes de `data/<rel>` como string crudo: sin vacíos, `.`, `..` ni barra final."""
    parts = value[len("data/") :].split("/")
    if len(parts) < 2 or any(part in ("", ".", "..") for part in parts):
        raise ValueError("OUTPUT_OUTSIDE_TAKE: ruta de salida data/ no canónica")
    return parts


def base_for(path, payload, data_dir):
    """Base, contexto privado y vista a verificar.

    Con salidas `data/<rel>` la raíz de datos se deriva del propio manifiesto: la
    carpeta del manifiesto debe ser exactamente `<datos>/dirname(<rel>)`. Nunca se
    buscan ancestros `data/` ni se valida contra ficheros ajenos al manifiesto.
    """
    _validate(payload)  # esquema v1 sobre el manifiesto ORIGINAL, antes de la vista
    paths = [o["path"] for o in payload["outputs"]]
    flagged = [v.startswith("data/") for v in paths]
    if not any(flagged):
        return path.parent, None, payload
    if not all(flagged):
        raise ValueError(
            "OUTPUT_MIXED_PATHS: salidas data/ y relativas en un manifiesto"
        )
    split = [_split(v) for v in paths]
    if len({tuple(parts[:-1]) for parts in split}) != 1:
        raise ValueError("OUTPUT_OUTSIDE_TAKE: salidas en carpetas distintas")
    parent = split[0][:-1]
    folder = path.absolute().parent
    tail = folder.parts[len(folder.parts) - len(parent) :]
    if [_norm(x) for x in tail] != [_norm(x) for x in parent]:
        raise ValueError(
            "OUTPUT_OUTSIDE_TAKE: las salidas no están en la carpeta del manifiesto"
        )
    derived = folder
    for _ in parent:
        derived = derived.parent
    if data_dir is not None and _norm(Path(data_dir).resolve()) != _norm(
        derived.resolve()
    ):
        raise ValueError(
            "OUTPUT_OUTSIDE_TAKE: --data-dir no contiene la carpeta del manifiesto"
        )
    # Vista privada como la del server: nombres base junto al manifiesto.
    view = {
        **payload,
        "outputs": [
            {**o, "path": parts[-1]} for o, parts in zip(payload["outputs"], split)
        ],
    }
    return folder, derived, view


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="directorio de datos en sí (el que el server monta como /data); opcional: se deriva del manifiesto y, si se da, debe coincidir",
    )
    args = parser.parse_args(argv)
    directory = args.path.is_dir()
    paths = sorted(args.path.rglob("*.json")) if directory else [args.path]
    if not paths or not args.path.exists():
        print("MANIFEST_MISSING", file=sys.stderr)
        return 1
    failed = False
    checked = 0
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            named_manifest = "manifest" in path.stem.lower()
            if (
                directory
                and not named_manifest
                and not (
                    isinstance(payload, dict)
                    and {"manifest_version", "commercial_use", "pipeline", "outputs"}
                    & payload.keys()
                )
            ):
                continue
            checked += 1
            base, context, view = base_for(path, payload, args.data_dir)
            verify_manifest(view, base, private_context_root=context)
        except (ValueError, OSError, TypeError, KeyError) as error:
            print(f"{path.name}: {error}", file=sys.stderr)
            failed = True
    if failed:
        return 1
    if not checked:
        print("MANIFEST_MISSING", file=sys.stderr)
        return 1
    print(f"all valid ({checked} manifests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
