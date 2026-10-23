# Friction log — PadhaiPal

Kept from the first commit. The hackathon awards up to a 10% judging bonus
for friction logs: each entry records the task attempted, steps taken,
expected vs actual, severity, workaround, and an actionable suggestion.

## 2026-10-17 — Environment setup

**Task:** Install Python dependencies for the scaffold (MCP SDK, web server, RAG).
**Steps:** `pip install --user mcp starlette uvicorn scikit-learn boto3 groq ...`
**Expected:** packages install into user site.
**Actual:** pip refused with PEP 668 "externally managed environment".
**Severity:** low (one-time setup).
**Workaround:** created a project venv (`python3 -m venv .venv`) and installed there.
**Suggestion for tool teams:** none — PEP 668 behaved correctly; the venv is the
right call and makes the repo reproducible for judges.

## 2026-10-17 — MCP SDK major version

**Task:** Wire the Alexa+ track's required tech: an MCP server over Streamable HTTP.
**Steps:** `pip install mcp`, then probed `mcp.server.fastmcp.FastMCP`.
**Expected:** FastMCP importable (matches most tutorials).
**Actual:** `mcp` 2.3.0 installed; `mcp.server.fastmcp` no longer exists — FastMCP
was renamed to `MCPServer` (`from mcp.server.mcpserver import MCPServer`).
The import error message itself pointed at the migration guide, which was helpful.
**Severity:** medium (would have broken every tutorial-following builder).
**Workaround:** used the v2 API: `MCPServer("padhaipal")`, `@mcp.tool()`,
`mcp.streamable_http_app()`. Verified the full JSON-RPC handshake
(initialize → notifications/initialized → tools/list → tools/call) over HTTP.
**Suggestion for tool teams:** the rename is fine, but the top search results
still teach the v1 API — an official "v1 vs v2 in 60 seconds" note on the
PyPI page would save builders real time.

## 2026-10-17 — MCP sub-app lifespan when mounted

**Task:** Serve the web demo and the MCP server from one uvicorn process by
mounting `mcp.streamable_http_app()` under a parent Starlette app.
**Expected:** the MCP endpoint works; Starlette runs mounted sub-app lifespans.
**Actual:** `POST /mcp` → 500, `RuntimeError: Task group is not initialized.
Make sure to use run()` — the streamable-HTTP session manager's task group
never started when mounted as a sub-app.
**Severity:** medium (a natural architecture that silently breaks).
**Workaround:** register the web routes directly on the MCP server with the
SDK's `@mcp.custom_route` decorator and serve the single app from
`mcp.streamable_http_app()`. One app, one lifespan, works first try.
**Suggestion for tool teams:** document that `streamable_http_app()` must be
the root app (or that mounting needs manual lifespan handling) — the
`custom_route` decorator deserves top billing in the docs for exactly this
"one process, HTTP + MCP" shape.

## 2026-10-17 — Groq API key org-restricted

**Task:** Wire a real LLM into the demo's Hinglish answer generation using the
Groq key supplied by the builder (used once, transiently, never saved).
**Steps:** passed the key to the Groq chat-completions endpoint via the
httpx-based provider in `src/llm.py` (verified request shape offline with
MockTransport first).
**Expected:** authenticated generation, making Groq the free-tier default LLM path.
**Actual:** Groq accepted the key format but returned 400
`organization_restricted` — the org behind that key is restricted, so the key
is unusable for inference. The Groq path is dead unless the org restriction
is cleared or a key from another account is used.
**Severity:** medium (killed the cheapest real-LLM path; forced a provider switch).
**Workaround:** dropped Groq as the default; added `gemini` and `openrouter`
providers to `src/llm.py` instead (no new deps, one retry on 429), with the
missing-key guard raising an honest error.
**Suggestion for tool teams:** a 400 `organization_restricted` reads like a
malformed request — surfacing "your organization is restricted" in plain
language (and whether it's fixable) would save builders the debugging loop.

## 2026-10-18 — Gemini model retired; live generation blocked by VM egress proxy

**Task:** Complete a live Hinglish generation test with the builder's Google AI
Studio (Gemini) key (used transiently, never saved; verified VALID via
authenticated API responses).
**Steps:** pointed `src/config.py` / `.env.example` at `gemini-2.5-flash`,
then `gemini-3.8-flash`; attempted `generateContent` calls over httpx,
requests, and streaming.
**Expected:** a live end-to-end answer over the RAG chunks in Hinglish.
**Actual:** two separate blockers. (1) `gemini-2.5-flash` is retired for new
users — Google returns 404, so the repo default was changed to
`gemini-3.8-flash` in `src/config.py` and `.env.example`. (2) Even tiny
requests pass through this VM's egress proxy, but `generateContent` hangs
240s+ — the proxy stalls the response, never an auth or code failure.
**Severity:** medium (the last on-VM verification step; blocks nothing in the
repo itself).
**Workaround:** handed the live test to the builder's own machine:
`LLM_PROVIDER=gemini uvicorn src.web_app:app` with the key in the gitignored
`.env`. All on-VM checks (imports, retrieval, mock generation, request shape)
remain green without a key.
**Suggestion for tool teams:** a pinned "which models are actually live this
month" table on the model docs would have saved the 404 detour — retirement
news travels by word of mouth right now.
