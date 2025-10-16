from sqlalchemy import Column, String, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class URLDocument(Base):
    __tablename__ = "url_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    url = Column(Text, nullable=False)
    status = Column(SQLEnum(IngestionStatus), default=IngestionStatus.PENDING, nullable=False)
    
    title = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    num_chunks = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<URLDocument(job_id={self.job_id}, url={self.url}, status={self.status})>"


class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(36), unique=True, index=True, nullable=False)
    query_text = Column(Text, nullable=False)
    
    num_results_retrieved = Column(Integer, default=0)
    response_generated = Column(Text, nullable=True)
    
    retrieval_time_ms = Column(Integer, nullable=True)
    generation_time_ms = Column(Integer, nullable=True)
    total_time_ms = Column(Integer, nullable=True)
    
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<QueryLog(query_id={self.query_id}, query_text={self.query_text[:50]})>"