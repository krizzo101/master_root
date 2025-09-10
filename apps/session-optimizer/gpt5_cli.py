#!/usr/bin/env python3
"""
GPT-5 Payload Generation CLI Tool
Command-line interface for the GPT-5 session optimization system.
Provides easy access to all optimization features with progress monitoring.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gpt5_payload_system import GPT5OptimizationConfig, GPT5PayloadSystem


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="GPT-5 Payload Generation System - Optimize Claude sessions for GPT-5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize single session
  python gpt5_cli.py optimize session.jsonl

  # Batch optimize all sessions in directory
  python gpt5_cli.py batch /path/to/sessions/ --output results/

  # Analyze large session with streaming
  python gpt5_cli.py stream large_session.jsonl

  # Compare chunking strategies
  python gpt5_cli.py compare session.jsonl

  # Get cost analysis
  python gpt5_cli.py analyze session.jsonl --cost-only

  # System status check
  python gpt5_cli.py status
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Optimize command
    optimize_parser = subparsers.add_parser(
        "optimize", help="Optimize single session file"
    )
    optimize_parser.add_argument(
        "session_file", type=Path, help="Claude .jsonl session file"
    )
    optimize_parser.add_argument(
        "--output", "-o", type=Path, help="Output directory for results"
    )
    optimize_parser.add_argument(
        "--strategy",
        choices=["conversation", "tool_usage", "adaptive"],
        default="adaptive",
        help="Chunking strategy (default: adaptive)",
    )
    optimize_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Batch command
    batch_parser = subparsers.add_parser(
        "batch", help="Batch optimize multiple sessions"
    )
    batch_parser.add_argument(
        "input_dir", type=Path, help="Directory containing .jsonl files"
    )
    batch_parser.add_argument(
        "--output", "-o", type=Path, help="Output directory for results"
    )
    batch_parser.add_argument(
        "--parallel", action="store_true", help="Enable parallel processing"
    )
    batch_parser.add_argument(
        "--pattern", default="*.jsonl", help="File pattern (default: *.jsonl)"
    )
    batch_parser.add_argument(
        "--max-workers", type=int, default=4, help="Max parallel workers"
    )

    # Stream command
    stream_parser = subparsers.add_parser("stream", help="Stream process large session")
    stream_parser.add_argument(
        "session_file", type=Path, help="Large Claude .jsonl session file"
    )
    stream_parser.add_argument(
        "--memory-limit", type=int, default=2048, help="Memory limit in MB"
    )
    stream_parser.add_argument(
        "--output", "-o", type=Path, help="Output directory for results"
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare", help="Compare chunking strategies"
    )
    compare_parser.add_argument(
        "session_file", type=Path, help="Claude .jsonl session file"
    )
    compare_parser.add_argument(
        "--output", "-o", type=Path, help="Output file for comparison"
    )

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze session cost and size"
    )
    analyze_parser.add_argument(
        "session_file", type=Path, help="Claude .jsonl session file"
    )
    analyze_parser.add_argument(
        "--cost-only", action="store_true", help="Show only cost analysis"
    )
    analyze_parser.add_argument(
        "--tokens-only", action="store_true", help="Show only token analysis"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed component status"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run system tests")
    test_parser.add_argument(
        "--benchmark", action="store_true", help="Run performance benchmarks"
    )
    test_parser.add_argument("--quick", action="store_true", help="Quick test only")

    # Global options
    parser.add_argument("--config", type=Path, help="Configuration file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")

    return parser


def load_config(config_path: Optional[Path]) -> GPT5OptimizationConfig:
    """Load configuration from file or use defaults"""
    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
            return GPT5OptimizationConfig(**config_data)
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
            print("Using default configuration")

    return GPT5OptimizationConfig()


def print_optimization_result(result, verbose: bool = False):
    """Print optimization result in formatted way"""
    if not result.success:
        print(f"❌ Optimization failed: {result.error_message}")
        return

    stats = result.processing_stats
    print(f"✅ Session {result.session_id} optimized successfully")
    print(
        f"   📊 {stats.get('original_tokens', 0):,} → {stats.get('optimized_tokens', 0):,} tokens"
    )
    print(
        f"   🗜️  {stats.get('compression_ratio', 1.0):.2f}x compression ({stats.get('strategy_used', 'unknown')})"
    )
    print(f"   💰 ${stats.get('cost_savings', 0.0):.4f} cost savings")
    print(f"   📦 {len(result.generated_payloads)} payloads generated")
    print(f"   ⏱️  {stats.get('processing_time_seconds', 0.0):.2f}s processing time")

    if verbose and result.optimization_analysis:
        opt = result.optimization_analysis
        print(f"   📈 Optimization score: {opt.optimization_score:.1f}/100")
        print(f"   🎯 Size category: {opt.size_category}")
        print(f"   💡 Savings potential: {opt.savings_percent:.1f}%")


def command_optimize(args, system: GPT5PayloadSystem):
    """Handle optimize command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    print(f"🚀 Optimizing session: {args.session_file.name}")

    start_time = time.time()
    result = system.optimize_session_file(args.session_file)
    end_time = time.time()

    print_optimization_result(result, args.verbose)

    # Save results if output directory specified
    if args.output and result.success:
        args.output.mkdir(parents=True, exist_ok=True)

        # Save optimization result
        result_file = args.output / f"{result.session_id}_optimization.json"
        result_data = {
            "session_id": result.session_id,
            "success": result.success,
            "processing_stats": result.processing_stats,
            "optimization_analysis": {
                "cost_savings": result.optimization_analysis.cost_savings,
                "savings_percent": result.optimization_analysis.savings_percent,
                "optimization_score": result.optimization_analysis.optimization_score,
                "size_category": result.optimization_analysis.size_category,
            }
            if result.optimization_analysis
            else None,
        }

        with open(result_file, "w") as f:
            json.dump(result_data, f, indent=2, default=str)

        # Save payloads
        if result.generated_payloads:
            payloads_file = args.output / f"{result.session_id}_payloads.json"
            payloads_data = [
                {
                    "payload": p.payload,
                    "estimated_tokens": p.estimated_tokens,
                    "compression_achieved": p.compression_achieved,
                    "payload_type": p.payload_type,
                    "quality_score": p.quality_score,
                }
                for p in result.generated_payloads
            ]

            with open(payloads_file, "w") as f:
                json.dump(payloads_data, f, indent=2, default=str)

        print(f"💾 Results saved to: {args.output}")

    return 0 if result.success else 1


