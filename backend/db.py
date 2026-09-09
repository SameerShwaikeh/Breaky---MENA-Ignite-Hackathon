from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session

DB_URL = "sqlite:///breaky.db"
engine = create_engine(DB_URL, echo=False)


class Record(SQLModel, table=True):
    record_id: str = Field(primary_key=True)
    facility_id: str = Field(index=True)
    facility_city: str = Field(index=True)
    facility_lat: float
    facility_lon: float
    reporter_msisdn_hash: str
    patient_hash: str
    age_band: str
    syndrome_code: str = Field(index=True)
    severity: str
    observed_at: datetime = Field(index=True)
    source_system: str
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    city: str
    syndrome_code: str
    risk_level: str
    z_score: float
    evidence: str            # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as s:
        yield s
