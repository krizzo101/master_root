#!/usr/bin/env python3
"""
Gatekeeper Module Demo

Demonstrates the gatekeeper functionality with various scenarios.
"""

import sys
from pathlib import Path

# Add the gatekeeper module to the path
sys.path.insert(0, str(Path(__file__).parent))

from gatekeeper_agent import GatekeeperAgent


def demo_basic_usage():
    """Demonstrate basic gatekeeper usage."""
    print("🚀 Gatekeeper Module Demo")
    print("=" * 60)

    # Initialize gatekeeper with demo dependencies
    gatekeeper = GatekeeperAgent("../../.proj-intel/file_dependencies_demo.json")
    gatekeeper.set_verbose(True)

    if not gatekeeper.load_dependencies():
        print("❌ Failed to load dependencies")
        return

    print("✅ Gatekeeper initialized successfully")
    print()


def demo_bug_fix_scenario():
    """Demonstrate bug fix scenario."""
    print("🐛 Bug Fix Scenario")
    print("-" * 40)

    gatekeeper = GatekeeperAgent("../../.proj-intel/file_dependencies_demo.json")
    gatekeeper.set_verbose(True)  # Show auto-attach details

    request = "Fix the authentication bug in the security module"
    files = ["libs/opsvi-security/opsvi_security/core.py"]

    print(f"Request: {request}")
    print(f"Files: {files}")
    print()

    result = gatekeeper.process_request(
        request, files, max_files=15, min_confidence=0.1
    )

    print("📊 Results:")
    print(f"  Original files: {len(result.original_files)}")
    print(f"  Recommended files: {len(result.recommended_files)}")
    print(f"  Final files: {len(result.final_files)}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Summary: {result.processing_summary}")
    print()

    print("📁 Final file selection:")
    for i, file_path in enumerate(result.final_files, 1):
        file_info = gatekeeper.auto_attach.get_file_info(file_path)
        file_type = file_info.get("file_type", "unknown")
        print(f"  {i:2d}. {file_path} ({file_type})")
    print()


def demo_feature_development_scenario():
    """Demonstrate feature development scenario."""
    print("🆕 Feature Development Scenario")
    print("-" * 40)

    gatekeeper = GatekeeperAgent("../../.proj-intel/file_dependencies_demo.json")
    gatekeeper.set_verbose(True)

    request = "Add a new configuration option to the core module"
    files = ["libs/opsvi-core/opsvi_core/core/base.py"]

    print(f"Request: {request}")
    print(f"Files: {files}")
    print()

    result = gatekeeper.process_request(
        request, files, max_files=12, min_confidence=0.1
    )

    print("📊 Results:")
    print(f"  Original files: {len(result.original_files)}")
    print(f"  Recommended files: {len(result.recommended_files)}")
    print(f"  Final files: {len(result.final_files)}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Summary: {result.processing_summary}")
    print()

    print("📁 Final file selection:")
    for i, file_path in enumerate(result.final_files, 1):
        file_info = gatekeeper.auto_attach.get_file_info(file_path)
        file_type = file_info.get("file_type", "unknown")
        print(f"  {i:2d}. {file_path} ({file_type})")
    print()


def demo_testing_scenario():
    """Demonstrate testing scenario."""
    print("🧪 Testing Scenario")
    print("-" * 40)

    gatekeeper = GatekeeperAgent("../../.proj-intel/file_dependencies_demo.json")
    gatekeeper.set_verbose(True)

    request = "Write unit tests for the logging functionality"
    files = ["libs/opsvi-security/opsvi_security/logging.py"]

    print(f"Request: {request}")
    print(f"Files: {files}")
    print()

    result = gatekeeper.process_request(
        request, files, max_files=10, min_confidence=0.1
    )

    print("📊 Results:")
    print(f"  Original files: {len(result.original_files)}")
    print(f"  Recommended files: {len(result.recommended_files)}")
    print(f"  Final files: {len(result.final_files)}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Summary: {result.processing_summary}")
    print()

    print("📁 Final file selection:")
    for i, file_path in enumerate(result.final_files, 1):
        file_info = gatekeeper.auto_attach.get_file_info(file_path)
        file_type = file_info.get("file_type", "unknown")
        print(f"  {i:2d}. {file_path} ({file_type})")
    print()


def demo_complex_scenario():
    """Demonstrate complex scenario with multiple files."""
    print("🔄 Complex Scenario")
    print("-" * 40)

    gatekeeper = GatekeeperAgent("../../.proj-intel/file_dependencies_demo.json")
    gatekeeper.set_verbose(True)

    request = "Refactor the security module to improve performance and add better error handling"
    files = [
        "libs/opsvi-security/opsvi_security/core.py",
        "libs/opsvi-security/opsvi_security/logging.py",
    ]

    print(f"Request: {request}")
    print(f"Files: {files}")
    print()

    result = gatekeeper.process_request(
        request, files, max_files=20, min_confidence=0.1
    )

    print("📊 Results:")
    print(f"  Original files: {len(result.original_files)}")
    print(f"  Recommended files: {len(result.recommended_files)}")
    print(f"  Final files: {len(result.final_files)}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Summary: {result.processing_summary}")
    print()

    # Group files by type
    files_by_type = {}
    for file_path in result.final_files:
        file_info = gatekeeper.auto_attach.get_file_info(file_path)
        file_type = file_info.get("file_type", "unknown")
        if file_type not in files_by_type:
            files_by_type[file_type] = []
        files_by_type[file_type].append(file_path)

    print("📁 Files by type:")
    for file_type, file_list in files_by_type.items():
        print(f"  {file_type.title()} ({len(file_list)} files):")
        for file_path in file_list:
            print(f"    - {file_path}")
        print()

    # Export result for inspection
    gatekeeper.export_result(result, "demo_complex_result.json")
    print("💾 Result exported to: demo_complex_result.json")


def demo_context_analysis():
    """Demonstrate context analysis capabilities."""
    print("🔍 Context Analysis Demo")
    print("-" * 40)

    from context_analyzer import ContextAnalyzer

    analyzer = ContextAnalyzer()

    test_requests = [
        "Fix the authentication bug",
        "Add a new feature for user management",
        "Write unit tests for the logging module",
        "Update the documentation",
        "Optimize performance of the database queries",
        "Add security validation to the API endpoints",
    ]

    for request in test_requests:
        print(f"Request: {request}")
        analysis = analyzer.analyze_request(request)
        print(f"  Type: {analysis.analysis_summary}")
        print(f"  Confidence: {analysis.confidence_score:.2f}")
        print(f"  Recommendations: {len(analysis.recommended_context)}")
        print()


def main():
    """Run all demos."""
    demo_basic_usage()
    demo_bug_fix_scenario()
    demo_feature_development_scenario()
    demo_testing_scenario()
    demo_complex_scenario()
    demo_context_analysis()

    print("🎉 Demo completed!")
    print("\n💡 The gatekeeper module is now ready for integration into your agents!")


if __name__ == "__main__":
    main()
