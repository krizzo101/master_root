#!/usr/bin/env python3
"""
Claude Session Analyzer - Production ready tool for analyzing Claude .jsonl session files
Using the Enhanced Claude Format Adapter with full SessionAnalyticsEngine integration.

This addresses the compatibility issue identified in Phase 1 testing by providing
robust .jsonl parsing that handles all Claude message types, tool calls, and system messages.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from enhanced_claude_format_adapter import (
    AdapterConfig,
    EnhancedClaudeFormatAdapter,
    create_enhanced_session_analytics_engine,
)


def analyze_claude_sessions(
    claude_dir: Path, output_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Analyze all Claude .jsonl sessions in a directory using the enhanced adapter.

    Args:
        claude_dir: Directory containing Claude .jsonl files
        output_file: Optional output file for results

    Returns:
        Analysis results dictionary
    """
    print(f"🔍 Analyzing Claude sessions in: {claude_dir}")

    # Find all .jsonl files
    jsonl_files = list(claude_dir.glob("**/*.jsonl"))
    if not jsonl_files:
        print(f"❌ No .jsonl files found in {claude_dir}")
        return {}

    print(f"📊 Found {len(jsonl_files)} session files")

    # Create enhanced analytics engine
    adapter = EnhancedClaudeFormatAdapter(
        AdapterConfig(preserve_all_metadata=True, extract_file_operations=True)
    )

    enhanced_engine = create_enhanced_session_analytics_engine(adapter)

    # Analyze sessions
    reports = []
    successful = 0
    failed = 0

    for i, jsonl_file in enumerate(jsonl_files, 1):
        try:
            print(f"  [{i}/{len(jsonl_files)}] Analyzing {jsonl_file.name}...")
            report = enhanced_engine.analyze_session(jsonl_file)

            # Extract key metrics
            session_data = {
                "session_id": report.session_context.session_id,
                "file_name": jsonl_file.name,
                "project_name": report.session_context.project_name,
                "working_directory": report.session_context.working_directory,
                "created_at": report.session_context.created_at.isoformat()
                if report.session_context.created_at
                else None,
                "ended_at": report.session_context.ended_at.isoformat()
                if report.session_context.ended_at
                else None,
                "conversation_metrics": {
                    "total_messages": report.conversation_flow.conversation_length,
                    "user_messages": report.conversation_flow.user_messages,
                    "assistant_messages": report.conversation_flow.assistant_messages,
                    "system_messages": report.conversation_flow.system_messages,
                    "avg_response_time": report.conversation_flow.avg_response_time,
                    "topic_shifts": report.conversation_flow.topic_shifts,
                    "patterns": report.conversation_flow.patterns,
                },
                "tool_usage": {
                    "total_tools": sum(report.tool_usage.tool_counts.values()),
                    "unique_tools": len(report.tool_usage.tool_counts),
                    "tool_categories": report.tool_usage.tool_categories,
                    "mcp_tools_used": list(report.tool_usage.mcp_tools_used),
                    "tool_success_rates": report.tool_usage.tool_success_rate,
                },
                "file_operations": {
                    "files_read": len(report.file_operations.files_read),
                    "files_written": len(report.file_operations.files_written),
                    "files_edited": len(report.file_operations.files_edited),
                    "file_hotspots": report.file_operations.file_hotspots,
                    "edit_patterns": report.file_operations.edit_patterns,
                },
                "optimization_metrics": {
                    "optimization_score": report.optimization_score,
                    "complexity_rating": report.complexity_rating,
                    "recommended_chunks": report.recommended_chunks,
                    "cost_estimate": report.cost_estimate,
                    "patterns_detected": report.patterns_detected,
                },
            }

            reports.append(session_data)
            successful += 1

        except Exception as e:
            print(f"    ❌ Failed to analyze {jsonl_file.name}: {e}")
            failed += 1
            continue

    # Generate summary
    summary = enhanced_engine.generate_summary_report(
        [
            type(
                "Report",
                (),
                {
                    "session_context": type("Context", (), r["session_id"])(),
                    "optimization_score": r["optimization_metrics"][
                        "optimization_score"
                    ],
                    "complexity_rating": r["optimization_metrics"]["complexity_rating"],
                    "cost_estimate": r["optimization_metrics"]["cost_estimate"],
                    "patterns_detected": r["optimization_metrics"]["patterns_detected"],
                    "tool_usage": type(
                        "ToolUsage",
                        (),
                        {
                            "tool_counts": {
                                k: v
                                for k, v in r["tool_usage"]
                                .get("tool_categories", {})
                                .items()
                            },
                            "mcp_tools_used": set(
                                r["tool_usage"].get("mcp_tools_used", [])
                            ),
                        },
                    )(),
                },
            )()
            for r in reports
        ]
    )

    # Build final results
    results = {
        "analysis_summary": {
            "total_files_processed": len(jsonl_files),
            "successful_analyses": successful,
            "failed_analyses": failed,
            "success_rate": (successful / len(jsonl_files) * 100) if jsonl_files else 0,
        },
        "aggregate_metrics": summary,
        "session_reports": reports,
        "enhancement_info": {
            "adapter_version": "2.0_enhanced",
            "sessionanalytics_compatible": True,
            "features_enabled": [
                "robust_jsonl_parsing",
                "comprehensive_tool_extraction",
                "claude_message_type_support",
                "enhanced_error_handling",
                "streaming_large_file_support",
            ],
        },
    }

    # Save results if output file specified
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Results saved to: {output_file}")

    print(f"\n✅ Analysis complete!")
    print(f"   Processed: {successful}/{len(jsonl_files)} files successfully")
    print(
        f"   Total messages analyzed: {sum(r['conversation_metrics']['total_messages'] for r in reports)}"
    )
    print(
        f"   Total tool calls extracted: {sum(r['tool_usage']['total_tools'] for r in reports)}"
    )

    return results


