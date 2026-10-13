"""Instructor dry run: replaces only the workshop containers on a disposable host.

Requires three images with versions validation-1, validation-2, and validation-bad.
The third image must be built with DEMO_BROKEN=1. Do not run on a shared deployment host.
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import deploy  # noqa: E402
from scripts.smoke import check  # noqa: E402


def expected_failure(image, version, report):
    try:
        deploy.deploy(image, version, report)
    except RuntimeError:
        return json.loads(Path(report).read_text())
    raise AssertionError("expected the release attempt to fail")


def verify():
    deploy.deploy("workshop/task-api:validation-1", "validation-1", "reports/release-v1.json")
    request = urllib.request.Request(
        "http://127.0.0.1:8000/tasks",
        data=json.dumps({"title": "validation persistence marker"}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        task_id = json.load(response)["id"]
    deploy.deploy("workshop/task-api:validation-2", "validation-2", "reports/release-v2.json")
    result = check("http://127.0.0.1:8000", "validation-2")
    assert any(task["id"] == task_id for task in result["tasks"]), "task data lost"
    report = expected_failure(
        "workshop/task-api:validation-bad", "validation-bad", "reports/release-bad.json",
    )
    assert any(event["action"] == "candidate_failed" for event in report["events"])
    check("http://127.0.0.1:8000", "validation-2")
    original_launch = deploy.launch
    original_check = deploy.check

    def inject_live_failure(name, image_id, port, volume=None):
        if name != deploy.LIVE:
            return original_launch(name, image_id, port, volume)
        deploy.docker(
            "run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:8000",
            "--mount", f"type=volume,src={volume},dst=/data",
            "--env", "DEMO_BROKEN=1", image_id,
        )

    def quicker_check(url, version=None):
        return original_check(url, version, attempts=8, delay=0.5)

    deploy.launch = inject_live_failure
    deploy.check = quicker_check
    try:
        report = expected_failure(
            "workshop/task-api:validation-1", "validation-1", "reports/release-recovery.json",
        )
    finally:
        deploy.launch = original_launch
        deploy.check = original_check
    assert any(event["action"] == "previous_release_restored" for event in report["events"])
    result = check("http://127.0.0.1:8000", "validation-2")
    assert any(task["id"] == task_id for task in result["tasks"])
    summary = {
        "healthy_release": True, "persistent_data": True,
        "bad_candidate_rejected": True, "real_container_recovery": True,
        "running_version": result["version"]["version"],
    }
    Path("reports/container-validation.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    verify()
