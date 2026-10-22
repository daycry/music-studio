"""Valida manifiestos v1 y hashes, sin importar pesos ni engines."""

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

from audio_post import verify_manifest


def _output_paths(payload):
    outputs = payload.get("outputs") if isinstance(payload, dict) else None
    if not isinstance(outputs, list):
        return []
    return [o["path"] for o in outputs if isinstance(o, dict) and "path" in o]


def base_for(path, payload, data_dir):
    """Base, contexto privado y vista a verificar.

    Con salidas `data/<rel>` la raíz de datos se deriva del propio manifiesto: la
    carpeta del manifiesto debe ser exactamente `<datos>/dirname(<rel>)`. Nunca se
    buscan ancestros `data/` ni se valida contra ficheros ajenos al manifiesto.
    """
    paths = _output_paths(payload)
    flagged = [isinstance(v, str) and v.startswith("data/") for v in paths]
    if not any(flagged):
        return path.parent, None, payload
    if not all(flagged):
        raise ValueError(
            "OUTPUT_MIXED_PATHS: salidas data/ y relativas en un manifiesto"
        )
    parents = {PurePosixPath(v[len("data/") :]).parent for v in paths}
    if len(parents) != 1:
        raise ValueError("OUTPUT_OUTSIDE_TAKE: salidas en carpetas distintas")
    parent = parents.pop()
    folder = path.absolute().parent
    if ".." in parent.parts or folder.parts[
        len(folder.parts) - len(parent.parts) :
    ] != (parent.parts):
        raise ValueError(
            "OUTPUT_OUTSIDE_TAKE: las salidas no están en la carpeta del manifiesto"
        )
    derived = folder
    for _ in parent.parts:
        derived = derived.parent
    if data_dir is not None and Path(data_dir).resolve() != derived.resolve():
        raise ValueError(
            "OUTPUT_OUTSIDE_TAKE: --data-dir no contiene la carpeta del manifiesto"
        )
    # Vista privada como la del server: nombres base junto al manifiesto.
    view = {
        **payload,
        "outputs": [
            {**o, "path": PurePosixPath(o["path"]).name} for o in payload["outputs"]
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
        except (ValueError, OSError) as error:
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
