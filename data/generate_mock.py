"""Generate 30 days of synthetic syndromic surveillance data with one injected outbreak.
Run:  python data/generate_mock.py   ->  data/mock_records.csv
Tweak OUTBREAK to change the demo story."""
import csv, hashlib, random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent / "mock_records.csv"
DAYS = 30
END = datetime(2026, 9, 9)

FACILITIES = [
    ("PS-HEB-001", "Hebron",    31.5326, 35.0998, 35),
    ("PS-HEB-002", "Hebron",    31.5450, 35.0870, 25),
    ("PS-RAM-001", "Ramallah",  31.9038, 35.2034, 40),
    ("PS-NAB-001", "Nablus",    32.2211, 35.2544, 35),
    ("PS-BET-001", "Bethlehem", 31.7054, 35.2024, 20),
    ("PS-JEN-001", "Jenin",     32.4597, 35.2951, 20),
]
# baseline share of daily visits per syndrome (must sum ~1)
SYNDROME_MIX = {"ILI": .25, "AGE": .15, "ARI": .25, "FEVER_RASH": .05, "JAUNDICE": .03,
                "MENINGITIS_LIKE": .02, "HEMORRHAGIC_FEVER": .005, "OTHER": .245}
AGE_BANDS = ["0-4", "5-17", "18-49", "50-64", "65+"]
SOURCES = ["ehr", "ehr", "ehr", "lab", "pharmacy"]

# THE DEMO STORY: AGE cases in Hebron climb from day 24 to 30 (multiplier per day offset)
OUTBREAK = {"city": "Hebron", "syndrome": "AGE", "start_day": 24,
            "multipliers": [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.0]}


def h(s): return hashlib.sha256(s.encode()).hexdigest()[:16]


rows = []
for d in range(DAYS):
    day = END - timedelta(days=DAYS - 1 - d)
    weekday_factor = 0.7 if day.weekday() == 4 else 1.0  # Friday dip
    for fid, city, lat, lon, base in FACILITIES:
        for syn, share in SYNDROME_MIX.items():
            lam = base * share * weekday_factor
            if city == OUTBREAK["city"] and syn == OUTBREAK["syndrome"] and d + 1 >= OUTBREAK["start_day"]:
                lam *= OUTBREAK["multipliers"][min(d + 1 - OUTBREAK["start_day"], 6)]
            n = max(0, int(random.gauss(lam, lam ** 0.5)))
            for i in range(n):
                ts = day + timedelta(hours=random.randint(7, 20), minutes=random.randint(0, 59))
                rows.append({
                    "facility_id": fid, "facility_city": city, "facility_lat": lat, "facility_lon": lon,
                    "reporter_msisdn_hash": h(f"{fid}-staff-{random.randint(1, 4)}"),
                    "patient_hash": h(f"{fid}-{d}-{syn}-{i}"),
                    "age_band": random.choices(AGE_BANDS, weights=[2, 3, 5, 2, 1])[0],
                    "syndrome_code": syn,
                    "severity": random.choices(["mild", "moderate", "severe"], weights=[7, 2.5, .5])[0],
                    "observed_at": ts.isoformat(),
                    "source_system": random.choice(SOURCES),
                })

with OUT.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
print(f"wrote {len(rows)} records -> {OUT}")
