"""BREAKY Ingestion API. Run: uvicorn backend.main:app --reload"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, SQLModel
from backend.db import init_db, get_session, Record, engine
from backend.schema import ClinicalRecordIn, IngestResult, DailyCount
from agent.detector import detect_anomalies

app = FastAPI(title="BREAKY Ingestion API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/reset")
def reset_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    return {"status": "reset"}

@app.post("/ingest", response_model=IngestResult)
def ingest(rec: ClinicalRecordIn, s: Session = Depends(get_session)):
    rid = rec.record_id()
    if s.get(Record, rid):
        return IngestResult(status="duplicate", record_id=rid)

    db_record = Record(
        id=rid,
        facility_id=rec.facility_id,
        facility_city=rec.facility_city,
        facility_lat=rec.facility_lat,
        facility_lon=rec.facility_lon,
        reporter_msisdn_hash=rec.reporter_msisdn_hash,
        patient_hash=rec.patient_hash,
        age_band=rec.age_band,
        syndrome_code=rec.syndrome_code,
        severity=rec.severity,
        observed_at=rec.observed_at,
        source_system=rec.source_system,
    )
    s.add(db_record)
    s.commit()
    return IngestResult(status="created", record_id=rid)

@app.get("/alerts/latest")
def get_latest_alerts(limit: int = 5):
    alerts = detect_anomalies(days_window=14, threshold_multiplier=1.2)
    if not alerts:
        # Fallback default alert if database is empty/low activity
        return [
            {
                "id": 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "syndrome": "ILI",
                "location": "Ramallah Central Hospital",
                "anomaly_score": 0.89,
                "status": "TRIGGERED",
                "camara_verification": {"sim_swap": "TRUSTED", "location": "VERIFIED"}
            }
        ]
    return alerts[:limit]

@app.get("/aggregate")
def get_aggregate_data(days: int = 14, syndrome: Optional[str] = None):
    with Session(engine) as session:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        query = select(Record).where(Record.observed_at >= cutoff)
        
        if syndrome:
            query = query.where(Record.syndrome_code == syndrome)
            
        records = session.exec(query).all()
        
        counts = {}
        for r in records:
            date_str = r.observed_at.strftime("%Y-%m-%d")
            counts[date_str] = counts.get(date_str, 0) + 1
            
        formatted_data = [
            {"date": date, "count": count} 
            for date, count in sorted(counts.items())
        ]
        return {"total_reports": len(records), "timeline": formatted_data}
    # --- Warehouse & Proactive Response Endpoints ---

@app.get("/warehouses")
def get_warehouse_stock():
    return [
        {"center": "Hebron Medical Center", "item": "Oral Rehydration Salts (ORS)", "stock_level": "CRITICAL", "qty": 120, "days_left": 2},
        {"center": "Hebron Medical Center", "item": "IV Fluids (Normal Saline)", "stock_level": "LOW", "qty": 450, "days_left": 5},
        {"center": "Nablus Medical Center", "item": "Antibiotics (Doxycycline)", "stock_level": "SUFFICIENT", "qty": 2400, "days_left": 30},
        {"center": "Ramallah Central Hospital", "item": "Personal Protective Equipment", "stock_level": "SUFFICIENT", "qty": 5000, "days_left": 45},
    ]

@app.get("/proactive-plan")
def get_proactive_plan(location: str = "Hebron Medical Center", syndrome: str = "AFI"):
    return {
        "location": location,
        "syndrome": syndrome,
        "status": "ACTION_REQUIRED",
        "steps": [
            {"priority": "P1", "action": "Mobilize emergency ORS supply chain to Hebron central warehouse."},
            {"priority": "P1", "action": "Issue alert to local health clinics for early case reporting."},
            {"priority": "P2", "action": "Deploy rapid testing kits to primary triage centers."},
            {"priority": "P3", "action": "Coordinate with municipal water authority for contamination testing."}
        ]
    }
# --- Breaky Pandemic & Inventory Endpoints ---

@app.get("/outbreak-data")
def get_outbreak_data():
    return [
        {
            "id": 1,
            "location": "Gaza",
            "lat": 31.5017,
            "lon": 34.4668,
            "agent": "Influenza-A",
            "risk_level": "PANDEMIC THREAT",
            "protocol": "Activate Quarantine Protocol: Gaza",
            "stock_status": "CRITICAL",
            "needed_supplies": "Tamiflu, N95 Masks, Oxygen Cylinders",
            "cases": 142
        },
        {
            "id": 2,
            "location": "Hebron",
            "lat": 31.5326,
            "lon": 35.0998,
            "agent": "Hepatitis",
            "risk_level": "PANDEMIC THREAT",
            "protocol": "Activate Quarantine Protocol: Hebron",
            "stock_status": "LOW STOCK",
            "needed_supplies": "Oral Rehydration Salts (ORS), Clean Water Filters, IV Fluids",
            "cases": 98
        },
        {
            "id": 3,
            "location": "Nablus",
            "lat": 32.2211,
            "lon": 35.2544,
            "agent": "Meningitis",
            "risk_level": "PANDEMIC THREAT",
            "protocol": "Activate Quarantine Protocol: Nablus",
            "stock_status": "WARNING",
            "needed_supplies": "Ceftriaxone, Antibiotics, Lumbar Kits",
            "cases": 64
        },
        {
            "id": 4,
            "location": "Bethlehem",
            "lat": 31.7057,
            "lon": 35.2024,
            "agent": "Covid-19",
            "risk_level": "PANDEMIC THREAT",
            "protocol": "Activate Quarantine Protocol: Bethlehem",
            "stock_status": "ADEQUATE",
            "needed_supplies": "Rapid Antigen Kits, Surgical Masks",
            "cases": 41
        },
        {
            "id": 5,
            "location": "Ramallah",
            "lat": 31.9038,
            "lon": 35.2034,
            "agent": "ILI (Flu-like)",
            "risk_level": "EVALUATE",
            "protocol": "Monitor Fever Clusters",
            "stock_status": "ADEQUATE",
            "needed_supplies": "Paracetamol, Diagnostic Swabs",
            "cases": 15
        }
    ]

@app.get("/warehouses")
def get_warehouse_inventory():
    return [
        {"warehouse": "Gaza Central Medical Depot", "city": "Gaza", "item": "Tamiflu (Oseltamivir)", "available": 85, "required": 500, "status": "CRITICAL SHORTAGE"},
        {"warehouse": "Hebron Regional Warehouse", "city": "Hebron", "item": "Oral Rehydration Salts (ORS)", "available": 120, "required": 1000, "status": "LOW STOCK"},
        {"warehouse": "Hebron Regional Warehouse", "city": "Hebron", "item": "Normal Saline IV (1L)", "available": 450, "required": 1200, "status": "LOW STOCK"},
        {"warehouse": "Nablus Northern Depot", "city": "Nablus", "item": "Ceftriaxone Injectable", "available": 310, "required": 800, "status": "LOW STOCK"},
        {"warehouse": "Ramallah Central Hospital Depot", "city": "Ramallah", "item": "Personal Protective Equipment", "available": 4500, "required": 5000, "status": "SUFFICIENT"},
        {"warehouse": "Bethlehem Health Center", "city": "Bethlehem", "item": "Rapid COVID-19 Antigen Test", "available": 890, "required": 1000, "status": "SUFFICIENT"}
    ]