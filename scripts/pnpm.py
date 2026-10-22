"""CLI local de pnpm verificado; no descarga herramientas ni usa el perfil."""

from __future__ import annotations

import base64
import json
import os
import stat
import subprocess
import sys
import tarfile
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
manager = __import__("fetch_web_tools")
CACHE = ".cache/web-runtime"
E2E_CONTROL_ENV = {"E2E_ISOLATED", "E2E_RECOVERY", "MOCK_STAGE_DELAY_MS"}
COMMANDS = {
    "install",
    "fetch",
    "test",
    "typecheck",
    "gen",
    "build",
    "lint",
    "dev",
    "run",
    "exec",
}


def validate_args(argv: list[str]) -> list[str]:
    """No permite cambiar gestor, configuración ni raíz desde el CLI."""
    if argv in (["--version"], ["-v"]):
        return argv
    position = 0
    if argv[:1] == ["--filter"]:
        if len(argv) < 3 or argv[1] not in {"web", "./apps/web"}:
            raise ValueError("Filtro no autorizado: usa web o ./apps/web")
        position = 2
    if position >= len(argv) or argv[position] not in COMMANDS:
        raise ValueError("Comando no autorizado en el entrypoint local")
    command = argv[position]
    for arg in argv[position + 1 :]:
        if arg == "--" and command not in {"install", "fetch"}:
            break  # A partir de aquí son argumentos del script, no opciones de pnpm.
        option = arg.split("=", 1)[0].lower()
        if (
            option.startswith(
                (
                    "--config",
                    "--store",
                    "--cache",
                    "--state",
                    "--userconfig",
                    "--global",
                    "--dir",
                    "--prefix",
                    "--lockfile",
                    "--modules",
                    "--virtual-store",
                    "--use-node",
                    "--node",
                    "--manage",
                    "--package-manager",
                    "--registry",
                    "--ignore",
                    "--no-ignore",
                    "--no-frozen",
                    "--resolution",
                    "--workspace",
                )
            )
            or option in {"-c", "-g", "--cwd", "--offline-dir", "--unsafe-perm"}
            or "\x00" in arg
        ) and arg != "--ignore-scripts":
            raise ValueError("Opción de configuración no autorizada")
        if (
            arg.startswith("-")
            and command not in {"install", "fetch"}
            and option
            not in {"--noemit", "--pretty", "--run", "--coverage", "--watch", "--help"}
        ):
            raise ValueError(
                "Opción no revisada: transporta argumentos del script después de --"
            )
    if command in {"install", "fetch"}:
        allowed = {
            "--frozen-lockfile",
            "--ignore-scripts",
            "--offline",
            "--prefer-offline",
            "--prod",
            "--dev",
            "--reporter=append-only",
        }
        if any(arg not in allowed for arg in argv[position + 1 :]):
            raise ValueError(
                "Instalación sólo congelada, sin paquetes ni opciones nuevas"
            )
        return (
            argv[: position + 1]
            + ["--frozen-lockfile", "--ignore-scripts"]
            + [
                arg
                for arg in argv[position + 1 :]
                if arg not in {"--frozen-lockfile", "--ignore-scripts"}
            ]
        )
    if command == "run" and (
        len(argv) <= position + 1
        or argv[position + 1]
        not in {"test", "typecheck", "gen", "build", "lint", "dev"}
    ):
        raise ValueError("Script no autorizado")
    if command == "exec" and (
        len(argv) <= position + 1
        or argv[position + 1] not in {"tsc", "vitest", "playwright"}
    ):
        raise ValueError("Ejecutable no autorizado: sólo tsc, vitest y playwright")
    return argv


def verified_tools(root: Path) -> dict:
    if os.name != "nt":
        raise ValueError("Linux no soportado: falta un pin de Node Linux verificado")
    archives = root / ".cache/fetch"
    if not all(
        (archives / ("web-pinned-" + pin["asset"])).is_file()
        for pin in manager.PINS.values()
    ):
        # Caché revisada previa, sólo lectura; prepare(check=True) no descarga ni extrae.
        return manager.prepare(
            root, root / ".cache/dev-cycle/m1/t08-web-toolchain-inventory", check=True
        )
    return manager.prepare(root, None, check=True)


