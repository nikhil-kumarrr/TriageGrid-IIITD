from triagegrid.storage import new_session, session_for, connect
from triagegrid.services.assistant import detect_language, handle_chat_message, merge_facts
from triagegrid.services.llm.base import LLMResponse
from triagegrid.services.memory import get_memory_provider


class CaptureAdapter:
    def __init__(self):
        self.calls = []

    def is_configured(self):
        return True

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return LLMResponse(
            message='Samajh gaya.',
            follow_up_question='Khansi kab shuru hui?',
            structured_facts={'patient_target': 'self', 'duration': '4 days', 'symptoms': ['fever']},
            suggested_chips=['Aaj', 'Kal', 'Pata nahi'],
        )


def test_language_matches_input_and_ambiguous_replies_keep_context():
    assert detect_language('mujhe 4 din se bukhar aa raha hai', 'English') == 'Hinglish'
    assert detect_language('मुझे बुखार है', 'English') == 'Hindi'
    assert detect_language('I have a cough', 'Hinglish') == 'English'
    assert detect_language('yes', 'Hinglish') == 'Hinglish'
    assert detect_language('Reply in English please', 'Hindi') == 'English'


def test_conversation_remembers_language_and_saves_question_separately():
    session = session_for(new_session())
    adapter = CaptureAdapter()
    mem = get_memory_provider()
    try:
        first = handle_chat_message(session, 'mujhe 4 din se bukhar aa raha hai', language='English', custom_adapter=adapter)
        assert first['language'] == 'Hinglish'
        handle_chat_message(session, 'yes', language='English', custom_adapter=adapter)
        assert [c['language'] for c in adapter.calls] == ['Hinglish', 'Hinglish']
        assert adapter.calls[1]['existing_facts']['duration'] == '4 days'
        # Current turn appears only in current_message, not duplicated in history.
        assert adapter.calls[1]['messages'][-1]['role'] == 'assistant'
        assert 'Khansi kab shuru hui?' in adapter.calls[1]['messages'][-1]['text']
        history = mem.get_history(session)
        assert history[-1].metadata['follow_up_question'] == 'Khansi kab shuru hui?'
        assert history[-1].metadata['language'] == 'Hinglish'
    finally:
        mem.clear(session)
        with connect() as db:
            db.execute("DELETE FROM sessions WHERE id=?", (session,))


def test_partial_extraction_preserves_known_facts_but_applies_corrections():
    previous = {'duration': '4 days', 'warning_signs': {'breathlessness': 'denied'}, 'symptoms': ['fever']}
    merged = merge_facts(previous, {'duration': 'unspecified', 'warning_signs': {'breathlessness': 'not_mentioned'}})
    assert merged['duration'] == '4 days'
    assert merged['warning_signs']['breathlessness'] == 'denied'
    corrected = merge_facts(merged, {'duration': '2 days', 'symptoms': [], 'warning_signs': {'breathlessness': 'confirmed'}})
    assert corrected['duration'] == '2 days'
    assert corrected['symptoms'] == []
    assert corrected['warning_signs']['breathlessness'] == 'confirmed'
