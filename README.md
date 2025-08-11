# Enhanced Research Assistant

Production-ready FastAPI service that answers research questions leveraging Perplexity search, OpenAI embeddings (text-embedding-3-large), and Qdrant vector store.

## Quick Start (Docker Compose)
## Quick Demo

Run the complete end-to-end demonstration:

```bash
export OPENAI_API_KEY=sk-...  # Optional - has fallback
export PERPLEXITY_API_KEY=pxy-...  # Optional - has fallback
bash scripts/full_demo.sh
```

See [Full Capabilities Walkthrough](docs/full_capabilities_walkthrough.md) for detailed explanation.


```bash
export OPENAI_API_KEY=sk-...  # Optional - has fallback
export PERPLEXITY_API_KEY=pxy-...  # Optional - has fallback

docker compose up --build
```

Then visit `http://localhost:8000/docs` or call:

```bash
curl -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{"query": "What is CRISPR?"}'
```

## Local Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

Run tests:

```bash
ruff src tests
mypy src
pytest
```

## Architecture Overview

![architecture](docs/architecture.png)

See `docs/ADR-001-initial-architecture.md` for design decisions.
