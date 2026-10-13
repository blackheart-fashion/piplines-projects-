import json
import subprocess
from unittest.mock import Mock

import pytest

from scripts import deploy, preflight, smoke


def test_preflight_without_docker(monkeypatch):
    monkeypatch.setattr(preflight.shutil, "which", lambda _: None)
    result = preflight.inspect()
    assert result["ok"] is False
    assert result["checks"][1]["ok"] is False


def test_preflight_daemon_failure(monkeypatch):
    monkeypatch.setattr(preflight.subprocess, "run", lambda *a, **k: Mock(returncode=1))
    assert preflight.inspect(True)["checks"][-1]["ok"] is False


def test_preflight_missing_docker(monkeypatch):
    monkeypatch.setattr(preflight.subprocess, "run", Mock(side_effect=FileNotFoundError))
    assert preflight.inspect(True)["checks"][-1]["ok"] is False


def test_smoke_http_roundtrip(monkeypatch):
    import io

    responses = [{"status": "ok"}, {"version": "v1"}, []]
    monkeypatch.setattr(
        smoke.urllib.request, "urlopen",
        lambda *a, **k: io.BytesIO(json.dumps(responses.pop(0)).encode()),
    )
    assert smoke.check("http://example", "v1", attempts=1)["tasks"] == []


def test_smoke_retries_and_fails(monkeypatch):
    request = Mock(side_effect=OSError("connection refused"))
    monkeypatch.setattr(smoke.urllib.request, "urlopen", request)
    monkeypatch.setattr(smoke.time, "sleep", lambda _: None)
    with pytest.raises(RuntimeError, match="after 2 attempts"):
        smoke.check("http://example", attempts=2)
    assert request.call_count == 2


def fake_host(monkeypatch, existing, failure_at=None):
    commands = []
    containers = set(existing)

    def command(*args, required=True):
        commands.append(args)
        output = "sha256:new\n" if args[:2] == ("image", "inspect") else ""
        rc = 0
        if args[:2] == ("container", "inspect"):
            rc = 0 if args[2] in containers else 1
        elif args[0] == "inspect":
            output = "sha256:old\n"
        elif args[0] == "run":
            containers.add(args[args.index("--name") + 1])
        elif args[0] == "rename":
            containers.remove(args[1])
            containers.add(args[2])
        elif args[0] == "rm":
            containers.discard(args[-1])
        return subprocess.CompletedProcess(args, rc, output, "")

    checks = Mock(side_effect=failure_at) if failure_at else Mock(return_value={})
    monkeypatch.setattr(deploy, "docker", command)
    monkeypatch.setattr(deploy, "check", checks)
    return commands, containers


def test_first_release(monkeypatch, tmp_path):
    commands, containers = fake_host(monkeypatch, [])
    assert deploy.deploy("api:v1", "v1", tmp_path / "report.json")["ok"]
    assert deploy.LIVE in containers
    assert deploy.CANDIDATE not in containers
    runs = [args for args in commands if args[0] == "run"]
    assert all(args[-1] == "sha256:new" for args in runs)


def test_failed_candidate_keeps_live(monkeypatch, tmp_path):
    commands, containers = fake_host(monkeypatch, [deploy.LIVE], [RuntimeError("bad")])
    report = tmp_path / "report.json"
    with pytest.raises(RuntimeError):
        deploy.deploy("api:v2", "v2", report)
    assert ("stop", deploy.LIVE) not in commands
    assert deploy.LIVE in containers
    assert deploy.CANDIDATE not in containers
    assert json.loads(report.read_text())["ok"] is False


def test_failed_cutover_restores_previous(monkeypatch, tmp_path):
    commands, containers = fake_host(
        monkeypatch, [deploy.LIVE], [{}, RuntimeError("live bad"), {}],
    )
    report = tmp_path / "report.json"
    with pytest.raises(RuntimeError):
        deploy.deploy("api:v2", "v2", report)
    assert ("start", deploy.LIVE) in commands
    assert deploy.LIVE in containers
    assert deploy.PREVIOUS not in containers
    assert json.loads(report.read_text())["events"][-1]["action"] == "previous_release_restored"


def test_recovery_failure_is_reported(monkeypatch, tmp_path):
    fake_host(monkeypatch, [deploy.LIVE], [{}, RuntimeError("live"), RuntimeError("old")])
    report = tmp_path / "report.json"
    with pytest.raises(RuntimeError):
        deploy.deploy("api:v2", "v2", report)
    assert json.loads(report.read_text())["events"][-1]["action"] == "recovery_failed"


def test_existing_candidate_is_not_deleted(monkeypatch, tmp_path):
    commands, _ = fake_host(monkeypatch, [deploy.CANDIDATE])
    with pytest.raises(RuntimeError, match="already exists"):
        deploy.deploy("api:v1", "v1", tmp_path / "report.json")
    assert not any(args[0] == "rm" for args in commands)


@pytest.mark.parametrize("responses", [
    [{"status": "bad"}, {"version": "v1"}, []],
    [{"status": "ok"}, {"version": "v2"}, []],
    [{"status": "ok"}, {"version": "v1"}, {}],
])
def test_smoke_rejects_bad_payloads(monkeypatch, responses):
    import io

    monkeypatch.setattr(
        smoke.urllib.request, "urlopen",
        lambda *a, **k: io.BytesIO(json.dumps(responses.pop(0)).encode()),
    )
    with pytest.raises(RuntimeError):
        smoke.check("http://example", "v1", attempts=1)


def test_docker_failure_propagates(monkeypatch):
    monkeypatch.setattr(
        deploy.subprocess, "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "daemon unavailable"),
    )
    with pytest.raises(RuntimeError, match="daemon unavailable"):
        deploy.docker("info")
    assert deploy.docker("info", required=False).returncode == 1


def test_same_image_is_verified_without_cutover(monkeypatch, tmp_path):
    commands, _ = fake_host(monkeypatch, [deploy.LIVE])
    original = deploy.docker

    def same_image(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[0] == "inspect":
            result.stdout = "sha256:new\n"
        return result

    monkeypatch.setattr(deploy, "docker", same_image)
    report = deploy.deploy("api:v1", "v1", tmp_path / "report.json")
    assert report["events"][-1]["action"] == "already_deployed"
    assert not any(args[0] in ("run", "stop") for args in commands)


def test_failed_rename_restarts_original_container(monkeypatch, tmp_path):
    commands, _ = fake_host(monkeypatch, [deploy.LIVE, deploy.PREVIOUS])
    original = deploy.docker

    def failed_rename(*args, **kwargs):
        if args[0] == "rename":
            raise RuntimeError("rename failed")
        return original(*args, **kwargs)

    monkeypatch.setattr(deploy, "docker", failed_rename)
    with pytest.raises(RuntimeError, match="rename failed"):
        deploy.deploy("api:v2", "v2", tmp_path / "report.json")
    assert ("start", deploy.LIVE) in commands
