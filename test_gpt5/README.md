# test_gpt5

A Python coding agent powered by GPT-5 and the OpenAI Responses API that:

- Translates natural language requests into fully functional software applications.
- Accepts an existing codebase as input and generates/applies patches to implement requested changes.

It uses `.reference/openai-cookbook/examples/gpt-5/apply_patch.py` mechanics (ported) to apply patch diffs safely.

## Requirements

- Python >= 3.10
- Environment variable `OPENAI_API_KEY` set (do not print or commit this).

## Install

```bash
uv sync || pip install -e .[dev]
```

## CLI

Two modes:

- build-app: Generate a new app from a natural language specification.
- patch-repo: Apply model-generated patches to an existing repository.

Examples:

```bash
python -m test_gpt5.agent.main build-app --spec "A simple Flask TODO app with SQLite"

python -m test_gpt5.agent.main patch-repo --repo /path/to/repo --request "Convert sync HTTP calls to async; add retries"
```

## Notes

- Uses Responses API `previous_response_id` to maintain context across tool calls.
- Tool set includes: web_search, web_scraping, tech_docs, local_reference_scan, generate_patch (model-driven), apply_patch, run_tests.
- Patch application is safe (relative paths only). Clear errors are surfaced for conflicts.

