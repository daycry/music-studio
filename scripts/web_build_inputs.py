"""Contexto selectivo para un futuro instalador Linux, sin ejecutar herramientas.

Las dependencias opacas van a inputs/archives; pnpm conserva sus 901 archivos,
incluido dist/node_modules. Node Windows y cachés del proyecto nunca se copian.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).absolute().parents[1]))

from scripts import fetch_web_dependencies as deps

ROOT = deps.ROOT
REQUIRED = (
    "package.json",
    "pnpm-workspace.yaml",
    "pnpm-lock.yaml",
    "tools/tools.lock.json",
    "tools/web-linux.lock.json",
    deps.LOCK,
    "apps/web/package.json",
    "apps/web/next.config.ts",
    "apps/web/next-env.d.ts",
    "apps/web/tsconfig.json",
    "apps/web/postcss.config.mjs",
    "apps/web/eslint.config.mjs",
    "apps/web/vitest.config.ts",
    "packages/contracts/openapi.json",
)
WEB_DIRS = ("app", "components", "lib", "i18n", "messages", "styles", "public")
SOURCE_EXTENSIONS = {".ts", ".tsx", ".css", ".json"}
PUBLIC_EXTENSIONS = {
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".svg",
    ".ico",
}
FORBIDDEN = {
    "node_modules",
    ".next",
    ".cache",
    "temp",
    "tmp",
    "data",
    "models",
    "__pycache__",
}
MAX_CONTEXT_FILES = 4096


def walk(root: Path, directory: Path) -> list[Path]:
    """Recorre sólo una raíz explícita; nunca sigue enlaces ni junctions."""
    deps.safe_path(root, directory)
    if not directory.is_dir():
        raise deps.InputError("MISSING_INPUT: raíz selectiva ausente")
    result = []
    pending = [directory]
    seen = 0
    while pending:
        current = pending.pop()
        with deps.ancestors(root, current / "unused"):
            for path in sorted(current.iterdir()):
                seen += 1
                if seen > MAX_CONTEXT_FILES:
                    raise deps.InputError("INPUT_LIMIT: contexto excesivo")
                if path.name in FORBIDDEN or path.name.startswith("."):
                    continue
                deps.safe_path(root, path)
                if path.is_dir():
                    pending.append(path)
                else:
                    result.append(path)
    return sorted(result)


def tool_files(root: Path, linux: dict, tools: dict) -> tuple[dict, str]:
    try:
        pin = tools["tools"]["pnpm"]
        if pin["version"] != "9.12.0" or linux["pnpm_version"] != pin["version"]:
            raise ValueError("pnpm pin")
        if pin["dest"] != "tools/pnpm/9.12.0":
            raise ValueError("pnpm destino")
        base = root / pin["dest"]
        receipt_path = base / ".studio-web-origin.json"
        receipt_bytes = deps.read_file(root, receipt_path)
        receipt = json.loads(receipt_bytes)
        if any(receipt["source"].get(key) != value for key, value in pin.items()):
            raise ValueError("pnpm origen")
        files = receipt["files"]
        if len(files) != 901:
            raise ValueError("pnpm cierre901")
        deps.authoritative(
            root, pin["dest"] + "/.studio-web-origin.json", receipt_bytes
        )
        names = set()
        frozen = {receipt_path: deps.metadata(receipt_bytes)}
        for name, row in files.items():
            deps.relative_name(name)
            if name.casefold() in names or name == ".studio-web-origin.json":
                raise ValueError("pnpm alias")
            names.add(name.casefold())
            path = base / name
            deps.verified(deps.read_file(root, path), row)
            frozen[path] = row
        # Inventario completo, incluyendo ficheros ocultos legítimos de pnpm.
        pending, actual, visited = [base], set(), 0
        while pending:
            directory = pending.pop()
            with deps.ancestors(root, directory / "unused"):
                for path in directory.iterdir():
                    visited += 1
                    deps.safe_path(root, path)
                    if path.is_dir():
                        pending.append(path)
                    else:
                        actual.add(path)
                    if visited > MAX_CONTEXT_FILES:
                        raise ValueError("pnpm límite")
        if actual != set(frozen):
            raise ValueError("pnpm inventario ajeno/incompleto")
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, deps.InputError):
            raise
        raise deps.InputError(
            "INVALID_TOOL_RECEIPT: distribución pnpm no verificada"
        ) from exc
    return frozen, pin["dest"]


def collect_inputs(root: Path) -> tuple[dict, dict]:
    lock, lock_frozen = deps.load_lock(root)
    frozen = {root / name: row for name, row in lock_frozen.items()}
    for name in REQUIRED:
        path = root / name
        frozen[path] = deps.metadata(deps.read_file(root, path))
    try:
        linux = json.loads(deps.read_file(root, root / "tools/web-linux.lock.json"))
        tools = json.loads(deps.read_file(root, root / "tools/tools.lock.json"))
        if (
            linux["tools_lock_sha256"]
            != frozen[root / "tools/tools.lock.json"]["sha256"]
        ):
            raise deps.InputError("LOCK_MISMATCH: base/tools")
        image = linux["image_id"]
        if (
            linux["schema_version"] != 1
            or linux["platform"] != "linux/amd64"
            or not re.fullmatch(r"sha256:[a-f0-9]{64}", image)
            or linux["observed_immutable_reference"] != "node@" + image
            or linux["node_version"] != "22.23.3"
            or linux["alpine_version"] != "3.24.2"
            or linux["pnpm_version"] != "9.12.0"
            or not linux["rootfs_layers"]
            or any(
                not re.fullmatch(r"sha256:[a-f0-9]{64}", layer)
                for layer in linux["rootfs_layers"]
            )
        ):
            raise ValueError("identidad Linux")
        package = json.loads(deps.read_file(root, root / "package.json"))
        if package["packageManager"] != "pnpm@" + linux["pnpm_version"]:
            raise deps.InputError("LOCK_MISMATCH: packageManager")
        web = json.loads(deps.read_file(root, root / "apps/web/package.json"))
        pnpm_text = deps.read_file(root, root / "pnpm-lock.yaml").decode("utf-8")
        importer = pnpm_text.split("\n  apps/web:\n", 1)[1].split("\npackages:\n", 1)[0]
        for section in ("dependencies", "devDependencies"):
            for name, version in web[section].items():
                if not re.search(
                    r"^      '?"
                    + re.escape(name)
                    + r"'?:\n        specifier: "
                    + re.escape(version)
                    + r"\n",
                    importer,
                    re.MULTILINE,
                ):
                    raise deps.InputError("LOCK_MISMATCH: manifiesto web/specifier")
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        if isinstance(exc, deps.InputError):
            raise
        raise deps.InputError(
            "INVALID_LINUX_LOCK: identidad/configuración inválida"
        ) from exc
    for name in ("tools/web-linux.lock.json", "tools/tools.lock.json"):
        deps.authoritative(root, name, deps.read_file(root, root / name))
    pnpm_files, pnpm_dest = tool_files(root, linux, tools)
    frozen.update(pnpm_files)
    for name in WEB_DIRS:
        directory = root / "apps/web" / name
        if name == "public" and not directory.exists():
            continue
        for path in walk(root, directory):
            allowed = PUBLIC_EXTENSIONS if name == "public" else SOURCE_EXTENSIONS
            if path.suffix in allowed:
                frozen[path] = deps.metadata(deps.read_file(root, path))
    for path in walk(root, root / "packages/contracts"):
        if path.suffix == ".json":
            frozen[path] = deps.metadata(deps.read_file(root, path))
    archives = deps.check_archives(root, lock)
    frozen.update(archives)
    if len(frozen) > MAX_CONTEXT_FILES:
        raise deps.InputError("INPUT_LIMIT: demasiados archivos de contexto")
    destinations = {}
    for path, row in frozen.items():
        name = path.relative_to(root).as_posix()
        if name.startswith(deps.ARCHIVE_ROOT + "/"):
            name = "inputs/archives/" + path.name
        destinations[path] = (name, row)
    return destinations, {
        "image_id": linux["image_id"],
        "platform": linux["platform"],
        "pnpm_dest": pnpm_dest,
    }


def build_context(root: Path, destination: Path) -> dict:
    root, destination = Path(os.path.abspath(root)), Path(os.path.abspath(destination))
    deps.safe_path(ROOT, root)
    deps.safe_path(root, destination)
    # Salidas propias bajo caché; nunca escribir encima de fuentes/herramientas.
    if (
        not destination.is_relative_to(root / ".cache")
        or destination == root / ".cache"
    ):
        raise deps.InputError("UNSAFE_DESTINATION: contexto sólo en .cache propia")
    if destination.exists():
        raise deps.InputError("DESTINATION_EXISTS: preservar salida existente")
    selected, identity = collect_inputs(root)
    manifest = {
        "schema_version": 1,
        "ready": True,
        "operation": "local_build_inputs",
        "image_validation": "configured_only; Docker runtime unverified",
        "archive_count": 609,
        "pnpm_file_count": 901,
        "linux": identity,
        "files": {},
    }
    with deps.Publication(root, destination) as publication:
        for path, (name, row) in selected.items():
            data = deps.read_file(root, path)
            deps.verified(data, row)
            publication.write(name, data, row.get("executable", False))
            manifest["files"][name] = deps.metadata(data)
        # No inferir ready de JSON del llamador ni de una copia parcial.
        for path, (_, row) in selected.items():
            deps.verified(deps.read_file(root, path), row)
        current, current_identity = collect_inputs(root)
        if current != selected or current_identity != identity:
            raise deps.InputError("INPUT_CHANGED: inventario cambió antes de publicar")
        publication.write(
            "build-inputs.json",
            json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        )
        publication.publish()
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Preparar contexto web local verificado; no ejecuta Docker"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = build_context(args.root, args.output)
    except (deps.InputError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
