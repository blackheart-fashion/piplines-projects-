# GitHub, Jenkins triggers, and notifications

## Current integration state

The workshop is published publicly at
[Siddhantji/jenkins-python-workshop](https://github.com/Siddhantji/jenkins-python-workshop).
The owner completed GitHub sign-in during preparation. A local Jenkins setup is included
below; read the validation record for the actual executed job results. No public webhook
or external messaging destination is configured.

## Step 1: sign in without sharing a token in chat

Run in your own terminal on the publishing computer:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth status
```

Complete the browser/device-code sign-in as yourself. Never paste passwords or tokens into
this chat or a teaching document. The account can differ from the expired saved account.
The sign-in requires your interaction; granting computer access does not complete it.

## Step 2: publish a public workshop repository

The following commands are for the owner from the repository root. Inspect `.gitignore`
and the staged file list before the first commit; credentials, keys, local dependencies,
reports, and databases must not be included.

```powershell
git init -b main
git add .
git diff --cached --stat
git commit -m "Add two-day Jenkins and Python workshop"
gh repo create jenkins-python-workshop --public --source . --remote origin --push
gh repo view --json nameWithOwner,url
```

If already initialized, omit `git init`; if a repository/remote exists, inspect it instead
of creating a duplicate. Use `git remote -v`. A name conflict requires a different name or
deliberately using the existing repository. Do not change repository visibility as an
error workaround. Students can read and fork the public reference repository. Their
practice commits go to their own forks; public visibility does not grant write access.

## Step 3: give Jenkins checkout access

A successful `gh auth login` on the laptop does **not** authenticate Jenkins on another
machine. For a public repository no checkout credential is usually needed. For private
HTTPS checkout, create a fine-grained GitHub token restricted to the workshop repository
with read access to repository contents, subject to organization approval if required.

In Jenkins → Credentials → add Username with password: GitHub username + token, ID
`github-read`. Select it in the job's Git SCM configuration. Do not write the token into
the repository URL or Jenkinsfile. Test **Build Now** first. Source:
[Jenkins credential use](https://www.jenkins.io/doc/book/using/using-credentials/).

## Step 4: choose a trigger suitable for the lab

### Path A: manual trigger (works with SSH-tunneled local Jenkins)

Use Build Now / Build with Parameters. This is the default classroom path. It teaches
pipeline behavior without public webhook infrastructure.

### Path B: SCM polling (automatic, no inbound public endpoint)

In the CI job's Configure → Build Triggers → Poll SCM, set `H/2 * * * *`.
Jenkins checks for repository changes approximately every two minutes. A change can take
until the next poll to trigger. Run an initial successful checkout first.
Use polling on the Day 1 CI job. Leave the Day 2 deployment job manually initiated so
students explicitly choose deployment parameters.

### Path C: GitHub push webhook (reachable HTTPS Jenkins required)

The bundled controller binds only to localhost. GitHub cannot send a webhook to
`localhost`, `127.0.0.1`, an SSH tunnel on your laptop, or an inaccessible private address.
To use this path, the instructor prepares a trusted HTTPS reverse proxy and network route
to Jenkins. Keep authentication enabled and configure the actual Jenkins root URL.

1. Install the GitHub Jenkins plugin. Verify manual checkout first.
2. In the Day 1 job enable **GitHub hook trigger for GITScm polling**.
3. Configure a webhook secret in the installed Jenkins GitHub plugin's hook-secret
   settings. The exact location depends on plugin version; consult its settings/help.
4. GitHub repo → Settings → Webhooks → Add webhook.
5. Payload URL: `https://YOUR_JENKINS_HOST/github-webhook/` with the trailing slash.
6. Content type: `application/json`; use the same secret as Jenkins; keep SSL verification.
7. Select push events and activate. Check the ping delivery first.
8. Push a harmless main-branch change. Inspect GitHub Recent Deliveries and the resulting
   Jenkins checkout/commit. A 2xx HTTP response is delivery evidence; also prove a build ran.

Verify an incorrect-secret delivery is rejected before claiming signature verification
works. If the installed plugin does not expose matching secret verification, use polling
until a verified setup is prepared; do not silently omit the secret.

Sources: [Jenkins GitHub plugin](https://plugins.jenkins.io/github/),
[creating GitHub webhooks](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks),
[webhook troubleshooting](https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks).

## Release notifications and evidence

The supplied pipelines print a build result and URL in their final `post` block. Jenkins
records stage logs, JUnit results, and archived report files. The Python release tool
prints a JSON event immediately after each release action and archives the final report.
That makes individual steps traceable without requiring a messaging account.

| Event | Evidence |
|---|---|
| Commit obtained | Checkout console + Git revision |
| Tests passed/failed | JUnit results + coverage report |
| Image built | Image tag and image ID |
| Approval requested | Jenkins input stage |
| Candidate verified/rejected | `candidate_verified` / `candidate_failed` |
| Live release verified | `live_verified` |
| Old release restored | `previous_release_restored` |
| Recovery unsuccessful | `recovery_failed` |

Full step logs appear in Jenkins. A five-minute Codex heartbeat named **Jenkins workshop
build alerts** is enabled for the owner's local setup: it runs `tools/monitor_jenkins.py`
and posts observed stage/result/release changes in this chat. It stays quiet when unchanged
and never starts builds or approves releases. Short stages can complete between polls;
this is not a real-time event stream. The computer and Jenkins must remain available.
No direct Jenkins-to-chat webhook, email, or Slack destination is configured.

For a quick instructor review, download the deployment JSON and JUnit XML and attach them
to the conversation. No secrets are needed to interpret these reports.

## Automated local setup on the owner's computer

The prepared local controller is at `http://127.0.0.1:8080`, with user `workshop-admin`.
Its generated password is in the ignored local file `.local-jenkins/admin-password`.
Read it locally when signing in; do not commit or share the file. The agent secret and
GitHub token are also ignored, excluded from image build contexts, and excluded from ZIP
packages. Jenkins stores the checkout credential in its encrypted credential store.

This optional setup uses a containerized Linux build agent on the host network, rather
than the native Ubuntu agent in the canonical classroom instructions. The agent has
Docker socket access and is only suitable for trusted workshop code. Host networking
must work on your Docker installation; Docker Desktop may require its host-networking
feature. Its Debian Python version may differ from the canonical Python 3.12 app image.

From the owner's repository root, after GitHub sign-in:

```powershell
python tools/prepare_local_jenkins.py
docker compose -p workshop -f infra/compose.jenkins.yml -f infra/compose.local.yml up -d --build
python tools/jenkins_local.py status
python tools/jenkins_local.py build --job workshop-day1
python tools/jenkins_local.py console --job workshop-day1
```

The preparation script captures the signed-in GitHub CLI token without printing it.
This owner's OAuth token has broader permissions than the read-only repository token
recommended for classroom Jenkins. Replace `github-read` with a repository-scoped read
credential before expanding access to other users. Keep the local secret directory
restricted to your account; Unix mode bits do not enforce Windows file ACLs.

For Day 2, run a default build once to load parameters, then deploy explicitly:

```powershell
python tools/jenkins_local.py build --job workshop-day2
python tools/jenkins_local.py build --job workshop-day2 --deploy
```

Review the pending image in the Jenkins browser and click Deploy. The local API helper
also supports `approve --job workshop-day2 --number N` for an owner-controlled dry run;
it approves only that selected workshop build. It does not provide production approval
authorization. All authenticated users have full control in this single-owner lab;
do not reuse this authorization model for a shared institutional controller.

Inspect state with `status` and logs with `console --job workshop-day2 --number N`.
These commands are on-demand checks. The app heartbeat supplies ongoing change monitoring.
To stop both local services while retaining their data:

```powershell
docker compose -p workshop -f infra/compose.jenkins.yml -f infra/compose.local.yml down
```
