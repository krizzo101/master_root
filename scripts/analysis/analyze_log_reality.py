#!/usr/bin/env python3
"""
Log Reality Analysis

Analyze the actual log content to get real statistics about duplication,
unique content, and session patterns.
"""

import re
from collections import Counter


def analyze_log_reality(log_file_path: str = "knowledge/nano.txt"):
    """Analyze the actual log content for real statistics."""

    print("=== LOG REALITY ANALYSIS ===\n")

    try:
        with open(log_file_path, encoding="utf-8") as f:
            lines = f.readlines()

        total_lines = len(lines)
        print(f"Total lines in log: {total_lines:,}")

        # Analyze unique lines
        unique_lines = set(lines)
        unique_count = len(unique_lines)
        print(f"Unique lines: {unique_count:,}")
        print(
            f"Duplication rate: {((total_lines - unique_count) / total_lines * 100):.1f}%"
        )

        # Analyze line patterns
        line_patterns = Counter()
        for line in lines:
            # Strip whitespace and get first 50 chars for pattern matching
            stripped = line.strip()
            if stripped:
                pattern = stripped[:50] + "..." if len(stripped) > 50 else stripped
                line_patterns[pattern] += 1

        # Find most common patterns
        print("\nMost common line patterns:")
        for pattern, count in line_patterns.most_common(5):
            print(f"  {count:4d}x: {pattern}")

        # Analyze session patterns
        session_markers = []
        for i, line in enumerate(lines):
            if "session_id" in line.lower():
                session_markers.append((i, line.strip()))

        print(f"\nSession markers found: {len(session_markers)}")
        if session_markers:
            print("Session IDs:")
            for i, (line_num, marker) in enumerate(session_markers[:5]):
                print(f"  {i+1}. Line {line_num}: {marker}")
            if len(session_markers) > 5:
                print(f"  ... and {len(session_markers) - 5} more")

        # Analyze API call patterns
        api_calls = [
            line for line in lines if "openai" in line.lower() or "api" in line.lower()
        ]
        print(f"\nAPI-related lines: {len(api_calls)}")

        # Analyze timestamp patterns
        timestamp_lines = [
            line for line in lines if re.search(r"\d{4}-\d{2}-\d{2}", line)
        ]
        print(f"Lines with timestamps: {len(timestamp_lines)}")

        # Estimate actual unique content
        # Remove common boilerplate and count meaningful content
        meaningful_lines = []
        boilerplate_patterns = [
            "You are a specialized professional",
            "Your output should be the complete",
            "Ensure the artifact is self-contained",
            "If the artifact is",
            "Your mission is to generate",
        ]

        for line in lines:
            line_stripped = line.strip()
            if line_stripped and not any(
                pattern in line_stripped for pattern in boilerplate_patterns
            ):
                meaningful_lines.append(line_stripped)

        meaningful_unique = len(set(meaningful_lines))
        print(
            f"\nMeaningful unique lines (excluding boilerplate): {meaningful_unique:,}"
        )

        # Calculate real log efficiency
        efficiency = meaningful_unique / total_lines * 100
        print(f"Log efficiency (meaningful content): {efficiency:.1f}%")

        return {
            "total_lines": total_lines,
            "unique_lines": unique_count,
            "duplication_rate": (total_lines - unique_count) / total_lines * 100,
            "meaningful_unique": meaningful_unique,
            "efficiency": efficiency,
            "sessions": len(session_markers),
        }

    except FileNotFoundError:
        print(f"Log file not found: {log_file_path}")
        return None
    except Exception as e:
        print(f"Error analyzing log: {e}")
        return None


def estimate_optimized_log_size(current_stats: dict) -> dict:
    """Estimate what the optimized log size would be."""

    if not current_stats:
        return None

    # Estimate optimization impact
    estimated_reduction = {
        "deduplication": 0.7,  # Remove 70% of duplicates
        "boilerplate_removal": 0.8,  # Remove 80% of boilerplate
        "structured_format": 0.9,  # 90% efficiency with structured format
        "session_consolidation": 0.5,  # 50% reduction from session consolidation
    }

    current_size = current_stats["total_lines"]
    meaningful_size = current_stats["meaningful_unique"]

    # Calculate optimized size
    optimized_size = meaningful_size * estimated_reduction["structured_format"]

    # Apply session consolidation
    if current_stats["sessions"] > 1:
        optimized_size *= estimated_reduction["session_consolidation"]

    reduction_percentage = (current_size - optimized_size) / current_size * 100

    print("\n=== OPTIMIZATION ESTIMATES ===")
    print(f"Current log size: {current_size:,} lines")
    print(f"Estimated optimized size: {optimized_size:,.0f} lines")
    print(f"Estimated reduction: {reduction_percentage:.1f}%")

    return {
        "current_size": current_size,
        "optimized_size": optimized_size,
        "reduction_percentage": reduction_percentage,
    }


if __name__ == "__main__":
    # Analyze the actual log
    stats = analyze_log_reality()

    if stats:
        # Estimate optimization impact
        optimization = estimate_optimized_log_size(stats)

        print("\n=== SUMMARY ===")
        print(f"Real log size: {stats['total_lines']:,} lines")
        print(f"Actual duplication: {stats['duplication_rate']:.1f}%")
        print(f"Meaningful content: {stats['meaningful_unique']:,} lines")
        print(f"Log efficiency: {stats['efficiency']:.1f}%")
        print(f"Number of sessions: {stats['sessions']}")

        if optimization:
            print(
                f"Optimization potential: {optimization['reduction_percentage']:.1f}% reduction"
            )
