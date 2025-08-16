#!/usr/bin/env python3
"""
Test script for the optimized critic implementation.

This demonstrates how the enhanced critic would work with structured feedback
and severity-based iteration approach.
"""

from optimized_critic_implementation import OptimizedCriticAgent, CriticResult
from optimized_nano_instructions import get_optimized_nano_prompt
import json


def test_critic_with_sample_code():
    """Test the critic with sample code that has various issues."""

    # Sample code with multiple issues
    sample_code = '''
import requests
import time

async def get api_key_from_header(request):
    """Get API key from request header."""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise ValueError("API key required")
    return api_key

def fetch_data(url):
    """Fetch data from URL."""
    response = requests.get(url)
    time.sleep(1)  # Blocking sleep
    return response.json()

class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, data):
        # Missing error handling
        result = data * 2
        return result

if __name__ == "__main__":
    processor = DataProcessor()
    result = processor.process("test")
    print(result)
'''

    # Test the critic
    critic = OptimizedCriticAgent()

    print("=== TESTING OPTIMIZED CRITIC ===\n")

    # Test first iteration (ruthless)
    print("1. FIRST ITERATION (RUTHLESS REVIEW)")
    print("=" * 50)

    result1 = critic.review_response(
        response=sample_code,
        artifact_type="code",
        original_prompt="Create a data processing utility with API authentication",
        context="Python async context with error handling",
        iteration_count=1,
    )

    print(f"Verdict: {result1.verdict}")
    print(f"Scores: {json.dumps(result1.scores, indent=2)}")
    print(f"Blocking Reason: {result1.blocking_reason}")
    print(f"\nFailures Found: {len(result1.failures)}")

    for i, failure in enumerate(result1.failures, 1):
        print(f"\n{i}. {failure.category.upper()}: {failure.evidence}")
        print(f"   Location: {failure.location}")
        print(f"   Fix: {failure.minimal_fix_hint}")

    print(f"\nNext Actions: {len(result1.next_actions)}")
    for i, action in enumerate(result1.next_actions, 1):
        print(f"   {i}. {action}")

    # Test second iteration (moderate)
    print(f"\n\n2. SECOND ITERATION (MODERATE REVIEW)")
    print("=" * 50)

    # Simulate some fixes
    improved_code = '''
import requests
import asyncio
from typing import Optional

async def get_api_key_from_header(request):
    """Get API key from request header."""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise ValueError("API key required")
    return api_key

async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    async with requests.Session() as session:
        response = await session.get(url, timeout=30)
        await asyncio.sleep(1)  # Non-blocking sleep
        return response.json()

class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, data):
        try:
            if not isinstance(data, (int, float)):
                raise TypeError("Data must be numeric")
            result = data * 2
            return result
        except Exception as e:
            raise ValueError(f"Processing failed: {e}")

if __name__ == "__main__":
    processor = DataProcessor()
    try:
        result = processor.process(42)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
'''

    result2 = critic.review_response(
        response=improved_code,
        artifact_type="code",
        original_prompt="Create a data processing utility with API authentication",
        context="Python async context with error handling",
        iteration_count=2,
    )

    print(f"Verdict: {result2.verdict}")
    print(f"Scores: {json.dumps(result2.scores, indent=2)}")
    print(f"Blocking Reason: {result2.blocking_reason}")
    print(f"\nFailures Found: {len(result2.failures)}")

    for i, failure in enumerate(result2.failures, 1):
        print(f"\n{i}. {failure.category.upper()}: {failure.evidence}")
        print(f"   Location: {failure.location}")
        print(f"   Fix: {failure.minimal_fix_hint}")

    print(f"\nNext Actions: {len(result2.next_actions)}")
    for i, action in enumerate(result2.next_actions, 1):
        print(f"   {i}. {action}")


def test_nano_instructions():
    """Test the optimized nano instructions."""

    print("\n\n=== TESTING OPTIMIZED NANO INSTRUCTIONS ===\n")

    # Test first iteration prompt
    print("1. FIRST ITERATION PROMPT")
    print("=" * 50)

    prompt1 = get_optimized_nano_prompt(
        artifact_type="code",
        original_prompt="Create a web scraper that extracts titles from URLs",
        iteration_count=1,
    )

    print(prompt1[:800] + "...")

    # Test second iteration prompt with critic feedback
    print("\n\n2. SECOND ITERATION PROMPT (WITH CRITIC FEEDBACK)")
    print("=" * 50)

    critic_feedback = """
{
  "verdict": "revise",
  "scores": {"correctness": 0.7, "consistency": 0.8, "safety": 0.6, "efficiency": 0.8, "clarity": 0.9},
  "failures": [
    {
      "category": "safety",
      "evidence": "requests.get() without timeout will hang indefinitely",
      "location": "fetch_data function",
      "minimal_fix_hint": "Add timeout parameter to requests.get()"
    },
    {
      "category": "syntax",
      "evidence": "async def get api_key_from_header(...) - space in function name",
      "location": "function definition",
      "minimal_fix_hint": "Remove space from function name: get_api_key_from_header"
    }
  ],
  "next_actions": [
    "Fix syntax: Remove space from function name get_api_key_from_header",
    "Fix safety: Add timeout=30 to requests.get() calls"
  ]
}
"""

    prompt2 = get_optimized_nano_prompt(
        artifact_type="code",
        original_prompt="Create a web scraper that extracts titles from URLs",
        critic_feedback=critic_feedback,
        iteration_count=2,
    )

    print(prompt2[:800] + "...")


def compare_approaches():
    """Compare the old vs new approach."""

    print("\n\n=== COMPARISON: OLD VS NEW APPROACH ===\n")

    print("OLD APPROACH:")
    print("- Free-form text feedback")
    print("- Vague suggestions like 'Consider using argparse'")
    print("- No severity prioritization")
    print("- No structured parsing")
    print("- Same prompt every iteration")

    print("\nNEW APPROACH:")
    print("- Structured JSON with specific scoring")
    print(
        "- Concrete evidence: 'async def get api_key_from_header(...) - space in function name'"
    )
    print("- Severity-based: First iteration = ruthless, later = lighter")
    print("- Machine-readable feedback with clear next actions")
    print("- Iteration-specific prompts with GPT-5 optimizations")

    print("\nEXPECTED BENEFITS:")
    print("- More efficient use of iterations")
    print("- Better quality improvement per iteration")
    print("- Focus on functional correctness over style")
    print("- Systematic issue resolution")
    print("- Reduced token waste on minor issues")


if __name__ == "__main__":
    test_critic_with_sample_code()
    test_nano_instructions()
    compare_approaches()
