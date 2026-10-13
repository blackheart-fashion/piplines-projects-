# Before class: instructor preparation and ordered setup

## Audience, time, and assumptions

Learners already understand Linux commands, Git basics, Docker images/containers, Ansible,
and AWS EC2. Basic Python is useful; Day 1 includes a guided code walkthrough. Run a
15-minute prerequisite check before the course. Students should be able to clone a repo,
describe an image vs a container, and read a Python function.

Each day is 390 minutes: 330 learning minutes plus 60 minutes of breaks/lunch. The default
schedule is 09:30–16:00. Times are examples, not scheduled calendar events.
For a six-hour day reduce the independent exercise by 30 minutes; for seven hours add
30 minutes of diagnosis. Keep the failure exercises.

Use pairs, rotating driver and reviewer. In larger groups, a third person investigates
failures. Each pair needs its own Docker host because the release script uses fixed names,
ports 8000/18080, and a named volume. One controller can serve multiple pairs if each job
uses a unique agent label; change the supplied `workshop-linux` label accordingly.

## Recommended lab topology

Use a prepared Ubuntu 24.04 VM per pair, with 4 vCPUs, 8 GB RAM, and roughly 30 GB free disk
as a workshop starting allocation. This is an instructor estimate, not a Jenkins minimum.
An EC2 VM or a local Linux VM works. Jenkins controller runs in Docker on that VM; a native
Linux agent on the same VM runs builds. The controller has zero executors and no Docker
socket mount. The agent has Python 3.12, Java 21, Git, and Docker CLI access.

```text
Student browser --SSH tunnel--> Jenkins controller :8080
GitHub --optional reachable HTTPS webhook--> Jenkins
Jenkins controller --WebSocket agent connection--> native Linux agent
Agent --> tests --> Docker image --> candidate :18080 --> live app :8000
                                                   live data: workshop-data volume
```

Run all Linux blocks in Bash on the lab VM, from the repository root unless explicitly
stated otherwise. Windows PowerShell is for access and native Python practice; it does
not execute the supplied Linux Jenkins `sh` steps. Windows users can also use WSL2 Ubuntu.
Do not mix a Windows virtual environment with a Linux one.

## Step 1: obtain the repository

The reference repository is public. Clone it for reading or use a personal fork for
student commits; the teacher runbook describes the fork workflow.

```bash
git clone https://github.com/Siddhantji/jenkins-python-workshop.git
cd jenkins-python-workshop
git status
```

Expected: files such as `requirements-dev.txt`, `app/`, `docs/`, and `pipelines/` exist.
The working tree should be clean. A 404 usually means a wrong URL or private-repository
access, not an absent Git installation. See the integration guide for private checkout.

The owner's published repository is `https://github.com/Siddhantji/jenkins-python-workshop`.
It is public; use your own fork/account when pushing classroom changes.

## Step 2: prepare the VM (instructor, before class)

These commands assume Ubuntu 24.04, a sudo-enabled account, and outbound package access.

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates openjdk-21-jre-headless python3 python3-venv
python3 --version
java -version
git --version
```

Expected Python: 3.12 or newer; Java: supported Java 21. The controller image bundles its
Java; the host Java is for the native agent. Do not install Java inside the Python app.

Install Docker using the official Ubuntu repository, on this dedicated lab VM:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out of SSH and log back in so group membership takes effect. Then:

```bash
docker info
docker compose version
docker run --rm hello-world
```

Expected: reachable server, Compose v2, and a successful hello-world message. Docker group
access grants root-equivalent privileges; use only a dedicated trusted workshop agent.
If Docker is already installed, inspect it first instead of reinstalling over an existing
installation. Official installation and privilege details:
[Docker Ubuntu setup](https://docs.docker.com/engine/install/ubuntu/),
[Docker post-installation](https://docs.docker.com/engine/install/linux-postinstall/).

## Step 3: create the Python environment

Linux / WSL:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/preflight.py
.venv/bin/python -m pytest -q
```

