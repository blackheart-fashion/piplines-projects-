"""Report prerequisites without revealing credentials or modifying the host."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def inspect(require_docker=False):
    checks = [{"name": "python >= 3.12", "ok": sys.version_info >= (3, 12)}]
    checks.append({"name": "git installed", "ok": shutil.which("git") is not None})
    if require_docker:
        try:
            result = subprocess.run(
                ["docker", "info", "--format", "{{.ServerVersion}}"],
                capture_output=True, text=True, timeout=15,
            )
            checks.append({"name": "Docker daemon reachable", "ok": result.returncode == 0})
        except (OSError, subprocess.TimeoutExpired):
            checks.append({"name": "Docker daemon reachable", "ok": False})
    return {"ok": all(item["ok"] for item in checks), "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker", action="store_true")
    args = parser.parse_args()
    report = inspect(args.docker)
    Path("reports").mkdir(exist_ok=True)
    Path("reports/preflight.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["ok"] else 1)
