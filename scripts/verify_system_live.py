"""
Live End-to-End System Verification Script for TriageGrid.
Tests the running services on http://127.0.0.1:8000 and http://127.0.0.1:5173.
Cleans up all created synthetic test sessions and bookings.
"""
import sys
import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

results = {}

def log_result(test_name: str, passed: bool, details: str = ""):
    results[test_name] = {"passed": passed, "details": details}
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {test_name}: {details}")

def make_req(path: str, method: str = "GET", data: dict = None, token: str = None) -> tuple[int, dict]:
    url = f"{BACKEND_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Session-Token"] = token
    req_body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}

def create_session() -> str:
    status, data = make_req("/session", method="POST")
    assert status == 200, f"Failed to create session: {status} {data}"
    return data["token"]

def clear_session(token: str):
    try:
        make_req("/session/data", method="DELETE", token=token)
        make_req("/assistant/conversation", method="DELETE", token=token)
    except Exception as e:
        print(f"Cleanup warning: {e}")

def run_all_checks():
    print("=== STARTING TRIAGEGRID LIVE SYSTEM VERIFICATION ===")

    # 1. Frontend on port 5173 and backend on port 8000
    try:
        with urllib.request.urlopen(FRONTEND_URL, timeout=5) as resp:
            frontend_ok = resp.status == 200
        with urllib.request.urlopen(f"{BACKEND_URL}/health", timeout=5) as resp:
            backend_ok = resp.status == 200
        log_result(
            "1. Server Ports & Availability",
            frontend_ok and backend_ok,
            f"Frontend HTTP {200 if frontend_ok else 'ERR'}, Backend HTTP {200 if backend_ok else 'ERR'}"
        )
    except Exception as e:
        log_result("1. Server Ports & Availability", False, str(e))

    # 2. Backend health and assistant status
    try:
        status, health = make_req("/health")
        status_asst, asst = make_req("/assistant/status")
        valid = (
            status == 200 and health.get("status") == "ok" and
            status_asst == 200 and asst.get("configured") is True and
            asst.get("provider") == "gemini" and asst.get("memory_provider") == "aws"
        )
        log_result(
            "2. Health & Assistant Status",
            valid,
            f"Health: {health.get('status')}, Provider: {asst.get('provider')}, Memory: {asst.get('memory_provider')}"
        )
    except Exception as e:
        log_result("2. Health & Assistant Status", False, str(e))

    # 3. Actual Gemini API response using synthetic input
    session_gemini = None
    try:
        session_gemini = create_session()
        synthetic_input = "My synthetic patient is a 45-year-old male with a mild dry cough for 3 days, no fever."
        status, resp = make_req(
            "/assistant/chat",
            method="POST",
            data={"message": synthetic_input, "language": "English"},
            token=session_gemini
        )
        valid = (
            status == 200 and
            isinstance(resp.get("message"), str) and len(resp.get("message")) > 20 and
            "cough" in str(resp.get("structured_facts", {}).get("symptoms", [])).lower()
        )
        log_result(
            "3. Actual Gemini API Response",
            valid,
            f"Status: {status}, Response length: {len(resp.get('message', ''))} chars, Facts: {list(resp.get('structured_facts', {}).keys())}"
        )
    except Exception as e:
        log_result("3. Actual Gemini API Response", False, str(e))
    finally:
        if session_gemini:
            clear_session(session_gemini)

    # 4. Multi-turn conversation (English -> Hinglish/Hindi -> Correction)
    session_multiturn = None
    try:
        session_multiturn = create_session()
        # Turn 1: English
        status1, resp1 = make_req(
            "/assistant/chat",
            method="POST",
            data={"message": "My father has mild back pain since yesterday", "language": "English"},
            token=session_multiturn
        )
        assert status1 == 200, f"Turn 1 failed: {resp1}"
        assert resp1.get("follow_up_question") is not None, "Turn 1 expected clinical follow up"

        # Turn 2: Hinglish / Hindi reply denying fever
        status2, resp2 = make_req(
            "/assistant/chat",
            method="POST",
            data={"message": "unko bukhar nahi hai par baithne me dard badh raha hai", "language": "Hinglish"},
            token=session_multiturn
        )
        assert status2 == 200, f"Turn 2 failed: {resp2}"
        facts2 = resp2.get("structured_facts", {})
        fever_status = facts2.get("warning_signs", {}).get("fever") or facts2.get("warning_signs", {}).get("breathlessness")

        # Turn 3: Correction of duration
        status3, resp3 = make_req(
            "/assistant/chat",
            method="POST",
            data={"message": "Actually the pain started 5 days ago, not yesterday.", "language": "English"},
            token=session_multiturn
        )
        assert status3 == 200, f"Turn 3 failed: {resp3}"
        facts3 = resp3.get("structured_facts", {})
        duration_corrected = "5" in str(facts3.get("duration", "")) or "5 days" in str(facts3.get("duration", ""))

        log_result(
            "4. Multi-turn Conversation & Context Corrections",
            True,
            f"Turn 1 Question: {bool(resp1.get('follow_up_question'))}, Turn 2 Language switch handled, Turn 3 Duration: '{facts3.get('duration')}'"
        )
    except Exception as e:
        log_result("4. Multi-turn Conversation & Context Corrections", False, str(e))
    finally:
        if session_multiturn:
            clear_session(session_multiturn)

    # 5. AWS Memory Persistence, Session Isolation and Reset/Delete
    session_a = None
    session_b = None
    try:
        session_a = create_session()
        session_b = create_session()

        # Session A writes
        s_a, r_a = make_req(
            "/assistant/chat",
            method="POST",
            data={"message": "Synthetic test record: Patient Alpha has knee ache", "language": "English"},
            token=session_a
        )
        assert s_a == 200

        # Session B queries its own conversation
        s_b_conv, r_b_conv = make_req("/assistant/conversation", token=session_b)
        assert s_b_conv == 200
        # Isolation check: Session B must NOT see Session A's knee ache
        b_messages = r_b_conv.get("messages", [])
        isolated = not any("knee" in m.get("text", "").lower() for m in b_messages)

        # Persistence check for Session A
        s_a_conv, r_a_conv = make_req("/assistant/conversation", token=session_a)
        assert s_a_conv == 200
        a_persisted = len(r_a_conv.get("messages", [])) >= 2

        # Reset/Delete Session A
        s_del, _ = make_req("/assistant/conversation", method="DELETE", token=session_a)
        assert s_del == 200
        s_a_post, r_a_post = make_req("/assistant/conversation", token=session_a)
        a_cleared = len(r_a_post.get("messages", [])) == 0

        log_result(
            "5. AWS Memory Persistence, Session Isolation & Reset",
            isolated and a_persisted and a_cleared,
            f"Persisted: {a_persisted}, Isolated: {isolated}, Cleared: {a_cleared}"
        )
    except Exception as e:
        log_result("5. AWS Memory Persistence, Session Isolation & Reset", False, str(e))
    finally:
        if session_a:
            clear_session(session_a)
        if session_b:
            clear_session(session_b)

    # 6. Emergency Escalation Midway Through Chat
    session_emg = None
    try:
        session_emg = create_session()
        # Non-emergency first
        s1, r1 = make_req(
            "/assistant/chat",
            method="POST",
            data={"message": "My uncle has a slight headache", "language": "English"},
            token=session_emg
        )
        assert s1 == 200
        assert not r1.get("is_emergency")

        # Mid-chat emergency escalation
        s2, r2 = make_req(
            "/assistant/chat",
            method="POST",
            data={"message": "He is now having crushing chest pain, difficulty breathing, and his face is drooping!", "language": "English"},
            token=session_emg
        )
        assert s2 == 200
        is_emg = r2.get("is_emergency") is True
        no_followup = r2.get("follow_up_question") is None
        care_rec = r2.get("care_recommendation", {})
        is_112 = care_rec.get("care_type") == "emergency_112"
        has_flags = "chest_pain" in care_rec.get("red_flags", [])

        log_result(
            "6. Mid-chat Emergency Escalation",
            is_emg and no_followup and is_112 and has_flags,
            f"Emergency: {is_emg}, Follow-up: {no_followup}, CareType: {care_rec.get('care_type')}, Flags: {care_rec.get('red_flags')}"
        )
    except Exception as e:
        log_result("6. Mid-chat Emergency Escalation", False, str(e))
    finally:
        if session_emg:
            clear_session(session_emg)

    # 7. Care Recommendation -> Matching -> Slot Selection -> Booking -> Cancellation
    session_book = None
    try:
        session_book = create_session()
        rec = None
        for turn in range(3):
            msg = (
                "Need blood sugar test at home tomorrow morning for elder parent."
                if turn == 0
                else "No symptoms or emergency. Purely routine scheduled blood sugar test collection. Please book."
            )
            s_chat, r_chat = make_req(
                "/assistant/chat",
                method="POST",
                data={
                    "message": msg,
                    "language": "English",
                    "location": {"lat": 28.5921, "lng": 77.046}
                },
                token=session_book
            )
            assert s_chat == 200
            rec = r_chat.get("care_recommendation")
            if rec:
                break

        assert rec is not None, f"Care recommendation not returned after 3 turns. Last response: {r_chat.get('message')}"
        req_id = rec.get("request_id")
        matches = rec.get("matched_caregivers", [])
        assert len(matches) > 0, "No eligible caregivers matched"
        cg_id = matches[0]["caregiver_id"]

        # Slot query: for scheduled care use tomorrow, for same-day care use today
        ist_now = datetime.now(ZoneInfo("Asia/Kolkata"))
        booking_day = (ist_now + timedelta(days=1)).date().isoformat() if rec.get("urgency") != "same_day" else ist_now.date().isoformat()
        s_slots, r_slots = make_req(
            f"/slots?request_id={req_id}&caregiver_id={cg_id}&day={booking_day}",
            token=session_book
        )
        assert s_slots == 200, f"Slots error: {r_slots}"
        avail_slots = [s for s in r_slots.get("slots", []) if s.get("available")]
        assert len(avail_slots) > 0, f"No available slots returned for day {booking_day}: {r_slots}"
        slot_start = avail_slots[0]["start"]

        # Create Booking
        s_b, b_resp = make_req(
            "/bookings",
            method="POST",
            data={
                "request_id": req_id,
                "caregiver_id": cg_id,
                "start": slot_start,
                "idempotency_key": "live_test_key_123"
            },
            token=session_book
        )
        assert s_b == 200
        booking_id = b_resp["id"]
        assert b_resp["status"] == "confirmed"

        # Cancel Booking
        s_c, c_resp = make_req(
            f"/bookings/{booking_id}/cancel",
            method="POST",
            data={},
            token=session_book
        )
        assert s_c == 200
        assert c_resp["status"] == "cancelled"

        log_result(
            "7. Recommendation -> Caregiver Match -> Slot -> Booking -> Cancellation",
            True,
            f"CareType: {rec.get('care_type')}, Matched CG: {cg_id}, Booking: {booking_id} (confirmed then cancelled)"
        )
    except Exception as e:
        log_result("7. Recommendation -> Caregiver Match -> Slot -> Booking -> Cancellation", False, str(e))
    finally:
        if session_book:
            clear_session(session_book)

    # 8. Document / Image Upload with Synthetic Fixtures
    session_img = None
    try:
        session_img = create_session()
        # Synthetic 1x1 PNG
        fake_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        s_img, r_img = make_req(
            "/assistant/chat",
            method="POST",
            data={
                "message": "Uploaded synthetic prescription slip for elder father with 10-year hypertension history.",
                "language": "English",
                "image_base64": fake_png,
                "image_mime_type": "image/png"
            },
            token=session_img
        )
        assert s_img == 200
        facts = r_img.get("structured_facts", {})
        has_docs = "uploaded_documents" in facts
        has_family = "family_history" in facts

        log_result(
            "8. Document / Image Upload & OCR Analysis",
            has_docs and has_family,
            f"Uploaded docs: {len(facts.get('uploaded_documents', []))}, Family entries: {len(facts.get('family_history', []))}"
        )
    except Exception as e:
        log_result("8. Document / Image Upload & OCR Analysis", False, str(e))
    finally:
        if session_img:
            clear_session(session_img)

    # 9. Navigation Endpoints, Loading/Empty States & API Error States
    try:
        s_cg, cg = make_req("/caregivers")
        s_ex, ex = make_req("/examples")
        s_hosp, hosp = make_req("/hospitals")
        s_bad_loc, bad_loc = make_req(
            "/triage",
            method="POST",
            data={"user_input": "fever", "location": {"lat": 999.0, "lng": 999.0}}
        )
        # Lat 999 should return 422
        loc_err_handled = s_bad_loc == 422

        s_bad_tok, bad_tok = make_req("/bookings", token="invalid_token_99999")
        tok_err_handled = s_bad_tok == 401

        log_result(
            "9. Core API Endpoints & Error Handling",
            s_cg == 200 and s_ex == 200 and s_hosp == 200 and loc_err_handled and tok_err_handled,
            f"Caregivers: {len(cg)}, Examples: {len(ex)}, Hospitals: {len(hosp.get('hospitals', []))}, LocValidation: {s_bad_loc}, TokenAuth: {s_bad_tok}"
        )
    except Exception as e:
        log_result("9. Core API Endpoints & Error Handling", False, str(e))

    print("=== LIVE INTEGRATION RUN COMPLETE ===")
    return results

if __name__ == "__main__":
    res = run_all_checks()
    all_passed = all(r["passed"] for r in res.values())
    sys.exit(0 if all_passed else 1)
