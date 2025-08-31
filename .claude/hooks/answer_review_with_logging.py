#!/usr/bin/env python3
import asyncio
import json
import os
import pathlib
import re
import sys
import time
import traceback
from typing import Dict, List, Optional, Tuple

# Import logging utilities
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from review_logging import get_loggers, log_with_context

# Use shared central AI interface instead of direct OpenAI
sys.path.insert(0, "/home/opsvi/master_root/libs/opsvi-llm")

from opsvi_llm.providers.openai_provider import (  # noqa: E402
    OpenAIConfig,
    OpenAIProvider,
)
from pydantic import BaseModel, Field  # noqa: E402

# Initialize loggers
logger, audit_logger, perf_logger = get_loggers()

# Initialize provider with timeout support
config = OpenAIConfig(
    provider_name="openai",
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=float(os.getenv("OPENAI_TIMEOUT_SEC", "25.0")),
    enable_audit_logging=os.getenv("ENABLE_API_AUDIT", "false").lower() == "true",
    enable_sanitization=False,
)
provider = OpenAIProvider(config)

# Configuration
MODEL_PRIMARY = os.getenv("REVIEW_MODEL", "gpt-5-nano")
MODEL_ESCALATE = os.getenv("REVIEW_MODEL_ESCALATE", "gpt-5-mini")
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
    "latest", "breaking", "today", "as of", "price", "cost", "fee",
    "exchange rate", "version", "api", "sdk", "library", "release",
    "changelog", "cve", "law", "regulation", "compliance", "policy",
    "election", "medical", "drug", "dosage", "availability", "schedule",
    "deadline", "admission", "calendar", "travel", "weather", "market",
    "stock", "crypto", "ceo", "cfo", "leadership", "org change",
]
UNSTABLE_TOPICS = [
    s.strip() for s in os.getenv("RESEARCH_UNSTABLE_TOPICS", "").split(",") if s.strip()
] or DEFAULT_UNSTABLE


class ReviewVerdictSchema(BaseModel):
    """Schema for review verdict output."""
    passed: bool = Field(description="Whether the review passed")
    guidance: str = Field(
        description="Specific, actionable fixes if failed; otherwise 'OK'."
    )

    class Config:
        extra = "forbid"

    @classmethod
    def model_json_schema(cls, **kwargs):
        """Override to ensure all fields are required for OpenAI strict mode."""
        schema = super().model_json_schema(**kwargs)
        if "properties" in schema:
            schema["required"] = list(schema["properties"].keys())
        return schema


def read_last_items(transcript_path: str, k_user: int = 5) -> Tuple[str, List[str]]:
    """Read the last assistant response and k user prompts from transcript."""
    users, assistant = [], ""
    
    log_with_context(logger, "debug", "Reading transcript", 
                    transcript_path=transcript_path, k_user=k_user)
    
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
                
        log_with_context(logger, "info", "Transcript parsed successfully",
                        assistant_length=len(assistant),
                        user_prompts_found=len(users))
                        
    except Exception as e:
        log_with_context(logger, "error", f"Failed to read transcript: {e}",
                        error_type=type(e).__name__)
        
    return assistant, list(reversed(users))[:k_user]


def get_output_text(resp):
    """Extract text from Responses API response or structured output."""
    if isinstance(resp, ReviewVerdictSchema):
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


