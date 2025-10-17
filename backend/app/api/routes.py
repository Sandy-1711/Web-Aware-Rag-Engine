from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field, ConfigDict
from typing import Optional, List
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
from app.services.vector_store import vector_store_manager
from app.utils.llm_client import LLMClient
from sqlalchemy import text
from fastapi import Query
from sqlalchemy import asc, desc

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


class DocumentResponse(BaseModel):
    id: int
    job_id: str
    url: str
    status: IngestionStatus
    title: Optional[str]
    num_chunks: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int

    model_config = ConfigDict(from_attributes=True)  # ✅ Important!


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    page: int
    limit: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)  # ✅ Important!


class QueryRequest(BaseModel):
    query: str = Field(..., description="Question to ask", min_length=1)
    llm_provider: Optional[str] = Field(
        None, description="LLM provider to use (gemini, openai, anthropic)"
    )


@router.post("/ingest-url", response_model=IngestURLResponse)
async def ingest_url(request: IngestURLRequest, db: Session = Depends(get_db)):
    try:
        job_id = str(uuid.uuid4())
        url_str = str(request.url)
        existing = (
            db.query(URLDocument)
            .filter(
                URLDocument.url == url_str,
                URLDocument.status == IngestionStatus.COMPLETED,
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
            "status": IngestionStatus.PENDING,
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
async def query_documents(request: QueryRequest, db: Session = Depends(get_db)):
    query_id = str(uuid.uuid4())
    start_time = time.time()
    try:
        stats = vector_store_manager.get_stats()
        if stats["total_documents"] == 0:
            raise HTTPException(
                status_code=400, detail="No documents found in vector store"
            )
        retrieval_start = time.time()
        results = vector_store_manager.search(request.query, k=settings.top_k_results)
        retrieval_time = int((time.time() - retrieval_start) * 1000)
        if not results:
            raise HTTPException(
                status_code=404, detail="No relevant documents found for your query"
            )
        context_chunks = [doc["page_content"] for doc, _ in results]
        query_log = QueryLog(
            query_id=query_id,
            query_text=request.query,
            num_results_retrieved=len(results),
            retrieval_time_ms=retrieval_time,
            llm_provider=request.llm_provider or settings.default_llm_provider,
        )
        db.add(query_log)
        db.commit()
        llm_client = LLMClient(request.llm_provider)
        query_log.llm_model = llm_client.model_name
        db.commit()

        async def generate_stream():
            generation_start = time.time()
            full_response = ""
            try:
                async for chunk in llm_client.generate_streaming(
                    prompt=request.query, context_chunks=context_chunks
                ):
                    yield chunk
                    full_response += chunk

                generation_time = int((time.time() - generation_start) * 1000)
                total_time = int((time.time() - start_time) * 1000)

                query_log.response_generated = full_response
                query_log.generation_time_ms = generation_time
                query_log.total_time_ms = total_time
                db.commit()
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                yield f"\n\n[Error: {str(e)}]"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"X-Query-ID": query_id, "X-Results-Count": str(len(results))},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vector store stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting vector store stats")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
):
    try:
        # Validate sort_by field
        valid_sort_fields = [
            "created_at",
            "updated_at",
            "completed_at",
            "status",
            "title",
            "url",
        ]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by field. Valid options: {', '.join(valid_sort_fields)}",
            )

        # Build query
        query = db.query(URLDocument)

        # Get total count
        total = query.count()

        # Apply sorting
        sort_column = getattr(URLDocument, sort_by)
        if order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        offset = (page - 1) * limit
        documents = query.offset(offset).limit(limit).all()

        # Calculate total pages
        total_pages = (total + limit - 1) // limit

        return DocumentListResponse(
            documents=[DocumentResponse.from_orm(doc) for doc in documents],
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get details of a specific document by ID

    - **document_id**: Document ID
    """
    try:
        document = db.query(URLDocument).filter(URLDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentResponse.from_orm(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    Delete a document by ID

    - **document_id**: Document ID to delete

    Note: This only deletes the metadata from the database.
    Vector embeddings in Qdrant are not automatically deleted.
    """
    try:
        document = db.query(URLDocument).filter(URLDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Store info for response
        job_id = document.job_id
        url = document.url

        # Delete from database
        db.delete(document)
        db.commit()

        logger.info(f"Deleted document {document_id}: {url}")

        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "job_id": job_id,
            "url": url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database
        db.execute(text("SELECT 1"))
        # Check vector store
        stats = vector_store_manager.get_stats()

        return {"status": "healthy", "database": "connected", "vector_store": stats}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
