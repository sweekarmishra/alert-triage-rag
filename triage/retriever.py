"""TF-IDF retrieval over runbook sections."""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

HEADING = re.compile(r"^## \[(?P<id>RB-[A-Z0-9]+-\d+)\]\s*(?P<title>.+)$")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str      # e.g. RB-BRUTE-01, used as the citation key
    runbook: str       # runbook title
    title: str         # section title
    text: str          # section body


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


def load_chunks(runbook_dir: str | Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(Path(runbook_dir).glob("*.md")):
        runbook, cur, body = "", None, []
        def flush():
            if cur:
                chunks.append(Chunk(cur[0], runbook, cur[1], " ".join(body).strip()))
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                runbook = line[2:].strip()
            m = HEADING.match(line)
            if m:
                flush()
                cur, body = (m["id"], m["title"].strip()), []
            elif cur and line.strip():
                body.append(line.strip())
        flush()
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = self.vec.fit_transform(f"{c.runbook} {c.title} {c.text}" for c in chunks)

    def search(self, query: str, k: int = 4) -> list[Hit]:
        q = self.vec.transform([query])
        sims = linear_kernel(q, self.matrix).ravel()
        order = sims.argsort()[::-1][:k]
        return [Hit(self.chunks[i], float(sims[i])) for i in order if sims[i] > 0]
