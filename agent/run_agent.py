import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

from agent.anomaly import run_anomaly_detection_model

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(message)s")

# --- CAMARA & System Helper Tools ---
def verify_reporter_identity(phone_number: str) -> dict:
    return {"verified": True, "sim_swapped": False}

def verify_facility_location(device_id: str, lat: float, lon: float) -> dict:
    return {"verified": True, "match_score": 1.0}

def check_network_quality(device_id: str) -> dict:
    return {"reachable": True, "status": "ONLINE"}

def check_medicine_stock(city: str, syndrome_code: str) -> dict:
    return {"sufficient": True, "stock_level": "OPTIMAL"}

def emit_ministry_alert(city: str, syndrome_code: str, risk_level: str, evidence: dict, z_score: float, ma_deviation: float, cusum: float) -> dict:
    return {"status": "EMITTED", "alert_id": "ALT-9921", "city": city}

def execute_tool(name: str, args: dict) -> dict:
    if name == "verify_reporter_identity":
        return verify_reporter_identity(args.get("phone_number", ""))
    elif name == "verify_facility_location":
        return verify_facility_location(args.get("device_id", ""), args.get("lat", 0.0), args.get("lon", 0.0))
    elif name == "check_network_quality":
        return check_network_quality(args.get("device_id", ""))
    elif name == "run_anomaly_detection":
        return run_anomaly_detection_model(
            city=args.get("city", ""),
            syndrome_code=args.get("syndrome_code", "")
        )
    elif name == "check_medicine_stock":
        return check_medicine_stock(args.get("city", ""), args.get("syndrome_code", ""))
    elif name == "emit_ministry_alert":
        return emit_ministry_alert(
            city=args.get("city", ""),
            syndrome_code=args.get("syndrome_code", ""),
            risk_level=args.get("risk_level", ""),
            evidence=args.get("evidence", {}),
            z_score=args.get("z_score", 0.0),
            ma_deviation=args.get("ma_deviation", 0.0),
            cusum=args.get("cusum", 0.0)
        )
    return {"error": f"Unknown tool {name}"}


TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "verify_reporter_identity",
            "description": "Verify reporter SIM status via CAMARA",
            "parameters": {"type": "object", "properties": {"phone_number": {"type": "string"}}, "required": ["phone_number"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_facility_location",
            "description": "Verify facility GPS match via CAMARA",
            "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}, "lat": {"type": "number"}, "lon": {"type": "number"}}, "required": ["device_id", "lat", "lon"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_network_quality",
            "description": "Check device network reachability via CAMARA",
            "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}}, "required": ["device_id"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_anomaly_detection",
            "description": "Run statistical ensemble models (Z-Score, MA Dev, CUSUM) on historical CSV cases",
            "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "syndrome_code": {"type": "string"}}, "required": ["city", "syndrome_code"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_medicine_stock",
            "description": "Verify medicine inventory for specific syndrome",
            "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "syndrome_code": {"type": "string"}}, "required": ["city", "syndrome_code"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emit_ministry_alert",
            "description": "Emit ministry alert if risk_level is OUTBREAK",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "syndrome_code": {"type": "string"},
                    "risk_level": {"type": "string"},
                    "evidence": {"type": "object"},
                    "z_score": {"type": "number"},
                    "ma_deviation": {"type": "number"},
                    "cusum": {"type": "number"}
                },
                "required": ["city", "syndrome_code", "risk_level", "evidence", "z_score", "ma_deviation", "cusum"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are BREAKY Epidemiological Agent.
1. Verify identity, location, and network quality.
2. Run anomaly detection.
3. Check medicine stock.
4. If risk_level is OUTBREAK, emit ministry alert.
5. Provide a concise markdown report with a statistical metrics table."""


def decide(report_data: dict):
    prompt = f"Process report for {report_data['city']} ({report_data['syndrome_code']}). Phone: {report_data['phone_number']}, Device: {report_data['device_id']}, Lat: {report_data['lat']}, Lon: {report_data['lon']}"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]


    try:
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        print(f"[*] Running Agent via Groq for {report_data['city']} ({report_data['syndrome_code']})...\n")

        while True:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                max_tokens=500
            )
            msg = response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                print("=== AGENT FINAL DECISION ===")
                print(msg.content)
                break

            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"-> Groq called tool: {fn_name}({fn_args})")

                tool_result = execute_tool(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fn_name,
                    "content": json.dumps(tool_result)
                })
        return
    except Exception as e:
        print(f"[!] Groq execution skipped/failed: {e}. Falling back to Gemini...")

    try:
        from google import genai
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        print(f"[*] Running Agent via Gemini Fallback for {report_data['city']}...\n")
        res = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        print("=== AGENT FINAL DECISION (GEMINI) ===")
        print(res.text)
    except Exception as e:
        print(f"[X] Execution failed on all providers: {e}")

if __name__ == "__main__":
    sample_report = {
        "phone_number": "+99999991000",
        "device_id": "+99999991000",
        "lat": 31.5326,
        "lon": 35.0998,
        "city": "Hebron",
        "syndrome_code": "AGE"
    }
    
    decide(sample_report)