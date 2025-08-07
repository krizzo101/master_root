from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .generation.planner import (
    build_messages_for_patch_repo,
    build_messages_full_from_spec,
    build_messages_to_fill_missing,
    run_tool_orchestrated,
)
from .openai_client import OpenAIClient, OpenAIClientError
from .patching.apply_patch_adapter import apply_patch_text


def _read_repo_hint(repo_root: str, max_chars: int = 5000) -> str:
    root = Path(repo_root)
    files = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".md", ".txt", ".toml", ".json"}:
            files.append(p)
        if len(files) >= 50:
            break
    parts = []
    for p in files[:20]:
        try:
            text = p.read_text(errors="ignore")
            parts.append(f"FILE: {p.relative_to(root)}\n{text[:500]}\n")
        except Exception:
            continue
    joined = "\n".join(parts)
    return joined[:max_chars]


def build_app(
    spec: str, out_dir: str, reasoning_effort: str, package_name: str = "pycalc"
) -> None:
    logging.info("[build-app] Starting app generation")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    client = OpenAIClient(reasoning_effort=reasoning_effort)
    logging.info("[build-app] Requesting patch from model (full-from-spec)")
    messages = build_messages_full_from_spec(spec, package_name)
    patch_text = run_tool_orchestrated(client, messages)
    if not patch_text.strip().startswith("*** Begin Patch"):
        raise RuntimeError("Model did not return a patch.")
    # apply into out_dir
    logging.info("[build-app] Applying patch to %s", out_dir)
    result = apply_patch_text(out_dir, patch_text)
    logging.info("[build-app] Patch result: %s", result)
    # Check whether expected source directory exists per README
    readme_path = Path(out_dir) / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(errors="ignore")
        expected_pkg = None
        for line in readme.splitlines():
            if line.strip().startswith(f"- {package_name}/"):
                expected_pkg = package_name
                break
        if expected_pkg and not (Path(out_dir) / expected_pkg).exists():
            logging.info(
                "[build-app] Detected missing source package '%s', requesting follow-up patch",
                expected_pkg,
            )
            # Build a quick tree listing to guide the model
            tree = "\n".join(
                sorted([str(p.relative_to(out_dir)) for p in Path(out_dir).rglob("*")])
            )
            client = OpenAIClient(reasoning_effort=reasoning_effort)
            suggested = (
                f"pyproject.toml\n{package_name}/__init__.py\n{package_name}/__main__.py\n"
                f"{package_name}/cli.py\n{package_name}/ast_eval.py\n{package_name}/operations.py\n"
                f"{package_name}/history.py\ntests/test_{package_name}.py\n"
            )
            fill_messages = build_messages_to_fill_missing(readme, tree, package_name, suggested)
            follow_patch = run_tool_orchestrated(client, fill_messages)
            if follow_patch.strip().startswith("*** Begin Patch"):
                logging.info(
                    "[build-app] Applying follow-up patch to add missing files"
                )
                apply_res = apply_patch_text(out_dir, follow_patch)
                logging.info("[build-app] Follow-up patch result: %s", apply_res)
            else:
                logging.warning(
                    "[build-app] Follow-up patch request did not return a patch"
                )
    logging.info("[build-app] Completed")


def patch_repo(repo: str, request: str, reasoning_effort: str) -> None:
    logging.info("[patch-repo] Starting for %s", repo)
    hint = _read_repo_hint(repo)
    client = OpenAIClient(reasoning_effort=reasoning_effort)
    logging.info("[patch-repo] Requesting patch from model")
    messages = build_messages_for_patch_repo(request, hint)
    patch_text = run_tool_orchestrated(client, messages)
    if not patch_text.strip().startswith("*** Begin Patch"):
        raise RuntimeError("Model did not return a patch.")
    logging.info("[patch-repo] Applying patch to repo")
    result = apply_patch_text(repo, patch_text)
    logging.info("[patch-repo] Patch result: %s", result)
    logging.info("[patch-repo] Completed")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GPT-5 coding agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build-app", help="Generate a new application from spec")
    p_build.add_argument("--spec", required=True, help="Natural language spec")
    p_build.add_argument("--out", default="./generated_app", help="Output directory")
    p_build.add_argument(
        "--reasoning-effort",
        default="medium",
        choices=["minimal", "low", "medium", "high"],
    )  # if unsupported, server will ignore

    p_patch = sub.add_parser("patch-repo", help="Patch an existing repository")
    p_patch.add_argument("--repo", required=True, help="Path to repository root")
    p_patch.add_argument(
        "--request", required=True, help="Change request in natural language"
    )
    p_patch.add_argument(
        "--reasoning-effort",
        default="medium",
        choices=["minimal", "low", "medium", "high"],
    )  # if unsupported, server will ignore

    return p.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s"
    )
    try:
        args = parse_args()
        if args.cmd == "build-app":
            build_app(args.spec, args.out, args.reasoning_effort)
        elif args.cmd == "patch-repo":
            patch_repo(args.repo, args.request, args.reasoning_effort)
    except OpenAIClientError as e:
        logging.error("OpenAI client error: %s", e)
    except Exception as e:
        logging.error("Error: %s", e)


if __name__ == "__main__":
    main()
