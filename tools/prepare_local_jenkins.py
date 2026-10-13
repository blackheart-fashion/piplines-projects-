"""Generate ignored local Jenkins secrets without printing tokens or passwords."""

import json
import secrets
import subprocess
from pathlib import Path


def github(*args):
    return subprocess.run(
        ["gh", *args], check=True, capture_output=True, text=True, timeout=30,
    ).stdout.strip()


def prepare():
    root = Path(__file__).resolve().parents[1]
    target = root / ".local-jenkins"
    target.mkdir(mode=0o700, exist_ok=True)
    username = github("api", "user", "--jq", ".login")
    password = target / "admin-password"
    if not password.exists():
        password.write_text(secrets.token_urlsafe(32), encoding="utf-8")
        password.chmod(0o600)
    (target / "github-token").write_text(github("auth", "token"), encoding="utf-8")
    (target / "github-token").chmod(0o600)
    (target / "github-user").write_text(username, encoding="utf-8")
    (target / "repo-url").write_text(
        f"https://github.com/{username}/jenkins-python-workshop.git", encoding="utf-8",
    )
    print(json.dumps({"user": username, "secrets_directory": str(target), "tokens_printed": False}))


if __name__ == "__main__":
    prepare()
