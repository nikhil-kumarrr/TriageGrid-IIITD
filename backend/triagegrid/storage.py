import sqlite3,secrets,hashlib,json
from datetime import datetime,timezone
from .config import settings

def now():return datetime.now(timezone.utc).isoformat()
def uid(prefix):return prefix+'_'+secrets.token_hex(8)
def digest(token):return hashlib.sha256(token.encode()).hexdigest()
def connect():
    settings.database_path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(settings.database_path,timeout=10,isolation_level=None)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=10000')
    return db
def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,token_hash TEXT UNIQUE,created TEXT);
        CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,session_id TEXT REFERENCES sessions(id),payload TEXT,response TEXT,created TEXT);
        CREATE TABLE IF NOT EXISTS bookings(id TEXT PRIMARY KEY,session_id TEXT REFERENCES sessions(id),request_id TEXT REFERENCES requests(id),caregiver_id TEXT,start TEXT,end TEXT,status TEXT,idempotency TEXT,created TEXT,UNIQUE(session_id,idempotency));
        CREATE INDEX IF NOT EXISTS booking_overlap ON bookings(caregiver_id,start,end,status);
        CREATE TABLE IF NOT EXISTS handovers(id TEXT PRIMARY KEY,session_id TEXT REFERENCES sessions(id),request_id TEXT REFERENCES requests(id),summary TEXT,status TEXT,created TEXT);
        CREATE TABLE IF NOT EXISTS lookups(id TEXT PRIMARY KEY,session_id TEXT REFERENCES sessions(id),hospital_id TEXT,status TEXT,result TEXT,created TEXT);
        ''')
def new_session():
    token=secrets.token_urlsafe(32);sid=uid('S')
    with connect() as db:db.execute('INSERT INTO sessions VALUES (?,?,?)',(sid,digest(token),now()))
    return token
def session_for(token):
    if not token:return None
    with connect() as db:
        row=db.execute('SELECT id FROM sessions WHERE token_hash=?',(digest(token),)).fetchone()
    return row['id'] if row else None
