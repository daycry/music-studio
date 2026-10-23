"""Entrypoints propios: controles funcionales nativos y límites del CLI."""

import importlib.util
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PS = (
    Path(os.environ.get("SYSTEMROOT", "C:/Windows"))
    / "System32/WindowsPowerShell/v1.0/powershell.exe"
)


@pytest.mark.skipif(os.name != "nt", reason="SWC y Node oficiales Windows")
def test_native_swc_transform_with_isolated_environment(cli, tmp_path):
    # Raíz corta (.t/, ignorada por git) dentro del proyecto: el lock de SWC no cabe en MAX_PATH bajo pytest-tmp.
    short = _short_root()
    try:
        _swc_transform(cli, tmp_path, short)
    finally:
        shutil.rmtree(short)  # un fallo al limpiar debe verse, no callarse


def _short_root():
    """Primer carácter libre de .t/: mkdir sin exist_ok evita chocar con otras ejecuciones."""
    base = ROOT / ".t"
    base.mkdir(exist_ok=True)
    for candidate in "abcdefghijklmnopqrstuvwxyz0123456789":
        try:
            (base / candidate).mkdir()
        except FileExistsError:
            continue
        return base / candidate
    raise RuntimeError(".t/ está lleno de restos de ejecuciones anteriores; bórralo")


