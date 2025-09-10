#!/usr/bin/env python3
"""
Simplified Integration Testing for Session Optimization System
Tests SessionAnalyticsEngine + GPT5PayloadGenerator with real Claude session data
"""

import json
import os
import sys
import time
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from enhanced_claude_format_adapter import create_enhanced_session_analytics_engine
from gpt5_payload_system import GPT5PayloadSystem


def test_session_analytics(session_file, session_name):
    """Test SessionAnalyticsEngine with a session file"""
    print(f"\n🔍 Testing SessionAnalyticsEngine with {session_name}...")

    try:
        # Create enhanced engine
        enhanced_engine = create_enhanced_session_analytics_engine()

        # Analyze session
        start_time = time.time()
        report = enhanced_engine.analyze_session(session_file)
        analysis_time = time.time() - start_time

        # Calculate totals
        total_messages = (
            report.conversation_flow.user_messages
            + report.conversation_flow.assistant_messages
            + report.conversation_flow.system_messages
        )
        total_tool_calls = sum(report.tool_usage.tool_counts.values())
        total_file_ops = sum(report.file_operations.operation_counts.values())

        print(f"✅ Session analyzed successfully in {analysis_time:.2f}s!")
        print(f"   - Session ID: {report.session_context.session_id}")
        print(f"   - Total messages: {total_messages}")
        print(f"   - Tool calls: {total_tool_calls}")
        print(f"   - File operations: {total_file_ops}")
        print(f"   - Optimization score: {report.optimization_score:.2f}")
        print(f"   - Complexity rating: {report.complexity_rating}")

        return {
            "success": True,
            "session_name": session_name,
            "session_id": report.session_context.session_id,
            "total_messages": total_messages,
            "total_tool_calls": total_tool_calls,
            "file_operations_count": total_file_ops,
            "optimization_score": report.optimization_score,
            "complexity_rating": report.complexity_rating,
            "analysis_time_seconds": analysis_time,
        }

    except Exception as e:
        print(f"❌ Error analyzing {session_name}: {e}")
        return {"success": False, "error": str(e), "session_name": session_name}


def test_gpt5_payload_generation(session_file, session_name):
    """Test GPT5PayloadGenerator"""
    print(f"\n🚀 Testing GPT5PayloadGenerator with {session_name}...")

    try:
        # Initialize GPT5 payload system
        payload_system = GPT5PayloadSystem()

        # Generate payload
        start_time = time.time()
        result = payload_system.optimize_session_file(Path(session_file))
        processing_time = time.time() - start_time

        if result.success:
            # Extract metrics
            original_tokens = result.token_analysis.total_tokens
            optimized_tokens = sum(
                p.estimated_tokens for p in result.generated_payloads
            )
            compression_ratio = (
                original_tokens / optimized_tokens if optimized_tokens > 0 else 0
            )

            print(f"✅ Payload generated successfully in {processing_time:.2f}s!")
            print(f"   - Original tokens: {original_tokens:,}")
            print(f"   - Optimized tokens: {optimized_tokens:,}")
            print(f"   - Compression ratio: {compression_ratio:.2f}x")
            print(f"   - Chunks created: {len(result.generated_payloads)}")

            return {
                "success": True,
                "session_name": session_name,
                "compression_ratio": compression_ratio,
                "original_tokens": original_tokens,
                "optimized_tokens": optimized_tokens,
                "chunks_created": len(result.generated_payloads),
                "processing_time": processing_time,
            }
        else:
            print(f"❌ Payload generation failed: {result.error_message}")
            return {
                "success": False,
                "error": result.error_message,
                "session_name": session_name,
            }

    except Exception as e:
        print(f"❌ Error generating payload for {session_name}: {e}")
        return {"success": False, "error": str(e), "session_name": session_name}


