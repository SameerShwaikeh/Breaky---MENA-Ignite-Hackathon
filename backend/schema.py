"""Unified clinical record schema. This is the team-wide contract — change only by agreement."""
import hashlib
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

SYNDROMES = ["ILI", "AGE", "ARI", "FEVER_RASH", "HEMORRHAGIC_FEVER", "JAUNDICE", "MENINGITIS_LIKE", "OTHER"]
AGE_BANDS = ["0-4", "5-17", "18-49", "50-64", "65+"]


class ClinicalRecordIn(BaseModel):
    """What a hospital / lab / pharmacy system POSTs to /ingest. No PII allowed."""
    facility_id: str
    facility_city: str
    facility_lat: float
    facility_lon: float
    reporter_msisdn_hash: str          # sha256 of staff phone — never the raw number
    patient_hash: str                  # salted hash — never name / ID number
    age_band: Literal["0-4", "5-17", "18-49", "50-64", "65+"]
    syndrome_code: str
    severity: Literal["mild", "moderate", "severe"]
    observed_at: datetime
    source_system: Literal["ehr", "lab", "pharmacy"]

    def record_id(self) -> str:
        key = f"{self.facility_id}|{self.patient_hash}|{self.observed_at.date()}|{self.syndrome_code}"
        return hashlib.sha256(key.encode()).hexdigest()[:24]


class IngestResult(BaseModel):
    status: Literal["created", "duplicate"]
    record_id: str


class DailyCount(BaseModel):
    day: str
    count: int
