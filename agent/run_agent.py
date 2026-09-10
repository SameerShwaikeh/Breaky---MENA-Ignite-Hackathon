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

# استدعاء الدوال من المشروع
try:
    from camara.client import check_sim_swap, verify_location, get_device_status
    from agent.anomaly import run_anomaly_detection_model
except ImportError:
    # Mocks مؤقتة تُرجع كل المعاملات الإحصائية الثلاثة
    def check_sim_swap(phone_number: str): 
        return {"swapped": False, "raw": {}}
        
    def verify_location(device_id: str, lat: float, lon: float): 
        return {"verified": True, "match_rate": 100, "raw": {}}
        
    def get_device_status(device_id: str): 
        return {"reachable": True, "connectivity": ["DATA", "SMS"], "raw": {}}
        
    def run_anomaly_detection_model(city: str, syndrome_code: str): 
        return {
            "city": city,
            "syndrome": syndrome_code,
            "risk_level": "OUTBREAK", 
            "metrics": {
                "actual_cases": 45,
                "z_score": 4.2,
                "ma_deviation": 1.8,
                "cusum": 3.5,
                "models_flagged": 3
            }
        }

def check_medicine_stock(city: str, syndrome_code: str):
    return {"status": "Sufficient"}

# استقبال كافة المعاملات الإحصائية
def emit_ministry_alert(city: str, syndrome_code: str, risk_level: str, z_score: float = 0.0, ma_deviation: float = 0.0, cusum: float = 0.0, evidence: dict = None):
    return {"status": "ALERT_EMITTED", "alert_id": 9921}

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# تعريف الأدوات لـ Groq و Gemini
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "verify_reporter_identity",
            "description": "Verify if the reporter's phone number is trusted using SIM Swap detection.",
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
            "description": "Verify if the device is actually at the expected facility location.",
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
            "description": "Check if the device is reachable on the network.",
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
            "description": "Run ensemble statistical models (Z-Score, Moving Average, CUSUM) to detect outbreaks.",
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
            "description": "Check if there is sufficient medicine stock for the syndrome in the city.",
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
            "description": "Emit an official alert to the Ministry of Health including all ensemble statistical metrics.",
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

SYSTEM_PROMPT = """You are BREAKY, an Autonomous Epidemiological Surveillance Agent deployed for disease outbreak detection.
Your mission is to validate incident reports from healthcare facilities, check network reliability, run ensemble statistical models, and emit alerts to the Ministry of Health if an outbreak or anomaly is detected.

Always follow this evaluation sequence using your available tools:
1. Verify reporter identity (verify_reporter_identity). If untrusted, abort and return REJECTED_IDENTITY.
2. Verify facility location (verify_facility_location).
3. Check network quality (check_network_quality). If unreachable, queue offline and return QUEUED_OFFLINE.
4. Run anomaly detection (run_anomaly_detection) for the reported city and syndrome.
5. Check medicine stock (check_medicine_stock) for the reported city and syndrome.
6. If risk level is WATCH, ALERT, or OUTBREAK, emit a ministry alert (emit_ministry_alert) passing all metrics returned by anomaly detection (z_score, ma_deviation, cusum).

In your final Markdown summary report, you MUST explicitly detail all three ensemble model metrics: Z-Score, Moving Average Deviation, and CUSUM score.
"""

def decide(report_data: dict) -> str:
    """
    Main Agent Loop: Tries Groq first, falls back to Gemini if Groq fails or quota is exceeded.
    """
    groq_api_key = os.environ.get("GROQ_API_KEY")
    
    # --- الخطة أ: التشغيل باستخدام Groq ---
    if groq_api_key:
        try:
            print(f"[*] Trying Groq API for {report_data.get('city')}...")
            client = Groq(api_key=groq_api_key)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Process this new report: {json.dumps(report_data)}"}
            ]
            
            while True:
                response = client.chat.completions.create(
                    model="qwen/qwen3.8-27b",
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=1024
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
            print(f"[!] Groq API failed (maybe quota exceeded): {e}")
            print("[*] Switching to Gemini Fallback...")

    # --- الخطة ب: التشغيل باستخدام Gemini (Fallback) بالباكيج الجديدة ---
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        return "Error: Groq failed and GEMINI_API_KEY is not set in .env file."
        
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return "Error: Please install the new Gemini SDK using: pip install google-genai"

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
        response = chat.send_message(f"Process this new report: {json.dumps(report_data)}")
        
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