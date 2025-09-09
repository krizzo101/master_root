#!/usr/bin/env python3
"""
Payload CLI Tool - Command-line payload generation with chunking strategies
Referenced in Phase 1 reports for GPT-5 session optimization.

Provides command-line interface for:
- Single session payload generation with multiple chunking strategies
- Batch processing for multiple sessions
- HTML/JSON output formats
- Integration with SessionAnalyticsEngine
- Size categories and optimization scoring (0-100 scale)

Usage:
  python payload_cli.py generate session.jsonl --strategy adaptive
  python payload_cli.py batch /path/to/sessions/ --output results/ --format json
  python payload_cli.py compare session.jsonl --all-strategies
"""

import argparse
import html
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gpt5_payload_system import GPT5OptimizationConfig, GPT5PayloadSystem
from session_analytics_engine import SessionAnalyticsEngine


class PayloadCLI:
    """Command-line interface for payload generation with chunking strategies"""

    def __init__(self):
        self.gpt5_system = GPT5PayloadSystem()
        self.session_analytics = SessionAnalyticsEngine()

        # Size categories for reporting
        self.size_categories = {
            "small": {"min": 0, "max": 10000, "name": "Small"},
            "medium": {"min": 10000, "max": 50000, "name": "Medium"},
            "large": {"min": 50000, "max": 200000, "name": "Large"},
            "extra_large": {"min": 200000, "max": float("inf"), "name": "Extra Large"},
        }

        # Available chunking strategies
        self.chunking_strategies = {
            "conversation": "Preserves conversation flow (2.36x compression)",
            "tool_usage": "Optimizes tool usage patterns (3.14x compression)",
            "adaptive": "Balanced approach (2.23x compression)",
            "none": "No chunking (1.0x compression)",
        }


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Payload CLI - Command-line payload generation with chunking strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate payload for single session
  python payload_cli.py generate session.jsonl --strategy adaptive

  # Batch process multiple sessions
  python payload_cli.py batch /path/to/sessions/ --output results/ --format json

  # Compare all chunking strategies
  python payload_cli.py compare session.jsonl --all-strategies

  # Generate HTML report
  python payload_cli.py report session.jsonl --format html --output report.html

  # Batch process with parallel execution
  python payload_cli.py batch /path/to/sessions/ --parallel --workers 4
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate payload for single session"
    )
    generate_parser.add_argument(
        "session_file", type=Path, help="Claude .jsonl session file"
    )
    generate_parser.add_argument(
        "--strategy",
        choices=["conversation", "tool_usage", "adaptive", "none"],
        default="adaptive",
        help="Chunking strategy (default: adaptive)",
    )
    generate_parser.add_argument(
        "--output", "-o", type=Path, help="Output file for payload"
    )
    generate_parser.add_argument(
        "--format",
        choices=["json", "text", "html"],
        default="json",
        help="Output format (default: json)",
    )
    generate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Batch command
    batch_parser = subparsers.add_parser(
        "batch", help="Batch process multiple sessions"
    )
    batch_parser.add_argument(
        "input_dir", type=Path, help="Directory containing .jsonl files"
    )
    batch_parser.add_argument(
        "--output", "-o", type=Path, required=True, help="Output directory"
    )
    batch_parser.add_argument(
        "--format",
        choices=["json", "html", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    batch_parser.add_argument(
        "--strategy",
        choices=["conversation", "tool_usage", "adaptive", "none"],
        default="adaptive",
        help="Chunking strategy (default: adaptive)",
    )
    batch_parser.add_argument(
        "--parallel", action="store_true", help="Enable parallel processing"
    )
    batch_parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers"
    )
    batch_parser.add_argument(
        "--pattern", default="*.jsonl", help="File pattern (default: *.jsonl)"
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare chunking strategies"
    )
    compare_parser.add_argument(
        "session_file", type=Path, help="Claude .jsonl session file"
    )
    compare_parser.add_argument(
        "--all-strategies", action="store_true", help="Compare all available strategies"
    )
    compare_parser.add_argument(
        "--strategies",
        nargs="+",
        choices=["conversation", "tool_usage", "adaptive", "none"],
        help="Specific strategies to compare",
    )
    compare_parser.add_argument(
        "--output", "-o", type=Path, help="Output file for comparison"
    )
    compare_parser.add_argument(
        "--format",
        choices=["json", "html", "table"],
        default="table",
        help="Output format (default: table)",
    )

    # Report command
    report_parser = subparsers.add_parser(
        "report", help="Generate comprehensive session report"
    )
    report_parser.add_argument(
        "session_file", type=Path, help="Claude .jsonl session file"
    )
    report_parser.add_argument(
        "--output", "-o", type=Path, help="Output file for report"
    )
    report_parser.add_argument(
        "--format",
        choices=["json", "html"],
        default="html",
        help="Report format (default: html)",
    )
    report_parser.add_argument(
        "--include-analytics",
        action="store_true",
        help="Include SessionAnalyticsEngine analysis",
    )

    # Global options
    parser.add_argument("--config", type=Path, help="Configuration file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")

    return parser


def categorize_session_size(tokens: int) -> str:
    """Categorize session by token count"""
    if tokens < 10000:
        return "small"
    elif tokens < 50000:
        return "medium"
    elif tokens < 200000:
        return "large"
    else:
        return "extra_large"


def calculate_optimization_score(
    tokens: int, compression_ratio: float, session_data: Optional[Dict] = None
) -> float:
    """Calculate optimization score (0-100 scale)"""
    score = 0.0

    # Base score from size category
    size_category = categorize_session_size(tokens)
    size_scores = {"small": 20.0, "medium": 40.0, "large": 70.0, "extra_large": 90.0}
    score += size_scores.get(size_category, 50.0)

    # Compression ratio bonus
    if compression_ratio > 3.0:
        score += 10.0
    elif compression_ratio > 2.5:
        score += 7.0
    elif compression_ratio > 2.0:
        score += 5.0

    # GPT-5 limit consideration
    if tokens > 200000:  # Exceeds practical GPT-5 limits
        score += 15.0
    elif tokens > 100000:
        score += 10.0

    return min(100.0, score)


def command_generate(args, cli: PayloadCLI):
    """Handle generate command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    print(f"🚀 Generating payload: {args.session_file.name}")
    print(f"   Strategy: {args.strategy}")
    print(f"   Format: {args.format}")

    start_time = time.time()

    try:
        # Optimize session
        result = cli.gpt5_system.optimize_session_file(args.session_file)

        if not result.success:
            print(f"❌ Optimization failed: {result.error_message}")
            return 1

        # Calculate metrics
        stats = result.processing_stats
        tokens = stats.get("original_tokens", 0)
        compression_ratio = stats.get("compression_ratio", 1.0)
        optimization_score = calculate_optimization_score(tokens, compression_ratio)
        size_category = categorize_session_size(tokens)

        # Prepare output data
        output_data = {
            "session_id": result.session_id,
            "generation_timestamp": datetime.now().isoformat(),
            "strategy_used": args.strategy,
            "optimization_metrics": {
                "original_tokens": tokens,
                "optimized_tokens": stats.get("optimized_tokens", 0),
                "compression_ratio": compression_ratio,
                "cost_savings": stats.get("cost_savings", 0.0),
                "optimization_score": optimization_score,
                "size_category": size_category,
                "processing_time_seconds": stats.get("processing_time_seconds", 0.0),
            },
            "payloads_generated": len(result.generated_payloads),
            "payloads": [
                {
                    "payload": p.payload,
                    "estimated_tokens": p.estimated_tokens,
                    "compression_achieved": p.compression_achieved,
                    "payload_type": p.payload_type,
                    "quality_score": p.quality_score,
                }
                for p in result.generated_payloads
            ],
        }

        # Output results
        if args.output:
            save_output(output_data, args.output, args.format)
            print(f"💾 Payload saved to: {args.output}")
        else:
            print_output(output_data, args.format)

        # Print summary
        end_time = time.time()
        print(f"\n✅ Payload generation complete")
        print(f"   📊 {tokens:,} → {stats.get('optimized_tokens', 0):,} tokens")
        print(f"   🗜️  {compression_ratio:.2f}x compression")
        print(f"   💰 ${stats.get('cost_savings', 0.0):.4f} cost savings")
        print(f"   🎯 Optimization score: {optimization_score:.1f}/100")
        print(f"   📦 {len(result.generated_payloads)} payloads generated")
        print(f"   ⏱️  {end_time - start_time:.2f}s total time")

        return 0

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def command_batch(args, cli: PayloadCLI):
    """Handle batch command"""
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        return 1

    # Find session files
    session_files = list(args.input_dir.glob(args.pattern))
    if not session_files:
        print(f"❌ No files matching pattern '{args.pattern}' in {args.input_dir}")
        return 1

    print(f"🚀 Batch processing {len(session_files)} sessions")
    print(f"   Strategy: {args.strategy}")
    print(f"   Output: {args.output}")
    print(f"   Format: {args.format}")
    if args.parallel:
        print(f"   Workers: {args.workers}")

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    results = []
    failed_sessions = []

    def process_session(session_file: Path) -> Dict[str, Any]:
        """Process single session file"""
        try:
            result = cli.gpt5_system.optimize_session_file(session_file)

            if result.success:
                stats = result.processing_stats
                tokens = stats.get("original_tokens", 0)
                compression_ratio = stats.get("compression_ratio", 1.0)
                optimization_score = calculate_optimization_score(
                    tokens, compression_ratio
                )
                size_category = categorize_session_size(tokens)

                return {
                    "session_file": str(session_file.name),
                    "session_id": result.session_id,
                    "success": True,
                    "optimization_metrics": {
                        "original_tokens": tokens,
                        "optimized_tokens": stats.get("optimized_tokens", 0),
                        "compression_ratio": compression_ratio,
                        "cost_savings": stats.get("cost_savings", 0.0),
                        "optimization_score": optimization_score,
                        "size_category": size_category,
                        "processing_time_seconds": stats.get(
                            "processing_time_seconds", 0.0
                        ),
                    },
                    "payloads_generated": len(result.generated_payloads),
                    "generated_payloads": [
                        {
                            "estimated_tokens": p.estimated_tokens,
                            "compression_achieved": p.compression_achieved,
                            "payload_type": p.payload_type,
                            "quality_score": p.quality_score,
                        }
                        for p in result.generated_payloads
                    ],
                }
            else:
                return {
                    "session_file": str(session_file.name),
                    "success": False,
                    "error": result.error_message,
                }

        except Exception as e:
            return {
                "session_file": str(session_file.name),
                "success": False,
                "error": str(e),
            }

    # Process sessions
    if args.parallel and len(session_files) > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_file = {
                executor.submit(process_session, f): f for f in session_files
            }

            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)

                if result["success"]:
                    metrics = result["optimization_metrics"]
                    print(
                        f"   ✅ {result['session_file']}: {metrics['compression_ratio']:.2f}x compression, "
                        f"score {metrics['optimization_score']:.1f}"
                    )
                else:
                    print(f"   ❌ {result['session_file']}: {result['error']}")
                    failed_sessions.append(result["session_file"])
    else:
        for session_file in session_files:
            result = process_session(session_file)
            results.append(result)

            if result["success"]:
                metrics = result["optimization_metrics"]
                print(
                    f"   ✅ {result['session_file']}: {metrics['compression_ratio']:.2f}x compression, "
                    f"score {metrics['optimization_score']:.1f}"
                )
            else:
                print(f"   ❌ {result['session_file']}: {result['error']}")
                failed_sessions.append(result["session_file"])

    end_time = time.time()

    # Calculate summary statistics
    successful_results = [r for r in results if r["success"]]
    total_sessions = len(results)
    successful_sessions = len(successful_results)

    if successful_results:
        total_original_tokens = sum(
            r["optimization_metrics"]["original_tokens"] for r in successful_results
        )
        total_optimized_tokens = sum(
            r["optimization_metrics"]["optimized_tokens"] for r in successful_results
        )
        total_cost_savings = sum(
            r["optimization_metrics"]["cost_savings"] for r in successful_results
        )
        avg_compression = sum(
            r["optimization_metrics"]["compression_ratio"] for r in successful_results
        ) / len(successful_results)
        avg_optimization_score = sum(
            r["optimization_metrics"]["optimization_score"] for r in successful_results
        ) / len(successful_results)
        total_payloads = sum(r["payloads_generated"] for r in successful_results)

        # Size category distribution
        size_distribution = {}
        for r in successful_results:
            category = r["optimization_metrics"]["size_category"]
            size_distribution[category] = size_distribution.get(category, 0) + 1
    else:
        total_original_tokens = total_optimized_tokens = total_cost_savings = 0
        avg_compression = avg_optimization_score = total_payloads = 0
        size_distribution = {}

    # Prepare batch summary
    batch_summary = {
        "batch_processing_summary": {
            "processing_timestamp": datetime.now().isoformat(),
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "failed_sessions": len(failed_sessions),
            "success_rate_percent": (successful_sessions / total_sessions * 100)
            if total_sessions > 0
            else 0,
            "total_processing_time_seconds": end_time - start_time,
            "strategy_used": args.strategy,
            "parallel_processing": args.parallel,
            "workers_used": args.workers if args.parallel else 1,
        },
        "optimization_metrics": {
            "total_original_tokens": total_original_tokens,
            "total_optimized_tokens": total_optimized_tokens,
            "overall_compression_ratio": total_original_tokens / total_optimized_tokens
            if total_optimized_tokens > 0
            else 0,
            "average_compression_ratio": avg_compression,
            "total_cost_savings": total_cost_savings,
            "average_optimization_score": avg_optimization_score,
            "total_payloads_generated": total_payloads,
        },
        "size_category_distribution": size_distribution,
        "failed_sessions": failed_sessions,
        "session_results": results,
    }

    # Save batch results
    if args.format == "json":
        output_file = args.output / "batch_results.json"
        with open(output_file, "w") as f:
            json.dump(batch_summary, f, indent=2, default=str)
    elif args.format == "html":
        output_file = args.output / "batch_results.html"
        generate_batch_html_report(batch_summary, output_file)
    elif args.format == "csv":
        output_file = args.output / "batch_results.csv"
        generate_batch_csv_report(successful_results, output_file)

    # Print summary
    print(f"\n📊 Batch Processing Summary")
    print(
        f"   Sessions: {successful_sessions}/{total_sessions} successful ({successful_sessions/total_sessions*100:.1f}%)"
    )
    print(f"   Total tokens: {total_original_tokens:,} → {total_optimized_tokens:,}")
    print(f"   Average compression: {avg_compression:.2f}x")
    print(f"   Total cost savings: ${total_cost_savings:.2f}")
    print(f"   Average optimization score: {avg_optimization_score:.1f}/100")
    print(f"   Total payloads: {total_payloads}")
    print(f"   Processing time: {end_time - start_time:.2f}s")
    print(f"   Results saved to: {output_file}")

    if failed_sessions:
        print(f"   ⚠️  {len(failed_sessions)} sessions failed")

    return 0 if successful_sessions == total_sessions else 1


def command_compare(args, cli: PayloadCLI):
    """Handle compare command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    # Determine strategies to compare
    if args.all_strategies:
        strategies = ["conversation", "tool_usage", "adaptive", "none"]
    elif args.strategies:
        strategies = args.strategies
    else:
        strategies = ["conversation", "tool_usage", "adaptive"]

    print(f"🔄 Comparing chunking strategies: {args.session_file.name}")
    print(f"   Strategies: {', '.join(strategies)}")

    # Get base session analysis
    try:
        converted = cli.gpt5_system.format_adapter.convert_session_file(
            args.session_file
        )
        if not converted:
            print(f"❌ Failed to convert session file")
            return 1

        token_analysis = cli.gpt5_system.token_analyzer.analyze_session_tokens(
            converted
        )
        tokens = token_analysis.total_tokens
        size_category = categorize_session_size(tokens)

        print(f"📊 Session: {tokens:,} tokens, category: {size_category}")

        # Compare strategies
        comparison_results = {}
        compression_ratios = {
            "conversation": 2.36,
            "tool_usage": 3.14,
            "adaptive": 2.23,
            "none": 1.0,
        }

        for strategy in strategies:
            compression_ratio = compression_ratios.get(strategy, 1.0)
            optimized_tokens = int(tokens / compression_ratio)
            optimization_score = calculate_optimization_score(tokens, compression_ratio)

            # Calculate cost savings (estimated)
            original_cost = (tokens / 1000) * 0.025  # Estimated GPT-5 cost
            optimized_cost = (optimized_tokens / 1000) * 0.025
            cost_savings = original_cost - optimized_cost
            savings_percent = (
                (cost_savings / original_cost * 100) if original_cost > 0 else 0
            )

            comparison_results[strategy] = {
                "compression_ratio": compression_ratio,
                "optimized_tokens": optimized_tokens,
                "optimization_score": optimization_score,
                "cost_savings": cost_savings,
                "savings_percent": savings_percent,
                "strategy_description": cli.chunking_strategies.get(
                    strategy, "Unknown strategy"
                ),
            }

        # Prepare comparison data
        comparison_data = {
            "session_file": str(args.session_file.name),
            "comparison_timestamp": datetime.now().isoformat(),
            "original_analysis": {
                "total_tokens": tokens,
                "size_category": size_category,
                "estimated_original_cost": (tokens / 1000) * 0.025,
            },
            "strategy_comparisons": comparison_results,
            "recommended_strategy": max(
                comparison_results.items(), key=lambda x: x[1]["optimization_score"]
            )[0],
        }

        # Output results
        if args.output:
            save_output(comparison_data, args.output, args.format)
            print(f"💾 Comparison saved to: {args.output}")
        else:
            print_comparison(comparison_data, args.format)

        return 0

    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return 1


def command_report(args, cli: PayloadCLI):
    """Handle report command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    print(f"📋 Generating comprehensive report: {args.session_file.name}")

    try:
        # Get GPT-5 analysis
        result = cli.gpt5_system.optimize_session_file(args.session_file)

        # Get SessionAnalyticsEngine analysis if requested
        session_analysis = None
        if args.include_analytics:
            print("   Including SessionAnalyticsEngine analysis...")
            session_analysis = cli.session_analytics.analyze_session(args.session_file)

        # Prepare comprehensive report
        stats = result.processing_stats if result.success else {}
        tokens = stats.get("original_tokens", 0)
        compression_ratio = stats.get("compression_ratio", 1.0)
        optimization_score = calculate_optimization_score(tokens, compression_ratio)
        size_category = categorize_session_size(tokens)

        report_data = {
            "report_metadata": {
                "session_file": str(args.session_file.name),
                "generation_timestamp": datetime.now().isoformat(),
                "report_type": "comprehensive",
                "includes_analytics": args.include_analytics,
            },
            "session_overview": {
                "session_id": result.session_id if result.success else "unknown",
                "total_tokens": tokens,
                "size_category": size_category,
                "optimization_score": optimization_score,
                "processing_status": "success" if result.success else "failed",
            },
            "optimization_analysis": {
                "original_tokens": tokens,
                "optimized_tokens": stats.get("optimized_tokens", 0),
                "compression_ratio": compression_ratio,
                "cost_savings": stats.get("cost_savings", 0.0),
                "payloads_generated": len(result.generated_payloads)
                if result.success
                else 0,
                "processing_time_seconds": stats.get("processing_time_seconds", 0.0),
            },
        }

        # Add SessionAnalyticsEngine data if available
        if session_analysis:
            report_data["session_analytics"] = {
                "conversation_flow": {
                    "user_messages": session_analysis.conversation_flow.user_messages,
                    "assistant_messages": session_analysis.conversation_flow.assistant_messages,
                    "system_messages": session_analysis.conversation_flow.system_messages,
                    "conversation_length": session_analysis.conversation_flow.conversation_length,
                    "avg_response_time": session_analysis.conversation_flow.avg_response_time,
                    "patterns": session_analysis.conversation_flow.patterns,
                },
                "tool_usage": {
                    "tool_counts": session_analysis.tool_usage.tool_counts,
                    "tool_categories": session_analysis.tool_usage.tool_categories,
                    "mcp_tools_used": list(session_analysis.tool_usage.mcp_tools_used),
                },
                "file_operations": {
                    "files_read": len(session_analysis.file_operations.files_read),
                    "files_written": len(
                        session_analysis.file_operations.files_written
                    ),
                    "files_edited": len(session_analysis.file_operations.files_edited),
                    "operation_counts": session_analysis.file_operations.operation_counts,
                },
                "patterns_detected": session_analysis.patterns_detected,
                "complexity_rating": session_analysis.complexity_rating,
            }

        # Add payload details if available
        if result.success and result.generated_payloads:
            report_data["payload_details"] = [
                {
                    "payload_type": p.payload_type,
                    "estimated_tokens": p.estimated_tokens,
                    "compression_achieved": p.compression_achieved,
                    "quality_score": p.quality_score,
                    "payload_preview": p.payload[:200] + "..."
                    if len(p.payload) > 200
                    else p.payload,
                }
                for p in result.generated_payloads
            ]

        # Output report
        if args.output:
            save_output(report_data, args.output, args.format)
            print(f"💾 Report saved to: {args.output}")
        else:
            print_output(report_data, args.format)

        print(f"✅ Report generation complete")
        print(f"   📊 Analysis score: {optimization_score:.1f}/100")
        print(f"   🗜️  Compression: {compression_ratio:.2f}x")
        print(f"   💰 Savings: ${stats.get('cost_savings', 0.0):.4f}")

        return 0

    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return 1


def save_output(data: Dict[str, Any], output_path: Path, format_type: str):
    """Save output data to file in specified format"""
    if format_type == "json":
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    elif format_type == "html":
        generate_html_report(data, output_path)
    elif format_type == "text":
        with open(output_path, "w") as f:
            f.write(format_text_output(data))


def print_output(data: Dict[str, Any], format_type: str):
    """Print output data to console"""
    if format_type == "json":
        print(json.dumps(data, indent=2, default=str))
    elif format_type == "text":
        print(format_text_output(data))
    elif format_type == "html":
        print("HTML format requires --output file specification")


def print_comparison(data: Dict[str, Any], format_type: str):
    """Print strategy comparison results"""
    if format_type == "table":
        print(f"\n🔍 Strategy Comparison Results:")
        print(
            f"{'Strategy':<12} {'Compression':<12} {'Score':<8} {'Savings':<10} {'Description'}"
        )
        print("-" * 80)

        for strategy, results in data["strategy_comparisons"].items():
            print(
                f"{strategy:<12} {results['compression_ratio']:<12.2f} "
                f"{results['optimization_score']:<8.1f} {results['savings_percent']:<9.1f}% "
                f"{results['strategy_description']}"
            )

        print(f"\n🎯 Recommended: {data['recommended_strategy']}")
    else:
        print_output(data, format_type)


def format_text_output(data: Dict[str, Any]) -> str:
    """Format data as readable text"""
    output = []

    if "session_overview" in data:
        overview = data["session_overview"]
        output.append(f"Session Overview:")
        output.append(f"  ID: {overview.get('session_id', 'N/A')}")
        output.append(f"  Tokens: {overview.get('total_tokens', 0):,}")
        output.append(f"  Size Category: {overview.get('size_category', 'N/A')}")
        output.append(
            f"  Optimization Score: {overview.get('optimization_score', 0):.1f}/100"
        )
        output.append("")

    if "optimization_analysis" in data:
        opt = data["optimization_analysis"]
        output.append(f"Optimization Analysis:")
        output.append(f"  Original Tokens: {opt.get('original_tokens', 0):,}")
        output.append(f"  Optimized Tokens: {opt.get('optimized_tokens', 0):,}")
        output.append(f"  Compression Ratio: {opt.get('compression_ratio', 1.0):.2f}x")
        output.append(f"  Cost Savings: ${opt.get('cost_savings', 0.0):.4f}")
        output.append(f"  Payloads Generated: {opt.get('payloads_generated', 0)}")
        output.append("")

    return "\n".join(output)


def generate_html_report(data: Dict[str, Any], output_path: Path):
    """Generate HTML report"""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Payload Generation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background-color: #f8f9fa; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .score {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
        .table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .table th {{ background-color: #3498db; color: white; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <h1 class="header">Payload Generation Report</h1>

    <div class="section">
        <h2>Session Overview</h2>
"""

    if "session_overview" in data:
        overview = data["session_overview"]
        html_content += f"""
        <div class="metric">
            <strong>Session ID:</strong> {html.escape(str(overview.get('session_id', 'N/A')))}
        </div>
        <div class="metric">
            <strong>Total Tokens:</strong> {overview.get('total_tokens', 0):,}
        </div>
        <div class="metric">
            <strong>Size Category:</strong> {overview.get('size_category', 'N/A').replace('_', ' ').title()}
        </div>
        <div class="metric">
            <strong>Optimization Score:</strong>
            <span class="score">{overview.get('optimization_score', 0):.1f}/100</span>
        </div>
        """

    html_content += """
    </div>

    <div class="section">
        <h2>Optimization Analysis</h2>
    """

    if "optimization_analysis" in data:
        opt = data["optimization_analysis"]
        html_content += f"""
        <table class="table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Original Tokens</td><td>{opt.get('original_tokens', 0):,}</td></tr>
            <tr><td>Optimized Tokens</td><td>{opt.get('optimized_tokens', 0):,}</td></tr>
            <tr><td>Compression Ratio</td><td>{opt.get('compression_ratio', 1.0):.2f}x</td></tr>
            <tr><td>Cost Savings</td><td>${opt.get('cost_savings', 0.0):.4f}</td></tr>
            <tr><td>Payloads Generated</td><td>{opt.get('payloads_generated', 0)}</td></tr>
            <tr><td>Processing Time</td><td>{opt.get('processing_time_seconds', 0.0):.2f}s</td></tr>
        </table>
        """

    html_content += (
        """
    </div>

    <div class="section">
        <h2>Generated At</h2>
        <p>"""
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        + """</p>
    </div>

</body>
</html>
    """
    )

    with open(output_path, "w") as f:
        f.write(html_content)


def generate_batch_html_report(data: Dict[str, Any], output_path: Path):
    """Generate HTML report for batch processing"""
    summary = data["batch_processing_summary"]
    metrics = data["optimization_metrics"]

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Batch Processing Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; background-color: #f8f9fa; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .score {{ font-size: 20px; font-weight: bold; color: #27ae60; }}
        .table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        .table th {{ background-color: #3498db; color: white; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <h1 class="header">Batch Processing Report</h1>

    <div class="section">
        <h2>Processing Summary</h2>
        <div class="metric">
            <strong>Total Sessions:</strong> {summary['total_sessions']}
        </div>
        <div class="metric">
            <strong>Successful:</strong> <span class="success">{summary['successful_sessions']}</span>
        </div>
        <div class="metric">
            <strong>Failed:</strong> <span class="error">{summary['failed_sessions']}</span>
        </div>
        <div class="metric">
            <strong>Success Rate:</strong> <span class="score">{summary['success_rate_percent']:.1f}%</span>
        </div>
        <div class="metric">
            <strong>Processing Time:</strong> {summary['total_processing_time_seconds']:.2f}s
        </div>
    </div>

    <div class="section">
        <h2>Optimization Metrics</h2>
        <table class="table">
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Original Tokens</td><td>{metrics['total_original_tokens']:,}</td></tr>
            <tr><td>Total Optimized Tokens</td><td>{metrics['total_optimized_tokens']:,}</td></tr>
            <tr><td>Overall Compression</td><td>{metrics['overall_compression_ratio']:.2f}x</td></tr>
            <tr><td>Average Compression</td><td>{metrics['average_compression_ratio']:.2f}x</td></tr>
            <tr><td>Total Cost Savings</td><td>${metrics['total_cost_savings']:.2f}</td></tr>
            <tr><td>Average Optimization Score</td><td>{metrics['average_optimization_score']:.1f}/100</td></tr>
            <tr><td>Total Payloads Generated</td><td>{metrics['total_payloads_generated']}</td></tr>
        </table>
    </div>
"""

    # Add size distribution if available
    if "size_category_distribution" in data and data["size_category_distribution"]:
        html_content += """
    <div class="section">
        <h2>Size Category Distribution</h2>
        <table class="table">
            <tr><th>Category</th><th>Sessions</th></tr>
"""
        for category, count in data["size_category_distribution"].items():
            html_content += f"            <tr><td>{category.replace('_', ' ').title()}</td><td>{count}</td></tr>\n"

        html_content += """        </table>
    </div>
"""

    html_content += f"""
    <div class="section">
        <h2>Report Generated</h2>
        <p>{datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
    </div>

</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html_content)


def generate_batch_csv_report(results: List[Dict[str, Any]], output_path: Path):
    """Generate CSV report for batch processing"""
    import csv

    with open(output_path, "w", newline="") as csvfile:
        fieldnames = [
            "session_file",
            "session_id",
            "size_category",
            "original_tokens",
            "optimized_tokens",
            "compression_ratio",
            "optimization_score",
            "cost_savings",
            "payloads_generated",
            "processing_time_seconds",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            if result["success"]:
                metrics = result["optimization_metrics"]
                writer.writerow(
                    {
                        "session_file": result["session_file"],
                        "session_id": result["session_id"],
                        "size_category": metrics["size_category"],
                        "original_tokens": metrics["original_tokens"],
                        "optimized_tokens": metrics["optimized_tokens"],
                        "compression_ratio": metrics["compression_ratio"],
                        "optimization_score": metrics["optimization_score"],
                        "cost_savings": metrics["cost_savings"],
                        "payloads_generated": result["payloads_generated"],
                        "processing_time_seconds": metrics["processing_time_seconds"],
                    }
                )


def main():
    """Main CLI entry point"""
    parser = setup_argparse()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    if not args.quiet:
        print("🔧 Initializing Payload CLI...")

    try:
        cli = PayloadCLI()
    except Exception as e:
        print(f"❌ Failed to initialize CLI: {e}")
        return 1

    # Route to command handlers
    try:
        if args.command == "generate":
            return command_generate(args, cli)
        elif args.command == "batch":
            return command_batch(args, cli)
        elif args.command == "compare":
            return command_compare(args, cli)
        elif args.command == "report":
            return command_report(args, cli)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print(f"\n⚠️  Operation interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Command failed: {e}")
        if not args.quiet:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
