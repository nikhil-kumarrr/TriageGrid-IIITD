"""Optional REST layer over the same package (the Streamlit app calls the package directly).

    PYTHONPATH=src uvicorn api.main:app --reload
"""
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from triage_matching import config, matcher, triage
from triage_matching.model import load_models

STATE: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    STATE["cg"] = matcher.load_caregivers(config.CAREGIVERS_CSV)
    yield
    STATE.clear()


app = FastAPI(title="Triage + Caregiver Matching API", version="1.0.0", lifespan=lifespan)


class Req(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    request_time: Optional[str] = Field(None, pattern=r"^\d{1,2}:\d{2}$")
    preferred_gender: Optional[Literal["M", "F"]] = None
    top_k: int = Field(3, ge=1, le=10)


@app.get("/health")
def health():
    return {"status": "ok", "caregivers": len(STATE.get("cg", []))}


@app.post("/triage")
def triage_ep(req: Req):
    return triage.triage(req.text)


@app.post("/triage-and-match")
def triage_and_match(req: Req):
    t = triage.triage(req.text)
    ct = t["care_type"]
    if ct == config.EMERGENCY:
        return {"action": "call_112", "triage": t, "matching": None}
    if ct == config.NEEDS_CLARIFICATION:
        return {"action": "ask_follow_up", "triage": t, "matching": None}
    try:
        m = matcher.match_caregivers(STATE["cg"], ct, req.text, req.lat, req.lng, t["detected_language"],
                                     req.request_time, req.preferred_gender, req.top_k)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"action": "matched" if m["candidates"] else "no_caregiver_available", "triage": t, "matching": m}
