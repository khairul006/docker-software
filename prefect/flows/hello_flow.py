"""
Sample scheduled flow for the docker-compose Prefect stack.

Register from INSIDE the container (paths must match the worker's view):
    docker compose exec prefect-worker python hello_flow.py

Check: http://localhost:4200 -> Deployments -> hello-scheduled
Run now: prefect deployment run 'say-hello/hello-scheduled'
"""

import os
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

# Load before importing prefect: it reads PREFECT_API_URL at import time.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
os.environ.setdefault("PREFECT_API_URL", "http://localhost:4200/api")

from prefect import flow, task  # noqa: E402
from prefect.client.schemas.schedules import CronSchedule  # noqa: E402


@task
def build_message() -> str:
    now = datetime.now(timezone.utc).isoformat()
    return f"Hello from Prefect! This ran at {now} (UTC)."


@flow(name="say-hello")
def say_hello():
    message = build_message()
    print(message)


if __name__ == "__main__":
    # Must resolve to the worker's view of this folder (/opt/prefect/flows).
    source_dir = str(Path(__file__).resolve().parent)

    say_hello.from_source(
        source=source_dir,
        entrypoint="hello_flow.py:say_hello",
    ).deploy(
        name="hello-scheduled",
        work_pool_name="default-process-pool",
        # Every 2 minutes for quick testing; swap for your real schedule.
        schedule=CronSchedule(
            cron="*/2 * * * *",
            timezone="Asia/Kuala_Lumpur",
        ),
    )