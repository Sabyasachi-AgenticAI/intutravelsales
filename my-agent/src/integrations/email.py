import asyncio
import logging
import os
import smtplib
from email.mime.text import MIMEText

logger = logging.getLogger("agent.integrations.email")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


async def send_email(*, to: str, subject: str, body: str) -> None:
    """Send a plain-text email via Gmail SMTP using an app password.

    Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD in the environment.
    """
    address = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = address
    message["To"] = to

    def _send() -> None:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(address, app_password)
            smtp.send_message(message)

    await asyncio.to_thread(_send)
    logger.info("email sent to %s", to)
