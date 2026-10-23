"""Entry point: serves the PadhaiPal app.

One Starlette app built by src/mcp_server.build_app():
- GET  /            -> simulated Alexa+ web demo
- POST /api/chat   -> {"message": str, "mode": "ask"|"explain"|"quiz"|"flashcards"}
- GET  /api/health -> index + provider status
- POST /mcp         -> MCP server over Streamable HTTP (spec 2025-11-25+)

Run:
    LLM_PROVIDER=mock uvicorn src.web_app:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

from . import config
from .mcp_server import build_app

app = build_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.WEB_HOST, port=config.WEB_PORT)
