import os
import json
from typing import Any
from .base import MemoryProvider, ChatMessage, StructuredFacts, utc_now
from ...config import settings

class AWSMemoryProvider(MemoryProvider):
    """
    AWS Memory implementation targeting Amazon DynamoDB for deterministic,
    sub-10ms session memory and TTL expiration.
    Evaluated against AWS Bedrock AgentCore Memory in docs/AWS_MEMORY_EVALUATION.md.
    """
    def __init__(self):
        self.region = settings.aws_region
        self.table_name = settings.aws_dynamodb_table
        self._has_creds = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
        self._client = None
        if self._has_creds:
            try:
                import boto3  # type: ignore
                self._client = boto3.resource("dynamodb", region_name=self.region)
            except Exception:
                self._client = None

    def is_configured(self) -> bool:
        return bool(self._has_creds and self._client is not None)

    def _ensure_connected(self):
        if not self.is_configured():
            raise RuntimeError(
                "AWS Memory is not configured. Missing valid AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or boto3 library."
            )

    def get_history(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        self._ensure_connected()
        table = self._client.Table(self.table_name)
        response = table.query(
            KeyConditionExpression="session_id = :sid AND record_type = :rtype",
            ExpressionAttributeValues={":sid": session_id, ":rtype": "message"},
            Limit=limit,
            ScanIndexForward=True,
        )
        items = response.get("Items", [])
        return [
            ChatMessage(
                id=item["id"],
                role=item["role"],
                text=item["text"],
                created=item["created"],
                metadata=json.loads(item.get("metadata", "{}")),
            )
            for item in items
        ]

    def add_message(self, session_id: str, role: str, text: str, metadata: dict[str, Any] | None = None) -> ChatMessage:
        self._ensure_connected()
        import secrets
        mid = f"msg_{secrets.token_hex(8)}"
        created = utc_now()
        table = self._client.Table(self.table_name)
        table.put_item(
            Item={
                "session_id": session_id,
                "sk": f"MSG#{created}#{mid}",
                "record_type": "message",
                "id": mid,
                "role": role,
                "text": text,
                "metadata": json.dumps(metadata or {}),
                "created": created,
            }
        )
        return ChatMessage(id=mid, role=role, text=text, created=created, metadata=metadata or {})

    def get_facts(self, session_id: str) -> StructuredFacts:
        self._ensure_connected()
        table = self._client.Table(self.table_name)
        response = table.get_item(Key={"session_id": session_id, "sk": "FACTS"})
        item = response.get("Item")
        if not item or "facts" not in item:
            return StructuredFacts()
        return StructuredFacts.from_dict(json.loads(item["facts"]))

    def update_facts(self, session_id: str, facts: StructuredFacts) -> None:
        self._ensure_connected()
        facts.updated_at = utc_now()
        table = self._client.Table(self.table_name)
        table.put_item(
            Item={
                "session_id": session_id,
                "sk": "FACTS",
                "record_type": "facts",
                "facts": json.dumps(facts.to_dict()),
                "updated_at": facts.updated_at,
            }
        )

    def clear(self, session_id: str) -> None:
        self._ensure_connected()
        # DynamoDB deletion scoped to this session
        table = self._client.Table(self.table_name)
        response = table.query(
            KeyConditionExpression="session_id = :sid",
            ExpressionAttributeValues={":sid": session_id},
        )
        with table.batch_writer() as batch:
            for item in response.get("Items", []):
                batch.delete_item(Key={"session_id": item["session_id"], "sk": item["sk"]})
