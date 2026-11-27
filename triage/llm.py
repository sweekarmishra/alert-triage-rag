"""LLM client interface and an Anthropic Messages API implementation (stdlib only)."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request


class LLMError(RuntimeError):
    """Any failure talking to the LLM (network, HTTP error, bad response envelope)."""


class LLMClient:
    def complete(self, prompt: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class AnthropicClient(LLMClient):
    DEFAULT_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 30.0,
                 url: str | None = None):
        self.url = url or os.environ.get("ANTHROPIC_API_URL", self.DEFAULT_URL)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model or os.environ.get("TRIAGE_MODEL", "claude-haiku-5-5")
        self.timeout = timeout
        if not self.api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")

    def complete(self, prompt: str) -> str:
        body = json.dumps({"model": self.model, "max_tokens": 1024, "temperature": 0,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST", headers={
            "content-type": "application/json", "x-api-key": self.api_key, "anthropic-version": "2023-06-01"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                payload = json.load(r)
            return payload["content"][0]["text"]
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as e:
            raise LLMError(f"LLM request failed: {e}") from e
