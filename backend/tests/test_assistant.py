import pytest
from fastapi.testclient import TestClient
from triagegrid.main import app
from triagegrid.services.llm.mock_adapter import MockLLMAdapter
from triagegrid.services.llm.base import LLMResponse
from triagegrid.services.assistant import handle_chat_message
from triagegrid.services.memory import get_memory_provider, StructuredFacts

client = TestClient(app)

def create_session():
    res = client.post("/session")
    assert res.status_code == 200
    return res.json()["token"]

def test_assistant_status():
    res = client.get("/assistant/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "provider" in data
    assert "supported_languages" in data

def test_unconfigured_assistant_returns_honest_error(monkeypatch):
    # Ensure provider is unconfigured
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GROK_API_KEY", "")
    monkeypatch.setenv("ASSISTANT_PROVIDER", "gemini")

    token = create_session()
    res = client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token},
        json={"message": "I have a mild fever", "language": "English"},
    )
    # Honest 503 error rather than fake responses
    assert res.status_code == 503
    assert "not configured" in res.json()["detail"].lower()

def test_emergency_escalation_midway(monkeypatch):
    # Test emergency bypass midway through conversation
    token = create_session()
    
    # First message: non-emergency
    # Using mock adapter
    monkeypatch.setenv("ASSISTANT_PROVIDER", "mock")
    res1 = client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token},
        json={"message": "My mother has mild fever for 2 days", "language": "English"},
    )
    assert res1.status_code == 200
    d1 = res1.json()
    assert not d1.get("is_emergency")
    assert d1.get("follow_up_question") is not None

    # Second message: emergency symptom reported midway ("chest pain")
    res2 = client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token},
        json={"message": "Now she also has sudden severe chest pain and breathlessness", "language": "English"},
    )
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["is_emergency"] is True
    assert d2["follow_up_question"] is None
    assert d2["care_recommendation"]["care_type"] == "emergency_112"
    assert d2["care_recommendation"]["urgency"] == "emergency"
    assert "chest_pain" in d2["care_recommendation"]["red_flags"]
    assert d2["next_action"]["type"] == "emergency"
    assert d2["next_action"]["route"] == "Emergency"

def test_multiturn_context_and_corrections(monkeypatch):
    monkeypatch.setenv("ASSISTANT_PROVIDER", "mock")
    token = create_session()

    # Step 1: user reports fever
    res1 = client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token},
        json={"message": "My mother has fever for 2 days", "language": "English"},
    )
    assert res1.status_code == 200
    facts1 = res1.json()["structured_facts"]
    assert facts1["patient_target"] == "family_member"
    assert "fever" in facts1["symptoms"]

    # Step 2: user answers clarifying question (no breathing trouble)
    res2 = client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token},
        json={"message": "No breathing difficulty, but she needs doctor advice", "language": "English"},
    )
    assert res2.status_code == 200
    d2 = res2.json()
    facts2 = d2["structured_facts"]
    assert facts2["warning_signs"].get("breathlessness") == "denied"
    assert d2["care_recommendation"] is not None
    assert d2["care_recommendation"]["care_type"] in ["teleconsultation", "home_nursing", "paramedic_home_visit"]

    # Step 3: user manually corrects structured facts via correction endpoint
    facts2["duration"] = "4 days"
    facts2["severity"] = "moderate"
    res_correct = client.post(
        "/assistant/facts/correct",
        headers={"X-Session-Token": token},
        json={"facts": facts2},
    )
    assert res_correct.status_code == 200
    assert res_correct.json()["updated"] is True

    # Step 4: verify conversation state
    conv = client.get("/assistant/conversation", headers={"X-Session-Token": token}).json()
    assert len(conv["messages"]) >= 4
    assert conv["structured_facts"]["duration"] == "4 days"

def test_session_isolation_and_deletion(monkeypatch):
    monkeypatch.setenv("ASSISTANT_PROVIDER", "mock")
    token_a = create_session()
    token_b = create_session()

    # Session A sends message
    client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token_a},
        json={"message": "Need wound dressing for patient A", "language": "English"},
    )

    # Session B sends different message
    client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token_b},
        json={"message": "Need blood test for patient B", "language": "English"},
    )

    conv_a = client.get("/assistant/conversation", headers={"X-Session-Token": token_a}).json()
    conv_b = client.get("/assistant/conversation", headers={"X-Session-Token": token_b}).json()

    assert any("patient A" in m["text"] for m in conv_a["messages"])
    assert not any("patient B" in m["text"] for m in conv_a["messages"])
    assert any("patient B" in m["text"] for m in conv_b["messages"])
    assert not any("patient A" in m["text"] for m in conv_b["messages"])

    # Clear Session A
    del_res = client.delete("/assistant/conversation", headers={"X-Session-Token": token_a})
    assert del_res.status_code == 200

    cleared_a = client.get("/assistant/conversation", headers={"X-Session-Token": token_a}).json()
    assert len(cleared_a["messages"]) == 0

    # Session B remains intact
    conv_b_after = client.get("/assistant/conversation", headers={"X-Session-Token": token_b}).json()
    assert len(conv_b_after["messages"]) >= 2

def test_provider_failure_handling(monkeypatch):
    # Simulated provider network timeout / failure
    token = create_session()
    failing_adapter = MockLLMAdapter(should_fail=True)

    with pytest.raises(Exception):
        handle_chat_message(
            session_id="dummy_sid",
            user_text="Help with fever",
            custom_adapter=failing_adapter,
        )

def test_successful_handoff_to_booking(monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    monkeypatch.setenv("ASSISTANT_PROVIDER", "mock")
    token = create_session()
    today_ist = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()

    # Request doctor teleconsultation (which matches teleconsultation doctors without location dependency)
    res = client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token},
        json={"message": "Need a doctor video consultation for routine checkup", "language": "English"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["next_action"] is not None
    rec = data["care_recommendation"]
    req_id = rec["request_id"]
    assert len(rec["matched_caregivers"]) > 0
    matched_cg = rec["matched_caregivers"][0]["caregiver_id"]

    # Verify request exists in backend and can query slots
    slots_res = client.get(
        f"/slots?request_id={req_id}&caregiver_id={matched_cg}&day={today_ist}",
        headers={"X-Session-Token": token},
    )
    assert slots_res.status_code == 200
    assert "slots" in slots_res.json()

def test_multimodal_document_upload_and_family_memory(monkeypatch):
    monkeypatch.setenv("ASSISTANT_PROVIDER", "mock")
    token = create_session()

    # Synthetic 1x1 PNG data
    fake_png_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    res = client.post(
        "/assistant/chat",
        headers={"X-Session-Token": token},
        json={
            "message": "Here is my father's previous prescription, he has chronic hypertension and diabetes",
            "language": "English",
            "image_base64": fake_png_base64,
            "image_mime_type": "image/png"
        },
    )
    assert res.status_code == 200
    data = res.json()
    facts = data["structured_facts"]

    # Verify document extracted
    assert len(facts["uploaded_documents"]) >= 1
    assert facts["uploaded_documents"][0]["doc_type"] == "prescription"

    # Verify family history recorded
    assert len(facts["family_history"]) >= 1
    assert any(f["relation"] == "father" for f in facts["family_history"])

    # Verify persistence in conversation endpoint
    conv_res = client.get("/assistant/conversation", headers={"X-Session-Token": token})
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert len(conv_data["structured_facts"]["uploaded_documents"]) >= 1
    assert len(conv_data["structured_facts"]["family_history"]) >= 1

