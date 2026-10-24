import json
from typing import Any
from .base import MemoryProvider, ChatMessage, StructuredFacts, utc_now
from ...storage import connect, uid

class SQLiteMemoryProvider(MemoryProvider):
    def get_history(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        if not session_id:
            return []
        with connect() as db:
            rows = db.execute(
                "SELECT id, role, text, metadata, created FROM assistant_messages WHERE session_id=? ORDER BY created ASC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        messages = []
        for r in rows:
            meta = {}
            if r["metadata"]:
                try:
                    meta = json.loads(r["metadata"])
                except Exception:
                    meta = {}
            messages.append(ChatMessage(id=r["id"], role=r["role"], text=r["text"], created=r["created"], metadata=meta))
        return messages

    def add_message(self, session_id: str, role: str, text: str, metadata: dict[str, Any] | None = None) -> ChatMessage:
        mid = uid("msg")
        created = utc_now()
        meta_json = json.dumps(metadata or {})
        with connect() as db:
            db.execute(
                "INSERT INTO assistant_messages (id, session_id, role, text, metadata, created) VALUES (?, ?, ?, ?, ?, ?)",
                (mid, session_id, role, text, meta_json, created),
            )
        return ChatMessage(id=mid, role=role, text=text, created=created, metadata=metadata or {})

    def get_facts(self, session_id: str) -> StructuredFacts:
        if not session_id:
            return StructuredFacts()
        with connect() as db:
            row = db.execute(
                "SELECT facts FROM assistant_facts WHERE session_id=?",
                (session_id,),
            ).fetchone()
        if not row or not row["facts"]:
            return StructuredFacts()
        try:
            data = json.loads(row["facts"])
            return StructuredFacts.from_dict(data)
        except Exception:
            return StructuredFacts()

    def update_facts(self, session_id: str, facts: StructuredFacts) -> None:
        if not session_id:
            return
        facts.updated_at = utc_now()
        payload = json.dumps(facts.to_dict())
        with connect() as db:
            db.execute(
                """
                INSERT INTO assistant_facts (session_id, facts, updated)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET facts=excluded.facts, updated=excluded.updated
                """,
                (session_id, payload, facts.updated_at),
            )

    def clear(self, session_id: str) -> None:
        if not session_id:
            return
        with connect() as db:
            db.execute("DELETE FROM assistant_messages WHERE session_id=?", (session_id,))
            db.execute("DELETE FROM assistant_facts WHERE session_id=?", (session_id,))

    def is_configured(self) -> bool:
        return True
