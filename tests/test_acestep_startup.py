"""Contrato conductual del entrypoint ACE mediante un shell POSIX real."""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ENTRYPOINT = Path(__file__).resolve().parents[1] / "apps/engines/acestep/entrypoint.sh"


@unittest.skipUnless(
    os.name == "posix" and shutil.which("sh"), "requiere shell POSIX real"
)
class AcestepStartupTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="acestep-startup-")
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.import_log = self.root / "premature-python.log"
        trap = self.root / "python"
        trap.write_text('#!/bin/sh\nprintf "%s\\n" "$*" > "$IMPORT_LOG"\nexit 97\n')
        trap.chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{self.root}{os.pathsep}{os.environ['PATH']}",
            "IMPORT_LOG": str(self.import_log),
        }

    def command(self, code, *args):
        return ["sh", str(ENTRYPOINT), sys.executable, "-c", code, *args]

    def test_pre_gate_startup_delegates_without_python_import(self):
        result = subprocess.run(
            self.command('print("preflight reached")'),
            env=self.env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertFalse(
            self.import_log.exists(),
            "entrypoint ejecutó Python antes de delegar al preflight",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "preflight reached\n")

    def test_preserves_arguments_exit_and_exec_pid(self):
        args = [
            "",
            "two words",
            "$(touch forbidden)",
            "; exit 1",
            "*",
            "quote'\"",
            "lírica",
        ]
        with subprocess.Popen(
            self.command(
                "import json,os,sys; print(json.dumps([os.getpid(),sys.argv[1:]])); sys.exit(23)",
                *args,
            ),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as child:
            stdout, stderr = child.communicate(timeout=10)
            self.assertEqual(child.returncode, 23, stderr)
            pid, observed_args = json.loads(stdout)
            self.assertEqual(observed_args, args)
            self.assertEqual(pid, child.pid, "el shell debe reemplazarse mediante exec")
        self.assertFalse(self.import_log.exists())

    def test_term_reaches_delegated_process(self):
        ready = self.root / "ready"
        code = (
            "import pathlib,signal,sys,time; "
            "signal.signal(signal.SIGTERM, lambda *_: sys.exit(42)); "
            "pathlib.Path(sys.argv[1]).write_text('ready'); time.sleep(30)"
        )
        with subprocess.Popen(
            self.command(code, str(ready)),
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as child:
            try:
                import time

                deadline = time.monotonic() + 10
                while (
                    not ready.exists()
                    and child.poll() is None
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.01)
                self.assertTrue(
                    ready.exists(), "el comando delegado no llegó a estar preparado"
                )
                child.send_signal(signal.SIGTERM)
                child.communicate(timeout=5)
                self.assertEqual(child.returncode, 42)
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate(timeout=5)
        self.assertFalse(self.import_log.exists())


if __name__ == "__main__":
    unittest.main()
