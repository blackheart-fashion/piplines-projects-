# Teacher runbook: what to explain and execute, and when

Use this beside the Day 1 and Day 2 student guides. Those guides contain the longer
theory cards and platform alternatives; this chapter is the instructor's live sequence.
Both days run 09:30-16:00, including 60 minutes of breaks. Commands below use Bash on
the prepared Linux lab host. Run them from the repository root. Keep Terminal A for the
Day 1 server and Terminal B for commands. Every pair has a separate Docker host.

## Before students arrive

Complete `00-setup.md`, including Jenkins plugins, the online Linux agent, and Python
dependencies. Installations and account registration belong before class. Use a teacher
fork for demonstration commits and one fork per pair for student commits. Everyone can
read the public reference repository without an account; pushing requires their own fork
and GitHub sign-in. Never have students push practice bugs into the reference repository.

On each participant's prepared Linux host, after installing GitHub CLI and signing in:

```bash
gh auth status
gh repo fork Siddhantji/jenkins-python-workshop --clone
cd jenkins-python-workshop
git remote -v
git status
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/preflight.py --docker
```

Confirm `origin` is the participant's fork and `upstream`, if present, is the reference.
If a fork already exists, clone its URL rather than creating another. If the folder
already exists, enter it and inspect its remotes rather than cloning over it. Configure
Git author name/email before the first commit using the participant's own identity.
Jenkins must point to the fork when testing that pair's changes.

Check Jenkins: controller executors = 0; agent online with the correct label; pair jobs
use that agent. On a shared controller, give every pair a distinct label and update their
Jenkinsfiles. One deployment job owns each Docker host. Download the handout and pre-pull
the base images so a slow classroom connection does not consume the practical session.

The teacher should rehearse a passing CI build and deployment on their own host. Keep a
known-good reference checkout available for pairs needing help. Do not run competing
teacher and student deployments against the same Docker names/ports.

## Day 1, 09:30-10:00: introduce CI and check readiness

**Say:** "A commit identifies code. A build is one execution of checks on that code.
The controller coordinates; the agent runs our commands. A failed required check must
stop later delivery, while its reports remain available."

Draw `commit -> checkout -> dependencies -> lint -> tests -> reports`. Ask students to
predict where a syntax error, wrong assertion, and offline agent will appear. Use Day 1
theory card 1 for CI versus delivery versus deployment.

**Terminal B, execute:**

```bash
pwd
git status
.venv/bin/python --version
.venv/bin/python scripts/preflight.py
```

**Look for:** repository root, a clean starting tree, the prepared interpreter, successful
preflight. A missing `.venv` means setup was skipped. A missing Git executable belongs to
host preparation. Resolve these before application debugging. Give students five minutes
to repeat the checks and identify where their Jenkins agent actually runs.

## Day 1, 10:00-10:45: explain and demonstrate the application

**Explain in this order:** `app/service.py` pure validation; `app/api.py` app factory;
SQLite connection lifetime; parameterized SQL; health versus version. Ask why tests
should use their own database instead of the developer's file.

**Terminal A, start the development server:**

```bash
.venv/bin/python -m flask --app app.api:create_app run --host 127.0.0.1 --port 8000
```

