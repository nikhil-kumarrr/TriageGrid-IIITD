import time
import json
from typing import Any
from .base import MemoryProvider, ChatMessage, StructuredFacts, utc_now
from ...config import settings

class AWSMemoryProvider(MemoryProvider):
    """
    Session memory backed by Amazon DynamoDB.
    Uses the standard AWS credential chain; does not promise latency or TTL.
    Evaluated against AWS Bedrock AgentCore Memory in docs/AWS_MEMORY_EVALUATION.md.
    """
    def __init__(self):
        self.region = settings.aws_region
        self.table_name = settings.aws_dynamodb_table
        self._client = None
        self._checked_at = 0.0
        self._reachable = False
        try:
            import boto3
            from botocore.config import Config
            self._client = boto3.resource(
                "dynamodb", region_name=self.region,
                config=Config(connect_timeout=3, read_timeout=5, retries={"max_attempts": 1}),
            )
        except Exception:
            self._client = None

    def is_configured(self) -> bool:
        if self._client is None:
            return False
        now = time.monotonic()
        if self._checked_at and now - self._checked_at < (30 if self._reachable else 5):
            return self._reachable
        try:
            response = self._client.meta.client.describe_table(TableName=self.table_name)
            self._reachable = response["Table"]["TableStatus"] == "ACTIVE"
        except Exception:
            self._reachable = False
        self._checked_at = now
        return self._reachable

    def _ensure_connected(self):
        if self._client is None:
            raise RuntimeError("AWS Memory unavailable. Check the AWS SDK and credential configuration.")

    def get_history(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        self._ensure_connected()
        if limit <= 0:
            return []
        table = self._client.Table(self.table_name)
        items = []
        cursor = None
        while len(items) < limit:
            query = {
                "KeyConditionExpression": "session_id = :sid AND begins_with(sk, :prefix)",
                "ExpressionAttributeValues": {":sid": session_id, ":prefix": "MSG#"},
                "Limit": limit - len(items),
                "ScanIndexForward": False,
                "ConsistentRead": True,
            }
            if cursor:
                query["ExclusiveStartKey"] = cursor
            response = table.query(**query)
            items.extend(response.get("Items", []))
            cursor = response.get("LastEvaluatedKey")
            if not cursor:
                break
        return [
            ChatMessage(id=item["id"], role=item["role"], text=item["text"],
                        created=item["created"], metadata=json.loads(item.get("metadata", "{}")))
            for item in reversed(items)
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
        cursor = None
        while True:
            query = {
                "KeyConditionExpression": "session_id = :sid",
                "ExpressionAttributeValues": {":sid": session_id},
                "ConsistentRead": True,
            }
            if cursor:
                query["ExclusiveStartKey"] = cursor
            response = table.query(**query)
            with table.batch_writer() as batch:
                for item in response.get("Items", []):
                    batch.delete_item(Key={"session_id": item["session_id"], "sk": item["sk"]})
            cursor = response.get("LastEvaluatedKey")
            if not cursor:
                break
