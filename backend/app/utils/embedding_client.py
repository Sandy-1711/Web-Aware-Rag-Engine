import logging
from app.config import settings
from google import genai
from openai import OpenAI
from typing import List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class EmbeddingClient:
    def __init__(self, provider: str = None):
        self.provider = provider or settings.embedding_provider
        self._initialize_client()

    def _initialize_client(self):
        if self.provider == "gemini":
            if not settings.gemini_api_key:
                raise ValueError("Gemini API key not available")
            self.client = genai.Client(api_key=settings.gemini_api_key)
        elif self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not available")
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider}")
        logger.info(f"Initialized embedding client: {self.provider}")

    def embed_text(self, text: str) -> List[float]:
        if self.provider == "gemini":
            return self._gemini_embed(text)
        elif self.provider == "openai":
            return self._openai_embed(text)

    def _gemini_embed(self, text: str) -> List[float]:
        try:
            result = self.client.models.embed_content(
                model=settings.gemini_embedding_model,
                contents=text,
            )
            return result.embeddings
        except Exception as e:
            logger.error(f"Error generating Gemini Embedding: {e}")
            raise

    def _openai_embed(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                input=text, model=settings.openai_embedding_model
            )
            return response.data[0]["embedding"]
        except Exception as e:
            logger.error(f"Error generating OpenAI Embedding: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if self.provider == "gemini":
            result = self.client.models.embed_content(
                model=settings.gemini_embedding_model, contents=[texts]
            )
            return result.embeddings
        elif self.provider == "openai":
            return self._openai_embed(texts)
