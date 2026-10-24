"""Triage inference: TF-IDF + LR pipelines (.pkl) + safety rules. No matching logic here."""
import re

from .config import EMERGENCY, NEEDS_CLARIFICATION
from .model import load_models

EMERGENCY_ESCALATE_P = 0.30        # model prob >= this -> treat as emergency (safety first)

RED_FLAG_PATTERNS = {
    "chest_pain": r"chest\s*pain|seene?\s*(?:me|mein|mai)\s*(?:\w+\s*)?dard|सीने\s*(?:में|मे)\s*(?:\S+\s*)?दर्द",
    "breathlessness": r"can'?t\s*breathe|cannot\s*breathe|breathless|short(?:ness)?\s*of\s*breath|"
                      r"saans?\s*nahi|sans\s*nahi|सा[ंँ]स\s*नही[ंं]?",
    "severe_bleeding": r"bleed|खून\s*(?:नहीं\s*)?(?:रुक|बह)|khoon\s*(?:nahi\s*)?(?:ruk|beh)",
    "unresponsive_collapse": r"collaps|unconscious|not\s*responding|response\s*nahi|jawab\s*nahi|behosh|"
                             r"gir\s*gay[ei]|गिर\s*गए|गिर\s*गई|जवाब\s*नहीं|बेहोश",
}
_RED_FLAG_RE = {k: re.compile(v, re.IGNORECASE) for k, v in RED_FLAG_PATTERNS.items()}

_HINGLISH_TOKENS = {
    "hai", "hain", "ghar", "ko", "ka", "ki", "ke", "pe", "par", "nahi", "chahiye", "karwana", "karwani",
    "karna", "karni", "aur", "se", "mein", "me", "papa", "mummy", "dadi", "dada", "dadaji", "wo", "wife",
    "ruk", "rahi", "rahe", "lagwana", "likha", "sakta", "koi", "kuch", "baat", "baare", "subah", "kal",
    "bukhar", "khansi", "saans", "dard", "bacche", "medicine", "ho", "hoon", "mujhe", "mera", "meri",
}

FOLLOW_UPS = {
    "English": "Happy to help. Could you tell me the main symptom or service you need "
               "(home visit, nursing, lab test, or teleconsult)?",
    "Hindi": "ज़रूर, मैं मदद करूँगा। कृपया बताइए कि मुख्य लक्षण या ज़रूरत क्या है "
             "(घर पर विज़िट, नर्सिंग, लैब टेस्ट या डॉक्टर से कंसल्ट)?",
    "Hinglish": "Zaroor, madad karunga. Please bataiye mukhya symptom ya service kya chahiye "
                "(home visit, nursing, lab test ya doctor consult)?",
}
EMERGENCY_MESSAGE = {
    "English": "This looks like an emergency. Call 112 immediately — do not wait for a home visit.",
    "Hindi": "यह आपातकालीन स्थिति लग रही है। तुरंत 112 पर कॉल करें — घर पर विज़िट का इंतज़ार न करें।",
    "Hinglish": "Yeh emergency lag rahi hai. Turant 112 par call karein — home visit ka wait na karein.",
}



def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("’", "'").replace("‘", "'")).strip()


def detect_language(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "English"
    deva = sum("ऀ" <= c <= "ॿ" for c in letters) / len(letters)
    if deva > 0.3:
        return "Hindi"
    toks = set(re.findall(r"[a-z']+", text.lower()))
    return "Hinglish" if toks & _HINGLISH_TOKENS else "English"


def detect_red_flags(text: str) -> list:
    return [name for name, rx in _RED_FLAG_RE.items() if rx.search(text)]


def triage(text: str) -> dict:
    care_pipe, urg_pipe, meta = load_models()
    clean = normalize(text)
    lang = detect_language(clean)
    flags = detect_red_flags(clean)

    care_p = dict(zip(care_pipe.classes_, care_pipe.predict_proba([clean])[0]))
    urg_p = dict(zip(urg_pipe.classes_, urg_pipe.predict_proba([clean])[0]))
    top_cls, top_p = max(care_p.items(), key=lambda kv: kv[1])
    thr = meta.get("conf_threshold", 0.45)

    if flags:
        care, urgency, source, conf = EMERGENCY, "emergency", "red_flag_rules", 1.0
        reasoning = f"Red-flag symptoms detected ({', '.join(flags)}); routed to emergency services, not home care."
    elif care_p.get(EMERGENCY, 0) >= EMERGENCY_ESCALATE_P or urg_p.get("emergency", 0) >= EMERGENCY_ESCALATE_P:
        care, urgency, source = EMERGENCY, "emergency", "model_escalation"
        conf = max(care_p.get(EMERGENCY, 0), urg_p.get("emergency", 0))
        reasoning = "Model flagged possible emergency; escalated as a precaution."
    elif top_cls == NEEDS_CLARIFICATION or top_p < thr:
        care, urgency, source, conf = NEEDS_CLARIFICATION, None, "model", top_p
        reasoning = ("Intent underspecified — asking a follow-up before deciding care type."
                     if top_cls == NEEDS_CLARIFICATION else
                     f"Low model confidence ({top_p:.2f} < {thr}) — asking a follow-up instead of guessing.")
    else:
        care, source, conf = top_cls, "model", top_p
        u = max(urg_p.items(), key=lambda kv: kv[1])[0]
        urgency = None if u == NEEDS_CLARIFICATION else u
        reasoning = f"Model predicted {care} (p={top_p:.2f}); urgency assessed as {urgency}."

    return {
        "care_type": care,
        "urgency": urgency,
        "red_flags": flags,
        "confidence": round(float(conf), 3),
        "source": source,
        "detected_language": lang,
        "follow_up_question": FOLLOW_UPS[lang] if care == NEEDS_CLARIFICATION else None,
        "emergency_message": EMERGENCY_MESSAGE[lang] if care == EMERGENCY else None,
        "reasoning": reasoning,
        "probabilities": {k: round(float(v), 3) for k, v in sorted(care_p.items(), key=lambda kv: -kv[1])},
    }
