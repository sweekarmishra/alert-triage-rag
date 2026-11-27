"""Local web UI + JSON API. Run: python3 server.py  then open http://127.0.0.1:5055"""
from __future__ import annotations
import json
import os
import re
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from triage import fallback
from triage.llm import AnthropicClient, LLMError
from triage.pipeline import make_retriever, triage

ROOT = Path(__file__).parent
app = Flask(__name__, static_folder=str(ROOT / "static"))
RETRIEVER = make_retriever()
ALERTS = json.loads((ROOT / "data" / "alerts.json").read_text())
BY_ID = {a["alert_id"]: a for a in ALERTS}


class SimLLM:
    """Simulated LLM for the demo: lets you inject the failures the validator is built to catch."""
    def __init__(self, mode: str, alert: dict):
        self.mode, self.alert = mode, alert

    def complete(self, prompt: str) -> str:
        if self.mode == "sim_api_error":
            raise LLMError("503 Service Unavailable (simulated)")
        if self.mode == "sim_invalid_json":
            return "Here is the analysis you asked for: the attack looks serious {severity: high,"
        fb = fallback.triage(self.alert, RETRIEVER.chunks)
        in_prompt = re.findall(r"^\[(RB-[A-Z0-9]+-\d+)\]", prompt, re.M)  # a well-behaved LLM only cites what it was shown
        actions = [dict(a) for a in fb["recommended_actions"] if a["citation"] in in_prompt]
        if not actions and in_prompt:
            actions = [{"action": "Follow the retrieved runbook guidance", "citation": in_prompt[0]}]
        cites = sorted({a["citation"] for a in actions})
        if self.mode == "sim_fake_citation":
            actions[0]["citation"] = "RB-FAKE-99"
            cites = cites + ["RB-FAKE-99"]
        return json.dumps({"attack_type": fb["attack_type"], "severity": fb["severity"],
                           "summary": "LLM (simulated): " + self.alert["description"].split(". ")[0] + ".",
                           "recommended_actions": actions, "citations": cites})


LIVE_PER_HOUR = int(os.environ.get("LIVE_LIMIT_PER_HOUR", "10"))
_live_calls: dict[str, list[float]] = {}


def live_allowed(ip: str) -> bool:
    """Protect the owner's API key on a public deployment: small per-IP hourly budget."""
    now = time.time()
    calls = [t for t in _live_calls.get(ip, []) if now - t < 3600]
    if len(calls) >= LIVE_PER_HOUR:
        _live_calls[ip] = calls
        return False
    _live_calls[ip] = calls + [now]
    return True


def pick_llm(mode: str, alert: dict):
    if mode == "offline":
        return None
    if mode == "live":
        if not live_allowed(request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()):
            raise LLMError(f"live mode rate limit reached ({LIVE_PER_HOUR} calls/hour per visitor)")
        return AnthropicClient()  # raises LLMError if no key; handled by caller
    return SimLLM(mode, alert)


def run(alert: dict, mode: str) -> dict:
    t0 = time.perf_counter()
    try:
        llm = pick_llm(mode, alert)
    except LLMError as e:
        res = triage(alert, RETRIEVER, None)
        res.update(source="fallback", error=f"llm_error: {e}")
    else:
        res = triage(alert, RETRIEVER, llm)
    res["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    res["mode"] = mode
    res["chunk_text"] = {r["id"]: next(c.text for c in RETRIEVER.chunks if c.chunk_id == r["id"])
                         for r in res["retrieved"]}
    return res


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/alerts")
def alerts():
    return jsonify(ALERTS)


@app.get("/api/meta")
def meta():
    return jsonify({"runbooks": len({c.runbook for c in RETRIEVER.chunks}), "chunks": len(RETRIEVER.chunks),
                    "alerts": len(ALERTS), "live_available": bool(os.environ.get("ANTHROPIC_API_KEY"))})


@app.post("/api/triage")
def api_triage():
    body = request.get_json(force=True)
    mode = body.get("mode", "offline")
    if "alert_id" in body:
        alert = BY_ID.get(body["alert_id"])
        if not alert:
            return jsonify({"error": "unknown alert"}), 404
    else:
        desc = (body.get("description") or "").strip()
        if not desc:
            return jsonify({"error": "description required"}), 400
        alert = {"alert_id": "ALR-CUSTOM", "source_ip": "n/a", "dest_ip": "n/a", "dest_port": 0,
                 "description": desc, "metrics": {}}
    return jsonify(run(alert, mode))


@app.get("/api/eval")
def api_eval():
    rows = []
    for a in ALERTS:
        r = triage(a, RETRIEVER)
        rows.append({"alert_id": a["alert_id"], "label": a["label"], "predicted": r["attack_type"],
                     "ok": r["attack_type"] == a["label"], "severity": r["severity"]})
    att = [x for x in rows if x["label"] != "benign"]
    return jsonify({"rows": rows, "attacks_correct": sum(x["ok"] for x in att), "attacks_total": len(att),
                    "all_correct": sum(x["ok"] for x in rows), "all_total": len(rows)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5055"))
    host = "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"  # Render sets PORT
    app.run(host=host, port=port, debug=False)
