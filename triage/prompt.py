"""Prompt construction for the LLM."""
from __future__ import annotations
import json

ATTACK_TYPES = ["brute_force", "ddos", "port_scan", "sql_injection", "data_exfiltration",
                "c2_beaconing", "dns_tunneling", "privilege_escalation", "benign"]
SEVERITIES = ["low", "medium", "high", "critical"]

SYSTEM = ("You are a SOC triage assistant. Use ONLY the runbook excerpts provided. "
          "Respond with a single JSON object and nothing else.")


def build_prompt(alert: dict, hits) -> str:
    context = "\n".join(f"[{h.chunk.chunk_id}] ({h.chunk.runbook} - {h.chunk.title}) {h.chunk.text}" for h in hits)
    schema = {
        "attack_type": f"one of {ATTACK_TYPES}",
        "severity": f"one of {SEVERITIES}",
        "summary": "2 sentence incident summary",
        "recommended_actions": [{"action": "string", "citation": "runbook id such as RB-BRUTE-02"}],
        "citations": ["runbook ids used"],
    }
    alert_view = {k: v for k, v in alert.items() if k != "label"}
    return (f"{SYSTEM}\n\nRUNBOOK EXCERPTS:\n{context}\n\nALERT:\n{json.dumps(alert_view, indent=2)}\n\n"
            f"Return JSON with this shape:\n{json.dumps(schema, indent=2)}\n"
            "Every citation must be an id that appears in the runbook excerpts above.")
