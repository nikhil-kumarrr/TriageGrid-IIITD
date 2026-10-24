import pytest
from fastapi.testclient import TestClient
from triagegrid.main import app
from triagegrid.services.calculator import calculate
from triagegrid.services.assistant import handle_chat_message
from triagegrid.services.llm.base import LLMResponse
from triagegrid.storage import connect

client=TestClient(app)
@pytest.mark.parametrize('text,answer',[('2+2 ?','4'),('Calculate (12+8)*3','60'),('0.1+0.2','0.3'),('2^10','1024'),('२+२','4'),('9/3','3')])
def test_exact_arithmetic(text,answer):assert calculate(text).endswith('= '+answer)
@pytest.mark.parametrize('text',["__import__('os').system('id')",'2 tablets + 2 days','I have had fever for 2 days'])
def test_not_executable_or_medical_calculation(text):assert calculate(text) is None
@pytest.mark.parametrize('text',['1/0','2**1000000'])
def test_invalid_or_unbounded_math(text):assert calculate(text).startswith('Calculation error')

def test_math_after_fever_no_repeated_medical_question(monkeypatch):
    monkeypatch.setenv('ASSISTANT_PROVIDER','mock')
    token=client.post('/session').json()['token'];headers={'X-Session-Token':token}
    before=client.post('/assistant/chat',headers=headers,json={'message':'I have fever for 2 days'}).json()
    r=client.post('/assistant/chat',headers=headers,json={'message':'2+2 ?'})
    assert r.status_code==200
    d=r.json();assert d['message'].endswith('= 4')
    assert d['follow_up_question'] is None and d['care_recommendation'] is None
    assert d['structured_facts']['symptoms']==before['structured_facts']['symptoms']
    saved=client.get('/assistant/conversation',headers=headers).json()
    assert saved['messages'][-1]['metadata']['intent']=='general'

def test_general_response_cannot_trigger_triage_or_pollute_facts():
    token=client.post('/session').json()['token']
    # Use an actual session ID without exposing authentication credentials.
    with connect() as db: sid=db.execute('SELECT id FROM sessions ORDER BY rowid DESC LIMIT 1').fetchone()[0]
    class General:
        def is_configured(self):return True
        def generate(self,**kwargs):
            return LLMResponse(message='Paris is the capital of France.',intent='general',follow_up_question='How long have you had fever?',structured_facts={'symptoms':['made up fever']},care_pathway_hint='teleconsultation',suggested_chips=['Fever'])
    d=handle_chat_message(sid,'What is the capital of France?',custom_adapter=General())
    assert d['message']=='Paris is the capital of France.'
    assert d['follow_up_question'] is None
    assert d['care_recommendation'] is None
    assert d['structured_facts']['symptoms']==[]
    assert d['suggested_chips']==[]
