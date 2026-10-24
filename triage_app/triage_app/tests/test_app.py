from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


def _run(text, area="Dwarka"):
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    next(s for s in at.selectbox if s.label == "Your area").set_value(area)
    at.run()
    at.text_area[0].set_value(text).run()          # enables the button
    at.button[0].click().run()
    assert not at.exception
    return at


def test_app_loads():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception and at.title[0].value.endswith("Caregiver Matching")


def test_match_flow_shows_caregivers():
    at = _run("papa ko insulin injection chahiye ghar pe")
    assert any("Found" in s.value for s in at.success)


def test_emergency_flow_shows_alert():
    at = _run("papa ko severe chest pain hai saans nahi aa rahi")
    assert any("112" in e.value for e in at.error)


def test_vague_flow_asks_follow_up():
    at = _run("doctor chahiye")
    assert any("bataiye" in i.value or "Could you tell me" in i.value for i in at.info)
