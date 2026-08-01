import os
import ssl
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL")
broker_url = os.getenv("CELERY_BROKER_URL", redis_url or "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", redis_url or "redis://localhost:6379/0")

celery_app = Celery(
    "ekarthub",
    broker=broker_url,
    backend=result_backend,
    include=["tasks.email_tasks"]
)

conf_dict = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_time_limit": 300,
    "broker_connection_retry_on_startup": True
}

if broker_url.startswith("rediss://"):
    conf_dict["broker_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}

if result_backend.startswith("rediss://"):
    conf_dict["redis_backend_use_ssl"] = {"ssl_cert_reqs": ssl.CERT_NONE}

celery_app.conf.update(**conf_dict)

if __name__ == "__main__":
    celery_app.start()

