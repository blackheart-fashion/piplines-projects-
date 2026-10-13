"""Bounded retries and read-only HTTP checks; no third-party dependencies."""

import argparse
import json
import time
import urllib.error
import urllib.request


def check(base_url, expected_version=None, attempts=15, delay=2):
    last_error = None
    for attempt in range(attempts):
        try:
            results = {}
            for endpoint in ("health", "version", "tasks"):
                with urllib.request.urlopen(f"{base_url.rstrip('/')}/{endpoint}", timeout=3) as r:
                    results[endpoint] = json.load(r)
            if results["health"].get("status") != "ok":
                raise ValueError("health check did not return status=ok")
            if not isinstance(results["tasks"], list):
                raise ValueError("tasks response is not a list")
            if expected_version and results["version"].get("version") != expected_version:
                raise ValueError("running version does not match the requested release")
            return results
        except (OSError, ValueError, urllib.error.URLError) as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(delay)
    raise RuntimeError(f"smoke check failed after {attempts} attempts: {last_error}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--version")
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.url, args.version), indent=2))
    except RuntimeError as error:
        parser.exit(1, f"{error}\n")
