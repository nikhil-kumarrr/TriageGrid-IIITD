"""Streamlit UI: triage (TF-IDF + LR .pkl + safety rules) -> rule-based caregiver matching."""
import sys
from datetime import time as dtime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from triage_matching import config, matcher, triage  # noqa: E402
from triage_matching.model import load_models  # noqa: E402

st.set_page_config(page_title="Care Triage & Matching", page_icon="🩺", layout="wide")

EXAMPLES = {
    "— choose an example —": "",
    "Injection at home (Hinglish)": "papa ko insulin injection chahiye ghar pe",
    "Wound dressing (English)": "Need wound dressing at home after surgery",
    "BP / sugar check (Hindi)": "माँ का बीपी और शुगर घर पर चेक करवाना है",
    "Fever, home check-up (Hinglish)": "papa ko do din se bukhar hai aur khansi bhi",
    "Lab test at home (English)": "Need blood sugar test at home tomorrow morning",
    "Doctor consult (Hindi)": "रिपोर्ट के बारे में डॉक्टर से बात करनी है",
    "Emergency (Hindi)": "पापा को तेज सीने में दर्द है और सांस नहीं आ रही",
    "Vague request": "doctor chahiye",
}
CARE_LABEL = {
    "home_nursing": "🏠 Home nursing", "paramedic_home_visit": "🩺 Paramedic home visit",
    "lab_test_home": "🧪 Lab test at home", "teleconsultation": "💻 Teleconsultation",
    "emergency_112": "🚨 Emergency (112)", "needs_clarification": "❓ Needs clarification",
}


@st.cache_resource(show_spinner="Loading models…")
def get_models():
    return load_models()


@st.cache_data
def get_caregivers():
    return matcher.load_caregivers(config.CAREGIVERS_CSV)


def area_presets(cg: pd.DataFrame) -> dict:
    g = cg.groupby("base_area")[["base_lat", "base_lng"]].mean().round(4)
    return {a: (r.base_lat, r.base_lng) for a, r in g.sort_index().iterrows()}


def render_map(user, cands):
    rows = [{"lat": user[0], "lon": user[1], "color": "#d62728", "size": 160}]
    if cands:
        cg = get_caregivers().set_index("caregiver_id")
        rows += [{"lat": cg.loc[c["caregiver_id"], "base_lat"], "lon": cg.loc[c["caregiver_id"], "base_lng"],
                  "color": "#1f77b4", "size": 110} for c in cands]
    st.map(pd.DataFrame(rows), color="color", size="size")
    st.caption("🔴 you  ·  🔵 matched caregivers (base location)")


def show_result(res):
    t, m, action = res["triage"], res["matching"], res["action"]
    if action == "call_112":
        st.error(f"🚨 {t['emergency_message']}", icon="🚨")
    elif action == "ask_follow_up":
        st.info(f"❓ {t['follow_up_question']}")
    elif action == "no_caregiver_available":
        st.warning(f"No caregiver available — {m['message']}")
    else:
        st.success(f"Found {len(m['candidates'])} caregiver(s).")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Care type", CARE_LABEL.get(t["care_type"], t["care_type"]))
    c2.metric("Urgency", (t["urgency"] or "—").replace("_", " "))
    c3.metric("Confidence", f"{t['confidence']:.0%}")
    c4.metric("Language", t["detected_language"])
    if t["red_flags"]:
        st.markdown("**Red flags:** " + ", ".join(f"`{f}`" for f in t["red_flags"]))
    st.caption(f"Source: `{t['source']}` — {t['reasoning']}")

    with st.expander("Model probabilities"):
        st.bar_chart(pd.Series(t["probabilities"], name="probability"), horizontal=True)

    if m and m["candidates"]:
        st.subheader("Matched caregivers")
        df = pd.DataFrame(m["candidates"])
        df["languages"] = df.languages.str.join(", ")
        df["tier"] = df.tier.fillna("—")
        st.dataframe(df[["caregiver_id", "name", "role", "qualification", "gender", "languages", "distance_km",
                         "rating", "experience_years", "tier", "free_window", "score"]],
                     hide_index=True, width="stretch",
                     column_config={"score": st.column_config.ProgressColumn("score", min_value=0, max_value=1,
                                                                            format="%.2f")})
        with st.expander("Why this ranking? (score breakdown)"):
            st.dataframe(pd.DataFrame([{"caregiver": c["caregiver_id"], **c["score_breakdown"]}
                                       for c in m["candidates"]]), hide_index=True)
            st.caption("Weights: proximity .35 · rating .25 · experience .10 · preferred skills .10 · "
                       "language .10 · tier .10 (medics) · gender preference .05 (if set).")
    if m:
        with st.expander("Matching funnel"):
            st.write({"required_skills": m["required_skills"], **m["funnel"]})
    render_map(res["user_loc"], m["candidates"] if m else [])


