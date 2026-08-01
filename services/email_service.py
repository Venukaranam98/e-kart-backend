import os
import logging
import socket
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

class IPv4SMTP(smtplib.SMTP):
    """SMTP subclass forcing IPv4 (AF_INET) resolution to bypass IPv6 network routing limitations on Linux hosting platforms like Render."""
    def _get_socket(self, host, port, timeout):
        infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        last_err = None
        for res in infos:
            af, socktype, proto, canonname, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)
                if timeout is not None and timeout != socket._GLOBAL_DEFAULT_TIMEOUT:
                    sock.settimeout(timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(sa)
                return sock
            except Exception as e:
                last_err = e
                if sock is not None:
                    sock.close()
        if last_err:
            raise last_err
        raise socket.error(f"No IPv4 address found for host {host}")

class IPv4SMTP_SSL(smtplib.SMTP_SSL):
    """SMTP_SSL subclass forcing IPv4 (AF_INET) resolution."""
    def _get_socket(self, host, port, timeout):
        sock = IPv4SMTP._get_socket(self, host, port, timeout)
        return self.context.wrap_socket(sock, server_hostname=self._host)

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

    def _dispatch_via_smtp(self, msg: MIMEMultipart, to_email: str, port: int) -> bool:
        if port == 465:
            with IPv4SMTP_SSL(self.smtp_host, port, timeout=30) as server:
                logger.info("[SMTP Connection Established SSL IPv4] Authenticating...")
                server.login(self.smtp_user, self.smtp_password)
                logger.info("[SMTP Authenticated] Sending message...")
                server.sendmail(self.from_email, [to_email], msg.as_string())
                try:
                    server.quit()
                except Exception:
                    pass
        else:
            with IPv4SMTP(self.smtp_host, port, timeout=30) as server:
                logger.info(f"[SMTP Connection Established IPv4 Port {port}] Initiating STARTTLS...")
                server.starttls()
                logger.info("[SMTP TLS Established] Authenticating...")
                server.login(self.smtp_user, self.smtp_password)
                logger.info("[SMTP Authenticated] Sending message...")
                server.sendmail(self.from_email, [to_email], msg.as_string())
                try:
                    server.quit()
                except Exception:
                    pass
        return True

    def send_email(self, to_email: str, subject: str, template_name: str, context: dict) -> bool:
        """
        Renders template and dispatches email via IPv4 SMTP with port fallback.
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
                f"Please set SMTP_USERNAME/SMTP_USER and SMTP_PASSWORD in .env."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        primary_port = self.smtp_port
        try:
            logger.info(f"[SMTP Connecting IPv4] Host: {self.smtp_host}, Port: {primary_port}, User: {self.smtp_user}")
            self._dispatch_via_smtp(msg, to_email, primary_port)
            logger.info(f"[Email Delivered] Email '{subject}' successfully sent to '{to_email}' via Port {primary_port}")
            return True
        except Exception as primary_exc:
            fallback_port = 465 if primary_port != 465 else 587
            logger.warning(f"[SMTP Primary Port {primary_port} Error] {primary_exc}. Attempting fallback port {fallback_port}...")
            try:
                self._dispatch_via_smtp(msg, to_email, fallback_port)
                logger.info(f"[Email Delivered Fallback] Email '{subject}' sent to '{to_email}' via Port {fallback_port}")
                return True
            except Exception as fallback_exc:
                logger.error(f"[SMTP Fallback Error] Port {fallback_port} also failed: {fallback_exc}", exc_info=True)
                raise primary_exc

email_service = EmailService()
