#!/usr/bin/env python3
"""
Comprehensive demonstration of proj-mapper capabilities
Shows what it creates, how to use the data, and its value
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/apps/proj-mapper/src")

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


class ProjMapperDemo:
    """Demonstrates proj-mapper capabilities and value"""

    def __init__(self):
        self.project_root = Path("/home/opsvi/master_root")
        self.target_project = self.project_root / "libs" / "opsvi-core"

    def run_analysis(self):
        """Run proj-mapper analysis on a project"""

        print("=" * 70)
        print("PROJ-MAPPER DEMONSTRATION")
        print("=" * 70)
        print(f"\nAnalyzing: {self.target_project}")
        print("-" * 70)

        # Run analysis
        cmd = [
            "/home/opsvi/miniconda/bin/python",
            str(self.project_root / "apps/proj-mapper/src/proj_mapper/cli/main.py"),
            "analyze",
            str(self.target_project),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={
                "PYTHONPATH": f"{self.project_root}/libs:{self.project_root}/apps/proj-mapper/src"
            },
        )

        if result.returncode == 0:
            print("✅ Analysis completed successfully")
        else:
            print(f"❌ Analysis failed: {result.stderr}")
            return False

        return True

    def show_generated_files(self):
        """Show what files proj-mapper generates"""

        print("\n📁 GENERATED FILES:")
        print("-" * 70)

        maps_dir = self.target_project / ".maps"

        if maps_dir.exists():
            for file in maps_dir.iterdir():
                size = file.stat().st_size
                print(f"  - {file.name} ({size:,} bytes)")

                # Show sample of each file type
                if file.suffix == ".json":
                    with open(file) as f:
                        data = json.load(f)
                        self.analyze_json_structure(data, file.name)
                elif file.suffix == ".dot":
                    print(
                        f"    → DOT graph visualization (can be rendered with Graphviz)"
                    )
                elif file.suffix == ".html":
                    print(f"    → Interactive HTML visualization")
        else:
            print("  No .maps directory found")

    def analyze_json_structure(self, data: Dict, filename: str):
        """Analyze and explain the JSON structure"""

        print(f"\n  📊 Structure of {filename}:")

        if "project" in data:
            project = data["project"]
            print(f"    Project: {project.get('name', 'Unknown')}")
            print(f"    Root: {project.get('root_path', 'Unknown')}")

        if "files" in data:
            files = data["files"]
            print(f"    Files discovered: {len(files)}")

            # Categorize files
            by_type = {}
            for file in files:
                ftype = file.get("file_type", "unknown")
                by_type[ftype] = by_type.get(ftype, 0) + 1

            print("    File types:")
            for ftype, count in sorted(by_type.items()):
                print(f"      - {ftype}: {count}")

        if "code_elements" in data:
            elements = data["code_elements"]
            print(f"    Code elements found: {len(elements)}")

            # Count element types
            by_type = {}
            for elem in elements:
                etype = elem.get("type", "unknown")
                by_type[etype] = by_type.get(etype, 0) + 1

            print("    Element types:")
            for etype, count in sorted(by_type.items()):
                print(f"      - {etype}: {count}")

        if "relationships" in data:
            relationships = data.get("relationships", [])
            if relationships:
                print(f"    Relationships found: {len(relationships)}")

    def demonstrate_value_propositions(self):
        """Show how proj-mapper data can be leveraged"""

        print("\n💡 VALUE PROPOSITIONS & USE CASES:")
        print("=" * 70)

        use_cases = [
            {
                "title": "1. AI-Optimized Context Building",
                "description": "The structured map provides perfect context for AI agents",
                "benefits": [
                    "- Reduces token usage by providing only relevant files",
                    "- Enables better code understanding through relationships",
                    "- Facilitates targeted code modifications",
                ],
                "example": "When asking AI to refactor a class, include its dependencies from the map",
            },
            {
                "title": "2. Dependency Analysis",
                "description": "Understand project dependencies and coupling",
                "benefits": [
                    "- Identify circular dependencies",
                    "- Find unused modules",
                    "- Detect high-coupling areas that need refactoring",
                ],
                "example": "Find all files that depend on a module before refactoring it",
            },
            {
                "title": "3. Documentation Generation",
                "description": "Auto-generate documentation from code structure",
                "benefits": [
                    "- Create architecture diagrams automatically",
                    "- Generate API documentation",
                    "- Build dependency graphs",
                ],
                "example": "Generate README with accurate project structure",
            },
            {
                "title": "4. Code Navigation & Search",
                "description": "Navigate large codebases efficiently",
                "benefits": [
                    "- Find implementations quickly",
                    "- Trace execution paths",
                    "- Locate related code across modules",
                ],
                "example": "Find all classes that inherit from BaseAgent",
            },
            {
                "title": "5. Migration Planning",
                "description": "Plan and execute code migrations",
                "benefits": [
                    "- Identify all files needing changes",
                    "- Understand impact radius",
                    "- Generate migration scripts",
                ],
                "example": "Migrate all custom agents to claude-code agent",
            },
            {
                "title": "6. Test Coverage Analysis",
                "description": "Map code to tests and find gaps",
                "benefits": [
                    "- Identify untested modules",
                    "- Find orphaned tests",
                    "- Generate test stubs for uncovered code",
                ],
                "example": "Find all classes without corresponding test files",
            },
            {
                "title": "7. Code Review Assistance",
                "description": "Enhance code reviews with context",
                "benefits": [
                    "- Show impact of changes",
                    "- Identify affected components",
                    "- Suggest related files to review",
                ],
                "example": "When reviewing a PR, see all dependent modules",
            },
            {
                "title": "8. Onboarding New Developers",
                "description": "Help new team members understand the codebase",
                "benefits": [
                    "- Visual project overview",
                    "- Interactive exploration",
                    "- Key component identification",
                ],
                "example": "Generate interactive HTML map for new developers",
            },
        ]

        for use_case in use_cases:
            print(f"\n{use_case['title']}")
            print("-" * 50)
            print(f"📝 {use_case['description']}")
            print("\n🎯 Benefits:")
            for benefit in use_case["benefits"]:
                print(f"  {benefit}")
            print(f"\n💭 Example: {use_case['example']}")

    def show_integration_examples(self):
        """Show how to integrate proj-mapper data with other tools"""

        print("\n🔧 INTEGRATION EXAMPLES:")
        print("=" * 70)

        examples = """
