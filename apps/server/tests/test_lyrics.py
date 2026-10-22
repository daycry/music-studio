"""Contrato sintético común; no contiene letras privadas."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads(
    (ROOT / "packages/contracts/lyrics-cases.json").read_text(encoding="utf8")
)["cases"]


def parser():
    path = ROOT / "apps/server/app/lyrics.py"
    if not path.exists():
        return lambda text: {
            "version": 1,
            "original": text,
            "sections": [],
            "annotations": [],
            "warnings": [],
        }
    spec = importlib.util.spec_from_file_location("lyrics", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse_lyrics


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_lyrics_contract(case):
    assert parser()(case["input"]) == case["expected"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_lyrics_literal_slices(case):
    result = parser()(case["input"])
    encoded = result["original"].encode("utf-16-le")

    def sliced(span):
        return encoded[span["start"] * 2 : span["end"] * 2].decode("utf-16-le")

    for section in result["sections"]:
        assert sliced(section["aliasRange"]) == section["alias"]
        if section["directions"] is not None:
            assert (
                sliced(section["directions"]["range"]) == section["directions"]["text"]
            )
    for annotation in result["annotations"]:
        assert sliced(annotation["range"]) == annotation["text"]
