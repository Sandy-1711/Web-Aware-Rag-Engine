from celery import Celery
from app.config import settings
from app.models.url_document import URLDocument, IngestionStatus
from app.database import get_db_context
import logging
import hashlib
from app.services.vector_store import vector_store_manager
from app.utils.web_scraper import scraper
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery("rag_worker", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)



@celery_app.task(name="process_url", bind=True, max_retries=3, retry_backoff=True)
def process_url(self, job_id: str, url: str):
    logger.info(f"Starting processing for job {job_id} : {url}")
    with get_db_context() as db:
        try:
            doc = db.query(URLDocument).filter(URLDocument.job_id == job_id).first()
            if not doc:
                logger.error(f"Job {job_id} not found in database")
                return

            doc.status = IngestionStatus.PROCESSING
            db.commit()

            logger.info(f"Scraping URL: {url}")
            scraped_data = scraper.scrape_url(url)
            content = scraped_data["content"]
            title = scraped_data["title"]
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            logger.info(f"Adding to vector store: {url}")
            num_chunks = vector_store_manager.add_document(
                content=content,
                job_id=job_id,
                url=url,
                title=title,
            )

            doc.status = IngestionStatus.COMPLETED
            doc.title = title
            doc.content_hash = content_hash
            doc.num_chunks = num_chunks
            doc.completed_at = func.now()
            doc.error_message = None
            db.commit()
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {e}")
            doc = db.query(URLDocument).filter(URLDocument.job_id == job_id).first()
            if doc:
                doc.status = IngestionStatus.FAILED
                doc.error_message = str(e)
                doc.retry_count += 1
                db.commit()

            if self.request.retries < self.max_retries:
                self.retry(exc=e, countdown=60 * (self.request.retries + 1))
            else:
                logger.error(f"Max retries reached for job {job_id}")


@celery_app.task(name="cleanup_failed_jobs")
def cleanup_failed_jobs():
    pass
