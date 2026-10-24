import pandas as pd
import pytest

from triage_matching import config, matcher


@pytest.fixture(scope="module")
def cg():
    return matcher.load_caregivers(config.CAREGIVERS_CSV)


def test_required_skills():
    assert matcher.required_skills("Insulin injection for father", "home_nursing")[0] == ["injection_im"]
    assert matcher.required_skills("need an IV drip", "home_nursing")[0] == ["injection_iv"]
    assert matcher.required_skills("bedsore dressing", "home_nursing")[0] == ["wound_dressing"]
    assert matcher.required_skills("fever", "paramedic_home_visit")[0] == ["vitals_monitoring"]


def test_hard_filters_respected(cg):
    r = matcher.match_caregivers(cg, "home_nursing", "insulin injection", 28.5947, 77.0508, "English", top_k=50)
    by_id = cg.set_index("caregiver_id")
    assert r["candidates"]
    for c in r["candidates"]:
        row = by_id.loc[c["caregiver_id"]]
        assert row.active and row.role == "medic" and "injection_im" in row.skills_list
        assert c["distance_km"] <= row.max_radius_km


def test_ranking_sorted_and_scores_bounded(cg):
    r = matcher.match_caregivers(cg, "teleconsultation", "doctor", 28.5, 77.2, "English", top_k=5)
    s = [c["score"] for c in r["candidates"]]
    assert s == sorted(s, reverse=True) and all(0 <= x <= 1 for x in s) and r["top_score"] == s[0]


def test_teleconsult_ignores_radius(cg):
    r = matcher.match_caregivers(cg, "teleconsultation", "doctor", 28.46, 77.09, "Hindi", top_k=5)
    assert any(c["distance_km"] > 12 for c in r["candidates"])


def test_time_filter_and_message(cg):
    ok = matcher.match_caregivers(cg, "lab_test_home", "blood test", 28.5807, 77.0491, request_time="15:00")
    no = matcher.match_caregivers(cg, "lab_test_home", "blood test", 28.5807, 77.0491, request_time="10:00")
    assert ok["candidates"] and not no["candidates"] and "free" in no["message"]


def test_out_of_coverage_message(cg):
    r = matcher.match_caregivers(cg, "lab_test_home", "cbc", 28.75, 77.39, "English")
    assert r["candidates"] == [] and "covers" in r["message"]


def test_inactive_never_returned(cg):
    inactive = set(cg[~cg.active].caregiver_id)
    for ct in matcher.MATCHABLE:
        r = matcher.match_caregivers(cg, ct, "injection dressing", 28.6, 77.2, top_k=100)
        assert not inactive & {c["caregiver_id"] for c in r["candidates"]}


def test_gender_preference_boosts(cg):
    r = matcher.match_caregivers(cg, "teleconsultation", "doctor", 28.5, 77.2, "English", preferred_gender="F")
    assert r["candidates"][0]["gender"] == "F"


def test_bad_inputs(cg):
    with pytest.raises(ValueError):
        matcher.match_caregivers(cg, "emergency_112", "x", 0, 0)
    with pytest.raises(ValueError):
        matcher.match_caregivers(cg, "lab_test_home", "x", 28.5, 77.2, request_time="25:99")


def test_matches_dataset_reference_eligibility(cg):
    """Every caregiver the reference dataset matched must be eligible under our hard filters."""
    t = pd.read_csv(config.TRIAGE_CSV)
    t = t[t.care_type.isin(matcher.MATCHABLE)]
    for _, r in t.iterrows():
        ref = set(r.matched_caregiver_ids.split(";")) if isinstance(r.matched_caregiver_ids, str) else set()
        got = {c["caregiver_id"] for c in matcher.match_caregivers(
            cg, r.care_type, r.user_input, r.lat, r.lng, top_k=100)["candidates"]}
        assert ref <= got and (bool(ref) == bool(got))
