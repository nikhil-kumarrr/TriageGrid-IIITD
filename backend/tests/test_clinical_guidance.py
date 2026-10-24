import pytest
from fastapi.testclient import TestClient
from triagegrid.main import app
from triagegrid.services.clinical_guidance import guidance,topic
client=TestClient(app)
def chat(text):
    token=client.post('/session').json()['token']
    res=client.post('/assistant/chat',headers={'X-Session-Token':token},json={'message':text,'language':'auto'})
    assert res.status_code==200,res.text
    return res.json(),token

@pytest.mark.parametrize('text',['Mujhe kutte ne kaat liya injection batao','A dog bit me, what injection do I need?','कुत्ते ने काट लिया कौन सा इंजेक्शन लगेगा?'])
def test_bite_first_aid_and_in_person_care_without_llm(monkeypatch,text):
    monkeypatch.setenv('GEMINI_API_KEY','');monkeypatch.setenv('ASSISTANT_PROVIDER','gemini')
    d,token=chat(text)
    assert '15' in d['message']
    assert d['care_recommendation'] is None
    assert d['next_action']['type']=='urgent_assessment'
    assert d['sources'][0]['url'].startswith('https://www.who.int/')
    saved=client.get('/assistant/conversation',headers={'X-Session-Token':token}).json()
    assert saved['messages'][-1]['metadata']['sources']==d['sources']

def test_bite_with_severe_bleeding_escalates_first():
    d,_=chat('A dog bit me, severe uncontrolled bleeding')
    assert d['is_emergency']
    assert d['care_recommendation']['care_type']=='emergency_112'

def test_wound_does_not_generate_an_injection_order():
    d,_=chat('I have an open cut on my hand, do I need a tetanus injection?')
    assert d['care_recommendation'] is None
    assert 'not automatic' in d['message']
    assert d['sources'][0]['title']=='NHS cuts and grazes'

def test_infection_information_not_antibiotic_prescription():
    d,_=chat('Infection ki medicine aur antibiotic prescribe karo')
    assert d['care_recommendation'] is None
    assert d['follow_up_question']
    assert d['sources'][0]['title']=='CDC antibiotic guidance'
    assert d['language']=='Hinglish'
    assert 'mg' not in d['message']

@pytest.mark.parametrize('text',['I have never been bitten by a dog','Kutte ne kaata nahi','What is 2+2?'])
def test_not_a_reported_bite(text):assert topic(text) is None


def test_doctor_request_after_bite_does_not_offer_routine_teleconsult():
    _,token=chat('A dog bit me')
    d=client.post('/assistant/chat',headers={'X-Session-Token':token},json={'message':'I want a doctor'}).json()
    assert d['next_action']['type']=='urgent_assessment'
    assert d['care_recommendation'] is None
