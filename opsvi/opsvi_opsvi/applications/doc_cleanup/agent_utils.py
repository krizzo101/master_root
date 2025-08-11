import ast
import os
import subprocess
from typing import List, Optional

from src.shared.openai_interfaces.responses_interface import OpenAIResponsesInterface


def get_changed_files(base_ref: str = "HEAD~1", target_ref: str = "HEAD") -> List[str]:
    """
    Return a list of changed files between two git refs (default: last commit).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}", f"{target_ref}"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        return [f for f in files if f]
    except Exception as e:
        print(f"[agent_utils] Error getting changed files: {e}")
        return []


def extract_code_summary(file_path: str) -> str:
    """
    Extract function/class signatures and docstrings from a Python file.
    """
    try:
        with open(file_path) as f:
            source = f.read()
        tree = ast.parse(source)
        summary = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                sig = f"{type(node).__name__} {node.name}"
                doc = ast.get_docstring(node) or ""
                summary.append(f"{sig}: {doc}")
        return "\n".join(summary)
    except Exception as e:
        print(f"[agent_utils] Error extracting code summary from {file_path}: {e}")
        return ""


def extract_doc_section(
    code_file: str, docs_dir: str = "docs/applications/doc_cleanup/"
) -> Optional[str]:
    """
    Try to find and return the documentation section for a given code file.
    Looks for a .md file with a matching base name in docs_dir.
    """
    base = os.path.splitext(os.path.basename(code_file))[0]
    for fname in os.listdir(docs_dir):
        if fname.startswith(base) and fname.endswith(".md"):
            with open(os.path.join(docs_dir, fname)) as f:
                return f.read()
    return None


def summarize_content(content: str, model: str = "gpt-4.1") -> str:
    """
    Summarize content using OpenAI Responses API.
    """
    try:
        client = OpenAIResponsesInterface()
        response = client.create_response(
            thread_id="dummy-thread-id",  # Replace with real thread logic if needed
            model=model,
            instructions="Summarize the following content:",
            input=content,
        )
        return response.get("output_text", "")
    except Exception as e:
        print(f"[agent_utils] Error summarizing content: {e}")
        return ""


def new_demo_function(x):
    """
    Demo function for drift detection and documentation sync testing.

    Args:
        x (int or float): Input value to be doubled.

    Returns:
        int or float: The input value multiplied by 2.

    Example:
        >>> new_demo_function(3)
        6
    """
    return x * 2
