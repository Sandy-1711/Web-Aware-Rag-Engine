from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    database_url: str = "postgresql://postgres:postgres@localhost:5432/rag_engine"
    
    redis_url: str = "redis://localhost:6379/0"
    
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    embedding_model: str = "text-embedding-004"
    embedding_provider: str = "gemini"
    
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    
    default_llm_provider: str = "gemini"
    gemini_model: str = "gemini-1.5-flash"
    openai_model: str = "gpt-4-turbo-preview"
    anthropic_model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    debug: bool = True
    log_level: str = "INFO"
    
    faiss_index_path: str = "/app/faiss_index"
    
    def get_available_llm_provider(self) -> str:
        """Get the first available LLM provider based on API keys"""
        if self.gemini_api_key:
            return "gemini"
        elif self.openai_api_key:
            return "openai"
        elif self.anthropic_api_key:
            return "anthropic"
        else:
            raise ValueError("No LLM API key configured. Please set at least one API key.")
    
    def get_llm_model(self, provider: Optional[str] = None) -> str:
        """Get the model name for the specified provider"""
        provider = provider or self.default_llm_provider
        
        if provider == "gemini":
            return self.gemini_model
        elif provider == "openai":
            return self.openai_model
        elif provider == "anthropic":
            return self.anthropic_model
        else:
            raise ValueError(f"Unknown provider: {provider}")


settings = Settings()