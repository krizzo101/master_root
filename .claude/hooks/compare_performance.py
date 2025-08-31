#!/usr/bin/env python3
"""Compare performance between original and optimized hooks."""

import json
import statistics
import subprocess
import tempfile
import time


def create_test_transcript():
    """Create a test transcript."""
    messages = [
        {"role": "user", "content": "Previous test prompt"},
        {"role": "assistant", "content": "Previous response"},
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")
        return f.name


def test_hook(script_path, prompt):
    """Test a hook and measure response time."""
    transcript = create_test_transcript()
    input_data = {"prompt": prompt, "transcript_path": transcript}

    times = []
    for i in range(3):
        start = time.time()
        try:
            result = subprocess.run(
                ["python", script_path],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=10,
            )
            elapsed = time.time() - start
            if result.returncode == 0:
                times.append(elapsed)
        except Exception:
            pass

    return times


def main():
    print("=" * 60)
    print("Performance Comparison")
    print("=" * 60)

    test_prompt = "Write a function to calculate factorial"

    # Test original
    print("\n1. Original prompt_opt.py (gpt-5-mini, full init):")
    orig_times = test_hook(".claude/hooks/prompt_opt.py", test_prompt)
    if orig_times:
        print(f"   Average: {statistics.mean(orig_times):.2f}s")
        print(f"   Min: {min(orig_times):.2f}s, Max: {max(orig_times):.2f}s")

    # Test optimized
    print("\n2. Optimized prompt_opt_fast.py (gpt-5-nano, lazy load):")
    fast_times = test_hook(".claude/hooks/prompt_opt_fast.py", test_prompt)
    if fast_times:
        print(f"   Average: {statistics.mean(fast_times):.2f}s")
        print(f"   Min: {min(fast_times):.2f}s, Max: {max(fast_times):.2f}s")

    if orig_times and fast_times:
        improvement = (
            1 - statistics.mean(fast_times) / statistics.mean(orig_times)
        ) * 100
        print(f"\n✅ Performance improvement: {improvement:.1f}%")
        print(
            f"   Saved: {statistics.mean(orig_times) - statistics.mean(fast_times):.2f}s per call"
        )


if __name__ == "__main__":
    main()
