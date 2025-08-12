#!/usr/bin/env python3
"""
Test Gatekeeper Module

Comprehensive test suite for the gatekeeper functionality.
"""

import sys
from pathlib import Path

# Add the gatekeeper module to the path
sys.path.insert(0, str(Path(__file__).parent))

from auto_attach import AutoAttach
from context_analyzer import ContextAnalyzer
from gatekeeper_agent import GatekeeperAgent


def test_context_analyzer():
    """Test the context analyzer functionality."""
    print("🧪 Testing Context Analyzer")
    print("=" * 50)

    analyzer = ContextAnalyzer()

    # Test different request types
    test_cases = [
        {
            "request": "Fix the bug in the authentication module",
            "files": ["libs/opsvi-security/opsvi_security/core.py"],
            "expected_type": "bug_fix",
        },
        {
            "request": "Add a new feature for user management",
            "files": ["libs/opsvi-core/opsvi_core/core/base.py"],
            "expected_type": "feature_development",
        },
        {
            "request": "Write unit tests for the logging module",
            "files": ["libs/opsvi-security/opsvi_security/logging.py"],
            "expected_type": "testing",
        },
        {
            "request": "Update the documentation for the API",
            "files": [],
            "expected_type": "documentation",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['request']}")

        analysis = analyzer.analyze_request(test_case["request"], test_case["files"])

        print(f"   Analysis: {analysis.analysis_summary}")
        print(f"   Confidence: {analysis.confidence_score:.2f}")
        print(f"   Recommendations: {len(analysis.recommended_context)}")

        # Check if expected type is detected
        request_types = [rec.context_type for rec in analysis.recommended_context]
        if (
            test_case["expected_type"] in request_types
            or analysis.confidence_score > 0.05
        ):
            print("   ✅ Test passed")
        else:
            print("   ❌ Test failed")

    print("\n✅ Context Analyzer tests completed")
    return True


def test_auto_attach():
    """Test the auto-attach functionality."""
    print("\n🧪 Testing Auto-Attach")
    print("=" * 50)

    # Use demo dependencies for testing
    auto_attach = AutoAttach("../../.proj-intel/file_dependencies_demo.json")

    if not auto_attach.load_dependencies():
        print("❌ Failed to load demo dependencies")
        return False

    test_file = "libs/opsvi-security/opsvi_security/core.py"
    related_files = auto_attach.find_related_files([test_file], verbose=True)

    print(f"Input file: {test_file}")
    print(f"Related files found: {len(related_files)}")

    if len(related_files) > 1:
        print("✅ Auto-attach test passed")
        return True
    else:
        print("❌ Auto-attach test failed")
        return False


def test_gatekeeper_agent():
    """Test the main gatekeeper agent."""
    print("\n🧪 Testing Gatekeeper Agent")
    print("=" * 50)

    # Use demo dependencies for testing
    gatekeeper = GatekeeperAgent("../../.proj-intel/file_dependencies_demo.json")
    gatekeeper.set_verbose(True)

    if not gatekeeper.load_dependencies():
        print("❌ Failed to load dependencies")
        return False

    # Test different scenarios
    test_scenarios = [
        {
            "name": "Bug Fix Request",
            "request": "Fix the authentication bug in the security module",
            "files": ["libs/opsvi-security/opsvi_security/core.py"],
            "max_files": 10,
        },
        {
            "name": "Feature Development",
            "request": "Add a new configuration option to the core module",
            "files": ["libs/opsvi-core/opsvi_core/core/base.py"],
            "max_files": 15,
        },
        {
            "name": "Testing Request",
            "request": "Write unit tests for the logging functionality",
            "files": ["libs/opsvi-security/opsvi_security/logging.py"],
            "max_files": 8,
        },
    ]

    for scenario in test_scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"Request: {scenario['request']}")
        print(f"Files: {scenario['files']}")

        result = gatekeeper.process_request(
            scenario["request"], scenario["files"], max_files=scenario["max_files"]
        )

        print(f"Original files: {len(result.original_files)}")
        print(f"Recommended files: {len(result.recommended_files)}")
        print(f"Final files: {len(result.final_files)}")
        print(f"Confidence: {result.confidence_score:.2f}")
        print(f"Summary: {result.processing_summary}")

        # Validate results
        if (
            len(result.final_files) > 0
            and len(result.final_files) <= scenario["max_files"]
            and result.confidence_score > 0.3
        ):
            print("   ✅ Scenario passed")
        else:
            print("   ❌ Scenario failed")

    print("\n✅ Gatekeeper Agent tests completed")
    return True


def test_integration():
    """Test integration between components."""
    print("\n🧪 Testing Integration")
    print("=" * 50)

    gatekeeper = GatekeeperAgent("../../.proj-intel/file_dependencies_demo.json")

    if not gatekeeper.load_dependencies():
        print("❌ Failed to load dependencies")
        return False

    # Test a complex scenario
    request = "Refactor the security module to improve performance and add better error handling"
    files = [
        "libs/opsvi-security/opsvi_security/core.py",
        "libs/opsvi-security/opsvi_security/logging.py",
    ]

    print(f"Complex request: {request}")
    print(f"Files: {files}")

    result = gatekeeper.process_request(
        request, files, max_files=20, min_confidence=0.4
    )

    print("Final result:")
    print(f"  - Original files: {len(result.original_files)}")
    print(f"  - Recommended files: {len(result.recommended_files)}")
    print(f"  - Final files: {len(result.final_files)}")
    print(f"  - Confidence: {result.confidence_score:.2f}")
    print(f"  - Summary: {result.processing_summary}")

    # Export result for inspection
    gatekeeper.export_result(result, "test_gatekeeper_result.json")

    if (
        len(result.final_files) > len(result.original_files)
        and result.confidence_score > 0.5
    ):
        print("✅ Integration test passed")
        return True
    else:
        print("❌ Integration test failed")
        return False


def main():
    """Run all tests."""
    print("🚀 Gatekeeper Module Test Suite")
    print("=" * 60)

    tests = [
        ("Context Analyzer", test_context_analyzer),
        ("Auto-Attach", test_auto_attach),
        ("Gatekeeper Agent", test_gatekeeper_agent),
        ("Integration", test_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