1. With Claude-Code Agent:
   ```python
   # Load project map
   with open('.maps/project_map.json') as f:
       project_map = json.load(f)

   # Find relevant files for a task
   relevant_files = find_related_files(project_map, "BaseAgent")

   # Provide context to claude-code
   context = build_context_from_files(relevant_files)
   result = claude_code_agent.execute(task, context=context)
   ```

2. With Test Coverage Scanner:
   ```python
   # Find all modules
   modules = [f for f in project_map['files'] if f['file_type'] == 'python']

   # Check for corresponding tests
   for module in modules:
       test_file = find_test_file(module['path'])
       if not test_file:
           generate_test_stub(module)
   ```

3. With Migration Tools:
   ```python
   # Find all files importing old module
   dependencies = project_map['relationships']
   affected_files = [r['source'] for r in dependencies
                     if r['target'] == 'old_module.py']

   # Generate migration script
   for file in affected_files:
       update_imports(file, old='old_module', new='new_module')
   ```

4. With Documentation Generator:
   ```python
   # Generate architecture documentation
   classes = [e for e in project_map['code_elements']
              if e['type'] == 'class']

   doc = generate_class_diagram(classes)
   doc += generate_dependency_graph(project_map['relationships'])
   save_documentation(doc)
   ```

5. With Code Quality Tools:
   ```python
   # Find high-complexity areas
   for file in project_map['files']:
       complexity = calculate_complexity(file)
       if complexity > threshold:
           suggest_refactoring(file)
   ```
"""
        print(examples)

    def show_queries_examples(self):
        """Show example queries you can run on the data"""

        print("\n🔍 EXAMPLE QUERIES ON PROJECT MAP DATA:")
        print("=" * 70)

        queries = [
            {
                "question": "Which files have the most dependencies?",
                "code": "sorted(files, key=lambda f: len(f['imports']), reverse=True)[:10]",
            },
            {
                "question": "What are the entry points to the system?",
                "code": "files_with_main = [f for f in files if '__main__' in f['content']]",
            },
            {
                "question": "Which modules are never imported?",
                "code": "all_imports = set(chain(*[f['imports'] for f in files]))\nunused = [f for f in files if f['path'] not in all_imports]",
            },
            {
                "question": "What's the inheritance hierarchy?",
                "code": "inheritance = [(r['source'], r['target']) for r in relationships if r['type'] == 'inherits']",
            },
            {
                "question": "Find circular dependencies",
                "code": "cycles = find_cycles_in_graph(relationships)",
            },
        ]

        for query in queries:
            print(f"\n❓ {query['question']}")
            print(f"   ```python")
            print(f"   {query['code']}")
            print(f"   ```")

    def run_demo(self):
        """Run the complete demonstration"""

        # Run analysis
        if not self.run_analysis():
            print("Demo failed - could not analyze project")
            return

        # Show generated files
        self.show_generated_files()

        # Show value propositions
        self.demonstrate_value_propositions()

        # Show integration examples
        self.show_integration_examples()

        # Show query examples
        self.show_queries_examples()

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(
            """
proj-mapper is a powerful tool that:

✅ Creates structured, searchable project maps
✅ Identifies relationships and dependencies
✅ Generates multiple visualization formats
✅ Provides AI-optimized context for code operations
✅ Enables sophisticated project analysis and navigation
✅ Facilitates migrations, refactoring, and documentation
✅ Integrates with other tools in the ecosystem

The generated data becomes the foundation for intelligent
automation, better code understanding, and efficient development.
"""
        )


def main():
    """Main execution"""
    demo = ProjMapperDemo()
    demo.run_demo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