def command_batch(args, system: GPT5PayloadSystem):
    """Handle batch command"""
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        return 1

    # Find session files
    session_files = list(args.input_dir.glob(args.pattern))
    if not session_files:
        print(f"❌ No files matching pattern '{args.pattern}' in {args.input_dir}")
        return 1

    print(f"🚀 Batch optimizing {len(session_files)} sessions...")
    if args.parallel:
        print(f"⚡ Using parallel processing with {args.max_workers} workers")

    # Update system config for batch processing
    system.config.enable_parallel_processing = args.parallel
    system.config.max_workers = args.max_workers

    start_time = time.time()
    batch_summary = system.batch_optimize_sessions(
        session_files, args.output, args.parallel
    )
    end_time = time.time()

    # Print summary
    summary = batch_summary["summary"]
    metrics = batch_summary["optimization_metrics"]

    print(f"\n📊 Batch Optimization Summary")
    print(
        f"   Sessions: {summary['successful_optimizations']}/{summary['total_sessions']} successful"
    )
    print(f"   Success rate: {summary['success_rate']:.1f}%")
    print(f"   Total time: {summary['total_processing_time_seconds']:.2f}s")
    print(f"   Average compression: {metrics['average_compression_ratio']:.2f}x")
    print(f"   Total cost savings: ${metrics['total_cost_savings']:.2f}")
    print(f"   Tokens processed: {metrics['total_original_tokens']:,}")
    print(f"   Payloads generated: {metrics['total_payloads_generated']}")

    if summary["failed_optimizations"] > 0:
        print(f"   ⚠️  {summary['failed_optimizations']} sessions failed")
        failed_sessions = batch_summary.get("failed_sessions", [])
        if failed_sessions:
            print(f"   Failed: {', '.join(failed_sessions[:5])}")

    performance = batch_summary["performance_analysis"]
    print(f"   Performance: {performance['tokens_per_second']:,} tokens/second")

    return 0 if summary["success_rate"] > 50 else 1


