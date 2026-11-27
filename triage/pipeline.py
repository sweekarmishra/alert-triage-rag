"""End to end triage pipeline: retrieve, prompt, validate, fall back."""
from __future__ import annotations
from pathlib import Path

from . import fallback
from .prompt import build_prompt
from .retriever import Retriever, load_chunks
from .validator import ValidationError, parse_json, validate

ROOT = Path(__file__).resolve().parent.parent


def make_retriever(runbook_dir: str | Path = ROOT / "data" / "runbooks") -> Retriever:
    return Retriever(load_chunks(runbook_dir))


def query_for(alert: dict) -> str:
    return alert["description"] + " " + " ".join(f"{k} {v}" for k, v in alert.get("metrics", {}).items())


def triage(alert: dict, retriever: Retriever, llm=None, k: int = 4) -> dict:
    """llm=None means offline mode (rule-based only). With an llm, any failure falls back to rules."""
    hits = retriever.search(query_for(alert), k=k)
    retrieved = [{"id": h.chunk.chunk_id, "score": round(h.score, 3), "title": h.chunk.title,
                  "runbook": h.chunk.runbook} for h in hits]
    base = {"alert_id": alert["alert_id"], "retrieved": retrieved, "error": None}
    if llm is not None:
        prompt = build_prompt(alert, hits)
        try:
            data = validate(parse_json(llm.complete(prompt)), {h.chunk.chunk_id for h in hits})
            return {**base, **data, "source": "llm"}
        except ValidationError as e:
            base["error"] = f"validation: {e}"
        except Exception as e:  # API errors, timeouts, anything unexpected
            base["error"] = f"llm_error: {e}"
    fb = fallback.triage(alert, retriever.chunks)
    ids = {r["id"] for r in retrieved}
    for cid in fb.pop("retrieved_ids"):
        if cid not in ids:
            c = next(c for c in retriever.chunks if c.chunk_id == cid)
            retrieved.append({"id": cid, "score": 0.0, "title": c.title, "runbook": c.runbook})
    return {**base, **fb, "source": "fallback" if llm is not None else "offline"}
