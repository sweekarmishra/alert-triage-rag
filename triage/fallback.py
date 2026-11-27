"""Rule-based triage used when the LLM is unavailable or returns invalid output (and for offline mode)."""
from __future__ import annotations
import re

SEV_ORDER = ["low", "medium", "high", "critical"]
BASE_SEVERITY = {"brute_force": "medium", "ddos": "high", "port_scan": "low", "sql_injection": "high",
                 "data_exfiltration": "high", "c2_beaconing": "high", "dns_tunneling": "medium",
                 "privilege_escalation": "high", "benign": "low"}
PREFIX = {"brute_force": "RB-BRUTE", "ddos": "RB-DDOS", "port_scan": "RB-SCAN", "sql_injection": "RB-SQLI",
          "data_exfiltration": "RB-EXFIL", "c2_beaconing": "RB-C2", "dns_tunneling": "RB-DNS",
          "privilege_escalation": "RB-PRIV", "benign": "RB-BENIGN"}


def _has(text: str, *words: str) -> bool:
    return any(w in text for w in words)


def classify(alert: dict) -> str:
    """Ordered keyword and metric rules. Order matters: specific signatures before generic ones."""
    t = alert["description"].lower()
    m = alert.get("metrics", {})
    if (m.get("scheduled_job") or m.get("approved_scan") or m.get("campaign") or m.get("patch_window")
            or m.get("then_success") or _has(t, "change calendar", "approved", "scheduled", "campaign", "patch deployment")):
        return "benign"
    if _has(t, "domain admins", "credential dumping", "privilege", "sudo") or m.get("group_change"):
        return "privilege_escalation"
    if "dns" in t and _has(t, "txt", "entropy", "subdomain"):
        return "dns_tunneling"
    if _has(t, "union select", "1=1", "sleep(", "sql", "injection"):
        return "sql_injection"
    if _has(t, "command and control", "beacon") or m.get("threat_intel_match"):
        return "c2_beaconing"
    if _has(t, "uploaded", "exfil") or (_has(t, " gb ") and _has(t, "external", "foreign")):
        return "data_exfiltration"
    if _has(t, "probing", "ports across", "sweep") or m.get("ports_probed") or m.get("hosts_probed"):
        return "port_scan"
    if _has(t, "flood", "half-open", "packets per second", "volumetric"):
        return "ddos"
    if _has(t, "failed") and _has(t, "login", "logon", "authentication"):
        return "brute_force"
    return "benign"


def severity(attack: str, alert: dict) -> str:
    m, t = alert.get("metrics", {}), alert["description"].lower()
    idx = SEV_ORDER.index(BASE_SEVERITY[attack])
    bump = 0
    if attack == "brute_force" and "successful login" in t:
        bump = 1
    if attack == "port_scan" and m.get("internal_source"):
        bump = 1
    if attack == "data_exfiltration" and m.get("outbound_gb", 0) >= 10:
        bump = 1
    if attack == "c2_beaconing" and m.get("threat_intel_match"):
        bump = 1
    if attack == "privilege_escalation" and m.get("group_change"):
        bump = 1
    return SEV_ORDER[min(idx + bump, 3)]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=\.)\s+", text) if s.strip()]


def triage(alert: dict, chunks) -> dict:
    attack = classify(alert)
    pre = PREFIX[attack]
    mine = {c.chunk_id: c for c in chunks if c.chunk_id.startswith(pre)}
    actions = []
    for cid in sorted(mine):
        if cid.endswith("-02"):
            actions += [{"action": s, "citation": cid} for s in _sentences(mine[cid].text)]
        elif cid.endswith("-03"):
            actions += [{"action": s, "citation": cid} for s in _sentences(mine[cid].text)[:1]]
    first = _sentences(alert["description"])[0]
    label = attack.replace("_", " ")
    summary = (f"Rule-based triage classified this alert as {label}. {first}" if attack != "benign"
               else f"Rule-based triage classified this alert as likely benign. {first}")
    return {"attack_type": attack, "severity": severity(attack, alert), "summary": summary,
            "recommended_actions": actions, "citations": sorted({a["citation"] for a in actions}),
            "retrieved_ids": sorted(mine)}
