"""
llm_augment.py
Module for augmenting LLM prompts with graph context and calling the LLM.
Requires: openai>=1.0.0 (pip install openai), OPENAI_API_KEY env variable.
"""

import os

import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def format_prompt(question: str, context: str) -> str:
    """Format a prompt for the LLM with the given question and graph context."""
    return f"Context:\n{context}\n\nQuestion: {question}\n" f"Answer:"


def call_llm(
    prompt: str, model: str = "gpt-4.1-2025-04-14", max_tokens: int = 256
) -> str:
    """Call OpenAI's API v1.x to get a completion for the prompt. Default: 'gpt-4.1-2025-04-14'."""
    if not client.api_key:
        return "[ERROR: OPENAI_API_KEY not set]"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM Error: {e}]"


def augment_with_graph(
    question: str, graph_info: str, model: str = "gpt-4.1-2025-04-14"
) -> str:
    """Combine question and graph info, call LLM ('gpt-4.1-2025-04-14' by default), and return the answer."""
    prompt = format_prompt(question, graph_info)
    return call_llm(prompt, model=model)