def command_stream(args, system: GPT5PayloadSystem):
    """Handle stream command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    file_size_mb = args.session_file.stat().st_size / (1024 * 1024)
    print(f"🌊 Streaming optimization: {args.session_file.name} ({file_size_mb:.1f}MB)")

    # Update memory limit
    system.config.memory_limit_mb = args.memory_limit

    chunk_count = 0
    total_tokens = 0
    total_payloads = 0

    start_time = time.time()

    try:
        for chunk_result in system.optimize_session_streaming(args.session_file):
            if chunk_result.get("is_final", False):
                # Final summary
                streaming_summary = chunk_result.get("streaming_summary", {})
                if streaming_summary.get("error_occurred"):
                    print(
                        f"❌ Streaming failed: {chunk_result.get('error', 'Unknown error')}"
                    )
                    return 1
                else:
                    total_tokens = streaming_summary.get(
                        "total_tokens_processed", total_tokens
                    )
                    chunk_count = streaming_summary.get(
                        "streaming_chunks_processed", chunk_count
                    )
                    print(f"\n✅ Streaming optimization complete")
                    break
            else:
                chunk_count += 1
                chunk_tokens = chunk_result.get("chunk_tokens", 0)
                payloads_count = chunk_result.get("payloads_generated", 0)
                compression = chunk_result.get("chunk_compression", 1.0)

                total_tokens += chunk_tokens
                total_payloads += payloads_count

                print(
                    f"   Chunk {chunk_count}: {chunk_tokens:,} tokens, "
                    f"{payloads_count} payloads, {compression:.2f}x compression"
                )

    except KeyboardInterrupt:
        print(f"\n⚠️  Streaming interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        return 1

    end_time = time.time()
    processing_time = end_time - start_time

    print(f"📊 Streaming Results:")
    print(f"   Chunks processed: {chunk_count}")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Total payloads: {total_payloads}")
    print(f"   Processing time: {processing_time:.2f}s")
    print(f"   Speed: {total_tokens / processing_time:,.0f} tokens/second")
    print(f"   Memory limit: {args.memory_limit}MB")

    return 0


def command_compare(args, system: GPT5PayloadSystem):
    """Handle compare command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    print(f"🔄 Comparing chunking strategies: {args.session_file.name}")

    # Get token count first
    converted = system.format_adapter.convert_session_file(args.session_file)
    if not converted:
        print(f"❌ Failed to convert session file")
        return 1

    token_analysis = system.token_analyzer.analyze_session_tokens(converted)
    tokens = token_analysis.total_tokens

    print(
        f"📊 Session analysis: {tokens:,} tokens, category: {token_analysis.size_category}"
    )

    # Compare strategies
    comparison = system.size_analyzer.compare_chunking_strategies(tokens, converted)

    print(f"\n🔍 Strategy Comparison:")
    print(
        f"{'Strategy':<12} {'Compression':<12} {'Cost':<10} {'Savings':<10} {'Quality':<10} {'Score':<8}"
    )
    print("-" * 70)

    strategies = comparison["strategy_comparisons"]
    for strategy, data in strategies.items():
        print(
            f"{strategy:<12} {data['compression_ratio']:<12.2f} "
            f"${data['optimized_cost']:<9.4f} {data['savings_percent']:<9.1f}% "
            f"{data['quality_impact']:<10} {data['efficiency_score']:<8.1f}"
        )

    print(f"\n🎯 Recommended: {comparison['recommended_strategy']} strategy")
    print(f"   Best compression: {comparison['best_compression']:.2f}x")
    print(f"   Best savings: ${comparison['best_savings']:.4f}")

    # Save comparison if output specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(comparison, f, indent=2, default=str)
        print(f"💾 Comparison saved to: {args.output}")

    return 0


def command_analyze(args, system: GPT5PayloadSystem):
    """Handle analyze command"""
    if not args.session_file.exists():
        print(f"❌ Session file not found: {args.session_file}")
        return 1

    print(f"📊 Analyzing session: {args.session_file.name}")

    # Convert and analyze
    converted = system.format_adapter.convert_session_file(args.session_file)
    if not converted:
        print(f"❌ Failed to convert session file")
        return 1

    token_analysis = system.token_analyzer.analyze_session_tokens(converted)

    if args.tokens_only:
        print(f"🔢 Token Analysis:")
        print(f"   Total tokens: {token_analysis.total_tokens:,}")
        print(f"   Input tokens: {token_analysis.input_tokens:,}")
        print(f"   Output tokens: {token_analysis.output_tokens:,}")
        print(f"   Size category: {token_analysis.size_category}")
        print(
            f"   Optimization potential: {token_analysis.optimization_potential:.1f}%"
        )
        return 0

    # Cost analysis
    cost_breakdown = system.size_analyzer.analyze_session_cost(
        token_analysis.total_tokens
    )
    optimization_analysis = system.size_analyzer.analyze_optimization_potential(
        token_analysis.total_tokens, converted
    )

    if args.cost_only:
        print(f"💰 Cost Analysis:")
        print(f"   Current cost: ${cost_breakdown.total_cost:.4f}")
        print(f"   Input cost: ${cost_breakdown.input_cost:.4f}")
        print(f"   Output cost: ${cost_breakdown.output_cost:.4f}")
        print(f"   Cost per interaction: ${cost_breakdown.cost_per_interaction:.6f}")
        print(
            f"   Potential savings: ${cost_breakdown.optimization_savings:.4f} ({cost_breakdown.potential_savings_percent:.1f}%)"
        )
        return 0

    # Full analysis
    print(f"📈 Complete Session Analysis:")
    print(
        f"   📏 Size: {token_analysis.total_tokens:,} tokens ({token_analysis.size_category})"
    )
    print(f"   💰 Cost: ${cost_breakdown.total_cost:.4f}")
    print(
        f"   🎯 Optimization score: {optimization_analysis.optimization_score:.1f}/100"
    )
    print(
        f"   💡 Savings potential: ${optimization_analysis.cost_savings:.4f} ({optimization_analysis.savings_percent:.1f}%)"
    )
    print(
        f"   🗜️  Recommended strategy: {system.size_analyzer.get_size_category_info(token_analysis.size_category).chunking_strategy}"
    )

    if optimization_analysis.recommended_actions:
        print(f"   📋 Recommendations:")
        for action in optimization_analysis.recommended_actions[:3]:
            print(f"      • {action}")

    return 0


