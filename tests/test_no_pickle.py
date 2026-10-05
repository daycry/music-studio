"""Guardia AST contra deserialización insegura; sin ejecutar código inspeccionado."""

import ast
from pathlib import Path

import pytest


def unsafe_calls(source):
    tree = ast.parse(source)
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                aliases[name.asname or name.name] = name.name
        elif isinstance(node, ast.ImportFrom):
            for name in node.names:
                aliases[name.asname or name.name] = f"{node.module}.{name.name}"

    def qualified(node):
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return f"{qualified(node.value)}.{node.attr}"
        return ""

    banned = {"torch.load", "pickle.load", "pickle.loads", "pickle.Unpickler"}
    found = []
    for node in ast.walk(tree):
        targets = (
            [node.func]
            if isinstance(node, ast.Call)
            else node.bases
            if isinstance(node, ast.ClassDef)
            else []
        )
        for target in targets:
            name = qualified(target)
            if name in banned:
                found.append((node.lineno, name))
    return found


@pytest.mark.parametrize(
    "source",
    [
        "import torch as t; t.load('x')",
        "from torch import load as read; read('x')",
        "import pickle as p; p.loads(b'x')",
        "from pickle import load; load('x')",
        "import pickle; pickle.Unpickler('x')",
        "from pickle import Unpickler as U\nclass Unsafe(U): pass",
        "import pickle\nclass Unsafe(pickle.Unpickler): pass",
    ],
)
def test_detects_aliases_and_unpicklers(source):
    assert unsafe_calls(source), "No detecta llamada/clase pickle o torch.load"


def test_no_pickle():
    root = Path(__file__).resolve().parents[1]
    allowlist = {}
    for line in (
        (root / "tests/no_pickle_allowlist.txt")
        .read_text(encoding="utf-8-sig")
        .splitlines()
    ):
        if line.strip() and not line.startswith("#"):
            path, reason = line.split("|", 1)
            assert reason.strip()
            allowlist[path.strip()] = reason.strip()
    violations = []
    for folder in ("apps", "packages"):
        for path in (root / folder).rglob("*.py"):
            relative = path.relative_to(root).as_posix()
            for lineno, name in unsafe_calls(path.read_text(encoding="utf-8-sig")):
                if relative not in allowlist or name != "pickle.Unpickler":
                    violations.append(f"{relative}:{lineno}: {name}")
    assert not violations, "\n".join(violations)
