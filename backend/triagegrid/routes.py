import json,secrets
from datetime import date
from typing import Annotated
from fastapi import APIRouter,Header,HTTPException,Depends,BackgroundTasks
from pydantic import Field
from .schemas import StrictModel,TriageRequest,AssistantChatRequest,AssistantFactsCorrectionRequest
from .storage import connect,new_session,session_for,uid,now
from .services.engine import predict,roster
from .services import bookings,hospitals
from .services.assistant import get_assistant_status,handle_chat_message
from .services.memory import get_memory_provider,StructuredFacts
router=APIRouter()
def owner(x_session_token:Annotated[str|None,Header()]=None):
    sid=session_for(x_session_token)
    if not sid:raise HTTPException(401,'Session expired. Refresh to start a new local session.')
    return sid
@router.post('/session')
def session():return {'token':new_session()}
@router.post('/ui/triage')
def evaluate(req:TriageRequest,sid=Depends(owner)):
    result=predict(req);rid=uid('R')
    with connect() as db:db.execute('INSERT INTO requests VALUES (?,?,?,?,?)',(rid,sid,req.model_dump_json(),result.model_dump_json(),now()))
    return {'request_id':rid,'result':result}
@router.get('/requests')
def requests(sid=Depends(owner)):
    with connect() as db:rows=db.execute('SELECT id,response,created FROM requests WHERE session_id=? ORDER BY created DESC LIMIT 20',(sid,)).fetchall()
    return [{'id':r['id'],'created':r['created'],'result':json.loads(r['response'])} for r in rows]
@router.get('/slots')
def slots(request_id:str,caregiver_id:str,day:date,sid=Depends(owner)):
    return {'slots':bookings.slots(sid,request_id,caregiver_id,day),'duration_minutes':30,'schedule_basis':'Configured 30-minute appointments; provided undated synthetic roster windows repeat over the next seven days. Not real provider availability.'}
class BookingInput(StrictModel):
    request_id:str=Field(max_length=64)
    caregiver_id:str=Field(max_length=32)
    start:str=Field(max_length=40)
    idempotency_key:str=Field(min_length=8,max_length=100)
@router.post('/bookings')
def book(req:BookingInput,sid=Depends(owner)):return bookings.public(bookings.create(sid,req.request_id,req.caregiver_id,req.start,req.idempotency_key))
@router.get('/bookings')
def list_bookings(sid=Depends(owner)):return bookings.all_bookings(sid)
@router.post('/bookings/{bid}/cancel')
def cancel(bid:str,sid=Depends(owner)):return bookings.cancel(sid,bid)
class HandoverInput(StrictModel):
    request_id:str=Field(max_length=64)
    consent:bool
@router.post('/handovers')
def handover(req:HandoverInput,sid=Depends(owner)):
    if not req.consent:raise HTTPException(422,'Explicit consent is required')
    row=bookings.source_request(sid,req.request_id);r=json.loads(row['response']);q=json.loads(row['payload'])
    if r['care_type']!='emergency_112':raise HTTPException(422,'Handover is only for an emergency request')
    summary={'reported_concern':[h['text'] for h in q['conversation_history'] if h['role']=='user']+[q['user_input']],'reported_flags':r['red_flags'],'language':q['language'],'location':q['location'],'duration':'Not separately provided','simulation':True}
    hid=uid('H')
    with connect() as db:db.execute('INSERT INTO handovers VALUES (?,?,?,?,?,?)',(hid,sid,req.request_id,json.dumps(summary),'received',now()))
    return {'id':hid,'summary':summary,'status':'received','simulation':True}
@router.get('/handovers')
def handovers(sid=Depends(owner)):
    with connect() as db:rows=db.execute('SELECT * FROM handovers WHERE session_id=? ORDER BY created DESC',(sid,)).fetchall()
    return [{'id':r['id'],'summary':json.loads(r['summary']),'status':r['status'],'created':r['created']} for r in rows]
@router.post('/handovers/{hid}/acknowledge')
def ack(hid:str,sid=Depends(owner)):
    with connect() as db:
        if not db.execute('SELECT 1 FROM handovers WHERE id=? AND session_id=?',(hid,sid)).fetchone():raise HTTPException(404,'Handover not found')
        db.execute("UPDATE handovers SET status='acknowledged_by_simulator' WHERE id=?",(hid,))
    return {'id':hid,'status':'acknowledged_by_simulator'}
@router.get('/hospitals')
def hospital_list():return {'hospitals':hospitals.HOSPITALS,'configured':hospitals.configured()}
class LookupInput(StrictModel):
    hospital_id:str=Field(max_length=40)
    force_refresh:bool=False
