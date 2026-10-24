import pytest
from triagegrid.schemas import TriageRequest
from triagegrid.services.engine import predict,rank,roster,BREATH
from triagegrid.services.safety import scan
@pytest.mark.parametrize('text,flag',[
 ('seene me dard hai','chest_pain'),('chest pain','chest_pain'),
 ('saans nahi aa rahi','breathlessness'),('सांस लेने में दिक्कत है','breathlessness'),
 ('bleeding will not stop','severe_bleeding'),('accident ke baad bleeding ruk nahi rahi','severe_bleeding'),
 ('unconscious','unconsciousness'),('behosh','unconsciousness'),('seizure','seizure'),('face droop','stroke_symptoms')])
def test_reported_flags_bypass_matching(text,flag):
    r=predict(TriageRequest(user_input=text));assert flag in r.red_flags
    assert r.care_type=='emergency_112' and r.urgency=='emergency' and not r.matched_caregivers
@pytest.mark.parametrize('text',['no chest pain','seene me dard nahi hai','breathing difficulty nahi hai','no severe bleeding','छाती में दर्द नहीं है'])
def test_negated_flags_not_reported(text):assert scan(text)[0]==[]
def test_negative_does_not_cancel_other_clause():
    assert scan('no chest pain but cannot breathe')[0]==['breathlessness']
def test_unknown_is_not_negative():assert 'breathlessness' in scan('breathing difficulty pata nahi')[1]
def test_bare_answer_to_breathing_question():
    h=[{'role':'user','text':'fever and cough'},{'role':'assistant','text':BREATH['Hinglish']}]
    assert predict(TriageRequest(user_input='haan',conversation_history=h)).red_flags==['breathlessness']
def test_history_red_flag_not_silently_erased():
    r=predict(TriageRequest(user_input='no chest pain now',conversation_history=[{'role':'user','text':'severe chest pain'}]))
    assert r.care_type=='emergency_112'
def test_followup_resolution():
    h=[{'role':'user','text':'doctor chahiye'},{'role':'assistant','text':'Main symptom ya service bataiye: home assessment, nursing, lab collection ya doctor se baat?'}]
    assert predict(TriageRequest(user_input='Need blood sugar test at home tomorrow morning',conversation_history=h)).care_type=='lab_test_home'
def test_teleconsult_ignores_location():
    from triagegrid.schemas import Location
    a=rank('teleconsultation','doctor call','English',None)
    b=rank('teleconsultation','doctor call','English',Location(lat=0,lng=0))
    assert a==b and a and all('distance' not in m.reason for m in a)
def test_physical_matching_requires_location():assert rank('lab_test_home','blood test','English',None)==[]
def test_no_assumed_injection_route():
    from triagegrid.schemas import Location
    assert rank('home_nursing','injection at home','English',Location(lat=28.54,lng=77.27))==[]
def test_matches_known_and_sorted():
    from triagegrid.schemas import Location
    m=rank('home_nursing','wound dressing','English',Location(lat=28.5921,lng=77.046))
    assert m and all(x.caregiver_id in {c['caregiver_id'] for c in roster()} for x in m)
    assert [x.score for x in m]==sorted([x.score for x in m],reverse=True)
