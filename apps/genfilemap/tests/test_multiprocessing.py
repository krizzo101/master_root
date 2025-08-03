
"""
Test script for multiprocessing implementation in GenFileMap.

This script runs tests with different process and concurrency settings to verify
the implementation and measure performance impacts.
"""

import os
import time
import subprocess
import argparse
from typing import Dict, List, Tuple

def test_processing_with_different_settings(base_path: str, min_lines: int = 10):
    """
    Test GenFileMap with different process and concurrency settings.
    
    Args:
        base_path: Path to process
        min_lines: Minimum number of lines for files to process
    
    Returns:
        List of results with performance metrics
    """
    results = []
    
    # Test configurations
    configs = [
        {"processes": 1, "concurrency": 1},
        {"processes": 1, "concurrency": 5},
        {"processes": 2, "concurrency": 3},
        {"processes": 3, "concurrency": 5}
    ]
    
    print("=== Testing GenFileMap with different process and concurrency settings ===")
    print(f"Base path: {base_path}")
    print(f"Min lines: {min_lines}")
    
    for config in configs:
        processes = config["processes"]
        concurrency = config["concurrency"]
        
        print(f"\nRunning with {processes} processes and concurrency {concurrency}...")
        
        start_time = time.time()
        cmd = [
            "python", "-m", "genfilemap",
            "--path", base_path,
            "--recursive",
            "--dry-run",  # Don't actually modify files
            "--min-lines", str(min_lines),
            "--processes", str(processes),
            "--concurrency", str(concurrency),
            "--debug"  # Enable debug output
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        duration = time.time() - start_time
        
        print(f"Execution time: {duration:.2f} seconds")
        print(f"Exit code: {process.returncode}")
        
        # Extract stats from output if available
        total_files = 0
        api_calls = 0
        for line in process.stdout.splitlines():
            if "Found " in line and " files to process" in line:
                try:
                    total_files = int(line.split("Found ")[1].split(" files")[0])
                except ValueError:
                    pass
            if "Total API calls:" in line:
                try:
                    api_calls = int(line.split("Total API calls: ")[1])
                except ValueError:
                    pass
        
        results.append({
            "processes": processes,
            "concurrency": concurrency,
            "duration": duration,
            "total_files": total_files,
            "api_calls": api_calls,
            "theoretical_max_concurrent": processes * concurrency
        })
    
    # Print summary
    print("\n=== Summary ===")
    print(f"{'Processes':<10} {'Concurrency':<15} {'Max Concurrent':<20} {'Duration (s)':<15} {'Files':<10}")
    print("-" * 70)
    for result in results:
        print(f"{result['processes']:<10} {result['concurrency']:<15} {result['theoretical_max_concurrent']:<20} {result['duration']:<15.2f} {result['total_files']:<10}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Test GenFileMap multiprocessing")
    parser.add_argument("--path", default=".", help="Path to process")
    parser.add_argument("--min-lines", type=int, default=10, help="Minimum lines")
    args = parser.parse_args()
    
    test_processing_with_different_settings(args.path, args.min_lines)

if __name__ == "__main__":
    main() 