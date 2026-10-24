"""Auditable lexical rules, not a clinically validated detector."""
import re
PATTERNS = {
 "chest_pain": r"chest\s+(?:pain|tightness)|(?:seene|seena|chhati|chati)\s+(?:(?:me|mein|mai)\s+)?(?:dard|jalan)|(?:सीने|छाती)\s*(?:में|मे)?\s*(?:दर्द|जकड़न)",
 "breathlessness": r"(?:severe\s+)?(?:breathlessness|breathing\s+(?:difficulty|problem)|difficulty\s+breathing|shortness\s+of\s+breath)|(?:can.?t|cannot|unable\s+to)\s+breathe|(?:saans|sans)\s+(?:lene\s+me\s+(?:dikkat|takleef)|(?:phool|ful)\s+rahi|nahi\s+(?:aa|a)\s+rahi)|साँ?स\s*(?:लेने\s*में\s*(?:दिक्कत|तकलीफ)|नहीं\s*आ\s*रही)|सांस\s*(?:लेने\s*में\s*दिक्कत|फूल\s*रही|नहीं\s*आ\s*रही)",
 "unconsciousness": r"unconscious|unresponsive|not\s+responding|behosh|बेहोश|जवाब\s*नहीं\s*दे",
 "severe_bleeding": r"(?:heavy|severe|uncontrolled)\s+bleeding|bleeding\s+ruk\s+nahi\s+rahi|bleeding\s+(?:won.?t|will\s+not|does\s+not|not|nahi)\s*(?:stop|ruk)|(?:khoon|khun)\s+(?:nahi\s+ruk|bahut\s+beh)|खून\s*(?:नहीं\s*रुक|बहुत\s*बह)",
 "stroke_symptoms": r"face\s+droop|one.sided\s+weakness|slurred\s+speech|muh\s+tedha|मुंह\s*टेढ़ा",
 "seizure": r"seizure|convulsion|दौरा|daura",
 "high_fever_infant": r"(?:newborn|infant\s+under\s+3\s+months).{0,45}fever",
 "severe_dehydration": r"severe\s+dehydration",
 "suicidal_ideation": r"want\s+to\s+(?:die|kill\s+myself)|suicidal|jeene\s+ka\s+mann\s+nahi|जीने\s*का\s*मन\s*नहीं",
}
NEG = re.compile(r"\b(?:no|denies|denied|without|not\s+having|never\s+had|nahi|nahin)\b|नहीं|नही",re.I)
UNKNOWN = re.compile(r"pata\s+nahi|don't\s+know|do\s+not\s+know|not\s+sure|पता\s*नहीं",re.I)
def scan(text):
    flags=[]; unknown=[]; model_text=text
    clauses=re.split(r"[.!?;\n]|\b(?:but|however|lekin|magar)\b|लेकिन|मगर",text,flags=re.I)
    for concept,pattern in PATTERNS.items():
        for clause in clauses:
            for match in re.finditer(pattern,clause,re.I):
                before=' '.join(clause[:match.start()].split()[-4:])
                after=' '.join(clause[match.end():].split()[:4])
                # Embedded negative phrases such as cannot breathe / bleeding won't stop are positive signals.
                if UNKNOWN.search(before+' '+after):unknown.append(concept);continue
                negative=NEG.search(before) or NEG.search(after)
                if negative:
                    model_text=model_text.replace(clause,' ')
                elif concept not in flags:flags.append(concept)
    return flags,unknown,model_text
