import os
import logging
import requests
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

class EmailService:
    def __init__(self):
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )

    @property
    def api_key(self) -> str:
        return (
            os.getenv("BREVO_API_KEY") or
            os.getenv("SENDINBLUE_API_KEY") or
            ""
        ).strip()

    @property
    def sender_email(self) -> str:
        return (
            os.getenv("BREVO_SENDER_EMAIL") or
            os.getenv("SENDER_EMAIL") or
            os.getenv("FROM_EMAIL") or
            os.getenv("SMTP_FROM_EMAIL") or
            "support@ekarthub.com"
        ).strip()

    @property
    def sender_name(self) -> str:
        return (
            os.getenv("BREVO_SENDER_NAME") or
            os.getenv("SENDER_NAME") or
            os.getenv("FROM_NAME") or
            os.getenv("SMTP_FROM_NAME") or
            "EKARTHUB"
        ).strip()

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
        Renders template and dispatches email via Brevo Transactional Email HTTPS API.
        """
        logger.info(f"[Brevo EmailService] Preparing email '{subject}' for '{to_email}' using template '{template_name}'")
        
        if not self.api_key:
            error_msg = (
                "[Brevo EmailService Config Error] BREVO_API_KEY is missing! "
                "Please configure BREVO_API_KEY in your environment variables."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        html_content = self.render_template(template_name, context)

        payload = {
            "sender": {
                "name": self.sender_name,
                "email": self.sender_email
            },
            "to": [
                {
                    "email": to_email
                }
            ],
            "subject": subject,
            "htmlContent": html_content
        }

        headers = {
            "accept": "application/json",
            "api-key": self.api_key,
            "content-type": "application/json"
        }

        logger.info(f"[Brevo API Request] Dispatching HTTP POST to {BREVO_API_URL} | Sender: '{self.sender_email}' | Recipient: '{to_email}'")

        try:
            response = requests.post(BREVO_API_URL, json=payload, headers=headers, timeout=20)
            logger.info(f"[Brevo API Response] Status Code: {response.status_code} | Body: {response.text}")

            if response.status_code in (200, 201, 202):
                logger.info(f"[Brevo Email Sent Successfully] Email '{subject}' successfully sent to '{to_email}'")
                return True
            else:
                logger.error(f"[Brevo API Error] Received status code {response.status_code}: {response.text}")
                raise Exception(f"Brevo API request failed with status code {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as req_err:
            logger.error(f"[Brevo Network Error] Failed to connect to Brevo API: {req_err}", exc_info=True)
            raise req_err
        except Exception as exc:
            logger.error(f"[Brevo Dispatch Error] Exception occurred while sending email: {exc}", exc_info=True)
            raise exc

email_service = EmailService()
