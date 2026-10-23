"""PadhaiPal agent: the shared brain behind the MCP tools and the web demo.

Every public function here is pure Python (no HTTP, no MCP types), so both
the MCP server and the simulated Alexa+ web experience call the same code.
"""
from __future__ import annotations

import json
import re

from . import config, llm, rag


def _context_block(hits: list[rag.Hit]) -> tuple[str, list[dict]]:
    """Format retrieved chunks as numbered excerpts + citation metadata."""
    lines, citations = [], []
    for i, h in enumerate(hits, 1):
        lines.append(f"[{i}] (from {h.source}):\n{h.text[:900]}")
        citations.append(
            {"n": i, "source": h.source, "excerpt": h.text[:220].strip()}
        )
    return "\n\n".join(lines), citations


def answer_question(question: str, style: str = "hinglish") -> dict:
    """RAG Q&A: retrieve notes, then have the LLM answer in Hinglish."""
    hits = rag.retrieve(question)
    context, citations = _context_block(hits)
    source_instruction = (
        "Answer in Hinglish, citing excerpts like [1], [2]."
        if hits
        else (
            "No study-note excerpt covers this question. Answer from general "
            "knowledge in Hinglish, say clearly that it is not covered in the "
            "provided notes, and do not invent citations."
        )
    )
    user = (
        f"Study-note excerpts:\n{context}\n\n"
        f"Student's question: {question}\n\n"
        f"{source_instruction}"
    )
    answer = llm.get_llm().complete(config.SYSTEM_PROMPT, user)
    return {"answer": answer, "citations": citations}


def explain_hinglish(topic: str) -> dict:
    """Explain a concept simply, Hinglish-first, with a tiny example."""
    hits = rag.retrieve(f"what is {topic} explain simply with example")
    context, citations = _context_block(hits)
    user = (
        f"Study-note excerpts:\n{context}\n\n"
        f"Explain this concept to a beginner, in simple Hinglish with one "
        f"relatable real-life example: {topic}\n\n"
        "Structure: 1) ek line mein matlab, 2) simple explanation, "
        "3) example, 4) exam tip. "
        + (
            "Cite excerpts like [1]."
            if hits
            else (
                "Say clearly that the provided notes do not cover this topic, "
                "and do not invent citations."
            )
        )
    )
    answer = llm.get_llm().complete(config.SYSTEM_PROMPT, user)
    return {"answer": answer, "citations": citations}


def _parse_json_array(text: str) -> list | None:
    """Best-effort extraction of a JSON array from LLM output."""
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, list) else None
        except json.JSONDecodeError:
            return None
    return None


def quiz_me(topic: str, n: int = 3) -> dict:
    """Generate n multiple-choice quiz questions on a topic."""
    n = max(1, min(n, 5))
    hits = rag.retrieve(topic)
    context, citations = _context_block(hits)
    user = (
        f"Study-note excerpts:\n{context}\n\n"
        f"Create {n} multiple-choice quiz questions about: {topic}.\n"
        "Respond with ONLY a JSON array, no other text. Each item:\n"
        '{"question": "...", "options": ["A) ...", "B) ...", "C) ...", '
        '"D) ..."], "answer": "B", "explanation_hinglish": "..."}'
    )
    raw = llm.get_llm().complete(config.SYSTEM_PROMPT, user)
    parsed = _parse_json_array(raw)
    if parsed is None:
        # Honest fallback: return the raw text instead of fake structure.
        return {"questions": [], "raw_text": raw, "citations": citations}
    return {"questions": parsed[:n], "citations": citations}


def make_flashcards(topic: str, n: int = 5) -> dict:
    """Generate n Q/A flashcards on a topic."""
    n = max(1, min(n, 8))
    hits = rag.retrieve(topic)
    context, citations = _context_block(hits)
    user = (
        f"Study-note excerpts:\n{context}\n\n"
        f"Create {n} flashcards about: {topic}.\n"
        "Respond with ONLY a JSON array, no other text. Each item:\n"
        '{"front": "question in Hinglish", "back": "answer in Hinglish"}'
    )
    raw = llm.get_llm().complete(config.SYSTEM_PROMPT, user)
    parsed = _parse_json_array(raw)
    if parsed is None:
        return {"cards": [], "raw_text": raw, "citations": citations}
    return {"cards": parsed[:n], "citations": citations}


def cite_sources(topic: str) -> dict:
    """Return the raw retrieved sources for a topic (no LLM call)."""
    hits = rag.retrieve(topic)
    _, citations = _context_block(hits)
    return {"citations": citations}


def health() -> dict:
    stats = rag.index_stats()
    return {
        "status": "ok",
        "llm_provider": llm.get_llm().name,
        "rag": stats,
    }
