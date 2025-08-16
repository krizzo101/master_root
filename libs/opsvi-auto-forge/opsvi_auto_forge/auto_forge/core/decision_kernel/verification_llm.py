from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import os

# Expect project to provide this client; keep import light to avoid circulars.
try:
    from opsvi_auto_forge.infrastructure.llm.openai_client import OpenAIResponsesClient
except Exception:  # pragma: no cover - unit tests will inject a fake
    OpenAIResponsesClient = None  # type: ignore


class VerifierResult(BaseModel):
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    agreement_rate: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


VERIFIER_PROMPT_SYSTEM = (
    "You are a strict software verification judge. "
    "You receive: (1) a claimed output in JSON, (2) a JSON Schema summary, (3) task instructions, "
    "and (4) optional evidence citations. Your job is to grade whether the output is correct and complete. "
    "Return a numeric score in [0,1] representing confidence that this output would pass quality gates. "
    "Be conservative."
)


def _response_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "passed": {"type": "boolean"},
            "score": {"type": "number"},
            "agreement_rate": {"type": "number"},
            "rationale": {"type": "string"},
        },
        "required": ["passed", "score", "agreement_rate", "rationale"],
        "additionalProperties": False,
    }


async def run_verifier_llm(
    output_json: Any,
    schema_summary: str,
    instructions: str,
    evidence_block: str = "",
    model: Optional[str] = None,
    temperature: float = 0.0,
    timeout: float = 30.0,
) -> VerifierResult:
    """Call the verifier model via OpenAI Responses Structured Outputs.

    The project must provide `OpenAIResponsesClient.create_json(model, system, user, schema, **kwargs)`.
    Unit tests can monkeypatch this function.
    """
    if model is None:
        model = os.getenv("REASONING_VERIFIER_MODEL", "gpt-4.1")
    if OpenAIResponsesClient is None:
        # Fallback conservative outcome
        return VerifierResult(
            passed=False,
            score=0.5,
            agreement_rate=0.5,
            rationale="Verifier client unavailable (fallback).",
        )

    system = VERIFIER_PROMPT_SYSTEM
    user = (
        f"INSTRUCTIONS:\n{instructions}\n\n"
        f"SCHEMA SUMMARY:\n{schema_summary}\n\n"
        f"OUTPUT JSON:\n{output_json}\n\n"
        f"EVIDENCE:\n{evidence_block}"
    )
    resp = await OpenAIResponsesClient.create_json(
        model=model,
        system=system,
        user=user,
        schema=_response_schema(),
        temperature=temperature,
        timeout=timeout,
    )
    # resp is expected as a dict-like JSON
    return VerifierResult(**resp)
