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
    def smtp_host(self) -> str:
        return os.getenv("SMTP_HOST", "smtp.gmail.com").strip()

    @property
    def smtp_port(self) -> int:
        port_val = os.getenv("SMTP_PORT", "587").strip()
        try:
            return int(port_val)
        except ValueError:
            logger.warning(f"[SMTP Config Warning] Invalid SMTP_PORT '{port_val}', defaulting to 587.")
            return 587

    @property
    def smtp_user(self) -> str:
        return (os.getenv("SMTP_USERNAME") or os.getenv("SMTP_USER") or "").strip()

    @property
    def smtp_password(self) -> str:
        return (os.getenv("SMTP_PASSWORD") or "").strip()

    @property
    def from_email(self) -> str:
        return (
            os.getenv("EMAIL_FROM") or
            os.getenv("FROM_EMAIL") or
            os.getenv("SMTP_FROM_EMAIL") or
            self.smtp_user or
            "support@ekarthub.com"
        ).strip()

    @property
    def from_name(self) -> str:
        return os.getenv("SMTP_FROM_NAME", "EKARTHUB").strip()

    def render_template(self, template_name: str, context: dict) -> str:
        """Render Jinja2 template with context merged with defaults."""
        full_context = {
            "frontend_url": self.frontend_url,
            "current_year": datetime.utcnow().year,
            **context
        }
        template = self.jinja_env.get_template(template_name)
        return template.render(full_context)

    def _dispatch_via_smtp(self, msg: MIMEMultipart, to_email: str, port: int) -> bool:
        logger.info(f"[SMTP Attempting Connection] Host: '{self.smtp_host}' | Port: {port} | Target Email: '{to_email}'")

        if port == 465:
            server = smtplib.SMTP_SSL(self.smtp_host, port, timeout=30)
            logger.info(f"[SMTP Connected SSL] Connected successfully to {self.smtp_host}:{port}")
            try:
                logger.info(f"[SMTP Login] Authenticating user '{self.smtp_user}'...")
                server.login(self.smtp_user, self.smtp_password)
                logger.info(f"[SMTP Login Successful] Authenticated with {self.smtp_host}")

                logger.info(f"[SMTP Dispatch] Sending message to '{to_email}'...")
                server.send_message(msg)
                logger.info(f"[SMTP Email Sent Successfully] Message delivered to '{to_email}' via SSL Port {port}")
            finally:
                try:
                    server.quit()
                except Exception:
                    pass
        else:
            server = smtplib.SMTP(self.smtp_host, port, timeout=30)
            logger.info(f"[SMTP Connected] Connected successfully to {self.smtp_host}:{port}")
            try:
                server.ehlo()
                logger.info("[SMTP STARTTLS] Initiating STARTTLS encryption...")
                server.starttls()
                server.ehlo()
                logger.info("[SMTP STARTTLS Successful] TLS connection established.")

                logger.info(f"[SMTP Login] Authenticating user '{self.smtp_user}'...")
                server.login(self.smtp_user, self.smtp_password)
                logger.info(f"[SMTP Login Successful] Authenticated with {self.smtp_host}")

                logger.info(f"[SMTP Dispatch] Sending message to '{to_email}'...")
                server.send_message(msg)
                logger.info(f"[SMTP Email Sent Successfully] Message delivered to '{to_email}' via Port {port}")
            finally:
                try:
                    server.quit()
                except Exception:
                    pass

        return True

    def send_email(self, to_email: str, subject: str, template_name: str, context: dict) -> bool:
        """
        Renders template and dispatches email via standard smtplib with port fallback.
        """
        logger.info(f"[EmailService Details] Host: '{self.smtp_host}' | Port: {self.smtp_port} | User: '{self.smtp_user}' | From: '{self.from_email}'")
        logger.info(f"[EmailService Rendering] Preparing email '{subject}' for '{to_email}' using template '{template_name}'")

        if not self.smtp_user or not self.smtp_password:
            error_msg = (
                f"[EmailService Config Error] Missing SMTP credentials! "
                f"Ensure SMTP_USERNAME/SMTP_USER and SMTP_PASSWORD are configured."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        html_content = self.render_template(template_name, context)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        primary_port = self.smtp_port
        try:
            self._dispatch_via_smtp(msg, to_email, primary_port)
            return True
        except Exception as primary_exc:
            logger.error(f"[SMTP Primary Port {primary_port} Failed] Error: {primary_exc}", exc_info=True)
            
            fallback_port = 465 if primary_port != 465 else 587
            logger.warning(f"[SMTP Fallback Triggered] Attempting fallback to Port {fallback_port}...")
            try:
                self._dispatch_via_smtp(msg, to_email, fallback_port)
                logger.info(f"[SMTP Fallback Success] Email successfully sent via fallback Port {fallback_port}")
                return True
            except Exception as fallback_exc:
                logger.error(f"[SMTP Fallback Port {fallback_port} Failed] Error: {fallback_exc}", exc_info=True)
                raise primary_exc

email_service = EmailService()
