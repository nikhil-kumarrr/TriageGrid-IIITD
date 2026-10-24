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

class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", settings.gemini_api_key)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def provider_name(self) -> str:
        return "gemini"

    def generate(
        self,
        messages: list[dict[str, str]],
        existing_facts: dict[str, Any],
        current_message: str,
        language: str = "English",
        image_base64: str | None = None,
        image_mime_type: str | None = None,
    ) -> LLMResponse:
        if not self.is_configured():
            raise RuntimeError("Gemini API key is not configured on the server.")

        prompt = format_user_prompt(messages, existing_facts, current_message, language)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        parts: list[dict[str, Any]] = [{"text": prompt}]
        if image_base64:
            clean_b64 = image_base64.split(",")[-1] if "," in image_base64 else image_base64
            mime = image_mime_type or "image/jpeg"
            parts.append({
                "inline_data": {
                    "mime_type": mime,
                    "data": clean_b64
                }
            })

        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": parts
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        # Bounded retries: 1 retry for transient network errors
        attempts = 2
        last_error = None
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, json=payload)
                if resp.status_code == 404 and self.model != "gemini-1.5-flash":
                    # Fallback to gemini-1.5-flash if 2.5 is unavailable in the region
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                    with httpx.Client(timeout=15.0) as client:
                        resp = client.post(url, json=payload)

                if resp.status_code != 200:
                    err_detail = "Provider request failed"
                    try:
                        err_json = resp.json()
                        err_detail = err_json.get("error", {}).get("message", resp.text[:200])
                    except Exception:
                        pass
                    raise RuntimeError(f"Gemini API returned {resp.status_code}: {err_detail}")

                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
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

        raise RuntimeError(f"Gemini service unavailable: {str(last_error)}")
