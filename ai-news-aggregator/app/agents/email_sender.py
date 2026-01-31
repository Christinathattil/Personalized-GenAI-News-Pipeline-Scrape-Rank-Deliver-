"""Simple SMTP email sender using environment credentials.

This utility sends HTML and/or plain text emails using SMTP details defined
in the project-level `.env` file:

    SMTP_HOST=<smtp server hostname>
    SMTP_PORT=<smtp port, usually 587 for TLS>
    SMTP_USER=<smtp username / login email>
    SMTP_PASSWORD=<smtp password or app-password>
    SENDER_EMAIL=<optional, defaults to SMTP_USER>
    RECIPIENT_EMAIL=<destination email address>

The `.env` file is automatically loaded if it exists at
`app/.env`. Fallbacks to already-exported environment variables when running
in production where a `.env` file may not be present.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------
_APP_ROOT = Path(__file__).resolve().parent.parent  # .../app
_ENV_PATH = _APP_ROOT / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class EmailSender:
    """Lightweight SMTP wrapper for sending rich-content emails."""

    def __init__(self,
                 smtp_host: Optional[str] = None,
                 smtp_port: Optional[int] = None,
                 smtp_user: Optional[str] = None,
                 smtp_password: Optional[str] = None,
                 sender_email: Optional[str] = None,
                 recipient_email: Optional[str] = None,
                 use_tls: bool = True):
        # Allow explicit overrides, otherwise pull from env
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL") or self.smtp_user
        self.recipient_email = recipient_email or os.getenv("RECIPIENT_EMAIL")
        self.use_tls = use_tls

        missing = [name for name, value in (
            ("SMTP_HOST", self.smtp_host),
            ("SMTP_USER", self.smtp_user),
            ("SMTP_PASSWORD", self.smtp_password),
            ("RECIPIENT_EMAIL", self.recipient_email),
        ) if not value]
        if missing:
            raise ValueError(
                "Missing required email environment variables: " + ", ".join(missing)
            )

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def send_email(self, *, subject: str, html_body: str, text_body: Optional[str] = None) -> None:
        """Send an email.

        Parameters
        ----------
        subject: str
            Message subject line.
        html_body: str
            HTML version of the message. Always attached as the rich part.
        text_body: str | None
            Plain-text fall-back. When *None*, the HTML is used as plain text.
        """
        if text_body is None:
            # Use HTML stripped of tags would be nicer but keep simple
            text_body = html_body

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        context = ssl.create_default_context()

        try:
            logger.info("Connecting to SMTP server %s:%s", self.smtp_host, self.smtp_port)
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info("Email successfully sent to %s", self.recipient_email)
        except Exception as exc:
            logger.error("Failed to send email: %s", exc)
            raise
