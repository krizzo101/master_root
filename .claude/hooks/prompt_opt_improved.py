#!/usr/bin/env python3
"""
Improved prompt optimizer that recognizes ambiguity and handles it intelligently.
"""
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

# Ambiguity detection keywords
VAGUE_INDICATORS = [
    "something",
    "some kind of",
    "maybe",
    "possibly",
    "could",
    "app",
    "tool",
    "system",
    "thing",
    "stuff",
    "manage",
    "handle",
]

SPECIFIC_INDICATORS = [
    "using",
    "with",
    "implement",
    "must have",
    "should include",
    "requirements:",
    "specs:",
    "api:",
    "database:",
    "frontend:",
    "backend:",
    "deploy",
    "test",
    "ci/cd",
]


def analyze_specificity(prompt: str) -> Tuple[float, List[str]]:
    """
    Analyze how specific a prompt is.
    Returns (specificity_score, missing_elements)
    Score: 0.0 = very vague, 1.0 = very specific
    """
    prompt_lower = prompt.lower()

    # Count vague vs specific indicators
    vague_count = sum(1 for v in VAGUE_INDICATORS if v in prompt_lower)
    specific_count = sum(1 for s in SPECIFIC_INDICATORS if s in prompt_lower)

    # Check for key missing elements
    missing = []

    # For software projects
    if any(
        word in prompt_lower
        for word in ["app", "application", "system", "tool", "software"]
    ):
        if (
            "language" not in prompt_lower
            and "typescript" not in prompt_lower
            and "python" not in prompt_lower
        ):
            missing.append("programming language/tech stack")
        if "database" not in prompt_lower and "storage" not in prompt_lower:
            missing.append("data storage approach")
        if (
            "ui" not in prompt_lower
            and "frontend" not in prompt_lower
            and "interface" not in prompt_lower
        ):
            missing.append("user interface requirements")
        if not any(
            word in prompt_lower
            for word in ["api", "endpoint", "route", "rest", "graphql"]
        ):
            missing.append("API design")

    # Length check - very short prompts are usually vague
    word_count = len(prompt.split())
    if word_count < 10:
        length_penalty = 0.3
    elif word_count < 20:
        length_penalty = 0.1
    else:
        length_penalty = 0

    # Calculate score
    if specific_count + vague_count > 0:
        specificity = (specific_count - vague_count) / (
            specific_count + vague_count + 1
        )
    else:
        specificity = 0.5  # neutral

    specificity = max(0, min(1, specificity - length_penalty))

    return specificity, missing


def get_conversation_context(transcript_path: str, k: int = 3) -> List[Dict]:
    """
    Get last k exchanges (user prompt + assistant response).
    """
    exchanges = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            messages = []
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    role = (obj.get("role") or obj.get("author") or "").lower()
                    content = (
                        obj.get("prompt") or obj.get("content") or obj.get("text") or ""
                    )
                    if isinstance(content, list):
                        content = "".join(
                            p.get("text", "") for p in content if isinstance(p, dict)
                        )
                    if role in ["user", "assistant"] and content:
                        messages.append(
                            {"role": role, "content": content[:500]}
                        )  # Truncate for context
                except:
                    continue

        # Group into exchanges
        for i in range(0, len(messages) - 1, 2):
            if messages[i]["role"] == "user":
                exchange = {"user": messages[i]["content"]}
                if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                    exchange["assistant"] = messages[i + 1]["content"]
                exchanges.append(exchange)

        return exchanges[-k:]
    except:
        return []


def generate_clarifying_questions(prompt: str, missing_elements: List[str]) -> str:
    """
    Generate clarifying questions based on what's missing.
    """
    questions = []

    if "programming language/tech stack" in missing_elements:
        questions.append(
            "What technology stack would you prefer? (e.g., Python/FastAPI, Node.js/Express, etc.)"
        )

    if "data storage approach" in missing_elements:
        questions.append(
            "What kind of data persistence do you need? (e.g., PostgreSQL, MongoDB, in-memory, file-based)"
        )

    if "user interface requirements" in missing_elements:
        questions.append(
            "What kind of interface do you envision? (e.g., Web UI, CLI, API-only, mobile app)"
        )

    if "API design" in missing_elements:
        questions.append("Do you need an API? If so, REST, GraphQL, or something else?")

    # General questions for vague requests
    if len(missing_elements) > 2:
        questions.insert(0, "Could you provide more details about your requirements?")
        questions.append(
            "What's the primary use case or problem you're trying to solve?"
        )
        questions.append("Who are the intended users?")

    return questions


def optimize_with_intelligence(prompt: str, transcript_path: str = "") -> Dict:
    """
    Intelligently optimize prompt based on specificity analysis.
    """
    # Analyze specificity
    specificity_score, missing_elements = analyze_specificity(prompt)

    # Get conversation context if available
    context = get_conversation_context(transcript_path) if transcript_path else []

    # Decision logic based on specificity
    if specificity_score < 0.3:  # Very vague
        # Don't try to optimize, add clarifying questions
        questions = generate_clarifying_questions(prompt, missing_elements)

        return {
            "strategy": "clarify",
            "original_prompt": prompt,
            "optimized_prompt": f"""[AMBIGUOUS REQUEST DETECTED]
User request: "{prompt}"

This request lacks specific requirements. Please engage in a requirements gathering conversation first.

Suggested clarifying questions:
{chr(10).join(f"- {q}" for q in questions)}

After gathering requirements, ask the user to confirm before proceeding with implementation.

DO NOT make assumptions about tech stack, architecture, or features unless explicitly stated.""",
            "questions": questions,
            "specificity_score": specificity_score,
        }

    elif specificity_score < 0.6:  # Somewhat vague
        # Partial optimization with caveats
        return {
            "strategy": "partial",
            "original_prompt": prompt,
            "optimized_prompt": f"""[PARTIAL SPECIFICATION]
User request: "{prompt}"

Missing details: {', '.join(missing_elements)}

Proceed with a minimal implementation and ask for clarification on:
{chr(10).join(f"- {element}" for element in missing_elements)}

Start with the simplest possible implementation that satisfies the explicit requirements.
Use defaults only where reasonable (e.g., SQLite for simple storage, CLI for simple interface).
Create a proof of concept first, then iterate based on user feedback.""",
            "specificity_score": specificity_score,
        }

    else:  # Specific enough
        # Full optimization as before
        return {
            "strategy": "optimize",
            "original_prompt": prompt,
            "optimized_prompt": f"""[READY FOR IMPLEMENTATION]
{prompt}

Implement this request with concrete deliverables and acceptance tests.
Break into Claude Code Tasks with SubagentStop checkpoints.""",
            "specificity_score": specificity_score,
        }


# Example usage
if __name__ == "__main__":
    # Test with ambiguous prompt
    result = optimize_with_intelligence("Let's create an app that manages agents")
    print(json.dumps(result, indent=2))

    # Test with specific prompt
    result = optimize_with_intelligence(
        "Create a Python FastAPI backend with PostgreSQL database for managing AI agents. "
        "Include CRUD operations, JWT auth, and WebSocket support for real-time updates."
    )
    print(json.dumps(result, indent=2))
