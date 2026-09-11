from datetime import datetime
from pydantic import BaseModel, field_validator
import hashlib

class ClinicalRecordIn(BaseModel):
    facility_id: str
    facility_city: str
    facility_lat: float
    facility_lon: float
    reporter_msisdn_hash: str
    patient_hash: str
    age_band: str
    syndrome_code: str
    severity: str
    observed_at: datetime
    source_system: str

    @field_validator("observed_at", mode="before")
    def parse_observed_at(cls, v):
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return dt.replace(tzinfo=None)
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v

    def record_id(self) -> str:
        raw = f"{self.facility_id}:{self.patient_hash}:{self.observed_at.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

class IngestResult(BaseModel):
    status: str
    record_id: str

class DailyCount(BaseModel):
    date: str
    count: int