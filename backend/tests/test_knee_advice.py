import pytest
from fastapi.testclient import TestClient
from triagegrid.main import app
client=TestClient(app)
def session():return client.post('/session').json()['token']
def send(token,text):
    res=client.post('/assistant/chat',headers={'X-Session-Token':token},json={'message':text})
    assert res.status_code==200,res.text
    return res.json()

@pytest.mark.parametrize('text,medicine',[('My knee hurts, what medicine can help?','Paracetamol'),('Mere ghutne mein dard hai dawai batao','paracetamol'),('घुटने में दर्द है दवा बताओ','पैरासिटामोल')])
def test_knee_advice_is_useful_not_refusal_only(text,medicine):
    d=send(session(),text)
    assert medicine in d['message']
    assert len(d['sources'])==2
    assert d['care_recommendation'] is None
    assert 'mg' not in d['message']

def test_short_prescription_request_keeps_latest_knee_context():
    token=session()
    send(token,'Mere ghutne mein dard hai aur Tiger Balm lagata hu')
    d=send(token,'PRESCRIBE BHI KRDE BHAI')
    assert 'paracetamol' in d['message']
    assert 'cold pack' in d['message']
    assert 'duration' not in (d['follow_up_question'] or '').lower()
    assert d['care_recommendation'] is None

def test_known_age_and_medicines_do_not_repeat_intake():
    token=session()
    client.post('/assistant/facts/correct',headers={'X-Session-Token':token},json={'facts':{'age_group':'adult','allergies_medications':['Tiger Balm'],'symptoms':['knee pain'],'duration':'2 months'}})
    d=send(token,'Mere ghutne ke dard ki medicine batao')
    assert d['follow_up_question'] is None
    assert d['structured_facts']['duration']=='2 months'
