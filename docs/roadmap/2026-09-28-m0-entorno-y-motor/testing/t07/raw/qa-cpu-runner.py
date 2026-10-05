"""Official pytest runner with a retained, anonymized receipt (no GPU)."""

import json
import os
import subprocess
import sys
from pathlib import Path

root = Path.cwd()
out = root / "docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t07/raw"
cmd = [
    str(root / ".venv/Scripts/python.exe"),
    "-m",
    "pytest",
    "packages/weights/tests",
    "packages/engine-contract/tests",
    "packages/audio-post/tests",
    "apps/engines/common/tests",
    "apps/engines/mock/tests",
    "tests",
    "apps/engines/acestep/tests",
    "-m",
    "not gpu",
    "-q",
    "--tb=short",
    "--cov=.",
    "--cov-report=json",
    "--basetemp=.cache/pytest/t07-qa",
    "-o",
    "cache_dir=.cache/pytest/cache",
]
env = os.environ.copy()
env["COVERAGE_FILE"] = str(root / ".cache/dev-cycle/t07/qa/qa.coverage")
env["CUDA_VISIBLE_DEVICES"] = ""
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    env=env,
    check=False,
)


def scrub(value):
    for path in [str(root), str(Path.home())]:
        for variant in [path.replace("\\", "\\\\"), path, path.replace("\\", "/")]:
            value = value.replace(
                variant, "<workspace>" if path == str(root) else "<user>"
            )
    return value


(out / "qa-cpu-tests.log").write_text(
    scrub(result.stdout + result.stderr) + f"\nEXIT={result.returncode}\n",
    encoding="utf-8",
)
(out / "qa-cpu-command.json").write_text(
    json.dumps(
        {
            "command": [scrub(c) for c in cmd],
            "CUDA_VISIBLE_DEVICES": "",
            "COVERAGE_FILE": ".cache/dev-cycle/t07/qa/qa.coverage",
            "exit": result.returncode,
        },
        indent=2,
    ),
    encoding="utf-8",
)
if (root / "coverage.json").exists():
    (out / "qa-coverage.json").write_text(
        scrub((root / "coverage.json").read_text(encoding="utf-8")), encoding="utf-8"
    )
sys.exit(result.returncode)
