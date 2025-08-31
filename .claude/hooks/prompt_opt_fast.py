#!/usr/bin/env python3
"""Optimized version of prompt_opt.py with lazy loading for faster response times."""

import asyncio
import json
import os
import re
import select
import sys
import textwrap
from datetime import datetime, timezone

# Defer heavy imports until needed
_provider = None
_schema_class = None


def get_provider():
    """Lazy load provider to reduce startup time."""
    global _provider
    if _provider is None:
        # Only import when actually needed
        sys.path.insert(0, "/home/opsvi/master_root/libs/opsvi-llm")
        from opsvi_llm.providers.openai_provider import OpenAIConfig, OpenAIProvider

        config = OpenAIConfig(
            provider_name="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=float(os.getenv("OPENAI_TIMEOUT_SEC", "15.0")),  # Reduced timeout
            enable_audit_logging=False,
            enable_sanitization=False,
        )
        _provider = OpenAIProvider(config)
    return _provider


def get_schema_class():
    """Lazy load schema class."""
    global _schema_class
    if _schema_class is None:
        from typing import Optional

        from pydantic import BaseModel, Field

        class OptimizedPromptSchema(BaseModel):
            """Schema for structured prompt optimization output."""

            optimized_prompt: str = Field(description="The optimized prompt")
            research_required: Optional[bool] = Field(
                default=False, description="Whether research is required"
            )

        _schema_class = OptimizedPromptSchema
    return _schema_class


# Use faster model by default
MODEL = os.getenv("PROMPT_OPT_MODEL", "gpt-5-nano")  # Changed to nano for speed
MAX_TOK = int(os.getenv("PROMPT_OPT_MAX_TOK", "2000"))  # Reduced for speed
TEMP = float(os.getenv("PROMPT_OPT_TEMPERATURE", "0.2"))
SEED = int(os.getenv("PROMPT_OPT_SEED", "42"))

KNOWLEDGE_CUTOFF = os.getenv("KNOWLEDGE_CUTOFF", "2024-06-01")
RESEARCH_ENABLE = os.getenv("RESEARCH_ENABLE", "true").lower() == "true"
DEFAULT_UNSTABLE = [
    "latest",
    "breaking",
    "today",
    "as of",
    "price",
    "cost",
    "fee",
    "exchange rate",
    "version",
    "api",
    "sdk",
    "library",
    "release",
    "changelog",
    "cve",
    "law",
    "regulation",
    "compliance",
    "policy",
    "election",
    "medical",
    "drug",
    "dosage",
    "availability",
    "schedule",
    "deadline",
    "admission",
    "calendar",
]
UNSTABLE_TOPICS = [
    s.strip() for s in os.getenv("RESEARCH_UNSTABLE_TOPICS", "").split(",") if s.strip()
] or DEFAULT_UNSTABLE
CURRENT_DATE = datetime.now(timezone.utc).date().isoformat()


def last_user_prompts(transcript_path, k=5):
    """Extract last k user prompts from transcript."""
    out = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                role = (obj.get("role") or obj.get("author") or "").lower()
                txt = obj.get("prompt") or obj.get("content") or obj.get("text") or ""
                if isinstance(txt, list):
                    txt = "".join(p.get("text", "") for p in txt if isinstance(p, dict))
                if role == "user" and txt:
                    out.append(txt)
        out = out[-k:]
    except Exception:
        pass
    return out


def get_output_text(resp):
    """Extract text from response."""
    OptimizedPromptSchema = get_schema_class()

    if isinstance(resp, OptimizedPromptSchema):
        return resp.model_dump_json()

    if hasattr(resp, "output_text") and resp.output_text:
        return resp.output_text

    try:
        if hasattr(resp, "output") and resp.output:
            for item in resp.output:
                if hasattr(item, "content") and item.content:
                    for content_item in item.content:
                        if hasattr(content_item, "text"):
                            return content_item.text
    except Exception:
        pass

    return ""


def main():
    """Main function with lazy loading for faster startup."""
    # Fast initial checks before loading heavy modules
    if sys.stdin.isatty():
        print(json.dumps({"error": "No input provided", "suppressOutput": True}))
        sys.exit(1)

    # Reduced timeout for faster failure
    readable, _, _ = select.select([sys.stdin], [], [], 3.0)
    if not readable:
        print(json.dumps({"error": "No input received", "suppressOutput": True}))
        sys.exit(1)

    try:
        inp = json.load(sys.stdin)
        user_prompt = inp.get("prompt", "")
        transcript = inp.get("transcript_path", "")

        # Quick exit if no prompt
        if not user_prompt:
            print(json.dumps({"suppressOutput": True}))
            sys.exit(0)

        # Get previous prompts (fast operation)
        prev5 = last_user_prompts(transcript, 5)

        # Prepare prompts (fast)
        system = (
            "Rewrite the user's prompt into a concise, execution-ready instruction. "
            "Preserve intent, remove ambiguity, specify concrete deliverables. "
            "If time-sensitive relative to {cutoff}, prepend 'RESEARCH BEFORE ACTION'. "
            "Output ONLY the optimized prompt text."
        ).format(cutoff=KNOWLEDGE_CUTOFF)

        user = textwrap.dedent(
            f"""
        Context (last 5 user prompts):
        {chr(10).join(f"- {p}" for p in prev5)}

        Knowledge cutoff: {KNOWLEDGE_CUTOFF}
        Current date (UTC): {CURRENT_DATE}

        Current prompt to optimize:
        {user_prompt}
        """
        ).strip()

        # Now load heavy modules (only when actually making the call)
        provider = get_provider()
        OptimizedPromptSchema = get_schema_class()

        # Make the API call
        resp = asyncio.run(
            provider.responses_create_with_structured_output(
                input=[
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system}],
                    },
                    {"role": "user", "content": [{"type": "input_text", "text": user}]},
                ],
                response_model=OptimizedPromptSchema,
                model=MODEL,
                max_tokens=MAX_TOK,
                temperature=TEMP,
            )
        )

        # Process response
        if isinstance(resp, OptimizedPromptSchema):
            optimized = resp.optimized_prompt.strip()
            research_flag = bool(resp.research_required)
        else:
            text = get_output_text(resp)
            try:
                data = json.loads(text)
                optimized = data.get("optimized_prompt", "").strip()
                research_flag = bool(data.get("research_required", False))
            except Exception:
                optimized = text.strip()
                research_flag = False

        # Quick heuristic check
        def needs_research_heuristic(p: str) -> bool:
            p_lower = (p or "").lower()
            if any(tok in p_lower for tok in UNSTABLE_TOPICS):
                return True
            return bool(
                re.search(r"\b(as of|updated|version|release|changelog|cve)\b", p_lower)
            )

        # Output result
        if RESEARCH_ENABLE and (research_flag or needs_research_heuristic(user_prompt)):
            prefix = "[PROMPT_OPTIMIZER]\nRESEARCH BEFORE ACTION:\n"
            injected = f"{prefix}{optimized}\n[END_PROMPT_OPTIMIZER]"
        else:
            injected = f"[PROMPT_OPTIMIZER]\n{optimized}\n[END_PROMPT_OPTIMIZER]"

        print(json.dumps({"output": {"output": {"additionalContext": injected}}}))
        sys.exit(0)

    except Exception as e:
        if os.getenv("DEBUG"):
            print(f"DEBUG: error={e}", file=sys.stderr)
        print(json.dumps({"suppressOutput": True}))
        sys.exit(0)


if __name__ == "__main__":
    main()
