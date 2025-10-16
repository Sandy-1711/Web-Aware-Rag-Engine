from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends
import logging
import time
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.url_document import URLDocument, IngestionStatus, QueryLog
from app.config import settings
import uuid
from pydantic import BaseModel
from app.services.celery_worker import process_url

logger = logging.getLogger(__name__)
router = APIRouter()


class IngestURLRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to be ingested")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.example.com",
            }
        }


class IngestURLResponse(BaseModel):
    job_id: str
    status: str
    message: str
    url: str


class JobStatusResponse(BaseModel):
    job_id: str
    url: str
    status: str
    title: Optional[str]
    num_chunks: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


@router.post("/ingest-url", response_model=IngestURLResponse)
async def ingest_url(request: IngestURLRequest, db: Session = Depends(get_db)):
    try:
        job_id = str(uuid.uuid4())
        url_str = str(request.url)
        existing = (
            db.query(URLDocument)
            .filter(
                URLDocument.url == url_str,
                URLDocument.status != IngestionStatus.COMPLETED,
            )
            .first()
        )
        if existing:
            logger.info(f"URL already inggested: {url_str}")
            return {
                "job_id": existing.job_id,
                "status": "completed",
                "message": "URL already processed",
                "url": url_str,
            }
        # if not already ingested
        doc = URLDocument(
            job_id=job_id,
            url=url_str,
            status=IngestionStatus.PENDING,
        )
        db.add(doc)
        db.commit()
        # Added task to celery
        process_url.delay(job_id, url_str)
        logger.info(f"Queued job: {job_id} for URL: {url_str}")
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "URL queued for processing",
            "url": url_str,
        }

    except Exception as e:
        logger.error(f"Error ingesting URL: {e}")
        raise HTTPException(status_code=500, detail="Error ingesting URL")


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    doc = db.query(URLDocument).filter(URLDocument.job_id == job_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=doc.job_id,
        url=doc.url,
        status=doc.status,
        title=doc.title,
        num_chunks=doc.num_chunks,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
        error_message=doc.error_message,
    )


@router.post("/query")
async def query_documents():
    pass


@router.get("/health")
async def health_check():
    # TODO Later implement health check based on db service and vector store
    return {"status": "healthy"}
