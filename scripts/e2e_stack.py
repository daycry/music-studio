"""Stack E2E dedicado: datos privados persistentes y operaciones síncronas.

Seleccionar E2E_PROJECT_NAME, E2E_COMPOSE_FILE, E2E_ENV_FILE y STUDIO_DATA_ROOT, o sus
flags CLI. Nunca utiliza el proyecto Compose implícito del usuario.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MARKER = ".music-studio-e2e.json"


def _validated_cli(value: str | None, names: set[str]) -> str:
    if not value:
        raise ValueError("Docker CLI E2E no disponible")
    path = Path(value)
    if (
        not path.is_absolute()
        or path.name.lower() not in names
        or not path.is_file()
        or not os.access(path, os.X_OK)
        or any(
            entry.is_symlink()
            or getattr(entry.lstat(), "st_file_attributes", 0)
            & stat.FILE_ATTRIBUTE_REPARSE_POINT
            for entry in (path, *path.parents)
        )
    ):
        raise ValueError("Docker CLI E2E no autorizado")
    return str(path)


def docker_cli(candidate: str | None = None) -> str:
    """Resuelve el CLI preinstalado sin delegar en shell ni ampliar PATH."""
    value = (
        candidate
        if candidate is not None
        else (os.environ.get("E2E_DOCKER_CLI") or shutil.which("docker"))
    )
    return _validated_cli(value, {"docker", "docker.exe"})


def compose_cli(candidate: str) -> str:
    return _validated_cli(candidate, {"docker-compose", "docker-compose.exe"})


def local_docker_host(value: str) -> str:
    """Sólo sockets Unix absolutos o named pipes de esta máquina."""
    if isinstance(value, str):
        if re.fullmatch(r"npipe:////\./pipe/[A-Za-z0-9_.-]+", value):
            return value
        match = re.fullmatch(r"unix://(/[A-Za-z0-9_./-]+)", value)
        if match and not match[1].startswith("//"):
            path = PurePosixPath(match[1])
            if path != PurePosixPath("/") and ".." not in path.parts:
                return value
    raise ValueError("Endpoint Docker E2E no local o no autorizado")


def private_path(value: str | Path, *, cache_only: bool) -> Path:
    """Comprueba la ruta original antes de resolver enlaces o junctions."""
    root = ROOT.resolve()
    path = Path(os.path.abspath(ROOT / value))
    boundary = root / ".cache" if cache_only else root
    if path == boundary or not path.is_relative_to(boundary):
        raise ValueError(
            "La ruta E2E debe estar dentro de la carpeta privada del repositorio"
        )
    current = path
    while current != root:
        if current.is_symlink() or current.is_junction():
            raise ValueError("La ruta E2E no admite enlaces ni junctions")
        if (
            current.exists()
            and getattr(current.lstat(), "st_file_attributes", 0)
            & stat.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ValueError("La ruta E2E no admite reparse points")
        current = current.parent
    resolved = path.resolve()
    if not resolved.is_relative_to(boundary):
        raise ValueError("La ruta E2E resuelta sale del repositorio")
    return resolved


class Stack:
    def __init__(
        self,
        project: str,
        compose_file: str | Path,
        data_root: str | Path,
        env_file: str | Path | None = None,
    ):
        if not re.fullmatch(r"music-studio-e2e(?:-[a-z0-9][a-z0-9_-]*)?", project):
            raise ValueError(
                "Se requiere un proyecto dedicado music-studio-e2e[-nombre]"
            )
        self.project = project
        self.compose_file = private_path(compose_file, cache_only=False)
        self.data_root = private_path(data_root, cache_only=True)
        self.env_file = private_path(env_file, cache_only=False) if env_file else None
        self.environment = os.environ.copy()
        self.environment.update(
            COMPOSE_PROJECT_NAME=project,
            E2E_PROJECT_NAME=project,
            E2E_COMPOSE_FILE=str(self.compose_file),
            STUDIO_DATA_ROOT=str(self.data_root),
            E2E_ISOLATED="1",
        )
        if self.env_file:
            self.environment["E2E_ENV_FILE"] = str(self.env_file)

    def run(self, *args: str) -> None:
        if selected := self.environment.get("E2E_COMPOSE_CLI"):
            command = [compose_cli(selected)]
            environment = dict(self.environment)
            environment["DOCKER_HOST"] = local_docker_host(
                environment.get("E2E_DOCKER_HOST", "")
            )
            for key in ("DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
                environment.pop(key, None)
        else:
            command = [docker_cli(), "compose"]
            environment = self.environment
        subprocess.run(
            [
                *command,
                "--project-name",
                self.project,
                "--profile",
                "studio",
                "--file",
                str(self.compose_file),
                *(["--env-file", str(self.env_file)] if self.env_file else []),
                *args,
            ],
            cwd=ROOT,
            check=True,
            env=environment,
        )

    def prepare_data(self) -> None:
        self.data_root = private_path(self.data_root, cache_only=True)
        self.data_root.mkdir(parents=True, exist_ok=True)
        if not any(self.data_root.iterdir()):
            (self.data_root / MARKER).write_text(
                json.dumps({"project": self.project}), encoding="utf-8"
            )

    def reset_data(self) -> None:
        data = private_path(self.data_root, cache_only=True)
        marker = private_path(data / MARKER, cache_only=True)
        try:
            ownership = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError("Falta el marcador de propiedad E2E") from exc
        if ownership != {"project": self.project}:
            raise ValueError("El marcador de propiedad corresponde a otro proyecto")
        # os.walk no sigue enlaces; comprobar cada entrada también impide que
        # rmtree alcance un junction/reparse point anidado en Windows.
        for parent, directories, files in os.walk(data, followlinks=False):
            for name in (*directories, *files):
                private_path(Path(parent) / name, cache_only=True)
        self.run("down")
        private_path(data, cache_only=True)
        shutil.rmtree(data)


def wait_url(url: str, timeout_s: float = 60) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except OSError:
            time.sleep(1)
    raise SystemExit(f"El servicio no responde: {url}")


def seed_isolated_stack(stack: Stack) -> None:
    """Siembra por API exclusivamente el stack E2E seleccionado."""
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "apps" / "server" / "scripts" / "seed_e2e.py"),
            "--base-url",
            "http://127.0.0.1:8000",
            "--output",
            str(private_path(stack.data_root / "e2e-seed.json", cache_only=True)),
        ],
        cwd=ROOT,
        check=True,
        env=stack.environment,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "up",
            "down",
            "restart-server",
            "kill-server",
            "start-server",
            "smoke",
        ),
    )
    parser.add_argument(
        "--project-name",
        default=os.environ.get("E2E_PROJECT_NAME")
        or os.environ.get("COMPOSE_PROJECT_NAME")
        or "music-studio-e2e",
    )
    parser.add_argument(
        "--compose-file",
        default=os.environ.get("E2E_COMPOSE_FILE", "docker-compose.yml"),
    )
    parser.add_argument(
        "--data-root", default=os.environ.get("STUDIO_DATA_ROOT", ".cache/e2e-data")
    )
    parser.add_argument("--env-file", default=os.environ.get("E2E_ENV_FILE"))
    parser.add_argument(
        "--reset-data",
        action="store_true",
        help="Borrar sólo datos E2E marcados; exclusivamente con up",
    )
    args = parser.parse_args()
    stack = Stack(args.project_name, args.compose_file, args.data_root, args.env_file)
    if args.reset_data:
        if args.command != "up":
            parser.error("--reset-data sólo se admite con up")
        stack.reset_data()
    if args.command in ("up", "smoke"):
        stack.prepare_data()
        stack.run("up", "-d", "--build", "web", "server", "engine-mock")
        wait_url("http://127.0.0.1:8000/health")
        wait_url("http://127.0.0.1:3000/create")
        if args.command == "up":
            seed_isolated_stack(stack)
    elif args.command == "down":
        stack.run("down")
    elif args.command == "kill-server":
        stack.run("kill", "--signal", "SIGKILL", "server")
    else:
        stack.run("restart" if args.command == "restart-server" else "start", "server")
        wait_url("http://127.0.0.1:8000/health")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
