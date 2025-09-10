#!/usr/bin/env python3
"""
Size Reporter - Session size analysis and reporting tool
Referenced in Phase 1 reports for GPT-5 session optimization.

Provides comprehensive session size analysis with:
- Size categories (Small/Medium/Large/Extra Large)
- Optimization scoring (0-100 scale)
- Cost analysis and ROI calculations
- HTML/JSON output formats
- Batch processing for multiple sessions
- Integration with existing SessionAnalyticsEngine
- Detailed reporting on compression potential

Usage:
  python size_reporter.py analyze session.jsonl --format html
  python size_reporter.py batch /path/to/sessions/ --output report.html
  python size_reporter.py dashboard /path/to/sessions/ --real-time
"""

import argparse
import html
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gpt5_payload_system import GPT5OptimizationConfig, GPT5PayloadSystem
from session_analytics_engine import SessionAnalyticsEngine
from size_analyzer import CostBreakdown, OptimizationAnalysis, SizeAnalyzer


class SizeReporter:
    """Comprehensive session size analysis and reporting tool"""

    def __init__(self):
        self.gpt5_system = GPT5PayloadSystem()
        self.session_analytics = SessionAnalyticsEngine()
        self.size_analyzer = SizeAnalyzer()

        # Size categories with detailed info
        self.size_categories = {
            "small": {
                "name": "Small",
                "range": "0 - 10K tokens",
                "typical_cost": "$0.00 - $0.75",
                "priority": "Low",
                "compression_potential": "1.5x",
                "chunking_strategy": "none",
                "description": "Simple conversations, minimal optimization needed",
            },
            "medium": {
                "name": "Medium",
                "range": "10K - 50K tokens",
                "typical_cost": "$0.75 - $3.75",
                "priority": "Medium",
                "compression_potential": "2.0x",
                "chunking_strategy": "conversation",
                "description": "Moderate complexity, good optimization potential",
            },
            "large": {
                "name": "Large",
                "range": "50K - 200K tokens",
                "typical_cost": "$3.75 - $15.00",
                "priority": "High",
                "compression_potential": "2.5x",
                "chunking_strategy": "adaptive",
                "description": "Complex workflows, significant optimization benefits",
            },
            "extra_large": {
                "name": "Extra Large",
                "range": "200K+ tokens",
                "typical_cost": "$15.00+",
                "priority": "Critical",
                "compression_potential": "3.0x",
                "chunking_strategy": "tool_usage",
                "description": "Exceeds GPT-5 limits, immediate optimization required",
            },
        }

        # Optimization score thresholds
        self.score_thresholds = {"excellent": 80, "good": 60, "fair": 40, "poor": 20}


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Size Reporter - Session size analysis and reporting tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single session
  python size_reporter.py analyze session.jsonl --format html

  # Batch analyze multiple sessions
  python size_reporter.py batch /path/to/sessions/ --output report.html

  # Generate dashboard for directory
  python size_reporter.py dashboard /path/to/sessions/ --output dashboard.html

  # Compare sessions
  python size_reporter.py compare session1.jsonl session2.jsonl --format json

  # Real-time monitoring
  python size_reporter.py monitor /path/to/sessions/ --watch-new --interval 30
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze single session size"
    )
    analyze_parser.add_argument(
        "session_file", type=Path, help="Claude .jsonl session file"
    )
    analyze_parser.add_argument(
        "--format",
        choices=["json", "html", "text"],
        default="text",
        help="Output format (default: text)",
    )
    analyze_parser.add_argument("--output", "-o", type=Path, help="Output file")
    analyze_parser.add_argument(
        "--include-analytics",
        action="store_true",
        help="Include SessionAnalyticsEngine analysis",
    )
    analyze_parser.add_argument(
        "--include-payloads",
        action="store_true",
        help="Include payload generation analysis",
    )
    analyze_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Batch command
    batch_parser = subparsers.add_parser(
        "batch", help="Batch analyze multiple sessions"
    )
    batch_parser.add_argument(
        "input_dir", type=Path, help="Directory containing .jsonl files"
    )
    batch_parser.add_argument(
        "--output", "-o", type=Path, required=True, help="Output file"
    )
    batch_parser.add_argument(
        "--format",
        choices=["json", "html", "csv"],
        default="html",
        help="Output format (default: html)",
    )
    batch_parser.add_argument(
        "--pattern", default="*.jsonl", help="File pattern (default: *.jsonl)"
    )
    batch_parser.add_argument(
        "--parallel", action="store_true", help="Enable parallel processing"
    )
    batch_parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers"
    )
    batch_parser.add_argument(
        "--include-analytics",
        action="store_true",
        help="Include SessionAnalyticsEngine analysis",
    )

    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard", help="Generate comprehensive dashboard"
    )
    dashboard_parser.add_argument(
        "input_dir", type=Path, help="Directory containing .jsonl files"
    )
    dashboard_parser.add_argument(
        "--output", "-o", type=Path, required=True, help="Output HTML file"
    )
    dashboard_parser.add_argument(
        "--real-time", action="store_true", help="Include real-time stats"
    )
    dashboard_parser.add_argument(
        "--include-trends", action="store_true", help="Include trend analysis"
    )
    dashboard_parser.add_argument(
        "--top-sessions",
        type=int,
        default=10,
        help="Number of top sessions to highlight",
    )

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare multiple sessions")
    compare_parser.add_argument(
        "session_files", nargs="+", type=Path, help="Session files to compare"
    )
    compare_parser.add_argument(
        "--format",
        choices=["json", "html", "table"],
        default="table",
        help="Output format (default: table)",
    )
    compare_parser.add_argument("--output", "-o", type=Path, help="Output file")
    compare_parser.add_argument(
        "--sort-by",
        choices=["size", "score", "cost", "compression"],
        default="score",
        help="Sort comparison by metric",
    )

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor session directory")
    monitor_parser.add_argument("input_dir", type=Path, help="Directory to monitor")
    monitor_parser.add_argument(
        "--watch-new", action="store_true", help="Watch for new files"
    )
    monitor_parser.add_argument(
        "--interval", type=int, default=60, help="Update interval in seconds"
    )
    monitor_parser.add_argument(
        "--output", "-o", type=Path, help="Output file for updates"
    )

    # Summary command
    summary_parser = subparsers.add_parser(
        "summary", help="Generate summary statistics"
    )
    summary_parser.add_argument(
        "input_dir", type=Path, help="Directory containing .jsonl files"
    )
    summary_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    summary_parser.add_argument("--output", "-o", type=Path, help="Output file")

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
    tokens: int, session_data: Optional[Dict] = None
) -> float:
    """Calculate optimization score (0-100 scale) based on Phase 1 testing results"""
    score = 0.0

    # Base score from size category
    size_category = categorize_session_size(tokens)
    size_scores = {
        "small": 20.0,  # Low optimization potential
        "medium": 40.0,  # Moderate optimization potential
        "large": 70.0,  # High optimization potential
        "extra_large": 90.0,  # Critical optimization need
    }
    score += size_scores.get(size_category, 50.0)

    # GPT-5 limit consideration (critical factor from Phase 1)
    if tokens > 200000:  # Exceeds practical GPT-5 limits
        score += 15.0
    elif tokens > 100000:
        score += 10.0
    elif tokens > 50000:
        score += 5.0

    # Session complexity bonus (if data available)
    if session_data:
        complexity = session_data.get("complexity_rating", "Unknown")
        if complexity in ["Very High"]:
            score += 8.0
        elif complexity in ["High"]:
            score += 5.0

        # Tool usage density
        tool_count = session_data.get("tool_usage", {}).get("total_tools", 0)
        if tool_count > 100:
            score += 5.0
        elif tool_count > 50:
            score += 3.0

        # Pattern bonuses
        patterns = session_data.get("patterns_detected", [])
        if "file_intensive" in patterns:
            score += 3.0
        if "mcp_integration" in patterns:
            score += 2.0

    return min(100.0, score)


