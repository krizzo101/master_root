#!/usr/bin/env python3
import json
import os
import pathlib
import re
import sys
from datetime import datetime

# OpenAI Responses API
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_PRIMARY = os.getenv("REVIEW_MODEL", "gpt-5-nano")
MODEL_ESCALATE = os.getenv(
    "REVIEW_MODEL_ESCALATE", "gpt-5-mini"
)  # optional one-time escalation
MAX_ATTEMPTS = int(os.getenv("REVIEW_MAX_ATTEMPTS", "3"))
MAX_TOK = int(os.getenv("REVIEW_MAX_TOK", "300"))
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


def get_output_text(resp):
    t = getattr(resp, "output_text", None)
    if t:
        return t
    try:
        d = resp.model_dump() if hasattr(resp, "model_dump") else resp.__dict__
        out = d.get("output") or d.get("outputs") or []
        if out and isinstance(out, list):
            c = out[0].get("content") if isinstance(out[0], dict) else None
            if c and isinstance(c, list):
                txt = c[0].get("text")
                if txt:
                    return txt
    except Exception:
        pass
    return ""


def call_review(model, assistant_out, prev5):
    system = (
        "You are a strict reviewer for a dev agent's answer. Check for: factual errors, internal contradictions, "
        "unsafe/destructive commands, missing acceptance tests, and mismatches with the prompt/context. "
        "Return a verdict and concrete guidance to fix failures."
    )
    schema = {
        "name": "ReviewVerdict",
        "schema": {
            "type": "object",
            "properties": {
                "passed": {"type": "boolean"},
                "guidance": {
                    "type": "string",
                    "description": "Specific, actionable fixes if failed; otherwise 'OK'.",
                },
            },
            "required": ["passed", "guidance"],
            "additionalProperties": False,
        },
        "strict": True,
    }
    user = (
        "Previous 5 user prompts:\n"
        + "\n".join(f"- {p}" for p in prev5)
        + "\n\nAnswer to review:\n"
        + assistant_out
    )
    r = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": system}]},
            {"role": "user", "content": [{"type": "input_text", "text": user}]},
        ],
        response_format={"type": "json_schema", "json_schema": schema},
        temperature=TEMP,
        max_output_tokens=MAX_TOK,
        seed=SEED,
        verbosity="low",
    )
    out = get_output_text(r)
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

        # Optional one-time escalation to a larger model if first check fails
        if not verdict.get("passed", False) and attempts == 0 and MODEL_ESCALATE:
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
    except Exception:
        # On reviewer failure, do NOT block delivery
        print(json.dumps({"suppressOutput": True}))
        sys.exit(0)


if __name__ == "__main__":
    main()