Windows PowerShell, from this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\preflight.py
.\.venv\Scripts\python.exe -m pytest -q
```

Python 3.14 can run the application as well; the canonical container/runtime target is
3.12. If `py -3.12` is unavailable, install Python 3.12 or use the prepared Linux VM.
Activation is optional because every command calls the environment's Python explicitly.
This avoids PowerShell execution-policy changes and accidental use of global packages.

## Step 4: start the Jenkins controller

On the Linux VM:

```bash
docker compose -f infra/compose.jenkins.yml up -d
docker compose -f infra/compose.jenkins.yml ps
docker compose -f infra/compose.jenkins.yml logs --tail=50 jenkins
docker compose -f infra/compose.jenkins.yml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

The last command displays a one-time setup secret. Enter it into Jenkins; do not put it in
screenshots, the repository, or a shared document. Wait for startup if the file is absent.
The controller image is `jenkins/jenkins:lts-jdk21`; pull and validate it before class.
The official [Jenkins Docker guide](https://www.jenkins.io/doc/book/installing/docker/)
explains container installation and Java requirements.

From Windows, keep a separate terminal open for the SSH tunnel:

```powershell
ssh -i C:\path\to\your-key.pem -L 8080:127.0.0.1:8080 ubuntu@YOUR_VM_IP
```

Open `http://127.0.0.1:8080` in your browser. If 8080 is already in use on the laptop,
use `-L 18080:127.0.0.1:8080` and browse port 18080 instead. On EC2, allow SSH from your
own IP; the local tunnel means no public Jenkins port is required for the manual lab.

Unlock Jenkins, install suggested plugins, create a named administrator, and verify these
plugins are installed: Pipeline, Git, JUnit, Credentials Binding, Timestamper. Add GitHub
only for the webhook lab. Use Manage Jenkins → Plugins; restart after installs if asked.
Do not disable authentication or CSRF to fix connectivity errors.

## Step 5: connect the native Linux build agent

In Jenkins: Manage Jenkins → Nodes → Built-In Node → Configure → set executors to **0**.
Jenkins recommends running builds on agents for isolation:
[controller isolation](https://www.jenkins.io/doc/book/security/controller-isolation/).

Create node `workshop-agent`: permanent agent, one executor, remote root
`/home/ubuntu/jenkins-agent`, label `workshop-linux`, launch method “Launch agents by
connecting it to the controller.” Restrict label usage to matching jobs. Save. Open the
node page and use its generated command/instructions; the secret and agent name must match.

On the VM as `ubuntu`, download the agent and store its secret outside the repository:

```bash
mkdir -p /home/ubuntu/jenkins-agent
curl -fsS http://127.0.0.1:8080/jnlpJars/agent.jar -o /home/ubuntu/jenkins-agent/agent.jar
read -rsp 'Paste the agent secret from the Jenkins node page: ' AGENT_SECRET
printf '\n'
umask 077
printf '%s' "$AGENT_SECRET" > /home/ubuntu/.jenkins-agent-secret
unset AGENT_SECRET
java -jar /home/ubuntu/jenkins-agent/agent.jar -url http://127.0.0.1:8080/ -secret @/home/ubuntu/.jenkins-agent-secret -name workshop-agent -webSocket -workDir /home/ubuntu/jenkins-agent
```

Keep this terminal running for the class. Expected: agent connected and node online.
Use the Jenkins-generated command if the installed agent's flags differ. A WebSocket
connection avoids exposing TCP agent port 50000. For another controller host, use its
reachable address, never the browser's SSH-tunnel address by assumption.

In a second VM terminal run `docker info`, `python3 --version`, and `git --version` as the
same agent account. Access that works under root can still fail under `ubuntu`.

## Instructor readiness gate

Before students arrive, verify one complete Day 1 build and one Day 2 deployment, a bad
candidate rejection, private Git checkout if used, and registry push if planned. Pre-pull
the Jenkins and Python base images. Save the exact controller/plugin versions in your
instructor notes. Prepare a known-good checkpoint for students who fall behind.

Optional EC2/Ansible exercises require a second prepared Linux host, SSH access, Docker,
and outbound registry access. They are stretch exercises, not prerequisites for the
core Day 2 outcome. Infrastructure provisioning is deliberately completed before class.
