from __future__ import annotations
import os
import json
import logging
from typing import Any
import httpx
from .base import LLMAdapter, LLMResponse
from .prompts import SYSTEM_INSTRUCTION, format_user_prompt
from ...config import settings

logger = logging.getLogger(__name__)

class GrokAdapter(LLMAdapter):
    def __init__(self, api_key: str | None = None, model: str = "grok-beta"):
        self.api_key = api_key or os.getenv("GROK_API_KEY", "") or os.getenv("XAI_API_KEY", settings.grok_api_key)
        self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def provider_name(self) -> str:
        return "grok"

    def generate(
        self,
        messages: list[dict[str, str]],
        existing_facts: dict[str, Any],
        current_message: str,
        language: str = "English",
    ) -> LLMResponse:
        if not self.is_configured():
            raise RuntimeError("Grok / xAI API key is not configured on the server.")

        prompt = format_user_prompt(messages, existing_facts, current_message, language)
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        attempts = 2
        last_error = None
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, headers=headers, json=payload)

                if resp.status_code != 200:
                    err_detail = "Provider request failed"
                    try:
                        err_json = resp.json()
                        err_detail = err_json.get("error", {}).get("message", resp.text[:200])
                    except Exception:
                        pass
                    raise RuntimeError(f"xAI/Grok API returned {resp.status_code}: {err_detail}")

                data = resp.json()
                raw_text = data["choices"][0]["message"]["content"]
                parsed = json.loads(raw_text)

                return LLMResponse(
                    message=parsed.get("message", "I have received your request."),
                    follow_up_question=parsed.get("follow_up_question"),
                    structured_facts=parsed.get("structured_facts", {}),
                    care_pathway_hint=parsed.get("care_pathway_hint"),
                    suggested_chips=parsed.get("suggested_chips", []),
                    is_emergency=bool(parsed.get("is_emergency", False)),
                )
            except Exception as e:
                last_error = e
                if attempt < attempts - 1:
                    continue

        raise RuntimeError(f"Grok service unavailable: {str(last_error)}")
