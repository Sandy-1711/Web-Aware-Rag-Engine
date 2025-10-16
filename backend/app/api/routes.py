from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime
import logging
import time

from app.database import get_db

from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest-url")
async def ingest_url():
    """This will take the url, and send it to celery worker for ingestion process"""
    pass

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    pass

@router.post("/query")
async def query_documents():
    pass
@router.get("/health")
async def health_check():
    # TODO Later implement health check based on db service and vector store
    return {"status": "healthy"}


