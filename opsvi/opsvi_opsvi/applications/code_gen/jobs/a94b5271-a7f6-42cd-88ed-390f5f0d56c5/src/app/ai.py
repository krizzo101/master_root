"""
AI-powered summarization and suggestion (mocked: returns simple string, replace with call to LLM OpenAI/GPT). 
"""
from typing import Dict, Any
import logging
import random


async def summarize(body: str) -> Dict[str, Any]:
    # Replace with LLM API integration
    first_sent = body.split(".")[0].strip() if "." in body else body[:100]
    return {"summary": f"Summary: {first_sent[:80]}..."}


async def suggest(body: str) -> Dict[str, Any]:
    # Replace with LLM API
    suggestions = [
        "Consider splitting long paragraphs.",
        "Clarify the introduction.",
        "Add an example to the conclusion.",
        "Try using more active voice.",
        "Make headings consistent.",
    ]
    return {"suggestion": random.choice(suggestions)}
