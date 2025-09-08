#!/usr/bin/env python3
"""
GPT-5 Payload Generator CLI
Command-line interface for generating GPT-5 optimized payloads from session analytics.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from gpt5_payload_generator import GPT5PayloadGenerator, TokenCountAnalyzer
except ImportError as e:
    print(f"Error importing GPT-5 payload generator: {e}")
    sys.exit(1)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def analyze_session_file(file_path: str) -> dict:
    """Analyze a single session file for token counts and basic metrics"""
    try:
        analyzer = TokenCountAnalyzer()

        # Load file content
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".jsonl"):
                # Handle JSONL files
                lines = f.readlines()
                content = {
                    "messages": [json.loads(line) for line in lines if line.strip()]
                }
            else:
                # Handle JSON files
                content = json.load(f)

        # Perform analysis
        analysis = analyzer.analyze_content(content)

        return {
            "file_path": file_path,
            "file_size_mb": Path(file_path).stat().st_size / (1024 * 1024),
            "total_tokens": analysis.total_tokens,
            "estimated_cost": analysis.estimated_cost,
            "context_efficiency_score": analysis.context_efficiency_score,
            "recommended_chunks": analysis.recommended_chunks,
            "processing_time_estimate": analysis.processing_time_estimate,
        }

    except Exception as e:
        logging.error(f"Error analyzing {file_path}: {e}")
        return {"file_path": file_path, "error": str(e)}


def generate_payload(args):
    """Generate GPT-5 payload from session file"""
    generator = GPT5PayloadGenerator()

    try:
        logging.info(f"Generating payload for: {args.input}")
        logging.info(f"Chunking strategy: {args.strategy}")
        logging.info(f"Output format: {args.format}")

        result = generator.generate_payload(
            args.input, chunking_strategy=args.strategy, output_format=args.format
        )

        # Write output
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)
            logging.info(f"Payload written to: {output_path}")
        else:
            print(json.dumps(result, indent=2, default=str))

        # Print summary
        if "analysis" in result:
            analysis = result["analysis"]
            summary = analysis.get("payload_summary", {})

            print(f"\n=== Payload Generation Summary ===")
            print(f"Session ID: {summary.get('session_id', 'unknown')}")
            print(f"Total Tokens: {summary.get('total_tokens', 0):,}")
            print(f"Chunk Count: {summary.get('chunk_count', 0)}")
            print(f"Estimated Cost: ${summary.get('estimated_cost', 0):.4f}")
            print(f"Size Category: {summary.get('size_category', 'unknown')}")
            print(f"Compression Ratio: {summary.get('compression_ratio', 1.0):.2f}x")

            # Print recommendations
            if "recommendations" in analysis and analysis["recommendations"]:
                print(f"\n=== Optimization Recommendations ===")
                for i, rec in enumerate(analysis["recommendations"], 1):
                    print(f"{i}. {rec}")

    except Exception as e:
        logging.error(f"Error generating payload: {e}")
        sys.exit(1)


def analyze_file(args):
    """Analyze file for token counts and metrics"""
    try:
        result = analyze_session_file(args.input)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)
            logging.info(f"Analysis written to: {output_path}")
        else:
            print(json.dumps(result, indent=2, default=str))

        # Print summary if no error
        if "error" not in result:
            print(f"\n=== File Analysis Summary ===")
            print(f"File: {result['file_path']}")
            print(f"File Size: {result['file_size_mb']:.2f} MB")
            print(f"Total Tokens: {result['total_tokens']:,}")
            print(f"Estimated Cost: ${result['estimated_cost']:.4f}")
            print(f"Context Efficiency: {result['context_efficiency_score']:.1f}%")
            print(f"Recommended Chunks: {result['recommended_chunks']}")
            print(f"Processing Time Est: {result['processing_time_estimate']:.2f}s")

    except Exception as e:
        logging.error(f"Error analyzing file: {e}")
        sys.exit(1)


def batch_analyze(args):
    """Analyze multiple files in batch"""
    input_path = Path(args.input)

    # Find all session files
    if input_path.is_dir():
        # Analyze directory
        patterns = ["*.jsonl", "*.json"] if not args.pattern else [args.pattern]
        files = []
        for pattern in patterns:
            files.extend(input_path.glob(pattern))
    else:
        # Single file
        files = [input_path]

    if not files:
        logging.error(f"No files found matching criteria")
        sys.exit(1)

    logging.info(f"Found {len(files)} files to analyze")

    # Analyze each file
    results = []
    for file_path in sorted(files):
        logging.info(f"Analyzing: {file_path}")
        result = analyze_session_file(str(file_path))
        results.append(result)

    # Generate batch summary
    total_tokens = sum(r.get("total_tokens", 0) for r in results if "error" not in r)
    total_cost = sum(r.get("estimated_cost", 0) for r in results if "error" not in r)
    total_files = len([r for r in results if "error" not in r])
    error_files = len([r for r in results if "error" in r])

    batch_summary = {
        "analysis_timestamp": datetime.now().isoformat(),
        "total_files_analyzed": total_files,
        "error_files": error_files,
        "total_tokens": total_tokens,
        "total_estimated_cost": total_cost,
        "average_tokens_per_file": total_tokens / total_files if total_files > 0 else 0,
        "files": results,
    }

    # Write output
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(batch_summary, f, indent=2, default=str)
        logging.info(f"Batch analysis written to: {output_path}")
    else:
        print(json.dumps(batch_summary, indent=2, default=str))

    # Print summary
    print(f"\n=== Batch Analysis Summary ===")
    print(f"Files Analyzed: {total_files}")
    if error_files > 0:
        print(f"Files with Errors: {error_files}")
    print(f"Total Tokens: {total_tokens:,}")
    print(f"Total Estimated Cost: ${total_cost:.4f}")
    if total_files > 0:
        print(f"Average Tokens/File: {total_tokens / total_files:,.0f}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="GPT-5 Payload Generator - Convert session analytics to optimized GPT-5 input format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate payload from session file
  python payload_cli.py generate session.jsonl

  # Generate with custom chunking and save to file
  python payload_cli.py generate session.jsonl --strategy conversation --output payload.json

  # Analyze file for token counts
  python payload_cli.py analyze session.jsonl

  # Batch analyze directory
  python payload_cli.py batch /path/to/sessions --pattern "*.jsonl"

  # Generate structured prompt format
  python payload_cli.py generate session.jsonl --format structured_prompt
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate payload command
    gen_parser = subparsers.add_parser(
        "generate", help="Generate GPT-5 optimized payload"
    )
    gen_parser.add_argument("input", help="Input session file (.jsonl or .json)")
    gen_parser.add_argument(
        "--strategy",
        "-s",
        choices=["conversation", "tool_usage", "adaptive"],
        default="adaptive",
        help="Chunking strategy (default: adaptive)",
    )
    gen_parser.add_argument(
        "--format",
        "-f",
        choices=["json", "structured_prompt"],
        default="json",
        help="Output format (default: json)",
    )
    gen_parser.add_argument("--output", "-o", help="Output file path")

    # Analyze file command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze file for token counts and metrics"
    )
    analyze_parser.add_argument("input", help="Input session file (.jsonl or .json)")
    analyze_parser.add_argument("--output", "-o", help="Output file path")

    # Batch analyze command
    batch_parser = subparsers.add_parser(
        "batch", help="Analyze multiple files in batch"
    )
    batch_parser.add_argument("input", help="Input directory or file pattern")
    batch_parser.add_argument("--pattern", "-p", help='File pattern (e.g., "*.jsonl")')
    batch_parser.add_argument("--output", "-o", help="Output file path")

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    setup_logging(args.verbose)

    # Execute command
    if args.command == "generate":
        generate_payload(args)
    elif args.command == "analyze":
        analyze_file(args)
    elif args.command == "batch":
        batch_analyze(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
