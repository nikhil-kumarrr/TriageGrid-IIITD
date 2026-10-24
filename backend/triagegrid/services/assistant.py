import json
from typing import Any
from datetime import datetime, timezone
from fastapi import HTTPException
from .safety import scan
from .engine import predict, roster
from .memory import get_memory_provider, StructuredFacts, ChatMessage
from .llm import get_llm_adapter, LLMResponse
from ..schemas import TriageRequest, Location, HistoryMessage
from ..storage import connect, uid, now
from ..config import settings

def detect_language(text: str, default: str = "English") -> str:
    """Detect clear language changes; keep context for short/ambiguous replies."""
    import re
    explicit = re.search(r"(?:reply|answer|respond|bolo|jawab).*?\b(english|hinglish|hindi)\b", text, re.I)
    if explicit:
        return {"english": "English", "hinglish": "Hinglish", "hindi": "Hindi"}[explicit.group(1).lower()]
    if re.search(r'[\u0900-\u097f]', text):
        return "Hindi"
    if re.search(r'\b(mujhe|mujko|mere|meri|mera|hum|aap|hai|hain|ho|raha|rahi|din|se|ko|ghar|chahiye|mummy|papa|nahi|nahin|haan|dard|bukhar|khansi|saans|pet|batao|kya|kaise|kitne)\b', text, re.I):
        return "Hinglish"
    if re.search(r"\b(i|my|have|having|feel|feeling|since|please|mother|father|need|started|days|pain|fever|cough)\b", text, re.I):
        return "English"
    return default if default in ("English", "Hindi", "Hinglish") else "English"


def merge_facts(previous: dict, extracted: dict) -> dict:
    """Keep known facts when a later extraction omits them; explicit corrections win."""
    merged = dict(previous)
    for key, value in extracted.items():
        if key == "warning_signs" and isinstance(value, dict):
            signs = dict(previous.get(key, {}))
            signs.update({k: v for k, v in value.items() if v in ("confirmed", "denied") or k not in signs})
            merged[key] = signs
        elif value is not None and value != "unspecified":
            merged[key] = value
    return merged

def get_assistant_status() -> dict[str, Any]:
    adapter = get_llm_adapter()
    mem = get_memory_provider()
    configured = adapter.is_configured()
    provider_name = adapter.provider_name()
    
    msg = "AI Assistant is ready." if configured else f"Assistant LLM is not configured. Please set {provider_name.upper()}_API_KEY on the server."
    return {
        "configured": configured,
        "provider": provider_name,
        "memory_provider": "aws" if settings.memory_provider == "aws" else "sqlite",
        "supported_languages": ["English", "Hindi", "Hinglish"],
        "message": msg,
    }

