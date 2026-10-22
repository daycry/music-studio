"""Configuración local validada antes del arranque."""

import re
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]
ENGINE_HOSTS = {
    "localhost",
    "127.0.0.1",
    "engine-mock",
    "engine-acestep",
    "engine-analysis",
    "engine-llm",
    "engine-comfy",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="STUDIO_",
        env_file=ROOT / ".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    data_dir: Path = ROOT / "data"
    models_dir: Path = ROOT / "models"
    engines: Annotated[dict[str, str], NoDecode] = Field(default_factory=dict)
    engine_token: SecretStr
    vram_margin_mb: int = Field(default=512, ge=0)
    # Cuando se declara, el server debe acreditar el montaje ext4 antes de
    # abrir logs, migrar SQLite o arrancar la cola. Vacío mantiene el modo de
    # desarrollo local sin VHDX.
    storage_uuid: UUID | None = None
    nightly_window: str = "01:00-07:00"
    web_origin: str = "http://127.0.0.1:3000"
    allowed_hosts: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "127.0.0.1:8000",
            "localhost:8000",
            "server:8000",
            "server",
        ]
    )

    @field_validator("engines", mode="before")
    @classmethod
    def parse_engines(cls, value):
        if isinstance(value, str):
            mapping = {}
            for entry in value.split(","):
                family, sep, url = entry.partition("=")
                family = family.strip()
                if not sep or family in mapping:
                    raise ValueError("Invalid engine mapping")
                mapping[family] = url.strip()
            value = mapping
        for family, url in value.items():
            parsed = urlsplit(url)
            if (
                not re.fullmatch(r"[a-z][a-z0-9_-]*", family)
                or parsed.scheme != "http"
                or parsed.hostname not in ENGINE_HOSTS
                or parsed.username
                or parsed.password
                or parsed.path not in ("", "/")
                or parsed.query
                or parsed.fragment
                or not parsed.port
                or not 1 <= parsed.port <= 65535
            ):
                raise ValueError("Invalid local engine URL")
        return value

    @field_validator("data_dir", "models_dir")
    @classmethod
    def confine_path(cls, value, info):
        resolved = (ROOT / value).resolve()
        container_path = Path("/data" if info.field_name == "data_dir" else "/models")
        if resolved.is_relative_to(ROOT) or (
            ROOT == Path("/studio") and resolved == container_path
        ):
            return resolved
        raise ValueError("Path must remain inside the studio")

    @field_validator("engine_token")
    @classmethod
    def validate_token(cls, value):
        raw = value.get_secret_value()
        if not raw or any(ord(char) < 33 or ord(char) > 126 for char in raw):
            raise ValueError(
                "Run scripts/init_env.py to configure the persistent token"
            )
        return value

    @field_validator("web_origin")
    @classmethod
    def validate_origin(cls, value):
        parsed = urlsplit(value)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"localhost", "127.0.0.1"}
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not parsed.port
        ):
            raise ValueError("Invalid local web origin")
        return value

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def validate_hosts(cls, value):
        if isinstance(value, str):
            value = [host.strip() for host in value.split(",")]
        if not value or any(
            not re.fullmatch(
                r"(127\.0\.0\.1|localhost|server)(:[1-9][0-9]{0,4})?", host
            )
            for host in value
        ):
            raise ValueError("Invalid closed host list")
        if any(":" in host and int(host.rsplit(":", 1)[1]) > 65535 for host in value):
            raise ValueError("Invalid host port")
        return value

    @field_validator("nightly_window")
    @classmethod
    def validate_window(cls, value):
        if not re.fullmatch(
            r"([01][0-9]|2[0-3]):[0-5][0-9]-([01][0-9]|2[0-3]):[0-5][0-9]", value
        ):
            raise ValueError("Invalid nightly window")
        return value


class ContractSettings(Settings):
    """Mismas validaciones, solo entradas explícitas para exportación offline."""

    model_config = SettingsConfigDict(env_file=None)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (init_settings,)
