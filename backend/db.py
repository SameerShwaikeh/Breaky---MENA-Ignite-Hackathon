from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine, Session

class Record(SQLModel, table=True):
    id: str = Field(primary_key=True)
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

sqlite_file_name = "breaky.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session