def call_review(model: str, assistant_out: str, prev5: List[str], 
                session_id: str, attempt_num: int) -> Dict:
    """Call the review model and return verdict."""
    
    log_with_context(logger, "info", f"Starting review with {model}",
                    session_id=session_id,
                    model=model,
                    attempt_num=attempt_num,
                    assistant_out_length=len(assistant_out),
                    prev_prompts_count=len(prev5))
    
    # Start performance timing
    perf_logger.start_timer("model_review", session_id)
    
    system = (
        "You are a strict reviewer for a dev agent's answer. Check for: factual errors, internal contradictions, "
        "unsafe/destructive commands, missing acceptance tests, and mismatches with the prompt/context. "
        "Return a verdict and concrete guidance to fix failures."
    )
    
    user = (
        "Previous 5 user prompts:\n"
        + "\n".join(f"- {p}" for p in prev5)
        + "\n\nAnswer to review:\n"
        + assistant_out
    )
    
    start_time = time.time()
    
    try:
        r = asyncio.run(
            provider.responses_create_with_structured_output(
                input=[
                    {"role": "system", "content": [{"type": "input_text", "text": system}]},
                    {"role": "user", "content": [{"type": "input_text", "text": user}]},
                ],
                response_model=ReviewVerdictSchema,
                model=model,
                max_tokens=MAX_TOK,
                temperature=TEMP,
            )
        )
        
        api_duration = time.time() - start_time
        
        # End performance timing
        duration_ms = perf_logger.end_timer("model_review", session_id, {
            "model": model,
            "attempt": attempt_num,
            "api_duration_s": round(api_duration, 2)
        })
        
        if isinstance(r, ReviewVerdictSchema):
            verdict = {"passed": r.passed, "guidance": r.guidance}
            
            log_with_context(logger, "info", "Review completed",
                            session_id=session_id,
                            model=model,
                            passed=r.passed,
                            duration_ms=duration_ms,
                            guidance_length=len(r.guidance))
            
            # Log to audit trail
            audit_logger.log_review(session_id, {
                "model": model,
                "attempt_num": attempt_num,
                "verdict": verdict,
                "assistant_response": assistant_out,
                "user_prompts": prev5,
                "duration_ms": duration_ms,
                "api_duration_s": round(api_duration, 2)
            })
            
            return verdict
        else:
            # Fallback for unexpected response format
            out = get_output_text(r)
            log_with_context(logger, "warning", "Non-structured response received",
                            session_id=session_id,
                            response_type=type(r).__name__)
            try:
                verdict = json.loads(out)
            except Exception:
                verdict = {"passed": False, "guidance": out}
                
            return verdict
            
    except Exception as e:
        log_with_context(logger, "error", f"Review call failed: {e}",
                        session_id=session_id,
                        model=model,
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc())
        
        # End timer even on error
        perf_logger.end_timer("model_review", session_id, {
            "model": model,
            "attempt": attempt_num,
            "error": str(e)
        })
        
        # Return a failure verdict on error
        return {"passed": False, "guidance": f"Review error: {str(e)}"}


def attempts_file(session_id: str, scope: str = "global") -> pathlib.Path:
    """Get the path to the attempts tracking file."""
    return STATE_DIR.joinpath(f"{session_id}.{scope}.review.json")


def get_attempts(session_id: str, scope: str) -> int:
    """Get the number of review attempts for a session."""
    p = attempts_file(session_id, scope)
    if p.exists():
        try:
            return json.loads(p.read_text()).get("attempts", 0)
        except Exception as e:
            log_with_context(logger, "warning", f"Failed to read attempts file: {e}",
                            session_id=session_id, scope=scope)
            return 0
    return 0


def set_attempts(session_id: str, scope: str, n: int):
    """Set the number of review attempts for a session."""
    try:
        attempts_file(session_id, scope).write_text(json.dumps({"attempts": n}))
        log_with_context(logger, "debug", f"Set attempts to {n}",
                        session_id=session_id, scope=scope)
    except Exception as e:
        log_with_context(logger, "error", f"Failed to write attempts file: {e}",
                        session_id=session_id, scope=scope)


def likely_time_sensitive(text: str) -> bool:
    """Check if text likely contains time-sensitive information."""
    t = (text or "").lower()
    is_sensitive = any(tok in t for tok in UNSTABLE_TOPICS)
    
    if not is_sensitive:
        is_sensitive = bool(re.search(r"\b(as of|updated|version|release|changelog|cve)\b", t))
    
    if is_sensitive:
        log_with_context(logger, "info", "Time-sensitive content detected",
                        sample=text[:100] if text else "")
    
    return is_sensitive


def has_sources(text: str) -> bool:
    """Check if text contains source citations."""
    t = (text or "").lower()
    has_src = any(
        k in t
        for k in ["sources:", "citations:", "references:", "no recent changes found"]
    )
    
    if has_src:
        log_with_context(logger, "debug", "Sources found in response")
    
    return has_src


