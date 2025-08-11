PROMPTS = {
    "code": "Write a Python function for the following request. Output only the function code, no explanations, no tests, no comments. Requirements: {prompt}",
    "doc": "Write a clear, well-structured markdown document for the following request. Output only the markdown content, no explanations or extra text. Requirements: {prompt}",
}
MODEL_MAP = {
    "code": ["gpt-4.1", "o3", "gpt-4.1-mini", "o3-mini"],
    "doc": ["gpt-4.1", "gpt-4.1-mini", "o3", "o3-mini"],
    "config": ["gpt-4.1", "gpt-4.1-mini", "o3", "o3-mini"],
    "unit_test": ["gpt-4.1", "gpt-4.1-mini", "o3", "o3-mini"],
    "diagram": ["gpt-4.1", "gpt-4.1-mini", "o3", "o3-mini"],
    "documentation": ["gpt-4.1", "gpt-4.1-mini", "o3", "o3-mini"],
}
VALIDATION_TOOLS = {"python": ["flake8", "black"], "markdown": ["markdownlint"]}
AGENT_PROMPTS = {
    "analyst": "You are a requirements analyst. Given the user request, produce a clear, complete requirements document.",
    "designer": "You are a software designer. Given the requirements, produce a high-level design document.",
    "spec": "You are a technical spec writer. Given the requirements and design, produce a detailed technical specification.",
    "promptgen": "You are a prompt engineer. Given the requirements, design, and spec, generate a custom prompt for the dev agent, referencing the docs as needed.",
}
DOC_TEMPLATES = {
    "requirements": "# Requirements\n\n- ...",
    "design": "# Design\n\n- ...",
    "spec": "# Technical Specification\n\n- ...",
}
