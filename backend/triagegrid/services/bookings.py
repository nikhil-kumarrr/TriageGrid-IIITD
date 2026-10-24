import json
from datetime import datetime,timedelta,date
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from ..storage import connect,now,uid
from .engine import roster
IST=ZoneInfo('Asia/Kolkata')
DURATION=30 # Configured synthetic scheduling convention; source only supplies daily windows.
def source_request(sid,rid):
    with connect() as db:row=db.execute('SELECT * FROM requests WHERE id=? AND session_id=?',(rid,sid)).fetchone()
    if not row:raise HTTPException(404,'Request not found')
    return dict(row)
def eligible(sid,rid,cid):
    req=source_request(sid,rid);r=json.loads(req['response'])
    if r['care_type']=='emergency_112' or not any(m['caregiver_id']==cid for m in r['matched_caregivers']):raise HTTPException(422,'Caregiver is not eligible for this request')
    c=next((c for c in roster() if c['caregiver_id']==cid and c['active'].lower()=='true'),None)
    if not c:raise HTTPException(422,'Caregiver unavailable')
    return req,c
def candidate_slots(c,day):
    today=datetime.now(IST).date()
    if day<today or day>today+timedelta(days=6):raise HTTPException(422,'Choose a day within the next seven days')
    start=datetime.fromisoformat(day.isoformat()+'T'+c['free_from']).replace(tzinfo=IST)
    end=datetime.fromisoformat(day.isoformat()+'T'+c['free_until']).replace(tzinfo=IST)
    slots=[]
    while start+timedelta(minutes=DURATION)<=end:
        finish=start+timedelta(minutes=DURATION)
        if start>datetime.now(IST):slots.append((start.isoformat(),finish.isoformat()))
        start=finish
    return slots
def slots(sid,rid,cid,day):
    req,c=eligible(sid,rid,cid)
    if json.loads(req['response'])['urgency']=='same_day' and day!=datetime.now(IST).date():raise HTTPException(422,'Same-day care cannot be postponed to another date')
    values=candidate_slots(c,day)
    with connect() as db:reserved=db.execute("SELECT start,end FROM bookings WHERE caregiver_id=? AND status='confirmed'",(cid,)).fetchall()
    return [{'start':s,'end':e,'available':not any(r['start']<e and r['end']>s for r in reserved)} for s,e in values]
def create(sid,rid,cid,start,idempotency):
    req,c=eligible(sid,rid,cid)
    try:dt=datetime.fromisoformat(start)
    except ValueError:raise HTTPException(422,'Invalid slot')
    if dt.tzinfo is None:raise HTTPException(422,'Slot must include timezone')
    if json.loads(req['response'])['urgency']=='same_day' and dt.astimezone(IST).date()!=datetime.now(IST).date():raise HTTPException(422,'Same-day care cannot be postponed to another date')
    canonical=dt.astimezone(IST).isoformat()
    match=next(((s,e) for s,e in candidate_slots(c,dt.astimezone(IST).date()) if s==canonical),None)
    if not match:raise HTTPException(422,'Select a valid future roster slot')
    s,e=match;db=connect()
    try:
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT * FROM bookings WHERE session_id=? AND idempotency=?',(sid,idempotency)).fetchone()
        if old:
            if old['request_id']!=rid or old['caregiver_id']!=cid or old['start']!=s:raise HTTPException(409,'Idempotency key reused for another booking')
            db.commit();return dict(old)
        if db.execute("SELECT 1 FROM bookings WHERE caregiver_id=? AND status='confirmed' AND start<? AND end>?",(cid,e,s)).fetchone():raise HTTPException(409,'Slot was reserved. Select another slot.')
        bid=uid('B');db.execute('INSERT INTO bookings VALUES (?,?,?,?,?,?,?,?,?)',(bid,sid,rid,cid,s,e,'confirmed',idempotency,now()))
        row=db.execute('SELECT * FROM bookings WHERE id=?',(bid,)).fetchone();db.commit();return dict(row)
    except:db.rollback();raise
    finally:db.close()
def all_bookings(sid):
    with connect() as db:rows=db.execute('SELECT * FROM bookings WHERE session_id=? ORDER BY created DESC',(sid,)).fetchall()
    return [public(dict(r)) for r in rows]
def public(b):
    c=next((x for x in roster() if x['caregiver_id']==b['caregiver_id']),{})
    return {k:b[k] for k in ['id','request_id','caregiver_id','start','end','status','created']}|{'caregiver_name':c.get('name',''),'role':c.get('role',''),'simulation':True}
def cancel(sid,bid):
    with connect() as db:
        row=db.execute('SELECT * FROM bookings WHERE id=? AND session_id=?',(bid,sid)).fetchone()
        if not row:raise HTTPException(404,'Booking not found')
        db.execute("UPDATE bookings SET status='cancelled' WHERE id=?",(bid,))
    return {'id':bid,'status':'cancelled'}
