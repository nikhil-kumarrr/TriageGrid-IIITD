"""Conservative explicit-intent routing; not a mental-health diagnosis model."""
import re

def classify_intent(text: str) -> str | None:
    t = text.casefold().strip()
    # Explicit present-tense danger only; broad distress is not an emergency diagnosis.
    if re.search(r"(?:i (?:am going to|will|want to) (?:kill|hurt) myself|i cannot keep myself safe|main (?:khud ko|apne aap ko) (?:maar|nuksan)|मैं (?:खुद को|अपने आप को) (?:मार|नुकसान))", t) and not re.search(r"(?:do not|don't|not going to|nahi|nahin|नहीं)", t):
        return "immediate_safety"
    doctor = r"doctor|physician|डॉक्टर|चिकित्सक"
    if not re.search(r"(?:doctor|डॉक्टर).{0,15}(?:nahi|nahin|नहीं)|(?:no|don't want|do not want).{0,15}doctor", t):
        if re.search(doctor, t) and re.search(r"connect|consult|appointment|book|need|want|see|talk|speak|baat|bt |chahiye|milna|दिखा|बात|मिलना|चाहिए", t):
            return "doctor"
        if re.search(r"(?:book|need|want).{0,20}(?:teleconsult|video consult)|डॉक्टर परामर्श", t):
            return "doctor"
    if re.search(r"app support|technical support|customer support|app help|ऐप सहायता", t):
        return "app_support"
    if re.search(r"emotional support|anxious|anxiety|panic|depressed|lonely|overwhelmed|stressed|mentally disturb|udaas|udass|ghabrahat|akela|pareshan|उदास|घबराहट|अकेला|परेशान|भावनात्मक सहयोग", t):
        return "emotional_support"
    if re.search(r"(?:human|insaan|insan|person|someone|aadmi|इंसान|इन्सान).{0,35}(?:talk|speak|baat|bt|chahiye|बात|connect)|(?:talk|speak|connect).{0,25}(?:human|person)|human help", t):
        return "human_clarification"
    return None

COPY = {
 "English": {
  "human_clarification": ("I can help you choose the right kind of support. Live support staff are not connected in this prototype.", "Would you like a doctor consultation, emotional support, or app help?", ["Talk to a doctor", "Emotional support", "App support"]),
  "emotional_support": ("I am here to listen. We can talk, or you can choose a doctor consultation. This chat does not diagnose a mental-health condition or connect to a live counsellor.", "Would you like to tell me what is troubling you, or see doctor options?", ["I want to talk", "Talk to a doctor"]),
  "app_support": ("There is no live support agent connected. You can open app settings, or describe the technical issue here.", None, []),
  "immediate_safety": ("Your immediate safety matters. If you may hurt yourself now, contact local emergency services or go to the nearest emergency department. Ask someone you trust to stay with you and move away from anything you could use to hurt yourself.", "Are you safe right now?", ["I am safe now", "I need urgent help"]),
  "doctor": ("You can view eligible doctors and prototype consultation slots now; describing symptoms first is optional. No real doctor is connected until a real service confirms it.", None, []),
 },
 "Hinglish": {
  "human_clarification": ("Main sahi support choose karne mein madad kar sakta hoon. Is prototype mein live support staff connected nahi hai.", "Aapko doctor consultation, emotional support, ya app help chahiye?", ["Doctor se baat karni hai", "Emotional support", "App support"]),
  "emotional_support": ("Main aapki baat sun sakta hoon. Aap baat kar sakte hain ya doctor options chun sakte hain. Yeh chat mental-health diagnosis ya live counsellor connection nahi hai.", "Aap apni pareshani batana chahenge ya doctor options dekhna chahenge?", ["Main apni baat batana chahta hoon", "Doctor se baat karni hai"]),
  "app_support": ("Abhi live support agent connected nahi hai. App settings khol sakte hain ya technical problem yahan bata sakte hain.", None, []),
  "immediate_safety": ("Aapki turant safety zaroori hai. Agar abhi khud ko nuksan pahunchane ka khatra hai, local emergency help ya nearest emergency department se madad lein. Kisi bharosemand insaan ko apne paas bulayein aur nuksan pahunchane wali cheezon se door ho jayein.", "Kya aap abhi safe hain?", ["Main abhi safe hoon", "Mujhe urgent help chahiye"]),
  "doctor": ("Aap seedhe eligible doctor aur prototype consultation slots dekh sakte hain; pehle symptoms batana optional hai. Real doctor connection tabhi hoga jab real service confirm kare.", None, []),
 },
 "Hindi": {
  "human_clarification": ("मैं सही सहायता चुनने में मदद कर सकता हूँ। इस प्रोटोटाइप में लाइव सपोर्ट कर्मचारी जुड़े नहीं हैं।", "आपको डॉक्टर परामर्श, भावनात्मक सहयोग या ऐप सहायता चाहिए?", ["डॉक्टर से बात करनी है", "भावनात्मक सहयोग", "ऐप सहायता"]),
  "emotional_support": ("मैं आपकी बात सुन सकता हूँ। आप बात कर सकते हैं या डॉक्टर के विकल्प चुन सकते हैं। यह चैट मानसिक स्वास्थ्य का निदान या लाइव काउंसलर कनेक्शन नहीं है।", "आप अपनी परेशानी बताना चाहेंगे या डॉक्टर के विकल्प देखना चाहेंगे?", ["मैं अपनी बात बताना चाहता हूँ", "डॉक्टर से बात करनी है"]),
  "app_support": ("अभी लाइव सपोर्ट कर्मचारी जुड़े नहीं हैं। ऐप सेटिंग्स खोल सकते हैं या तकनीकी समस्या यहाँ बता सकते हैं।", None, []),
  "immediate_safety": ("आपकी तत्काल सुरक्षा ज़रूरी है। अभी खुद को नुकसान पहुँचाने का खतरा हो तो स्थानीय आपातकालीन सेवा या नज़दीकी आपातकालीन विभाग से मदद लें। किसी भरोसेमंद व्यक्ति को पास बुलाएँ और नुकसान पहुँचाने वाली चीज़ों से दूर हो जाएँ।", "क्या आप अभी सुरक्षित हैं?", ["मैं अभी सुरक्षित हूँ", "मुझे तत्काल मदद चाहिए"]),
  "doctor": ("आप सीधे पात्र डॉक्टर और प्रोटोटाइप परामर्श स्लॉट देख सकते हैं; पहले लक्षण बताना वैकल्पिक है। वास्तविक डॉक्टर कनेक्शन वास्तविक सेवा की पुष्टि पर ही होगा।", None, []),
 }
}
