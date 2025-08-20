#!/usr/bin/env python3
"""
Practical examples of leveraging proj-mapper data
Shows real-world use cases and value extraction
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# import networkx as nx  # Optional - for graph analysis


class ProjectMapAnalyzer:
    """Analyzes and leverages proj-mapper data for various use cases"""

    def __init__(self, project_map_path: str):
        """Load project map data"""
        with open(project_map_path) as f:
            self.data = json.load(f)

        self.files = self.data.get("files", [])
        self.project = self.data.get("project", {})

    def find_largest_files(self, top_n: int = 10) -> List[Dict]:
        """Find the largest files that might need refactoring"""

        sorted_files = sorted(self.files, key=lambda f: f.get("size", 0), reverse=True)

        print(f"\n📊 Top {top_n} Largest Files (refactoring candidates):")
        print("-" * 60)

        results = []
        for i, file in enumerate(sorted_files[:top_n]):
            size_kb = file.get("size", 0) / 1024
            path = Path(file["relative_path"])

            print(f"{i+1:2}. {path.name:30} {size_kb:8.1f} KB")

            results.append(
                {
                    "path": file["relative_path"],
                    "size": file.get("size", 0),
                    "recommendation": "Consider splitting" if size_kb > 50 else "OK",
                }
            )

        return results

    def find_test_coverage_gaps(self) -> Dict[str, List[str]]:
        """Find modules without corresponding test files"""

        print("\n🧪 Test Coverage Analysis:")
        print("-" * 60)

        # Separate source and test files
        source_files = []
        test_files = []

        for file in self.files:
            path = file["relative_path"]
            if "test" in path.lower() or path.startswith("tests/"):
                test_files.append(path)
            elif path.endswith(".py") and not path.endswith("__init__.py"):
                source_files.append(path)

        # Find untested modules
        untested = []
        for source in source_files:
            # Expected test file name
            source_name = Path(source).stem
            expected_test = f"test_{source_name}.py"

            # Check if test exists
            has_test = any(expected_test in test for test in test_files)

            if not has_test:
                untested.append(source)

        print(f"Source modules: {len(source_files)}")
        print(f"Test files: {len(test_files)}")
        print(f"Untested modules: {len(untested)}")

        if untested:
            print("\n⚠️  Modules without tests:")
            for module in untested[:10]:  # Show first 10
                print(f"  - {module}")

        return {
            "source_files": source_files,
            "test_files": test_files,
            "untested": untested,
            "coverage_percentage": (1 - len(untested) / len(source_files)) * 100
            if source_files
            else 100,
        }

    def analyze_module_structure(self) -> Dict[str, Any]:
        """Analyze the module structure and organization"""

        print("\n🏗️ Module Structure Analysis:")
        print("-" * 60)

        # Group files by directory
        modules = {}
        for file in self.files:
            if file["file_type"] == "python":
                path = Path(file["relative_path"])
                module = str(path.parent) if path.parent != Path(".") else "root"

                if module not in modules:
                    modules[module] = {"files": [], "total_size": 0, "file_count": 0}

                modules[module]["files"].append(path.name)
                modules[module]["total_size"] += file.get("size", 0)
                modules[module]["file_count"] += 1

        # Sort by file count
        sorted_modules = sorted(
            modules.items(), key=lambda x: x[1]["file_count"], reverse=True
        )

        print(f"Total modules: {len(modules)}")
        print("\nModule breakdown:")
        for module, info in sorted_modules:
            size_kb = info["total_size"] / 1024
            print(f"  {module:30} {info['file_count']:3} files, {size_kb:8.1f} KB")

        return modules

    def generate_import_graph(self) -> Dict:
        """Generate a dependency graph from the project map"""

        print("\n🔗 Dependency Graph Analysis:")
        print("-" * 60)

        # Simple graph structure without networkx
        graph = {"nodes": [], "edges": []}

        # Add nodes for each Python file
        for file in self.files:
            if file["file_type"] == "python":
                graph["nodes"].append(file["relative_path"])

        # In real implementation, we would parse imports
        # For demo, we'll show the structure
        print(f"Nodes (files): {len(graph['nodes'])}")
        print(f"Edges (dependencies): {len(graph['edges'])}")

        # Find potential entry points (main files)
        entry_points = [
            node for node in graph["nodes"] if "__main__" in node or "main.py" in node
        ]
        print(f"Potential entry points: {len(entry_points)}")
        for entry in entry_points[:5]:
            print(f"  - {entry}")

        return graph

    def find_related_files(self, target_file: str) -> List[str]:
        """Find files related to a target file"""

        print(f"\n🔍 Finding files related to: {target_file}")
        print("-" * 60)

        related = []
        target_path = Path(target_file)
        target_module = target_path.parent
        target_name = target_path.stem

        for file in self.files:
            path = Path(file["relative_path"])

            # Same module
            if path.parent == target_module:
                related.append(file["relative_path"])
            # Test file for this module
            elif f"test_{target_name}" in path.name:
                related.append(file["relative_path"])
            # Similar name
            elif target_name in path.stem:
                related.append(file["relative_path"])

        print(f"Found {len(related)} related files:")
        for file in related[:10]:
            print(f"  - {file}")

        return related

    def generate_context_for_ai(self, task: str, max_files: int = 5) -> Dict[str, Any]:
        """Generate optimized context for AI operations"""

        print(f"\n🤖 Generating AI Context for: {task}")
        print("-" * 60)

        # Select relevant files based on task keywords
        relevant_files = []
        keywords = task.lower().split()

        for file in self.files:
            path = file["relative_path"].lower()
            if any(keyword in path for keyword in keywords):
                relevant_files.append(file)

        # Sort by relevance (simplified - by size)
        relevant_files.sort(key=lambda f: f.get("size", 0))

        # Build context
        context = {
            "task": task,
            "project": self.project,
            "relevant_files": relevant_files[:max_files],
            "file_count": len(relevant_files),
            "total_context_size": sum(
                f.get("size", 0) for f in relevant_files[:max_files]
            ),
        }

        print(f"Selected {len(relevant_files[:max_files])} files for context")
        print(f"Total context size: {context['total_context_size'] / 1024:.1f} KB")
        print("\nFiles included:")
        for file in relevant_files[:max_files]:
            print(f"  - {file['relative_path']} ({file.get('size', 0) / 1024:.1f} KB)")

        return context

    def suggest_refactoring_targets(self) -> List[Dict]:
        """Suggest files that might benefit from refactoring"""

        print("\n♻️ Refactoring Suggestions:")
        print("-" * 60)

        suggestions = []

        for file in self.files:
            if file["file_type"] != "python":
                continue

            size = file.get("size", 0)
            path = Path(file["relative_path"])

            # Criteria for refactoring
            reasons = []

            # Large file
            if size > 50000:  # > 50KB
                reasons.append("Large file")

            # Deep nesting
            if len(path.parts) > 4:
                reasons.append("Deep nesting")

            # Multiple responsibilities (heuristic based on name)
            if "_and_" in path.name or len(path.stem.split("_")) > 4:
                reasons.append("Multiple responsibilities")

            # God object pattern
            if any(
                name in path.stem.lower()
                for name in ["manager", "handler", "processor", "controller"]
            ):
                if size > 20000:
                    reasons.append("Potential god object")

            if reasons:
                suggestions.append(
                    {"file": file["relative_path"], "size": size, "reasons": reasons}
                )

        # Sort by number of reasons
        suggestions.sort(key=lambda x: len(x["reasons"]), reverse=True)

        print(f"Found {len(suggestions)} refactoring candidates\n")

        for i, suggestion in enumerate(suggestions[:10]):
            print(f"{i+1}. {suggestion['file']}")
            print(f"   Size: {suggestion['size'] / 1024:.1f} KB")
            print(f"   Reasons: {', '.join(suggestion['reasons'])}")

        return suggestions


def main():
    """Demonstrate practical uses of proj-mapper data"""

    print("=" * 70)
    print("LEVERAGING PROJ-MAPPER DATA - PRACTICAL EXAMPLES")
    print("=" * 70)

    # Find a project map to analyze
    project_map_path = Path(
        "/home/opsvi/master_root/libs/opsvi-core/.maps/project_map.json"
    )

    if not project_map_path.exists():
        print(f"❌ No project map found at {project_map_path}")
        print(
            "   Run: scripts/proj-mapper analyze /home/opsvi/master_root/libs/opsvi-core"
        )
        return 1

    # Create analyzer
    analyzer = ProjectMapAnalyzer(str(project_map_path))

    print(f"\n📁 Analyzing: {analyzer.project.get('name', 'Unknown')}")
    print(f"📍 Path: {analyzer.project.get('root_path', 'Unknown')}")
    print(f"📊 Total files: {len(analyzer.files)}")

    # Run various analyses

    # 1. Find large files
    analyzer.find_largest_files(top_n=5)

    # 2. Test coverage gaps
    coverage = analyzer.find_test_coverage_gaps()
    print(f"\n📈 Coverage: {coverage['coverage_percentage']:.1f}%")

    # 3. Module structure
    analyzer.analyze_module_structure()

    # 4. Generate dependency graph
    graph = analyzer.generate_import_graph()

    # 5. Find related files
    if analyzer.files:
        sample_file = analyzer.files[0]["relative_path"]
        analyzer.find_related_files(sample_file)

    # 6. Generate AI context
    analyzer.generate_context_for_ai("refactor authentication", max_files=3)

    # 7. Suggest refactoring
    analyzer.suggest_refactoring_targets()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(
        """
proj-mapper data enables:

✅ Automated code quality analysis
✅ Test coverage gap identification
✅ Intelligent refactoring suggestions
✅ AI-optimized context generation
✅ Dependency and relationship mapping
✅ Project structure visualization

This structured data becomes the foundation for:
- Automated code improvements
- Migration planning and execution
- Documentation generation
- Code review enhancement
- Developer onboarding
- Technical debt identification
"""
    )

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
