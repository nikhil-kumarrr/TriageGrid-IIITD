from .base import MemoryProvider, ChatMessage, StructuredFacts
from .sqlite_provider import SQLiteMemoryProvider
from .aws_provider import AWSMemoryProvider
from ...config import settings

def get_memory_provider() -> MemoryProvider:
    if settings.memory_provider == "aws":
        return AWSMemoryProvider()
    return SQLiteMemoryProvider()

__all__ = ["MemoryProvider", "ChatMessage", "StructuredFacts", "get_memory_provider", "SQLiteMemoryProvider", "AWSMemoryProvider"]
