"""Single-host release with candidate verification and recovery after failed cutover.

Requires exclusive use of this host's workshop container names and ports.
No schema migration is performed; old and new applications must share a compatible schema.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.smoke import check
except ModuleNotFoundError:
    from smoke import check

LIVE = "workshop-api"
CANDIDATE = "workshop-api-candidate"
PREVIOUS = "workshop-api-previous"


def docker(*args, required=True):
    result = subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=120,
    )
    if required and result.returncode:
        raise RuntimeError(f"docker {args[0]} failed: {result.stderr.strip()}")
    return result


def exists(name):
    return docker("container", "inspect", name, required=False).returncode == 0


def launch(name, image_id, port, volume=None):
    args = ["run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:8000"]
    if volume:
        args += ["--mount", f"type=volume,src={volume},dst=/data", "--restart", "unless-stopped"]
    docker(*args, image_id)


def deploy(image, version, report_path="reports/deployment.json"):
    report = {"image": image, "version": version, "events": [], "ok": False}

    def event(action, **details):
        item = {"at": datetime.now(timezone.utc).isoformat(), "action": action, **details}
        report["events"].append(item)
        print(json.dumps(item), flush=True)

    replaced = False
    live_created = False
    try:
        docker("info")
        # Resolve a tag once. Candidate and live use the exact same local image ID.
        image_id = docker("image", "inspect", "--format", "{{.Id}}", image).stdout.strip()
        report["image_id"] = image_id
        event("image_resolved", image_id=image_id)
        if exists(CANDIDATE):
            raise RuntimeError("candidate container already exists; inspect it before retrying")
        if exists(LIVE):
            current_id = docker("inspect", "--format", "{{.Image}}", LIVE).stdout.strip()
            if current_id == image_id:
                check("http://127.0.0.1:8000", version)
                event("already_deployed")
                report["ok"] = True
                return report
        try:
            launch(CANDIDATE, image_id, 18080)
            check("http://127.0.0.1:18080", version)
            event("candidate_verified")
        except Exception:
            logs = docker("logs", "--tail", "50", CANDIDATE, required=False)
            event("candidate_failed", logs=logs.stdout + logs.stderr)
            raise
        finally:
            docker("rm", "-f", CANDIDATE, required=False)

        if exists(LIVE):
            if exists(PREVIOUS):
                docker("rm", "-f", PREVIOUS)
            docker("stop", LIVE)
            # If rename fails, restore service under its original name immediately.
            try:
                docker("rename", LIVE, PREVIOUS)
            except Exception:
                docker("start", LIVE)
                raise
            replaced = True
            event("previous_release_retained")
        # Mark before running: docker run can create a container before returning failure.
        live_created = True
        launch(LIVE, image_id, 8000, "workshop-data")
        check("http://127.0.0.1:8000", version)
        event("live_verified")
        report["ok"] = True
        return report
    except Exception as error:
        event("release_failed", error=str(error))
        if live_created:
            logs = docker("logs", "--tail", "50", LIVE, required=False)
            event("live_failure_logs", logs=logs.stdout + logs.stderr)
            docker("rm", "-f", LIVE, required=False)
        if replaced:
            try:
                docker("rename", PREVIOUS, LIVE)
                docker("start", LIVE)
                check("http://127.0.0.1:8000")
                event("previous_release_restored")
            except Exception as recovery_error:
                event("recovery_failed", error=str(recovery_error))
        raise
    finally:
        target = Path(report_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        deploy(args.image, args.version)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
