# Product feedback — PadhaiPal (draft, fill in as we build)

The hackathon requires feedback on every tool, API, and SDK used: what it was
used for, what worked well, what needs work, how onboarding felt, and whether
we'd build with it again. Draft notes below; final version goes in the
Devpost submission form.

## MCP Python SDK (v2.3.0) — MCP server, Streamable HTTP
- Used for: the Alexa+ track's required technology — 5 tools over Streamable HTTP.
- Worked well: (fill in after build week)
- Needs work: v1→v2 rename breaks all existing tutorials (see friction log).
- Onboarding: (fill in)
- Build with it again? (fill in)

## AWS Bedrock (Converse API, ap-south-1) — LLM backend
- Used for: answer generation over retrieved study notes.
- Worked well: (fill in — pending model-access approval)
- Needs work: (fill in)
- Onboarding: requesting model access in the console took (fill in).
- Build with it again? (fill in)

## Groq API (fallback LLM)
- Used for: (fill in if needed)

## Web Speech API (hi-IN) — voice input in the web demo
- Used for: mic input in the simulated Alexa+ experience.
- Worked well: (fill in)
- Needs work: (fill in)
- Build with it again? (fill in)

## scikit-learn TF-IDF — RAG retrieval
- Used for: zero-dependency retrieval over 134 markdown notes.
- Worked well: instant indexing, no API keys, good enough for a demo corpus.
- Needs work: keyword-based; Hinglish queries only match English terms.
  Upgrade path is embeddings (documented in src/rag.py).
- Build with it again? Yes for scaffolds/prototypes.
