from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.routes import router
from app.database import init_db
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info("Starting RAG Engine API...")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    logger.info(f"Qdrant Collection: {settings.qdrant_collection_name}")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Log available LLM providers
    providers = []
    if settings.gemini_api_key:
        providers.append("Gemini")
    if settings.openai_api_key:
        providers.append("OpenAI")
    if settings.anthropic_api_key:
        providers.append("Anthropic")
    
    logger.info(f"Available LLM providers: {', '.join(providers)}")
    logger.info(f"Default provider: {settings.default_llm_provider}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG Engine API...")


# Create FastAPI app
app = FastAPI(
    title="RAG Engine API",
    description="Scalable Web-Aware RAG Engine with Asynchronous Ingestion",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["RAG Engine"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Engine API",
        "version": "1.0.0",
        "docs": "/docs"
    }