**Terminal B, inspect and create a task:**

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/version
TASK_JSON=$(curl -fsS -X POST http://127.0.0.1:8000/tasks -H 'Content-Type: application/json' -d '{"title":"  Teach Jenkins  "}')
printf '%s\n' "$TASK_JSON"
TASK_ID=$(printf '%s' "$TASK_JSON" | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -fsS -X PATCH "http://127.0.0.1:8000/tasks/$TASK_ID" -H 'Content-Type: application/json' -d '{"done":true}'
curl -fsS http://127.0.0.1:8000/tasks
curl -i -X POST http://127.0.0.1:8000/tasks -H 'Content-Type: application/json' -d '{"title":"   "}'
```

**Look for:** health `ok`, version `dev`, trimmed title, correct returned ID, boolean
completion, HTTP 400 for the blank title. The last call deliberately uses `-i` rather
than `-f` so students can inspect the error response. An occupied port requires identifying
the existing process; connection refusal means the server is not listening at that URL.
Never assume a fresh database starts at task ID 1.

Use the final ten minutes for pairs to explain one route to their partner. Break 10:45-11:00.

## Day 1, 11:00-12:15: students write and reason about tests

**Say:** "The Flask test client runs inside Python; it is not a network smoke test.
Our fixture creates a temporary database. Assertions, not simply executing lines, protect
the behavior we want." Read `application`, `client`, and `test_normalize_title` together.

**Terminal B, execute:**

```bash
.venv/bin/python -m pytest tests/test_api.py -v
.venv/bin/python -m pytest tests/test_api.py -k invalid_title -v
.venv/bin/python -m pytest tests/test_api.py -k persistence -v
```

Give pairs 35 minutes to write a new test, predict its outcome, run it, and explain the
failure it would detect. Boundary cases already exist in the reference; require a new
assertion or behavior instead of copying one unchanged. Example new file
`tests/test_student.py`:

```python
from app.service import normalize_title


def test_unicode_title_preserves_text():
    assert normalize_title("  Learn DevOps café  ") == "Learn DevOps café"
```

```bash
.venv/bin/python -m pytest tests/test_student.py -v
```

Expected: the new test passes and the accented character remains intact. As a deliberate red exercise,
change only the expected output to include the leading spaces; the test should fail.
Restore the correct assertion afterwards. Ask each pair to name the input, expected
output, and rule being tested. Missing pytest means dependencies were installed into a
different interpreter; always use `.venv/bin/python -m ...`.

At 12:15, require a responding API and one explained student test. If behind, run a
selected test and discuss its assertion before moving to the full gate.

## Day 1, 12:15-13:00: turn checks into a quality gate

**Say:** "Lint checks code patterns; tests check behavior; coverage shows execution.
Coverage does not prove good assertions. Jenkins acts on exit codes and keeps evidence."

```bash
.venv/bin/python -m ruff check app scripts tests
.venv/bin/python -m pytest --junitxml=reports/junit.xml --cov=app --cov=scripts --cov-report=xml:reports/coverage.xml --cov-report=term-missing --cov-fail-under=80
ls reports
```

Explain one uncovered line and open the XML reports. The unchanged reference suite has
39 tests and measured 88.41% coverage; student additions can change both values. Require
passing lint/tests and the 80% gate, rather than requiring that exact reference count.

Demonstrate an intentionally higher gate separately:

```bash
.venv/bin/python -m pytest --cov=app --cov=scripts --cov-fail-under=100
echo "$?"
```

Expected: the reference suite fails the 100% gate with a nonzero exit status. Execute
`echo` immediately after pytest so it reports that command's status. Restore the normal
80% command before proceeding; do not lower the gate to conceal a regression.
Lunch 13:00-13:45.

## Day 1, 13:45-14:45: build Jenkins CI in stages

Use the Jenkins UI sequence in Day 1 Lab 3. Name the pair's job `workshop-day1`; select
Pipeline from SCM, the pair's fork, branch `*/main`, script path
`pipelines/Jenkinsfile.day1`. Public checkout needs no GitHub token.

Have pairs work on `lab/ci-construction`, incrementally constructing the reference:

1. Agent label, timeout, concurrency option, explicit checkout. Build and locate commit.
2. Preparation stage with venv and dependency install. Build and find interpreter output.
3. Lint stage. Build and identify what a nonzero command would do.
4. Test stage with coverage and JUnit arguments. Build and inspect test results.
5. `post` sections for JUnit, archive, and cleanup. Build and download the reports.

```bash
git switch -c lab/ci-construction
```

After each edit, repeat this sequence with a meaningful stage-specific message:

```bash
git add pipelines/Jenkinsfile.day1
git commit -m "lab: add CI stage and evidence"
git push -u origin lab/ci-construction
```

Configure the practice job's branch to `*/lab/ci-construction` while constructing it.
Explain `sh` executes on the Linux agent, not in the student's browser. Waiting for an
executor means inspecting labels/agent availability before Python. A script-path error
means checking the SCM path. At 14:45, each pair must show Jenkins reports from the same
checks they ran locally. Review and merge their completed CI work into their fork's main.

## Day 1, 14:45-15:30: fail a build, investigate, then repair

From the pair's main branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c lab/day1-failure
```

In `app/service.py`, replace `title = value.strip()` with `title = value`. Ask students
to predict which test fails before running anything.

```bash
.venv/bin/python -m pytest tests/test_api.py -k normalize_title -v
git add app/service.py
git commit -m "lab: demonstrate whitespace regression"
git push -u origin lab/day1-failure
```

Use a separate practice job pointed to this branch. Find the failed test, expected/actual
value, and source commit in Jenkins. Restore `.strip()`, then:

```bash
.venv/bin/python -m pytest tests/test_api.py -k normalize_title -v
git add app/service.py
git commit -m "lab: restore whitespace validation"
git push
```

Build again and show green results. Keep the fault exercise on its practice branch.
If pushing fails, inspect `git remote -v` and account permissions; the public reference
does not grant students write access. Do not work around that by sharing an owner token.

## Day 1, 15:30-16:00: assess and leave a clean starting point

Each pair gets two minutes to show a good build, a failed build, their new test, and
one diagnosis. Use the rubric in `05-instructor.md`. Ask where commands execute and why
reports survive a failure. Before dismissal, restore the fork's main branch and stop
Terminal A's Flask server with Ctrl+C. Day 2 needs port 8000 free.

## Day 2, 09:30-10:00: recap and establish release identity

**Say:** "Today we deliver a tested image. The image, runtime configuration, and database
are separate. The approval gate makes this continuous delivery. A running process is
not enough: readiness and release version must match."

```bash
git switch main
git pull --ff-only origin main
.venv/bin/python scripts/preflight.py --docker
docker ps --format 'table {{.Names}}\t{{.Ports}}'
```

Verify the host belongs to this pair and no Day 1 server holds port 8000. Explain Day 2
theory cards 1 and 3: mutable tags, content IDs, volume persistence, and the limits of
application recovery. Reserve registry and Ansible for pairs finishing the core early.

## Day 2, 10:00-10:45: demonstrate build and real smoke checks

In Terminal B, keep this shell open: later commands reuse these variables.

```bash
RELEASE_VERSION="$(git rev-parse --short=12 HEAD)-manual-1"
IMAGE_REF="workshop/task-api:$RELEASE_VERSION"
docker build --build-arg APP_VERSION="$RELEASE_VERSION" -t "$IMAGE_REF" .
docker image inspect "$IMAGE_REF" --format '{{.Id}}'
docker run -d --name workshop-api-manual -p 127.0.0.1:8000:8000 "$IMAGE_REF"
.venv/bin/python scripts/smoke.py --url http://127.0.0.1:8000 --version "$RELEASE_VERSION"
docker logs --tail=50 workshop-api-manual
docker inspect workshop-api-manual --format '{{.Config.User}}'
docker rm -f workshop-api-manual
```

Look for the exact version and `appuser`. Explain Waitress, bounded retries, timeouts,
and checked subprocess exit codes using `scripts/smoke.py` and `scripts/deploy.py`.
Walk the release decision branches before executing delivery: resolve image, candidate,
cutover, live verification, report, possible recovery. The removal above frees port 8000
and affects only the named throwaway container. Break 10:45-11:00.

## Day 2, 11:00-12:15: pairs build, release, and prove persistence

Pairs repeat the preceding build/run/smoke/removal sequence on their hosts. After the
manual container has been removed, execute the following in order:

```bash
.venv/bin/python scripts/deploy.py --image "$IMAGE_REF" --version "$RELEASE_VERSION"
curl -fsS -X POST http://127.0.0.1:8000/tasks -H 'Content-Type: application/json' -d '{"title":"Must survive release"}'
RELEASE_VERSION="$(git rev-parse --short=12 HEAD)-manual-2"
IMAGE_REF="workshop/task-api:$RELEASE_VERSION"
docker build --build-arg APP_VERSION="$RELEASE_VERSION" -t "$IMAGE_REF" .
.venv/bin/python scripts/deploy.py --image "$IMAGE_REF" --version "$RELEASE_VERSION"
.venv/bin/python scripts/smoke.py --url http://127.0.0.1:8000 --version "$RELEASE_VERSION"
curl -fsS http://127.0.0.1:8000/tasks
```

Expected: the new version is live and the marker task survives. Explain the named
`workshop-data` volume and disposable candidate data. If an image is missing, inspect the
Docker host/context and tag; do not assume an image built on another host is available.
If permission is denied accessing Docker, fix the prepared user's access and start a new
login session as described in setup. Do not delete the volume to fix a release failure.

## Day 2, 12:15-13:00: trace automation and check idempotency

```bash
cat reports/deployment.json
docker ps --filter name=workshop-api
.venv/bin/python scripts/deploy.py --image "$IMAGE_REF" --version "$RELEASE_VERSION"
cat reports/deployment.json
.venv/bin/python -m pytest tests/test_automation.py -v
```

Expected repeated-release event: `already_deployed`, if the same content ID is healthy.
Have students point to the Python condition that makes that decision and explain why
the `finally` block writes evidence even when an exception occurs. Contrast mocked
automation tests with today's real Docker/HTTP proof. Ask what happens if recovery itself
fails; the report must record that rather than claiming success. Lunch 13:00-13:45.

## Day 2, 13:45-14:45: Jenkins performs the full delivery

Create `workshop-day2` from the pair's fork main, script path
`pipelines/Jenkinsfile.day2`, dedicated agent label. Follow Day 2 Lab 3:

1. First run defaults: tests and image build; no delivery or registry push.
2. Run with `DEPLOY=true`, `PUSH_IMAGE=false`, `INJECT_BAD_RELEASE=false`.
3. At the approval stage, read the image/version aloud and inspect test evidence.
4. Approve within five minutes; watch candidate and live verification.
5. Download archived deployment JSON and compare `/version` to the approved release.

```bash
curl -fsS http://127.0.0.1:8000/version
curl -fsS http://127.0.0.1:8000/tasks
```

The first run loads parameters, so Jenkins can initially show Build Now. An expired
approval means another parameterized run, not editing the script to skip authorization.
The approval holds the agent in this small lab. Avoid concurrent manual deployment.
Explain the observed short cutover outage; this script does not implement traffic routing.

## Day 2, 14:45-15:30: reject a bad candidate and explain recovery

Record the healthy version before attempting the broken release:

```bash
curl -fsS http://127.0.0.1:8000/version
BAD_VERSION="$(git rev-parse --short=12 HEAD)-bad-1"
BAD_IMAGE="workshop/task-api:$BAD_VERSION"
docker build --build-arg APP_VERSION="$BAD_VERSION" --build-arg DEMO_BROKEN=1 -t "$BAD_IMAGE" .
.venv/bin/python scripts/deploy.py --image "$BAD_IMAGE" --version "$BAD_VERSION"
echo "$?"
cat reports/deployment.json
curl -fsS http://127.0.0.1:8000/version
curl -fsS http://127.0.0.1:8000/tasks
```

Expected nonzero exit, failed candidate checks, unchanged healthy live version and tasks.
Bounded smoke retries take time; let them fail naturally. Ask students to explain why
this is candidate rejection rather than recovery after cutover. Repeat through Jenkins
with `DEPLOY=true`, `INJECT_BAD_RELEASE=true`, `PUSH_IMAGE=false` if time permits.

Show the distinct recovery decision test:

```bash
.venv/bin/python -m pytest tests/test_automation.py -k 'cutover or candidate' -v
```

For a real teacher recovery demonstration, use a separate disposable Docker host, not
the pair's active host. Prepare the images before class, then run this host-only sequence:

```bash
docker build --build-arg APP_VERSION=validation-1 -t workshop/task-api:validation-1 .
docker build --build-arg APP_VERSION=validation-2 -t workshop/task-api:validation-2 .
docker build --build-arg APP_VERSION=validation-bad --build-arg DEMO_BROKEN=1 -t workshop/task-api:validation-bad .
.venv/bin/python tools/verify_release.py
```

The helper actually replaces this host's workshop containers, adds marker data, rejects
an unhealthy candidate, then injects a new-live-only failure and checks the restored
previous release. Show its reports in `reports/`; distinguish that actual proof from a
mock test. Application recovery keeps the same database and cannot undo schema changes.

## Day 2, 15:30-16:00: assess evidence and conclude the two-day module

Require each pair's source commit, successful CI and delivery URLs, rejected release
evidence, matching live version, persistent task, and explanation of candidate versus
cutover failure. Score with `05-instructor.md`. For students stuck, require a diagnostic
command and justified next action; provide the reference checkpoint for further practice.

Use the remaining time for pair demonstrations. Fast pairs may follow the fully ordered
registry/Ansible extension in Day 2; do not introduce cloud provisioning for the whole
class here. Record future topics for Days 3-5 without adding them to this module.
Save reports before stopping classroom services. Retain task volumes unless their owner
has decided the disposable lab data is no longer needed.

## Teacher escalation path when a demonstration fails

Read the failing command's exit status/logs. Ask for a hypothesis, then use
`04-troubleshooting.md`. Check host/directory, interpreter/credentials, then application
behavior. Correct the cause and resume from the last verified checkpoint. Keep mandatory
checks enabled.
