"""BREAKY AI agent — orchestrates CAMARA APIs as trusted data sources, then the anomaly model.

Phase 1: deterministic tool-calling pipeline with a readable decision trace.
Phase 2 (Mahmoud): replace `decide()` with the LLM/agent framework allowed by the hackathon's
Resource & Tooling Guide, passing TOOLS as its function/tool schema. Keep the trace format.

Run:  python -m agent.run_agent            (uses mock CAMARA + live backend)
      python -m agent.run_agent --swapped  (simulate a compromised reporter)
"""
import json, sys, urllib.request
from datetime import datetime
from camara import client as camara
from agent import anomaly

API = "http://127.0.0.1:8000"

# Tool schema — this is what gets handed to the LLM in Phase 2
TOOLS = [
    {"name": "verify_reporter_identity", "description": "Check the reporting clinician's SIM was not swapped recently (SIM Swap API). A swapped SIM means the report is untrusted.",
     "parameters": {"type": "object", "properties": {"phone_number": {"type": "string"}}, "required": ["phone_number"]}},
    {"name": "verify_facility_location", "description": "Confirm the reporting device is physically at the registered facility (Location Verification API).",
     "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}, "lat": {"type": "number"}, "lon": {"type": "number"}}, "required": ["device_id", "lat", "lon"]}},
    {"name": "check_network_quality", "description": "Read device reachability (Device Status API). If unreachable, queue for offline sync; if degraded, request QoD.",
     "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}}, "required": ["device_id"]}},
    {"name": "run_anomaly_detection", "description": "Rolling z-score on daily counts for (city, syndrome). Returns NORMAL/WATCH/ALERT/OUTBREAK.",
     "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "syndrome_code": {"type": "string"}}, "required": ["city", "syndrome_code"]}},
    {"name": "emit_ministry_alert", "description": "Publish an alert to the Ministry dashboard with risk level, evidence and recommended protocol.",
     "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "syndrome_code": {"type": "string"}, "risk_level": {"type": "string"}, "z_score": {"type": "number"}, "evidence": {"type": "object"}}, "required": ["city", "syndrome_code", "risk_level", "z_score"]}},
]

PROTOCOLS = {
    "WATCH": "Increase sampling; request lab confirmation from reporting facilities.",
    "ALERT": "Notify district health officer; pre-position ORS/IV fluids; issue water-safety advisory.",
    "OUTBREAK": "Activate district response team; open case-investigation; consider movement advisory for affected wards.",
}


# ---------------- tool implementations (thin wrappers) ----------------

def verify_reporter_identity(phone_number):
    r = camara.check_sim_swap(phone_number)
    return {"trusted": not r["swapped"], **r}

def verify_facility_location(device_id, lat, lon):
    return camara.verify_location(device_id, lat, lon)

def check_network_quality(device_id):
    r = camara.get_device_status(device_id)
    action = "live_sync" if r["reachable"] else "queue_offline"
    return {"action": action, **r}

def run_anomaly_detection(city, syndrome_code):
    return anomaly.assess(city, syndrome_code)

def emit_ministry_alert(city, syndrome_code, risk_level, z_score, evidence=None):
    q = f"{API}/alerts?city={city}&syndrome_code={syndrome_code}&risk_level={risk_level}&z_score={z_score}"
    req = urllib.request.Request(q, data=json.dumps(evidence or {}).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))

TOOL_IMPL = {t["name"]: globals()[t["name"]] for t in TOOLS}


# ---------------- orchestration ----------------

class Trace:
    def __init__(self): self.steps = []
    def log(self, step, tool, args, result, reasoning):
        self.steps.append({"step": step, "tool": tool, "args": args, "result": result, "reasoning": reasoning})
        print(f"\n[{step}] {tool}({json.dumps(args)})\n    -> {json.dumps({k: v for k, v in result.items() if k != 'raw' and k != 'series'})}\n    reasoning: {reasoning}")


def decide(report: dict, trace: Trace) -> dict:
    """Phase 1: hand-written policy. Phase 2: replace with LLM tool-calling loop over TOOLS."""
    # Step 1 — identity
    r1 = TOOL_IMPL["verify_reporter_identity"](report["reporter_phone"])
    trace.log(1, "verify_reporter_identity", {"phone_number": report["reporter_phone"]}, r1,
              "SIM swapped recently -> report untrusted, excluded from surveillance." if not r1["trusted"]
              else "No recent SIM swap -> reporter identity trusted.")
    if not r1["trusted"]:
        return {"outcome": "REJECTED_IDENTITY", "trace": trace.steps}

    # Step 2 — location
    r2 = TOOL_IMPL["verify_facility_location"](report["device_id"], report["facility_lat"], report["facility_lon"])
    trace.log(2, "verify_facility_location", {"device_id": report["device_id"], "lat": report["facility_lat"], "lon": report["facility_lon"]}, r2,
              "Device is at the registered facility -> report geo-attributed with high confidence." if r2["verified"]
              else "Device NOT at facility -> report accepted but down-weighted; flag for review.")

    # Step 3 — network
    r3 = TOOL_IMPL["check_network_quality"](report["device_id"])
    trace.log(3, "check_network_quality", {"device_id": report["device_id"]}, r3,
              f"Device reachable -> {r3['action']}." if r3["reachable"] else "Device unreachable -> queued for offline sync; will retry with QoD.")
    if not r3["reachable"]:
        return {"outcome": "QUEUED_OFFLINE", "trace": trace.steps}

    # Step 4 — model
    r4 = TOOL_IMPL["run_anomaly_detection"](report["facility_city"], report["syndrome_code"])
    trace.log(4, "run_anomaly_detection", {"city": report["facility_city"], "syndrome_code": report["syndrome_code"]}, r4,
              f"Latest count {r4['latest_count']} vs 14-day baseline {r4['baseline_mean']} -> z={r4['z_score']} -> {r4['risk_level']}.")

    # Step 5 — alert
    if r4["risk_level"] in PROTOCOLS:
        evidence = {"z_score": r4["z_score"], "alert_streak_days": r4["alert_streak_days"], "latest_count": r4["latest_count"],
                    "baseline_mean": r4["baseline_mean"], "identity_verified": True, "location_verified": r2["verified"],
                    "protocol": PROTOCOLS[r4["risk_level"]], "emitted_at": datetime.now().isoformat()}
        r5 = TOOL_IMPL["emit_ministry_alert"](report["facility_city"], report["syndrome_code"], r4["risk_level"], r4["z_score"], evidence)
        trace.log(5, "emit_ministry_alert", {"city": report["facility_city"], "risk_level": r4["risk_level"]}, {"alert_id": r5.get("id")},
                  f"Risk {r4['risk_level']} with verified reporter + location -> Ministry alert emitted. Protocol: {PROTOCOLS[r4['risk_level']]}")
        return {"outcome": f"ALERT_EMITTED_{r4['risk_level']}", "trace": trace.steps}
    trace.log(5, "emit_ministry_alert", {}, {"skipped": True}, "Risk NORMAL -> no alert; record counted toward baseline.")
    return {"outcome": "NO_ALERT", "trace": trace.steps}


if __name__ == "__main__":
    # A new incoming report from Hebron — this is the demo trigger
    report = {"reporter_phone": "+3637123456", "device_id": "+3637123456", "facility_id": "PS-HEB-001",
              "facility_city": "Hebron", "facility_lat": 31.5326, "facility_lon": 35.0998, "syndrome_code": "AGE"}
    if "--swapped" in sys.argv:
        camara.check_sim_swap = lambda p, max_age_hours=240: {"swapped": True, "raw": {"_simulated": True}}
    print("=== BREAKY agent run ===  CAMARA_MODE =", camara.MODE)
    result = decide(report, Trace())
    print("\n=== OUTCOME:", result["outcome"], "===")
