from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

@dataclass
class LLMResponse:
    message: str
    follow_up_question: str | None = None
    structured_facts: dict[str, Any] = field(default_factory=dict)
    care_pathway_hint: str | None = None
    suggested_chips: list[str] = field(default_factory=list)
    is_emergency: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "follow_up_question": self.follow_up_question,
            "structured_facts": self.structured_facts,
            "care_pathway_hint": self.care_pathway_hint,
            "suggested_chips": self.suggested_chips,
            "is_emergency": self.is_emergency,
        }

class LLMAdapter(ABC):
    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        existing_facts: dict[str, Any],
        current_message: str,
        language: str = "English",
    ) -> LLMResponse:
        """Generate an assistant response, extract facts, and determine clarification or care path."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if credentials are provided and valid for this adapter."""
        pass

    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini', 'grok', 'mock')."""
        pass
