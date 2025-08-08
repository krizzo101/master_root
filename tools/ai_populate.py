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
    model = get_env_var("OPENAI_MODEL", "gpt-5") or "gpt-5"
    if model not in APPROVED_MODELS:
        print(f"Warning: Model '{model}' not approved; falling back to gpt-5")
        model = "gpt-5"
    return model


def ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def call_openai_responses(prompt: str) -> Optional[dict]:
    api_key = get_env_var("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = get_env_var("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = select_model()

    import urllib.request
    import urllib.error

    url = f"{base_url.rstrip('/')}/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Responses API: simple shape; ask for JSON object output
    # Minimal Responses API payload; request JSON via instruction in prompt
    body = {
        "model": model,
        "input": prompt,
        # Request plain text output; we'll self-parse JSON if present
        "text": {"format": {"type": "text"}},
        "reasoning": {"effort": "medium"} if model.startswith("gpt-5") else None,
        "max_output_tokens": 3000,
    }
    # Remove None fields
    body = {k: v for k, v in body.items() if v is not None}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    print(f"[{ts()}] OpenAI/Responses: POST {url} model={model}")
    try:
        with urllib.request.urlopen(req, timeout=get_timeout_seconds()) as resp:
            raw = resp.read().decode("utf-8")
            print(f"[{ts()}] OpenAI/Responses: HTTP {resp.status}; {len(raw)} bytes")
            payload = json.loads(raw)

            # Unified text extraction
            text_val: Optional[str] = None
            if isinstance(payload.get("output_text"), str):
                text_val = payload["output_text"]
            else:
                outputs = payload.get("output") or payload.get("outputs")
                if outputs:
                    first = outputs[0]
                    for part in (first.get("content") or []):
                        if part.get("type") in ("output_text", "text") and isinstance(part.get("text"), str):
                            text_val = part.get("text")
                            break
            if text_val is None and isinstance(payload.get("text"), str):
                text_val = payload["text"]

            if not text_val:
                return None

            # Prefer structured JSON {code, reasoning}; else treat as raw code
            try:
                parsed = json.loads(text_val)
                if isinstance(parsed, dict) and isinstance(parsed.get("code"), str):
                    return parsed
                # If parsed JSON is not the expected shape, fall back to raw text
                return {"code": text_val, "reasoning": "freeform"}
            except Exception:
                return {"code": text_val, "reasoning": "freeform"}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8', 'ignore')
        except Exception:
            err_body = '<no-body>'
        print(f"[{ts()}] OpenAI/Responses ERROR: {e.code} {err_body}")
    except Exception as e:  # noqa: BLE001
        print(f"[{ts()}] OpenAI/Responses EXCEPTION: {e}")
    return None


def call_openai_chat(prompt: str) -> Optional[dict]:
    api_key = get_env_var("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = get_env_var("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = select_model()

    import urllib.request
    import urllib.error

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    print(f"[{ts()}] OpenAI/Chat: POST {url} model={model}")
    try:
        with urllib.request.urlopen(req, timeout=get_timeout_seconds()) as resp:
            raw = resp.read().decode("utf-8")
            print(f"[{ts()}] OpenAI/Chat: HTTP {resp.status}; {len(raw)} bytes")
            payload = json.loads(raw)
            choices = payload.get("choices") or []
            if not choices:
                return None
            content = choices[0].get("message", {}).get("content", "")
            try:
                return json.loads(content)
            except Exception:
                return {"code": content, "reasoning": "freeform"}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8', 'ignore')
        except Exception:
            err_body = '<no-body>'
        print(f"[{ts()}] OpenAI/Chat ERROR: {e.code} {err_body}")
    except Exception as e:  # noqa: BLE001
        print(f"[{ts()}] OpenAI/Chat EXCEPTION: {e}")
    return None


def build_prompt(file_path: Path, rel_path: str, lib_name: str, content: str) -> str:
    return (
        "You are an expert Python library developer. Generate high-quality, typed, "
        "readable code that replaces TODO/stub placeholders. Follow these rules: "
        "- Match the module purpose inferred from the path and current content. "
        "- Use asyncio where appropriate; include minimal docstrings; no secrets. "
        "- Keep code under ~200 lines if possible; no external network calls.\n\n"
        f"Library: {lib_name}\nFile: {rel_path}\n\n"
        "Current content:\n---BEGIN---\n" + content + "\n---END---\n\n"
        "Respond as JSON with fields: {\"code\": str, \"reasoning\": str}."
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
    parser.add_argument(
        "--mode",
        choices=["append", "replace"],
        default="append",
        help="How to write generated code into target files",
    )
    args = parser.parse_args()

    libs_dir = Path(args.libs_dir)
    only = set(args.only or [])

    any_changes = False
    for lib_name, lib_dir, pkg_dir in iter_library_packages(libs_dir):
        if only and lib_name not in only:
            continue
        print(f"[{ts()}] Scanning: {lib_name} at {lib_dir}")
        targets = find_targets(lib_dir)
        if not targets:
            print(f"{lib_name}: no AI targets found")
            continue
        print(f"[{ts()}] {lib_name}: {len(targets)} target files")
        for s in targets:
            rel = str(s.relative_to(lib_dir))
            print(f"[{ts()}] target -> {rel}")
            if args.write and not args.dry_run:
                offline = bool(args.offline)
                if not offline:
                    try:
                        content = s.read_text(encoding="utf-8")
                    except Exception:
                        content = ""
                    prompt = build_prompt(s, rel, lib_name, content)
                    print(f"[{ts()}] invoking AI for {rel} (mode={args.mode})")
                    result = call_openai_responses(prompt)
                    code = (result or {}).get("code") if isinstance(result, dict) else None
                    if not code:
                        # Fallback to placeholder if AI failed
                        print(f"[{ts()}] AI failed; aborting. lib={lib_name} file={rel}")
                        print(f"[{ts()}] HINT: Ensure OPENAI_API_KEY and OPENAI_BASE_URL (if custom) are set; model={select_model()}; timeout={get_timeout_seconds()}s")
                        return 2
                    else:
                        print(f"[{ts()}] AI returned code ({len(code)} chars); applying -> {rel}")
                        apply_generated_code(s, args.mode, code)
                    any_changes = True
                else:
                    print(f"[{ts()}] OFFLINE mode enabled — skipping AI and failing fast by design")
                    return 3

    if any_changes:
        print(f"[{ts()}] WROTE AI-generated code to target files.")
    else:
        print(f"[{ts()}] No changes written.")

    # OpenAI integration is enabled when OPENAI_API_KEY is present; in CI this will typically be absent.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
