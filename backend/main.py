"""BREAKY ingestion API.  Run:  uvicorn backend.main:app --reload"""
import json
from typing import List, Optional
from fastapi import FastAPI, Depends
from sqlmodel import Session, select, func
from backend.db import init_db, get_session, Record, Alert
from backend.schema import ClinicalRecordIn, IngestResult, DailyCount

app = FastAPI(title="BREAKY Ingestion API", version="0.1")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
@app.get("/health")
def health_check():
    return {"status": "ok"}
def _startup():
    init_db()


@app.post("/ingest", response_model=IngestResult)
def ingest(rec: ClinicalRecordIn, s: Session = Depends(get_session)):
    rid = rec.record_id()
    if s.get(Record, rid):
        return IngestResult(status="duplicate", record_id=rid)
    s.add(Record(record_id=rid, **rec.model_dump()))
    s.commit()
    return IngestResult(status="created", record_id=rid)


@app.post("/ingest/batch")
def ingest_batch(recs: List[ClinicalRecordIn], s: Session = Depends(get_session)):
    created = dup = 0
    for rec in recs:
        rid = rec.record_id()
        if s.get(Record, rid):
            dup += 1
            continue
        s.add(Record(record_id=rid, **rec.model_dump()))
        created += 1
    s.commit()
    return {"created": created, "duplicate": dup}


@app.get("/records")
def records(facility_id: Optional[str] = None, city: Optional[str] = None,
            limit: int = 100, s: Session = Depends(get_session)):
    q = select(Record).order_by(Record.observed_at.desc())
    if facility_id:
        q = q.where(Record.facility_id == facility_id)
    if city:
        q = q.where(Record.facility_city == city)
    return s.exec(q.limit(limit)).all()


@app.get("/aggregate", response_model=List[DailyCount])
def aggregate(city: str, syndrome: str, s: Session = Depends(get_session)):
    """Daily counts for one (city, syndrome) — the anomaly model's input."""
    day = func.date(Record.observed_at)
    q = (select(day, func.count()).where(Record.facility_city == city,
                                          Record.syndrome_code == syndrome)
         .group_by(day).order_by(day))
    return [DailyCount(day=d, count=c) for d, c in s.exec(q).all()]


@app.get("/cities")
def cities(s: Session = Depends(get_session)):
    return s.exec(select(Record.facility_city).distinct()).all()


@app.post("/alerts")
def create_alert(city: str, syndrome_code: str, risk_level: str, z_score: float,
                 evidence: dict, s: Session = Depends(get_session)):
    a = Alert(city=city, syndrome_code=syndrome_code, risk_level=risk_level,
              z_score=z_score, evidence=json.dumps(evidence))
    s.add(a); s.commit(); s.refresh(a)
    return a


@app.get("/alerts")
def list_alerts(s: Session = Depends(get_session)):
    return s.exec(select(Alert).order_by(Alert.created_at.desc())).all()