def analyze_single_session(
    session_file: Path,
    reporter: SizeReporter,
    include_analytics: bool = False,
    include_payloads: bool = False,
) -> Dict[str, Any]:
    """Analyze a single session file"""
    try:
        # Get basic token analysis
        converted = reporter.gpt5_system.format_adapter.convert_session_file(
            session_file
        )
        if not converted:
            return {
                "error": "Failed to convert session file",
                "session_file": str(session_file),
            }

        token_analysis = reporter.gpt5_system.token_analyzer.analyze_session_tokens(
            converted
        )
        tokens = token_analysis.total_tokens
        size_category = categorize_session_size(tokens)

        # Get cost analysis
        cost_breakdown = reporter.size_analyzer.analyze_session_cost(tokens)
        optimization_analysis = reporter.size_analyzer.analyze_optimization_potential(
            tokens, converted
        )

        # Base analysis result
        analysis_result = {
            "session_file": str(session_file.name),
            "session_id": converted.get("session_id", str(session_file.stem)),
            "analysis_timestamp": datetime.now().isoformat(),
            "size_analysis": {
                "total_tokens": tokens,
                "input_tokens": token_analysis.input_tokens,
                "output_tokens": token_analysis.output_tokens,
                "size_category": size_category,
                "size_category_info": reporter.size_categories[size_category],
                "optimization_potential_percent": token_analysis.optimization_potential,
            },
            "cost_analysis": {
                "current_cost": cost_breakdown.total_cost,
                "input_cost": cost_breakdown.input_cost,
                "output_cost": cost_breakdown.output_cost,
                "cost_per_interaction": cost_breakdown.cost_per_interaction,
                "optimization_savings": cost_breakdown.optimization_savings,
                "potential_savings_percent": cost_breakdown.potential_savings_percent,
            },
            "optimization_analysis": {
                "optimization_score": optimization_analysis.optimization_score,
                "original_cost": optimization_analysis.original_cost,
                "optimized_cost": optimization_analysis.optimized_cost,
                "cost_savings": optimization_analysis.cost_savings,
                "savings_percent": optimization_analysis.savings_percent,
                "recommended_actions": optimization_analysis.recommended_actions,
                "quality_impact": optimization_analysis.quality_impact,
            },
        }

        # Add SessionAnalyticsEngine analysis if requested
        if include_analytics:
            session_analysis = reporter.session_analytics.analyze_session(session_file)

            # Calculate optimization score with additional context
            session_data = {
                "complexity_rating": session_analysis.complexity_rating,
                "tool_usage": {
                    "total_tools": sum(session_analysis.tool_usage.tool_counts.values())
                },
                "patterns_detected": session_analysis.patterns_detected,
            }
            enhanced_score = calculate_optimization_score(tokens, session_data)
            analysis_result["optimization_analysis"][
                "optimization_score"
            ] = enhanced_score

            analysis_result["session_analytics"] = {
                "conversation_flow": {
                    "user_messages": session_analysis.conversation_flow.user_messages,
                    "assistant_messages": session_analysis.conversation_flow.assistant_messages,
                    "conversation_length": session_analysis.conversation_flow.conversation_length,
                    "avg_response_time": session_analysis.conversation_flow.avg_response_time,
                    "patterns": session_analysis.conversation_flow.patterns,
                    "topic_shifts": session_analysis.conversation_flow.topic_shifts,
                },
                "tool_usage": {
                    "total_tool_calls": sum(
                        session_analysis.tool_usage.tool_counts.values()
                    ),
                    "unique_tools": len(session_analysis.tool_usage.tool_counts),
                    "tool_categories": session_analysis.tool_usage.tool_categories,
                    "mcp_tools_used": len(session_analysis.tool_usage.mcp_tools_used),
                    "tool_success_rates": session_analysis.tool_usage.tool_success_rate,
                },
                "file_operations": {
                    "files_read": len(session_analysis.file_operations.files_read),
                    "files_written": len(
                        session_analysis.file_operations.files_written
                    ),
                    "files_edited": len(session_analysis.file_operations.files_edited),
                    "operation_counts": session_analysis.file_operations.operation_counts,
                    "file_hotspots": session_analysis.file_operations.file_hotspots[:5],
                },
                "complexity_rating": session_analysis.complexity_rating,
                "patterns_detected": session_analysis.patterns_detected,
            }

        # Add payload generation analysis if requested
        if include_payloads:
            try:
                payload_result = reporter.gpt5_system.optimize_session_file(
                    session_file
                )
                if payload_result.success:
                    stats = payload_result.processing_stats
                    analysis_result["payload_analysis"] = {
                        "payloads_generated": len(payload_result.generated_payloads),
                        "compression_achieved": stats.get("compression_ratio", 1.0),
                        "strategy_used": stats.get("strategy_used", "unknown"),
                        "processing_time_seconds": stats.get(
                            "processing_time_seconds", 0.0
                        ),
                        "payload_details": [
                            {
                                "payload_type": p.payload_type,
                                "estimated_tokens": p.estimated_tokens,
                                "compression_achieved": p.compression_achieved,
                                "quality_score": p.quality_score,
                            }
                            for p in payload_result.generated_payloads
                        ],
                    }
                else:
                    analysis_result["payload_analysis"] = {
                        "error": payload_result.error_message,
                        "payloads_generated": 0,
                    }
            except Exception as e:
                analysis_result["payload_analysis"] = {
                    "error": str(e),
                    "payloads_generated": 0,
                }

        return analysis_result

    except Exception as e:
        return {
            "error": str(e),
            "session_file": str(session_file),
            "analysis_timestamp": datetime.now().isoformat(),
        }


