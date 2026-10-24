import csv,json,re
from functools import lru_cache
from pathlib import Path
import joblib
import numpy as np
from ..config import settings
from ..schemas import TriageRequest,TriageResponse,Match
from .safety import scan
LABELS={"paramedic_home_visit","home_nursing","lab_test_home","teleconsultation","emergency_112"}
QUESTION={"English":"What is the main symptom or service you need: home assessment, nursing, lab collection or a doctor call?","Hindi":"मुख्य परेशानी या सेवा बताइए: घर पर जांच, नर्सिंग, लैब सैंपल या डॉक्टर से बात?","Hinglish":"Main symptom ya service bataiye: home assessment, nursing, lab collection ya doctor se baat?"}
BREATH={"English":"Is there difficulty breathing?","Hindi":"क्या सांस लेने में दिक्कत है?","Hinglish":"Kya saans lene mein dikkat hai?"}
@lru_cache
def models():
    # Artifacts rebuilt locally by scripts/train_models.py; never accept uploaded pickle files.
    meta=json.loads((settings.model_dir/'model_meta.json').read_text())
    import sklearn
    if meta['sklearn_version']!=sklearn.__version__:raise RuntimeError('Run the explicit training script for this sklearn version')
    return joblib.load(settings.model_dir/'care_type_pipeline.pkl'),joblib.load(settings.model_dir/'urgency_pipeline.pkl'),meta
@lru_cache
def roster():
    with (settings.data_dir/'caregivers.csv').open() as f:return list(csv.DictReader(f))
def lang(req):
    if req.language!='auto':return req.language
    if re.search(r'[\u0900-\u097f]',req.user_input):return 'Hindi'
    return 'Hinglish' if re.search(r'\b(hai|ko|ghar|chahiye|mummy|papa|nahi)\b',req.user_input,re.I) else 'English'
def clarification(q,reason):return TriageResponse(follow_up_question=q,care_type=None,urgency=None,red_flags=[],reasoning=reason,matched_caregivers=[])
def emergency(flags):return TriageResponse(follow_up_question=None,care_type='emergency_112',urgency='emergency',red_flags=flags,reasoning='Reported warning signs require the emergency-help path; do not wait for a caregiver booking.',matched_caregivers=[])
def distance(a,b,c,d):
    a,b,c,d=np.radians([a,b,c,d]);v=np.sin((c-a)/2)**2+np.cos(a)*np.cos(c)*np.sin((d-b)/2)**2
    return float(6371.0088*2*np.arcsin(np.sqrt(np.clip(v,0,1))))
def rank(ct,text,language,location):
    role={'teleconsultation':'doctor','lab_test_home':'phlebotomist','home_nursing':'medic','paramedic_home_visit':'medic'}[ct]
    required=[]
    if ct=='teleconsultation':required=['teleconsultation']
    elif ct=='lab_test_home':required=['sample_collection']
    elif ct=='paramedic_home_visit':required=['vitals_monitoring']
    else:
        if re.search(r'\biv\b|drip|ड्रिप',text,re.I):required.append('injection_iv')
        elif re.search(r'inject|इंजेक्शन',text,re.I):
            # An unspecified injection route must not silently become intramuscular.
            if re.search(r'\bim\b|intramuscular',text,re.I):required.append('injection_im')
            else:return []
        for pattern,skill in [(r'dressing|wound|पट्टी|घाव','wound_dressing'),(r'catheter|कैथेटर','catheter_care'),(r'nebul|नेबुल','nebulization')]:
            if re.search(pattern,text,re.I):required.append(skill)
    if ct!='teleconsultation' and location is None:return []
    candidates=[]
    for c in roster():
        skills=c['skills'].split(';');languages=c['languages'].split(';')
        if c['active'].lower()!='true' or c['role']!=role or not all(s in skills for s in required):continue
        # Roster windows are supplied synthetic windows, not assertions of current availability.
        start,end=c['free_from'],c['free_until']
        if start>=end:continue
        d=None if ct=='teleconsultation' else distance(location.lat,location.lng,float(c['base_lat']),float(c['base_lng']))
        if d is not None and d>float(c['max_radius_km']):continue
        lm=1 if ('Hindi' if language=='Hinglish' else language) in languages else 0
        vals=[(.35,lm),(.20,1 if required else 0),(.15,float(c['rating'])/5)]
        if d is not None:vals.append((.30,max(0,1-d/float(c['max_radius_km']))))
        score=sum(w*v for w,v in vals)/sum(w for w,v in vals)
        reason=f"{c['role']}; languages: {', '.join(languages)}; roster window {start}-{end} IST; rating {c['rating']}"
        if d is not None:reason+=f'; {d:.1f} km straight-line distance'
        if not lm:reason+='; preferred language unavailable'
        candidates.append(Match(caregiver_id=c['caregiver_id'],score=round(score,3),reason=reason))
    return sorted(candidates,key=lambda c:(-c.score,c.caregiver_id))[:3]
def predict(req:TriageRequest):
    language=lang(req);current=req.user_input.strip()
    if not current:return clarification(QUESTION[language],'Please describe the fictional care need.')
    user_texts=[h.text for h in req.conversation_history if h.role=='user']+[current]
    flags=[];uncertain=[];clean=[]
    for text in user_texts:
        f,u,c=scan(text);flags+=f;uncertain+=u;clean.append(c)
    # Preserve previously reported flags on contradiction rather than silently downgrading.
    if flags:return emergency(sorted(set(flags)))
    last=next((h.text for h in reversed(req.conversation_history) if h.role=='assistant'),None)
    short=current.lower().strip(' .!?')
    is_breath=last in BREATH.values()
    if is_breath and short in {'yes','haan','ha','हाँ','हां'}:return emergency(['breathlessness'])
    if is_breath and short in {'pata nahi','don’t know',"don't know",'unknown','पता नहीं'}:
        return clarification('Please describe what the person is experiencing, or request a doctor consultation.','Breathing status remains unknown; no negative answer was assumed.')
    if is_breath and short in {'no','nahi','nahin','नहीं','नही'}:clean=clean[:-1]
    elif short in {'yes','no','haan','nahi','pata nahi','हाँ','नहीं'}:
        return clarification(QUESTION[language],'A short answer needs a matching question and symptom context.')
    if uncertain and not is_breath:return clarification(BREATH[language],'A reported safety concern is uncertain; clarification is needed.')
    text=' '.join(clean).strip()
    care,urg,meta=models()
    cp=care.predict_proba([text])[0];ct=str(care.classes_[cp.argmax()])
    if ct=='emergency_112':return emergency([])
    if ct not in LABELS or cp.max()<meta.get('conf_threshold',.45):return clarification(QUESTION[language],'The care need is not clear enough to select a service.')
    up=urg.predict_proba([text])[0];ut=str(urg.classes_[up.argmax()])
    if ut=='emergency':return emergency([])
    if ut not in {'same_day','scheduled'}:return clarification(QUESTION[language],'More information is needed to determine urgency.')
    matches=rank(ct,text,language,req.location)
    label={'home_nursing':'home nursing','paramedic_home_visit':'home assessment','lab_test_home':'home sample collection','teleconsultation':'a virtual doctor consultation'}[ct]
    reason=f'The reported request was routed to {label}; timing category: {ut.replace("_"," ")}. No diagnosis was generated.'
    if not matches:reason+=' No eligible roster match was found for the supplied requirements/location.'
    return TriageResponse(follow_up_question=None,care_type=ct,urgency=ut,red_flags=[],reasoning=reason,matched_caregivers=matches)
