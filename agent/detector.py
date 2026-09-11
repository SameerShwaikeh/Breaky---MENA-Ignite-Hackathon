from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from backend.db import engine, Record
from camara.location import verify_location
from camara.sim_swap import check_sim_swap

def detect_anomalies(days_window: int = 14, threshold_multiplier: float = 1.5):
    """
    Scans recent records, groups by city and syndrome, and generates alerts
    if report density exceeds average baseline volume.
    """
    alerts = []
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_window)

    with Session(engine) as session:
        records = session.exec(select(Record).where(Record.observed_at >= cutoff)).all()

    if not records:
        return alerts

    # Group counts by (city, syndrome)
    counts = {}
    latest_records = {}
    
    for r in records:
        key = (r.facility_city, r.syndrome_code)
        counts[key] = counts.get(key, 0) + 1
        latest_records[key] = r

    avg_baseline = max(1, len(records) / max(1, len(counts)))

    alert_id = 1
    for (city, syndrome), count in counts.items():
        if count > avg_baseline * threshold_multiplier:
            sample_rec = latest_records[(city, syndrome)]
            
            # Enrich alert using CAMARA verification functions
            loc_status = verify_location(city, sample_rec.facility_lat, sample_rec.facility_lon)
            sim_status = check_sim_swap(sample_rec.reporter_msisdn_hash)

            anomaly_score = min(0.99, round(count / (avg_baseline * 2), 2))

            alerts.append({
                "id": alert_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "syndrome": syndrome,
                "location": f"{city} Medical Center",
                "anomaly_score": anomaly_score,
                "status": "TRIGGERED",
                "camara_verification": {
                    "sim_swap": sim_status,
                    "location": loc_status
                }
            })
            alert_id += 1

    return alerts
