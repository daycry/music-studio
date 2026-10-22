"""Arranque reproducible del stack E2E local de M1."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "--profile", "studio", "-f", "docker-compose.yml"]


def isolated_data_root() -> Path | None:
    if os.environ.get("E2E_ISOLATED") != "1" and os.environ.get("E2E_RECOVERY") != "1":
        return None
    return ROOT / ".cache" / "e2e-data"


def run(*args: str) -> None:
    environment = os.environ.copy()
    data_root = isolated_data_root()
    if data_root is not None:
        data_root.mkdir(parents=True, exist_ok=True)
        environment["STUDIO_DATA_ROOT"] = str(data_root)
    subprocess.run([*COMPOSE, *args], cwd=ROOT, check=True, env=environment)


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


def seed_isolated_stack() -> None:
    """Siembra por API sólo el volumen efímero reservado para E2E."""
    if isolated_data_root() is None:
        return
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "apps" / "server" / "scripts" / "seed_e2e.py"),
            "--base-url",
            "http://127.0.0.1:8000",
            "--output",
            str(ROOT / ".cache" / "e2e-seed.json"),
        ],
        cwd=ROOT,
        check=True,
        env=os.environ.copy(),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("up", "down", "restart-server", "smoke"))
    args = parser.parse_args()
    if args.command == "up":
        data_root = isolated_data_root()
        if data_root is not None:
            # Recovery E2E must never consume or mutate the user's persistent data.
            run("down")
            if data_root.exists():
                shutil.rmtree(data_root)
            data_root.mkdir(parents=True, exist_ok=True)
        run("up", "-d", "--build", "web", "server", "engine-mock")
        wait_url("http://127.0.0.1:8000/health")
        wait_url("http://127.0.0.1:3000/create")
        seed_isolated_stack()
    elif args.command == "down":
        run("down", "--remove-orphans")
    elif args.command == "restart-server":
        run("restart", "server")
        wait_url("http://127.0.0.1:8000/health")
    else:
        run("up", "-d", "--build", "web", "server", "engine-mock")
        wait_url("http://127.0.0.1:3000/create")
        print(
            "Stack E2E listo; ejecuta pnpm --filter ./apps/web exec playwright -- test"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
