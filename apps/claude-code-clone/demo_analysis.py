#!/usr/bin/env python3
"""Demonstrate static code analysis capabilities."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claude_code import ClaudeCodeConfig, CodeAnalyzer


async def demonstrate_analysis():
    """Demonstrate code analysis capabilities."""
    print("🔍 Claude Code Clone - Static Analysis Demo")
    print("=" * 50)

    # Configuration
    config = ClaudeCodeConfig(
        working_directory=".",
        enable_file_operations=True,
    )

    # Initialize analyzer
    analyzer = CodeAnalyzer(config)

    # Analyze the sample code file
    sample_file = Path("sample_code.py")

    if sample_file.exists():
        print(f"📄 Analyzing: {sample_file.name}")
        print("-" * 30)

        # Python file analysis
        metrics = analyzer.analyze_python_file(sample_file)

        print("📊 **Code Metrics:**")
        print(f"   • Lines of Code: {metrics['lines_of_code']}")
        print(f"   • Functions: {len(metrics['functions'])}")
        print(f"   • Classes: {len(metrics['classes'])}")
        print(f"   • Complexity: {metrics['complexity']}")
        print(f"   • Issues Found: {len(metrics['issues'])}")
        print()

        # Show functions
        if metrics["functions"]:
            print("🔧 **Functions Found:**")
            for func in metrics["functions"]:
                print(
                    f"   • {func['name']}() - Line {func['line']}, Args: {func['args']}, Complexity: {func['complexity']}"
                )
            print()

        # Show classes
        if metrics["classes"]:
            print("🏗️  **Classes Found:**")
            for cls in metrics["classes"]:
                print(
                    f"   • {cls['name']} - Line {cls['line']}, Methods: {cls['methods']}"
                )
            print()

        # Show issues
        if metrics["issues"]:
            print("⚠️  **Issues Detected:**")
            for issue in metrics["issues"][:10]:  # Show first 10 issues
                print(f"   • {issue}")
            if len(metrics["issues"]) > 10:
                print(f"   ... and {len(metrics['issues']) - 10} more issues")
            print()

        # Show imports
        if metrics["imports"]:
            print("📦 **Imports:**")
            for imp in metrics["imports"]:
                print(f"   • {imp}")
            print()

    # Project structure analysis
    print("🏗️  **Project Structure Analysis:**")
    print("-" * 30)

    structure = analyzer.analyze_project_structure()

    print(f"📊 Total Files: {structure['total_files']}")
    print(f"📊 File Types: {len(structure['file_types'])}")
    print(f"📊 Total Functions: {structure['complexity_summary']['total_functions']}")
    print(f"📊 Total Classes: {structure['complexity_summary']['total_classes']}")
    print(f"📊 Total Complexity: {structure['complexity_summary']['total_complexity']}")
    print()

    # Show file type distribution
    print("📈 **File Type Distribution:**")
    top_types = sorted(
        structure["file_types"].items(), key=lambda x: x[1], reverse=True
    )
    for ext, count in top_types:
        print(f"   • {ext}: {count} files")
    print()

    # Show largest files
    print("📏 **Largest Files:**")
    for file_info in structure["largest_files"][:5]:
        size_kb = file_info["size"] / 1024
        print(f"   • {file_info['path']}: {size_kb:.1f} KB")
    print()

    # Duplicate code detection
    print("🔍 **Duplicate Code Detection:**")
    print("-" * 30)

    duplicates = analyzer.find_duplicate_code(["*.py"])
    if duplicates:
        print(f"📊 Found {len(duplicates)} potential duplicate code blocks:")
        for key, lines in list(duplicates.items())[:3]:  # Show first 3
            print(f"   • {key}: {len(lines)} common lines")
    else:
        print("✅ No duplicate code blocks found")
    print()

    print("🎉 Analysis demonstration complete!")


if __name__ == "__main__":
    asyncio.run(demonstrate_analysis())

