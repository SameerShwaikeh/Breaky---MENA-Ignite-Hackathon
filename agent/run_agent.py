"""BREAKY AI agent — orchestrates CAMARA APIs as trusted data sources, then the anomaly model.

Phase 1: deterministic tool-calling pipeline with a readable decision trace.
Phase 2 (Mahmoud): replace `decide()` with the LLM/agent framework allowed by the hackathon's
Resource & Tooling Guide, passing TOOLS as its function/tool schema. Keep the trace format.

Run:  python -m agent.run_agent            (uses mock CAMARA + live backend)
      python -m agent.run_agent --swapped  (simulate a compromised reporter)
"""
import os
import json
from groq import Groq
from dotenv import load_dotenv

try:
    from camara.client import check_sim_swap, verify_location, get_device_status
    from agent.anomaly import run_anomaly_detection_model
except ImportError:
    def check_sim_swap(phone_number: str): 
        return {"swapped": False, "raw": {}}
        
    def verify_location(device_id: str, lat: float, lon: float): 
        return {"verified": True, "match_rate": 100, "raw": {}}
        
    def get_device_status(device_id: str): 
        return {"reachable": True, "connectivity": ["DATA", "SMS"], "raw": {}}
        
    import random

    def run_anomaly_detection_model(city: str, syndrome_code: str):
        actual_cases = random.randint(10, 60)
        
        z_score = round((actual_cases - 15) / 5.0 + random.uniform(-0.3, 0.3), 2)
        ma_dev = round((actual_cases - 20) / 8.0 + random.uniform(-0.2, 0.2), 2)
        cusum = round((actual_cases - 18) / 7.0 + random.uniform(-0.4, 0.4), 2)
        
        z_flagged = z_score > 2.0
        ma_flagged = ma_dev > 1.5
        cusum_flagged = cusum > 2.2
        
        models_flagged = sum([z_flagged, ma_flagged, cusum_flagged])
        
        if models_flagged >= 2:
            risk = "OUTBREAK"
        elif models_flagged == 1:
            risk = "WATCH"
        else:
            risk = "NORMAL"
            
        return {
            "city": city,
            "syndrome": syndrome_code,
            "risk_level": risk, 
            "metrics": {
                "actual_cases": actual_cases,
                "z_score": z_score,
                "ma_deviation": ma_dev,
                "cusum": cusum,
                "models_flagged": models_flagged
            }
        }   

def check_medicine_stock(city: str, syndrome_code: str):
    return {"status": "Sufficient"}

def emit_ministry_alert(city: str, syndrome_code: str, risk_level: str, z_score: float = 0.0, ma_deviation: float = 0.0, cusum: float = 0.0, evidence: dict = None):
    return {"status": "ALERT_EMITTED", "alert_id": 9921}

load_dotenv()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "verify_reporter_identity",
            "description": "Verify phone via SIM Swap.",
            "parameters": {
                "type": "object",
                "properties": {"phone_number": {"type": "string"}},
                "required": ["phone_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_facility_location",
            "description": "Verify facility GPS location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "lat": {"type": "number"},
                    "lon": {"type": "number"}
                },
                "required": ["device_id", "lat", "lon"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_network_quality",
            "description": "Check device network status.",
            "parameters": {
                "type": "object",
                "properties": {"device_id": {"type": "string"}},
                "required": ["device_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_anomaly_detection",
            "description": "Run statistical models for outbreak detection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "syndrome_code": {"type": "string"}
                },
                "required": ["city", "syndrome_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_medicine_stock",
            "description": "Check medicine stock in city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "syndrome_code": {"type": "string"}
                },
                "required": ["city", "syndrome_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "emit_ministry_alert",
            "description": "Emit alert with statistical metrics to Ministry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "syndrome_code": {"type": "string"},
                    "risk_level": {"type": "string"},
                    "z_score": {"type": "number"},
                    "ma_deviation": {"type": "number"},
                    "cusum": {"type": "number"},
                    "evidence": {"type": "object"}
                },
                "required": ["city", "syndrome_code", "risk_level"]
            }
        }
    }
]

TOOL_IMPL = {
    "verify_reporter_identity": check_sim_swap,
    "verify_facility_location": verify_location,
    "check_network_quality": get_device_status,
    "run_anomaly_detection": run_anomaly_detection_model,
    "check_medicine_stock": check_medicine_stock,
    "emit_ministry_alert": emit_ministry_alert
}

SYSTEM_PROMPT = """You are BREAKY, an epidemiological agent.
Follow sequence:
1. verify_reporter_identity (If untrusted -> REJECTED_IDENTITY)
2. verify_facility_location
3. check_network_quality (If unreachable -> QUEUED_OFFLINE)
4. run_anomaly_detection
5. check_medicine_stock
6. emit_ministry_alert (If WATCH/ALERT/OUTBREAK, pass z_score, ma_deviation, cusum).

Return a concise Markdown report explicitly listing Z-Score, MA Dev, and CUSUM score. Keep output under 200 words."""

def decide(report_data: dict) -> str:
    """
    Main Agent Loop: Tries Groq first, falls back to Gemini if Groq fails or quota is exceeded.
    """
    groq_api_key = os.environ.get("GROQ_API_KEY")
    
    if groq_api_key:
        try:
            print(f"[*] Trying Groq API for {report_data.get('city')}...")
            client = Groq(api_key=groq_api_key)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Process this report: {json.dumps(report_data)}"}
            ]
            
            while True:
                response = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=500 
                )
                
                response_message = response.choices[0].message
                messages.append(response_message)
                
                if not response_message.tool_calls:
                    print("\n=== AGENT FINAL DECISION (GROQ) ===")
                    print(response_message.content)
                    return response_message.content
                    
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    print(f"-> Groq called tool: {function_name}({function_args})")
                    
                    try:
                        func_response = TOOL_IMPL[function_name](**function_args) if function_name in TOOL_IMPL else {"error": "Not found"}
                    except Exception as e:
                        func_response = {"error": str(e)}
                        
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(func_response)
                    })
        except Exception as e:
            print(f"[!] Groq API failed: {e}")
            print("[*] Switching to Gemini Fallback...")

    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        return "Error: Groq failed and GEMINI_API_KEY is not set in .env file."
        
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return "Error: Please install Gemini SDK using: pip install google-genai"

    print("[*] Switching to Gemini Fallback (New SDK)...")
    client = genai.Client(api_key=gemini_api_key)
    gemini_tools = list(TOOL_IMPL.values())
    
    try:
        chat = client.chats.create(
            model="gemini-3.6-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=gemini_tools,
                temperature=0.1,
            )
        )
        response = chat.send_message(f"Process this report: {json.dumps(report_data)}")
        
        print("\n=== AGENT FINAL DECISION (GEMINI) ===")
        print(response.text)
        return response.text
    except Exception as e:
        error_msg = f"[!] Gemini Fallback also failed: {e}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    test_report = {
        "phone_number": "+99999991000",
        "device_id": "+99999991000",
        "lat": 31.5326,
        "lon": 35.0998,
        "city": "Hebron",
        "syndrome_code": "AGE"
    }
    decide(test_report)