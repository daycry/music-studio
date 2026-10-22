"""Valida manifiestos v1 y hashes, sin importar pesos ni engines."""

import argparse
import json
import sys
from pathlib import Path

from audio_post import verify_manifest


def data_relative(payload):
    outputs = payload.get("outputs") if isinstance(payload, dict) else None
    return isinstance(outputs, list) and any(
        isinstance(o, dict) and str(o.get("path", "")).startswith("data/")
        for o in outputs
    )


def base_for(path, payload, data_dir):
    """Base y contexto privado; `data_dir` es el directorio de datos en sí (el que el server monta)."""
    if not data_relative(payload):
        return path.parent, None, payload
    if data_dir is not None:
        # Vista privada como la del server: sin prefijo `data/`; el manifiesto en disco no se toca.
        outputs = [
            {**o, "path": o["path"][len("data/") :]}
            if isinstance(o, dict) and str(o.get("path", "")).startswith("data/")
            else o
            for o in payload["outputs"]
        ]
        return Path(data_dir), Path(data_dir), {**payload, "outputs": outputs}
    root = next((p for p in path.absolute().parents if (p / "data").is_dir()), None)
    if root is None:
        return path.parent, None, payload
    return root, root / "data", payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="directorio de datos en sí (el que el server monta como /data); "
        "para manifiestos con rutas data/... cuando no cuelga de un directorio data/",
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
