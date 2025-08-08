#!/usr/bin/env python3
"""
ai_populate.py — AI-assisted file population for OPSVI libs.

- Scans for generated libraries and identifies stub/TODO files
- Dry-run prints a plan; write mode can append or replace content
- Real AI integration via OpenAI Responses API with approved models only

Usage:
  python tools/ai_populate.py --libs-dir libs --dry-run
  python tools/ai_populate.py --libs-dir libs --only opsvi-core --write --mode append

Env:
  OPENAI_API_KEY (required for AI mode)
  OPENAI_BASE_URL (optional; default https://api.openai.com/v1)
  OPENAI_MODEL (optional; default gpt-5-mini; approved: o3, o4-mini, gpt-5, gpt-5-mini, gpt-5-nano)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Iterable, Optional
from datetime import datetime, timezone
import time

STUB_MARKER = "AUTO-GENERATED STUB"
TODO_MARKER = "# TODO(ai):"
APPROVED_MODELS = {"o3", "o4-mini", "gpt-5", "gpt-5-mini", "gpt-5-nano"}

# Global log file path (set via --log-file). When set, all prints are also written to this file.
LOG_FILE_PATH: Optional[str] = None


class _TeeWriter:
    def __init__(self, file_path: str, stream) -> None:
        self._stream = stream
        self._file = open(file_path, "a", encoding="utf-8")

    def write(self, data: str) -> int:
        w1 = self._stream.write(data)
        self._stream.flush()
        self._file.write(data)
        self._file.flush()
        return w1

    def flush(self) -> None:  # noqa: D401
        self._stream.flush()
        self._file.flush()

    def isatty(self) -> bool:
        return False


def get_timeout_seconds() -> int:
    try:
        return int(os.environ.get("OPENAI_TIMEOUT", "60"))
    except Exception:
        return 60


def iter_library_packages(libs_dir: Path) -> Iterable[tuple[str, Path, Path]]:
    for lib_dir in sorted(p for p in libs_dir.iterdir() if p.is_dir()):
        pkg_name = lib_dir.name.replace("-", "_")
        pkg_dir = lib_dir / pkg_name
        if pkg_dir.exists():
            yield (lib_dir.name, lib_dir, pkg_dir)


def find_targets(lib_dir: Path) -> list[Path]:
    targets: list[Path] = []
    for path in lib_dir.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if STUB_MARKER in text or TODO_MARKER in text:
            targets.append(path)
    return targets


def write_placeholder(path: Path) -> None:
    header = "\n# TODO(ai): Populate implementation using contexts and templates.\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(header)


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.environ.get(name)
    return val if val else default


def is_ai_enabled() -> bool:
    return bool(get_env_var("OPENAI_API_KEY"))


def select_model() -> str:
    model = get_env_var("OPENAI_MODEL", "gpt-5-mini") or "gpt-5-mini"
    if model not in APPROVED_MODELS:
        print(f"Warning: Model '{model}' not approved; falling back to gpt-5-mini")
        model = "gpt-5-mini"
    return model


def ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _choose_model_for_content(content: str) -> str:
    """Heuristic: use gpt-5 for larger files, else gpt-5-mini."""
    try:
        default_model = select_model()
        # Rough char threshold where we prefer larger model capacity
        return "gpt-5" if len(content) > 3000 else default_model
    except Exception:
        return "gpt-5-mini"


def _estimate_output_tokens(basis: str) -> int:
    # Rough heuristic: ~3 chars per token; add headroom; clamp to sane bounds
    approx = max(1200, (len(basis) // 3) + 800)
    return min(8000, approx)


def _call_responses_with_schema(prompt: str, *, model: str, base_url: Optional[str], content_hint: str = "") -> Optional[dict]:
    """Version-tolerant Responses call. Returns dict with keys 'code' and optional 'reasoning'."""
    try:
        from openai import OpenAI  # type: ignore
        try:
            from openai import APIError, RateLimitError, APITimeoutError  # type: ignore
        except Exception:  # noqa: BLE001
            APIError = Exception  # type: ignore[assignment]
            RateLimitError = Exception  # type: ignore[assignment]
            APITimeoutError = Exception  # type: ignore[assignment]
    except Exception as e:  # noqa: BLE001
        print(f"[{ts()}] OpenAI SDK import failed: {e}")
        return None

    client_kwargs = {}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(timeout=get_timeout_seconds(), **client_kwargs)

    schema: dict = {
        "name": "ai_populate_response",
        "schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "reasoning": {"type": "string"},
            },
            "required": ["code"],
            "additionalProperties": False,
        },
    }

    max_tokens = _estimate_output_tokens(content_hint or prompt)
    base_kwargs: dict = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_tokens,
        "temperature": 0,
    }
    with_schema_kwargs = {
        **base_kwargs,
        "response": {
            "modalities": ["text"],
            "text": {
                "format": {
                    "type": "json_schema",
                    "json_schema": schema,
                }
            },
        },
    }

    last_err: Optional[Exception] = None
    for attempt in range(1, 4):
        for use_schema in (True, False):
            kwargs = with_schema_kwargs if use_schema else base_kwargs
            try:
                print(f"[{ts()}] OpenAI/Responses: create model={model} attempt={attempt} schema={use_schema} max_tokens={max_tokens}")
                resp = client.responses.create(**kwargs)
                parsed = getattr(resp, "output_parsed", None)
                if isinstance(parsed, dict) and isinstance(parsed.get("code"), str) and parsed["code"].strip():
                    return {"code": parsed.get("code"), "reasoning": parsed.get("reasoning", "")}
                text = getattr(resp, "output_text", "") or ""
                if isinstance(text, str) and text.strip():
                    # Expect JSON per schema; fail if not parseable or missing code
                    try:
                        obj = json.loads(text)
                        if isinstance(obj, dict) and isinstance(obj.get("code"), str) and obj["code"].strip():
                            return {"code": obj.get("code"), "reasoning": obj.get("reasoning", "")}
                        last_err = RuntimeError("Structured output missing 'code'")
                        continue
                    except Exception as e:
                        last_err = RuntimeError(f"Non-JSON output under structured mode: {e}")
                        continue
                try:
                    data = resp.model_dump()
                except Exception:
                    data = {}
                outputs = (data.get("output") or data.get("outputs") or [])
                for item in outputs:
                    if item.get("type") == "message":
                        for c in item.get("content") or []:
                            if c.get("type") in ("output_text", "text", "input_text"):
                                val = c.get("text")
                                if isinstance(val, dict):
                                    val = val.get("value") or val.get("text")
                                if isinstance(val, str) and val.strip():
                                    # Attempt JSON parse; otherwise fail
                                    try:
                                        obj = json.loads(val)
                                        if isinstance(obj, dict) and isinstance(obj.get("code"), str) and obj["code"].strip():
                                            return {"code": obj.get("code"), "reasoning": obj.get("reasoning", "")}
                                    except Exception:
                                        pass
                                    last_err = RuntimeError("Unstructured fallback content without JSON 'code'")
                                    continue
                last_err = RuntimeError("Empty response content")
            except (RateLimitError, APITimeoutError) as e:  # type: ignore[name-defined]
                print(f"[{ts()}] OpenAI/Responses retryable error: {e}")
                last_err = e
            except APIError as e:  # type: ignore[name-defined]
                status = getattr(e, "status_code", 500)
                print(f"[{ts()}] OpenAI/Responses API error: status={status} {e}")
                last_err = e
                if status < 500:
                    return None
            except TypeError as e:
                last_err = e
                if use_schema:
                    print(f"[{ts()}] OpenAI/Responses TypeError: {e}; retrying without structured response payload")
                    continue
                print(f"[{ts()}] OpenAI/Responses TypeError without schema: {e}")
                return None
            except Exception as e:  # noqa: BLE001
                print(f"[{ts()}] OpenAI/Responses exception: {e}")
                last_err = e
        if attempt < 3:
            time.sleep(1.5 * attempt)
    return None


def call_openai_responses(prompt: str, *, content_hint: str = "") -> Optional[dict]:
    """Call OpenAI Responses API using a version-tolerant helper.

    Returns {'code': str, 'reasoning': str} or None.
    """
    if not is_ai_enabled():
        print(f"[{ts()}] OpenAI/Responses: missing OPENAI_API_KEY")
        return None
    base_url = get_env_var("OPENAI_BASE_URL")
    model = _choose_model_for_content(content_hint)
    return _call_responses_with_schema(prompt, model=model, base_url=base_url, content_hint=content_hint)


# Removed chat fallback: GPT-5 is only served by Responses API


def build_prompt(file_path: Path, rel_path: str, lib_name: str, content: str) -> str:
    return (
        "You are an expert Python library developer. Generate high-quality, typed, "
        "readable code that replaces TODO/stub placeholders. Follow these rules: "
        "- Match the module purpose inferred from the path and current content. "
        "- Use asyncio where appropriate; include minimal docstrings; no secrets. "
        "- Keep code under ~200 lines if possible; no external network calls.\n\n"
        f"Library: {lib_name}\nFile: {rel_path}\n\n"
        "Current content:\n---BEGIN---\n" + content + "\n---END---\n\n"
        "Return a JSON object with fields {\"code\": string, \"reasoning\": string}. "
        "Place the full file contents in the 'code' field only. Do not include markdown fences."
    )


def apply_generated_code(path: Path, mode: str, generated_code: str) -> None:
    if mode == "replace":
        path.write_text(generated_code, encoding="utf-8")
    else:
        with path.open("a", encoding="utf-8") as f:
            f.write("\n\n" + generated_code + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--libs-dir", default="libs")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--type", dest="only_type", nargs="*", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--offline", action="store_true", help="Disable network/AI calls; write deterministic placeholders only (use only for diagnostics)")
    parser.add_argument("--log-file", help="Path to write detailed logs (also echoed to console)")
    parser.add_argument(
        "--mode",
        choices=["append", "replace"],
        default="append",
        help="How to write generated code into target files",
    )
    args = parser.parse_args()

    libs_dir = Path(args.libs_dir)
    only = set(args.only or [])

    # Configure tee logging if requested
    global LOG_FILE_PATH
    if args.log_file:
        LOG_FILE_PATH = args.log_file
        log_dir = os.path.dirname(LOG_FILE_PATH)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        sys.stdout = _TeeWriter(LOG_FILE_PATH, sys.stdout)  # type: ignore[assignment]
        sys.stderr = _TeeWriter(LOG_FILE_PATH, sys.stderr)  # type: ignore[assignment]
        print(f"[{ts()}] ai_populate: logging to {LOG_FILE_PATH}")

    any_changes = False
    libs_processed = 0
    for lib_name, lib_dir, pkg_dir in iter_library_packages(libs_dir):
        if only and lib_name not in only:
            continue
        print(f"[{ts()}] Scanning: {lib_name} at {lib_dir}")
        targets = find_targets(lib_dir)
        if not targets:
            print(f"{lib_name}: no AI targets found")
            continue
        print(f"[{ts()}] {lib_name}: {len(targets)} target files")
        start_lib = time.time()
        completed_in_lib = 0
        for idx, s in enumerate(targets, start=1):
            rel = str(s.relative_to(lib_dir))
            print(f"[{ts()}] target [{idx}/{len(targets)}] -> {rel}")
            if args.write and not args.dry_run:
                offline = bool(args.offline)
                if not offline:
                    t0 = time.time()
                    try:
                        content = s.read_text(encoding="utf-8")
                    except Exception:
                        content = ""
                    prompt = build_prompt(s, rel, lib_name, content)
                    print(f"[{ts()}] invoking AI for {rel} (mode={args.mode})")
                    result = call_openai_responses(prompt, content_hint=content)
                    code = (result or {}).get("code") if isinstance(result, dict) else None
                    if not code:
                        # Fallback to placeholder if AI failed
                        print(f"[{ts()}] AI failed; aborting. lib={lib_name} file={rel}")
                        print(f"[{ts()}] HINT: Ensure OPENAI_API_KEY and OPENAI_BASE_URL (if custom) are set; model={select_model()}; timeout={get_timeout_seconds()}s")
                        return 2
                    else:
                        took = time.time() - t0
                        print(f"[{ts()}] AI returned code ({len(code)} chars) in {took:.1f}s; applying -> {rel}")
                        apply_generated_code(s, args.mode, code)
                        completed_in_lib += 1
                    any_changes = True
                else:
                    print(f"[{ts()}] OFFLINE mode enabled — skipping AI and failing fast by design")
                    return 3
        libs_processed += 1
        print(f"[{ts()}] Completed {lib_name}: wrote {completed_in_lib}/{len(targets)} files in {time.time()-start_lib:.1f}s")

    if any_changes:
        print(f"[{ts()}] WROTE AI-generated code to target files. Libraries processed: {libs_processed}")
    else:
        print(f"[{ts()}] No changes written.")

    # OpenAI integration is enabled when OPENAI_API_KEY is present; in CI this will typically be absent.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
