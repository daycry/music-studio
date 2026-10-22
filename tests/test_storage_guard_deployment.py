"""Contratos del despliegue CPU aislado; no acreditan permisos del mount real."""

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONSUMERS = ("server", "engine-mock", "engine-analysis", "engine-acestep")


@pytest.fixture
def manifests():
    return tuple(
        yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))["services"]
        for name in ("docker-compose.yml", "docker-compose.storage.yml")
    )


def _library(service):
    return next(volume for volume in service["volumes"] if volume["target"] == "/data")


def _required(value, name):
    assert re.fullmatch(r"\$\{" + name + r":\?[^}]+\}", value)


def test_helper_image_is_pinned_stdlib_cpu_and_exclusive_uid():
    path = ROOT / "apps/storage-guard/Dockerfile"
    assert path.is_file(), "Falta imagen CPU del helper exclusivo"
    instructions = [
        line.split(maxsplit=1)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len([line for line in instructions if line[0] == "FROM"]) == 1
    image = next(value for key, value in instructions if key == "FROM")
    assert image.startswith("python:3.12.14-slim-bookworm@sha256:")
    assert len(image.split("@sha256:")[1]) == 64
    assert image in (ROOT / "apps/server/Dockerfile").read_text(encoding="utf-8")
    assert [value for key, value in instructions if key == "USER"] == ["19000:10001"]
    assert json.loads(next(value for key, value in instructions if key == "CMD")) == [
        "python",
        "-m",
        "studio_storage_guard.helper",
    ]
    assert not {"RUN", "EXPOSE", "ADD", "HEALTHCHECK"} & {
        key for key, _ in instructions
    }
    copies = [value.split() for key, value in instructions if key == "COPY"]
    assert copies == [
        [
            "packages/storage-guard/studio_storage_guard",
            "/studio/packages/storage-guard/studio_storage_guard",
        ]
    ]
    assert (ROOT / copies[0][0] / "helper.py").is_file()
    environment = dict(
        value.split("=", 1) for key, value in instructions if key == "ENV"
    )
    assert environment["PYTHONPATH"] == "/studio/packages/storage-guard"


def test_helper_storage_authority_requires_exact_mount_and_uuid(manifests):
    _, override = manifests
    assert "storage-guard" in override, "Falta servicio helper del dominio aislado"
    helper = override["storage-guard"]
    assert set(helper["profiles"]) == {"studio", "engines"}
    assert helper["build"] == {
        "context": ".",
        "dockerfile": "apps/storage-guard/Dockerfile",
    }
    _required(helper["environment"]["STUDIO_STORAGE_UUID"], "STUDIO_STORAGE_UUID")
    assert len(helper["volumes"]) == 1
    library = _library(helper)
    _required(library["source"], "STUDIO_STORAGE_ROOT")
    assert library["type"] == "bind"
    assert library.get("read_only", False) is False
    assert library["bind"]["create_host_path"] is False


def test_helper_has_no_additional_authority_or_concurrent_uid_process(manifests):
    _, override = manifests
    assert "storage-guard" in override, "Falta servicio helper del dominio aislado"
    helper = override["storage-guard"]
    assert helper["user"] == "19000:10001"
    assert helper["cap_drop"] == ["ALL"]
    assert helper["security_opt"] == ["no-new-privileges:true"]
    for key in (
        "ports",
        "expose",
        "devices",
        "device_cgroup_rules",
        "gpus",
        "deploy",
        "cap_add",
        "privileged",
        "pid",
        "ipc",
        "network_mode",
        "userns_mode",
        "healthcheck",
        "entrypoint",
        "command",
    ):
        assert key not in helper, (
            f"El helper recibe autoridad o proceso adicional: {key}"
        )


@pytest.mark.parametrize("name", CONSUMERS)
def test_consumers_keep_base_dependencies_and_mount_scope(manifests, name):
    base, override = manifests
    consumer = override[name]
    assert consumer.get("user") == "10001:10001", "Consumidor sin identidad explícita"
    assert consumer["cap_drop"] == ["ALL"]
    assert consumer["security_opt"] == ["no-new-privileges:true"]
    # Compose merges mapping keys: long depends_on preserves the base engine-mock.
    assert isinstance(consumer["depends_on"], dict)
    dependencies = base[name].get("depends_on", {}) | consumer["depends_on"]
    assert dependencies["storage-guard"] == {"condition": "service_started"}
    for dependency, condition in base[name].get("depends_on", {}).items():
        assert dependencies[dependency] == condition
    _required(consumer["environment"]["STUDIO_STORAGE_UUID"], "STUDIO_STORAGE_UUID")
    library = _library(consumer)
    _required(library["source"], "STUDIO_STORAGE_ROOT")
    assert library["bind"]["create_host_path"] is False
    assert library.get("read_only", False) is (name != "server")
    if name != "server":
        raw = next(v for v in consumer["volumes"] if v["target"] == "/data/tmp")
        assert raw["source"] == library["source"] + "/tmp"
        assert raw.get("read_only", False) is False
        assert raw["bind"]["create_host_path"] is False
