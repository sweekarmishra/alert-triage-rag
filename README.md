# LLM-Powered Security Alert Triage Assistant (RAG)

Retrieval-augmented assistant that turns anomaly alerts into structured incident summaries
(attack type, severity, recommended actions) grounded in security runbooks, using TF-IDF retrieval
and an LLM prompt that returns JSON.

- **Output validation**: schema check plus a grounding check that every citation comes from the retrieved runbook text.
- **Rule-based fallback** when the LLM fails (invalid JSON, invented citation, API error). Offline mode runs the fallback only.
- **Offline mode identified the correct attack type for 13 of 13 true attacks** (18 labeled alerts: 13 attacks + 5 benign).
- **11 pytest tests** with a mocked LLM client covering invalid JSON, invented citations and API errors.

## Run
    pip install -r requirements.txt
    python3 -m pytest -q          # 11 passed
    python3 server.py             # GUI at http://127.0.0.1:5055
    export ANTHROPIC_API_KEY=...  # optional, enables the "Live API" mode (model via TRIAGE_MODEL)

## Layout
    triage/retriever.py  TF-IDF over runbook sections (citation id = section id, e.g. RB-BRUTE-02)
    triage/prompt.py     prompt + JSON schema
    triage/validator.py  JSON parsing, schema checks, citation grounding check
    triage/fallback.py   rule-based classifier, severity, runbook-derived actions
    triage/llm.py        LLM client interface + Anthropic Messages API client (stdlib)
    triage/pipeline.py   retrieve -> prompt -> validate -> fallback
    server.py, static/   Flask API + interactive console GUI
    data/runbooks/       9 runbooks (26 sections);  data/alerts.json  18 labeled alerts
![GUI](docs/screenshot.png)
## Note on the dataset
Alerts are synthetic and hand-labeled by the project author, and the fallback rules were written
against the same alert style. Say "13 labeled attack scenarios" when discussing the 13/13 figure.

See **GUIDE.md** for the complete guide (run, live API test, GitHub, Render, resume text, demo script, interview Q&A).