def handle_chat_message(
    session_id: str,
    user_text: str,
    language: str = "auto",
    location: Location | None = None,
    image_base64: str | None = None,
    image_mime_type: str | None = None,
    custom_adapter = None,
) -> dict[str, Any]:
    text = (user_text or "").strip()
    if not text and not image_base64:
        raise HTTPException(400, "Message or uploaded medical document is required.")
    
    if not text and image_base64:
        text = "Uploaded a medical document / prescription for analysis."

    mem = get_memory_provider()
    adapter = custom_adapter or get_llm_adapter()

    # User wording takes priority over UI language; short answers inherit the chat.
    prior_history = mem.get_history(session_id)
    previous_language = next((m.metadata.get("language") for m in reversed(prior_history)
                              if m.metadata.get("language") in ("English", "Hindi", "Hinglish")), None)
    language = detect_language(text, previous_language or language)

    # 2. Add user message to session memory
    user_meta = {"language": language}
    if image_base64:
        user_meta["has_image"] = True
        user_meta["mime"] = image_mime_type or "image/jpeg"
    user_msg = mem.add_message(session_id, "user", text, user_meta)

    # 3. Emergency Safety Check: scan current message and all user history
    history = mem.get_history(session_id)
    user_texts = [m.text for m in history if m.role == "user"]
    all_flags = []
    for t in user_texts:
        flags, _, _ = scan(t)
        all_flags.extend(flags)

    existing_facts = mem.get_facts(session_id)

    if all_flags:
        # Clinical red flag detected: immediate emergency escalation
        unique_flags = sorted(set(all_flags))
        for flag in unique_flags:
            existing_facts.warning_signs[flag] = "confirmed"
        existing_facts.severity = "critical"
        existing_facts.care_preference = "emergency_112"
        existing_facts.source_message_id = user_msg.id
        mem.update_facts(session_id, existing_facts)

        # Call engine.predict to produce official emergency request and record
        triage_req = TriageRequest(
            user_input=text,
            language=language if language in ("English", "Hindi", "Hinglish") else "auto", # type: ignore
            location=location,
            conversation_history=[HistoryMessage(role=m.role, text=m.text) for m in history[:-1]], # type: ignore
        )
        triage_resp = predict(triage_req)
        rid = uid("R")
        with connect() as db:
            db.execute(
                "INSERT INTO requests VALUES (?,?,?,?,?)",
                (rid, session_id, triage_req.model_dump_json(), triage_resp.model_dump_json(), now()),
            )

        em_msg = (
            "⚠️ CRITICAL: The symptoms you described indicate a potential emergency. "
            "Please call 112 immediately or proceed to the nearest emergency room. "
            "Do not wait for a routine home visit or video call."
        ) if language == "English" else (
            "⚠️ आपातकालीन चेतावनी: आपके बताए लक्षण गंभीर आपातकाल का संकेत देते हैं। "
            "कृपया तुरंत 112 पर कॉल करें या नजदीकी आपातकालीन केंद्र जाएँ।"
        ) if language == "Hindi" else (
            "⚠️ CRITICAL: Aapke bataye symptoms emergency indicate kar rahe hain. "
            "Kripya turant 112 par call karein ya nearest emergency hospital jayein. "
            "Ghar par visit ya routine call ka wait na karein."
        )

        asst_msg = mem.add_message(
            session_id,
            "assistant",
            em_msg,
            {
                "is_emergency": True,
                "language": language,
                "red_flags": unique_flags,
                "request_id": rid,
            },
        )

        return {
            "message": em_msg,
            "language": language,
            "follow_up_question": None,
            "structured_facts": existing_facts.to_dict(),
            "care_recommendation": {
                **triage_resp.model_dump(),
                "request_id": rid,
            },
            "suggested_chips": [
                "Call 112 Now" if language == "English" else "112 पर कॉल करें",
                "Hospital Handover" if language == "English" else "अस्पताल हैंडओवर",
                "Find Nearest Hospital" if language == "English" else "अस्पताल जानकारी",
            ],
            "next_action": {
                "type": "emergency",
                "label": "Open Emergency Help & Handover",
                "request_id": rid,
                "route": "Emergency",
            },
            "is_emergency": True,
        }

    # 4. Check if LLM Adapter is configured
    if not adapter.is_configured():
        raise HTTPException(
            503,
            f"AI Care Assistant is not configured. Please set {adapter.provider_name().upper()}_API_KEY on the backend server.",
        )

    # 5. Invoke LLM Adapter with conversation context
    messages_payload = []
    for m in history[:-1]:
        content = m.text
        question = m.metadata.get("follow_up_question") if m.role == "assistant" else None
        if question and question.casefold() not in content.casefold():
            content += "\n" + question
        messages_payload.append({"role": m.role, "text": content})
    facts_dict = existing_facts.to_dict()

    llm_resp: LLMResponse = adapter.generate(
        messages=messages_payload,
        existing_facts=facts_dict,
        current_message=text,
        language=language,
        image_base64=image_base64,
        image_mime_type=image_mime_type,
    )

    # 6. Update structured facts from LLM extraction
    updated_facts = StructuredFacts.from_dict(merge_facts(facts_dict, llm_resp.structured_facts))
    updated_facts.source_message_id = user_msg.id
    mem.update_facts(session_id, updated_facts)

    # 7. Evaluate if Care Recommendation should be produced
    care_recommendation = None
    next_action = None

    # If LLM indicates emergency
    if llm_resp.is_emergency or llm_resp.care_pathway_hint == "emergency_112":
        triage_req = TriageRequest(
            user_input=text,
            language=language if language in ("English", "Hindi", "Hinglish") else "auto", # type: ignore
            location=location,
        )
        triage_resp = predict(triage_req)
        rid = uid("R")
        with connect() as db:
            db.execute("INSERT INTO requests VALUES (?,?,?,?,?)", (rid, session_id, triage_req.model_dump_json(), triage_resp.model_dump_json(), now()))
        care_recommendation = {**triage_resp.model_dump(), "request_id": rid}
        next_action = {"type": "emergency", "label": "Open Emergency Help", "request_id": rid, "route": "Emergency"}
    elif llm_resp.follow_up_question is None or (llm_resp.care_pathway_hint and any(w in text.lower() for w in ["book", "schedule", "connect", "appointment", "proceed", "directly"])):
        # If user explicitly requested booking and care pathway was decided, clear follow_up_question to show booking action
        if llm_resp.care_pathway_hint and any(w in text.lower() for w in ["book", "schedule", "connect", "appointment", "proceed", "directly"]):
            llm_resp.follow_up_question = None

        # Ready for care pathway decision: clinical intake complete
        symptom_summary = ", ".join(updated_facts.symptoms) if updated_facts.symptoms else text
        if updated_facts.care_preference and updated_facts.care_preference != "unspecified":
            symptom_summary += f" ({updated_facts.care_preference})"
        if updated_facts.duration and updated_facts.duration != "unspecified":
            symptom_summary += f" for {updated_facts.duration}"

        triage_req = TriageRequest(
            user_input=symptom_summary,
            language=language if language in ("English", "Hindi", "Hinglish") else "auto", # type: ignore
            location=location,
            conversation_history=[HistoryMessage(role=m.role, text=m.text) for m in history], # type: ignore
        )
        try:
            triage_resp = predict(triage_req)
            rid = uid("R")
            with connect() as db:
                db.execute("INSERT INTO requests VALUES (?,?,?,?,?)", (rid, session_id, triage_req.model_dump_json(), triage_resp.model_dump_json(), now()))
            care_recommendation = {**triage_resp.model_dump(), "request_id": rid}
            if triage_resp.care_type == "emergency_112":
                next_action = {"type": "emergency", "label": "Emergency Help Required", "request_id": rid, "route": "Emergency"}
            else:
                next_action = {"type": "matches", "label": "View Caregivers & Book", "request_id": rid, "route": "Recommendation"}
        except Exception:
            pass

    # 8. Record assistant message in memory
    asst_msg = mem.add_message(
        session_id,
        "assistant",
        llm_resp.message,
        {
            "follow_up_question": llm_resp.follow_up_question,
            "language": language,
            "is_emergency": bool(care_recommendation and care_recommendation.get("care_type") == "emergency_112"),
            "chips": llm_resp.suggested_chips,
            "care_pathway_hint": llm_resp.care_pathway_hint,
            "next_action": next_action,
        },
    )

    return {
        "message": llm_resp.message,
        "language": language,
        "follow_up_question": llm_resp.follow_up_question,
        "structured_facts": updated_facts.to_dict(),
        "care_recommendation": care_recommendation,
        "suggested_chips": llm_resp.suggested_chips,
        "next_action": next_action,
        "is_emergency": bool(care_recommendation and care_recommendation.get("care_type") == "emergency_112"),
    }
