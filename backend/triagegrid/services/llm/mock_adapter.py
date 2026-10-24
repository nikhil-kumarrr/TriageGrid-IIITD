from __future__ import annotations
from typing import Any
import re
from .base import LLMAdapter, LLMResponse

class MockLLMAdapter(LLMAdapter):
    """
    Test fixture adapter providing predictable responses for automated testing.
    Clearly labelled as a test mock to satisfy Phase 1 test requirements.
    """
    def __init__(self, should_fail: bool = False, custom_response: LLMResponse | None = None):
        self.should_fail = should_fail
        self.custom_response = custom_response

    def is_configured(self) -> bool:
        return True

    def provider_name(self) -> str:
        return "mock"

    def generate(
        self,
        messages: list[dict[str, str]],
        existing_facts: dict[str, Any],
        current_message: str,
        language: str = "English",
        image_base64: str | None = None,
        image_mime_type: str | None = None,
    ) -> LLMResponse:
        if self.should_fail:
            raise RuntimeError("Mock provider simulated network timeout / API error")

        if self.custom_response:
            return self.custom_response

        text = current_message.lower()
        facts = dict(existing_facts or {})
        facts.setdefault("symptoms", [])
        facts.setdefault("warning_signs", {})
        facts.setdefault("uploaded_documents", [])
        facts.setdefault("family_history", [])

        if image_base64:
            facts["uploaded_documents"].append({
                "doc_type": "prescription",
                "summary": "Verified medical prescription (extracted via OCR)",
                "date": "2026-10-24"
            })
            if "paracetamol 500mg" not in facts.get("allergies_medications", []):
                facts.setdefault("allergies_medications", []).append("paracetamol 500mg")

        # Check for family history in text
        if any(w in text for w in ["diabetes", "sugar", "bp", "hypertension", "heart condition"]):
            if any(w in text for w in ["father", "papa", "dad"]):
                facts["family_history"].append({"relation": "father", "condition": "hypertension/diabetes", "timeline": "chronic"})
            elif any(w in text for w in ["mother", "mummy", "mom"]):
                facts["family_history"].append({"relation": "mother", "condition": "hypertension/diabetes", "timeline": "chronic"})

        # Check for emergency signs in mock
        if any(w in text for w in ["chest pain", "seene me dard", "unconscious", "behosh", "bleeding"]):
            facts["warning_signs"]["chest_pain"] = "confirmed"
            msg = "This sounds critical. Please seek emergency medical care immediately." if language == "English" else "यह गंभीर स्थिति लग रही है। कृपया तुरंत आपातकालीन सहायता (112) लें।"
            return LLMResponse(
                message=msg,
                follow_up_question=None,
                structured_facts=facts,
                care_pathway_hint="emergency_112",
                suggested_chips=["Call 112", "Find Emergency Hospital"],
                is_emergency=True,
            )

        # Check for patient target
        if "mother" in text or "mummy" in text or "papa" in text or "father" in text:
            facts["patient_target"] = "family_member"
            facts["age_group"] = "elderly"
        elif "myself" in text or "mere" in text or "mujhe" in text:
            facts["patient_target"] = "self"

        # Check for symptoms
        if "fever" in text or "bukhar" in text:
            if "fever" not in facts["symptoms"]:
                facts["symptoms"].append("fever")
        if "dressing" in text or "wound" in text or "ghav" in text:
            if "wound care" not in facts["symptoms"]:
                facts["symptoms"].append("wound care")
            facts["care_preference"] = "home_nursing"

        # Check duration
        if "2 days" in text or "do din" in text:
            facts["duration"] = "2 days"

        # Check for denials
        if "no breathing" in text or "saans me dikkat nahi" in text or "no chest pain" in text:
            facts["warning_signs"]["breathlessness"] = "denied"
            facts["warning_signs"]["chest_pain"] = "denied"

        # If breathing status is unknown and fever is present, ask targeted question
        if "fever" in facts.get("symptoms", []) and facts["warning_signs"].get("breathlessness") is None:
            q = "Is there any difficulty breathing, chest pain, or severe weakness?" if language == "English" else "क्या सांस लेने में दिक्कत या सीने में दर्द है?"
            chips = ["No difficulty", "Yes, having difficulty", "Only mild fever"] if language == "English" else ["कोई दिक्कत नहीं", "हाँ, सांस फूल रही है", "सिर्फ हल्का बुखार"]
            return LLMResponse(
                message=f"I understand. For the fever, let me check safety first. {q}",
                follow_up_question=q,
                structured_facts=facts,
                care_pathway_hint=None,
                suggested_chips=chips,
                is_emergency=False,
            )

        # Care pathway recommendation ready
        hint = "teleconsultation"
        if facts.get("care_preference") == "home_nursing" or "wound" in text or "dressing" in text:
            hint = "home_nursing"
        elif "blood" in text or "lab" in text or "test" in text:
            hint = "lab_test_home"

        msg = f"Based on your care needs, a {hint.replace('_', ' ')} is the recommended care pathway." if language == "English" else f"आपकी स्थिति के अनुसार {hint.replace('_', ' ')} सबसे उपयुक्त सेवा है।"

        return LLMResponse(
            message=msg,
            follow_up_question=None,
            structured_facts=facts,
            care_pathway_hint=hint,
            suggested_chips=["View Caregivers", "Book Appointment", "Ask Another Question"],
            is_emergency=False,
        )
