import json
from datetime import datetime,timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import pytest
from fastapi.testclient import TestClient
from triagegrid.main import app
from triagegrid import storage
from triagegrid.services import hospitals
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'settings',SimpleNamespace(database_path=tmp_path/'test.sqlite3'))
    with TestClient(app) as c:yield c

def session(c):return {'X-Session-Token':c.post('/session').json()['token']}
def request(c,h,text='Need wound dressing at home after surgery'):
    r=c.post('/ui/triage',headers=h,json={'user_input':text,'location':{'lat':28.5921,'lng':77.046}})
    assert r.status_code==200,r.text
    return r.json()
def booking_data(c,h):
    r=request(c,h,'Need blood sugar test at home tomorrow morning');cid=r['result']['matched_caregivers'][0]['caregiver_id'];day=(datetime.now(ZoneInfo('Asia/Kolkata'))+timedelta(days=1)).date().isoformat()
    s=c.get('/slots',headers=h,params={'request_id':r['request_id'],'caregiver_id':cid,'day':day});assert s.status_code==200,s.text
    slot=next(s for s in s.json()['slots'] if s['available'])
    return {'request_id':r['request_id'],'caregiver_id':cid,'start':slot['start'],'idempotency_key':'unique-key-123'}
def test_session_required(client):assert client.get('/bookings').status_code==401
def test_booking_idempotency_cancel_and_ownership(client):
    h=session(client);data=booking_data(client,h)
    b=client.post('/bookings',headers=h,json=data);assert b.status_code==200,b.text
    assert client.post('/bookings',headers=h,json=data).json()['id']==b.json()['id']
    other=session(client)
    assert client.post('/bookings/'+b.json()['id']+'/cancel',headers=other,json={}).status_code==404
    assert client.get('/bookings',headers=other).json()==[]
    assert len(client.get('/bookings',headers=h).json())==1
    assert client.post('/bookings/'+b.json()['id']+'/cancel',headers=h,json={}).status_code==200
    assert client.get('/bookings',headers=h).json()[0]['status']=='cancelled'
def test_slot_conflict_across_sessions(client):
    a=session(client);b=session(client);x=booking_data(client,a);y=booking_data(client,b)
    assert x['start']==y['start']
    assert client.post('/bookings',headers=a,json=x).status_code==200
    assert client.post('/bookings',headers=b,json=y).status_code==409

def test_unmatched_caregiver_cannot_be_booked(client):
    h=session(client);d=booking_data(client,h);d['caregiver_id']='CG_FAKE'
    assert client.post('/bookings',headers=h,json=d).status_code==422

def test_emergency_cannot_book_and_consent_required(client):
    h=session(client);r=request(client,h,'severe chest pain')
    assert r['result']['matched_caregivers']==[]
    assert client.get('/slots',headers=h,params={'request_id':r['request_id'],'caregiver_id':'CG_001','day':datetime.now().date().isoformat()}).status_code==422
    assert client.post('/handovers',headers=h,json={'request_id':r['request_id'],'consent':False}).status_code==422
    x=client.post('/handovers',headers=h,json={'request_id':r['request_id'],'consent':True})
    assert x.status_code==200,x.text
    other=session(client)
    assert client.get('/handovers',headers=other).json()==[]
    assert client.post('/handovers/'+x.json()['id']+'/acknowledge',headers=other,json={}).status_code==404
    assert client.post('/handovers/'+x.json()['id']+'/acknowledge',headers=h,json={}).status_code==200
    assert client.get('/handovers',headers=h).json()[0]['status']=='acknowledged_by_simulator'
def test_clear_only_own_data(client):
    a=session(client);b=session(client);request(client,a);request(client,b)
    assert client.delete('/session/data',headers=a).status_code==200
    assert client.get('/requests',headers=a).json()==[]
    assert len(client.get('/requests',headers=b).json())==1