def command_analyze(args, reporter: SizeReporter):
    """Handle analyze command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    print(f"📊 Analyzing session: {args.session_file.name}")

    start_time = time.time()
    analysis = analyze_single_session(
        args.session_file, reporter, args.include_analytics, args.include_payloads
    )
    end_time = time.time()

    if "error" in analysis:
        print(f"❌ Analysis failed: {analysis['error']}")
        return 1

    # Add processing time
    analysis["processing_time_seconds"] = end_time - start_time

    # Output results
    if args.output:
        save_analysis_output(analysis, args.output, args.format)
        print(f"💾 Analysis saved to: {args.output}")
    else:
        print_analysis_output(analysis, args.format, args.verbose)

    # Print summary
    size_analysis = analysis["size_analysis"]
    opt_analysis = analysis["optimization_analysis"]

    print(f"\n✅ Analysis complete")
    print(
        f"   📏 Size: {size_analysis['total_tokens']:,} tokens ({size_analysis['size_category_info']['name']})"
    )
    print(f"   🎯 Optimization score: {opt_analysis['optimization_score']:.1f}/100")
    print(f"   💰 Current cost: ${analysis['cost_analysis']['current_cost']:.4f}")
    print(
        f"   💡 Potential savings: ${opt_analysis['cost_savings']:.4f} ({opt_analysis['savings_percent']:.1f}%)"
    )
    print(f"   ⏱️  Analysis time: {end_time - start_time:.2f}s")

    return 0


def command_batch(args, reporter: SizeReporter):
    """Handle batch command"""
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        return 1

    # Find session files
    session_files = list(args.input_dir.glob(args.pattern))
    if not session_files:
        print(f"❌ No files matching pattern '{args.pattern}' in {args.input_dir}")
        return 1

    print(f"📊 Batch analyzing {len(session_files)} sessions")
    if args.parallel:
        print(f"⚡ Using {args.workers} parallel workers")

    start_time = time.time()

    def process_session(session_file: Path) -> Dict[str, Any]:
        """Process single session file"""
        return analyze_single_session(
            session_file, reporter, args.include_analytics, False
        )

    # Process sessions
    results = []
    if args.parallel and len(session_files) > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_file = {
                executor.submit(process_session, f): f for f in session_files
            }

            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)

                if "error" not in result:
                    score = result["optimization_analysis"]["optimization_score"]
                    category = result["size_analysis"]["size_category"]
                    print(
                        f"   ✅ {result['session_file']}: {score:.1f}/100 ({category})"
                    )
                else:
                    print(f"   ❌ {result['session_file']}: {result['error']}")
    else:
        for session_file in session_files:
            result = process_session(session_file)
            results.append(result)

            if "error" not in result:
                score = result["optimization_analysis"]["optimization_score"]
                category = result["size_analysis"]["size_category"]
                print(f"   ✅ {result['session_file']}: {score:.1f}/100 ({category})")
            else:
                print(f"   ❌ {result['session_file']}: {result['error']}")

    end_time = time.time()

    # Generate batch summary
    batch_summary = generate_batch_summary(results, end_time - start_time)

    # Save results
    save_batch_output(batch_summary, args.output, args.format)

    # Print summary
    summary = batch_summary["summary_statistics"]
    priority_dist = batch_summary.get("priority_distribution", {})
    print(f"\n📈 Batch Analysis Summary")
    print(
        f"   Sessions: {summary['successful_analyses']}/{summary['total_sessions']} analyzed"
    )
    print(f"   Average score: {summary['average_optimization_score']:.1f}/100")
    print(f"   Total potential savings: ${summary['total_potential_savings']:.2f}")
    print(f"   High priority sessions: {priority_dist.get('high_priority', 0)}")
    print(f"   Processing time: {summary['total_processing_time_seconds']:.2f}s")
    print(f"   Results saved to: {args.output}")

    return 0


def command_dashboard(args, reporter: SizeReporter):
    """Handle dashboard command"""
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        return 1

    print(f"📊 Generating dashboard for: {args.input_dir}")

    # Find session files
    session_files = list(args.input_dir.glob("*.jsonl"))
    if not session_files:
        print(f"❌ No .jsonl files found in {args.input_dir}")
        return 1

    print(f"   Analyzing {len(session_files)} sessions...")

    # Analyze all sessions
    start_time = time.time()
    results = []

    for i, session_file in enumerate(session_files, 1):
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(session_files)}")

        try:
            result = analyze_single_session(session_file, reporter, True, False)
            if "error" not in result:
                results.append(result)
        except Exception as e:
            print(f"   ⚠️  Skipped {session_file.name}: {e}")

    end_time = time.time()

    if not results:
        print(f"❌ No sessions could be analyzed")
        return 1

    # Generate dashboard data
    dashboard_data = generate_dashboard_data(results, args, end_time - start_time)

    # Generate HTML dashboard
    generate_html_dashboard(dashboard_data, args.output)

    print(f"✅ Dashboard generated: {args.output}")
    print(f"   Sessions analyzed: {len(results)}")
    print(f"   Processing time: {end_time - start_time:.2f}s")

    return 0


def command_compare(args, reporter: SizeReporter):
    """Handle compare command"""
    # Validate session files
    valid_files = []
    for session_file in args.session_files:
        if session_file.exists():
            valid_files.append(session_file)
        else:
            print(f"⚠️  File not found: {session_file}")

    if not valid_files:
        print(f"❌ No valid session files found")
        return 1

    print(f"🔄 Comparing {len(valid_files)} sessions")

    # Analyze all sessions
    results = []
    for session_file in valid_files:
        analysis = analyze_single_session(session_file, reporter, True, False)
        if "error" not in analysis:
            results.append(analysis)
        else:
            print(f"   ⚠️  Failed to analyze {session_file.name}: {analysis['error']}")

    if not results:
        print(f"❌ No sessions could be analyzed")
        return 1

    # Generate comparison
    comparison_data = generate_comparison_data(results, args.sort_by)

    # Output results
    if args.output:
        save_analysis_output(comparison_data, args.output, args.format)
        print(f"💾 Comparison saved to: {args.output}")
    else:
        print_comparison_output(comparison_data, args.format)

    return 0


def command_summary(args, reporter: SizeReporter):
    """Handle summary command"""
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        return 1

    # Quick analysis for summary
    session_files = list(args.input_dir.glob("*.jsonl"))
    if not session_files:
        print(f"❌ No .jsonl files found in {args.input_dir}")
        return 1

    print(f"📋 Generating summary for {len(session_files)} sessions")

    # Quick analysis (tokens only)
    summary_data = {
        "summary_metadata": {
            "directory": str(args.input_dir),
            "generation_timestamp": datetime.now().isoformat(),
            "total_files_found": len(session_files),
        },
        "size_distribution": {},
        "total_tokens": 0,
        "total_estimated_cost": 0.0,
        "high_priority_sessions": [],
    }

    size_counts = defaultdict(int)

    for session_file in session_files:
        try:
            converted = reporter.gpt5_system.format_adapter.convert_session_file(
                session_file
            )
            if converted:
                token_analysis = (
                    reporter.gpt5_system.token_analyzer.analyze_session_tokens(
                        converted
                    )
                )
                tokens = token_analysis.total_tokens
                size_category = categorize_session_size(tokens)

                size_counts[size_category] += 1
                summary_data["total_tokens"] += tokens
                summary_data["total_estimated_cost"] += (tokens / 1000) * 0.025

                # Track high priority sessions
                if size_category in ["large", "extra_large"]:
                    score = calculate_optimization_score(tokens)
                    summary_data["high_priority_sessions"].append(
                        {
                            "file": session_file.name,
                            "tokens": tokens,
                            "category": size_category,
                            "score": score,
                        }
                    )
        except:
            continue

    summary_data["size_distribution"] = dict(size_counts)
    summary_data["high_priority_sessions"].sort(key=lambda x: x["score"], reverse=True)
    summary_data["high_priority_sessions"] = summary_data["high_priority_sessions"][:10]

    # Output summary
    if args.output:
        save_analysis_output(summary_data, args.output, args.format)
        print(f"💾 Summary saved to: {args.output}")
    else:
        print_summary_output(summary_data, args.format)

    return 0


def generate_batch_summary(
    results: List[Dict[str, Any]], processing_time: float
) -> Dict[str, Any]:
    """Generate comprehensive batch summary"""
    successful_results = [r for r in results if "error" not in r]
    failed_results = [r for r in results if "error" in r]

    if not successful_results:
        return {
            "summary_statistics": {
                "total_sessions": len(results),
                "successful_analyses": 0,
                "failed_analyses": len(failed_results),
                "success_rate_percent": 0.0,
            },
            "results": results,
        }

    # Calculate statistics
    total_tokens = sum(r["size_analysis"]["total_tokens"] for r in successful_results)
    total_cost = sum(r["cost_analysis"]["current_cost"] for r in successful_results)
    total_potential_savings = sum(
        r["optimization_analysis"]["cost_savings"] for r in successful_results
    )

    optimization_scores = [
        r["optimization_analysis"]["optimization_score"] for r in successful_results
    ]
    avg_score = statistics.mean(optimization_scores)

    # Size distribution
    size_distribution = defaultdict(int)
    for result in successful_results:
        category = result["size_analysis"]["size_category"]
        size_distribution[category] += 1

    # Priority categorization
    high_priority = len(
        [
            r
            for r in successful_results
            if r["optimization_analysis"]["optimization_score"] >= 70
        ]
    )
    medium_priority = len(
        [
            r
            for r in successful_results
            if 40 <= r["optimization_analysis"]["optimization_score"] < 70
        ]
    )
    low_priority = len(
        [
            r
            for r in successful_results
            if r["optimization_analysis"]["optimization_score"] < 40
        ]
    )

    # Top sessions for optimization
    top_sessions = sorted(
        successful_results,
        key=lambda x: x["optimization_analysis"]["optimization_score"],
        reverse=True,
    )[:10]

    return {
        "batch_analysis_metadata": {
            "generation_timestamp": datetime.now().isoformat(),
            "total_processing_time_seconds": processing_time,
            "analysis_includes_sessionanalytics": any(
                "session_analytics" in r for r in successful_results
            ),
        },
        "summary_statistics": {
            "total_sessions": len(results),
            "successful_analyses": len(successful_results),
            "failed_analyses": len(failed_results),
            "success_rate_percent": len(successful_results) / len(results) * 100,
            "total_tokens_analyzed": total_tokens,
            "total_current_cost": total_cost,
            "total_potential_savings": total_potential_savings,
            "potential_savings_percent": (total_potential_savings / total_cost * 100)
            if total_cost > 0
            else 0,
            "average_optimization_score": avg_score,
            "total_processing_time_seconds": processing_time,
        },
        "size_category_distribution": dict(size_distribution),
        "priority_distribution": {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
        },
        "top_optimization_candidates": [
            {
                "session_file": r["session_file"],
                "optimization_score": r["optimization_analysis"]["optimization_score"],
                "tokens": r["size_analysis"]["total_tokens"],
                "potential_savings": r["optimization_analysis"]["cost_savings"],
                "size_category": r["size_analysis"]["size_category"],
            }
            for r in top_sessions
        ],
        "failed_analyses": [
            {"session_file": r["session_file"], "error": r["error"]}
            for r in failed_results
        ],
        "detailed_results": successful_results,
    }


def generate_dashboard_data(
    results: List[Dict[str, Any]], args, processing_time: float
) -> Dict[str, Any]:
    """Generate comprehensive dashboard data"""
    # Basic statistics
    total_tokens = sum(r["size_analysis"]["total_tokens"] for r in results)
    total_cost = sum(r["cost_analysis"]["current_cost"] for r in results)
    total_savings = sum(r["optimization_analysis"]["cost_savings"] for r in results)

    optimization_scores = [
        r["optimization_analysis"]["optimization_score"] for r in results
    ]
    avg_score = statistics.mean(optimization_scores)

    # Size distribution
    size_distribution = defaultdict(int)
    for result in results:
        category = result["size_analysis"]["size_category"]
        size_distribution[category] += 1

    # Score distribution
    score_distribution = {
        "excellent": len([s for s in optimization_scores if s >= 80]),
        "good": len([s for s in optimization_scores if 60 <= s < 80]),
        "fair": len([s for s in optimization_scores if 40 <= s < 60]),
        "poor": len([s for s in optimization_scores if s < 40]),
    }

    # Top sessions by different metrics
    top_by_score = sorted(
        results,
        key=lambda x: x["optimization_analysis"]["optimization_score"],
        reverse=True,
    )[: args.top_sessions]
    top_by_size = sorted(
        results, key=lambda x: x["size_analysis"]["total_tokens"], reverse=True
    )[: args.top_sessions]
    top_by_savings = sorted(
        results, key=lambda x: x["optimization_analysis"]["cost_savings"], reverse=True
    )[: args.top_sessions]

    # Trends analysis (if requested)
    trends = {}
    if args.include_trends:
        # Sort by file modification time or creation time
        try:
            sorted_results = sorted(
                results, key=lambda x: Path(x["session_file"]).stat().st_mtime
            )

            # Calculate rolling averages
            window_size = min(10, len(sorted_results) // 4)
            if window_size > 1:
                rolling_scores = []
                rolling_tokens = []

                for i in range(len(sorted_results) - window_size + 1):
                    window = sorted_results[i : i + window_size]
                    avg_score = statistics.mean(
                        r["optimization_analysis"]["optimization_score"] for r in window
                    )
                    avg_tokens = statistics.mean(
                        r["size_analysis"]["total_tokens"] for r in window
                    )

                    rolling_scores.append(avg_score)
                    rolling_tokens.append(avg_tokens)

                trends = {
                    "rolling_optimization_scores": rolling_scores,
                    "rolling_token_counts": rolling_tokens,
                    "trend_direction": "improving"
                    if rolling_scores[-1] > rolling_scores[0]
                    else "declining",
                }
        except:
            trends = {"error": "Could not calculate trends"}

    return {
        "dashboard_metadata": {
            "generation_timestamp": datetime.now().isoformat(),
            "source_directory": str(args.input_dir),
            "total_sessions_analyzed": len(results),
            "processing_time_seconds": processing_time,
            "includes_real_time": args.real_time,
            "includes_trends": args.include_trends,
        },
        "overview_statistics": {
            "total_sessions": len(results),
            "total_tokens": total_tokens,
            "average_tokens_per_session": total_tokens / len(results),
            "total_current_cost": total_cost,
            "total_potential_savings": total_savings,
            "savings_percentage": (total_savings / total_cost * 100)
            if total_cost > 0
            else 0,
            "average_optimization_score": avg_score,
            "roi_potential": f"{(total_savings / total_cost * 100):.1f}%"
            if total_cost > 0
            else "0%",
        },
        "distributions": {
            "size_categories": dict(size_distribution),
            "optimization_scores": score_distribution,
        },
        "top_sessions": {
            "by_optimization_score": [
                {
                    "session_file": r["session_file"],
                    "score": r["optimization_analysis"]["optimization_score"],
                    "tokens": r["size_analysis"]["total_tokens"],
                    "category": r["size_analysis"]["size_category"],
                    "savings": r["optimization_analysis"]["cost_savings"],
                }
                for r in top_by_score
            ],
            "by_size": [
                {
                    "session_file": r["session_file"],
                    "tokens": r["size_analysis"]["total_tokens"],
                    "category": r["size_analysis"]["size_category"],
                    "score": r["optimization_analysis"]["optimization_score"],
                }
                for r in top_by_size
            ],
            "by_savings_potential": [
                {
                    "session_file": r["session_file"],
                    "savings": r["optimization_analysis"]["cost_savings"],
                    "tokens": r["size_analysis"]["total_tokens"],
                    "score": r["optimization_analysis"]["optimization_score"],
                }
                for r in top_by_savings
            ],
        },
        "trends": trends,
        "recommendations": generate_dashboard_recommendations(
            results, size_distribution, avg_score
        ),
    }


def generate_comparison_data(
    results: List[Dict[str, Any]], sort_by: str
) -> Dict[str, Any]:
    """Generate session comparison data"""
    # Sort results by specified metric
    sort_keys = {
        "size": lambda x: x["size_analysis"]["total_tokens"],
        "score": lambda x: x["optimization_analysis"]["optimization_score"],
        "cost": lambda x: x["cost_analysis"]["current_cost"],
        "compression": lambda x: x["optimization_analysis"]["savings_percent"],
    }

    if sort_by in sort_keys:
        results.sort(key=sort_keys[sort_by], reverse=True)

    return {
        "comparison_metadata": {
            "generation_timestamp": datetime.now().isoformat(),
            "sessions_compared": len(results),
            "sorted_by": sort_by,
        },
        "comparison_summary": {
            "total_tokens": sum(r["size_analysis"]["total_tokens"] for r in results),
            "total_cost": sum(r["cost_analysis"]["current_cost"] for r in results),
            "total_potential_savings": sum(
                r["optimization_analysis"]["cost_savings"] for r in results
            ),
            "average_optimization_score": statistics.mean(
                r["optimization_analysis"]["optimization_score"] for r in results
            ),
        },
        "session_comparisons": [
            {
                "session_file": r["session_file"],
                "tokens": r["size_analysis"]["total_tokens"],
                "size_category": r["size_analysis"]["size_category"],
                "current_cost": r["cost_analysis"]["current_cost"],
                "optimization_score": r["optimization_analysis"]["optimization_score"],
                "potential_savings": r["optimization_analysis"]["cost_savings"],
                "savings_percent": r["optimization_analysis"]["savings_percent"],
                "recommended_actions": r["optimization_analysis"][
                    "recommended_actions"
                ][:3],
            }
            for r in results
        ],
    }


def generate_dashboard_recommendations(
    results: List[Dict[str, Any]], size_distribution: Dict[str, int], avg_score: float
) -> List[str]:
    """Generate dashboard recommendations"""
    recommendations = []

    total_sessions = len(results)
    critical_sessions = size_distribution.get("extra_large", 0)
    high_priority_sessions = size_distribution.get("large", 0)

    # Critical recommendations
    if critical_sessions > 0:
        recommendations.append(
            f"🚨 URGENT: {critical_sessions} sessions exceed GPT-5 limits - implement optimization immediately"
        )

    if high_priority_sessions > 0:
        recommendations.append(
            f"⚠️  HIGH PRIORITY: {high_priority_sessions} large sessions have significant optimization potential"
        )

    # Score-based recommendations
    if avg_score > 70:
        recommendations.append(
            "✅ Excellent optimization opportunity - deploy system-wide optimization"
        )
    elif avg_score > 50:
        recommendations.append(
            "💡 Good optimization potential - prioritize high-scoring sessions"
        )
    elif avg_score > 30:
        recommendations.append(
            "📊 Moderate optimization potential - focus on largest sessions first"
        )
    else:
        recommendations.append(
            "📝 Low optimization scores - review session patterns for efficiency"
        )

    # Cost-based recommendations
    total_cost = sum(r["cost_analysis"]["current_cost"] for r in results)
    total_savings = sum(r["optimization_analysis"]["cost_savings"] for r in results)

    if total_savings > 100:
        recommendations.append(
            f"💰 Major cost savings potential: ${total_savings:.2f} total savings available"
        )
    elif total_savings > 20:
        recommendations.append(
            f"💵 Significant savings available: ${total_savings:.2f} through optimization"
        )

    # Pattern-based recommendations
    high_score_sessions = len(
        [r for r in results if r["optimization_analysis"]["optimization_score"] >= 70]
    )
    if high_score_sessions > total_sessions * 0.3:
        recommendations.append(
            "📈 30%+ of sessions are high-priority - consider batch optimization strategy"
        )

    return recommendations


def save_analysis_output(data: Dict[str, Any], output_path: Path, format_type: str):
    """Save analysis output to file"""
    if format_type == "json":
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    elif format_type == "html":
        generate_analysis_html(data, output_path)
    elif format_type == "text":
        with open(output_path, "w") as f:
            f.write(format_analysis_text(data))


def save_batch_output(data: Dict[str, Any], output_path: Path, format_type: str):
    """Save batch output to file"""
    if format_type == "json":
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    elif format_type == "html":
        generate_batch_html(data, output_path)
    elif format_type == "csv":
        generate_batch_csv(data, output_path)


def print_analysis_output(
    data: Dict[str, Any], format_type: str, verbose: bool = False
):
    """Print analysis output to console"""
    if format_type == "json":
        print(json.dumps(data, indent=2, default=str))
    elif format_type == "text":
        print(format_analysis_text(data, verbose))
    elif format_type == "html":
        print("HTML format requires --output file specification")


def print_comparison_output(data: Dict[str, Any], format_type: str):
    """Print comparison output to console"""
    if format_type == "table":
        print(
            f"\n🔍 Session Comparison Results (sorted by {data['comparison_metadata']['sorted_by']}):"
        )
        print(
            f"{'Session':<25} {'Tokens':<10} {'Category':<12} {'Score':<8} {'Savings':<10} {'Cost':<10}"
        )
        print("-" * 85)

        for session in data["session_comparisons"]:
            print(
                f"{session['session_file'][:24]:<25} {session['tokens']:<10,} "
                f"{session['size_category']:<12} {session['optimization_score']:<8.1f} "
                f"{session['savings_percent']:<9.1f}% ${session['current_cost']:<9.4f}"
            )

        summary = data["comparison_summary"]
        print(
            f"\n📊 Summary: {data['comparison_metadata']['sessions_compared']} sessions"
        )
        print(f"   Total tokens: {summary['total_tokens']:,}")
        print(f"   Total cost: ${summary['total_cost']:.2f}")
        print(f"   Potential savings: ${summary['total_potential_savings']:.2f}")
        print(f"   Average score: {summary['average_optimization_score']:.1f}/100")
    else:
        print(json.dumps(data, indent=2, default=str))


def print_summary_output(data: Dict[str, Any], format_type: str):
    """Print summary output to console"""
    if format_type == "text":
        print(f"\n📋 Session Size Summary")
        print(f"   Directory: {data['summary_metadata']['directory']}")
        print(f"   Files found: {data['summary_metadata']['total_files_found']}")
        print(f"   Total tokens: {data['total_tokens']:,}")
        print(f"   Estimated cost: ${data['total_estimated_cost']:.2f}")

        print(f"\n📊 Size Distribution:")
        for category, count in data["size_distribution"].items():
            print(f"   {category.replace('_', ' ').title()}: {count} sessions")

        if data["high_priority_sessions"]:
            print(f"\n🎯 Top High-Priority Sessions:")
            for session in data["high_priority_sessions"][:5]:
                print(
                    f"   {session['file']}: {session['tokens']:,} tokens (score: {session['score']:.1f})"
                )
    else:
        print(json.dumps(data, indent=2, default=str))


def format_analysis_text(data: Dict[str, Any], verbose: bool = False) -> str:
    """Format analysis data as readable text"""
    output = []

    if "size_analysis" in data:
        size = data["size_analysis"]
        output.append(f"📏 Size Analysis:")
        output.append(f"  Total Tokens: {size['total_tokens']:,}")
        output.append(
            f"  Size Category: {size['size_category_info']['name']} ({size['size_category_info']['range']})"
        )
        output.append(
            f"  Optimization Potential: {size['optimization_potential_percent']:.1f}%"
        )
        output.append("")

    if "cost_analysis" in data:
        cost = data["cost_analysis"]
        output.append(f"💰 Cost Analysis:")
        output.append(f"  Current Cost: ${cost['current_cost']:.4f}")
        output.append(f"  Input Cost: ${cost['input_cost']:.4f}")
        output.append(f"  Output Cost: ${cost['output_cost']:.4f}")
        output.append(f"  Cost per Interaction: ${cost['cost_per_interaction']:.6f}")
        output.append(
            f"  Potential Savings: ${cost['optimization_savings']:.4f} ({cost['potential_savings_percent']:.1f}%)"
        )
        output.append("")

    if "optimization_analysis" in data:
        opt = data["optimization_analysis"]
        output.append(f"🎯 Optimization Analysis:")
        output.append(f"  Optimization Score: {opt['optimization_score']:.1f}/100")
        output.append(
            f"  Cost Savings: ${opt['cost_savings']:.4f} ({opt['savings_percent']:.1f}%)"
        )
        output.append(f"  Quality Impact: {opt['quality_impact']}")

        if verbose and opt["recommended_actions"]:
            output.append(f"  Recommendations:")
            for action in opt["recommended_actions"][:3]:
                output.append(f"    • {action}")
        output.append("")

    if verbose and "session_analytics" in data:
        analytics = data["session_analytics"]
        output.append(f"📊 Session Analytics:")
        output.append(
            f"  Conversation Length: {analytics['conversation_flow']['conversation_length']} messages"
        )
        output.append(f"  Tool Calls: {analytics['tool_usage']['total_tool_calls']}")
        output.append(f"  Unique Tools: {analytics['tool_usage']['unique_tools']}")
        output.append(
            f"  File Operations: {sum(analytics['file_operations']['operation_counts'].values())}"
        )
        output.append(f"  Complexity: {analytics['complexity_rating']}")
        output.append("")

    return "\n".join(output)


def generate_analysis_html(data: Dict[str, Any], output_path: Path):
    """Generate HTML report for single analysis"""
    size_analysis = data.get("size_analysis", {})
    cost_analysis = data.get("cost_analysis", {})
    opt_analysis = data.get("optimization_analysis", {})

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Session Size Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 30px; }}
        .section {{ margin: 25px 0; padding: 20px; border-left: 4px solid #3498db; background-color: #f8f9fa; border-radius: 5px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }}
        .metric {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-label {{ font-size: 14px; color: #666; margin-bottom: 5px; }}
        .metric-value {{ font-size: 20px; font-weight: bold; color: #2c3e50; }}
        .score {{ font-size: 32px; font-weight: bold; }}
        .score.excellent {{ color: #27ae60; }}
        .score.good {{ color: #f39c12; }}
        .score.fair {{ color: #e67e22; }}
        .score.poor {{ color: #e74c3c; }}
        .category-badge {{ display: inline-block; padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; }}
        .small {{ background-color: #95a5a6; }}
        .medium {{ background-color: #3498db; }}
        .large {{ background-color: #f39c12; }}
        .extra_large {{ background-color: #e74c3c; }}
        .recommendations {{ background-color: #fff3cd; border-left-color: #ffc107; }}
        .recommendations ul {{ padding-left: 20px; }}
        .timestamp {{ color: #666; font-size: 12px; text-align: right; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1 class="header">📊 Session Size Analysis Report</h1>

    <div class="section">
        <h2>Session Overview</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Session File</div>
                <div class="metric-value">{html.escape(data.get('session_file', 'N/A'))}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Tokens</div>
                <div class="metric-value">{size_analysis.get('total_tokens', 0):,}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Size Category</div>
                <div class="metric-value">
                    <span class="category-badge {size_analysis.get('size_category', 'small')}">
                        {size_analysis.get('size_category_info', {}).get('name', 'Unknown')}
                    </span>
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Optimization Score</div>
                <div class="metric-value">
                    <span class="score {'excellent' if opt_analysis.get('optimization_score', 0) >= 80 else 'good' if opt_analysis.get('optimization_score', 0) >= 60 else 'fair' if opt_analysis.get('optimization_score', 0) >= 40 else 'poor'}">
                        {opt_analysis.get('optimization_score', 0):.1f}/100
                    </span>
                </div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>💰 Cost Analysis</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Current Cost</div>
                <div class="metric-value">${cost_analysis.get('current_cost', 0):.4f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Potential Savings</div>
                <div class="metric-value">${opt_analysis.get('cost_savings', 0):.4f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Savings Percentage</div>
                <div class="metric-value">{opt_analysis.get('savings_percent', 0):.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Quality Impact</div>
                <div class="metric-value">{opt_analysis.get('quality_impact', 'Unknown')}</div>
            </div>
        </div>
    </div>
"""

    # Add recommendations if available
    if opt_analysis.get("recommended_actions"):
        html_content += f"""
    <div class="section recommendations">
        <h2>💡 Optimization Recommendations</h2>
        <ul>
"""
        for action in opt_analysis["recommended_actions"][:5]:
            html_content += f"            <li>{html.escape(action)}</li>\n"

        html_content += """        </ul>
    </div>
"""

    # Add session analytics if available
    if "session_analytics" in data:
        analytics = data["session_analytics"]
        html_content += f"""
    <div class="section">
        <h2>📊 Detailed Analytics</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Conversation Length</div>
                <div class="metric-value">{analytics['conversation_flow']['conversation_length']} messages</div>
            </div>
            <div class="metric">
                <div class="metric-label">Tool Calls</div>
                <div class="metric-value">{analytics['tool_usage']['total_tool_calls']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">File Operations</div>
                <div class="metric-value">{sum(analytics['file_operations']['operation_counts'].values())}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Complexity Rating</div>
                <div class="metric-value">{analytics['complexity_rating']}</div>
            </div>
        </div>
    </div>
"""

    html_content += f"""
    <div class="timestamp">
        Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
    </div>

</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html_content)


def generate_batch_html(data: Dict[str, Any], output_path: Path):
    """Generate HTML report for batch analysis"""
    summary = data["summary_statistics"]

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Batch Size Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .header {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 15px; margin-bottom: 30px; }}
        .section {{ margin: 25px 0; padding: 20px; border-left: 4px solid #3498db; background-color: #f8f9fa; border-radius: 5px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }}
        .metric {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-label {{ font-size: 14px; color: #666; margin-bottom: 5px; }}
        .metric-value {{ font-size: 20px; font-weight: bold; color: #2c3e50; }}
        .table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        .table th {{ background-color: #3498db; color: white; }}
        .table tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .error {{ color: #e74c3c; font-weight: bold; }}
        .chart-container {{ margin: 20px 0; }}
        .bar {{ display: inline-block; height: 20px; background-color: #3498db; margin: 2px 0; }}
        .timestamp {{ color: #666; font-size: 12px; text-align: right; margin-top: 30px; }}
    </style>
</head>
<body>
    <h1 class="header">📊 Batch Size Analysis Report</h1>

    <div class="section">
        <h2>Summary Statistics</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Total Sessions</div>
                <div class="metric-value">{summary['total_sessions']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value success">{summary['success_rate_percent']:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Tokens</div>
                <div class="metric-value">{summary['total_tokens_analyzed']:,}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{summary['average_optimization_score']:.1f}/100</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Savings</div>
                <div class="metric-value">${summary['total_potential_savings']:.2f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Processing Time</div>
                <div class="metric-value">{summary['total_processing_time_seconds']:.2f}s</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Size Category Distribution</h2>
        <table class="table">
            <tr><th>Category</th><th>Sessions</th><th>Percentage</th></tr>
"""

    size_dist = data.get("size_category_distribution", {})
    total_sessions = summary["successful_analyses"]

    for category, count in size_dist.items():
        percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
        html_content += f"""            <tr>
                <td>{category.replace('_', ' ').title()}</td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
"""

    html_content += """        </table>
    </div>

    <div class="section">
        <h2>🎯 Top Optimization Candidates</h2>
        <table class="table">
            <tr><th>Session</th><th>Score</th><th>Tokens</th><th>Category</th><th>Potential Savings</th></tr>
"""

    top_candidates = data.get("top_optimization_candidates", [])
    for candidate in top_candidates[:10]:
        score_class = (
            "success"
            if candidate["optimization_score"] >= 70
            else "warning"
            if candidate["optimization_score"] >= 50
            else "error"
        )
        html_content += f"""            <tr>
                <td>{html.escape(candidate['session_file'])}</td>
                <td><span class="{score_class}">{candidate['optimization_score']:.1f}</span></td>
                <td>{candidate['tokens']:,}</td>
                <td>{candidate['size_category'].replace('_', ' ').title()}</td>
                <td>${candidate['potential_savings']:.4f}</td>
            </tr>
"""

    html_content += f"""        </table>
    </div>

    <div class="timestamp">
        Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
    </div>

</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html_content)


def generate_batch_csv(data: Dict[str, Any], output_path: Path):
    """Generate CSV report for batch analysis"""
    import csv

    detailed_results = data.get("detailed_results", [])

    with open(output_path, "w", newline="") as csvfile:
        fieldnames = [
            "session_file",
            "session_id",
            "total_tokens",
            "size_category",
            "optimization_score",
            "current_cost",
            "potential_savings",
            "savings_percent",
            "quality_impact",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for result in detailed_results:
            writer.writerow(
                {
                    "session_file": result["session_file"],
                    "session_id": result["session_id"],
                    "total_tokens": result["size_analysis"]["total_tokens"],
                    "size_category": result["size_analysis"]["size_category"],
                    "optimization_score": result["optimization_analysis"][
                        "optimization_score"
                    ],
                    "current_cost": result["cost_analysis"]["current_cost"],
                    "potential_savings": result["optimization_analysis"][
                        "cost_savings"
                    ],
                    "savings_percent": result["optimization_analysis"][
                        "savings_percent"
                    ],
                    "quality_impact": result["optimization_analysis"]["quality_impact"],
                }
            )


def generate_html_dashboard(data: Dict[str, Any], output_path: Path):
    """Generate comprehensive HTML dashboard"""
    overview = data["overview_statistics"]
    distributions = data["distributions"]

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Session Size Analysis Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.9; }}
        .section {{ background: white; padding: 25px; margin-bottom: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .metric-card.blue {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .metric-card.green {{ background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }}
        .metric-card.orange {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }}
        .metric-card.purple {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333; }}
        .metric-label {{ font-size: 14px; opacity: 0.9; margin-bottom: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .chart-container {{ margin: 20px 0; }}
        .chart-bar {{ display: flex; align-items: center; margin: 10px 0; }}
        .chart-label {{ width: 120px; font-weight: bold; }}
        .chart-bar-fill {{ height: 25px; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 5px; margin: 0 10px; position: relative; }}
        .chart-bar-text {{ color: white; line-height: 25px; padding: 0 10px; }}
        .table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        .table th, .table td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        .table th {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .table tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .recommendations {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); }}
        .recommendations ul {{ margin: 10px 0; padding-left: 20px; }}
        .timestamp {{ text-align: center; color: #666; margin-top: 30px; font-size: 12px; }}
        .score {{ font-weight: bold; }}
        .score.excellent {{ color: #27ae60; }}
        .score.good {{ color: #f39c12; }}
        .score.fair {{ color: #e67e22; }}
        .score.poor {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>📊 Session Size Analysis Dashboard</h1>
            <p>Comprehensive analysis of {overview['total_sessions']} sessions • Generated {data['dashboard_metadata']['generation_timestamp'][:19]}</p>
        </div>

        <div class="metric-grid">
            <div class="metric-card blue">
                <div class="metric-label">Total Sessions</div>
                <div class="metric-value">{overview['total_sessions']}</div>
            </div>
            <div class="metric-card green">
                <div class="metric-label">Total Tokens</div>
                <div class="metric-value">{overview['total_tokens']:,}</div>
            </div>
            <div class="metric-card orange">
                <div class="metric-label">Potential Savings</div>
                <div class="metric-value">${overview['total_potential_savings']:.2f}</div>
            </div>
            <div class="metric-card purple">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{overview['average_optimization_score']:.1f}/100</div>
            </div>
        </div>

        <div class="section">
            <h2>💰 Cost Analysis Overview</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">Current Total Cost</div>
                    <div class="metric-value">${overview['total_current_cost']:.2f}</div>
                </div>
                <div class="metric-card blue">
                    <div class="metric-label">Savings Percentage</div>
                    <div class="metric-value">{overview['savings_percentage']:.1f}%</div>
                </div>
                <div class="metric-card green">
                    <div class="metric-label">ROI Potential</div>
                    <div class="metric-value">{overview['roi_potential']}</div>
                </div>
                <div class="metric-card orange">
                    <div class="metric-label">Avg Tokens/Session</div>
                    <div class="metric-value">{overview['average_tokens_per_session']:,.0f}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Size Category Distribution</h2>
            <div class="chart-container">
"""

    # Add size distribution chart
    size_categories = distributions["size_categories"]
    total_sessions = sum(size_categories.values())
    max_count = max(size_categories.values()) if size_categories else 1

    for category, count in size_categories.items():
        percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
        bar_width = (count / max_count * 300) if max_count > 0 else 0

        html_content += f"""
                <div class="chart-bar">
                    <div class="chart-label">{category.replace('_', ' ').title()}</div>
                    <div class="chart-bar-fill" style="width: {bar_width}px;">
                        <div class="chart-bar-text">{count} ({percentage:.1f}%)</div>
                    </div>
                </div>
"""

    html_content += """
            </div>
        </div>

        <div class="section">
            <h2>🎯 Optimization Score Distribution</h2>
            <div class="chart-container">
"""

    # Add score distribution chart
    score_dist = distributions["optimization_scores"]
    max_score_count = max(score_dist.values()) if score_dist else 1

    score_labels = {
        "excellent": "Excellent (80-100)",
        "good": "Good (60-79)",
        "fair": "Fair (40-59)",
        "poor": "Poor (0-39)",
    }

    for score_range, count in score_dist.items():
        percentage = (count / total_sessions * 100) if total_sessions > 0 else 0
        bar_width = (count / max_score_count * 300) if max_score_count > 0 else 0

        html_content += f"""
                <div class="chart-bar">
                    <div class="chart-label">{score_labels.get(score_range, score_range)}</div>
                    <div class="chart-bar-fill" style="width: {bar_width}px;">
                        <div class="chart-bar-text">{count} ({percentage:.1f}%)</div>
                    </div>
                </div>
"""

    html_content += """
            </div>
        </div>

        <div class="section">
            <h2>🏆 Top Sessions by Optimization Score</h2>
            <table class="table">
                <tr><th>Session</th><th>Score</th><th>Tokens</th><th>Category</th><th>Savings</th></tr>
"""

    # Add top sessions by score
    top_by_score = data["top_sessions"]["by_optimization_score"][:10]
    for session in top_by_score:
        score_class = (
            "excellent"
            if session["score"] >= 80
            else "good"
            if session["score"] >= 60
            else "fair"
            if session["score"] >= 40
            else "poor"
        )
        html_content += f"""
                <tr>
                    <td>{html.escape(session['session_file'][:40])}</td>
                    <td><span class="score {score_class}">{session['score']:.1f}</span></td>
                    <td>{session['tokens']:,}</td>
                    <td>{session['category'].replace('_', ' ').title()}</td>
                    <td>${session['savings']:.4f}</td>
                </tr>
"""

    html_content += """
            </table>
        </div>

        <div class="section recommendations">
            <h2>💡 Optimization Recommendations</h2>
            <ul>
"""

    # Add recommendations
    recommendations = data.get("recommendations", [])
    for recommendation in recommendations:
        html_content += f"                <li>{html.escape(recommendation)}</li>\n"

    html_content += f"""
            </ul>
        </div>

        <div class="timestamp">
            Dashboard generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")} • Processing time: {data['dashboard_metadata']['processing_time_seconds']:.2f}s
        </div>

    </div>
</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html_content)


def main():
    """Main CLI entry point"""
    parser = setup_argparse()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize reporter
    if not args.quiet:
        print("🔧 Initializing Size Reporter...")

    try:
        reporter = SizeReporter()
    except Exception as e:
        print(f"❌ Failed to initialize reporter: {e}")
        return 1

    # Route to command handlers
    try:
        if args.command == "analyze":
            return command_analyze(args, reporter)
        elif args.command == "batch":
            return command_batch(args, reporter)
        elif args.command == "dashboard":
            return command_dashboard(args, reporter)
        elif args.command == "compare":
            return command_compare(args, reporter)
        elif args.command == "summary":
            return command_summary(args, reporter)
        elif args.command == "monitor":
            # TODO: Implement monitoring functionality
            print("⚠️  Monitor command not yet implemented")
            return 1
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
