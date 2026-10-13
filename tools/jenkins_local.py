"""Local Jenkins API helper. Authentication remains in ignored files; no secret output."""

import argparse
import base64
import http.cookiejar
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8080"


def connect():
    password = (ROOT / ".local-jenkins" / "admin-password").read_text().strip()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
    )
    encoded = base64.b64encode(f"workshop-admin:{password}".encode()).decode()
    opener.addheaders = [("Authorization", f"Basic {encoded}")]
    return opener


def post(opener, path, data=None):
    with opener.open(f"{URL}/crumbIssuer/api/json", timeout=15) as response:
        crumb = json.load(response)
    request = urllib.request.Request(
        URL + path, data=urllib.parse.urlencode(data or {}).encode(),
        headers={crumb["crumbRequestField"]: crumb["crumb"]}, method="POST",
    )
    with opener.open(request, timeout=30) as response:
        return response.read().decode(), response.headers.get("Location")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["status", "build", "console", "approve", "configure"])
    parser.add_argument(
        "--job", default="workshop-day1", choices=["workshop-day1", "workshop-day2"],
    )
    parser.add_argument("--number", type=int)
    parser.add_argument("--deploy", action="store_true")
    args = parser.parse_args()
    opener = connect()
    if args.action == "configure":
        script = (
            "jenkins.model.JenkinsLocationConfiguration.get()"
            ".setUrl('http://127.0.0.1:8080/'); println('Local root URL configured')"
        )
        print(post(opener, '/scriptText', {"script": script})[0])
        return
    if args.action == "status":
        path = '/api/json?tree=jobs[name,color,lastBuild[number,result,building]]'
        with opener.open(URL + path, timeout=15) as response:
            result = json.load(response)
            result["jenkins_version"] = response.headers.get("X-Jenkins")
        node_url = URL + '/computer/api/json?tree=computer[displayName,offline]'
        with opener.open(node_url, timeout=15) as r:
            result["nodes"] = json.load(r)["computer"]
        print(json.dumps(result, indent=2))
    elif args.action == "build":
        suffix = "buildWithParameters" if args.deploy else "build"
        data = {"DEPLOY": "true", "PUSH_IMAGE": "false", "INJECT_BAD_RELEASE": "false",
                "IMAGE_REPO": "workshop/task-api"} if args.deploy else {}
        _, location = post(opener, f"/job/{args.job}/{suffix}", data)
        print(json.dumps({"queued": True, "queue_url": location}))
    elif args.action == "console":
        number = args.number or "lastBuild"
        with opener.open(f"{URL}/job/{args.job}/{number}/consoleText", timeout=15) as r:
            print(r.read().decode()[-14000:])
    else:
        if not args.number:
            parser.error("--number is required for approval")
        # Local administrator action: approve this specific workshop build only.
        script = (
            "def b=jenkins.model.Jenkins.get().getItem('" + args.job + "')"
            ".getBuildByNumber(" + str(args.number) + "); "
            "def a=b.getAction(org.jenkinsci.plugins.workflow.support.steps.input.InputAction); "
            "def xs=a?.getExecutions(); "
            "if (!xs) { println('No pending approval'); } "
            "else { xs.each { it.proceed(null) }; println('Workshop release approved'); }"
        )
        body, _ = post(opener, '/scriptText', {"script": script})
        print(body)


if __name__ == "__main__":
    try:
        main()
    except (OSError, urllib.error.URLError) as error:
        raise SystemExit(f"Local Jenkins request failed: {error}") from error
