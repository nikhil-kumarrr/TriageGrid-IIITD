import os,time
from collections import defaultdict,deque
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from .services.engine import predict, models, roster
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .schemas import TriageRequest, TriageResponse
from .storage import initialize
from .routes import router
load_dotenv(settings.data_dir.parents[1] / ".env", override=False)
@asynccontextmanager
async def lifespan(app):
    initialize()
    from .storage import connect
    with connect() as db:
        db.execute("UPDATE lookups SET status='unavailable',result=? WHERE status IN ('queued','checking')", ('{"message":"Lookup interrupted by server restart. Please retry."}',))
    models()
    roster()
    yield

app = FastAPI(title="TriageGrid", version="0.2.0", lifespan=lifespan)
RATE_BUCKETS=defaultdict(deque)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type", "X-Session-Token"])
@app.middleware("http")
async def security_headers(request, call_next):
    if request.method != 'OPTIONS' and request.url.path != '/health':
        bucket=(request.client.host if request.client else 'local', 'lookup' if request.url.path=='/hospital-lookups' and request.method=='POST' else 'general')
        timestamp=time.monotonic()
        times=RATE_BUCKETS[bucket]
        while times and times[0]<timestamp-60:times.popleft()
        if len(times)>=(10 if bucket[1]=='lookup' else 300):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=429,content={'detail':'Too many requests. Please wait and retry.'},headers={'Retry-After':'60'})
        times.append(timestamp)
        if len(RATE_BUCKETS)>2048:
            for key in list(RATE_BUCKETS):
                if not RATE_BUCKETS[key] or RATE_BUCKETS[key][-1]<timestamp-60:RATE_BUCKETS.pop(key,None)
    if request.headers.get('content-length','0').isdigit() and int(request.headers.get('content-length','0'))>100_000:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=413,content={'detail':'Request too large'})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response
@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0", "prediction_ready": all((settings.model_dir / name).exists() for name in ["care_type_pipeline.pkl", "urgency_pipeline.pkl"]), "tinyfish": "configured" if os.getenv("TINYFISH_API_KEY") else "not_configured"}
@app.post("/triage", response_model=TriageResponse)
def triage(request: TriageRequest):
    try:
        return predict(request)
    except (FileNotFoundError, RuntimeError):
        raise HTTPException(status_code=503, detail="Model artifacts are unavailable. Run the training script.")

@app.get("/caregivers")
def caregivers():
    return [{k:v for k,v in c.items() if k not in {"gender"}} for c in roster()]

app.include_router(router)
