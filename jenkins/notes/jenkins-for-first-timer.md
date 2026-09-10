# Jenkins for First-Timers: Setting Up & Testing Server Connectivity

A beginner's guide to getting a Dockerized Jenkins instance running PowerShell pipelines, using a simple "ping the plazas" connectivity test as the first working example.

---

## 1. Prerequisites

- Docker installed and a Jenkins container already running (e.g. `docker run -p 8080:8080 jenkins/jenkins:lts`)
- Access to the Jenkins Web UI (default: `http://localhost:8080`)
- Terminal access to the host machine (to run `docker exec` commands)

> **Note:** The official `jenkins/jenkins` Docker image is built on **Debian**, not Ubuntu. This is normal — don't switch base images just because tutorials assume Ubuntu. Debian and Ubuntu behave almost identically for everything in this guide.

---

## 2. Initial Jenkins Setup

1. Find your Jenkins container name/ID:
   ```bash
   docker ps
   ```
2. Get the initial admin password (only needed on first run):
   ```bash
   docker logs <jenkins_container_name>
   ```
   or
   ```bash
   docker exec <jenkins_container_name> cat /var/jenkins_home/secrets/initialAdminPassword
   ```
3. Open `http://localhost:8080` in your browser, paste the password.
4. Choose **"Install suggested plugins"**.
5. Create your first admin user when prompted.

---

## 3. Installing PowerShell Core (`pwsh`) Inside the Container

Jenkins pipelines can run PowerShell scripts, but the Jenkins Docker image doesn't include PowerShell by default. Since the container is Linux-based, we install **PowerShell Core (`pwsh`)**, not Windows PowerShell.

### 3.1 Enter the container as root

```bash
docker exec -u root -it <jenkins_container_name> bash
```

### 3.2 Install required base tools

```bash
apt-get update && apt-get install -y curl tar
```

### 3.3 Download and install PowerShell Core from the official tarball

Using the tarball avoids distro-specific package repo issues (e.g. Microsoft's `.deb` repos are built for Ubuntu and may not match Debian).

```bash
mkdir -p /opt/microsoft/powershell/7
curl -L -o /tmp/powershell.tar.gz https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/powershell-7.4.6-linux-x64.tar.gz
tar -xzf /tmp/powershell.tar.gz -C /opt/microsoft/powershell/7
chmod +x /opt/microsoft/powershell/7/pwsh
ln -sf /opt/microsoft/powershell/7/pwsh /usr/bin/pwsh
```

### 3.4 Test it

```bash
pwsh -Command "echo hello"
```

**Common error #1 — missing ICU library:**

```
Couldn't find a valid ICU package installed on the system...
```

Fix:

```bash
apt-get install -y libicu-dev
```

Re-run the test command — it should now print `hello`.

### 3.5 Install the `ping` utility (needed for connectivity tests)

Minimal Debian-based containers often strip out the `ping` binary. PowerShell's `Test-Connection` cmdlet relies on it under the hood.

```bash
apt-get install -y iputils-ping
```

### 3.6 Exit the container

```bash
exit
```

---

## 4. Install the PowerShell Plugin in Jenkins

1. Go to **Manage Jenkins → Plugins → Available plugins**
2. Search for **"PowerShell"**
3. Install it (restart Jenkins if prompted)

This plugin provides the `pwsh` step used in Pipeline scripts (for PowerShell Core). Note: there is a separate `powershell` step meant for Windows PowerShell — since our container only has PowerShell **Core**, we use `pwsh`, not `powershell`.

---

## 5. Create Your First Pipeline Job

1. From the Jenkins Dashboard, click **"New Item"**
2. Enter a name, e.g. `test-plaza-connectivity`
3. Select **"Pipeline"** → click **OK**
4. Scroll down to the **"Pipeline"** section
5. Under **"Definition"**, leave it as **"Pipeline script"** (paste directly into the UI — simplest for a first test; later you can switch to **"Pipeline script from SCM"** to pull the Jenkinsfile from Git)
6. Paste the test script below into the text area
7. Click **Save**

---

## 6. Test Scenario: Ping a List of Servers

This is a minimal pipeline that loops through a list of servers/hosts and checks reachability using PowerShell — no credentials needed, since we're only testing network connectivity (ICMP ping), not logging into anything.

```groovy
pipeline {
    agent any
    stages {
        stage('Ping Plazas') {
            steps {
                script {
                    def servers = ['8.8.8.8', 'google.com', '10.0.0.99'] // replace with your real IPs/hosts
                    for (s in servers) {
                        pwsh """
                            \$result = Test-Connection -ComputerName '${s}' -Count 2 -ErrorAction SilentlyContinue
                            if (\$result) {
                                Write-Host "[OK] ${s} is reachable"
                            } else {
                                Write-Host "[FAIL] ${s} is NOT reachable"
                            }
                        """
                    }
                }
            }
        }
    }
}
```

### Run it

1. Click **"Build Now"** on the left sidebar
2. Click the build number (e.g. `#1`)
3. Click **"Console Output"** to see the ping results

Expected output looks like:

```
[OK] 8.8.8.8 is reachable
[OK] google.com is reachable
[FAIL] 10.0.0.99 is NOT reachable
```

---

## 7. Troubleshooting Reference

| Error | Cause | Fix |
|---|---|---|
| `Cannot run program "powershell"` | Used the `powershell` step, but only PowerShell **Core** is installed | Use the `pwsh` step instead of `powershell` in the Jenkinsfile |
| `Couldn't find a valid ICU package` | Missing globalization library for .NET/PowerShell Core | `apt-get install -y libicu-dev` |
| `The system's ping utility could not be found` | `Test-Connection` shells out to `ping`, which isn't installed | `apt-get install -y iputils-ping` |
| `Unable to locate package software-properties-common` | Container is Debian, not Ubuntu — some Ubuntu-specific packages/repos don't apply | Ignore Ubuntu-specific repo instructions; use the tarball install method instead |

---

## 8. What's Next

Once this basic ping test works, natural next steps (in order of complexity) are:

1. **Externalize the server list** — move it out of the Jenkinsfile into a JSON/CSV file, so the pipeline reads from a config file instead of a hardcoded list.
2. **Move the Jenkinsfile into Git** — switch the job's Pipeline "Definition" to **"Pipeline script from SCM"**, pointing at your repo, so the pipeline is version-controlled.
3. **Add credentials** — only needed once you move from "ping" to actually connecting and doing something (e.g. WinRM remoting into a Windows server to stop/start a service). Store credentials in **Manage Jenkins → Credentials**, never hardcode them in the Jenkinsfile.
4. **Upgrade the check** — for real-world validation, prefer a TCP port check over ICMP ping, since it better reflects whether the actual service you care about (e.g. WinRM on port 5985, SSH on port 22) is reachable:
   ```powershell
   Test-NetConnection -ComputerName '<host>' -Port 5985
   ```
5. **Add a Windows Jenkins agent** — required once you need to actually manage Windows Services remotely (via WinRM), since Windows Service management commands (`New-Service`, `Start-Service`, etc.) and reliable WinRM remoting are best run from a Windows-based Jenkins agent rather than emulated from a Linux container.

---

*This guide reflects a real first-time setup session — including the actual errors encountered and how they were resolved, so you know what to expect and aren't caught off guard by them.*