def owned_file(root: Path, path: Path, content: bytes) -> Path:
    """Crea sólo archivos nuevos; conserva y rechaza cualquier destino alterado."""
    path = manager.safe_path(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or path.read_bytes() != content
        ):
            raise ValueError("Archivo privado alterado; no sobrescribir")
    else:
        with path.open("xb") as stream:
            stream.write(content)
    return path


def _launcher_identity(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        getattr(info, "st_file_attributes", 0),
        getattr(info, "st_reparse_tag", 0),
    )


def _validate_launcher(root: Path, path: Path, content: bytes, identity=None):
    manager.safe_path(path, root)
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or (identity is not None and _launcher_identity(before) != identity)
        or path.read_bytes() != content
    ):
        raise ValueError("Archivo privado alterado; no sobrescribir")
    manager.safe_path(path, root)
    after = path.lstat()
    if _launcher_identity(after) != _launcher_identity(before) or after.st_nlink != 1:
        raise ValueError("Launcher cambiado durante validación")


def _write_launcher(root: Path, path: Path, content: bytes) -> Path:
    """Publica bytes completos, sin reemplazo: rename tiene este contrato en Windows."""
    if os.name != "nt":
        raise ValueError("Linux no soportado: publicación sin reemplazo Windows")
    path = manager.safe_path(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        _validate_launcher(root, path, content)
        return path
    parents = {
        parent: _launcher_identity(parent.lstat())
        for parent in (path.parent, *path.parent.parents)
        if parent.is_relative_to(root)
    }

    def check_parents():
        manager.safe_path(path.parent, root)
        if any(
            _launcher_identity(p.lstat()) != identity for p, identity in parents.items()
        ):
            raise ValueError("Directorio del launcher cambiado")

    temporary = manager.safe_path(
        path.with_name(".pnpm-" + uuid.uuid4().hex + ".tmp"), root
    )
    identity = None
    try:
        with temporary.open("xb") as stream:
            identity = _launcher_identity(os.fstat(stream.fileno()))
            stream.write(content)
        check_parents()
        _validate_launcher(root, temporary, content, identity)
        try:
            # En Windows falla si otro creador ganó; nunca usar replace/POSIX rename.
            os.rename(temporary, path)
        except FileExistsError:
            # La excepción no acredita legitimidad: comprobar tipo, links y bytes.
            check_parents()
            _validate_launcher(root, path, content)
        else:
            identity = None  # Ya no hay temporal propio que retirar.
        check_parents()
        _validate_launcher(root, path, content)
        return path
    finally:
        if identity is not None:
            check_parents()
            manager.safe_path(temporary, root)
            info = temporary.lstat()
            if _launcher_identity(info) != identity or info.st_nlink != 1:
                raise ValueError("Temporal cambiado; no eliminar")
            temporary.unlink()


def native_cache(root: Path, path: Path) -> Path:
    """Refuse aliases before SWC can load or materialize native executable bytes."""
    path = manager.safe_path(path, root)
    path.mkdir(parents=True, exist_ok=True)
    for entry in path.rglob("*"):
        manager.safe_path(entry, root)
        info = entry.lstat()
        if not stat.S_ISDIR(info.st_mode) and (
            not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
        ):
            raise ValueError("Entrada de caché nativa insegura")
    return path


def environment(root: Path, tools: dict) -> dict:
    # El producto nunca escribe en los runtimes sellados de las pruebas.
    base = manager.safe_path(root / CACHE, root)
    base.mkdir(parents=True, exist_ok=True)
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE"}
        or key.upper() in E2E_CONTROL_ENV
    }
    system = Path(env.get("SYSTEMROOT", "C:/Windows"))
    env["COMSPEC"] = str(system / "System32/cmd.exe")
    env["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
    locations = {
        "PNPM_HOME": "pnpm-home",
        "npm_config_store_dir": "store",
        "npm_config_cache": "cache",
        "npm_config_cache_dir": "cache",
        "npm_config_state_dir": "state",
        "npm_config_global_dir": "global",
        "XDG_CACHE_HOME": "xdg-cache",
        "XDG_CONFIG_HOME": "xdg-config",
        "XDG_DATA_HOME": "xdg-data",
        "XDG_STATE_HOME": "xdg-state",
        "TEMP": "temp",
        "TMP": "temp",
    }
    for key, relative in locations.items():
        path = manager.safe_path(base / relative, root)
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    # El carrier oficial Windows resuelve también el fallback antes de usar el root.
    # No heredar perfiles ni overrides de bindings del proceso llamador.
    env["LOCALAPPDATA"] = str(native_cache(root, base / "local-appdata"))
    env["SWC_NATIVE_BINDING_CACHE"] = str(native_cache(root, base / "swc-native"))
    settings = {
        "manage-package-manager-versions": "false",
        "package-manager-strict": "true",
        "package-manager-strict-version": "true",
        "engine-strict": "true",
    }
    config = "".join(f"{key}={value}\n" for key, value in settings.items()).encode()
    for key, filename in (
        ("npm_config_userconfig", "user.npmrc"),
        ("npm_config_globalconfig", "global.npmrc"),
    ):
        env[key] = str(owned_file(root, base / filename, config))
    env.update(
        {
            "npm_config_" + key.replace("-", "_"): value
            for key, value in settings.items()
        }
    )
    # %~dp0 evita interpolar la raíz (espacios/metacaracteres) como código cmd.
    # Cada llamada anidada entra por Python aislado y verifica de nuevo todo.
    launcher = _write_launcher(
        root,
        base / "bin/pnpm.cmd",
        b"@echo off\r\nsetlocal DisableDelayedExpansion\r\n"
        b'"%~dp0..\\..\\..\\.venv\\Scripts\\python.exe" -I '
        b'"%~dp0..\\..\\..\\scripts\\pnpm.py" %*\r\n'
        b"exit /b %errorlevel%\r\n",
    )
    env["PATH"] = os.pathsep.join((str(launcher.parent), str(tools["node"]["dest"])))
    env["CI"] = "true"
    env["npm_config_ignore_scripts"] = "true"
    env["npm_config_verify_store_integrity"] = "true"
    env["npm_config_registry"] = "https://registry.npmjs.org/"
    # Node Windows no encuentra scopes package.json largos; pnpm 9 admite este límite.
    env["npm_config_virtual_store_dir_max_length"] = "40"
    env["NO_UPDATE_NOTIFIER"] = "1"
    env["npm_config_update_notifier"] = "false"
    home = manager.safe_path(base / "home", root)
    home.mkdir(exist_ok=True)
    env["HOME"] = env["USERPROFILE"] = str(home)
    return env


def execute(argv: list[str], root: Path) -> int:
    args = validate_args(argv)
    for relative in (
        ".npmrc",
        ".pnpmfile.cjs",
        "pnpmfile.cjs",
        "apps/web/.npmrc",
        "apps/web/.pnpmfile.cjs",
    ):
        if manager.safe_path(root / relative, root).exists():
            raise ValueError("Configuración de proyecto no revisada; no ejecutar pnpm")
    tools = verified_tools(root)
    node = manager.safe_path(tools["node"]["dest"] / "node.exe", root)
    pnpm = manager.safe_path(tools["pnpm"]["dest"] / "bin/pnpm.cjs", root)
    env = environment(root, tools)
    return subprocess.run(
        [str(node), str(pnpm), *args], cwd=root, env=env, shell=False, check=False
    ).returncode


def main(argv=None) -> int:
    try:
        args = list(sys.argv[1:] if argv is None else argv)
        if args[:1] == ["--studio-argv-base64"]:
            if len(args) != 2:
                raise ValueError("Transporte de argumentos inválido")
            args = json.loads(base64.b64decode(args[1], validate=True).decode("utf-8"))
            if not isinstance(args, list) or any(
                not isinstance(arg, str) for arg in args
            ):
                raise ValueError("Se requiere una lista de cadenas")
        return execute(args, ROOT)
    except (
        ValueError,
        OSError,
        KeyError,
        tarfile.TarError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
    ) as exc:
        print(f"pnpm NO LISTO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
