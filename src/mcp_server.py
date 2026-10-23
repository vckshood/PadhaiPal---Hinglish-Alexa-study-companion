"""PadhaiPal MCP server (Model Context Protocol, spec 2025-11-25+, Streamable HTTP).

This is the Alexa+ track's required technology: a self-hosted MCP server that
an Alexa+ Agent Skill / integration can call. Each tool is a thin wrapper over
src/agent.py — the same brain the web demo uses.

The simulated Alexa+ web experience is registered on the SAME app via
@mcp.custom_route (the SDK's supported pattern), so there is exactly one
Starlette app and one lifespan — no sub-app mounting issues.

Run everything (web demo at /, MCP at /mcp):
    LLM_PROVIDER=mock uvicorn src.web_app:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from . import agent

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

mcp = MCPServer(
    "padhaipal",
    instructions=(
        "PadhaiPal is a Hinglish study companion. It answers questions, "
        "explains concepts, and quizzes students using their own study notes."
    ),
)


# ---------------------------------------------------------------- MCP tools
@mcp.tool(description="Answer a study question in Hinglish using the student's notes (RAG).")
def ask_concept(question: str) -> str:
    return json.dumps(agent.answer_question(question), ensure_ascii=False)


@mcp.tool(description="Explain a concept simply in Hinglish with a real-life example and exam tip.")
def explain_hinglish(topic: str) -> str:
    return json.dumps(agent.explain_hinglish(topic), ensure_ascii=False)


@mcp.tool(description="Generate 1-5 multiple-choice quiz questions on a topic (JSON).")
def quiz_me(topic: str, n: int = 3) -> str:
    return json.dumps(agent.quiz_me(topic, n), ensure_ascii=False)


@mcp.tool(description="Generate 1-8 Q/A flashcards on a topic (JSON).")
def make_flashcards(topic: str, n: int = 5) -> str:
    return json.dumps(agent.make_flashcards(topic, n), ensure_ascii=False)


@mcp.tool(description="Return the raw study-note sources matching a topic (no LLM call).")
def cite_sources(topic: str) -> str:
    return json.dumps(agent.cite_sources(topic), ensure_ascii=False)


# ------------------------------------------------- simulated Alexa+ web demo
@mcp.custom_route("/", methods=["GET"])
async def index(request: Request) -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@mcp.custom_route("/api/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    return JSONResponse(agent.health())


@mcp.custom_route("/api/chat", methods=["POST"])
async def chat(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "expected JSON body"}, status_code=400)
    message = (body.get("message") or "").strip()
    mode = (body.get("mode") or "ask").strip().lower()
    if not message:
        return JSONResponse({"error": "message is empty"}, status_code=400)

    try:
        if mode == "explain":
            result = agent.explain_hinglish(message)
        elif mode == "quiz":
            result = agent.quiz_me(message, n=int(body.get("n", 3)))
        elif mode == "flashcards":
            result = agent.make_flashcards(message, n=int(body.get("n", 5)))
        else:
            result = agent.answer_question(message)
    except Exception as exc:  # never crash the demo; say so honestly
        return JSONResponse({"error": f"agent failed: {exc}"}, status_code=500)
    return JSONResponse(result)


def build_app():
    """The single Starlette app: MCP at /mcp (Streamable HTTP) + web demo."""
    return mcp.streamable_http_app()