@router.post('/hospital-lookups',status_code=202)
def lookup(req:LookupInput,background:BackgroundTasks,sid=Depends(owner)):
    if not any(h['id']==req.hospital_id for h in hospitals.HOSPITALS):raise HTTPException(422,'Hospital not allowlisted')
    if not hospitals.configured():raise HTTPException(503,'Hospital lookup is not configured on the server')
    with connect() as db:
        if not req.force_refresh:
            cached=db.execute("SELECT result FROM lookups WHERE hospital_id=? AND status IN ('found','partial') ORDER BY created DESC LIMIT 1",(req.hospital_id,)).fetchone()
            if cached:
                from datetime import datetime, timezone, timedelta
                data=json.loads(cached['result'])
                if data.get('checked_at') and datetime.now(timezone.utc)-datetime.fromisoformat(data['checked_at'])<timedelta(hours=6):
                    job=uid('L')
                    db.execute('INSERT INTO lookups VALUES (?,?,?,?,?,?)',(job,sid,req.hospital_id,'cached',json.dumps(data),now()))
                    return {'id':job,'status':'cached','result':data}
        if db.execute("SELECT 1 FROM lookups WHERE session_id=? AND status IN ('queued','checking')",(sid,)).fetchone():raise HTTPException(409,'A lookup is already running')
        job=uid('L');db.execute('INSERT INTO lookups VALUES (?,?,?,?,?,?)',(job,sid,req.hospital_id,'queued','{}',now()))
    background.add_task(hospitals.perform,job,req.hospital_id)
    return {'id':job,'status':'queued'}
@router.get('/hospital-lookups/{job}')
def lookup_status(job:str,sid=Depends(owner)):
    with connect() as db:r=db.execute('SELECT * FROM lookups WHERE id=? AND session_id=?',(job,sid)).fetchone()
    if not r:raise HTTPException(404,'Lookup not found')
    return {'id':r['id'],'status':r['status'],'result':json.loads(r['result'])}
@router.get('/mentor/metrics')
def metrics(sid=Depends(owner)):
    from .services.engine import models
    meta=models()[2]
    return {k:v for k,v in meta.items() if k not in {'training_sha256'}}
@router.delete('/session/data')
def clear(sid=Depends(owner)):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        for table in ['assistant_messages','assistant_facts','lookups','handovers','bookings','requests']:
            db.execute(f'DELETE FROM {table} WHERE session_id=?',(sid,))
        db.commit()
    return {'cleared':True}
@router.get('/examples')
def examples():
    import csv
    from .config import settings
    values=[];seen=set()
    with (settings.data_dir/'triage_dataset_flat.csv').open() as f:
        for row in csv.DictReader(f):
            key=(row['care_type'] or 'clarification',row['detected_language'])
            if key in seen:continue
            seen.add(key);values.append({'id':row['id'],'text':row['user_input'],'language':row['detected_language'],'care_type':row['care_type'] or None,'location':{'lat':float(row['lat']),'lng':float(row['lng'])}})
    return values
@router.get('/requests/{rid}')
def request_detail(rid:str,sid=Depends(owner)):
    r=bookings.source_request(sid,rid)
    return {'id':r['id'],'request':json.loads(r['payload']),'result':json.loads(r['response']),'created':r['created']}

@router.get('/assistant/status')
def assistant_status():
    return get_assistant_status()

@router.get('/assistant/conversation')
def assistant_conversation(sid=Depends(owner)):
    mem=get_memory_provider()
    history=mem.get_history(sid)
    facts=mem.get_facts(sid)
    latest_rec=None
    with connect() as db:
        row=db.execute("SELECT id,response FROM requests WHERE session_id=? ORDER BY created DESC LIMIT 1",(sid,)).fetchone()
        if row:
            latest_rec={**json.loads(row['response']),"request_id":row['id']}
    return {
        "messages":[m.to_dict() for m in history],
        "structured_facts":facts.to_dict(),
        "care_recommendation":latest_rec,
    }

@router.post('/assistant/chat')
def assistant_chat(req:AssistantChatRequest,sid=Depends(owner)):
    return handle_chat_message(
        session_id=sid,
        user_text=req.message,
        language=req.language,
        location=req.location,
        image_base64=req.image_base64,
        image_mime_type=req.image_mime_type,
    )

@router.post('/assistant/facts/correct')
def assistant_facts_correct(req:AssistantFactsCorrectionRequest,sid=Depends(owner)):
    mem=get_memory_provider()
    facts=StructuredFacts.from_dict(req.facts)
    mem.update_facts(sid,facts)
    return {"updated":True,"structured_facts":facts.to_dict()}

@router.delete('/assistant/conversation')
def assistant_clear(sid=Depends(owner)):
    mem=get_memory_provider()
    mem.clear(sid)
    return {"cleared":True}

