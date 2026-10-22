"""Siembra datos mínimos y deterministas para el stack E2E local."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SEED_VERSION = "m1-e2e-v1"
COLLECTION_NAME = "E2E · Semilla"
SONG_TITLE = "E2E · Canción semilla"


def first_named(
    items: list[dict[str, Any]], key: str, value: str
) -> dict[str, Any] | None:
    """Devuelve la primera entidad con el nombre exacto, de forma determinista."""
    for item in items:
        if item.get(key) == value:
            return item
    return None


@dataclass
class SeedClient:
    base_url: str
    opener: Callable[..., Any] = urlopen

    def request(
        self,
        method: str,
        path: str,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        *,
        bootstrap: bool = False,
    ) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Accept": "application/json", "Origin": "http://127.0.0.1:3000"}
        if bootstrap:
            headers["X-Studio-Session-Bootstrap"] = "1"
        if token:
            headers["X-Studio-Session-Token"] = token
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.base_url.rstrip('/')}{path}",
            method=method,
            headers=headers,
            data=body,
        )
        try:
            with self.opener(request, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"seed E2E {method} {path}: HTTP {error.code}: {detail}"
            ) from error
        if not isinstance(result, dict):
            raise TypeError(f"seed E2E {method} {path}: respuesta no es un objeto")
        return result

    def bootstrap(self) -> str:
        result = self.request(
            "POST", "/api/session/bootstrap", payload=None, bootstrap=True
        )
        token = result.get("session_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("seed E2E: el server no devolvió session_token")
        return token

    def ensure(self) -> dict[str, Any]:
        token = self.bootstrap()
        collections = self.request("GET", "/api/collections", token)
        collection = first_named(collections.get("items", []), "name", COLLECTION_NAME)
        if collection is None:
            collection = self.request(
                "POST", "/api/collections", token, {"name": COLLECTION_NAME}
            )
        songs = self.request("GET", "/api/songs?limit=100", token)
        song = first_named(songs.get("items", []), "title", SONG_TITLE)
        if song is None:
            song = self.request(
                "POST",
                "/api/songs",
                token,
                {
                    "title": SONG_TITLE,
                    "artist": "Estudio local",
                    "style_prompt": "hip hop luminoso · semilla E2E",
                    "language": "es",
                    "tags": ["e2e", SEED_VERSION],
                    "notes": "Registro generado por el seed reproducible del stack E2E.",
                    "collection_id": collection["id"],
                },
            )
        return {
            "seed_version": SEED_VERSION,
            "collection_id": collection.get("id"),
            "song_id": song.get("id"),
            "collection_name": COLLECTION_NAME,
            "song_title": SONG_TITLE,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url", default=os.environ.get("E2E_API_ORIGIN", "http://127.0.0.1:8000")
    )
    parser.add_argument("--output", type=Path, default=Path(".cache/e2e-seed.json"))
    args = parser.parse_args(argv)
    result = SeedClient(args.base_url).ensure()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
