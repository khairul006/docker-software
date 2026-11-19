# Prefect — Setup Guide

Simple guide for starting the Prefect server, deploying flows, and
making changes going forward.

---

## 1. First-time setup

**1.1 Fill in your credentials / config**

Edit the `.env` file (same folder as `docker-compose.yaml`) with any
values your flows need (API keys, SMTP settings, tokens, etc).

**1.2 Start everything**

```bash
docker compose up -d
```

This starts the Prefect server, database, and the worker container.

**1.3 Check it's running**

Open the Prefect UI in your browser:

```
http://localhost:4200
```

---

## 2. Deploying a flow (register it + its schedule)

This step tells Prefect "this flow exists, run it on this schedule."
Run it **inside the worker container** (not on your host machine):

```bash
docker compose exec prefect-worker python /opt/prefect/flows/<your_flow_file>.py
```

Replace `<your_flow_file>.py` with the actual script name. You only
need to re-run this when:
- You change the schedule (cron/interval) in the flow file
- You change flow/task logic in the flow file
- It's the first time deploying that flow

You do **NOT** need to redeploy for changes to files the flow simply
*reads* at runtime (e.g. templates, config files it loads with
`read_text()` — see section 5).

---

## 3. Test a flow immediately

Don't want to wait for the schedule? Trigger a run manually:

```bash
docker compose exec prefect-worker prefect deployment run '<flow-name>/<deployment-name>'
```

Check the result:
- **UI:** http://localhost:4200 → Deployments → select your deployment → Runs
- **Logs:** `docker compose logs -f prefect-worker`

---

## 4. Pausing / resuming a schedule

**Pause (stop it from running automatically):**
```bash
docker compose exec prefect-worker prefect deployment pause-schedule '<flow-name>/<deployment-name>'
```

**Resume:**
```bash
docker compose exec prefect-worker prefect deployment resume-schedule '<flow-name>/<deployment-name>'
```

(Or use the Active/Inactive toggle in the UI under the deployment's Schedule tab.)

---

## 5. What needs a restart, and what doesn't

| Change | Action needed |
|---|---|
| `.env` values (credentials, config) | `docker compose down` then `docker compose up -d` |
| Files a flow reads at runtime (templates, config it loads fresh each run) | **Nothing** — picked up on the next run automatically |
| Flow logic or schedule (`@flow` / `@task` code, `.deploy()` args) | Re-run the deploy command (section 2) — no full restart needed |

**Why `.env` needs a restart:** environment variables are only loaded
into the container process once, at startup. Editing `.env` while the
container is already running has no effect until it's restarted.

**Why runtime-read files don't:** if the Python code reads a file from
disk during task execution (rather than at container startup), any
edit is picked up on the very next run — scheduled or manual.

---

## 6. Stopping everything

```bash
docker compose down
```

This stops all containers (server, database, worker). Flow
definitions and past run history in the Prefect database are
preserved as long as you don't delete the associated volume.

---

## Quick reference

```bash
# Start
docker compose up -d

# Deploy / register a flow's schedule (only needed after code/schedule changes)
docker compose exec prefect-worker python /opt/prefect/flows/<your_flow_file>.py

# Test now
docker compose exec prefect-worker prefect deployment run '<flow-name>/<deployment-name>'

# Pause schedule
docker compose exec prefect-worker prefect deployment pause-schedule '<flow-name>/<deployment-name>'

# Resume schedule
docker compose exec prefect-worker prefect deployment resume-schedule '<flow-name>/<deployment-name>'

# View logs
docker compose logs -f prefect-worker

# Stop
docker compose down
```