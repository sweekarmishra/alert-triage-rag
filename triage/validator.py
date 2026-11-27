"""Validation of LLM output, including the grounding check on citations."""
from __future__ import annotations
import json
import re

from .prompt import ATTACK_TYPES, SEVERITIES


class ValidationError(ValueError):
    """Raised when LLM output is unusable."""


def parse_json(raw: str) -> dict:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start:end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValidationError(f"invalid JSON: {e.msg}") from e
    if not isinstance(data, dict):
        raise ValidationError("top level JSON must be an object")
    return data


def validate(data: dict, retrieved_ids: set[str]) -> dict:
    for key in ("attack_type", "severity", "summary", "recommended_actions", "citations"):
        if key not in data:
            raise ValidationError(f"missing field: {key}")
    if data["attack_type"] not in ATTACK_TYPES:
        raise ValidationError(f"unknown attack_type: {data['attack_type']!r}")
    if data["severity"] not in SEVERITIES:
        raise ValidationError(f"unknown severity: {data['severity']!r}")
    if not isinstance(data["summary"], str) or not data["summary"].strip():
        raise ValidationError("summary must be a non-empty string")
    actions = data["recommended_actions"]
    if not isinstance(actions, list) or not actions:
        raise ValidationError("recommended_actions must be a non-empty list")
    cited = set()
    for a in actions:
        if not isinstance(a, dict) or not a.get("action") or not a.get("citation"):
            raise ValidationError("each action needs 'action' and 'citation'")
        cited.add(a["citation"])
    if not isinstance(data["citations"], list):
        raise ValidationError("citations must be a list")
    cited |= set(data["citations"])
    invented = sorted(cited - retrieved_ids)
    if invented:  # grounding check: every citation must come from the retrieved runbook text
        raise ValidationError(f"citations not in retrieved runbooks: {invented}")
    return data
