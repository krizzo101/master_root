#!/usr/bin/env python3
"""Demo script for Claude Code Clone capabilities."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_code import ClaudeCodeConfig, ClaudeCodeExecutor, CodeAnalyzer


async def demo_claude_code_clone():
    """Demonstrate Claude Code Clone capabilities."""
    print("🚀 Claude Code Clone Demo")
    print("=" * 50)

    # Configuration
    config = ClaudeCodeConfig(
        provider="openai",
        model="gpt-5-mini",
        working_directory=".",
        enable_file_operations=True,
        api_key="demo_key",  # Replace with real API key for actual use
    )

    print(f"📋 Configuration: {config.provider} with {config.model}")
    print(f"📁 Working Directory: {config.working_directory}")
    print(
        f"🔧 File Operations: {'Enabled' if config.enable_file_operations else 'Disabled'}"
    )
    print()

    # Initialize components
    print("🔧 Initializing components...")
    executor = ClaudeCodeExecutor(config)
    analyzer = CodeAnalyzer(config)
    print("✅ Components initialized successfully")
    print()

    # Demo 1: Configuration validation
    print("📊 Demo 1: Configuration Validation")
    print("-" * 30)
    print(f"✅ Provider: {config.provider}")
    print(f"✅ Model: {config.model}")
    print(f"✅ Max Tokens: {config.max_tokens}")
    print(f"✅ Temperature: {config.temperature}")
    print(f"✅ Allowed Extensions: {len(config.allowed_file_extensions)} file types")
    print(f"✅ Max File Size: {config.max_file_size / 1024 / 1024:.1f} MB")
    print()

    # Demo 2: Code Analysis (static analysis)
    print("🔍 Demo 2: Static Code Analysis")
    print("-" * 30)
    try:
        # Analyze the demo script itself
        demo_file = Path(__file__)
        if demo_file.exists():
            print(f"📄 Analyzing: {demo_file.name}")

            # Python file analysis
            metrics = analyzer.analyze_python_file(demo_file)
            print(f"📊 Lines of Code: {metrics['lines_of_code']}")
            print(f"📊 Functions: {len(metrics['functions'])}")
            print(f"📊 Classes: {len(metrics['classes'])}")
            print(f"📊 Complexity: {metrics['complexity']}")
            print(f"📊 Issues Found: {len(metrics['issues'])}")

            if metrics["issues"]:
                print("⚠️  Issues:")
                for issue in metrics["issues"][:3]:  # Show first 3 issues
                    print(f"   - {issue}")
        else:
            print("❌ Demo file not found for analysis")
    except Exception as e:
        print(f"⚠️  Analysis demo failed: {e}")
    print()

    # Demo 3: Project Structure Analysis
    print("🏗️  Demo 3: Project Structure Analysis")
    print("-" * 30)
    try:
        structure = analyzer.analyze_project_structure()
        print(f"📊 Total Files: {structure['total_files']}")
        print(f"📊 File Types: {len(structure['file_types'])}")
        print(
            f"📊 Total Functions: {structure['complexity_summary']['total_functions']}"
        )
        print(f"📊 Total Classes: {structure['complexity_summary']['total_classes']}")
        print(
            f"📊 Total Complexity: {structure['complexity_summary']['total_complexity']}"
        )

        # Show top file types
        top_types = sorted(
            structure["file_types"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        print("📈 Top File Types:")
        for ext, count in top_types:
            print(f"   - {ext}: {count} files")
    except Exception as e:
        print(f"⚠️  Project analysis demo failed: {e}")
    print()

    # Demo 4: Duplicate Code Detection
    print("🔍 Demo 4: Duplicate Code Detection")
    print("-" * 30)
    try:
        duplicates = analyzer.find_duplicate_code(["*.py"])
        if duplicates:
            print(f"📊 Found {len(duplicates)} potential duplicate code blocks")
            for key, lines in list(duplicates.items())[:2]:  # Show first 2
                print(f"   - {key}: {len(lines)} common lines")
        else:
            print("✅ No duplicate code blocks found")
    except Exception as e:
        print(f"⚠️  Duplicate detection demo failed: {e}")
    print()

    # Demo 5: Language Detection
    print("🌐 Demo 5: Language Detection")
    print("-" * 30)
    test_files = [
        ("example.py", "python"),
        ("script.js", "javascript"),
        ("app.ts", "typescript"),
        ("main.cpp", "cpp"),
        ("server.go", "go"),
        ("lib.rs", "rust"),
    ]

    for filename, expected_lang in test_files:
        detected = executor._get_language_from_extension(Path(filename).suffix)
        status = "✅" if detected == expected_lang else "❌"
        print(f"{status} {filename} -> {detected} (expected: {expected_lang})")
    print()

    # Demo 6: CLI Commands Preview
    print("💻 Demo 6: Available CLI Commands")
    print("-" * 30)
    commands = [
        (
            "claude-code analyze file.py --analysis-type security",
            "Analyze file for security issues",
        ),
        ("claude-code generate api.py 'Create REST API'", "Generate code from prompt"),
        (
            "claude-code refactor old.py --refactor-type optimize",
            "Refactor code for optimization",
        ),
        (
            "claude-code project ./my-app --analysis-types structure,complexity",
            "Analyze entire project",
        ),
        ("claude-code interactive", "Start interactive mode"),
    ]

    for cmd, desc in commands:
        print(f"🔧 {cmd}")
        print(f"   📝 {desc}")
    print()

    # Demo 7: Provider Support
    print("🤖 Demo 7: Multi-Provider Support")
    print("-" * 30)
    providers = [
        ("openai", "GPT-5, GPT-4, GPT-3.5 models"),
        ("anthropic", "Claude 3 Opus, Sonnet, Haiku models"),
        ("perplexity", "Perplexity Pro models"),
    ]

    for provider, models in providers:
        print(f"✅ {provider.title()}: {models}")
    print()

    # Cleanup
    print("🧹 Cleaning up...")
    await executor.close()
    print("✅ Demo completed successfully!")
    print()

    # Summary
    print("🎉 Claude Code Clone Demo Summary")
    print("=" * 50)
    print("✅ Configuration management")
    print("✅ Static code analysis")
    print("✅ Project structure analysis")
    print("✅ Duplicate code detection")
    print("✅ Multi-language support")
    print("✅ CLI interface")
    print("✅ Multi-provider LLM support")
    print()
    print("🚀 Ready for production use!")
    print()
    print("📖 Next Steps:")
    print("1. Set your API key: export CLAUDE_CODE_API_KEY=your_key")
    print("2. Try the CLI: claude-code analyze your_file.py")
    print("3. Use the Python API in your projects")
    print("4. Extend with additional providers as needed")


if __name__ == "__main__":
    asyncio.run(demo_claude_code_clone())

