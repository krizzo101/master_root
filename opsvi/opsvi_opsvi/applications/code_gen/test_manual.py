#!/usr/bin/env python3
"""Manual test script to verify AI-powered code generation works end-to-end.

Run this to verify the real AI functionality without mocks.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import tempfile
import zipfile
from pipeline import build_pipeline
from config import config


def test_ai_project_detection():
    """Test AI project type detection."""
    print("🧠 Testing AI Project Type Detection...")

    from ai_agents import detect_project_type_with_ai

    test_cases = [
        ("Create a REST API for user management", "web_api"),
        ("Build a command line calculator", "cli_tool"),
        ("Make a simple hello world script", "simple_script"),
        ("Create a web app with login", "web_app"),
        ("Build a CSV data processor", "data_processor"),
    ]

    for request, expected in test_cases:
        try:
            detected = detect_project_type_with_ai(request)
            status = "✅" if detected.value == expected else "❌"
            print(f"  {status} '{request}' → {detected.value} (expected: {expected})")
        except Exception as e:
            print(f"  ❌ '{request}' → ERROR: {e}")


def test_ai_requirements_extraction():
    """Test AI requirements extraction."""
    print("\n📋 Testing AI Requirements Extraction...")

    from ai_agents import extract_requirements_with_ai
    from project_templates import ProjectType

    request = "Create a FastAPI web service for managing a library with book CRUD operations and user authentication"

    try:
        requirements = extract_requirements_with_ai(request, ProjectType.WEB_API)
        print(f"  ✅ Title: {requirements.title}")
        print(
            f"  ✅ Functional Requirements: {len(requirements.functional_requirements)} items"
        )
        print(
            f"  ✅ Non-Functional Requirements: {len(requirements.non_functional_requirements)} items"
        )

        # Show some examples
        if requirements.functional_requirements:
            print(f"  📝 Example: {requirements.functional_requirements[0]}")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")


def test_ai_architecture_generation():
    """Test AI architecture generation."""
    print("\n🏗️ Testing AI Architecture Generation...")

    from ai_agents import extract_requirements_with_ai, generate_architecture_with_ai
    from project_templates import ProjectType

    request = "Create a FastAPI web service for managing users"

    try:
        requirements = extract_requirements_with_ai(request, ProjectType.WEB_API)
        architecture = generate_architecture_with_ai(requirements, ProjectType.WEB_API)

        print(f"  ✅ Components: {len(architecture.components)} generated")
        print(f"  ✅ Design Decisions: {len(architecture.design_decisions)} items")

        # Show first component
        if architecture.components:
            comp = architecture.components[0]
            print(f"  📝 Example Component: {comp.get('name', 'Unknown')}")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")


def test_full_pipeline():
    """Test the complete AI-powered pipeline."""
    print("\n🚀 Testing Full AI-Powered Pipeline...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        try:
            pipeline = build_pipeline()
            state = {
                "request": "Create a simple Python script that calculates fibonacci numbers",
                "output_dir": tmp_path,
            }

            print("  ⚡ Running complete pipeline...")
            result = pipeline.invoke(state)

            if result.get("status") == "DONE":
                print("  ✅ Pipeline completed successfully!")
                print(f"    📋 Project: {result['requirements'].title}")
                print(f"    🎯 Type: {result['project_type'].value}")
                print(
                    f"    🧪 Tests: {result['test_report'].passed} passed, {result['test_report'].failed} failed"
                )
                print(f"    📊 Coverage: {result['test_report'].coverage:.1%}")

                # Check artifacts
                artifacts_zip = tmp_path / "artifacts.zip"
                if artifacts_zip.exists():
                    with zipfile.ZipFile(artifacts_zip, "r") as zf:
                        files = zf.namelist()
                        python_files = [f for f in files if f.endswith(".py")]
                        print(
                            f"    📦 Artifacts: {len(files)} files, {len(python_files)} Python files"
                        )
                        print("  ✅ Complete working project generated!")
                else:
                    print("  ❌ Artifacts ZIP not found")
            else:
                print(f"  ❌ Pipeline failed with status: {result.get('status')}")

        except Exception as e:
            print(f"  ❌ Pipeline ERROR: {e}")
            import traceback

            traceback.print_exc()


def test_ai_security():
    """Test AI security validation."""
    print("\n🔒 Testing AI Security Validation...")

    from ai_agents import analyze_request_security_with_ai

    test_cases = [
        ("Create a simple calculator", True),
        ("Build a file manager app", True),
        ("Create a script that uses eval() and exec()", False),
        ("Make a tool that deletes system files", False),
    ]

    for request, should_be_safe in test_cases:
        try:
            analysis = analyze_request_security_with_ai(request)
            status = "✅" if analysis.is_safe == should_be_safe else "⚠️"
            risk_info = f"(risk: {analysis.risk_level})"
            concerns_info = (
                f", concerns: {len(analysis.concerns)}" if analysis.concerns else ""
            )
            print(
                f"  {status} '{request}' → safe: {analysis.is_safe} {risk_info}{concerns_info}"
            )
        except Exception as e:
            print(f"  ❌ '{request}' → ERROR: {e}")


def main():
    """Run all manual tests."""
    print("🧪 Manual AI-Powered Code Generation Tests")
    print("=" * 50)

    # Check API key
    if not config.openai_api_key:
        print("❌ OPENAI_API_KEY not set. Please set it to run these tests.")
        print("   export OPENAI_API_KEY='your-key-here'")
        return 1

    print("✅ OpenAI API Key configured")

    # Run tests
    test_ai_project_detection()
    test_ai_requirements_extraction()
    test_ai_architecture_generation()
    test_ai_security()
    test_full_pipeline()

    print("\n" + "=" * 50)
    print("🎉 Manual testing completed!")
    print("\nTo run the full integration test suite:")
    print("  python -m pytest tests/test_integration.py -v")
    print("\nTo start the server:")
    print("  python main.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
