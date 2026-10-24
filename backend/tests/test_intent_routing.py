import pytest
from fastapi.testclient import TestClient
from triagegrid.main import app
from triagegrid.services.intents import classify_intent

client=TestClient(app)
def session():return client.post('/session').json()['token']
def chat(token,text):
    r=client.post('/assistant/chat',headers={'X-Session-Token':token},json={'message':text,'language':'auto'})
    assert r.status_code==200,r.text
    return r.json()

@pytest.mark.parametrize('text',['Mujhe doctor se baat karni hai','I want to speak to a doctor','डॉक्टर से बात करनी है','I need a doctor'])
def test_doctor_access_without_llm(monkeypatch,text):
    monkeypatch.setenv('GEMINI_API_KEY','')
    monkeypatch.setenv('ASSISTANT_PROVIDER','gemini')
    d=chat(session(),text)
    assert d['intent']=='doctor'
    assert d['follow_up_question'] is None
    assert d['care_recommendation']['care_type']=='teleconsultation'
    assert d['care_recommendation']['matched_caregivers']
    assert d['next_action']['route']=='Recommendation'

def test_human_clarification_then_doctor_and_persistence():
    token=session();a=chat(token,'mujhe insaan se bt krni h')
    assert a['intent']=='human_clarification'
    assert len(a['suggested_chips'])==3
    assert a['care_recommendation'] is None
    b=chat(token,a['suggested_chips'][0])
    assert b['intent']=='doctor'
    assert b['follow_up_question'] is None
    saved=client.get('/assistant/conversation',headers={'X-Session-Token':token}).json()['messages']
    assert saved[-1]['metadata']['intent']=='doctor'
    assert saved[-1]['metadata']['next_action']['request_id']==b['next_action']['request_id']

def test_distress_not_a_diagnosis():
    d=chat(session(),'I feel lonely and overwhelmed')
    assert d['intent']=='emotional_support'
    assert not d['is_emergency']
    assert d['care_recommendation'] is None
    assert d['structured_facts']['symptoms']==[]
    assert 'diagnose' in d['message']

def test_explicit_immediate_danger():
    d=chat(session(),'I am going to hurt myself')
    assert d['is_emergency']
    assert d['next_action']['route']=='Emergency'
    assert d['care_recommendation'] is None

def test_red_flags_override_doctor_intent():
    d=chat(session(),'I want a doctor, I have severe chest pain and breathlessness')
    assert d['is_emergency']
    assert d['next_action']['route']=='Emergency'

def test_app_help():
    d=chat(session(),'App support')
    assert d['intent']=='app_support'
    assert d['next_action']['route']=='Settings'
    assert d['follow_up_question'] is None

@pytest.mark.parametrize('text',['I do not want a doctor','doctor nahi chahiye','I am not going to hurt myself','mujhe bukhar hai'])
def test_non_requests(text):assert classify_intent(text) is None


def test_hindi_emotional_chip_is_routable():
    d=chat(session(),'भावनात्मक सहयोग')
    assert d['intent']=='emotional_support'
    assert not d['is_emergency']
