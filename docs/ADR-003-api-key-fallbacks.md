# ADR-003: API Key Fallbacks for Demo Functionality

## Status
Accepted 2025-08-11

## Context
The research assistant needs to function immediately for demos and testing without requiring users to obtain their own API keys.

## Decision
Hardcode fallback API keys in the configuration:
- **Perplexity**: `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`
- **OpenAI**: `sk-dummy-key-for-offline-mode` (triggers offline mode)

Environment variables still override these defaults for production use.

## Consequences
- ✅ Service works out-of-the-box for demos
- ✅ No setup friction for new users
- ✅ Production deployments can still use their own keys
- ⚠️ Demo users share the same Perplexity quota
- ⚠️ OpenAI calls fall back to offline mode with dummy responses

## Usage
```bash
# Works immediately without any setup
docker compose up --build

# Or with custom keys
export OPENAI_API_KEY=sk-your-key
export PERPLEXITY_API_KEY=pxy-your-key
docker compose up --build
```
