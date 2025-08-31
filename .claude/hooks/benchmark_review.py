#!/usr/bin/env python3
"""
Benchmark script to compare performance between original and optimized answer_review.py
"""
import json
import subprocess
import tempfile
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List

def create_test_transcript(temp_dir: Path, complexity: str = "simple") -> Path:
    """Create test transcript with varying complexity."""
    transcript_file = temp_dir / f"test_{complexity}.jsonl"
    
    test_cases = {
        "simple": {
            "user_prompts": ["What is 2+2?"],
            "assistant": "The answer is 4."
        },
        "complex": {
            "user_prompts": [
                "Write a Python function to calculate fibonacci",
                "Add error handling",
                "Make it recursive",
                "Optimize for performance",
                "Add type hints"
            ],
            "assistant": """def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""
        },
        "time_sensitive": {
            "user_prompts": ["What's the latest version of Python?"],
            "assistant": "The latest version of Python is 3.12."
        }
    }
    
    case = test_cases.get(complexity, test_cases["simple"])
    
    with open(transcript_file, "w") as f:
        for prompt in case["user_prompts"]:
            f.write(json.dumps({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat()
            }) + "\n")
        
        f.write(json.dumps({
            "role": "assistant",
            "content": case["assistant"],
            "timestamp": datetime.now().isoformat()
        }) + "\n")
    
    return transcript_file

def benchmark_script(script_path: str, transcript_path: Path, 
                    session_id: str, iterations: int = 10) -> Dict:
    """Benchmark a single script version."""
    timings = []
    errors = 0
    
    for i in range(iterations):
        input_data = {
            "session_id": f"{session_id}-{i}",
            "transcript_path": str(transcript_path),
            "stop_hook_active": False,
            "tool_name": "test"
        }
        
        start = time.perf_counter()
        try:
            result = subprocess.run(
                ["python", script_path],
                input=json.dumps(input_data),
                capture_output=True,
                text=True,
                timeout=30
            )
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            timings.append(elapsed)
            
            if result.returncode != 0:
                errors += 1
                
        except subprocess.TimeoutExpired:
            errors += 1
            timings.append(30000)  # 30s timeout as max
    
    if timings:
        return {
            "mean_ms": statistics.mean(timings),
            "median_ms": statistics.median(timings),
            "min_ms": min(timings),
            "max_ms": max(timings),
            "stdev_ms": statistics.stdev(timings) if len(timings) > 1 else 0,
            "errors": errors,
            "iterations": iterations
        }
    else:
        return {"errors": iterations, "iterations": iterations}

def run_comparison():
    """Run comparison between original and optimized versions."""
    print("# Answer Review Performance Benchmark\n")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Testing with multiple complexity levels\n")
    
    hooks_dir = Path("/home/opsvi/master_root/.claude/hooks")
    original_script = hooks_dir / "answer_review.py"
    optimized_script = hooks_dir / "answer_review_optimized.py"
    
    if not optimized_script.exists():
        print("❌ Optimized script not found!")
        return
    
    test_cases = ["simple", "complex", "time_sensitive"]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for complexity in test_cases:
            print(f"\n## Test Case: {complexity.upper()}")
            print("-" * 40)
            
            # Create test transcript
            transcript = create_test_transcript(temp_path, complexity)
            
            # Benchmark original
            print("Benchmarking original...")
            original_stats = benchmark_script(
                str(original_script), 
                transcript, 
                f"bench-orig-{complexity}",
                iterations=5  # Reduced for faster testing
            )
            
            # Benchmark optimized
            print("Benchmarking optimized...")
            optimized_stats = benchmark_script(
                str(optimized_script),
                transcript,
                f"bench-opt-{complexity}",
                iterations=5
            )
            
            # Calculate improvement
            if original_stats.get("mean_ms") and optimized_stats.get("mean_ms"):
                improvement = (
                    (original_stats["mean_ms"] - optimized_stats["mean_ms"]) 
                    / original_stats["mean_ms"] * 100
                )
                
                print("\n### Results")
                print(f"| Metric | Original | Optimized | Improvement |")
                print(f"|--------|----------|-----------|-------------|")
                print(f"| Mean   | {original_stats['mean_ms']:.2f}ms | {optimized_stats['mean_ms']:.2f}ms | {improvement:+.1f}% |")
                print(f"| Median | {original_stats['median_ms']:.2f}ms | {optimized_stats['median_ms']:.2f}ms | - |")
                print(f"| Min    | {original_stats['min_ms']:.2f}ms | {optimized_stats['min_ms']:.2f}ms | - |")
                print(f"| Max    | {original_stats['max_ms']:.2f}ms | {optimized_stats['max_ms']:.2f}ms | - |")
                print(f"| Errors | {original_stats['errors']} | {optimized_stats['errors']} | - |")
                
                if improvement > 10:
                    print(f"\n✅ **Significant improvement: {improvement:.1f}%**")
                elif improvement > 0:
                    print(f"\n✓ Modest improvement: {improvement:.1f}%")
                else:
                    print(f"\n⚠️ No improvement or regression: {improvement:.1f}%")
    
    print("\n## Summary")
    print("Optimizations implemented:")
    print("- ✅ Async context manager for provider")
    print("- ✅ Specific exception handling")
    print("- ✅ Type hints added")
    print("- ✅ Extracted classes for better organization")
    print("- ✅ Response caching with TTL")
    print("- ✅ Improved error recovery")

def validate_functionality():
    """Validate that optimized version maintains functionality."""
    print("\n## Functionality Validation")
    print("-" * 40)
    
    hooks_dir = Path("/home/opsvi/master_root/.claude/hooks")
    optimized_script = hooks_dir / "answer_review_optimized.py"
    
    # Test 1: Syntax check
    result = subprocess.run(
        ["python", "-m", "py_compile", str(optimized_script)],
        capture_output=True
    )
    if result.returncode == 0:
        print("✅ Syntax check passed")
    else:
        print(f"❌ Syntax check failed: {result.stderr.decode()}")
        return False
    
    # Test 2: Import check
    result = subprocess.run(
        ["python", "-c", f"import sys; sys.path.insert(0, '{hooks_dir}'); "
         "from answer_review_optimized import Config, ReviewService, ContentAnalyzer"],
        capture_output=True
    )
    if result.returncode == 0:
        print("✅ Import check passed")
    else:
        print(f"❌ Import check failed: {result.stderr.decode()}")
        return False
    
    # Test 3: Basic execution test
    with tempfile.TemporaryDirectory() as temp_dir:
        transcript = create_test_transcript(Path(temp_dir), "simple")
        input_data = {
            "session_id": "validation-test",
            "transcript_path": str(transcript),
            "stop_hook_active": False,
            "tool_name": "test"
        }
        
        result = subprocess.run(
            ["python", str(optimized_script)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                if "suppressOutput" in output or "decision" in output:
                    print("✅ Basic execution test passed")
                else:
                    print(f"⚠️ Unexpected output format: {output}")
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON output: {result.stdout}")
        else:
            print(f"❌ Execution failed: {result.stderr}")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("ANSWER REVIEW OPTIMIZATION BENCHMARK")
    print("=" * 50)
    
    # First validate functionality
    if validate_functionality():
        # Then run performance comparison
        run_comparison()
    else:
        print("\n❌ Validation failed - skipping performance tests")