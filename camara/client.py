"""CAMARA / Nokia Network-as-Code client.
CAMARA_MODE=mock  -> returns saved sample JSON from camara/samples/  (default, safe for teammates)
CAMARA_MODE=live  -> calls Nokia NaC using NAC_TOKEN from .env

The live code follows the pattern in the `network-as-code` Python SDK README.
Yara: verify each call against the SDK docs and your sandbox test devices, then save the
REAL responses into camara/samples/ so mock mode returns genuine payloads."""
import json, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
MODE = os.getenv("CAMARA_MODE", "mock")
SAMPLES = Path(__file__).parent / "samples"


def _sample(name):
    p = SAMPLES / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else {"_mock": True, "_missing_sample": name}


def _client():
    import network_as_code as nac  # pip install network-as-code
    return nac.NetworkAsCodeClient(token=os.environ["NAC_TOKEN"])


def _device(client, device_id: str):
    # NaC identifies a device by phone number, NAI, or IP. Sandbox test devices use e.g. "+3670..."
    return client.devices.get(phone_number=device_id) if device_id.startswith("+") \
        else client.devices.get(network_access_identifier=device_id)


# ---------------- public interface (Mahmoud codes against these signatures) ----------------

def verify_location(device_id: str, lat: float, lon: float, radius_km: float = 2.0) -> dict:
    """Is the device within radius_km of (lat, lon)?"""
    if MODE == "mock":
        raw = _sample("location_verification")
        return {"verified": raw.get("verificationResult", "TRUE") == "TRUE",
                "match_rate": raw.get("matchRate"), "raw": raw}
    dev = _device(_client(), device_id)
    res = dev.verify_location(latitude=lat, longitude=lon, radius=int(radius_km * 1000))
    raw = {"result_type": str(res.result_type), "match_rate": getattr(res, "match_rate", None)}
    return {"verified": "TRUE" in raw["result_type"].upper(), "match_rate": raw["match_rate"], "raw": raw}


def check_sim_swap(phone_number: str, max_age_hours: int = 240) -> dict:
    """Was the SIM swapped within the last max_age_hours? (identity trust signal)"""
    if MODE == "mock":
        raw = _sample("sim_swap")
        return {"swapped": bool(raw.get("swapped", False)), "raw": raw}
    dev = _device(_client(), phone_number)
    swapped = dev.verify_sim_swap(max_age=max_age_hours * 60)
    return {"swapped": bool(swapped), "raw": {"swapped": swapped}}


def get_device_status(device_id: str) -> dict:
    """Reachability + connectivity. Drives offline-queue vs live-sync decision."""
    if MODE == "mock":
        raw = _sample("device_status")
        # التعديل هنا: استخدام connectivity كمصفوفة بدلاً من roaming بناءً على تجربة يارا
        return {"reachable": raw.get("reachable", True), "connectivity": raw.get("connectivity", ["SMS", "DATA"]), "raw": raw}
    
    dev = _device(_client(), device_id)
    reach = dev.get_connectivity()
    
    # التعديل هنا للـ Live Mode: الاستغناء عن roaming واسترجاع connectivity كمصفوفة
    raw = {"connectivity": str(reach)}
    
    is_reachable = "CONNECTED" in str(reach).upper() or "TRUE" in str(reach).upper()
    connectivity_array = ["SMS"] if is_reachable else []
    
    return {"reachable": is_reachable, "connectivity": connectivity_array, "raw": raw}


def request_qod(device_id: str, profile: str = "QOS_L", duration_s: int = 600) -> dict:
    """Reserve a QoS session so a facility can push a backlog reliably during congestion."""
    if MODE == "mock":
        raw = _sample("qod")
        return {"session_id": raw.get("sessionId", "mock-session"), "status": raw.get("qosStatus", "AVAILABLE"), "raw": raw}
    dev = _device(_client(), device_id)
    session = dev.create_qod_session(profile=profile, duration=duration_s)
    return {"session_id": session.id, "status": str(session.status), "raw": {"id": session.id, "status": str(session.status)}}


if __name__ == "__main__":
    # Smoke test. Yara: run with CAMARA_MODE=live and a sandbox device, then paste the raw dicts into samples/.
    dev = os.getenv("NAC_TEST_DEVICE", "+3637123456")
    print("mode:", MODE)
    print("location :", verify_location(dev, 31.5326, 35.0998))
    print("sim_swap :", check_sim_swap(dev))
    print("status   :", get_device_status(dev))
    print("qod      :", request_qod(dev))