def command_status(args, system: GPT5PayloadSystem):
    """Handle status command"""
    print("🔧 GPT-5 Payload Generation System Status")

    status = system.get_system_status()

    # Component status
    components = status["system_info"]["components_loaded"]
    print(f"\n📦 Components:")
    for component, loaded in components.items():
        status_icon = "✅" if loaded else "❌"
        print(f"   {status_icon} {component.replace('_', ' ').title()}")

    # Configuration
    if args.detailed:
        config = status["system_info"]["configuration"]
        print(f"\n⚙️  Configuration:")
        for key, value in config.items():
            print(f"   {key}: {value}")

    # Processing stats
    stats = status["processing_statistics"]
    if stats["sessions_processed"] > 0:
        print(f"\n📊 Processing Statistics:")
        print(f"   Sessions processed: {stats['sessions_processed']}")
        print(f"   Total tokens: {stats['total_tokens_analyzed']:,}")
        print(f"   Average compression: {stats['average_compression_ratio']:.2f}x")
        print(f"   Total savings: ${stats['total_cost_savings']:.2f}")
        print(f"   Processing time: {stats['processing_time_seconds']:.2f}s")

    # Compression capabilities
    capabilities = status["compression_capabilities"]
    print(f"\n🗜️  Compression Capabilities:")
    for strategy, ratio in capabilities.items():
        print(f"   {strategy.replace('_', ' ').title()}: {ratio}")

    # Phase 1 validation
    phase1 = status["phase_1_validation"]
    print(f"\n✅ Phase 1 Validation:")
    for key, value in phase1.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")

    return 0


def command_test(args, system: GPT5PayloadSystem):
    """Handle test command"""
    print("🧪 Running GPT-5 System Tests")

    if args.quick:
        print("⚡ Quick test mode")
        # Import and run a subset of tests
        try:
            import unittest

            from test_gpt5_system import TestGPT5PayloadSystem

            suite = unittest.TestSuite()
            suite.addTest(TestGPT5PayloadSystem("test_token_count_analyzer"))
            suite.addTest(TestGPT5PayloadSystem("test_chunking_engine"))
            suite.addTest(TestGPT5PayloadSystem("test_system_status"))

            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)

            return 0 if result.wasSuccessful() else 1

        except ImportError:
            print("❌ Test module not available")
            return 1

    elif args.benchmark:
        print("🚀 Running performance benchmarks")
        try:
            sys.path.append(str(Path(__file__).parent))
            from test_gpt5_system import run_performance_benchmark

            run_performance_benchmark()
            return 0
        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            return 1

    else:
        print("🔬 Running full test suite")
        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "test_gpt5_system.py")],
                capture_output=True,
                text=True,
            )

            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)

            return result.returncode

        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return 1


def main():
    """Main CLI entry point"""
    parser = setup_argparse()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load configuration
    config = (
        load_config(args.config)
        if hasattr(args, "config")
        else GPT5OptimizationConfig()
    )

    # Initialize system
    if not args.quiet:
        print("🔧 Initializing GPT-5 Payload Generation System...")

    try:
        system = GPT5PayloadSystem(config)
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return 1

    # Route to command handlers
    try:
        if args.command == "optimize":
            return command_optimize(args, system)
        elif args.command == "batch":
            return command_batch(args, system)
        elif args.command == "stream":
            return command_stream(args, system)
        elif args.command == "compare":
            return command_compare(args, system)
        elif args.command == "analyze":
            return command_analyze(args, system)
        elif args.command == "status":
            return command_status(args, system)
        elif args.command == "test":
            return command_test(args, system)
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
