<div align="center">

<img src="docs/assets/banner.png" alt="PadhaiPal — Hinglish Alexa+ Study Companion" width="720">

# PadhaiPal 🎓 — a Hinglish Alexa+ Study Companion

**Ask study questions in Hinglish, get answers in Hinglish — grounded in your own study notes.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![MCP spec 2025-11-25](https://img.shields.io/badge/MCP-2025--11--25-purple.svg)](https://modelcontextprotocol.io/)
[![Demo backend: Gemini](https://img.shields.io/badge/Demo%20backend-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![Hackathon](https://img.shields.io/badge/Build%2C%20Ship%2C%20Shape-Amazon%20Developer%20Hackathon-yellow.svg)](https://amazonappdev2026.devpost.com/)

🎥 **[Watch the demo video](https://youtu.be/6iEvzrVgFB4)** · Track: **Alexa+** · Mini challenge: **Open Source**

</div>

---

## ✨ What it does

Hundreds of millions of Indians think, study, and speak in **Hinglish** — but every major voice assistant answers in stiff, formal English or Hindi. PadhaiPal meets students in the language they actually think in:

- 🗣️ **Ask in Hinglish** — *"gradient descent ko simple words mein samjha do"* — by text or voice (Web Speech API, `hi-IN`)
- 📚 **Grounded answers with citations** — RAG over 134 real ML study notes (450 indexed chunks); every answer cites the exact notes it came from
- 📝 **Instant quizzes** — 3-question quizzes with right/wrong feedback and Hinglish explanations of your mistakes
- 🃏 **Flippable flashcards** — generated from the same notes for quick revision
- 🔊 **Spoken answers** — Hindi-voice text-to-speech, right in the browser

## 🎥 Demo

The full flow — one spoken question → cited Hinglish answer → quiz → flashcards — is in the [demo video](https://youtu.be/6iEvzrVgFB4) (2 min, English narration).

The MCP server's real tool surface, from an actual run of this code:

<div align="center">
<img src="docs/assets/mcp-terminal.png" alt="PadhaiPal MCP server tools/list output" width="720">
</div>

## 🏗️ Architecture

```
Browser (simulated Alexa+ experience)
   │  chat · voice input (hi-IN) · TTS · quiz & flashcard UI
   ▼
Agent  (src/agent.py) ──►  RAG  (src/rag.py)
   │                          TF-IDF over 134 study notes → cited chunks
   ▼
MCP server  (src/mcp_server.py) — Streamable HTTP, 5 tools:
   ask_concept · explain_hinglish · quiz_me · make_flashcards · cite_sources
   │
   ▼
LLM provider  (src/llm.py, pluggable via LLM_PROVIDER)
   gemini (demo) · mock · groq · openrouter · bedrock (implemented, see note)
```

- **MCP server** (`src/mcp_server.py`) — the Alexa+ track's required tech: self-hosted MCP server (spec 2025-11-25+, Streamable HTTP) with 5 tools the agent actually calls at runtime.
- **Simulated Alexa+ experience** (`web/index.html` + `src/web_app.py`) — chat + voice demo UI calling the same agent over HTTP.
- **Agent** (`src/agent.py`) — RAG over 134 ML study notes (TF-IDF, zero-dependency retrieval) + pluggable LLM backends.
- **Honest note on AWS:** a **Bedrock** backend (Converse API, `amazon.nova-micro-v1:0`, us-east-1) is implemented and wired via `LLM_PROVIDER=bedrock`, but the account's Bedrock entitlement is currently blocked (Error 002; AWS Support case 179258850400190, opened 2026-10-21) — no successful Bedrock call has ever been made on this account, so this submission does **NOT** claim the AWS Builder mini challenge. Track: **Alexa+** · Mini challenge: **Open Source**.

## 🧰 Tech stack

| Layer | Tech |
|---|---|
| MCP server | Python, `mcp` SDK v2.3.0, Streamable HTTP |
| Web demo | Starlette, uvicorn, vanilla JS, Web Speech API (`hi-IN`) |
| Retrieval | scikit-learn TF-IDF over 134 markdown notes (450 chunks) |
| LLM (demo) | Google Gemini API |
| LLM (also implemented) | AWS Bedrock Converse API (pending enablement), Groq, OpenRouter, offline mock |

## 🚀 Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then set LLM_PROVIDER and keys

# Point at your notes (or copy them into data/notes/; blank NOTES_DIR defaults there)
export NOTES_DIR=/path/to/notes

# Run everything (web demo at :8000, MCP at :8000/mcp)
LLM_PROVIDER=mock uvicorn src.web_app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 — try *"gradient descent ko simple words mein samjha do"*.

If no notes are present, the app answers from general knowledge and clearly marks that the topic is not covered in your notes; it does not cite unrelated repository files.

### MCP only

```bash
LLM_PROVIDER=mock uvicorn src.mcp_server:http_app --host 127.0.0.1 --port 8000
# Streamable HTTP endpoint: POST http://127.0.0.1:8000/mcp
```

### LLM backends

| `LLM_PROVIDER` | Needs | Notes |
|---|---|---|
| `mock` (default) | nothing | Offline testing; answers marked `[MOCK]` |
| `gemini` | `GEMINI_API_KEY` (AI Studio, free, no card) | **Backend used in the demo/submission** |
| `openrouter` | `OPENROUTER_API_KEY` (free `:free` models, no card) | Swap models via `OPENROUTER_MODEL` |
| `groq` | `GROQ_API_KEY` | Free tier, fast |
| `bedrock` | AWS creds + model access in Bedrock console (us-east-1) | Implemented and wired; **NOT** the demo backend — never verified working on this account (entitlement blocked, Error 002); set `BEDROCK_MODEL_ID` once AWS enables it |

## 📂 Project structure

```
padhaipal/
├── src/
│   ├── mcp_server.py   # MCP server (Streamable HTTP, 5 tools)
│   ├── web_app.py      # simulated Alexa+ web experience backend
│   ├── agent.py        # agent layer over RAG + LLM
│   ├── rag.py          # TF-IDF index over the study notes
│   ├── llm.py          # pluggable LLM providers
│   └── config.py       # env-based configuration
├── web/
│   └── index.html      # chat, voice, quiz & flashcard UI
├── docs/
│   ├── friction-log.md         # build friction log (kept from day one)
│   └── product-feedback-draft.md
├── data/notes/         # 134 study notes (git-ignored — pre-existing data)
├── requirements.txt
└── LICENSE             # MIT
```

## 🗓️ What was built when (submission honesty)

The 134 study notes (`data/notes/`, git-ignored) pre-date the hackathon and are declared as data. Every line of the MCP server, agent, RAG pipeline, and web app was written inside the submission window (Oct 17–23, 2026), for the **Build, Ship, Shape: Amazon Developer Hackathon** (Devpost).

The build's friction log — PEP 668, the MCP SDK v1→v2 rename, the sub-app lifespan bug, and their workarounds — is in [`docs/friction-log.md`](docs/friction-log.md).

## 📜 License

MIT — see [LICENSE](LICENSE).
