r"""
Sends a simple "hello" email over SMTP, on a schedule.

Credentials come from environment variables (SMTP_HOST, SMTP_PORT,
SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO), set in your
../.env file and passed into the prefect-worker container via
docker-compose.yaml's environment: block. Nothing is hardcoded here.

Setup:
    1. Fill in the SMTP_* / EMAIL_* values in ../.env with your real
       provider details (Gmail app password, SendGrid, your company
       SMTP relay, etc).
    2. Apply the env change to the running containers:
           docker compose down
           docker compose up -d
       (containers only read .env at startup, not live)

Register the schedule (run INSIDE the worker container, same reasoning
as hello_flow.py -- the recorded source path must match what the
worker itself will see later):
    docker compose exec prefect-worker python /opt/prefect/flows/email_flow.py

Test immediately without waiting for the schedule:
    docker compose exec prefect-worker prefect deployment run 'send-hello-email/hello-email-scheduled'

Check it worked:
    - UI: http://localhost:4200 -> Deployments -> hello-email-scheduled
    - Or: docker compose logs -f prefect-worker
"""

from datetime import timedelta
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from prefect import flow, task
from prefect.client.schemas.schedules import CronSchedule, IntervalSchedule


@task(retries=2, retry_delay_seconds=30)
def send_email() -> None:
    host = "smtp.office365.com"
    port = 587
    username = ""
    password = ""
    from_addr = ""
    to_addr = ""

    # host = os.environ["SMTP_HOST"]
    # port = int(os.environ.get("SMTP_PORT", "587"))
    # username = os.environ["SMTP_USERNAME"]
    # password = os.environ["SMTP_PASSWORD"]
    # from_addr = os.environ.get("EMAIL_FROM", username)
    # to_addr = os.environ["EMAIL_TO"]

    msg = EmailMessage()
    msg["Subject"] = "Hello from Prefect"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content("Hello! This is a scheduled email sent via Prefect.")

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(username, password)
        server.send_message(msg)


@flow(name="send-hello-email")
def send_hello_email():
    send_email()


if __name__ == "__main__":
    source_dir = str(Path(__file__).resolve().parent)

    send_hello_email.from_source(
        source=source_dir,
        entrypoint="email_flow.py:send_hello_email",
    ).deploy(
        name="hello-email-scheduled",
        work_pool_name="default-process-pool",
        # Daily at 1pm, Malaysia time. Change the cron string for a
        # different schedule.
        schedule=IntervalSchedule(
            interval=timedelta(seconds=60),
            timezone="Asia/Kuala_Lumpur",
        ),
    )