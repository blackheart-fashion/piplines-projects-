# Jenkins + Python: first two days

A practical instructor and student pack for learners who already know Docker, Kubernetes,
Ansible, and basic AWS. Only Days 1 and 2 are included. No Kubernetes course or database
migration course is squeezed into these two days.

## Start here

1. [Instructor preparation and lab setup](docs/00-setup.md): complete before class.
2. [Day 1 — Python testing and Jenkins CI](docs/01-day1.md).
3. [Day 2 — automated delivery and recovery](docs/02-day2.md).
4. [GitHub connection and release notifications](docs/03-integrations.md).
5. [Troubleshooting by command and symptom](docs/04-troubleshooting.md).
6. [Instructor answers and assessment](docs/05-instructor.md).
7. [Validation record](docs/06-validation.md): what has actually been executed.

8. [Timed teacher runbook](docs/07-teacher-runbook.md): speaking notes, demonstration commands, expected results, and student checkpoints.

The printable HTML book is generated into `dist/workshop-days-1-2.html`.
Open it in a browser and use Print → Save as PDF if you need a handout.
The complete portable teaching pack is `dist/workshop-days-1-2.zip`.
The printable PDF is `output/pdf/workshop-days-1-2.pdf` and is included in the ZIP.

To rebuild the handout after editing Markdown:

```bash
.venv/bin/python -m pip install -r requirements-docs.txt
.venv/bin/python tools/build_book.py
.venv/bin/python tools/package_workshop.py
```

## Deliverables students build

- A Flask task API with validation, SQLite persistence, and a production WSGI server.
- Unit tests, API/database integration tests, lint checks, and a coverage gate.
- A Git-tracked Declarative Jenkins pipeline with test reports and archived evidence.
- A Docker release pipeline with immutable release tags and optional registry publication.
- Python preflight checks, HTTP smoke tests, candidate verification, and failure recovery.
- An optional Ansible delivery exercise on a prepared EC2 host.

The API has `/health`, `/version`, `GET/POST /tasks`, and `PATCH /tasks/<id>`.
SQLite is a persistence foundation for these days. PostgreSQL migrations belong in the
later database module.

Public repository: [Siddhantji/jenkins-python-workshop](https://github.com/Siddhantji/jenkins-python-workshop).
The owner's prepared Jenkins is at [localhost:8080](http://127.0.0.1:8080/), with both jobs
verified. Its login and optional automated setup are documented in the integration guide.

## Quick local test (Linux / WSL, repository root)

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m ruff check app scripts tests
.venv/bin/python -m pytest --junitxml=reports/junit.xml --cov=app --cov=scripts --cov-report=term-missing --cov-fail-under=80
```

Windows PowerShell: replace `.venv/bin/python` with `.venv\Scripts\python.exe` and
use `py -3.12 -m venv .venv`. Detailed commands are in the setup guide.

## Repository map

| Path | Purpose |
|---|---|
| `app/service.py` | Pure Python title validation |
| `app/api.py` | Application factory, API routes, parameterized SQL |
| `tests/` | Application and automation tests |
| `scripts/preflight.py` | Machine prerequisite report |
| `scripts/smoke.py` | Read-only HTTP verification with bounded retries |
| `scripts/deploy.py` | Candidate checks, cutover, recovery, event report |
| `pipelines/Jenkinsfile.day1` | CI-only reference solution |
| `pipelines/Jenkinsfile.day2` | CI and single-host delivery reference solution |
| `infra/compose.jenkins.yml` | Local-only Jenkins controller with persistent home |
| `infra/deploy.yml` | Optional remote delivery via Ansible |

## Boundaries

The supplied Jenkinsfiles are instructor solutions; students build them stage by stage.
One trusted team owns one Linux agent/Docker host. Do not run untrusted pull requests on
this privileged agent. The release script uses fixed ports/names and assumes exclusive
host access. Application ports bind to localhost. This is a single-host classroom release
with a short cutover outage, not zero-downtime deployment. Application recovery requires
schema compatibility and does not reverse data changes.

Direct dependencies are version-pinned. Transitive dependencies and the base images are
not fully locked: freeze tested image digests and a complete lockfile before a repeatable
college rollout. Do not describe the current files as a fully reproducible supply chain.
