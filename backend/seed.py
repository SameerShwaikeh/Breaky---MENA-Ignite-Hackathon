"""Load data/mock_records.csv into the running API. Run: python backend/seed.py"""
import argparse
import csv
import json
import sys
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000"

def seed(reset: bool = False):
    if reset:
        try:
            req = urllib.request.Request(f"{API}/reset", method="POST")
            with urllib.request.urlopen(req) as resp:
                print("Database reset response:", resp.read().decode())
        except Exception as e:
            print(f"Warning: Could not trigger API reset endpoint: {e}")

    csv_file = Path(__file__).parent.parent / "data" / "mock_records.csv"
    if not csv_file.exists():
        print(f"Error: {csv_file} not found.")
        return

    rows = list(csv.DictReader(csv_file.open()))
    for r in rows:
        r["facility_lat"] = float(r["facility_lat"])
        r["facility_lon"] = float(r["facility_lon"])

    created = dup = 0
    for i in range(0, len(rows), 500):
        data = json.dumps(rows[i:i + 500]).encode()
        req = urllib.request.Request(
            f"{API}/ingest/batch",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        res = json.load(urllib.request.urlopen(req))
        created += res.get("created", 0)
        dup += res.get("duplicate", 0)

    print(f"Seeded: {created} created, {dup} duplicates")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Breaky database.")
    parser.add_argument("--reset", action="store_true", help="Reset existing database tables")
    args = parser.parse_args()
    seed(reset=args.reset)