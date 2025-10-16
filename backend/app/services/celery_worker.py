from celery import Celery
from app.config import settings

from app.database import get_db_context
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery("rag_worker", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    # update some configs later
)


@celery_app.task(name="process_url", bind=True, max_retries=3)
def process_url(self, job_id: str, url: str):
    pass


@celery_app.task(name="cleanup_failed_jobs")
def cleanup_failed_jobs():
    pass
