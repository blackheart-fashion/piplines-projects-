# Instructor guide, checkpoints, answers, and assessment

Use [the timed teacher runbook](07-teacher-runbook.md) during class for speaking notes,
commands in execution order, expected results, and student activities.

## Facilitation method

Explain one concept, demonstrate one action, have students predict the result, then let
them execute it. Ask students to say which host/account a command uses. Review evidence,
not only green pipeline boxes. Rotate the keyboard every lab.

The Python app and reference pipelines are supplied so the instructor does not spend
class time inventing an application. Students should still write tests and construct
their pipeline stages. Do not paste the complete Jenkinsfile and call that the exercise.

## Day 1 checkpoints

| Point | Minimum evidence | If behind |
|---|---|---|
| Before class | Reachable controller + online agent + working repo checkout | Use instructor's prepared pair host |
| 12:15 | API returns health; student explains one validation test | Provide code walkthrough and run test subset |
| 13:00 | Local lint/tests/gate green; XML reports exist | Diagnose interpreter and missing packages first |
| 14:45 | Jenkins executes same checks and displays test report | Supply known-good stage checkpoint |
| 16:00 | A failed build explained and fixed | Require written expected vs actual behavior |

## Day 2 checkpoints

| Point | Minimum evidence | If behind |
|---|---|---|
| 12:15 | Built image serves exact version over HTTP | Check Docker access and startup logs |
| 13:00 | Python deployment report + persistent task after replacement | Walk candidate/cutover branches together |
| 14:45 | Jenkins approved release with archived JSON | Keep registry push disabled until core works |
| 16:00 | Bad candidate rejected; healthy live still reachable | Skip Ansible extension; preserve recovery exercise |

## Expected answers

- CI checks a code revision; continuous delivery adds a releasable artifact and controlled
  deployment. Today's Day 2 approval means continuous delivery, not continuous deployment.
- Builds run on the labeled agent. The controller orchestrates and stores Jenkins data.
- A virtual environment isolates Python packages. Explicit interpreter paths avoid a
  mistaken global installation and make shell activation optional.
- Unit tests isolate business rules; API integration tests here use real temporary SQLite;
  smoke tests use a network endpoint on a real running service.
- A `pytest` exit code causes Jenkins to fail the required stage. `post always` retains
  evidence; it does not convert a failed test into success.
- JUnit is the report format Jenkins displays, even when Python produced it.
- Docker image identity and source identity are related but different. The script resolves
  the image ID so candidate/live use the same local artifact.
- Candidate rejection avoids cutover. Restoring a previous live container after cutover is
  application recovery. Neither reverses database changes.
- The persistent volume retains task data across container replacement. Disposable
  candidate data does not prove compatibility with every real live record.
- A Jenkins credential is not inherited from the owner's GitHub CLI login.
- `localhost` in a GitHub webhook means GitHub's own machine, not the student's laptop.
- `disableConcurrentBuilds` affects one job, not every job sharing the host.

## Sample fault cards

Give each pair one card and require a symptom, hypothesis, diagnostic command, correction,
and evidence. Use isolated lab jobs/hosts; avoid deleting data as a failure exercise.

1. Configure a nonexistent agent label: students identify scheduling failure.
2. Replace `.strip()` in a practice branch: students explain test failure.
3. Configure a wrong script path: students inspect SCM layout.
4. Keep Flask running on 8000: students identify port ownership before deployment.
5. Set the wrong expected smoke version: students distinguish readiness from identity.
6. Build with `DEMO_BROKEN=1`: students prove live was never replaced.
7. Use an incorrect registry credential ID: students locate credential configuration.
8. Configure a localhost webhook: students explain network reachability and use polling.

## Assessment rubric (100 points)

| Item | Points | Evidence |
|---|---:|---|
| Python understanding and meaningful tests | 20 | Explain validation, fixtures, and one new test |
| CI construction and reports | 20 | Git-tracked pipeline, lint/test gate, archived XML |
| Delivery and release identity | 20 | Running image/version matches the build |
| Persistence and failure handling | 25 | Task survives release; bad candidate rejected; explain cutover recovery |
| Diagnosis and collaboration | 15 | One fault investigated with evidence; roles rotated |

Passing target: 70, with both a working CI run and a safe failed-release demonstration.
Optional Ansible/cloud work earns feedback, not extra points needed to pass core objectives.

## Stretch improvements for later days

Record suggestions without implementing them now: PostgreSQL migrations, Kubernetes
delivery, artifact promotion across environments, shared libraries, scanners, registry
digest pinning, complete dependency locking, agent lifecycle management, and release
authorization. These are not additional Day 1/2 requirements.

## Preparation checklist

Validate canonical Python 3.12/Linux execution and installed Jenkins plugin versions on
the actual teaching platform. Read `06-validation.md` to distinguish pack verification
from a completed classroom dry run. Use the public repository and individual student forks,
pre-provision pair hosts, pre-pull images, and establish end-of-class EC2 cleanup ownership.
