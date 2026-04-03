import os
import sys
from pathlib import Path

from celery import Celery


redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

api_app_path = Path(__file__).resolve().parents[2] / "api"
if str(api_app_path) not in sys.path:
    sys.path.insert(0, str(api_app_path))

celery_app = Celery("rgp-worker", broker=redis_url, backend=redis_url)


@celery_app.task(name="rgp.healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@celery_app.task(name="rgp.run_check_run")
def run_check_run(check_run_id: str) -> dict[str, str]:
    from app.services.check_dispatch_service import check_dispatch_service

    check_dispatch_service.execute_check_run(check_run_id)
    return {"status": "ok", "check_run_id": check_run_id}
