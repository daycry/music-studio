"""Exportación determinista del contrato code-first."""

import argparse
import json
from pathlib import Path

from engine_contract import contract_schema


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "packages/contracts/engine-v1.json"
    content = (
        json.dumps(contract_schema(), indent=2, sort_keys=True, ensure_ascii=False)
        + "\n"
    )
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            print("engine-v1.json out of date")
            return 1
        print("engine-v1.json up to date")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
