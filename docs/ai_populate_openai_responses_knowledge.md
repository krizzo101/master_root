# OpenAI Responses API (GPT-5 family) — Structured Outputs Quick Notes

## Correct API and Models
- Use Responses API (not Chat Completions) for GPT‑5 family
  - Endpoint: POST /v1/responses (OpenAI SDK: `client.responses.create`)
- Default model: `gpt-5-mini` (fast, cost-effective); upgrade to `gpt-5` for heavier codegen

## Required/Recommended Parameters
- `model`: `gpt-5-mini` | `gpt-5`
- `input`: single string prompt or an array of input items
- `max_output_tokens`: required for bounded output; do NOT use `max_tokens`
- Structured outputs via JSON Schema (when SDK supports on Responses):
  - `response_format={"type":"json_schema","json_schema": {"name": str, "schema": <JSON Schema>, "strict": true}}`
  - Prefer strict schemas with `additionalProperties: false` and explicit `required`
- Reasoning & verbosity (SDK/version dependent):
  - `reasoning={"effort":"medium"}` (or omit if unsupported)
  - `text={"verbosity":"low"}` (or omit if unsupported)
- Timeouts/Retries:
  - Set HTTP client timeout; implement retry/backoff for 429/5xx/timeouts

## Output Extraction Order of Preference
1) `response.output_parsed` (when `response_format=json_schema` is accepted)
2) `response.output_text` (parse as JSON when schema requested but unsupported)
3) Deep fallback: inspect `response.model_dump()` for `output/outputs[*].content[*].text`

## Cross‑Version Compatibility (Observed in repo and community)
- Some OpenAI Python SDK versions reject certain kwargs on `responses.create`:
  - `response_format` may raise `TypeError: unexpected keyword argument`
  - `reasoning` / `reasoning_effort`, `verbosity` may be rejected
- Progressive fallback strategy:
  1) Try with `response_format + reasoning + text`
  2) On TypeError: drop `response_format`
  3) On TypeError: drop `reasoning`
  4) On TypeError: drop `text`
  5) Always keep `max_output_tokens`
- If `response_format` is dropped, instruct model in the prompt to return JSON and parse `output_text`

## Practical Prompting for Code Generation
- Ask for JSON with fields `{code: string, reasoning: string}`
- Put the full file contents in `code` only; no fences; no extra commentary
- Keep code under ~200 lines per file; avoid network calls; add minimal docstrings

## References
- OpenAI: Introducing Structured Outputs — https://openai.com/index/introducing-structured-outputs-in-the-api/
- Azure OpenAI (structured outputs how‑to; JSON Schema subset and SDK examples) — https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/structured-outputs
- Community threads on json_schema usage, pitfalls, and pydantic conversion

## Repo Observations
- Our logs show frequent `TypeError: unexpected keyword argument 'response_format'` on `responses.create`; fallback without `response_format` succeeds and returns `output_text` that we can parse or use as raw code.
- Switching to `gpt-5-mini` with `max_output_tokens` + retries stabilizes runs.
