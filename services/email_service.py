"""Email delivery service integrating Jinja2 templates and Brevo HTTP API."""

import logging
import os
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailService:
    """Service wrapper for rendering email templates and sending emails via Brevo."""

    def __init__(self) -> None:
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True
        )

    @property
    def api_key(self) -> str:
        """Retrieve configured Brevo / Sendinblue API key."""
        return (
            os.getenv("BREVO_API_KEY") or os.getenv("SENDINBLUE_API_KEY") or ""
        ).strip()

    @property
    def sender_email(self) -> str:
        """Retrieve configured sender email address."""
        return (
            os.getenv("BREVO_SENDER_EMAIL")
            or os.getenv("SENDER_EMAIL")
            or os.getenv("FROM_EMAIL")
            or os.getenv("SMTP_FROM_EMAIL")
            or "support@ekarthub.com"
        ).strip()

    @property
    def sender_name(self) -> str:
        """Retrieve configured sender display name."""
        return (
            os.getenv("BREVO_SENDER_NAME")
            or os.getenv("SENDER_NAME")
            or os.getenv("FROM_NAME")
            or os.getenv("SMTP_FROM_NAME")
            or "EKARTHUB"
        ).strip()

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a HTML Jinja2 email template with provided context."""
        logger.info(f"Rendering email template '{template_name}' from {TEMPLATES_DIR}")
        full_context = {
            "frontend_url": self.frontend_url,
            "current_year": datetime.utcnow().year,
            **context,
        }
        template = self.jinja_env.get_template(template_name)
        return template.render(full_context)

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
    ) -> bool:
        """Send an email using Brevo HTTP API."""
        logger.info(
            f"Sending email '{subject}' to {to_email} using template {template_name}"
        )

        if not self.api_key:
            logger.error("BREVO_API_KEY is missing from environment variables.")
            raise ValueError("BREVO_API_KEY missing")

        try:
            html_content = self.render_template(template_name, context)
        except Exception as e:
            logger.error(f"Template rendering error for {template_name}: {e}")
            raise

        payload = {
            "sender": {"name": self.sender_name, "email": self.sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content,
        }

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                BREVO_API_URL, json=payload, headers=headers, timeout=30
            )

            logger.info(f"Brevo API response status: {response.status_code}")

            if response.status_code in (200, 201, 202):
                logger.info(f"Email successfully sent to {to_email}")
                return True

            raise Exception(f"Brevo Error {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise


email_service = EmailService()
