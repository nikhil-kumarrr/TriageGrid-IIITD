import pytest

from triage_matching import triage
from triage_matching.model import load_models


@pytest.fixture(scope="module", autouse=True)
def _models():
    load_models()


@pytest.mark.parametrize("text,flag", [
    ("papa ko severe chest pain hai saans nahi aa rahi", "chest_pain"),
    ("My father is having severe chest pain and can't breathe", "breathlessness"),
    ("Heavy bleeding that won't stop after an accident", "severe_bleeding"),
    ("वो अचानक गिर गए और जवाब नहीं दे रहे", "unresponsive_collapse"),
    ("एक्सीडेंट के बाद खून नहीं रुक रहा", "severe_bleeding"),
])
def test_red_flags_force_emergency(text, flag):
    r = triage.triage(text)
    assert flag in r["red_flags"]
    assert r["care_type"] == "emergency_112" and r["urgency"] == "emergency"
    assert r["emergency_message"]


def test_non_emergency_has_no_red_flags():
    assert triage.triage("Need blood sugar test at home tomorrow morning")["red_flags"] == []


def test_vague_input_asks_follow_up_in_user_language():
    r = triage.triage("मदद चाहिए")
    assert r["care_type"] == "needs_clarification" and r["detected_language"] == "Hindi"
    assert r["follow_up_question"] and r["urgency"] is None


@pytest.mark.parametrize("text,expected", [
    ("Need wound dressing at home after surgery", "home_nursing"),
    ("papa ko insulin injection chahiye ghar pe", "home_nursing"),
    ("cbc aur thyroid test ghar se sample lekar", "lab_test_home"),
    ("Want to talk to a doctor about my reports", "teleconsultation"),
])
def test_known_intents(text, expected):
    assert triage.triage(text)["care_type"] == expected


def test_language_detection():
    assert triage.detect_language("घर पर इंजेक्शन लगवाना है") == "Hindi"
    assert triage.detect_language("ghar pe injection lagwana hai") == "Hinglish"
    assert triage.detect_language("I need an injection at home") == "English"


def test_probabilities_sum_to_one():
    assert abs(sum(triage.triage("hello koi hai?")["probabilities"].values()) - 1) < 0.02
