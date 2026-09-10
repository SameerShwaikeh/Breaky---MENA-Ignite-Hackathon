# BREAKY — Agent Design (Phase 2)

## Goal

Replace the hand-written `decide()` policy in `agent/run_agent.py` with an LLM tool-calling loop that makes the same decisions, but reasons over the tools instead of following fixed if/else logic — and extends the pipeline to cover medicine-stock awareness and outbreak spread-pattern description, per the full project vision (hospital data → outbreak detection → medicine-stock check → Ministry alert with protocol + spread pattern + stock status).

## System Prompt (summary)

The LLM is told:
- It is BREAKY's decision agent for an early-warning disease surveillance system in the West Bank.
- It receives one incoming clinical report at a time (identity, facility location, syndrome, city).
- It has access to a fixed set of tools (below) and must decide, step by step, which to call and in what order, mirroring the trust chain: verify who reported → verify where → verify connectivity → assess outbreak risk → check response readiness → alert if warranted.
- It must never fabricate tool results — every claim in the final alert must trace back to a tool call.
- It should stop and return early if identity verification fails or the device is unreachable (same short-circuit behavior as current `decide()`).

## Tools

### Existing tools (already implemented in `run_agent.py` / `TOOLS`)

| Tool | Purpose |
|---|---|
| `verify_reporter_identity` | SIM Swap check — is the reporting clinician's identity trustworthy? |
| `verify_facility_location` | Location Verification — is the device physically at the registered facility? |
| `check_network_quality` | Device Status — is the device reachable, or should this be queued offline? |
| `run_anomaly_detection` | Rolling z-score model — NORMAL / WATCH / ALERT / OUTBREAK for a (city, syndrome) pair |
| `emit_ministry_alert` | Publish the final alert to the Ministry dashboard |

### New tool to add for Phase 2

| Tool | Purpose | Notes |
|---|---|---|
| `check_medicine_stock` | Given a city and syndrome code, returns available medicine types and quantities relevant to treating that syndrome in that region | Backed by a new mock data file, e.g. `data/pharmacy_stock.csv` or `.json` (city → medicine type → quantity). Not a CAMARA API — internal mock data, same pattern as `generate_mock.py`. **Needs Sameer/Yasmeen to help produce this mock dataset.** |

**Tool schema (to add to `TOOLS` in `run_agent.py`):**
```python
{"name": "check_medicine_stock",
 "description": "Check available medicine types and quantities in a city's stock, relevant to a given syndrome.",
 "parameters": {"type": "object",
   "properties": {"city": {"type": "string"}, "syndrome_code": {"type": "string"}},
   "required": ["city", "syndrome_code"]}}
```

### Spread-pattern reasoning — not a tool

Describing *how* a disease is likely spreading (e.g. "AGE in this pattern suggests water-borne transmission") is **not** a separate API call — it's reasoning the LLM does itself, using the syndrome code and known epidemiological patterns, combined with the anomaly model's output (which city, how fast it's climbing). This gets composed directly into the final alert text, not fetched from a tool.

## The Loop (Phase 2 flow)

```
1. verify_reporter_identity(phone_number)
   -> if not trusted: return REJECTED_IDENTITY

2. verify_facility_location(device_id, lat, lon)
   -> logged, does not block

3. check_network_quality(device_id)
   -> if unreachable: return QUEUED_OFFLINE

4. run_anomaly_detection(city, syndrome_code)
   -> if risk_level == NORMAL: return NO_ALERT

5. check_medicine_stock(city, syndrome_code)          <- NEW

6. LLM composes reasoning:
   - risk level + evidence (z-score, streak days) from step 4
   - spread-pattern description (LLM's own reasoning from syndrome_code)
   - recommended protocol (same PROTOCOLS mapping as today)
   - medicine stock status from step 5 (sufficient / shortage, by type)

7. emit_ministry_alert(city, syndrome_code, risk_level, z_score, evidence)
   -> evidence now includes: spread_pattern, medicine_stock, protocol
```

This keeps the exact same trace format the team already has (`Trace.log`), so the demo's printed decision trace doesn't need to change shape — just gets two extra steps.

## Framework

Per `docs/tooling_guide.md`: native tool-calling via **Groq** (fallback: Gemini), no multi-agent framework. The existing `TOOLS` list is passed directly to the LLM's function-calling API; `TOOL_IMPL` dispatch stays the same pattern, just called by the LLM's tool-choice output instead of by fixed Python control flow.

## Dependencies / Open Items

- **Blocked on Yara:** final confirmed list of live CAMARA APIs (by midday Day 2) — determines which of steps 1–3 run against real data vs mock.
- **Needs from Sameer/Yasmeen:** a mock medicine-stock dataset (city × syndrome-relevant medicine × quantity) to back `check_medicine_stock`. Should follow the same style as `data/mock_records.csv` / `generate_mock.py`.
- **Not yet decided:** exact list of medicine types per syndrome (needs Yasmeen's clinical input — e.g. which medicines are relevant for AGE vs ILI).
