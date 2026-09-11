import json
import urllib.request
import random
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000"

def seed():
    req = urllib.request.Request(f"{BASE_URL}/reset", method="POST")
    with urllib.request.urlopen(req) as res:
        print("Reset response:", res.read().decode())

    syndromes = ["ILI", "AGE", "ARI", "FEVER_RASH"]
    cities = ["Ramallah", "Nablus", "Hebron", "Jericho"]
    
    for i in range(50):
        days_ago = random.randint(0, 13)
        observed = datetime.now(timezone.utc) - timedelta(days=days_ago)
        
        payload = {
            "facility_id": f"FAC-{random.randint(100, 999)}",
            "facility_city": random.choice(cities),
            "facility_lat": 31.9,
            "facility_lon": 35.2,
            "reporter_msisdn_hash": f"hash_reporter_{i}",
            "patient_hash": f"hash_patient_{i}",
            "age_band": random.choice(["0-4", "5-17", "18-49", "50-64", "65+"]),
            "syndrome_code": random.choice(syndromes),
            "severity": random.choice(["mild", "moderate", "severe"]),
            "observed_at": observed.strftime("%Y-%m-%dT%H:%M:%S"),
            "source_system": random.choice(["ehr", "lab", "pharmacy"])
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/ingest", 
            data=data, 
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                pass
        except Exception as e:
            print(f"Error ingesting record {i}: {e}")

    print("Seeding finished successfully!")

if __name__ == "__main__":
    seed()  