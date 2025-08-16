from __future__ import annotations
from typing import Any, Dict, List
from opsvi_auto_forge.core.retrieval_orchestrator.models import ContextPack


def build_prompt_pack(
    role: str,
    task_type: str,
    instructions: str,
    context_pack: ContextPack | None,
    schema: Any,
    knobs: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a structured prompt pack.

    Returns dict with:
      - system
      - user
      - evidence_block
      - schema
      - model_params
    """
    evidence_block = ""
    if context_pack:
        parts: List[str] = []
        for s in context_pack.vector_snippets[:8]:
            parts.append(f"[{s.citation}] {s.text}")
        for s in context_pack.bm25_snippets[:4]:
            parts.append(f"[{s.citation}] {s.text}")
        evidence_block = "\n".join(parts)

    system = (
        "You are a specialized agent. Always comply with the JSON schema. "
        "Cite evidence using the provided citations. If insufficient evidence, say so and request retrieval."
    )
    user = f"{instructions}\n\nEvidence:\n{evidence_block}"

    model_params = {
        "temperature": knobs.get("temperature", 0.1),
    }

    return {
        "system": system,
        "user": user,
        "schema": schema,
        "model_params": model_params,
    }
