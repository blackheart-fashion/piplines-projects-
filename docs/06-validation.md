# Validation record

Prepared on 12 October 2026. This record separates executed checks from optional exercises.

## Executed successfully

- Ruff lint on application, automation, tests, and instructor helpers.
- Windows Python 3.14: 39 tests passed; 88.41% coverage across `app` and `scripts`.
- Linux Python 3.12.15 in the CI image: 39 tests passed; 88.41% coverage.
- Actual Docker application image build and non-root Waitress startup.
- Actual HTTP health/version/task checks against the running container.
- Actual task persistence across a replacement image release.
- Actual unhealthy candidate rejection with the previous live service retained.
- Actual recovery after live cutover: a controlled launch injection sets DEMO_BROKEN=1
  only on the new live container. Its health check fails; the previous container is
  restarted, version rechecked, and persistent task data verified.
- Private GitHub repository creation and successful Git push.
- Local Jenkins 2.580.1 setup, zero controller executors, connected Linux agent.
- Jenkins Day 1 build 1: SUCCESS, private GitHub checkout, lint, 39 tests, 88.41% coverage,
  JUnit publication, artifact archiving, and workspace cleanup. Agent Python: 3.13.5.
- Jenkins Day 2 build 2: SUCCESS, corrected agent preflight, tests, image build,
  explicit approval, real deployment, live verification, archived JSON/XML, and cleanup.
  Running release: `d6e5de679fe9-2`.
- Five-minute chat monitoring enabled through the Codex app heartbeat
  `Jenkins workshop build alerts`; the helper compares stages, results, and release events.

## Integration findings

The first Day 2 Jenkins attempt failed preflight because the initial Debian agent image
installed Docker engine components without the separately packaged Docker CLI. The agent
Dockerfile was corrected to copy the official Docker CLI and Buildx plugin. The corrected
Day 2 build 2 completed successfully. The failed first attempt remains as troubleshooting
evidence; it has not been hidden or relabeled as a passing run.

The Windows default pytest temporary directory could not be created in the sandbox.
Verification used `--basetemp=reports/pytest-tmp` and isolated plugin loading. These are
verification-environment accommodations; the Linux test suite needed neither workaround.
The system Python venv creation also failed; workspace-target dependencies were used
for Windows checks. The Jenkins/Linux environments create normal virtual environments.

## Not executed against external infrastructure

- Docker Hub publication: no registry account/token was supplied.
- Ansible deployment to EC2: no external target/key was supplied.
- Public GitHub webhook: the local Jenkins endpoint is not public HTTPS.
- PostgreSQL migrations or Kubernetes delivery: intentionally outside Days 1 and 2.

The GitHub access used in the local lab is the owner's authenticated OAuth checkout
credential. Replace it with repository-scoped read access before sharing the controller.
The local agent has host Docker privileges and is suitable only for trusted workshop code.

## Evidence locations

`reports/junit.xml`, `reports/coverage.xml`, `reports/container-validation.json`, and the
release-specific JSON reports are local generated outputs and excluded from Git.
Jenkins build pages retain test and artifact evidence. The maintained source and this
validation record are published to the public repository.

## Teaching pack update

The repository was changed to PUBLIC at the owner's request after auditing Git history
for local credential values and paths. The original private checkout results above
describe the initial dry run. A timed teacher runbook now supplies both days'
speaking notes, demonstration commands, expected results, and practical checkpoints.

Local Jenkins evidence:

- [Day 1 successful build](http://127.0.0.1:8080/job/workshop-day1/1/).
- [Day 2 successful release](http://127.0.0.1:8080/job/workshop-day2/2/).

These localhost links work only on the prepared owner computer. Classroom pairs must use
their own controller address or SSH tunnel. The automation requires this computer and
Jenkins to remain available; it polls, rather than guaranteeing immediate stage alerts.