def demo_enhanced_features():
    """Demonstrate enhanced adapter features"""
    print("\n🚀 Enhanced Claude Format Adapter - Feature Demo")
    print("=" * 50)

    # Find Claude projects directory
    claude_projects = Path("/home/opsvi/.claude/projects")
    if not claude_projects.exists():
        print("❌ Claude projects directory not found")
        return

    # Get a sample file for demo
    sample_files = list(claude_projects.glob("**/*.jsonl"))[:1]
    if not sample_files:
        print("❌ No sample files found for demo")
        return

    sample_file = sample_files[0]
    print(f"🔍 Demo with: {sample_file.name}")

    # Create enhanced adapter
    adapter = EnhancedClaudeFormatAdapter(
        AdapterConfig(preserve_all_metadata=True, extract_file_operations=True)
    )

    # Demo 1: Direct MessageNode parsing
    print("\n📊 Demo 1: Direct MessageNode parsing")
    nodes = adapter.parse_session_file(sample_file)
    print(f"   Parsed {len(nodes)} MessageNode objects")

    if nodes:
        sample_node = nodes[0]
        print(f"   Sample node type: {sample_node.node_type}")
        print(f"   Sample node timestamp: {sample_node.timestamp}")
        print(f"   Sample node tool calls: {len(sample_node.tool_calls)}")

    # Demo 2: Enhanced session conversion
    print("\n🔄 Demo 2: Enhanced session conversion")
    enhanced_session = adapter.convert_session_file(sample_file)
    print(f"   Session ID: {enhanced_session['session_id']}")
    print(f"   Analytics ready: {enhanced_session['analytics_ready']}")
    print(f"   Message count: {len(enhanced_session['messages'])}")
    print(
        f"   Tool calls extracted: {enhanced_session['conversion_stats']['tool_calls_extracted']}"
    )

    # Demo 3: SessionAnalyticsEngine integration
    print("\n🔧 Demo 3: Enhanced SessionAnalyticsEngine")
    enhanced_engine = create_enhanced_session_analytics_engine(adapter)
    report = enhanced_engine.analyze_session(sample_file)

    print(f"   Session complexity: {report.complexity_rating}")
    print(f"   Optimization score: {report.optimization_score:.1f}")
    print(f"   Patterns detected: {', '.join(report.patterns_detected[:3])}")
    print(f"   Tool categories: {list(report.tool_usage.tool_categories.keys())}")

    print("\n✅ Demo complete - Enhanced adapter is fully functional!")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Analyze Claude .jsonl session files with enhanced format adapter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all Claude sessions
  python claude_session_analyzer.py /home/opsvi/.claude/projects

  # Save results to file
  python claude_session_analyzer.py /home/opsvi/.claude/projects -o results.json

  # Run demo
  python claude_session_analyzer.py --demo
        """,
    )

    parser.add_argument(
        "claude_dir",
        nargs="?",
        type=Path,
        help="Directory containing Claude .jsonl files",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output file for analysis results"
    )
    parser.add_argument("--demo", action="store_true", help="Run feature demonstration")

    args = parser.parse_args()

    if args.demo:
        demo_enhanced_features()
        return

    if not args.claude_dir:
        print("❌ Please specify Claude directory or use --demo")
        parser.print_help()
        return

    if not args.claude_dir.exists():
        print(f"❌ Directory not found: {args.claude_dir}")
        return

    # Run analysis
    results = analyze_claude_sessions(args.claude_dir, args.output)

    if results:
        print(f"\n📊 Quick Summary:")
        summary = results["analysis_summary"]
        print(f"   Success rate: {summary['success_rate']:.1f}%")
        print(
            f"   Files processed: {summary['successful_analyses']}/{summary['total_files_processed']}"
        )

        if "session_reports" in results and results["session_reports"]:
            avg_optimization = sum(
                r["optimization_metrics"]["optimization_score"]
                for r in results["session_reports"]
            ) / len(results["session_reports"])
            print(f"   Average optimization score: {avg_optimization:.1f}")


if __name__ == "__main__":
    main()
