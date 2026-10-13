# Troubleshooting: command, symptom, diagnosis, recovery

Use this order: identify the failed stage → read its first meaningful error → verify the
relevant account/host → fix the cause → rerun only the necessary check → retry the build.
Do not erase logs, disable security controls, or lower test thresholds to get green output.

## Python and tests

| Command / action | Likely symptom | Cause / next check | Recovery |
|---|---|---|---|
| `python3 -m venv .venv` | `ensurepip is not available` | Ubuntu venv package missing | Install `python3-venv`; recreate the incomplete env |
| `py -3.12 -m venv .venv` | Requested Python not found | Windows interpreter missing | Install 3.12 or use Linux lab |
| `python -m venv` on this workstation | `Failed to find real location` / ensurepip failed | Interpreter/environment issue; not application logic | Use known-good interpreter/VM; workspace-target dependencies were used only for pack validation |
| pip install | DNS error / connection refused / certificate failure | Proxy, internet, CA, or incorrect package index | Check `python -m pip config debug`; repair approved network/CA setup; do not use `--trusted-host` blindly |
| pip install | Permission denied / externally managed environment | Global interpreter instead of venv | Use `.venv/bin/python -m pip`; avoid `sudo pip` |
| pytest | `ModuleNotFoundError: flask` | Wrong interpreter or install failed | Run the explicit venv Python and reinstall requirements |
| pytest | Cannot create numbered temp directory | Temp permissions, notably sandboxed Windows | Use a writable workspace temp path, e.g. `--basetemp=reports/pytest-tmp`; pytest clears that directory, so reserve it only for tests |
| pytest | Coverage failure with passing assertions | Gate below 80% | Read missing lines; add meaningful tests |
| pytest | No tests collected | Wrong directory, path, or `-k` filter | Run from repo root; use `--collect-only` |
| Flask start | Address already in use | Port 8000 occupied | Identify and stop your previous lab server/container |
| POST/PATCH | HTTP 400 | Invalid JSON/title/boolean | Inspect request; use JSON boolean `true`, not string `"true"` |
| PATCH | HTTP 404 | Wrong task ID | Use ID returned by POST |

Useful Python checks (Linux):

```bash
.venv/bin/python -c 'import sys; print(sys.executable)'
.venv/bin/python -m pip show Flask pytest
.venv/bin/python -m pytest --collect-only -q
```

## Docker and release automation

| Command / action | Likely symptom | Cause / next check | Recovery |
|---|---|---|---|
| `docker info` | Cannot connect / pipe not found | Docker daemon stopped | Start Docker Desktop or Linux Docker service |
| `docker info` | Permission denied | Agent account lacks access or sandbox blocks pipe | Check account/group; re-login after group change; host verification may require approved execution |
| image build | Pull timeout / rate limit | Base-image registry inaccessible or limited | Authenticate if needed, pre-pull before class, retry after fixing access |
| image build | COPY file not found | Wrong build context | Run `docker build ... .` at repo root |
| `docker run` | Name already in use | Existing manual/candidate container | Inspect that named container; remove only an abandoned lab container |
| `docker run` | Port already allocated | Flask or previous container listening | Inspect `docker ps`; on Linux use `ss -ltnp`; stop the identified lab owner |
| smoke | Connection refused | Wrong host/port or failed startup | Check `docker ps -a` and container logs |
| smoke | Version mismatch | Wrong image or URL | Inspect tag, image ID, and `/version` |
| health | HTTP 503 | Deliberate bad release or unavailable database | Check DEMO_BROKEN and logs; inspect volume access/table state |
| API startup | SQLite unable to open / readonly | Incorrect mount path or file ownership | Inspect `/data` and user UID 10001; fix only lab volume ownership, avoid `chmod 777` |
| deployment | Candidate already exists | Previous incomplete operation or another job | Inspect candidate/logs; remove it only when verified abandoned |
| deployment | Image not found | Built/pulled on a different host | Publish/pull the correct image on deployment host |
| deployment | `candidate_failed` | Candidate readiness failed | Read logs/report; existing live remains intact |
| deployment | `previous_release_restored` | New live release failed after cutover | Fix release; deployment remains failed even though service was restored |
| deployment | `recovery_failed` | Old release cannot recover either | Inspect old container, volume, ports, daemon; escalate to instructor |
| registry push/pull | Unauthorized / denied | Wrong token, namespace, or permissions | Verify repository and scoped token; reconfigure credentials |

Read-only diagnosis:

```bash
docker ps -a --filter name=workshop-api
docker logs --tail=50 workshop-api
docker logs --tail=50 workshop-api-previous
docker inspect workshop-api --format '{{.Image}}'
docker volume inspect workshop-data
cat reports/deployment.json
```

Names absent from a first release will naturally return “No such container.”
Preserve the named data volume during recovery. Removing containers is not the same as
deleting volumes; deleting `workshop-data` destroys saved workshop tasks.

## Jenkins, GitHub, and Ansible

| Action | Likely symptom | Next check / fix |
|---|---|---|
| Build Now | Waiting for executor | Label must match online agent; check node and Java process |
| Load Jenkinsfile | Script path not found | Confirm filename/case, SCM branch, and committed file |
| Pipeline step | `No such DSL method junit/timestamps` | Install JUnit/Timestamper plugin; restart if required |
| Prepare stage | `python3` missing | Check native agent host, not controller container |
| Private checkout | Authentication failed | Jenkins needs its own `github-read` credential; laptop gh login is separate |
| Checkout | Remote branch not found | Check `git branch -a` and configured branch specifier |
| Approval | Build aborted after five minutes | Rerun and approve in time; distinguish rejection/timeout from release failure |
| Registry stage | Credential ID not found | Create username/password credential with ID `dockerhub` |
| `gh auth status` | Token invalid | Complete `gh auth login --hostname github.com --web` |
| `git commit` | Identity unknown | Configure your actual `git config user.name` and `user.email` locally |
| GitHub webhook | No delivery | Confirm subscribed push event and actual pushed branch |
| GitHub webhook | Cannot reach / timeout | Localhost/private URL is not reachable from GitHub; use polling or prepared HTTPS endpoint |
| GitHub webhook | 404 | Check reverse-proxy routing and `/github-webhook/` path |
| GitHub webhook | 403 | Inspect signature/secret mismatch and plugin logs; do not disable CSRF |
| GitHub webhook | Delivery 2xx but no build | Check trigger enabled, matching repo/branch, initial checkout, SCM poll log |
| Ansible ping | Permission denied (publickey) | Verify target `ubuntu`, key, SSH rules, and manual SSH |
| Ansible | Host-key verification failed | Verify/accept actual host key with SSH first |
| Ansible Docker pull | Permission denied/unauthorized | Target Docker user access and registry login are separate prerequisites |
| Jenkins browser | Page unreachable | Tunnel still open? Controller running? Correct laptop port? |

Jenkins diagnostics on the controller host:

```bash
docker compose -f infra/compose.jenkins.yml ps
docker compose -f infra/compose.jenkins.yml logs --tail=100 jenkins
```

## Cleanup after class

Stop Jenkins while retaining its home volume:

```bash
docker compose -f infra/compose.jenkins.yml down
```

For application cleanup, inspect container names first, export any needed task data,
then remove only this lab's containers. Keep `workshop-data` until the instructor confirms
the data is disposable. Do not use `docker system prune --volumes` on a shared machine.
Stop the native agent with Ctrl+C. EC2 instances incur costs until stopped/terminated;
record owner and cleanup responsibility in the lab inventory.