def main():
    """Main entry point for the answer review hook."""
    start_time = time.time()
    session_id = "unknown"
    
    try:
        # Parse input
        inp = json.load(sys.stdin)
        session_id = inp.get("session_id", "unknown")
        transcript = inp.get("transcript_path", "")
        stop_hook_active = bool(inp.get("stop_hook_active", False))
        scope = (inp.get("tool_name") or "final").lower()
        
        log_with_context(logger, "info", "Review hook started",
                        session_id=session_id,
                        stop_hook_active=stop_hook_active,
                        scope=scope)
        
        # Start overall timing
        perf_logger.start_timer("review_total", session_id)
        
        # Read transcript
        assistant_out, prev5_user = read_last_items(transcript)
        
        # If nothing to review, allow stop quietly
        if not (assistant_out and assistant_out.strip()):
            log_with_context(logger, "info", "No content to review, passing through",
                            session_id=session_id)
            print(json.dumps({"suppressOutput": False}))
            sys.exit(0)
        
        # Research enforcement check
        if (
            RESEARCH_ENABLE
            and likely_time_sensitive(" ".join(prev5_user + [assistant_out]))
            and not has_sources(assistant_out)
        ):
            attempts = get_attempts(session_id, scope)
            if attempts < MAX_ATTEMPTS and not stop_hook_active:
                set_attempts(session_id, scope, attempts + 1)
                
                reason = (
                    "Research required: The topic appears time-sensitive relative to the knowledge cutoff "
                    f"({KNOWLEDGE_CUTOFF}). Before finalizing, perform a brief KB/docs (and web if available) check, "
                    "summarize any updates since the cutoff, and include Sources:/Citations: or a 'no recent changes found' note. "
                    f"(attempt {attempts+1}/{MAX_ATTEMPTS})"
                )
                
                log_with_context(logger, "info", "Blocking for research requirement",
                                session_id=session_id,
                                attempts=attempts + 1,
                                max_attempts=MAX_ATTEMPTS)
                
                # Audit log the research block
                audit_logger.log_review(session_id, {
                    "action": "research_block",
                    "attempts": attempts + 1,
                    "max_attempts": MAX_ATTEMPTS,
                    "reason": "time_sensitive_no_sources"
                })
                
                print(json.dumps({"decision": "block", "reason": reason}))
                sys.exit(0)
        
        # Regular review pass/fail
        attempts = get_attempts(session_id, scope)
        verdict = call_review(MODEL_PRIMARY, assistant_out, prev5_user, 
                            session_id, attempts + 1)
        
        # Optional escalation
        if not verdict.get("passed", False) and attempts == 1 and MODEL_ESCALATE:
            log_with_context(logger, "info", "Escalating to secondary model",
                            session_id=session_id,
                            primary_model=MODEL_PRIMARY,
                            escalate_model=MODEL_ESCALATE)
            
            verdict = call_review(MODEL_ESCALATE, assistant_out, prev5_user,
                                session_id, attempts + 1)
        
        # Decision logic
        if verdict.get("passed", False) or attempts >= MAX_ATTEMPTS or stop_hook_active:
            set_attempts(session_id, scope, 0)
            
            action = "pass" if verdict.get("passed", False) else "max_attempts_reached"
            log_with_context(logger, "info", f"Review completed: {action}",
                            session_id=session_id,
                            attempts=attempts,
                            passed=verdict.get("passed", False))
            
            # End overall timing
            total_ms = perf_logger.end_timer("review_total", session_id, {
                "result": action,
                "attempts": attempts
            })
            
            print(json.dumps({"suppressOutput": False}))
            sys.exit(0)
        
        # Block and request revision
        set_attempts(session_id, scope, attempts + 1)
        
        reason = (
            f"Reviewer feedback (attempt {attempts+1}/{MAX_ATTEMPTS}):\n"
            f"{verdict.get('guidance','')}\n"
            f"Revise and return only the improved answer."
        )
        
        log_with_context(logger, "info", "Blocking for revision",
                        session_id=session_id,
                        attempts=attempts + 1,
                        max_attempts=MAX_ATTEMPTS,
                        guidance_length=len(verdict.get('guidance', '')))
        
        # End overall timing
        total_ms = perf_logger.end_timer("review_total", session_id, {
            "result": "block_for_revision",
            "attempts": attempts + 1
        })
        
        print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)
        
    except Exception as e:
        log_with_context(logger, "error", f"Review hook failed: {e}",
                        session_id=session_id,
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc(),
                        execution_time_ms=(time.time() - start_time) * 1000)
        
        # On reviewer failure, do NOT block delivery
        print(json.dumps({"suppressOutput": False}))
        sys.exit(0)


if __name__ == "__main__":
    main()