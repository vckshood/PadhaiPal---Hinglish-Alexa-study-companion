# PadhaiPal 🎓 — a Hinglish Alexa+ Study Companion

Built for the **Build, Ship, Shape: Amazon Developer Hackathon** (Devpost, Oct 2026).
Track: **Alexa+** · Mini challenges: **AWS Builder** + **Open Source**.

Ask study questions in Hinglish, get Hinglish answers grounded in your own
study notes (RAG), with citations, quizzes, and flashcards.

## Architecture

- **MCP server** (`src/mcp_server.py`) — the Alexa+ track's required tech:
  self-hosted MCP server (spec 2025-11-25+, Streamable HTTP) with 5 tools:
  `ask_concept`, `explain_hinglish`, `quiz_me`, `make_flashcards`, `cite_sources`.
- **Simulated Alexa+ experience** (`web/index.html` + `src/web_app.py`) — chat +
  voice (Web Speech API, `hi-IN`) demo UI calling the same agent over HTTP.
- **Agent** (`src/agent.py`) — RAG over 134 ML study notes (TF-IDF, zero-dep)
  + pluggable LLM: `mock` (offline) → `groq` → `bedrock` (AWS Builder integration).
- AWS usage (documented for the mini challenge): **Bedrock** (Converse API,
  ap-south-1) as the LLM backend; study notes can live in **S3**.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set LLM_PROVIDER and keys

# Point at your notes (or copy them into data/notes/; blank NOTES_DIR defaults there)
export NOTES_DIR=/path/to/notes

# Run everything (web demo at :8000, MCP at :8000/mcp)
LLM_PROVIDER=mock uvicorn src.web_app:app --host 127.0.0.1 --port 8000
```

If no notes are present, the app answers from general knowledge and clearly
marks that the topic is not covered in your notes; it does not cite unrelated
repository files.

Open http://127.0.0.1:8000 — try "gradient descent ko simple words mein samjha do".

### MCP only

```bash
LLM_PROVIDER=mock uvicorn src.mcp_server:http_app --host 127.0.0.1 --port 8000
# Streamable HTTP endpoint: POST http://127.0.0.1:8000/mcp
```

### LLM backends

| `LLM_PROVIDER` | Needs | Notes |
|---|---|---|
| `mock` (default) | nothing | Offline testing; answers marked `[MOCK]` |
| `gemini` | `GEMINI_API_KEY` (AI Studio, free, no card) | Recommended free pick |
| `openrouter` | `OPENROUTER_API_KEY` (free `:free` models, no card) | Swap models via `OPENROUTER_MODEL` |
| `groq` | `GROQ_API_KEY` | Free tier, fast |
| `bedrock` | AWS creds + model access in Bedrock console (ap-south-1) | Set `BEDROCK_MODEL_ID` to an enabled model |

## What was built when (submission honesty)

The 134 study notes (`data/notes/`, git-ignored) pre-date the hackathon and are
declared as data. Every line of the MCP server, agent, RAG pipeline, and web
app was written inside the submission window (Oct 17–23, 2026).

## Submission checklist

- [ ] Repo public with MIT license (or private + Amazon reviewers added at submit time)
- [ ] Demo video < 3 min, English, YouTube/Vimeo, no third-party trademarks/music
- [ ] Devpost description + product feedback (draft in `docs/`)
- [ ] Friction log (`docs/friction-log.md`) — kept since first commit
- [ ] Open Source mini fields: contribution URL + repo URL + username + description
