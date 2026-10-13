"""Read-only Jenkins change detection for chat monitoring; saves an ignored baseline."""

import json
import re
import sys
import urllib.error
from pathlib import Path

from jenkins_local import URL, connect

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".local-jenkins" / "monitor-state.json"


def snapshot():
    opener = connect()
    query = '/api/json?tree=jobs[name,lastBuild[number,result,building]]'
    with opener.open(URL + query, timeout=15) as response:
        jobs = json.load(response)["jobs"]
    state = {"reachable": True, "jobs": {}}
    for job in jobs:
        if job["name"] not in {"workshop-day1", "workshop-day2"}:
            continue
        build = job["lastBuild"]
        if not build:
            continue
        number = build["number"]
        build_url = f"{URL}/job/{job['name']}/{number}/"
        with opener.open(build_url + 'consoleText', timeout=15) as response:
            console = response.read().decode()
        stages = re.findall(r'\[Pipeline\] \{ \(([^\n]+)\)', console)
        release_events = re.findall(r'"action":\s*"([a-z_]+)"', console)
        state["jobs"][job["name"]] = {
            "number": number, "result": build["result"], "building": build["building"],
            "latest_stage": stages[-1] if stages else None,
            "release_events": list(dict.fromkeys(release_events)), "url": build_url,
            "approval_pending": bool(build["building"] and stages
                                     and stages[-1] == "Approve release" and not release_events),
        }
    return state


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        current = snapshot()
    except (OSError, urllib.error.URLError):
        current = {"reachable": False, "jobs": {}}
    previous = json.loads(BASELINE.read_text()) if BASELINE.exists() else None
    changes = []
    if previous is not None:
        if current["reachable"] != previous["reachable"]:
            changes.append({"controller_reachable": current["reachable"]})
        if current["reachable"]:
            for name, state in current["jobs"].items():
                if state != previous.get("jobs", {}).get(name):
                    changes.append({"job": name, **state})
    BASELINE.parent.mkdir(exist_ok=True)
    BASELINE.write_text(json.dumps(current, indent=2), encoding="utf-8")
    print(json.dumps({"initialized": previous is None, "changes": changes}, indent=2))


if __name__ == "__main__":
    main()
