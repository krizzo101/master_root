#!/usr/bin/env python3
import asyncio
import json
import os
import re
import select
import sys
import textwrap
from datetime import datetime, timezone

# Use shared central AI interface instead of direct OpenAI
# Replaced direct OpenAI usage with shared central AI interface (automated migration)
sys.path.insert(0, "/home/opsvi/master_root/libs/opsvi-llm")
from opsvi_llm.providers.openai_provider import (  # noqa: E402
    OpenAIConfig,
    OpenAIProvider,
)
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

MODEL = os.getenv("PROMPT_OPT_MODEL", "gpt-5-mini")
MAX_TOK = int(os.getenv("PROMPT_OPT_MAX_TOK", "4000"))
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
CURRENT_DATE = datetime.now(timezone.utc).date().isoformat()


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


# Define schema for structured output
class OptimizedPromptSchema(BaseModel):
    """Schema for structured prompt optimization output."""

    optimized_prompt: str = Field(description="The optimized prompt")
    research_required: bool = Field(
        default=False, description="Whether research is required"
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
    if isinstance(resp, OptimizedPromptSchema):
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


def load_config():
    """Load configuration from prompt_opt_config.json"""
    config_path = "/home/opsvi/master_root/.claude/hooks/prompt_opt_config.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except:
        # Default config if file doesn't exist
        return {
            "mode": "opt-out",
            "opt_in_triggers": ["!!", "!opt", "!optimize"],
            "opt_out_triggers": ["!skip", "!noopt", "!pass"],
            "bypass_triggers": ["!raw", "!exact", "!verbatim"],
        }


def should_optimize(prompt: str, config: dict) -> tuple:
    """
    Determine if prompt should be optimized based on config and triggers.
    Returns: (should_optimize, cleaned_prompt, is_bypass)
    """
    prompt_lower = prompt.lower().strip()

    # Check for bypass triggers (raw content, no optimization)
    for trigger in config.get("bypass_triggers", []):
        if prompt_lower.startswith(trigger + " "):
            cleaned = (
                prompt.split(" ", 1)[1] if " " in prompt else prompt[len(trigger) :]
            )
            return False, cleaned, True

    mode = config.get("mode", "opt-out")

    if mode == "disabled":
        return False, prompt, False

    elif mode == "opt-in":
        # Only optimize if explicitly requested
        for trigger in config.get("opt_in_triggers", []):
            if prompt_lower.startswith(trigger + " "):
                cleaned = (
                    prompt.split(" ", 1)[1] if " " in prompt else prompt[len(trigger) :]
                )
                return True, cleaned, False
            elif prompt_lower.startswith(trigger) and len(prompt) == len(trigger):
                # Handle "!!" alone case
                return True, "", False
        return False, prompt, False

    elif mode == "opt-out":
        # Optimize unless explicitly skipped
        for trigger in config.get("opt_out_triggers", []):
            if prompt_lower.startswith(trigger + " "):
                cleaned = (
                    prompt.split(" ", 1)[1] if " " in prompt else prompt[len(trigger) :]
                )
                return False, cleaned, False
        return True, prompt, False

    else:  # mode == "always"
        return True, prompt, False


def main():
    # Check if stdin has data available (with 2 second timeout)
    if sys.stdin.isatty():
        # Terminal is attached but no pipe
        print(
            json.dumps(
                {
                    "error": 'No input provided. Usage: echo \'{"prompt": "...", "transcript_path": "..."}\' | python3 prompt_opt.py',
                    "suppressOutput": False,
                }
            )
        )
        sys.exit(1)

    # Check if stdin has data within 5 seconds (hooks sometimes deliver late)
    readable, _, _ = select.select([sys.stdin], [], [], 5.0)
    if not readable:
        print(
            json.dumps(
                {"error": "No input received within 2 seconds", "suppressOutput": False}
            )
        )
        sys.exit(1)

    try:
        inp = json.load(sys.stdin)
        user_prompt = inp.get("prompt", "")

        # Load configuration
        config = load_config()

        # Check if we should optimize
        should_opt, cleaned_prompt, is_bypass = should_optimize(user_prompt, config)

        if is_bypass:
            # Bypass mode - send raw content
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": f"[USER EXACT INSTRUCTIONS - NO OPTIMIZATION]\\n{cleaned_prompt}\\n[END EXACT INSTRUCTIONS]",
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        if not should_opt:
            # Pass through without optimization
            if os.getenv("DEBUG"):
                print(
                    f"DEBUG: Skipping optimization (mode={config.get('mode')})",
                    file=sys.stderr,
                )
            print(json.dumps({"suppressOutput": False}))
            sys.exit(0)

        # Use cleaned prompt for optimization
        user_prompt = cleaned_prompt

        # Extract RAW sections
        import re

        raw_pattern = r"\[RAW\](.*?)\[/RAW\]"
        raw_sections = []
        processable_prompt = user_prompt

        for match in re.finditer(raw_pattern, user_prompt, re.DOTALL | re.IGNORECASE):
            raw_sections.append(match.group(1))
            processable_prompt = processable_prompt.replace(match.group(0), " ")

        processable_prompt = processable_prompt.strip()
        has_raw = bool(raw_sections)

        transcript = inp.get("transcript_path", "")
        prev5 = last_user_prompts(transcript, 5)
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(
                f"DEBUG: prompt_opt.py:main() -- user_prompt='{user_prompt[:50]}...'",
                file=sys.stderr,
            )

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

        # Schema now defined as Pydantic model (OptimizedPromptSchema)

        user = textwrap.dedent(
            f"""
        Context (last 5 user prompts):
        {chr(10).join(f"- {p}" for p in prev5)}

        Knowledge cutoff: {KNOWLEDGE_CUTOFF}
        Current date (UTC): {CURRENT_DATE}
        Heuristic unstable topics: {', '.join(UNSTABLE_TOPICS)}

        Current prompt to optimize:
        {processable_prompt if has_raw else user_prompt}
        """
        ).strip()

        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(
                f"DEBUG: prompt_opt.py:main() -- calling model={MODEL} with max_tokens={MAX_TOK}",
                file=sys.stderr,
            )

        # Replaced direct OpenAI usage with shared central AI interface
        # Provider will automatically use correct parameters based on model
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
                max_tokens=MAX_TOK,  # Will be translated to max_output_tokens
                temperature=TEMP,
                # Note: seed parameter may not be supported by all models
            )
        )

        # Response is now a structured object (OptimizedPromptSchema)
        if isinstance(resp, OptimizedPromptSchema):
            optimized = resp.optimized_prompt.strip()
            research_flag = bool(resp.research_required)
        else:
            # Fallback for unexpected response format
            text = get_output_text(resp)
            try:
                data = json.loads(text)
                optimized = data.get("optimized_prompt", "").strip()
                research_flag = bool(data.get("research_required", False))
            except Exception:
                optimized = text.strip()
                research_flag = False

        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(
                f"DEBUG: prompt_opt.py:main() -- optimized={bool(optimized)}, research_flag={research_flag}",
                file=sys.stderr,
            )

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

        # Add RAW sections back if they exist
        if has_raw:
            raw_content = "\n\n".join(raw_sections)
            optimized = f"{optimized}\\n\\n[USER EXACT INSTRUCTIONS - PRESERVE AS-IS]\\n{raw_content}\\n[END EXACT INSTRUCTIONS]"

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
    except Exception as e:
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(f"DEBUG: prompt_opt.py:main() -- exception={e}", file=sys.stderr)
        # Degrade gracefully: no injection, do not block prompt processing
        print(json.dumps({"suppressOutput": False}))
        sys.exit(0)


if __name__ == "__main__":
    main()
