#!/usr/bin/env python3
"""
Cognitive Query Tool for Cursor IDE Agents
Simple interface to cognitive database without AQL complexity
"""

import sys
import json
import argparse

# Add the core module to path
sys.path.append("/home/opsvi/asea/development/cognitive_interface/core")

try:
    from cognitive_database import CognitiveDatabase
except ImportError as e:
    print(json.dumps({"error": f"Failed to import cognitive_database: {e}"}))
    sys.exit(1)


def main():
    """Main CLI interface for agents"""

    parser = argparse.ArgumentParser(description="Cognitive Database Query Tool")
    parser.add_argument(
        "operation",
        choices=[
            "find_memories_about",
            "get_foundational_memories",
            "get_concepts_by_domain",
            "get_startup_context",
            "assess_system_health",
        ],
        help="Operation to perform",
    )

    # Arguments for different operations
    parser.add_argument("--topic", help="Topic to search for")
    parser.add_argument("--domain", help="Domain to filter by")
    parser.add_argument(
        "--importance-threshold",
        type=float,
        default=0.7,
        help="Minimum importance score",
    )
    parser.add_argument(
        "--min-quality", type=float, default=0.8, help="Minimum quality score"
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum results to return"
    )

    args = parser.parse_args()

    try:
        # Initialize database connection
        db = CognitiveDatabase()

        # Execute operation
        if args.operation == "find_memories_about":
            if not args.topic:
                print(json.dumps({"error": "Topic required for find_memories_about"}))
                sys.exit(1)

            results = db.find_memories_about(
                topic=args.topic,
                importance_threshold=args.importance_threshold,
                limit=args.limit,
            )

        elif args.operation == "get_foundational_memories":
            results = db.get_foundational_memories(min_quality=args.min_quality)

        elif args.operation == "get_concepts_by_domain":
            if not args.domain:
                print(
                    json.dumps({"error": "Domain required for get_concepts_by_domain"})
                )
                sys.exit(1)

            results = db.get_concepts_by_domain(
                domain=args.domain, min_quality=args.min_quality
            )

        elif args.operation == "get_startup_context":
            results = db.get_startup_context()

        elif args.operation == "assess_system_health":
            results = db.assess_system_health()

        else:
            print(json.dumps({"error": f"Unknown operation: {args.operation}"}))
            sys.exit(1)

        # Output results as JSON
        output = {
            "operation": args.operation,
            "success": True,
            "results": results,
            "count": len(results) if isinstance(results, list) else 1,
        }

        print(json.dumps(output, indent=2))

    except Exception as e:
        error_output = {
            "operation": args.operation,
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }

        print(json.dumps(error_output, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
