from typing import AsyncIterator, Optional, List
from google import genai
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
            self.model_name = settings.gemini_model
            self.client = genai.Client(api_key=settings.gemini_api_key)

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
        temperature: Optional[float] = None,
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
        context = "\n\n".join(
            [f"[Document {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)]
        )

        full_prompt = f"""You are a domain-aware Retrieval-Augmented Generation (RAG) assistant.
Use ONLY the provided context to answer the question accurately.

RESPONSE POLICY:
- Stick strictly to facts found in the context.
- Do not use outside knowledge or hallucinate.
- If the answer is not present, say: "The provided context does not contain information about this."
- Always respond in plain text only. Do not use Markdown, bullet points, code blocks, or special formatting.
- Keep explanations clear and easy to follow.
- If helpful, summarize and combine information from multiple context chunks naturally in the answer.

Context:
{context}

User Question:
{prompt}

Answer (Markdown or Plain Text only):
"""


        try:
            if self.provider == "gemini":
                async for chunk in self._gemini_stream(full_prompt):
                    yield chunk

            elif self.provider == "openai":
                async for chunk in self._openai_stream(
                    full_prompt, max_tokens, temperature
                ):
                    yield chunk

            elif self.provider == "anthropic":
                async for chunk in self._anthropic_stream(
                    full_prompt, max_tokens, temperature
                ):
                    yield chunk

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"Error generating response: {str(e)}"

    async def _gemini_stream(self, prompt: str) -> AsyncIterator[str]:
        """Stream from Gemini"""
        # Use the synchronous method without await
        stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config={"max_output_tokens": settings.max_tokens},
        )

        # Iterate synchronously over the stream
        for event in stream:
            if hasattr(event, "text") and event.text:
                yield event.text

    async def _openai_stream(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> AsyncIterator[str]:
        """Stream from OpenAI"""
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _anthropic_stream(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> AsyncIterator[str]:
        """Stream from Anthropic Claude"""
        async with self.client.messages.stream(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
