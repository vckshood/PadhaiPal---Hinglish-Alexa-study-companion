"""RAG over Vicky's 100 Days of ML notes.

Scaffold-grade retrieval: TF-IDF over paragraph chunks (scikit-learn).
Fast, dependency-light, no API keys needed. Upgrade path: swap
TfidfVectorizer for embeddings without changing the public functions.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from . import config


@dataclass
class Chunk:
    source: str   # e.g. "007 - Gradient Descent - ....md"
    text: str


@dataclass
class Hit:
    source: str
    text: str
    score: float


_index: dict | None = None


def _chunk_markdown(text: str, target: int = config.CHUNK_TARGET_CHARS) -> list[str]:
    """Split markdown into paragraph chunks, merging tiny ones."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) + 2 <= target or not buf:
            buf = f"{buf}\n\n{p}".strip()
        else:
            chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return chunks


def build_index(notes_dir: Path | None = None) -> dict:
    """Load every .md file under notes_dir and build the TF-IDF index."""
    global _index
    notes_dir = notes_dir or config.NOTES_DIR
    if not notes_dir.is_dir():
        if notes_dir != config.NOTES_DIR or config.NOTES_DIR_CONFIGURED:
            raise FileNotFoundError(
                f"Notes dir not found: {notes_dir}. "
                "Set NOTES_DIR env var or copy notes into data/notes/."
            )
        chunks: list[Chunk] = []
    else:
        chunks = []
        for md in sorted(notes_dir.glob("*.md")):
            if md.name.lower() in {"index.md"}:
                continue
            text = md.read_text(encoding="utf-8", errors="ignore")
            for c in _chunk_markdown(text):
                chunks.append(Chunk(source=md.name, text=c))

    if not chunks:
        _index = {"chunks": [], "vectorizer": None, "matrix": None}
        return _index

    vectorizer = TfidfVectorizer(stop_words="english", max_features=20000)
    matrix = vectorizer.fit_transform(c.text for c in chunks)
    _index = {"chunks": chunks, "vectorizer": vectorizer, "matrix": matrix}
    print(f"[rag] indexed {len(chunks)} chunks from {notes_dir}")
    return _index


def retrieve(query: str, k: int | None = None) -> list[Hit]:
    """Return the top-k most relevant chunks for a query."""
    global _index
    if _index is None:
        build_index()
    assert _index is not None
    if not _index["chunks"]:
        return []
    k = k or config.TOP_K
    vec = _index["vectorizer"].transform([query])
    scores = linear_kernel(vec, _index["matrix"]).flatten()
    top = scores.argsort()[::-1][:k]
    chunks: list[Chunk] = _index["chunks"]
    return [
        Hit(source=chunks[i].source, text=chunks[i].text, score=float(scores[i]))
        for i in top
        if scores[i] > 0
    ]


def index_stats() -> dict:
    global _index
    if _index is None:
        build_index()
    assert _index is not None
    chunks: list[Chunk] = _index["chunks"]
    return {
        "chunks": len(chunks),
        "files": len({c.source for c in chunks}),
        "notes_dir": str(config.NOTES_DIR),
        "available": bool(chunks),
    }
