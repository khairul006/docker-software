r"""
Sends a custom HTML email over SMTP, on a schedule.

Credentials come from environment variables (SMTP_HOST, SMTP_PORT,
SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO), set in your
../.env file and passed into the prefect-worker container via
docker-compose.yaml's environment: block. Nothing is hardcoded here.

The email body is loaded from email_template.html, sitting next to
this script. Edit that file to change the email's look/content --
no need to touch this Python file for content changes.

Setup:
    1. Fill in the SMTP_* / EMAIL_* values in ../.env with your real
       provider details (Gmail app password, SendGrid, your company
       SMTP relay, etc).
    2. Apply the env change to the running containers:
           docker compose down
           docker compose up -d
       (containers only read .env at startup, not live)

Register the schedule (run INSIDE the worker container):
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

# HTML template lives next to this script
TEMPLATE_PATH = Path(__file__).resolve().parent / "email_template.html"
MEME_PATH = Path(__file__).resolve().parent / "random16.jpg"


@task(retries=2, retry_delay_seconds=30)
def send_email() -> None:

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    from_addr = os.environ.get("EMAIL_FROM", username)
    to_addr = os.environ["EMAIL_TO"]

    print(f"Sending email from {from_addr} to {to_addr} via {host}:{port} as {username}")

    html_content = TEMPLATE_PATH.read_text(encoding="utf-8")

    msg = EmailMessage()
    msg["Subject"] = "Hello from Prefect"
    msg["From"] = from_addr
    msg["To"] = to_addr

    # Plain-text fallback for clients that can't render HTML
    msg.set_content("Hello! This is a scheduled email sent via Prefect. "
                     "(Your email client doesn't support HTML.)")

    # HTML version -- this is what most clients will actually display
    msg.add_alternative(html_content, subtype="html")

    # Attach the gif and link it to the cid:meme_image reference in the HTML
    html_part = msg.get_payload()[-1]
    with open(MEME_PATH, "rb") as f:
        html_part.add_related(
            f.read(),
            maintype="image",
            subtype="jpg",
            cid="meme_image",
        )

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
        schedule=IntervalSchedule(
            interval=timedelta(seconds=60),
            timezone="Asia/Kuala_Lumpur",
        ),
    )