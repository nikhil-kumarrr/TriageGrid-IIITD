from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any
from datetime import datetime, timezone

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass
class ChatMessage:
    id: str
    role: str
    text: str
    created: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "text": self.text,
            "created": self.created,
            "metadata": self.metadata,
        }

@dataclass
class StructuredFacts:
    patient_target: str = "unspecified"
    age_group: str = "unspecified"
    symptoms: list[str] = field(default_factory=list)
    duration: str = "unspecified"
    severity: str = "unspecified"
    warning_signs: dict[str, str] = field(default_factory=dict)  # flag_name -> 'confirmed' | 'denied' | 'not_mentioned'
    existing_conditions: list[str] = field(default_factory=list)
    allergies_medications: list[str] = field(default_factory=list)
    family_history: list[dict[str, str]] = field(default_factory=list)
    uploaded_documents: list[dict[str, str]] = field(default_factory=list)
    care_preference: str = "unspecified"
    uncertainties: list[str] = field(default_factory=list)
    source_message_id: str | None = None
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredFacts":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

class MemoryProvider(ABC):
    @abstractmethod
    def get_history(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        """Fetch conversation history for the given session ordered chronologically."""
        pass

    @abstractmethod
    def add_message(self, session_id: str, role: str, text: str, metadata: dict[str, Any] | None = None) -> ChatMessage:
        """Append a message to the session conversation history."""
        pass

    @abstractmethod
    def get_facts(self, session_id: str) -> StructuredFacts:
        """Fetch the current user-confirmed structured facts for the session."""
        pass

    @abstractmethod
    def update_facts(self, session_id: str, facts: StructuredFacts) -> None:
        """Persist updated structured facts for the session."""
        pass

    @abstractmethod
    def clear(self, session_id: str) -> None:
        """Erase all messages and structured facts for the session."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the underlying storage backend is active and reachable."""
        pass
