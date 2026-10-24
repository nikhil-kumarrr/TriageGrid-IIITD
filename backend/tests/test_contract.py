import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from triagegrid.main import app
from triagegrid.schemas import TriageResponse
client=TestClient(app)
def test_health():
    assert client.get('/health').json()['prediction_ready'] is True
def test_valid_request_has_exact_contract():
    r=client.post('/triage',json={'user_input':'Need wound dressing at home after surgery','location':{'lat':28.5921,'lng':77.046}})
    assert r.status_code==200
    assert set(r.json())=={'follow_up_question','care_type','urgency','red_flags','reasoning','matched_caregivers'}
    assert r.json()['care_type']=='home_nursing'
def test_invalid_location_rejected():
    assert client.post('/triage',json={'user_input':'x','location':{'lat':100,'lng':0}}).status_code==422
def test_emergency_cannot_have_matches():
    with pytest.raises(ValidationError):
        TriageResponse(follow_up_question=None,care_type='emergency_112',urgency='emergency',red_flags=['chest_pain'],reasoning='Reported symptom',matched_caregivers=[{'caregiver_id':'CG_001','score':.5,'reason':'x'}])
def test_followup_has_null_labels():
    r=client.post('/triage',json={'user_input':'doctor chahiye'}).json()
    assert r['care_type'] is None and r['urgency'] is None and r['follow_up_question']
