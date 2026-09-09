"""Load data/mock_records.csv into the running API.  Run:  python backend/seed.py"""
import csv, sys, json, urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000"
CSV = Path(__file__).parent.parent / "data" / "mock_records.csv"

rows = list(csv.DictReader(CSV.open()))
for r in rows:
    r["facility_lat"] = float(r["facility_lat"]); r["facility_lon"] = float(r["facility_lon"])

created = dup = 0
for i in range(0, len(rows), 500):
    req = urllib.request.Request(f"{API}/ingest/batch", data=json.dumps(rows[i:i + 500]).encode(),
                                 headers={"Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req))
    created += res["created"]; dup += res["duplicate"]
print(f"seeded: {created} created, {dup} duplicates")
