#!/usr/bin/env python3
import asyncio
import json
import os
import pathlib
import re
import sys

# datetime import removed - not used

# Use shared central AI interface instead of direct OpenAI
# Replaced direct OpenAI usage with shared central AI interface (automated migration)
sys.path.insert(0, "/home/opsvi/master_root/libs/opsvi-llm")
# typing imports not used

from opsvi_llm.providers.openai_provider import OpenAIConfig, OpenAIProvider  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

# Initialize provider with timeout support
config = OpenAIConfig(
    provider_name="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=float(os.getenv("OPENAI_TIMEOUT_SEC", "25.0")),
    enable_audit_logging=False,
    enable_sanitization=False,
)
provider = OpenAIProvider(config)

# Default to nano → mini, per README intent
MODEL_PRIMARY = os.getenv("REVIEW_MODEL", "gpt-5-nano")
MODEL_ESCALATE = os.getenv(
    "REVIEW_MODEL_ESCALATE", "gpt-5-mini"
)  # optional one-time escalation
MAX_ATTEMPTS = int(os.getenv("REVIEW_MAX_ATTEMPTS", "3"))
MAX_TOK = int(os.getenv("REVIEW_MAX_TOK", "4000"))
TEMP = float(os.getenv("REVIEW_TEMPERATURE", "0.2"))
SEED = int(os.getenv("REVIEW_SEED", "42"))

STATE_DIR = pathlib.Path(
    os.getenv("CLAUDE_PROJECT_DIR", "."), ".claude", "hooks", "state"
)
STATE_DIR.mkdir(parents=True, exist_ok=True)

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
    "travel",
    "weather",
    "market",
    "stock",
    "crypto",
    "ceo",
    "cfo",
    "leadership",
    "org change",
]
UNSTABLE_TOPICS = [
    s.strip() for s in os.getenv("RESEARCH_UNSTABLE_TOPICS", "").split(",") if s.strip()
] or DEFAULT_UNSTABLE


def read_last_items(transcript_path, k_user=5):
    users, assistant = [], ""
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            items = [json.loads(x) for x in f if x.strip().startswith("{")]
        for obj in reversed(items):
            role = (obj.get("role") or obj.get("author") or "").lower()
            text = obj.get("content") or obj.get("text") or obj.get("prompt") or ""
            if isinstance(text, list):
                text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
            if role == "assistant" and not assistant:
                assistant = text
            if role == "user" and text:
                users.append(text)
            if assistant and len(users) >= k_user:
                break
    except Exception:
        pass
    return assistant, list(reversed(users))[:k_user]


