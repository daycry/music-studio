"""Exportación determinista de contratos code-first, sin arranque runtime."""

import argparse
import json
from pathlib import Path

from app.main import create_app
from app.settings import ContractSettings
from engine_contract import contract_schema


def server_schema():
    settings = ContractSettings(engine_token="contract-export-neutral-token")
    return create_app(settings).openapi()


def main(argv=None, *, output_dir=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    # Resolve the default destination at call time.  Besides keeping the CLI
    # relocatable, this lets the contract check run against an isolated
    # checkout in tests instead of the repository that happened to be on
    # ``sys.path`` when this module was imported.
    directory = (
        Path(output_dir)
        if output_dir is not None
        else Path(__file__).resolve().parents[1] / "packages/contracts"
    )
    stale = False
    for name, schema in [
        ("engine-v1.json", contract_schema()),
        ("openapi.json", server_schema()),
    ]:
        path = directory / name
        content = (
            json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        # El engine preexistente conserva sus bytes CRLF al comprobar su JSON.
        matches = path.exists() and (
            path.read_text(encoding="utf-8") == content
            if name == "engine-v1.json"
            else path.read_bytes() == content.encode("utf-8")
        )
        if args.check:
            print(f"{name} {'up to date' if matches else 'out of date'}")
            stale = stale or not matches
        elif not matches:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
    return int(stale)


if __name__ == "__main__":
    raise SystemExit(main())
