from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """Send an email via SMTP (aiosmtplib). Falls back to console log in dev."""
    # if settings.ENV == "local":
    #     _log_to_console(to, subject, html_body)
    #     return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_ADDRESS}>"
    msg["To"] = to

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=False,
        )
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.error("email_failed", to=to, subject=subject, error=str(exc))
        if settings.ENV == "local":
            _log_to_console(to, subject, html_body)
        return False


def _log_to_console(to: str, subject: str, body: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"EMAIL TO:      {to}")
    print(f"SUBJECT:       {subject}")
    print(f"{'=' * 60}")
    print(body)
    print(f"{'=' * 60}\n")