def test_cli_tools():
    """Test CLI tools functionality"""
    print(f"\n🛠️  Testing CLI tools functionality...")

    import subprocess

    results = {"payload_cli": False, "size_reporter": False}

    # Test gpt5_cli.py
    print("   Testing gpt5_cli.py...")
    try:
        result = subprocess.run(
            [
                "python",
                "gpt5_cli.py",
                "analyze",
                "/home/opsvi/.claude/projects/-home-opsvi-master-root/87d77601-6cec-4852-bc5e-e6a0306d3c88.jsonl",
            ],
            capture_output=True,
            text=True,
            cwd="/home/opsvi/master_root/apps/session-optimizer",
            timeout=60,
        )

        if result.returncode == 0:
            print("      ✅ gpt5_cli.py executed successfully")
            results["payload_cli"] = True
        else:
            print(f"      ❌ gpt5_cli.py failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"      ❌ gpt5_cli.py error: {e}")

    # Test enhanced Claude session analyzer
    print("   Testing claude_session_analyzer.py...")
    try:
        # Create test directory structure
        test_dir = Path("/home/opsvi/master_root/apps/session-optimizer/test_sessions")
        test_dir.mkdir(exist_ok=True)

        # Copy a session file
        import shutil

        session_file = "/home/opsvi/.claude/projects/-home-opsvi-master-root/87d77601-6cec-4852-bc5e-e6a0306d3c88.jsonl"
        if os.path.exists(session_file):
            shutil.copy(session_file, test_dir)

            result = subprocess.run(
                [
                    "python",
                    "claude_session_analyzer.py",
                    str(test_dir),
                    "--output",
                    "test_analyzer_results.json",
                ],
                capture_output=True,
                text=True,
                cwd="/home/opsvi/master_root/apps/session-optimizer",
                timeout=60,
            )

            if result.returncode == 0:
                print("      ✅ claude_session_analyzer.py executed successfully")
                results["size_reporter"] = True
            else:
                print(
                    f"      ❌ claude_session_analyzer.py failed: {result.stderr[:200]}"
                )
    except Exception as e:
        print(f"      ❌ claude_session_analyzer.py error: {e}")

    return results


def generate_validation_report(
    session_87d_results,
    session_47b_results,
    gpt5_87d_results,
    gpt5_47b_results,
    cli_results,
):
    """Generate comprehensive validation report"""
    print(f"\n📊 Generating validation report...")

    # Expected Phase 1 results
    expected_compression = {"min": 2.23, "max": 3.14}

    validation_report = {
        "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_summary": {
            "session_87d77601_analytics_success": session_87d_results.get(
                "success", False
            ),
            "session_47b30416_analytics_success": session_47b_results.get(
                "success", False
            ),
            "session_87d77601_gpt5_success": gpt5_87d_results.get("success", False),
            "session_47b30416_gpt5_success": gpt5_47b_results.get("success", False),
            "cli_tools_tested": cli_results,
        },
        "phase1_expected_results": {"compression_ratio_range": expected_compression},
        "actual_results": {
            "session_87d77601": {
                "analytics": session_87d_results,
                "gpt5_optimization": gpt5_87d_results,
            },
            "session_47b30416": {
                "analytics": session_47b_results,
                "gpt5_optimization": gpt5_47b_results,
            },
        },
        "validation_status": {
            "sessionanalytics_functional": (
                session_87d_results.get("success", False)
                and session_47b_results.get("success", False)
            ),
            "gpt5_payload_functional": (
                gpt5_87d_results.get("success", False)
                and gpt5_47b_results.get("success", False)
            ),
            "compression_ratios_in_range": False,
            "cli_tools_functional": any(cli_results.values()),
        },
    }

    # Check compression ratios
    compression_ratios = []
    if gpt5_87d_results.get("success"):
        compression_ratios.append(gpt5_87d_results["compression_ratio"])
    if gpt5_47b_results.get("success"):
        compression_ratios.append(gpt5_47b_results["compression_ratio"])

    if compression_ratios:
        min_ratio = min(compression_ratios)
        max_ratio = max(compression_ratios)

        print(f"   Compression ratios: {min_ratio:.2f}x - {max_ratio:.2f}x")
        print(
            f"   Expected range: {expected_compression['min']}x - {expected_compression['max']}x"
        )

        # Allow 20% tolerance
        if (
            min_ratio >= expected_compression["min"] * 0.8
            and max_ratio <= expected_compression["max"] * 1.2
        ):
            print("   ✅ Compression ratios within acceptable range")
            validation_report["validation_status"]["compression_ratios_in_range"] = True
        else:
            print("   ⚠️  Compression ratios outside expected range")

    # Save validation report
    with open("integration_validation_report.json", "w") as f:
        json.dump(validation_report, f, indent=2, default=str)

    print("📄 Validation report saved to integration_validation_report.json")

    return validation_report


def main():
    """Run simplified integration tests"""
    print("🧪 Starting Session Optimization Integration Tests (Simplified)")
    print("=" * 80)

    # Session files
    session_87d = "/home/opsvi/.claude/projects/-home-opsvi-master-root/87d77601-6cec-4852-bc5e-e6a0306d3c88.jsonl"
    session_47b = "/home/opsvi/.claude/projects/-home-opsvi-em7-disk/47b30416-32c6-438d-b905-2d71442efb4b.jsonl"

    # Verify files exist
    if not os.path.exists(session_87d):
        print(f"❌ Session file not found: {session_87d}")
        return
    if not os.path.exists(session_47b):
        print(f"❌ Session file not found: {session_47b}")
        return

    # Test 1: SessionAnalyticsEngine with current session (87d77601)
    session_87d_results = test_session_analytics(session_87d, "87d77601 (293K tokens)")

    # Test 2: SessionAnalyticsEngine with largest session (47b30416)
    session_47b_results = test_session_analytics(session_47b, "47b30416 (4.5M tokens)")

    # Test 3: GPT5PayloadGenerator with current session
    gpt5_87d_results = test_gpt5_payload_generation(session_87d, "87d77601")

    # Test 4: GPT5PayloadGenerator with largest session
    gpt5_47b_results = test_gpt5_payload_generation(session_47b, "47b30416")

    # Test 5: CLI tools functionality
    cli_results = test_cli_tools()

    # Test 6: Generate validation report
    validation_report = generate_validation_report(
        session_87d_results,
        session_47b_results,
        gpt5_87d_results,
        gpt5_47b_results,
        cli_results,
    )

    print(f"\n🎉 Integration testing completed!")
    print(f"📊 Results:")
    print(
        f"   - SessionAnalyticsEngine: {'✅' if validation_report['validation_status']['sessionanalytics_functional'] else '❌'}"
    )
    print(
        f"   - GPT5PayloadGenerator: {'✅' if validation_report['validation_status']['gpt5_payload_functional'] else '❌'}"
    )
    print(
        f"   - Compression ratios: {'✅' if validation_report['validation_status']['compression_ratios_in_range'] else '❌'}"
    )
    print(
        f"   - CLI tools: {'✅' if validation_report['validation_status']['cli_tools_functional'] else '❌'}"
    )
    print(f"📄 Check integration_validation_report.json for detailed results")


if __name__ == "__main__":
    main()