# Define schema for structured output
class ReviewVerdictSchema(BaseModel):
    """Schema for review verdict output."""

    passed: bool = Field(description="Whether the review passed")
    guidance: str = Field(
        description="Specific, actionable fixes if failed; otherwise 'OK'."
    )

    class Config:
        extra = "forbid"  # This translates to additionalProperties: false

    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure all fields are required for OpenAI strict mode."""
        schema = super().model_json_schema(**kwargs)
        # OpenAI strict mode requires all fields in 'required' array
        if "properties" in schema:
            schema["required"] = list(schema["properties"].keys())
        return schema


def get_output_text(resp):
    # Extract text from Responses API response or structured output
    # For structured responses from opsvi-llm
    if isinstance(resp, ReviewVerdictSchema):
        return resp.model_dump_json()

    # First try direct attribute
    if hasattr(resp, "output_text") and resp.output_text:
        return resp.output_text

    # Try to extract from output structure
    try:
        if hasattr(resp, "output") and resp.output:
            for item in resp.output:
                if hasattr(item, "content") and item.content:
                    for content_item in item.content:
                        if hasattr(content_item, "text"):
                            return content_item.text
    except Exception:
        pass

    # Return empty string if no text found (don't convert whole response to string)
    return ""


def call_review(model, assistant_out, prev5):
    # TODO: temporary print-based debug — replace with proper logger before merge/release
    if os.getenv("DEBUG"):
        print(
            f"DEBUG: answer_review.py:call_review() -- calling model={model} with {len(prev5)} previous prompts",
            file=sys.stderr,
        )
    system = (
        "You are a strict reviewer for a dev agent's answer. Check for: factual errors, internal contradictions, "
        "unsafe/destructive commands, missing acceptance tests, and mismatches with the prompt/context. "
        "Return a verdict and concrete guidance to fix failures."
    )
    # Schema now defined as Pydantic model (ReviewVerdictSchema)
    user = (
        "Previous 5 user prompts:\n"
        + "\n".join(f"- {p}" for p in prev5)
        + "\n\nAnswer to review:\n"
        + assistant_out
    )
    # Replaced direct OpenAI usage with shared central AI interface
    # Provider will automatically use correct parameters based on model
    r = asyncio.run(
        provider.responses_create_with_structured_output(
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system}]},
                {"role": "user", "content": [{"type": "input_text", "text": user}]},
            ],
            response_model=ReviewVerdictSchema,
            model=model,
            max_tokens=MAX_TOK,  # Will be translated to max_output_tokens
            temperature=TEMP,
            # Note: seed parameter may not be supported by all models
        )
    )
    # Response is now a structured object (ReviewVerdictSchema)
    if isinstance(r, ReviewVerdictSchema):
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(
                f"DEBUG: answer_review.py:call_review() -- response received, passed={r.passed}",
                file=sys.stderr,
            )
        return {"passed": r.passed, "guidance": r.guidance}
    else:
        # Fallback for unexpected response format
        out = get_output_text(r)
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(
                f"DEBUG: answer_review.py:call_review() -- response received, output_text={bool(out)}",
                file=sys.stderr,
            )
        try:
            return json.loads(out)
        except Exception:
            return {"passed": False, "guidance": out}


def attempts_file(session_id, scope="global"):
    return STATE_DIR.joinpath(f"{session_id}.{scope}.review.json")


def get_attempts(session_id, scope):
    p = attempts_file(session_id, scope)
    if p.exists():
        try:
            return json.loads(p.read_text()).get("attempts", 0)
        except Exception:
            return 0
    return 0


def set_attempts(session_id, scope, n):
    attempts_file(session_id, scope).write_text(json.dumps({"attempts": n}))


def likely_time_sensitive(text: str) -> bool:
    t = (text or "").lower()
    if any(tok in t for tok in UNSTABLE_TOPICS):
        return True
    return bool(re.search(r"\b(as of|updated|version|release|changelog|cve)\b", t))


def has_sources(text: str) -> bool:
    t = (text or "").lower()
    return any(
        k in t
        for k in ["sources:", "citations:", "references:", "no recent changes found"]
    )


def main():
    try:
        inp = json.load(sys.stdin)
        session_id = inp.get("session_id", "")
        transcript = inp.get("transcript_path", "")
        stop_hook_active = bool(inp.get("stop_hook_active", False))
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(
                f"DEBUG: answer_review.py:main() -- session_id={session_id}, stop_hook_active={stop_hook_active}",
                file=sys.stderr,
            )
        scope = (
            inp.get("tool_name") or "final"
        ).lower()  # separate counters per tool/final

        assistant_out, prev5_user = read_last_items(transcript)

        # If nothing to review, allow stop quietly
        if not (assistant_out and assistant_out.strip()):
            print(json.dumps({"suppressOutput": True}))
            sys.exit(0)

        # Research enforcement (pre-check before LLM review to save tokens)
        if (
            RESEARCH_ENABLE
            and likely_time_sensitive(" ".join(prev5_user + [assistant_out]))
            and not has_sources(assistant_out)
        ):
            attempts = get_attempts(session_id, scope)
            if attempts < MAX_ATTEMPTS and not stop_hook_active:
                set_attempts(session_id, scope, attempts + 1)
                print(
                    json.dumps(
                        {
                            "decision": "block",
                            "reason": (
                                "Research required: The topic appears time-sensitive relative to the knowledge cutoff "
                                f"({KNOWLEDGE_CUTOFF}). Before finalizing, perform a brief KB/docs (and web if available) check, "
                                "summarize any updates since the cutoff, and include Sources:/Citations: or a 'no recent changes found' note. "
                                f"(attempt {attempts+1}/{MAX_ATTEMPTS})"
                            ),
                        }
                    )
                )
                sys.exit(0)

        # Regular review pass/fail
        attempts = get_attempts(session_id, scope)
        verdict = call_review(MODEL_PRIMARY, assistant_out, prev5_user)

        # Optional one-time escalation to a larger model if second check fails
        if not verdict.get("passed", False) and attempts == 1 and MODEL_ESCALATE:
            verdict = call_review(MODEL_ESCALATE, assistant_out, prev5_user)

        # Allow stop on pass / cap / already continuing
        if verdict.get("passed", False) or attempts >= MAX_ATTEMPTS or stop_hook_active:
            set_attempts(session_id, scope, 0)
            print(json.dumps({"suppressOutput": True}))
            sys.exit(0)

        # Block and request revision with explicit guidance
        set_attempts(session_id, scope, attempts + 1)
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": f"Reviewer feedback (attempt {attempts+1}/{MAX_ATTEMPTS}):\n{verdict.get('guidance','')}\n"
                    f"Revise and return only the improved answer.",
                }
            )
        )
        sys.exit(0)
    except Exception as e:
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(f"DEBUG: answer_review.py:main() -- exception={e}", file=sys.stderr)
        # On reviewer failure, do NOT block delivery
        print(json.dumps({"suppressOutput": True}))
        sys.exit(0)


if __name__ == "__main__":
    main()