def run(text, lat, lng, request_time, gender, top_k):
    t = triage.triage(text)
    ct = t["care_type"]
    if ct == config.EMERGENCY:
        action, m = "call_112", None
    elif ct == config.NEEDS_CLARIFICATION:
        action, m = "ask_follow_up", None
    else:
        m = matcher.match_caregivers(get_caregivers(), ct, text, lat, lng, language=t["detected_language"],
                                     request_time=request_time, preferred_gender=gender, top_k=top_k)
        action = "matched" if m["candidates"] else "no_caregiver_available"
    return {"action": action, "triage": t, "matching": m, "user_loc": (lat, lng)}


# ───────────────────────────── sidebar ─────────────────────────────
get_models()
cg_df = get_caregivers()
presets = area_presets(cg_df)

with st.sidebar:
    st.header("Matching options")
    top_k = st.slider("Max caregivers", 1, 5, 3)
    use_time = st.checkbox("Filter by time slot")
    req_time = st.time_input("Requested time", dtime(15, 0)) if use_time else None
    gender = st.selectbox("Preferred caregiver gender", ["Any", "F", "M"])
    st.divider()
    st.caption("⚠️ Decision-support demo — **not medical advice**. In an emergency call **112**.")

st.title("🩺 Care Triage & Caregiver Matching")
st.caption("Text → triage (TF-IDF + Logistic Regression + safety rules) → rule-based caregiver matching.")
tab_main, tab_cg, tab_model = st.tabs(["Triage & Match", "Caregivers", "Model info"])

# ───────────────────────────── tab 1 ─────────────────────────────
with tab_main:
    left, right = st.columns([3, 2])
    with left:
        ex = st.selectbox("Try an example", list(EXAMPLES))
        text = st.text_area("Describe the need (English / हिंदी / Hinglish)", value=EXAMPLES[ex], height=100,
                            key=f"text_{ex}", placeholder="e.g. mummy ka bp sugar ghar pe check karwana hai")
    with right:
        area = st.selectbox("Your area", ["Custom"] + list(presets), index=list(presets).index("Saket") + 1)
        dlat, dlng = presets.get(area, (28.6139, 77.2090))
        a, b = st.columns(2)
        lat = a.number_input("Latitude", value=float(dlat), format="%.4f", step=0.001, key=f"lat_{area}")
        lng = b.number_input("Longitude", value=float(dlng), format="%.4f", step=0.001, key=f"lng_{area}")

    if st.button("Find care", type="primary", disabled=not text.strip()):
        rt = req_time.strftime("%H:%M") if req_time else None
        st.session_state["result"] = run(text.strip(), lat, lng, rt, None if gender == "Any" else gender, top_k)
    if "result" in st.session_state:
        st.divider()
        show_result(st.session_state["result"])

# ───────────────────────────── tab 2 ─────────────────────────────
with tab_cg:
    f1, f2 = st.columns(2)
    roles = f1.multiselect("Role", sorted(cg_df.role.unique()), default=sorted(cg_df.role.unique()))
    only_active = f2.checkbox("Active only", value=True)
    view = cg_df[cg_df.role.isin(roles) & (cg_df.active | (not only_active))]
    st.dataframe(view.drop(columns=["skills_list", "lang_list"]), hide_index=True, width="stretch")
    st.map(view.rename(columns={"base_lat": "lat", "base_lng": "lon"})[["lat", "lon"]])
    st.caption(f"{len(view)} of {len(cg_df)} caregivers")

# ───────────────────────────── tab 3 ─────────────────────────────
with tab_model:
    _, _, meta = get_models()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CV accuracy (group-wise)", f"{meta['cv_group_accuracy']:.1%}")
    m2.metric("CV macro-F1", f"{meta['cv_group_macro_f1']:.2f}")
    m3.metric("Training rows / unique texts", f"{meta['n_rows']} / {meta['n_unique_texts']}")
    m4.metric("Confidence threshold", meta["conf_threshold"])
    st.caption(f"Trained {meta['trained_at_utc']} · sklearn {meta['sklearn_version']} · C={meta['best_C']}")
    st.warning("Training data has only ~65 unique sentences, so the honest (group-wise CV) score is far below "
               "a random split. Red-flag rules and the low-confidence follow-up act as safety nets. "
               "Retrain on real logs: `make train`.")
    per = pd.DataFrame(meta.get("cv_per_class", {})).T.drop(index=["accuracy"], errors="ignore")
    if not per.empty:
        st.dataframe(per[["precision", "recall", "f1-score", "support"]], width="stretch")
    if config.CM_PATH.exists():
        st.image(str(config.CM_PATH), caption="Out-of-fold confusion matrix", width=520)
