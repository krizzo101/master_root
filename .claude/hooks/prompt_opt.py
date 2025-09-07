#!/usr/bin/env python3
import asyncio
import hashlib
import json
import os
import random
import re
import select
import sys
import textwrap
from datetime import datetime, timezone

# Import logger for tracking
try:
    from prompt_opt_logger import PromptOptLogger

    logger = PromptOptLogger()
except Exception:
    logger = None  # Fail silently if logger not available

# Lazy loading - only import when needed
_provider = None

MODEL = os.getenv(
    "PROMPT_OPT_MODEL", "gpt-5-nano"
)  # Fast model for prompt optimization
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


def get_cognitive_guidance(prompt_text):
    """Generate context-aware cognitive guidance with variation."""
    prompt_lower = prompt_text.lower()

    # Context-aware base guidance
    if any(word in prompt_lower for word in ["fix", "bug", "error", "issue", "broken"]):
        base_guidance = [
            "Reproduce issue → Use TodoWrite for tracking → Root cause analysis → Fix → Verify",
            "First reproduce the bug. Plan fix steps with TodoWrite. Implement systematically. Test thoroughly.",
            "Debug workflow: Reproduce, TodoWrite for steps, analyze cause, apply fix, validate solution",
        ]
    elif any(
        word in prompt_lower
        for word in ["implement", "add", "feature", "create", "build"]
    ):
        base_guidance = [
            "Architecture planning (TodoWrite) → Research patterns → Build incrementally → Test features",
            "Design first with TodoWrite. Study existing patterns. Implement step-by-step. Verify functionality.",
            "Feature flow: Plan structure, research similar code, implement progressively, validate behavior",
        ]
    elif any(
        word in prompt_lower
        for word in ["refactor", "reorganize", "restructure", "clean"]
    ):
        base_guidance = [
            "Map current state → TodoWrite refactor plan → Preserve behavior → Verify with tests",
            "Understand existing code. Plan changes in TodoWrite. Refactor safely. Confirm behavior unchanged.",
            "Refactor protocol: Analyze structure, list changes needed, transform carefully, test thoroughly",
        ]
    elif any(
        word in prompt_lower
        for word in ["research", "find", "search", "analyze", "investigate"]
    ):
        base_guidance = [
            "Broad search → Document findings → Narrow focus → Synthesize results",
            "Cast wide net first. Track discoveries. Focus on relevant. Summarize insights.",
            "Research method: Explore widely, record findings, refine search, compile conclusions",
        ]
    elif any(word in prompt_lower for word in ["test", "verify", "validate", "check"]):
        base_guidance = [
            "Identify test scenarios → TodoWrite test plan → Execute tests → Document results",
            "Plan test coverage with TodoWrite. Write test cases. Run systematically. Report outcomes.",
            "Testing approach: Define scenarios, organize with todos, execute thoroughly, verify coverage",
        ]
    else:
        # Generic guidance with variety
        base_guidance = [
            "Think → Plan with TodoWrite → Execute → Verify",
            "Understand requirements. Create task breakdown. Work systematically. Validate results.",
            "Start with todos, research context, implement carefully, confirm success",
            "Blueprint first (TodoWrite), investigate needs, build methodically, quality check",
        ]

    # Select guidance variant based on prompt hash for consistency
    prompt_hash = int(hashlib.md5(prompt_text.encode()).hexdigest()[:8], 16)
    selected_base = base_guidance[prompt_hash % len(base_guidance)]

    # Add emphasis patterns for variety
    emphasis_patterns = [
        ("📋 ", ""),  # Emoji prefix
        ("**Important**: ", ""),  # Bold emphasis
        ("", " ✓"),  # Checkmark suffix
        ("→ ", ""),  # Arrow prefix
        ("Note: ", "."),  # Note format
        ("", " — this leads to better results."),  # Explanatory suffix
        ("💡 ", ""),  # Lightbulb
        ("", " (proven approach)"),  # Parenthetical
        ("Best practice: ", ""),  # Best practice prefix
        ("", " for optimal quality"),  # Quality suffix
    ]

    # Use different emphasis based on another part of the hash
    emphasis_index = (prompt_hash >> 8) % len(emphasis_patterns)
    prefix, suffix = emphasis_patterns[emphasis_index]

    return f"{prefix}{selected_base}{suffix}"


