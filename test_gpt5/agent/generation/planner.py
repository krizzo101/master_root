from __future__ import annotations

from typing import Any

from ..openai_client import OpenAIClient
from ..patching.apply_patch_adapter import PatchApplyError, apply_patch_text
from ..tools.local_reference_scan import local_reference_scan
from ..tools.run_tests import run_tests
from ..tools.tech_docs import tech_docs_search
from ..tools.web_scraping import web_scrape
from ..tools.web_search import web_search


def get_function_tools() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Define function tools and router mapping."""
    tools: list[dict[str, Any]] = [
        {
            "type": "function",
            "name": "web_search",
            "description": "Search the web for recent information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 3},
                },
                "required": ["query", "limit"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "web_scrape",
            "description": "Fetch a page and return title and text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                },
                "required": ["url"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "tech_docs_search",
            "description": "Search OpenAI Python SDK README for references.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "local_reference_scan",
            "description": "Scan local .reference folder for query matches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "root": {"type": "string"},
                },
                "required": ["query", "root"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "apply_patch",
            "description": "Apply a cookbook-style patch to a repository root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_root": {"type": "string"},
                    "patch_text": {"type": "string"},
                },
                "required": ["repo_root", "patch_text"],
                "additionalProperties": False,
            },
            "strict": True,
        },
        {
            "type": "function",
            "name": "run_tests",
            "description": "Quick syntax check on Python files under a repo root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_root": {"type": "string"},
                },
                "required": ["repo_root"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ]

    router = {
        "web_search": web_search,
        "web_scrape": web_scrape,
        "tech_docs_search": tech_docs_search,
        "local_reference_scan": local_reference_scan,
        "apply_patch": lambda a: _apply_patch_safe(a),
        "run_tests": run_tests,
    }

    return tools, router


def _apply_patch_safe(args: dict[str, Any]) -> dict[str, Any]:
    try:
        res = apply_patch_text(args["repo_root"], args["patch_text"])
        return {"status": res}
    except PatchApplyError as e:
        return {"error": str(e)}


def build_messages_for_build_app(spec: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": (
                "You are a senior software engineer. Generate a complete, runnable application. "
                "Use small, modular files with clear names and docstrings. If code is long, split files.\n"
                "When producing code edits, output ONLY a cookbook patch format between *** Begin Patch and *** End Patch."
            ),
        },
        {"role": "user", "content": spec},
    ]


def build_messages_for_patch_repo(
    request: str, repo_snapshot_hint: str = ""
) -> list[dict[str, Any]]:
    return [
        {
            "role": "developer",
            "content": (
                "You are a precise code editor. Produce a patch to implement the requested changes.\n"
                "Patch format rules:\n"
                "- Use relative paths only.\n- Use *** Update File:/Add File:/Delete File: sections.\n"
                "- Include sufficient unchanged context and optional @@ anchors.\n"
                "- End each file section with *** End of File if you used @@ anchors.\n"
            ),
        },
        {
            "role": "user",
            "content": request
            + ("\n\nHINT:\n" + repo_snapshot_hint if repo_snapshot_hint else ""),
        },
    ]


def run_tool_orchestrated(client: OpenAIClient, messages: list[dict[str, Any]]) -> str:
    tools, router = get_function_tools()
    final_text, _ = client.tool_loop(messages, tools, router)
    return final_text