def test_tinyfish_missing_key_and_allowlist(client,monkeypatch):
    h=session(client);monkeypatch.delenv('TINYFISH_API_KEY',raising=False)
    assert client.post('/hospital-lookups',headers=h,json={'hospital_id':'aiims'}).status_code==503
    assert client.post('/hospital-lookups',headers=h,json={'hospital_id':'http://localhost'}).status_code==422

def test_lookup_status_and_no_patient_payload(client,monkeypatch):
    h=session(client);monkeypatch.setenv('TINYFISH_API_KEY','test-only')
    def fake(job,hospital_id):hospitals.update(job,'partial',{'source_url':'https://www.aiims.edu/','contact':None})
    monkeypatch.setattr(hospitals,'perform',fake)
    x=client.post('/hospital-lookups',headers=h,json={'hospital_id':'aiims'})
    assert x.status_code==202,x.text
    assert client.get('/hospital-lookups/'+x.json()['id'],headers=h).json()['status']=='partial'
    assert client.get('/hospital-lookups/'+x.json()['id'],headers=session(client)).status_code==404
    assert client.post('/hospital-lookups',headers=h,json={'hospital_id':'aiims','patient':'private'}).status_code==422

def test_example_source_is_supplied_dataset(client):
    e=client.get('/examples').json();assert e and all(x['id'].startswith('S') for x in e)

def test_future_window_validation(client):
    h=session(client);d=booking_data(client,h);d['start']='2000-01-01T12:00:00+05:30'
    assert client.post('/bookings',headers=h,json=d).status_code==422

def test_concurrent_slot_reservation_has_one_winner(client):
    from concurrent.futures import ThreadPoolExecutor
    from triagegrid.services.bookings import create
    from fastapi import HTTPException
    a=session(client);b=session(client);x=booking_data(client,a);y=booking_data(client,b)
    def attempt(h,d):
        try:
            create(storage.session_for(h['X-Session-Token']),d['request_id'],d['caregiver_id'],d['start'],d['idempotency_key'])
            return 200
        except HTTPException as e:return e.status_code
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda v:attempt(*v),[(a,x),(b,y)]))
    assert sorted(results)==[200,409]

def test_source_jsonl_and_csv_have_same_cases():
    import csv
    from triagegrid.config import settings
    source=[json.loads(l) for l in (settings.data_dir/'triage_dataset.jsonl').read_text().splitlines() if l.strip()]
    with (settings.data_dir/'triage_dataset_flat.csv').open() as f:flat=list(csv.DictReader(f))
    assert len(source)==len(flat)==340
    lookup={r['id']:r for r in flat}
    assert all(lookup[r['id']]['user_input']==r['request']['user_input'] for r in source)

def test_provided_multiturn_examples(client):
    from triagegrid.config import settings
    examples=[json.loads(l) for l in (settings.data_dir/'multi_turn_examples.jsonl').read_text().splitlines() if l.strip()]
    for example in examples:
        h=session(client);history=[]
        for index,turn in enumerate(example['turns']):
            if turn['role']!='user':continue
            r=client.post('/ui/triage',headers=h,json={'user_input':turn['text'],'conversation_history':history}).json()['result']
            expected=example['turns'][index+1]
            if expected.get('care_type'):assert r['care_type']==expected['care_type']
            else:assert r['follow_up_question'] and r['care_type'] is None
            history.append({'role':'user','text':turn['text']})
            if r['follow_up_question']:history.append({'role':'assistant','text':r['follow_up_question']})


def test_same_day_cannot_be_postponed(client):
    h=session(client);r=request(client,h);cid=r['result']['matched_caregivers'][0]['caregiver_id']
    tomorrow=(datetime.now(ZoneInfo('Asia/Kolkata'))+timedelta(days=1)).date().isoformat()
    assert client.get('/slots',headers=h,params={'request_id':r['request_id'],'caregiver_id':cid,'day':tomorrow}).status_code==422


def test_saved_request_ownership(client):
    a=session(client);b=session(client);r=request(client,a)
    assert client.get('/requests/'+r['request_id'],headers=a).status_code==200
    assert client.get('/requests/'+r['request_id'],headers=b).status_code==404
