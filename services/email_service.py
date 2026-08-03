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
    def api_key(self):
        return (
            os.getenv("BREVO_API_KEY")
            or os.getenv("SENDINBLUE_API_KEY")
            or ""
        ).strip()

    @property
    def sender_email(self):
        return (
            os.getenv("BREVO_SENDER_EMAIL")
            or os.getenv("SENDER_EMAIL")
            or os.getenv("FROM_EMAIL")
            or os.getenv("SMTP_FROM_EMAIL")
            or "support@ekarthub.com"
        ).strip()

    @property
    def sender_name(self):
        return (
            os.getenv("BREVO_SENDER_NAME")
            or os.getenv("SENDER_NAME")
            or os.getenv("FROM_NAME")
            or os.getenv("SMTP_FROM_NAME")
            or "EKARTHUB"
        ).strip()

    def render_template(self, template_name: str, context: dict):

        print("=" * 70)
        print("TEMPLATE RENDER START")
        print("Template:", template_name)
        print("Templates Directory:", TEMPLATES_DIR)
        print("=" * 70)

        full_context = {
            "frontend_url": self.frontend_url,
            "current_year": datetime.utcnow().year,
            **context
        }

        template = self.jinja_env.get_template(template_name)

        html = template.render(full_context)

        print("=" * 70)
        print("TEMPLATE RENDER SUCCESS")
        print("=" * 70)

        return html

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict
    ):

        print("\n")
        print("=" * 70)
        print("EMAIL SERVICE STARTED")
        print("=" * 70)

        print("Recipient :", to_email)
        print("Subject   :", subject)
        print("Template  :", template_name)

        print("\nEnvironment")

        print("BREVO_API_KEY Exists :", bool(self.api_key))
        print("Sender Email         :", self.sender_email)
        print("Sender Name          :", self.sender_name)

        if not self.api_key:
            print("BREVO API KEY MISSING")
            raise ValueError("BREVO_API_KEY missing")

        try:

            html_content = self.render_template(
                template_name,
                context
            )

        except Exception as e:

            print("=" * 70)
            print("TEMPLATE ERROR")
            print(type(e).__name__)
            print(e)
            print("=" * 70)

            raise

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

        print("=" * 70)
        print("CALLING BREVO API")
        print(BREVO_API_URL)
        print("=" * 70)

        try:

            response = requests.post(
                BREVO_API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )

            print("=" * 70)
            print("BREVO RESPONSE")
            print("Status :", response.status_code)
            print("Body   :", response.text)
            print("=" * 70)

            if response.status_code in (200, 201, 202):

                print("EMAIL SENT SUCCESSFULLY")

                return True

            raise Exception(
                f"Brevo Error {response.status_code}: {response.text}"
            )

        except Exception as e:

            print("=" * 70)
            print("EMAIL SEND FAILED")
            print(type(e).__name__)
            print(e)
            print("=" * 70)

            raise


email_service = EmailService()