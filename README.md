<div align="center">

# 🚀 Jenkins + Python: Last Two Days

**A practical instructor & student pack for learners who already know Docker, Kubernetes, Ansible, and basic AWS.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?style=for-the-badge&logo=jenkins&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Release-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-Optional-EE0000?style=for-the-badge&logo=ansible&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Persistence-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

📦 **Only Days 1 and 2 are included.** No Kubernetes course or database migration course is squeezed into these two days.

</div>

---

## 📑 Table of Contents

- [Start Here](#-start-here)
- [Printable Handout](#-printable-handout)
- [What Students Build](#-what-students-build)
- [API Endpoints](#-api-endpoints)
- [Repository & Jenkins](#-repository--jenkins)
- [Quick Local Test](#-quick-local-test)
- [Repository Map](#-repository-map)
- [Boundaries](#-boundaries)

---

## 🧭 Start Here

| # | Guide | What you get |
|---|-------|--------------|
| 1 | [Instructor preparation and lab setup](docs/00-setup.md) | ✅ Complete **before** class |
| 2 | [Day 1 — Python testing and Jenkins CI](docs/01-day1.md) | Tests, lint, coverage, CI pipeline |
| 3 | [Day 2 — Automated delivery and recovery](docs/02-day2.md) | Docker release, smoke tests, recovery |
| 4 | [GitHub connection and release notifications](docs/03-integrations.md) | Webhooks, notifications |
| 5 | [Troubleshooting by command and symptom](docs/04-troubleshooting.md) | Quick fixes |
| 6 | [Instructor answers and assessment](docs/05-instructor.md) | Answer key |
| 7 | [Validation record](docs/06-validation.md) | What has actually been executed |
| 8 | [Timed teacher runbook](docs/07-teacher-runbook.md) | Speaking notes, demos, expected results, student checkpoints |

---

## 🖨️ Printable Handout

- 📄 The printable HTML book is generated into `dist/workshop-days-1-2.html`.
  Open it in a browser and use **Print → Save as PDF** if you need a handout.
- 🗜️ The complete portable teaching pack is `dist/workshop-days-1-2.zip`.
- 📕 The printable PDF is `output/pdf/workshop-days-1-2.pdf` and is included in the ZIP.

**To rebuild the handout after editing Markdown:**

```bash
.venv/bin/python -m pip install -r requirements-docs.txt
.venv/bin/python tools/build_book.py tools/package_workshop.py
```

---

## 🛠️ What Students Build

- 🌶️ A **Flask task API** with validation, SQLite persistence, and a production WSGI server.
- 🧪 **Unit tests**, API/database integration tests, lint checks, and a coverage gate.
- 🔧 A **Git-tracked Declarative Jenkins pipeline** with test reports and archived evidence.
- 🐳 A **Docker release pipeline** with immutable release tags and optional registry publication.
- ✈️ **Python preflight checks**, HTTP smoke tests, candidate verification, and failure recovery.
- ☁️ An **optional Ansible delivery exercise** on a prepared EC2 host.

---

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Health check |
| `GET` | `/version` | Running version |
| `GET` | `/tasks` | List tasks |
| `POST` | `/tasks` | Create a task |
| `PATCH` | `/tasks/<id>` | Update a task |

> 💾 SQLite is a persistence foundation for these days. PostgreSQL migrations belong in the later database module.

---

## 🔗 Repository & Jenkins

- 📂 **Public repository:** [Siddhantji/jenkins-python-workshop](https://github.com/Siddhantji/jenkins-python-workshop)
- 🏗️ **Owner's prepared Jenkins:** [localhost:8080](http://127.0.0.1:8080/) — both jobs verified.
- 📘 Login and optional automated setup are documented in the integration guide.

---

## ⚡ Quick Local Test

**Linux / WSL (repository root):**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m ruff check app scripts tests
.venv/bin/python -m pytest --junitxml=reports/junit.xml \
  --cov=app --cov=scripts --cov-report=term-missing --cov-fail-under=80
```

**Windows PowerShell:** replace `.venv/bin/python` with `.venv\Scripts\python.exe` and use `py -3.12 -m venv .venv`.

📖 Detailed commands are in the [setup guide](docs/00-setup.md).

---

## 🗺️ Repository Map

| Path | Purpose |
|------|---------|
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

---

## ⚠️ Boundaries

> [!IMPORTANT]
> Please read these before using the pack in a real class.

- 🧑‍🏫 The supplied Jenkinsfiles are **instructor solutions**; students build them stage by stage.
- 👥 One trusted team owns one Linux agent/Docker host.
- 🚫 **Do not run untrusted pull requests** on this privileged agent.
- 🔒 The release script uses fixed ports/names and assumes exclusive host access.
- 🏠 Application ports bind to `localhost`.
- ⏱️ This is a **single-host classroom release** with a short cutover outage, **not** zero-downtime deployment.
- 🔄 Application recovery requires schema compatibility and does **not** reverse data changes.
- 📌 Direct dependencies are version-pinned. Transitive dependencies and base images are **not fully locked**: freeze tested image digests and a complete lockfile before a rollout to a full college batch.
- ❌ Do not describe the current files as a fully reproducible supply chain.

---

<div align="center">

Made with ❤️ for learners who want hands-on Jenkins + Python experience.

</div>
