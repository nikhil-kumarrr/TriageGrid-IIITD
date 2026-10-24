import os
from .base import LLMAdapter, LLMResponse
from .gemini_adapter import GeminiAdapter
from .grok_adapter import GrokAdapter
from .mock_adapter import MockLLMAdapter
from ...config import settings

def get_llm_adapter() -> LLMAdapter:
    provider = os.getenv("ASSISTANT_PROVIDER", settings.assistant_provider).lower()
    if provider == "mock":
        return MockLLMAdapter()
    elif provider in ("grok", "xai"):
        return GrokAdapter()
    else:
        # default to gemini
        return GeminiAdapter()

__all__ = ["LLMAdapter", "LLMResponse", "get_llm_adapter", "GeminiAdapter", "GrokAdapter", "MockLLMAdapter"]
