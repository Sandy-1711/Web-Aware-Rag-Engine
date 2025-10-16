from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.api.routes import router
from app.database import init_db
from fastapi.responses import JSONResponse
import logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info("Starting RAG Engine API...")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Redis URL: {settings.redis_url}")
    logger.info(f"FAISS Index Path: {settings.faiss_index_path}")

    init_db()
    logger.info("Database initialized")

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

    logger.info("Shutting down RAG Engine API...")


app = FastAPI(
    title="RAG Engine API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "RAG Engine API", "version": "1.0.0", "docs": "/docs"}
