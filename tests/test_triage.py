import json
from unittest.mock import MagicMock

import pytest

from triage.llm import LLMError
from triage.pipeline import make_retriever, triage
from triage.retriever import load_chunks
from triage.validator import ValidationError, parse_json, validate

ALERTS = json.load(open("data/alerts.json"))
BY_ID = {a["alert_id"]: a for a in ALERTS}
RETRIEVER = make_retriever()


def mock_llm(reply=None, exc=None):
    llm = MagicMock()
    if exc:
        llm.complete.side_effect = exc
    else:
        llm.complete.return_value = reply
    return llm


def good_reply(cite="RB-BRUTE-02", attack="brute_force"):
    return json.dumps({"attack_type": attack, "severity": "high", "summary": "SSH brute force from one IP.",
                       "recommended_actions": [{"action": "Block the source IP", "citation": cite}],
                       "citations": [cite]})


def test_01_runbooks_load_with_unique_citation_ids():
    chunks = load_chunks("data/runbooks")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)) and len(ids) >= 25


def test_02_retriever_returns_matching_runbook_first():
    hits = RETRIEVER.search(BY_ID["ALR-003"]["description"], k=3)
    assert hits[0].chunk.chunk_id.startswith("RB-DDOS")


def test_03_valid_llm_output_is_accepted():
    res = triage(BY_ID["ALR-001"], RETRIEVER, mock_llm(good_reply()))
    assert res["source"] == "llm" and res["error"] is None and res["attack_type"] == "brute_force"


def test_04_invalid_json_triggers_fallback():
    res = triage(BY_ID["ALR-001"], RETRIEVER, mock_llm("Sure! here is some text, not JSON"))
    assert res["source"] == "fallback" and "invalid JSON" in res["error"]
    assert res["attack_type"] == "brute_force"


def test_05_invented_citation_is_rejected_and_fallback_used():
    res = triage(BY_ID["ALR-001"], RETRIEVER, mock_llm(good_reply(cite="RB-FAKE-99")))
    assert res["source"] == "fallback" and "RB-FAKE-99" in res["error"]


def test_06_real_runbook_id_not_retrieved_is_also_rejected():
    ids = {"RB-BRUTE-01"}
    data = json.loads(good_reply(cite="RB-DDOS-02"))
    with pytest.raises(ValidationError, match="not in retrieved"):
        validate(data, ids)


def test_07_api_error_triggers_fallback():
    res = triage(BY_ID["ALR-009"], RETRIEVER, mock_llm(exc=LLMError("503 service unavailable")))
    assert res["source"] == "fallback" and "llm_error" in res["error"]
    assert res["attack_type"] == "data_exfiltration"


def test_08_unexpected_exception_does_not_crash_pipeline():
    res = triage(BY_ID["ALR-011"], RETRIEVER, mock_llm(exc=TimeoutError("timed out")))
    assert res["source"] == "fallback" and res["attack_type"] == "c2_beaconing"


def test_09_schema_violations_are_rejected():
    ids = {"RB-BRUTE-02"}
    bad_type = json.loads(good_reply()); bad_type["attack_type"] = "aliens"
    bad_sev = json.loads(good_reply()); bad_sev["severity"] = "apocalyptic"
    missing = json.loads(good_reply()); del missing["summary"]
    for bad in (bad_type, bad_sev, missing):
        with pytest.raises(ValidationError):
            validate(bad, ids)


def test_10_json_inside_markdown_fence_is_parsed():
    assert parse_json("```json\n" + good_reply() + "\n```")["attack_type"] == "brute_force"


def test_11_offline_mode_finds_all_13_true_attacks_and_cites_only_real_runbooks():
    attacks = [a for a in ALERTS if a["label"] != "benign"]
    assert len(attacks) == 13
    known = {c.chunk_id for c in RETRIEVER.chunks}
    for a in attacks:
        res = triage(a, RETRIEVER)  # llm=None -> offline
        assert res["attack_type"] == a["label"], a["alert_id"]
        assert res["source"] == "offline" and set(res["citations"]) <= known
