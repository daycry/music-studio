"""Valida manifiestos v1 y hashes, sin importar pesos ni engines."""

import argparse
import json
import sys
from pathlib import Path

from audio_post import verify_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
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
            verify_manifest(payload, path.parent)
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
