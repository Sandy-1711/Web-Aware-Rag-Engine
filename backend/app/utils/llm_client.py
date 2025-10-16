from typing import AsyncIterator, Optional, List
import google.generativeai as genai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client supporting Gemini, OpenAI, and Claude"""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.get_available_llm_provider()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.provider == "gemini":
            if not settings.gemini_api_key:
                raise ValueError("Gemini API key not configured")
            genai.configure(api_key=settings.gemini_api_key)
            self.model_name = settings.gemini_model
            self.client = genai.GenerativeModel(self.model_name)
            
        elif self.provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.model_name = settings.openai_model
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            
        elif self.provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.model_name = settings.anthropic_model
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        logger.info(f"Initialized LLM client: {self.provider} - {self.model_name}")
    
    async def generate_streaming(
        self,
        prompt: str,
        context_chunks: List[str],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming response with context
        
        Args:
            prompt: User query
            context_chunks: Retrieved document chunks for context
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        
        Yields:
            Tokens from the LLM response
        """
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature
        
        # Build context-aware prompt
        context = "\n\n".join([f"[Document {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)])
        
        full_prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided context.
If the context doesn't contain relevant information, say so clearly.

Context:
{context}

Question: {prompt}

Answer:"""
        
        try:
            if self.provider == "gemini":
                async for chunk in self._gemini_stream(full_prompt):
                    yield chunk
                    
            elif self.provider == "openai":
                async for chunk in self._openai_stream(full_prompt, max_tokens, temperature):
                    yield chunk
                    
            elif self.provider == "anthropic":
                async for chunk in self._anthropic_stream(full_prompt, max_tokens, temperature):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"\n\nError generating response: {str(e)}"
    
    async def _gemini_stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream from Gemini"""
        response = await self.client.generate_content_async(
            prompt,
            stream=True,
            generation_config=genai.GenerationConfig(
                max_output_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
    
    async def _openai_stream(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> AsyncIterator[str]:
        """Stream from OpenAI"""
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def _anthropic_stream(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> AsyncIterator[str]:
        """Stream from Anthropic Claude"""
        async with self.client.messages.stream(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text