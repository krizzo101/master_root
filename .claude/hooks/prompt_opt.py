#!/usr/bin/env python3
import json
import os
import pathlib
import re
import sys
import textwrap
from datetime import datetime

# OpenAI Responses API
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = os.getenv("PROMPT_OPT_MODEL", "gpt-4o-mini")
MAX_TOK = int(os.getenv("PROMPT_OPT_MAX_TOK", "400"))
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
CURRENT_DATE = datetime.utcnow().date().isoformat()


def last_user_prompts(transcript_path, k=5):
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
    # Extract text from chat completions response
    try:
        # Standard chat completions response
        if hasattr(resp, "choices") and resp.choices:
            return resp.choices[0].message.content
        # Legacy Responses API format
        t = getattr(resp, "output_text", None)
        if t:
            return t
        # Fallback to dict walk
        d = resp.model_dump() if hasattr(resp, "model_dump") else resp.__dict__
        out = d.get("output") or d.get("outputs") or []
        # Common shape: output[0].content[0].text
        if out and isinstance(out, list):
            c = out[0].get("content") if isinstance(out[0], dict) else None
            if c and isinstance(c, list):
                txt = c[0].get("text")
                if txt:
                    return txt
    except Exception:
        pass
    return ""


def main():
    try:
        inp = json.load(sys.stdin)
        user_prompt = inp.get("prompt", "")
        transcript = inp.get("transcript_path", "")
        prev5 = last_user_prompts(transcript, 5)

        system = (
            "Rewrite the user's prompt into a concise, execution-ready instruction for a coding/dev agent (Claude Code). "
            "Preserve intent, remove ambiguity, specify concrete deliverables and acceptance tests, and encourage stepwise "
            "execution via Claude Code Tasks so each major step creates SubagentStop checkpoints. "
            "You are aware the model knowledge cutoff is {cutoff} and today's date is {today}. "
            "If the task appears time-sensitive or likely to be outdated relative to {cutoff}, prepend a clear "
            "'RESEARCH BEFORE ACTION' directive that instructs the agent to: (1) perform brief research using available "
            "KB/search tools (and web if enabled), (2) summarize findings, and (3) cite sources or note 'no recent changes found'. "
            "Output ONLY the optimized prompt text; no preface."
        ).format(cutoff=KNOWLEDGE_CUTOFF, today=CURRENT_DATE)

        schema = {
            "name": "OptimizedPrompt",
            "schema": {
                "type": "object",
                "properties": {
                    "optimized_prompt": {
                        "type": "string",
                        "description": "Final optimized prompt for the agent.",
                    },
                    "notes": {"type": "array", "items": {"type": "string"}},
                    "research_required": {
                        "type": "boolean",
                        "description": "True iff research should precede execution.",
                    },
                },
                "required": ["optimized_prompt"],
                "additionalProperties": False,
            },
            "strict": True,
        }

        user = textwrap.dedent(
            f"""
        Context (last 5 user prompts):
        {chr(10).join(f"- {p}" for p in prev5)}

        Knowledge cutoff: {KNOWLEDGE_CUTOFF}
        Current date (UTC): {CURRENT_DATE}
        Heuristic unstable topics: {', '.join(UNSTABLE_TOPICS)}

        Current prompt to optimize:
        {user_prompt}
        """
        ).strip()

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_schema", "json_schema": schema},
            temperature=TEMP,
            max_completion_tokens=MAX_TOK,
            seed=SEED,
        )

        text = get_output_text(resp)
        try:
            data = json.loads(text)
            optimized = data.get("optimized_prompt", "").strip()
            research_flag = bool(data.get("research_required", False))
        except Exception:
            optimized = text.strip()
            research_flag = False

        def needs_research_heuristic(p: str) -> bool:
            p_lower = (p or "").lower()
            if any(tok in p_lower for tok in UNSTABLE_TOPICS):
                return True
            # crude date mentions imply volatility
            return bool(
                re.search(r"\b(as of|updated|version|release|changelog|cve)\b", p_lower)
            )

        research_needed = RESEARCH_ENABLE and (
            research_flag or needs_research_heuristic(user_prompt)
        )

        if research_needed:
            preface = (
                "RESEARCH BEFORE ACTION:\n"
                "- Run a brief KB/docs search and, if available, a web check for the latest.\n"
                f"- Summarize what changed since {KNOWLEDGE_CUTOFF} or confirm no material changes.\n"
                "- Include sources/citations or a 'no recent changes found' note.\n"
            )
            optimized = f"{preface}\n{optimized}".strip()

        injected = f"[PROMPT_OPTIMIZER]\\n{optimized}\\n[END_PROMPT_OPTIMIZER]"

        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": injected,
                    }
                }
            )
        )
        sys.exit(0)
    except Exception:
        # Degrade gracefully: no injection, do not block prompt processing
        print(json.dumps({"suppressOutput": True}))
        sys.exit(0)


if __name__ == "__main__":
    main()