def get_provider():
    """Lazy load OpenAI client to reduce startup time."""
    global _provider
    if _provider is None:
        from openai import OpenAI

        _provider = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _provider


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
            "opt_in_triggers": ["++", "+opt", "+optimize", "opt:", "optimize:"],
            "opt_out_triggers": ["--skip", "--noopt", "--pass", "skip:", "noopt:"],
            "bypass_triggers": ["--raw", "--exact", "--verbatim", "raw:", "exact:"],
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
                # Handle "++" or "opt:" alone case
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
            if logger:
                logger.log_skip("bypass_mode", cleaned_prompt)
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": f"[USER EXACT INSTRUCTIONS - NO OPTIMIZATION]\\n{cleaned_prompt}\\n[END EXACT INSTRUCTIONS]",
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        if not should_opt:
            # Pass through without optimization but still add token conservation guidance
            if logger:
                logger.log_skip(f"mode_{config.get('mode')}_no_trigger", user_prompt)
            if os.getenv("DEBUG"):
                print(
                    f"DEBUG: Skipping optimization (mode={config.get('mode')})",
                    file=sys.stderr,
                )

            # Add token conservation guidance regardless of optimization
            token_guidance = "CRITICAL: Conserve tokens when responding - wasting tokens costs money and reduces available context space, forcing early session compaction or restarts. Use minimal words for maximum effect."
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": f"[TOKEN CONSERVATION GUIDANCE]\n{token_guidance}\n\n[USER PROMPT]\n{user_prompt}",
                }
            }
            print(json.dumps(output))
            sys.exit(0)

        # Store original prompt for logging
        original_prompt = user_prompt
        # Use cleaned prompt for optimization
        user_prompt = cleaned_prompt

        # Extract RAW sections
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
            "CRITICAL: Add guidance that the agent must conserve tokens when responding - wasting tokens costs money and "
            "reduces available context space, forcing early session compaction or restarts. Use minimal words for maximum effect. "
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

        # Use direct OpenAI call with lazy loading
        client = get_provider()

        # Use correct parameter name based on model
        if MODEL.startswith(("gpt-5", "o3", "o4")):
            max_tokens_param = "max_completion_tokens"
        else:
            max_tokens_param = "max_tokens"

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **{max_tokens_param: MAX_TOK},
            temperature=TEMP,
            response_format={"type": "json_object"},
        )

        # Parse response
        try:
            data = json.loads(resp.choices[0].message.content)
            optimized = data.get("optimized_prompt", "").strip()
            research_flag = bool(data.get("research_required", False))
        except Exception:
            optimized = resp.choices[0].message.content.strip()
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

        # Add cognitive guidance based on the cleaned prompt (without trigger)
        cognitive_guidance = get_cognitive_guidance(user_prompt)

        # Add RAW sections back if they exist
        if has_raw:
            raw_content = "\n\n".join(raw_sections)
            optimized = f"{optimized}\n\n[USER EXACT INSTRUCTIONS - PRESERVE AS-IS]\n{raw_content}\n[END EXACT INSTRUCTIONS]"

        # Combine cognitive guidance with optimized prompt
        injected = f"[COGNITIVE APPROACH]\n{cognitive_guidance}\n\n[OPTIMIZED TASK]\n{optimized}\n[END_PROMPT_OPTIMIZER]"

        # Log the successful optimization
        if logger:
            trigger = None
            for t in config.get("opt_in_triggers", []):
                if user_prompt.lower().startswith(t):
                    trigger = t
                    break
            logger.log_optimization(
                original=original_prompt,  # Use the original prompt before cleaning
                optimized=optimized,
                mode=config.get("mode", "unknown"),
                triggered_by=trigger,
                cognitive=cognitive_guidance,
            )

        # Show user how their prompt was modified
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": injected,
                        "userVisible": f"🔧 **Prompt Optimized**\n\n**Original:** {original_prompt[:100]}{'...' if len(original_prompt) > 100 else ''}\n\n**Optimized:** {optimized[:200]}{'...' if len(optimized) > 200 else ''}",
                    }
                }
            )
        )
        sys.exit(0)
    except Exception as e:
        if logger:
            logger.log_error(e, {"prompt": user_prompt[:100] if user_prompt else None})
        # TODO: temporary print-based debug — replace with proper logger before merge/release
        if os.getenv("DEBUG"):
            print(f"DEBUG: prompt_opt.py:main() -- exception={e}", file=sys.stderr)
        # Degrade gracefully: add token conservation guidance even on error
        token_guidance = "CRITICAL: Conserve tokens when responding - wasting tokens costs money and reduces available context space, forcing early session compaction or restarts. Use minimal words for maximum effect."
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": f"[TOKEN CONSERVATION GUIDANCE]\n{token_guidance}\n\n[USER PROMPT]\n{user_prompt}",
            }
        }
        print(json.dumps(output))
        sys.exit(0)


if __name__ == "__main__":
    main()
