import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Locate templates directory relative to backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

class EmailService:
    def __init__(self):
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )

    @property
    def smtp_host(self):
        return os.getenv("SMTP_HOST", "smtp.gmail.com")

    @property
    def smtp_port(self):
        return int(os.getenv("SMTP_PORT", "587"))

    @property
    def smtp_user(self):
        return os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER", "")

    @property
    def smtp_password(self):
        return os.getenv("SMTP_PASSWORD", "")

    @property
    def from_email(self):
        return os.getenv("FROM_EMAIL") or os.getenv("SMTP_FROM_EMAIL") or self.smtp_user or "support@ekarthub.com"

    @property
    def from_name(self):
        return os.getenv("SMTP_FROM_NAME", "EKARTHUB")


    def render_template(self, template_name: str, context: dict) -> str:
        """Render Jinja2 template with context merged with defaults."""
        full_context = {
            "frontend_url": self.frontend_url,
            "current_year": datetime.utcnow().year,
            **context
        }
        template = self.jinja_env.get_template(template_name)
        return template.render(full_context)

    def send_email(self, to_email: str, subject: str, template_name: str, context: dict) -> bool:
        """
        Renders template and dispatches email via SMTP.
        Returns True on success, raises Exception on failure so Celery can retry.
        """
        logger.info(f"[EmailService Rendering] Preparing email '{subject}' for '{to_email}' using template '{template_name}'")
        html_content = self.render_template(template_name, context)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        if not self.smtp_user or not self.smtp_password:
            error_msg = (
                f"[EmailService Error] SMTP credentials missing! "
                f"Please set SMTP_USERNAME/SMTP_USER and SMTP_PASSWORD in .env. "
                f"Email subject='{subject}' to '{to_email}' could not be dispatched."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            logger.info(f"[SMTP Connecting] Host: {self.smtp_host}, Port: {self.smtp_port}, User: {self.smtp_user}")
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=15) as server:
                    logger.info("[SMTP Connection Established SSL] Authenticating...")
                    server.login(self.smtp_user, self.smtp_password)
                    logger.info("[SMTP Authenticated] Sending message...")
                    server.sendmail(self.from_email, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                    logger.info("[SMTP Connection Established] Initiating STARTTLS...")
                    server.starttls()
                    logger.info("[SMTP TLS Established] Authenticating...")
                    server.login(self.smtp_user, self.smtp_password)
                    logger.info("[SMTP Authenticated] Sending message...")
                    server.sendmail(self.from_email, [to_email], msg.as_string())

            logger.info(f"[Email Delivered] Email '{subject}' successfully sent to '{to_email}'")
            return True
        except Exception as e:
            logger.error(f"[SMTP Error] Failed to send email '{subject}' to '{to_email}': {e}", exc_info=True)
            raise e

email_service = EmailService()

