"""Seguridad y persistencia del stack E2E sin acceder a Docker ni a la red."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

SPEC = importlib.util.spec_from_file_location(
    "e2e_stack", Path(__file__).resolve().parents[1] / "scripts" / "e2e_stack.py"
)
stack = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stack)
SEED_STACK = stack.seed_isolated_stack
WAIT_URL = stack.wait_url


@pytest.fixture
def harness(tmp_path, monkeypatch):
    monkeypatch.setattr(stack, "ROOT", tmp_path)
    for key in (
        "E2E_PROJECT_NAME",
        "COMPOSE_PROJECT_NAME",
        "E2E_COMPOSE_FILE",
        "STUDIO_DATA_ROOT",
        "E2E_ENV_FILE",
        "E2E_DOCKER_CLI",
        "E2E_COMPOSE_CLI",
        "E2E_DOCKER_HOST",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("E2E_ISOLATED", "1")
    docker = tmp_path / "docker.exe"
    docker.write_bytes(b"simulated executable; never executed")
    docker.chmod(0o700)
    monkeypatch.setattr(stack.shutil, "which", lambda command: str(docker))
    monkeypatch.setattr(stack.subprocess, "run", Mock())
    monkeypatch.setattr(stack, "wait_url", Mock())
    monkeypatch.setattr(stack, "seed_isolated_stack", Mock())
    monkeypatch.setattr(stack.shutil, "rmtree", Mock())
    return tmp_path


def invoke(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["e2e_stack.py", *args])
    return stack.main()


def test_up_preserves_existing_data_and_never_stops_a_stack(harness, monkeypatch):
    data = harness / ".cache" / "e2e-data"
    data.mkdir(parents=True)
    (data / "song.wav").write_bytes(b"saved song")
    invoke(monkeypatch, "up")
    assert not stack.shutil.rmtree.called
    assert all(
        "down" not in call.args[0] for call in stack.subprocess.run.call_args_list
    )
    assert (data / "song.wav").read_bytes() == b"saved song"


def test_restart_uses_private_project_compose_and_data(harness, monkeypatch):
    compose = harness / ".cache" / "private" / "compose.json"
    compose.parent.mkdir(parents=True)
    compose.write_text("{}")
    data = harness / ".cache" / "private" / "data"
    monkeypatch.setenv("E2E_PROJECT_NAME", "music-studio-e2e-test")
    monkeypatch.setenv("E2E_COMPOSE_FILE", str(compose))
    monkeypatch.setenv("STUDIO_DATA_ROOT", str(data))
    invoke(monkeypatch, "restart-server")
    call = stack.subprocess.run.call_args
    assert call.args[0] == [
        str(harness / "docker.exe"),
        "compose",
        "--project-name",
        "music-studio-e2e-test",
        "--profile",
        "studio",
        "--file",
        str(compose),
        "restart",
        "server",
    ]
    assert call.kwargs["check"] is True
    assert call.kwargs["env"]["STUDIO_DATA_ROOT"] == str(data)
    stack.wait_url.assert_called_once_with("http://127.0.0.1:8000/health")


def test_recovery_uses_explicit_absolute_docker_with_filtered_path(
    harness, monkeypatch
):
    docker = harness / "Docker Desktop/docker.exe"
    docker.parent.mkdir()
    docker.write_bytes(b"simulated executable; never executed")
    docker.chmod(0o700)
    monkeypatch.setenv("PATH", str(harness / "filtered-node-only"))
    monkeypatch.setenv("E2E_DOCKER_CLI", str(docker))
    invoke(monkeypatch, "kill-server", "--project-name", "music-studio-e2e-private")
    command = stack.subprocess.run.call_args.args[0]
    assert command[0] == str(docker)
    assert command[-4:] == ["kill", "--signal", "SIGKILL", "server"]


def test_recovery_uses_standalone_compose_and_local_endpoint(harness, monkeypatch):
    compose = harness / "docker-compose.exe"
    compose.write_bytes(b"simulated executable; never executed")
    compose.chmod(0o700)
    monkeypatch.setenv("E2E_COMPOSE_CLI", str(compose))
    monkeypatch.setenv("E2E_DOCKER_HOST", "npipe:////./pipe/dockerDesktopLinuxEngine")
    monkeypatch.setenv("DOCKER_CONTEXT", "foreign-context")
    monkeypatch.setenv("DOCKER_TLS_VERIFY", "1")
    monkeypatch.setenv("DOCKER_CERT_PATH", "foreign-certs")
    invoke(monkeypatch, "kill-server", "--project-name", "music-studio-e2e-private")
    call = stack.subprocess.run.call_args
    assert call.args[0][0] == str(compose)
    assert call.args[0][1] == "--project-name"
    assert (
        call.kwargs["env"]["DOCKER_HOST"] == "npipe:////./pipe/dockerDesktopLinuxEngine"
    )
    assert (
        not {"DOCKER_CONTEXT", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"}
        & call.kwargs["env"].keys()
    )


@pytest.mark.parametrize(
    "endpoint",
    ["npipe:////./pipe/dockerDesktopLinuxEngine", "unix:///var/run/docker.sock"],
)
def test_local_docker_host_accepts_only_local_socket_forms(endpoint):
    assert stack.local_docker_host(endpoint) == endpoint


@pytest.mark.parametrize(
    "endpoint",
    [
        "tcp://127.0.0.1:2375",
        "tcp://remote:2375",
        "npipe:////remote/pipe/docker_engine",
        "unix://remote/run/docker.sock",
        "unix:////remote/docker.sock",
        "unix:///run/../foreign.sock",
        "unix:///",
        "",
        None,
    ],
)
def test_local_docker_host_rejects_network_or_ambiguous_endpoints(endpoint):
    with pytest.raises(ValueError, match="Endpoint Docker E2E"):
        stack.local_docker_host(endpoint)


def test_standalone_compose_refuses_remote_endpoint_before_any_command(
    harness, monkeypatch
):
    compose = harness / "docker-compose.exe"
    compose.write_bytes(b"simulated executable; never executed")
    compose.chmod(0o700)
    monkeypatch.setenv("E2E_COMPOSE_CLI", str(compose))
    monkeypatch.setenv("E2E_DOCKER_HOST", "tcp://remote:2375")
    with pytest.raises(ValueError, match="Endpoint Docker E2E"):
        invoke(monkeypatch, "kill-server")
    stack.subprocess.run.assert_not_called()


@pytest.mark.parametrize(
    "project", ["music-studio", "default", "e2e", "../../e2e-foreign"]
)
def test_refuses_user_project_before_any_command(harness, monkeypatch, project):
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", project)
    with pytest.raises((ValueError, SystemExit)):
        invoke(monkeypatch, "down")
    stack.subprocess.run.assert_not_called()


@pytest.mark.parametrize("kind", ["relative", "name", "missing", "directory", "link"])
def test_docker_cli_rejects_unvalidated_executable(harness, monkeypatch, kind):
    candidate = harness / "docker.exe"
    candidate.write_bytes(b"simulated executable; never executed")
    candidate.chmod(0o700)
    if kind == "relative":
        value = "docker.exe"
    elif kind == "name":
        candidate = candidate.rename(harness / "other.exe")
        value = str(candidate)
    elif kind == "missing":
        candidate.unlink()
        value = str(candidate)
    elif kind == "directory":
        candidate.unlink()
        candidate.mkdir()
        value = str(candidate)
    else:
        original = Path.is_symlink
        monkeypatch.setattr(
            Path, "is_symlink", lambda path: path == candidate or original(path)
        )
        value = str(candidate)
    monkeypatch.setenv("E2E_DOCKER_CLI", value)
    with pytest.raises(ValueError, match="Docker CLI E2E"):
        invoke(monkeypatch, "kill-server")
    stack.subprocess.run.assert_not_called()


def test_docker_cli_reports_missing_installation_without_subprocess(
    harness, monkeypatch
):
    monkeypatch.setattr(stack.shutil, "which", lambda command: None)
    with pytest.raises(ValueError, match="no disponible"):
        invoke(monkeypatch, "start-server")
    stack.subprocess.run.assert_not_called()


def test_refuses_data_outside_private_cache(harness, monkeypatch):
    monkeypatch.setenv("STUDIO_DATA_ROOT", str(harness / "data"))
    with pytest.raises((ValueError, SystemExit)):
        invoke(monkeypatch, "up")
    stack.subprocess.run.assert_not_called()
    stack.shutil.rmtree.assert_not_called()


def test_reset_requires_existing_ownership_marker(harness, monkeypatch):
    data = harness / ".cache" / "e2e-data"
    data.mkdir(parents=True)
    (data / "library.db").write_text("private")
    with pytest.raises(ValueError, match="propiedad"):
        invoke(monkeypatch, "up", "--reset-data")
    stack.subprocess.run.assert_not_called()
    stack.shutil.rmtree.assert_not_called()


def test_restart_failure_is_propagated_without_waiting(harness, monkeypatch):
    stack.subprocess.run.side_effect = subprocess.CalledProcessError(12, "docker")
    with pytest.raises(subprocess.CalledProcessError):
        invoke(monkeypatch, "restart-server")
    stack.wait_url.assert_not_called()


def test_explicit_reset_only_deletes_marked_data_after_scoped_down(
    harness, monkeypatch
):
    invoke(monkeypatch, "up")
    data = harness / ".cache" / "e2e-data"
    assert (
        json.loads((data / stack.MARKER).read_text())["project"] == "music-studio-e2e"
    )
    stack.subprocess.run.reset_mock()
    invoke(monkeypatch, "up", "--reset-data")
    command = stack.subprocess.run.call_args_list[0].args[0]
    assert command[-1] == "down"
    assert "music-studio-e2e" in command
    stack.shutil.rmtree.assert_called_once_with(data)


def test_reset_refuses_marker_from_another_project(harness, monkeypatch):
    data = harness / ".cache" / "e2e-data"
    data.mkdir(parents=True)
    (data / stack.MARKER).write_text(json.dumps({"project": "music-studio-e2e-other"}))
    with pytest.raises(ValueError, match="propiedad"):
        invoke(monkeypatch, "up", "--reset-data")
    stack.subprocess.run.assert_not_called()
    stack.shutil.rmtree.assert_not_called()


def test_reset_rejects_nested_windows_junction_without_deleting(harness, monkeypatch):
    invoke(monkeypatch, "up")
    data = harness / ".cache" / "e2e-data"
    nested = data / "junction"
    nested.mkdir()
    original = Path.is_junction
    monkeypatch.setattr(
        Path, "is_junction", lambda path: path == nested or original(path)
    )
    stack.subprocess.run.reset_mock()
    with pytest.raises(ValueError, match="junction|reparse|enlaces"):
        invoke(monkeypatch, "up", "--reset-data")
    stack.subprocess.run.assert_not_called()
    stack.shutil.rmtree.assert_not_called()


def test_kill_server_targets_only_private_stack(harness, monkeypatch):
    invoke(monkeypatch, "kill-server", "--project-name", "music-studio-e2e-recovery")
    command = stack.subprocess.run.call_args.args[0]
    assert command[command.index("--project-name") + 1] == "music-studio-e2e-recovery"
    assert command[-4:] == ["kill", "--signal", "SIGKILL", "server"]
    stack.wait_url.assert_not_called()


def test_recovery_inherits_exact_private_compose_env_file(harness, monkeypatch):
    env_file = harness / ".cache" / "stack.env"
    env_file.parent.mkdir()
    env_file.write_text("TEST_SETTING=private")
    monkeypatch.setenv("E2E_ENV_FILE", str(env_file))
    invoke(monkeypatch, "start-server")
    command = stack.subprocess.run.call_args.args[0]
    assert command[command.index("--env-file") + 1] == str(env_file)
    assert command[-2:] == ["start", "server"]
    stack.wait_url.assert_called_once_with("http://127.0.0.1:8000/health")


def test_seed_metadata_stays_inside_selected_private_data(harness):
    selected = stack.Stack(
        "music-studio-e2e-meta", "docker-compose.yml", ".cache/private/data"
    )
    SEED_STACK(selected)
    command = stack.subprocess.run.call_args.args[0]
    assert command[command.index("--output") + 1] == str(
        selected.data_root / "e2e-seed.json"
    )
    assert (
        stack.subprocess.run.call_args.kwargs["env"]["COMPOSE_PROJECT_NAME"]
        == selected.project
    )


def test_wait_url_retries_connection_errors_without_real_network(monkeypatch):
    response = Mock()
    response.__enter__ = Mock(return_value=Mock(status=200))
    response.__exit__ = Mock(return_value=False)
    opener = Mock(side_effect=[OSError("not ready"), response])
    monkeypatch.setattr(stack, "urlopen", opener)
    monkeypatch.setattr(stack.time, "sleep", Mock())
    WAIT_URL("http://127.0.0.1:8000/health")
    assert opener.call_count == 2


def test_wait_url_reports_unavailable_service(monkeypatch):
    monkeypatch.setattr(stack.time, "monotonic", Mock(side_effect=[1, 3]))
    monkeypatch.setattr(stack, "urlopen", Mock())
    with pytest.raises(SystemExit, match="no responde"):
        WAIT_URL("http://127.0.0.1:8000/health", timeout_s=1)
    stack.urlopen.assert_not_called()
