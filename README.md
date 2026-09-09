# BREAKY — AI-Powered Early Warning Network

Ignite MENA Hackathon · Team: Sameer, Yasmeen, Yara, Mahmoud
Deadline: **Sep 13, 2026, 11:59 PM IST** — submit by the afternoon.

## What this repo does (Phase 1 state)

1. `backend/` — FastAPI ingestion API with a unified, PII-free clinical schema and deduplication (SQLite).
2. `data/` — synthetic 30-day syndromic dataset for 6 Palestinian facilities with an injected AGE outbreak in Hebron.
3. `camara/` — Nokia Network-as-Code client (Location Verification, SIM Swap, Device Status, QoD) with `mock`/`live` switch.
4. `agent/` — AI agent that orchestrates the CAMARA tools → rolling z-score model → Ministry alert, printing a decision trace.

## Run it (everyone, 5 minutes)

```bash
git clone <repo-url> && cd breaky
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # keep CAMARA_MODE=mock unless you're Yara

python data/generate_mock.py                          # -> data/mock_records.csv
uvicorn backend.main:app --reload                     # terminal 1, leave running
python backend/seed.py                                # terminal 2: loads CSV via /ingest/batch
python backend/seed.py                                # run again -> "0 created, 4680 duplicates" proves dedup
python -m agent.run_agent                             # full pipeline -> OUTBREAK alert for Hebron/AGE
python -m agent.run_agent --swapped                   # compromised reporter -> REJECTED_IDENTITY
```

Open http://127.0.0.1:8000/docs for the API explorer. Try `/aggregate?city=Hebron&syndrome=AGE` and `/alerts`.

## Phase 1 tasks by person

### Sameer — backend
- [ ] Create GitHub repo, push this scaffold, add teammates as collaborators, protect nothing (speed > process).
- [ ] Run the commands above; confirm dedup output.
- [ ] Add `GET /health` and CORS middleware (`fastapi.middleware.cors`) so the Phase 3 dashboard can call the API.
- [ ] Add a `--reset` flag to `seed.py` that deletes `breaky.db` first (demo re-runs need a clean state).
- [ ] Write `docs/api.md`: one line per endpoint. Judges read READMEs.

### Yasmeen — clinical spec & data
- [ ] Open `data/generate_mock.py`. Check facility list, syndrome mix and `OUTBREAK` block make clinical sense; edit freely, re-run.
- [ ] Write `docs/clinical_spec.md` with: (a) the 8 syndrome codes + 3–5 presenting symptoms each, (b) why AGE/Hebron is a realistic MENA scenario (water-borne, seasonal), (c) threshold justification: WATCH z≥2, ALERT z≥3, OUTBREAK = 3 consecutive ALERT days, 14-day baseline with 3-day guard band, (d) the privacy list — fields that never leave the facility (name, national ID, raw phone, free text).
- [ ] Sanity-check `python agent/anomaly.py Hebron AGE` vs `python agent/anomaly.py Ramallah AGE` — the second should be NORMAL. If false positives appear elsewhere, tell Mahmoud/Yara to raise thresholds.
- [ ] Start the Idea Capture Template (separate submission deliverable) — you have the clearest problem/impact language.

### Yara — CAMARA / Nokia NaC
- [ ] Register on the Nokia Network-as-Code developer portal, create an app, copy the API key into `.env` as `NAC_TOKEN`. Find the sandbox test device numbers and set `NAC_TEST_DEVICE`.
- [ ] `pip install network-as-code`, read the SDK README, then `CAMARA_MODE=live python camara/client.py`.
- [ ] Each live call in `camara/client.py` follows the SDK's documented pattern but **verify method names/arguments against the README** and fix anything that differs. Expected: Location Verification and Device Status work first; SIM Swap next; QoD after; Number Verification likely needs an on-device flow — if it isn't working by end of Sep 10, drop it and rely on SIM Swap for identity.
- [ ] Paste every REAL response into `camara/samples/*.json` (strip nothing but secrets) and take screenshots into `docs/evidence/` — these go in the demo video and deck.
- [ ] Write `docs/camara_status.md`: table of API → works in sandbox? → notes. This decides Phase 2 scope.

### Mahmoud — agent layer
- [ ] **First:** open the AI Resource and Tooling Guide linked on the HackerEarth problem statement. List every permitted tool/framework/model provider in `docs/tooling_guide.md`. Post it in the team chat. The agent layer may use nothing outside that list.
- [ ] Run `python -m agent.run_agent` and read `decide()` — that hand-written policy is what an LLM tool-calling loop replaces in Phase 2. `TOOLS` is already in JSON-schema shape for that.
- [ ] Design (don't build yet) the Phase 2 loop: system prompt describing BREAKY's mission and the 5 tools → LLM chooses tool → we execute from `TOOL_IMPL` → return result → repeat until it emits or declines an alert. Sketch it in `docs/agent_design.md` naming the framework from the tooling guide.
- [ ] Confirm the dashboard tool for Phase 3 (Streamlit reading `/aggregate` and `/alerts` is the fastest) is not excluded by the guide.

## Phase 1 exit checklist
- Repo on GitHub, all four have pushed
- Backend + seed + agent run on every laptop in mock mode
- At least one real Nokia NaC response saved in `camara/samples/` with a screenshot
- `docs/tooling_guide.md`, `docs/camara_status.md`, `docs/clinical_spec.md` exist
- Idea Capture Template started
