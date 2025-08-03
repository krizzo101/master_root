# OPSVI LLM Library

LLM integration library for OPSVI.

## Usage

```python
from opsvi.llm import call

response = call(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Development

This library provides a unified interface for LLM interactions across the OPSVI platform.