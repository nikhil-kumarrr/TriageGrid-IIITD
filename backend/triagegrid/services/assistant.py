import json
from typing import Any
from datetime import datetime, timezone
from fastapi import HTTPException
from .safety import scan
from .intents import classify_intent, COPY
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
    if re.search(r'\b(mujhe|mujko|mere|meri|mera|karo|dawa|dawai|kaat|kutte|hum|aap|hai|hain|ho|raha|rahi|din|se|ko|ghar|chahiye|mummy|papa|nahi|nahin|haan|dard|bukhar|khansi|saans|pet|batao|kya|kaise|kitne)\b', text, re.I):
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

    # Standalone arithmetic is a topic change, not a symptom or a clinical fact.
    from .calculator import calculate
    calculation = calculate(text) if not image_base64 else None
    if calculation is not None:
        mem.add_message(session_id, "assistant", calculation, {"language":language, "intent":"general", "follow_up_question":None, "chips":[], "next_action":None, "is_emergency":False})
        return {"message":calculation, "language":language, "intent":"general", "follow_up_question":None,
            "structured_facts":mem.get_facts(session_id).to_dict(), "care_recommendation":None,
            "suggested_chips":[], "next_action":None, "is_emergency":False}

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

    # Source-grounded bite/wound guidance must not depend on an LLM guessing a drug.
    from .clinical_guidance import guidance
    reference = guidance(text, language) if not image_base64 else None
    # "Prescribe bhi kar do" refers to the preceding patient-reported complaint.
    # Resolve the latest reported clinical topic, never an assistant-invented diagnosis.
    import re
    if reference is None and not image_base64 and re.search(r"prescrib|medicine|dawa|dawai|दवा|प्रिस्क्र", text, re.I):
        previous_patient_text = next((m.text for m in reversed(prior_history) if m.role == "user"), "")
        if previous_patient_text:
            reference = guidance(previous_patient_text, language)
    explicit_intent = classify_intent(text)
    last_guidance = next((m.metadata.get("guidance_topic") for m in reversed(prior_history) if m.role == "assistant"), None)
    if not reference and last_guidance == "bite" and explicit_intent == "doctor":
        reference = guidance("dog bite", language)
    if reference and (reference["topic"] == "bite" or explicit_intent not in {"doctor", "app_support", "human_clarification"}):
        # Continue adaptive intake after the first note instead of replaying a script.
        previous_reference = next((m.metadata.get("guidance_topic") for m in reversed(prior_history) if m.role == "assistant"), None)
        if reference["topic"] == "bite" or reference["topic"] != previous_reference or re.search(r"prescrib|medicine|dawa|दवा", text, re.I):
            action = None
            if reference["topic"] == "knee" and existing_facts.age_group != "unspecified":
                reference["question"] = {"English":"Have you already taken any pain medicine?", "Hindi":"क्या दर्द की कोई दवा पहले ली है?", "Hinglish":"Kya dard ki koi medicine pehle li hai?"}[language] if not existing_facts.allergies_medications else None
            if reference["topic"] == "bite":
                action = {"type":"urgent_assessment", "label":{"English":"Open urgent-care information", "Hindi":"तत्काल चिकित्सा जानकारी", "Hinglish":"Urgent care information dekhein"}[language], "route":"Emergency"}
            meta = {"language":language,"intent":"health","guidance_topic":reference["topic"],"sources":reference["sources"],"reference_reviewed":reference["reviewed"],"follow_up_question":reference["question"],"chips":[],"next_action":action,"is_emergency":False}
            mem.add_message(session_id,"assistant",reference["message"],meta)
            return {"message":reference["message"],"language":language,"follow_up_question":reference["question"],"structured_facts":existing_facts.to_dict(),"care_recommendation":None,"suggested_chips":[],"next_action":action,"is_emergency":False,"sources":reference["sources"]}

    # Explicit requests bypass symptom interrogation and do not require an LLM.
    intent = classify_intent(text)
    last_assistant = next((m for m in reversed(prior_history) if m.role == "assistant"), None)
    # A free-text emotional-support conversation remains with the LLM, rather than
    # repeating the support chooser on each new anxious sentence.
    if intent == "emotional_support" and last_assistant and last_assistant.metadata.get("intent") == "emotional_support":
        intent = None
    if intent:
        message, question, chips = COPY[language][intent]
        recommendation = None
        action = None
        if intent == "doctor":
            # Preserve explicitly denied warning signs even when access bypasses the LLM.
            import re
            from .safety import PATTERNS
            for clause in re.split(r"[.!?;\n]|\b(?:but|however|lekin|magar)\b|लेकिन|मगर", text, flags=re.I):
                positive, uncertain, cleaned = scan(clause)
                if cleaned != clause:
                    for concept, pattern in PATTERNS.items():
                        if re.search(pattern, clause, re.I) and concept not in positive and concept not in uncertain:
                            existing_facts.warning_signs[concept] = "denied"
            existing_facts.source_message_id = user_msg.id
            mem.update_facts(session_id, existing_facts)
            from .engine import rank
            from ..schemas import TriageResponse
            req = TriageRequest(user_input=text, language=language, location=location)
            result = TriageResponse(care_type="teleconsultation", urgency="same_day", red_flags=[], follow_up_question=None,
                reasoning="User-requested doctor access, not a clinical urgency assessment. Supplied roster and booking are simulated.",
                matched_caregivers=rank("teleconsultation", text, language, location))
            rid = uid("R")
            with connect() as db:
                db.execute("INSERT INTO requests VALUES (?,?,?,?,?)", (rid, session_id, req.model_dump_json(), result.model_dump_json(), now()))
            recommendation = {**result.model_dump(), "request_id": rid}
            action = {"type": "matches", "label": {"English":"View doctor options", "Hindi":"डॉक्टर के विकल्प देखें", "Hinglish":"Doctor options dekhein"}[language], "request_id":rid, "route":"Recommendation"}
        elif intent == "app_support":
            action = {"type":"settings", "label":{"English":"Open settings", "Hindi":"सेटिंग्स खोलें", "Hinglish":"Settings kholein"}[language], "route":"Settings"}
        elif intent == "immediate_safety":
            action = {"type":"emergency", "label":{"English":"Open urgent help", "Hindi":"तत्काल मदद खोलें", "Hinglish":"Urgent help kholein"}[language], "route":"Emergency"}
        mem.add_message(session_id, "assistant", message, {"language":language, "intent":intent,
            "follow_up_question":question, "chips":chips, "next_action":action,
            "is_emergency":intent == "immediate_safety"})
        return {"message":message, "language":language, "intent":intent, "follow_up_question":question,
            "structured_facts":existing_facts.to_dict(), "care_recommendation":recommendation,
            "suggested_chips":chips, "next_action":action, "is_emergency":intent == "immediate_safety"}

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
    # Non-medical turns may not overwrite medical facts or trigger care routing.
    if llm_resp.intent == "general" and not llm_resp.is_emergency:
        llm_resp.follow_up_question = None
        llm_resp.care_pathway_hint = None
        llm_resp.suggested_chips = []
    updated_facts = StructuredFacts.from_dict(facts_dict if llm_resp.intent == "general" else merge_facts(facts_dict, llm_resp.structured_facts))
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
    elif llm_resp.intent != "general" and (llm_resp.follow_up_question is None or (llm_resp.care_pathway_hint and any(w in text.lower() for w in ["book", "schedule", "connect", "appointment", "proceed", "directly"]))):
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
            "intent": llm_resp.intent,
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
