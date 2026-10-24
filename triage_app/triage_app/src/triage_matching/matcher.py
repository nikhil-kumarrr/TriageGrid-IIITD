"""Rule-based caregiver matching & ranking. Reads caregivers.csv; no ML, no pickles."""
import re
from pathlib import Path

import numpy as np
import pandas as pd

HOME_VISIT = {"home_nursing", "paramedic_home_visit", "lab_test_home"}
MATCHABLE = HOME_VISIT | {"teleconsultation"}
ROLE_FOR = {
    "teleconsultation": "doctor",
    "home_nursing": "medic",
    "paramedic_home_visit": "medic",
    "lab_test_home": "phlebotomist",
}
TIER_SCORE = {"base": 0.25, "standard": 0.50, "advanced": 0.75, "expert": 1.00}

_IV = re.compile(r"\biv\b|drip|saline|ड्रिप", re.I)
_INJ = re.compile(r"inject|इंजेक्शन|insulin|इंसुलिन|\bim\b", re.I)
_DRESS = re.compile(r"dressing|bedsore|wound|post[- ]?op|operation|surgery|bandage|घाव|पट्टी|ड्रेसिंग|ऑपरेशन", re.I)
_CATH = re.compile(r"catheter|कैथेटर", re.I)
_NEB = re.compile(r"nebuli[sz]|नेबुला", re.I)


def required_skills(text: str, care_type: str):
    """Returns (hard_required_skills, preferred_skills)."""
    t = text or ""
    if care_type == "teleconsultation":
        return ["teleconsultation"], ["report_review", "prescription"]
    if care_type == "lab_test_home":
        return ["sample_collection"], ["home_phlebotomy"]
    if care_type == "paramedic_home_visit":
        return ["vitals_monitoring"], ["bp_sugar_check", "elderly_care"]
    if care_type == "home_nursing":
        hard = []
        if _IV.search(t): hard.append("injection_iv")
        elif _INJ.search(t): hard.append("injection_im")
        if _DRESS.search(t): hard.append("wound_dressing")
        if _CATH.search(t): hard.append("catheter_care")
        if _NEB.search(t): hard.append("nebulization")
        return hard, ["elderly_care", "post_surgical_care"]
    return [], []


def load_caregivers(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["active"] = df["active"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])
    df["skills_list"] = df["skills"].fillna("").str.split(";").apply(lambda xs: [x.strip() for x in xs if x.strip()])
    df["lang_list"] = df["languages"].fillna("").str.split(";").apply(lambda xs: [x.strip() for x in xs if x.strip()])
    df["tier"] = df["tier"].fillna("")
    return df


def haversine_km(lat1, lng1, lat2, lng2):
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lng2 - lng1) * p / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def _to_min(hhmm: str) -> int:
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(hhmm).strip())
    if not m or int(m[1]) > 23 or int(m[2]) > 59:
        raise ValueError(f"request_time must be HH:MM (24h), got {hhmm!r}")
    return int(m[1]) * 60 + int(m[2])


def match_caregivers(caregivers: pd.DataFrame, care_type: str, text: str, lat: float, lng: float,
                     language: str = "Hindi", request_time: str = None, preferred_gender: str = None,
                     top_k: int = 3) -> dict:
    if care_type not in MATCHABLE:
        raise ValueError(f"care_type {care_type!r} is not matchable")
    role = ROLE_FOR[care_type]
    hard, preferred = required_skills(text, care_type)
    home = care_type in HOME_VISIT
    funnel = {"total": len(caregivers)}

    cc = caregivers[caregivers.active & (caregivers.role == role)].copy()
    funnel["active_and_role"] = len(cc)
    if hard:
        cc = cc[cc.skills_list.apply(lambda s: all(k in s for k in hard))]
    funnel["has_required_skills"] = len(cc)

    cc["distance_km"] = haversine_km(lat, lng, cc.base_lat.values, cc.base_lng.values) if len(cc) else []
    if home:
        cc = cc[cc.distance_km <= cc.max_radius_km]
        funnel["within_radius"] = len(cc)
    if request_time:
        t = _to_min(request_time)
        cc = cc[cc.apply(lambda r: _to_min(r.free_from) <= t <= _to_min(r.free_until), axis=1)]
        funnel["available_at_time"] = len(cc)

    result = {"care_type": care_type, "role_required": role, "required_skills": hard,
              "preferred_skills": preferred, "candidates": [], "top_score": None, "funnel": funnel,
              "message": None}
    if cc.empty:
        stage = next((k for k, v in list(funnel.items())[1:] if v == 0), "unknown")
        why = {"active_and_role": "no active caregiver with this role",
               "has_required_skills": "no active caregiver has the required skill(s)",
               "within_radius": "no eligible caregiver covers this location",
               "available_at_time": "no eligible caregiver is free at the requested time"}.get(stage, "no match")
        result["message"] = f"No caregiver available: {why}."
        return result

    need_lang = "English" if language == "English" else "Hindi"
    weights = {"rating": 0.25, "experience": 0.10, "skills": 0.10, "language": 0.10}
    if home: weights["proximity"] = 0.35
    else:    weights["rating"] += 0.15; weights["experience"] += 0.10; weights["language"] += 0.10
    if role == "medic": weights["tier"] = 0.10
    if preferred_gender: weights["gender"] = 0.05

    def comp(r):
        c = {
            "rating": float(np.clip((r.rating - 3.5) / 1.5, 0, 1)),
            "experience": min(r.experience_years / 15, 1.0),
            "skills": (sum(k in r.skills_list for k in preferred) / len(preferred)) if preferred else 1.0,
            "language": 1.0 if need_lang in r.lang_list else 0.0,
        }
        if "proximity" in weights: c["proximity"] = max(0.0, 1 - r.distance_km / r.max_radius_km)
        if "tier" in weights: c["tier"] = TIER_SCORE.get(r.tier, 0.0)
        if "gender" in weights: c["gender"] = 1.0 if r.gender == preferred_gender else 0.0
        return c

    wsum = sum(weights.values())
    rows = []
    for _, r in cc.iterrows():
        c = comp(r)
        score = sum(weights[k] * c[k] for k in weights) / wsum
        rows.append((score, r, c))
    rows.sort(key=lambda x: (-round(x[0], 4), x[1].distance_km, -x[1].rating))

    for score, r, c in rows[:top_k]:
        result["candidates"].append({
            "caregiver_id": r.caregiver_id, "name": r["name"], "role": r.role,
            "qualification": r.qualification, "gender": r.gender,
            "languages": r.lang_list, "skills": r.skills_list,
            "distance_km": round(float(r.distance_km), 2), "rating": float(r.rating),
            "experience_years": int(r.experience_years), "tier": r.tier or None,
            "free_window": f"{r.free_from}-{r.free_until}",
            "score": round(float(score), 3),
            "score_breakdown": {k: round(v, 3) for k, v in c.items()},
        })
    result["top_score"] = result["candidates"][0]["score"]
    return result