def _swc_transform(cli, tmp_path, short):
    """Transformación nativa real: no sustituye el wrapper canónico del build."""
    import hashlib

    tools = cli.verified_tools(ROOT)
    env = cli.environment(short, tools)
    cli.check_swc_path_budget(short)
    payload = (
        ROOT
        / "node_modules/.pnpm/@swc+core@1.16.13_@swc+helpers@0.5.23/node_modules/@swc/core"
    )
    native = (
        ROOT
        / "node_modules/.pnpm/@swc+core-win32-x64-msvc@1.16.13/node_modules/@swc/core-win32-x64-msvc/swc.win32-x64-msvc.node"
    )
    # Sólo bytes oficiales ya instalados; nunca descargar ni sustituir el binding.
    script = short / "transform.cjs"
    script.write_text(
        "const swc=require(" + json.dumps(str(payload)) + ");"
        "const result=swc.transformSync('const value: number = 42;',"
        "{jsc:{parser:{syntax:'typescript'}}});"
        "console.log(JSON.stringify({pid:process.pid,parent:process.ppid,"
        "node:process.execPath,utc:new Date().toISOString(),code:result.code}));",
        encoding="utf-8",
    )
    folder = (
        Path(os.environ["STUDIO_TEST_ROOT"]).parent / "swc-receipts" / tmp_path.name
    )
    folder.mkdir(parents=True)
    argv = [str(tools["node"]["dest"] / "node.exe"), str(script)]
    shutil.copyfile(script, folder / "transform-before.cjs")
    shutil.copyfile(ROOT / "scripts/pnpm.py", folder / "pnpm-before.py")
    shutil.copyfile(payload / "binding.js", folder / "binding-before.js")
    (folder / "before.json").write_text(
        json.dumps(
            {
                "utc": datetime.now(UTC).isoformat(),
                "argv": argv,
                "env": env,
                "native_sha256": hashlib.sha256(native.read_bytes()).hexdigest(),
                "FILETIME": "UNKNOWN",
                "Job": "UNKNOWN",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with subprocess.Popen(
        argv, cwd=short, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as child:
        stdout, stderr = child.communicate(timeout=60)
        (folder / "stdout-original.bin").write_bytes(stdout)
        (folder / "stderr-original.bin").write_bytes(stderr)
        cache = short / ".cache"
        writes = {
            p.relative_to(short).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in cache.rglob("*")
            if p.is_file()
        }
        (folder / "after.json").write_text(
            json.dumps(
                {
                    "utc": datetime.now(UTC).isoformat(),
                    "pid": child.pid,
                    "exit": child.returncode,
                    "cache_writes": writes,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    assert child.returncode == 0, stderr.decode("utf-8", errors="replace")
    result = json.loads(stdout)
    assert "value = 42" in result["code"]
    assert result["node"] == str(tools["node"]["dest"] / "node.exe")
    assert result["pid"] != result["parent"]


@pytest.mark.parametrize("kind", ["hardlink", "directory-link", "ordinary"])
def test_native_cache_rejects_aliases_before_child(cli, tmp_path, kind):
    cache = tmp_path / ".cache/swc"
    cache.mkdir(parents=True)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    original = foreign / "payload.node"
    original.write_bytes(b"foreign binding")
    target = cache / "payload.node"
    if kind == "hardlink":
        os.link(original, target)
    elif kind == "directory-link":
        if os.name == "nt":
            import _winapi

            _winapi.CreateJunction(str(foreign), str(target))
        else:
            target.symlink_to(foreign)
    else:
        target.write_bytes(b"ordinary cache entry")
    try:
        tools = {"node": {"dest": tmp_path / "node"}}
        if kind == "ordinary":
            env = cli.environment(tmp_path, tools)
            assert env["SWC_NATIVE_BINDING_CACHE"] == str(cache)
            assert Path(env["LOCALAPPDATA"]).is_relative_to(tmp_path / ".cache/la")
        else:
            with pytest.raises(ValueError):
                cli.environment(tmp_path, tools)
        assert original.read_bytes() == b"foreign binding"
    finally:
        if kind == "directory-link" and os.name == "nt":
            target.rmdir()
        elif kind in {"hardlink", "directory-link"}:
            target.unlink()


def clone_scripts(path):
    (path / "scripts").mkdir()
    for name in (
        "env.ps1",
        "env.sh",
        "bootstrap.ps1",
        "bootstrap.sh",
        "pnpm.py",
        "pnpm.ps1",
        "pnpm.sh",
        "fetch_web_tools.py",
    ):
        source = ROOT / "scripts" / name
        if source.exists():
            shutil.copyfile(source, path / "scripts" / name)
    shutil.copyfile(ROOT / "package.json", path / "package.json")
    (path / "tools").mkdir()
    shutil.copyfile(ROOT / "tools/tools.lock.json", path / "tools/tools.lock.json")
    (path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n")
    (path / ".venv/Scripts").mkdir(parents=True)
    shutil.copyfile(ROOT / ".venv/pyvenv.cfg", path / ".venv/pyvenv.cfg")
    shutil.copyfile(
        ROOT / ".venv/Scripts/python.exe", path / ".venv/Scripts/python.exe"
    )


def native_ps(path, command):
    runner = path / "invoke.ps1"
    runner.write_text(command, encoding="utf-8")
    argv = [str(PS), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(runner)]
    folder = Path(os.environ["STUDIO_TEST_ROOT"]).parent / "native-receipts"
    frozen = folder / path.name
    frozen.mkdir(parents=True)
    shutil.copytree(path / "scripts", frozen / "scripts")
    shutil.copyfile(runner, frozen / "invoke.ps1")
    started = datetime.now(UTC).isoformat()
    result = subprocess.run(
        argv,
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    receipt = {
        "utc": started,
        "argv": argv,
        "exit": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    # Original subprocess receipts survive workspace teardown in the private namespace.
    (folder / (path.name + ".json")).write_text(json.dumps(receipt, indent=2))
    return result


@pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows nativo")
@pytest.mark.parametrize("mode", ["missing", "tampered", "override"])
def test_env_rejects_foreign_manager(tmp_path, mode):
    clone_scripts(tmp_path)
    if mode == "tampered":
        fake = tmp_path / "tools/node/22.23.2/win-x64"
        fake.mkdir(parents=True)
        (fake / "node.exe").write_bytes(b"wrong hash")
    arguments = "--store-dir outside" if mode == "override" else "--version"
    result = native_ps(
        tmp_path,
        f"""
function pnpm {{ 'FOREIGN_MANAGER_EXECUTED'; $global:LASTEXITCODE = 0 }}
. "$PSScriptRoot/scripts/env.ps1"
pnpm {arguments}
exit $LASTEXITCODE
""",
    )
    assert "FOREIGN_MANAGER_EXECUTED" not in result.stdout
    assert result.returncode != 0


@pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows nativo")
def test_bootstrap_rejects_missing_tools_after_benign_uv(tmp_path):
    clone_scripts(tmp_path)
    result = native_ps(
        tmp_path,
        """
function uv { 'BENIGN_PRIVATE_UV'; $global:LASTEXITCODE = 0 }
function pnpm { 'FOREIGN_MANAGER_EXECUTED'; $global:LASTEXITCODE = 0 }
& "$PSScriptRoot/scripts/bootstrap.ps1"
""",
    )
    assert result.stdout.count("BENIGN_PRIVATE_UV") == 2
    assert "FOREIGN_MANAGER_EXECUTED" not in result.stdout
    assert "bootstrap completo" not in result.stdout
    assert result.returncode != 0


@pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows nativo")
def test_ps_exact_typed_argv_and_exit_mock_python_boundary(tmp_path):
    clone_scripts(tmp_path)
    # Mock explícito del receptor Python, nunca autoridad de hashes/versiones de Node.
    (tmp_path / "scripts/pnpm.py").write_text(
        'import json, sys, pathlib\npathlib.Path(__file__).with_name("received.json").write_text(json.dumps(sys.argv[1:]))\nsys.exit(37)\n'
    )
    expected = [
        "test",
        "--",
        "two words",
        'a"b',
        "trailing\\",
        "$(never)",
        "`never`",
        "español",
    ]
    (tmp_path / "args.json").write_text(json.dumps(expected), encoding="utf-8")
    out = native_ps(
        tmp_path,
        """
. "$PSScriptRoot/scripts/env.ps1"
$typedArgs = Get-Content -Raw "$PSScriptRoot/args.json" | ConvertFrom-Json
pnpm @typedArgs
exit $LASTEXITCODE
""",
    )
    assert out.returncode == 37
    received = json.loads((tmp_path / "scripts/received.json").read_text())
    if received[:1] == ["--studio-argv-base64"]:
        import base64

        received = json.loads(base64.b64decode(received[1]).decode("utf-8"))
    assert received == expected


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "studio_pnpm", ROOT / "scripts/pnpm.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["dlx", "x"],
        ["--filter"],
        ["--filter", "../outside", "test"],
        ["install", "new-package"],
        ["fetch", "--no-frozen-lockfile"],
        ["test", "--store-dir=outside"],
        ["test", "--cache-dir", "outside"],
        ["test", "--userconfig", "outside"],
        ["test", "-C", "outside"],
        ["exec", "node"],
        ["run", "foreign"],
    ],
)
def test_rejects_config_and_new_resolution(cli, args):
    with pytest.raises(ValueError):
        cli.validate_args(args)


@pytest.mark.parametrize(
    "args",
    [
        ["--version"],
        ["-v"],
        ["install"],
        ["fetch", "--offline"],
        ["--filter", "web", "install", "--frozen-lockfile", "--ignore-scripts"],
        ["--filter", "./apps/web", "test", "--", "-g", "two words"],
        ["exec", "tsc", "--noEmit"],
        ["exec", "playwright", "test"],
        ["run", "gen"],
        ["build"],
    ],
)
def test_preserves_allowed_argv(cli, args):
    actual = cli.validate_args(args)
    if "install" in args or "fetch" in args:
        assert actual.count("--ignore-scripts") == 1
        assert actual.count("--frozen-lockfile") == 1
    else:
        assert actual == args


def test_main_error_is_readable_and_nonzero(cli, capsys, monkeypatch):
    monkeypatch.setattr(
        cli,
        "execute",
        lambda *args: (_ for _ in ()).throw(ValueError("control sin secretos")),
    )
    assert cli.main(["--version"]) == 1
    assert "pnpm NO LISTO: control sin secretos" in capsys.readouterr().err


def test_exec_environment_argv_and_exit_mock_boundary(cli, tmp_path, monkeypatch):
    tools = {name: {"dest": tmp_path / name} for name in ("node", "pnpm")}
    monkeypatch.setattr(cli, "verified_tools", lambda root: tools)
    monkeypatch.setenv("NODE_OPTIONS", "--require foreign")
    monkeypatch.setenv("npm_config_store_dir", "outside")
    monkeypatch.setenv("PNPM_HOME", "outside")

    def run(argv, **options):
        assert argv == [
            str(tmp_path / "node/node.exe"),
            str(tmp_path / "pnpm/bin/pnpm.cjs"),
            "test",
            "--",
            'a"b',
            "$(never)",
            "`never`",
            "two words",
        ]
        assert options["cwd"] == tmp_path
        assert options["shell"] is False
        env = options["env"]
        assert "NODE_OPTIONS" not in env
        assert env["CI"] == "true"
        assert env["npm_config_ignore_scripts"] == "true"
        assert env["npm_config_virtual_store_dir_max_length"] == "40"
        assert env["npm_config_manage_package_manager_versions"] == "false"
        for key in (
            "TEMP",
            "TMP",
            "PNPM_HOME",
            "npm_config_store_dir",
            "npm_config_userconfig",
        ):
            assert Path(env[key]).is_relative_to(tmp_path)
        return subprocess.CompletedProcess(argv, 37)

    monkeypatch.setattr(cli.subprocess, "run", run)
    assert (
        cli.execute(["test", "--", 'a"b', "$(never)", "`never`", "two words"], tmp_path)
        == 37
    )


def test_environment_preserves_only_e2e_control_variables(cli, tmp_path, monkeypatch):
    monkeypatch.setenv("E2E_RECOVERY", "1")
    monkeypatch.setenv("E2E_ISOLATED", "1")
    monkeypatch.setenv("MOCK_STAGE_DELAY_MS", "5000")
    monkeypatch.setenv("FOREIGN_RUNTIME_OVERRIDE", "must-not-leak")

    env = cli.environment(tmp_path, {"node": {"dest": tmp_path / "node"}})

    assert env["E2E_RECOVERY"] == "1"
    assert env["E2E_ISOLATED"] == "1"
    assert env["MOCK_STAGE_DELAY_MS"] == "5000"
    assert "FOREIGN_RUNTIME_OVERRIDE" not in env


def test_rejects_project_config_before_execution(cli, tmp_path, monkeypatch):
    (tmp_path / ".npmrc").write_text("store-dir=outside")
    monkeypatch.setattr(
        cli, "verified_tools", lambda root: pytest.fail("must not execute")
    )
    with pytest.raises(ValueError, match="no revisada"):
        cli.execute(["--version"], tmp_path)


def test_platform_guard(cli, monkeypatch):
    monkeypatch.setattr(cli.os, "name", "posix")
    with pytest.raises(ValueError, match="Linux no soportado"):
        cli.verified_tools(ROOT)


@pytest.mark.parametrize(
    "payload", ["{}", "[42]", '["test", "--", "two words", "a\\"b", "$(never)"]']
)
def test_base64_transport_is_typed(cli, payload, monkeypatch):
    import base64

    monkeypatch.setattr(
        cli, "execute", lambda args, root: 37 if args == json.loads(payload) else 99
    )
    result = cli.main(
        ["--studio-argv-base64", base64.b64encode(payload.encode()).decode()]
    )
    assert result == (37 if payload.startswith('["') else 1)


def test_base64_transport_invalid_size(cli):
    assert cli.main(["--studio-argv-base64"]) == 1


@pytest.mark.skipif(os.name != "nt", reason="Node Windows verificado")
def test_current_tools_verified_without_execution(cli):
    prepared = cli.verified_tools(ROOT)
    assert prepared["node"]["dest"] == ROOT / "tools/node/22.23.2/win-x64"
    assert len(prepared["node"]["manifest"]) + len(prepared["pnpm"]["manifest"]) == 2933


@pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows nativo")
def test_native_current_manager_rejects_wrong_payload_hash(tmp_path):
    clone_scripts(tmp_path)
    archive_dir = tmp_path / ".cache/dev-cycle/m1/t08-web-toolchain-inventory"
    archive_dir.mkdir(parents=True)
    for name in ("node-v22.23.2-win-x64.zip", "pnpm-9.12.0.tgz"):
        shutil.copyfile(
            ROOT / ".cache/dev-cycle/m1/t08-web-toolchain-inventory" / name,
            archive_dir / name,
        )
    dest = tmp_path / "tools/node/22.23.2/win-x64"
    shutil.copytree(ROOT / "tools/node/22.23.2/win-x64", dest)
    with (dest / "node.exe").open("r+b") as stream:
        stream.seek(120)
        original = stream.read(1)
        stream.seek(120)
        stream.write(bytes([original[0] ^ 1]))
    out = native_ps(
        tmp_path,
        """
function pnpm { 'FOREIGN_MANAGER_EXECUTED'; $global:LASTEXITCODE = 0 }
. "$PSScriptRoot/scripts/env.ps1"
pnpm --version
exit $LASTEXITCODE
""",
    )
    assert out.returncode == 1
    assert "FOREIGN_MANAGER_EXECUTED" not in out.stdout
    assert "Disco alterado/incompleto" in out.stderr


@pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows nativo")
def test_bootstrap_frozen_ignore_scripts_mock_python_boundary(tmp_path):
    clone_scripts(tmp_path)
    (tmp_path / "scripts/pnpm.py").write_text(
        'import json,sys,base64,pathlib\npathlib.Path(__file__).with_name("received.json").write_text(base64.b64decode(sys.argv[2]).decode())\n'
    )
    result = native_ps(
        tmp_path,
        """
function uv { 'BENIGN_PRIVATE_UV'; $global:LASTEXITCODE = 0 }
& "$PSScriptRoot/scripts/bootstrap.ps1"
""",
    )
    assert result.returncode == 0
    assert result.stdout.count("BENIGN_PRIVATE_UV") == 2
    assert json.loads((tmp_path / "scripts/received.json").read_text()) == [
        "install",
        "--frozen-lockfile",
        "--ignore-scripts",
    ]


@pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows nativo")
def test_env_lexical_binding_survives_caller_root_cwd_and_alias(tmp_path):
    clone_scripts(tmp_path)
    (tmp_path / "scripts/pnpm.py").write_text(
        'import pathlib\nprint("OWN_MOCK_BOUNDARY:"+str(pathlib.Path(__file__).resolve().parent.parent))\n'
    )
    out = native_ps(
        tmp_path,
        """
function Foreign-Pnpm { 'FOREIGN_MANAGER_EXECUTED' }
Set-Alias pnpm Foreign-Pnpm
. "$PSScriptRoot/scripts/env.ps1"
$root = 'outside'
$studioPnpmScript = 'outside'
Set-Location "$PSScriptRoot/tools"
pnpm --version
exit $LASTEXITCODE
""",
    )
    assert out.returncode == 0
    assert "FOREIGN_MANAGER_EXECUTED" not in out.stdout
    assert f"OWN_MOCK_BOUNDARY:{tmp_path}" in out.stdout


@pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows nativo")
def test_native_python_startup_ignores_foreign_pythonpath(tmp_path):
    clone_scripts(tmp_path)
    foreign = tmp_path / "foreign-python"
    foreign.mkdir()
    (foreign / "sitecustomize.py").write_text('print("FOREIGN_PYTHON_STARTUP")\n')
    out = native_ps(
        tmp_path,
        """
$env:PYTHONPATH = "$PSScriptRoot/foreign-python"
. "$PSScriptRoot/scripts/env.ps1"
pnpm --version
exit $LASTEXITCODE
""",
    )
    assert "FOREIGN_PYTHON_STARTUP" not in out.stdout
    assert out.returncode == 1


@pytest.fixture
def nested_project(cli, tmp_path):
    """Herramientas oficiales copiadas después de verificar origen y destino."""
    tmp_path = tmp_path / "own root & español `literal` %"
    tmp_path.mkdir()
    clone_scripts(tmp_path)
    prepared = cli.verified_tools(ROOT)
    for tool in prepared.values():
        files = [tool["archive"], *tool["dest"].rglob("*")]
        for source in files:
            cli.manager.safe_path(source, ROOT)
            target = cli.manager.safe_path(
                tmp_path / source.relative_to(ROOT), tmp_path
            )
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                assert source.stat().st_nlink == 1
                target.parent.mkdir(parents=True, exist_ok=True)
                assert not target.exists()
                shutil.copyfile(source, target)
                assert cli.manager.digest(source) == cli.manager.digest(target)
    cli.verified_tools(tmp_path)
    (tmp_path / "pnpm-workspace.yaml").write_text("packages:\n  - apps/web\n")
    web = tmp_path / "apps/web"
    web.mkdir(parents=True)
    (web / "package.json").write_text(
        json.dumps(
            {
                "name": "web",
                "private": True,
                "scripts": {"gen": "node child.cjs", "test": "node child.cjs"},
            }
        )
    )
    (web / "child.cjs").write_text(
        "const fs=require('fs'); fs.writeFileSync('result.json',JSON.stringify({"
        "argv:process.argv.slice(2),pid:process.pid,parent:process.ppid,"
        "node:process.execPath,cwd:process.cwd(),utc:new Date().toISOString()}));"
        "process.exit(Number(fs.readFileSync('exit.txt','utf8')));"
    )
    (web / "exit.txt").write_text("0")
    ambient = tmp_path / "ambient"
    ambient.mkdir()
    (ambient / "pnpm.cmd").write_text(
        "@echo FOREIGN_MANAGER_EXECUTED\r\n@exit /b 0\r\n"
    )
    return tmp_path


def nested_native(path, args):
    """Sella el comando y todos los bytes propios antes del hijo nativo."""
    import hashlib
    import uuid

    folder = (
        Path(os.environ["STUDIO_TEST_ROOT"]).parent
        / "nested-receipts"
        / uuid.uuid4().hex
    )
    folder.mkdir(parents=True)
    (path / "args.json").write_text(json.dumps(args), encoding="utf-8")
    runner = path / "nested.ps1"
    runner.write_text(
        '$env:PATH = "$PSScriptRoot/ambient"\n'
        '. "$PSScriptRoot/scripts/env.ps1"\n'
        '$typedArgs = Get-Content -Raw "$PSScriptRoot/args.json" | ConvertFrom-Json\n'
        "pnpm @typedArgs\nexit $LASTEXITCODE\n",
        encoding="utf-8",
    )
    argv = [str(PS), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(runner)]
    manifest = {}
    for source in path.rglob("*"):
        if source.is_file():
            relative = source.relative_to(path)
            manifest[relative.as_posix()] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            if relative.parts[0] in {"scripts", "apps"} or source.parent == path:
                target = folder / "fixture" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
    before = {
        "utc": datetime.now(UTC).isoformat(),
        "argv": argv,
        "cwd": str(path),
        "child_args": args,
        "manifest": manifest,
    }
    (folder / "before.json").write_text(json.dumps(before, indent=2))
    with subprocess.Popen(
        argv, cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as child:
        stdout_bytes, stderr_bytes = child.communicate(timeout=120)
        (folder / "stdout-original.bin").write_bytes(stdout_bytes)
        (folder / "stderr-original.bin").write_bytes(stderr_bytes)
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        result = subprocess.CompletedProcess(argv, child.returncode, stdout, stderr)
        receipt = {
            "pid": child.pid,
            "parent": os.getpid(),
            "exit": child.returncode,
            "finished_utc": datetime.now(UTC).isoformat(),
            "stdout": stdout,
            "stderr": stderr,
        }
    (folder / "after.json").write_text(json.dumps(receipt, indent=2))
    result_file = path / "apps/web/result.json"
    if result_file.exists():
        shutil.copyfile(result_file, folder / "child-result.json")
    return result


@pytest.mark.skipif(os.name != "nt", reason="pnpm y Node Windows oficiales")
def test_native_root_gen_routes_nested_manager(nested_project):
    out = nested_native(nested_project, ["gen"])
    assert out.returncode == 0, out.stdout + out.stderr
    result = json.loads(
        (nested_project / "apps/web/result.json").read_text(encoding="utf-8")
    )
    assert result["cwd"] == str(nested_project / "apps/web")
    assert result["node"] == str(nested_project / "tools/node/22.23.2/win-x64/node.exe")
    assert result["pid"] != result["parent"]
    assert "FOREIGN_MANAGER_EXECUTED" not in out.stdout


@pytest.mark.skipif(os.name != "nt", reason="pnpm y Node Windows oficiales")
def test_native_nested_argv_and_exact_exit(nested_project):
    web = nested_project / "apps/web"
    (web / "exit.txt").write_text("37")
    expected = ["two words", "español", "`literal`"]
    out = nested_native(nested_project, ["gen", "--", *expected])
    result = json.loads((web / "result.json").read_text(encoding="utf-8"))
    # pnpm 9 conserva el separador al transportarlo por los dos scripts.
    assert result["argv"] == ["--", *expected]
    assert out.returncode == 37, out.stdout + out.stderr
    assert "FOREIGN_MANAGER_EXECUTED" not in out.stdout


@pytest.mark.parametrize("kind", ["tampered", "hardlink", "directory", "reparse"])
def test_owned_launcher_preserves_foreign_target(cli, tmp_path, kind):
    target = tmp_path / ".cache/web-runtime/bin/pnpm.cmd"
    target.parent.mkdir(parents=True)
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"foreign data")
    if kind == "hardlink":
        os.link(foreign, target)
    elif kind == "reparse":
        if os.name == "nt":
            import _winapi

            directory = tmp_path / "foreign-directory"
            directory.mkdir()
            _winapi.CreateJunction(str(directory), str(target))
        else:
            target.symlink_to(foreign)
    elif kind == "directory":
        target.mkdir()
    else:
        target.write_bytes(b"foreign data")
    try:
        with pytest.raises(ValueError):
            cli.owned_file(tmp_path, target, b"trusted launcher")
        assert foreign.read_bytes() == b"foreign data"
        if kind not in {"directory", "reparse"}:
            assert target.read_bytes() == b"foreign data"
    finally:
        if kind == "reparse" and os.name == "nt":
            target.rmdir()
        elif kind in {"hardlink", "reparse"}:
            target.unlink()


@pytest.mark.skipif(os.name != "nt", reason="pnpm y Node Windows oficiales")
@pytest.mark.parametrize("mode", ["missing", "tampered", "override", "config"])
def test_native_nested_call_revalidates_tools_and_config(nested_project, mode):
    web = nested_project / "apps/web"
    commands = {
        "missing": "require('fs').unlinkSync('../../tools/pnpm/9.12.0/bin/pnpm.cjs');",
        "tampered": "require('fs').appendFileSync('../../tools/pnpm/9.12.0/bin/pnpm.cjs','tampered');",
        "config": "require('fs').writeFileSync('../../.npmrc','store-dir=outside');",
        "override": "",
    }
    # Las rutas oficiales se obtienen del lock vigente, sin un gestor sustituto.
    lock = json.loads((nested_project / "tools/tools.lock.json").read_text())
    pnpm_path = "../../" + lock["tools"]["pnpm"]["dest"] + "/bin/pnpm.cjs"
    code = commands[mode].replace("../../tools/pnpm/9.12.0/bin/pnpm.cjs", pnpm_path)
    (web / "prepare.cjs").write_text(code)
    package = json.loads((web / "package.json").read_text())
    args = "test --store-dir=outside" if mode == "override" else "--version"
    package["scripts"]["gen"] = "node prepare.cjs && pnpm " + args
    (web / "package.json").write_text(json.dumps(package))
    out = nested_native(nested_project, ["gen"])
    assert out.returncode != 0
    assert "pnpm NO LISTO" in out.stderr
    assert "FOREIGN_MANAGER_EXECUTED" not in out.stdout
    assert not (web / "result.json").exists()


@pytest.mark.skipif(os.name != "nt", reason="pnpm y Node Windows oficiales")
def test_native_tampered_owned_launcher_is_preserved(cli, nested_project):
    cli.environment(nested_project, cli.verified_tools(nested_project))
    launcher = nested_project / ".cache/web-runtime/bin/pnpm.cmd"
    launcher.write_bytes(b"@echo FOREIGN_MANAGER_EXECUTED\r\n")
    out = nested_native(nested_project, ["gen"])
    assert out.returncode == 1
    assert "FOREIGN_MANAGER_EXECUTED" not in out.stdout
    assert launcher.read_bytes() == b"@echo FOREIGN_MANAGER_EXECUTED\r\n"


def test_stable_runtime_reuses_only_expected_launcher(cli, tmp_path):
    tools = {"node": {"dest": tmp_path / "node"}}
    first = cli.environment(tmp_path, tools)
    second = cli.environment(tmp_path, tools)
    assert first == second
    assert first["PATH"].split(os.pathsep) == [
        str(tmp_path / ".cache/web-runtime/bin"),
        str(tmp_path / "node"),
    ]
    for key in (
        "TEMP",
        "TMP",
        "HOME",
        "USERPROFILE",
        "PNPM_HOME",
        "npm_config_store_dir",
        "npm_config_userconfig",
    ):
        assert Path(first[key]).is_relative_to(tmp_path / ".cache/web-runtime")
        assert "dev-cycle" not in Path(first[key]).relative_to(tmp_path).parts


# SWC añade swc-native-<SID>/v1/<128 hex>.lock a la caché; el addon no usa rutas largas
# (MAX_PATH 260): con la caché bajo web-runtime la ruta medía 263 y el build fallaba.
def _swc_lock_length(root, key):
    path = Path(root) / ".cache" / key
    # "\" + swc-native-<SID de 48>, "\" + v1, "\" + 128 hex + .lock
    return (
        len(str(path))
        + 1
        + len("swc-native-")
        + 48
        + 1
        + len("v1")
        + 1
        + 128
        + len(".lock")
    )


def test_environment_pins_playwright_browsers_to_existing_location(cli, tmp_path):
    env = cli.environment(tmp_path, {"node": {"dest": tmp_path / "node"}})
    expected = tmp_path / ".cache/web-runtime/local-appdata/ms-playwright"
    assert Path(env["PLAYWRIGHT_BROWSERS_PATH"]) == expected
    # LOCALAPPDATA ya no apunta a web-runtime: sin el pin Playwright no hallaría los navegadores.
    assert not Path(env["LOCALAPPDATA"]).is_relative_to(tmp_path / ".cache/web-runtime")


@pytest.mark.skipif(os.name != "nt", reason="MAX_PATH es una limitación de Windows")
def test_swc_cache_lock_paths_fit_max_path(cli, tmp_path):
    env = cli.environment(tmp_path, {"node": {"dest": tmp_path / "node"}})
    assert Path(env["SWC_NATIVE_BINDING_CACHE"]) == tmp_path / ".cache/swc"
    assert Path(env["LOCALAPPDATA"]) == tmp_path / ".cache/la"
    assert _swc_lock_length(cli.ROOT, "swc") < 260
    assert _swc_lock_length(cli.ROOT, "la/swc") < 260
    cli.check_swc_path_budget(cli.ROOT)


@pytest.mark.skipif(os.name != "nt", reason="MAX_PATH es una limitación de Windows")
def test_swc_cache_refuses_root_too_long_for_max_path(cli, tmp_path):
    deep = tmp_path / ("d" * 60) / ("e" * 60) / ("f" * 60)
    deep.mkdir(parents=True)
    with pytest.raises(ValueError, match="MAX_PATH"):
        cli.check_swc_path_budget(deep)
    cli.check_swc_path_budget(cli.ROOT)


class NativeWindowsFS:
    """Instrumenta barreras; todas las operaciones y errores son del disco nativo."""

    def __init__(self, target, mode):
        import threading

        self.target = target
        self.mode = mode
        self.exists = Path.exists
        self.open = Path.open
        self.barrier = threading.Barrier(2, timeout=15)
        self.writing = threading.Event()
        self.release = threading.Event()
        self.events = []

    def checked_exists(self, path):
        import threading

        result = self.exists(path)
        if path == self.target and threading.current_thread().name.startswith("init-"):
            self.events.append({"operation": "exists", "result": result})
            if self.mode == "simultaneous" and not result:
                self.barrier.wait()
        return result

    def checked_open(self, path, *args, **kwargs):
        import threading

        try:
            stream = self.open(path, *args, **kwargs)
        except OSError as exc:
            self.events.append(
                {"operation": "open", "path": str(path), "error": repr(exc)}
            )
            raise
        if (
            self.mode == "partial"
            and path.parent == self.target.parent
            and args[:1] == ("xb",)
            and threading.current_thread().name == "init-writer"
        ):
            owner = self

            class PausedNativeWriter:
                def fileno(self):
                    return stream.fileno()

                def __enter__(self):
                    stream.__enter__()
                    return self

                def write(self, content):
                    midpoint = len(content) // 2
                    stream.write(content[:midpoint])
                    stream.flush()
                    owner.events.append(
                        {"operation": "partial-write", "path": str(path)}
                    )
                    owner.writing.set()
                    if not owner.release.wait(15):
                        raise TimeoutError("No se liberó el escritor nativo")
                    stream.write(content[midpoint:])
                    return len(content)

                def __exit__(self, *exc):
                    return stream.__exit__(*exc)

            return PausedNativeWriter()
        return stream


@pytest.fixture(autouse=True)
def archive_native_text_child_bytes(monkeypatch):
    """Conserva bytes antes de decodificar los helpers históricos, sin cambiar su AST."""
    import hashlib
    import locale
    import uuid

    original = subprocess.run

    def recorded_run(argv, **options):
        if not (options.get("capture_output") and options.get("text")):
            return original(argv, **options)
        path = Path(options["cwd"])
        folder = (
            Path(os.environ["STUDIO_TEST_ROOT"]).parent
            / "native-byte-receipts"
            / uuid.uuid4().hex
        )
        folder.mkdir(parents=True)
        manifest = {
            source.relative_to(path).as_posix(): hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            for source in path.rglob("*")
            if source.is_file()
        }
        (folder / "before.json").write_text(
            json.dumps(
                {
                    "utc": datetime.now(UTC).isoformat(),
                    "argv": argv,
                    "cwd": str(path),
                    "manifest": manifest,
                },
                indent=2,
            )
        )
        binary_options = {
            k: v for k, v in options.items() if k not in {"text", "encoding", "errors"}
        }
        result = original(argv, **binary_options)
        (folder / "stdout-original.bin").write_bytes(result.stdout)
        (folder / "stderr-original.bin").write_bytes(result.stderr)
        (folder / "after.json").write_text(
            json.dumps(
                {"utc": datetime.now(UTC).isoformat(), "exit": result.returncode},
                indent=2,
            )
        )
        encoding = options.get("encoding") or locale.getpreferredencoding(False)
        errors = options.get("errors") or "strict"
        result.stdout = (
            result.stdout.decode(encoding, errors)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
        result.stderr = (
            result.stderr.decode(encoding, errors)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )
        return result

    monkeypatch.setattr(subprocess, "run", recorded_run)


@pytest.mark.skipif(os.name != "nt", reason="Filesystem Windows nativo")
@pytest.mark.parametrize("mode", ["simultaneous", "partial"])
def test_native_concurrent_initializers_publish_complete_launcher(
    cli, tmp_path, monkeypatch, mode
):
    import threading

    assert (tmp_path / ".studio-test-owner").is_file()
    tools = {"node": {"dest": tmp_path / "node"}}
    expected_env = cli.environment(tmp_path, tools)
    target = tmp_path / ".cache/web-runtime/bin/pnpm.cmd"
    expected = target.read_bytes()
    # Configuraciones legítimas completas antes de comenzar; shim ausente.
    configs = {
        name: (tmp_path / ".cache/web-runtime" / name).read_bytes()
        for name in ("user.npmrc", "global.npmrc")
    }
    target.unlink()
    assert not target.exists()
    native = NativeWindowsFS(target, mode)
    monkeypatch.setattr(Path, "exists", lambda path: native.checked_exists(path))
    monkeypatch.setattr(
        Path,
        "open",
        lambda path, *args, **kwargs: native.checked_open(path, *args, **kwargs),
    )
    results, errors = [], []

    def initialize():
        try:
            results.append(cli.environment(tmp_path, tools))
        except (OSError, ValueError, threading.BrokenBarrierError) as exc:
            errors.append(repr(exc))

    writer = threading.Thread(target=initialize, name="init-writer", daemon=True)
    reader = threading.Thread(target=initialize, name="init-reader", daemon=True)
    try:
        writer.start()
        if mode == "partial":
            assert native.writing.wait(15), "No se alcanzó la escritura real"
        reader.start()
        if mode == "partial":
            reader.join(15)
            assert not reader.is_alive(), "Inicialización lectora bloqueada"
        else:
            writer.join(20)
            reader.join(20)
    finally:
        native.release.set()
        native.barrier.abort()
        writer.join(20)
        if reader.ident is not None:
            reader.join(20)
        folder = Path(os.environ["STUDIO_TEST_ROOT"]).parent / "race-receipts"
        folder.mkdir(exist_ok=True)
        (folder / (tmp_path.name + ".json")).write_text(
            json.dumps(
                {
                    "utc": datetime.now(UTC).isoformat(),
                    "root": str(tmp_path),
                    "mode": mode,
                    "events": native.events,
                    "errors": errors,
                    "successes": len(results),
                    "threads_terminated": not writer.is_alive()
                    and not reader.is_alive(),
                },
                indent=2,
            )
        )
    assert not writer.is_alive() and not reader.is_alive()
    assert errors == [], errors
    assert results == [expected_env, expected_env]
    assert target.read_bytes() == expected
    assert target.lstat().st_nlink == 1
    assert not getattr(target.lstat(), "st_file_attributes", 0) & 0x400
    for name, content in configs.items():
        assert (tmp_path / ".cache/web-runtime" / name).read_bytes() == content


@pytest.mark.skipif(os.name != "nt", reason="rename Windows sin reemplazo")
@pytest.mark.parametrize(
    "kind", ["valid", "wrong", "partial", "hardlink", "directory", "junction"]
)
def test_native_publication_validates_concurrent_winner(
    cli, tmp_path, monkeypatch, kind
):
    target = tmp_path / ".cache/web-runtime/bin/pnpm.cmd"
    target.parent.mkdir(parents=True)
    content = b"complete expected launcher\r\n"
    foreign = tmp_path / "foreign"
    foreign.write_bytes(content)
    actual_rename = os.rename
    errors = []
    temporaries = []

    def creator_wins(source, destination):
        assert destination == target
        assert source.parent == target.parent
        assert source.read_bytes() == content
        assert source.lstat().st_nlink == 1
        temporaries.append(source)
        if kind == "hardlink":
            os.link(foreign, target)
        elif kind == "directory":
            target.mkdir()
        elif kind == "junction":
            import _winapi

            directory = tmp_path / "foreign-directory"
            directory.mkdir()
            _winapi.CreateJunction(str(directory), str(target))
        else:
            target.write_bytes(
                content
                if kind == "valid"
                else content[:5]
                if kind == "partial"
                else b"foreign"
            )
        try:
            return actual_rename(source, destination)
        except OSError as exc:
            errors.append(type(exc).__name__)
            raise

    monkeypatch.setattr(os, "rename", creator_wins)
    try:
        if kind == "valid":
            assert cli._write_launcher(tmp_path, target, content) == target
            assert target.read_bytes() == content
        else:
            with pytest.raises(ValueError):
                cli._write_launcher(tmp_path, target, content)
            if kind in {"wrong", "partial", "hardlink"}:
                assert target.read_bytes() == (
                    content
                    if kind == "hardlink"
                    else content[:5]
                    if kind == "partial"
                    else b"foreign"
                )
            else:
                assert target.is_dir()
        assert errors == ["FileExistsError"]
        assert foreign.read_bytes() == content
        assert len(temporaries) == 1 and not temporaries[0].exists()
    finally:
        if kind == "junction":
            target.rmdir()
        elif kind == "hardlink":
            target.unlink()


@pytest.mark.skipif(os.name != "nt", reason="Identidad nativa del temporal")
def test_native_cleanup_preserves_swapped_temporary(cli, tmp_path, monkeypatch):
    target = tmp_path / ".cache/web-runtime/bin/pnpm.cmd"
    target.parent.mkdir(parents=True)
    content = b"complete expected launcher"
    actual_rename = os.rename
    swapped = []

    def swap_temporary(source, destination):
        # Conserva el original con su identidad para impedir reutilización del inode.
        original = source.with_suffix(".saved")
        actual_rename(source, original)
        source.write_bytes(b"foreign temporary")
        destination.write_bytes(content)
        swapped.extend((source, original))
        return actual_rename(source, destination)

    monkeypatch.setattr(os, "rename", swap_temporary)
    with pytest.raises(ValueError, match="Temporal cambiado"):
        cli._write_launcher(tmp_path, target, content)
    assert swapped[0].read_bytes() == b"foreign temporary"
    assert swapped[1].read_bytes() == content
    assert target.read_bytes() == content


@pytest.mark.skipif(os.name != "nt", reason="pnpm y filesystem Windows nativos")
def test_native_concurrent_initialization_then_official_nested_commands(
    cli, nested_project
):
    import threading

    tools = cli.verified_tools(nested_project)
    expected_env = cli.environment(nested_project, tools)
    target = nested_project / ".cache/web-runtime/bin/pnpm.cmd"
    expected = target.read_bytes()
    target.unlink()
    assert not target.exists()
    assert (nested_project.parent / ".studio-test-owner").is_file()
    barrier = threading.Barrier(3, timeout=15)
    results, errors = [], []

    def initialize():
        try:
            barrier.wait()
            results.append(cli.environment(nested_project, tools))
        except (OSError, ValueError, threading.BrokenBarrierError) as exc:
            errors.append(repr(exc))

    threads = [threading.Thread(target=initialize, daemon=True) for _ in range(2)]
    try:
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(20)
    finally:
        barrier.abort()
        for thread in threads:
            if thread.ident is not None:
                thread.join(20)
    assert all(not thread.is_alive() for thread in threads)
    assert errors == [], errors
    assert results == [expected_env, expected_env]
    assert target.read_bytes() == expected
    assert not list(target.parent.glob(".pnpm-*.tmp"))
    out = nested_native(nested_project, ["gen"])
    assert out.returncode == 0, out.stdout + out.stderr
    web = nested_project / "apps/web"
    (web / "exit.txt").write_text("37")
    arguments = ["two words", "español", "`literal`"]
    out = nested_native(nested_project, ["gen", "--", *arguments])
    assert out.returncode == 37, out.stdout + out.stderr
    result = json.loads((web / "result.json").read_text(encoding="utf-8"))
    assert result["argv"] == ["--", *arguments]
    assert result["node"] == str(tools["node"]["dest"] / "node.exe")
    assert "FOREIGN_MANAGER_EXECUTED" not in out.stdout
    assert target.read_bytes() == expected
