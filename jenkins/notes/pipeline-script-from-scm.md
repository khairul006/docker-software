# Pipeline Script from SCM — Notes

## What it is

When creating a Jenkins Pipeline job, the **Definition** field under the Pipeline section has two options:

- **Pipeline script** — you paste Groovy directly into a text box in the Jenkins UI. It's saved as part of the job's internal config (an XML file inside `jenkins_home`), not in your own version control.
- **Pipeline script from SCM** — the Jenkinsfile lives in your git repo, and Jenkins fetches it fresh from the repo on every build.

## Why SCM is the better default

- **Version controlled.** The pipeline logic changes alongside the code/infra it builds, with full commit history and diffability — you can see exactly when and why a pipeline step changed.
- **Survives Jenkins loss.** If `jenkins_home` is ever wiped or rebuilt, an inline "Pipeline script" job definition is gone with it. An SCM-based job just re-fetches from git the next time it runs.
- **Reviewable.** Since it's a real file in your repo, it can go through the same PR/review process as any other code change.
- **Single source of truth.** No copy-paste drift between "what's in git" and "what's pasted into the Jenkins UI."

The tradeoff: slightly more setup (the SCM connection has to be configured and working), and every change needs an actual commit before Jenkins will see it — editing the file on disk without committing does nothing.

## Setting it up (local git repo example)

**Repo layout used:**

```
docker-doftware/
  .git
  jenkins/
    docker-compose.yaml
    pipelines/
      config/
        servers.json
      test-plaza-connectivity/
        Jenkinsfile
```

**Job config, step by step:**

1. New Item → Pipeline
2. Under **Pipeline → Definition**, choose **"Pipeline script from SCM"**
3. **SCM**: Git
4. **Repository URL**: the path *as seen from inside the Jenkins container*, not your host path — e.g. `file:///repos/docker-doftware` if that's what you mounted it as
5. **Branch Specifier**: an explicit branch, e.g. `*/main` — never leave this blank (see gotchas below)
6. **Script Path**: the Jenkinsfile's path *relative to the repo root* — e.g. `jenkins/pipelines/test-plaza-connectivity/Jenkinsfile`
7. Save

## Prerequisites specific to a *local* git repo as the SCM source

Since Jenkins runs in its own container, it needs to actually see and trust your repo:

1. **Mount the whole repo, not just a subfolder.** Git needs the `.git` metadata at the repo root to run `fetch`/`checkout` — mounting only a subdirectory gives Jenkins a folder with no git history to work with.
   ```yaml
   volumes:
     - ..:/repos/docker-doftware:ro
   ```
   Read-only is a good default safety net; Jenkins only needs to read from it.

2. **Tell git to trust the mounted path.** Ownership mismatch between your host user and the container's `jenkins` user triggers git's "dubious ownership" protection.
   ```bash
   docker exec -it jenkins git config --global --add safe.directory '*'
   ```
   Run this *without* `-u root` — it must write to the `jenkins` user's own `~/.gitconfig` (which lives at `/var/jenkins_home/.gitconfig`, so it persists across container recreation since that path is bind-mounted).

3. **Allow local (`file://`) checkouts.** Jenkins blocks these by default as a security precaution, since a `file://` remote could otherwise be used to read arbitrary paths on the Jenkins host.
   ```yaml
   environment:
     - JAVA_OPTS=-Dhudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT=true
   ```
   This **must** be set via `JAVA_OPTS` at container startup, not through the Script Console at runtime — the flag is read into a static value when the Git plugin's classes first load, so setting it later has no effect even though `System.getProperty(...)` will report `true`. After adding it, do a full recreate, not just a restart:
   ```bash
   docker compose down
   docker compose up -d
   ```

## Gotchas encountered

| Symptom | Cause | Fix |
|---|---|---|
| `Invalid refspec refs/heads/**` | Branch Specifier left empty defaults to an invalid wildcard | Set an explicit branch, e.g. `*/main` |
| `fatal: detected dubious ownership in repository` | Host/container UID mismatch on the mounted repo | `git config --global --add safe.directory '*'` as the `jenkins` user |
| `Checkout ... aborted because it references a local directory` | `file://` checkouts blocked by default | `JAVA_OPTS=-D...ALLOW_LOCAL_CHECKOUT=true`, then full `down`/`up` (not `restart`) |
| `Unable to find Jenkinsfile from git ...` | Script Path doesn't match the file's actual location in the repo | Verify with `docker exec -it jenkins find /repos/<repo> -iname Jenkinsfile`, then match Script Path exactly (case-sensitive, no leading slash) |
| Job doesn't reflect a Jenkinsfile edit | Change was made on disk but never committed | SCM checkout only sees committed history — commit the change, then rebuild |

## Key mental model

Everything Jenkins does with "Pipeline script from SCM" boils down to: **treat the Jenkinsfile as just another file in git.** Jenkins' only special behavior is that it re-clones/re-fetches the repo before every build and executes whatever Jenkinsfile is at the current commit on the specified branch. All the usual git rules apply — uncommitted changes are invisible, and the checked-out workspace mirrors your full repo structure, so any file paths referenced inside the Jenkinsfile (e.g. `readJSON file: ...`) need to be given relative to the **repo root**, not relative to the Jenkinsfile's own folder.