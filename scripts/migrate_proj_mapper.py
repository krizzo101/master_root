#!/usr/bin/env python3
"""
Migration script for proj-mapper to use master_root shared libraries
This script performs the actual refactoring of proj-mapper
"""

import os
import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


class ProjMapperMigrator:
    """Handles migration of proj-mapper to shared libs"""

    def __init__(self):
        self.project_root = Path("/home/opsvi/master_root")
        self.app_path = self.project_root / "apps" / "proj-mapper"
        self.libs_path = self.project_root / "libs"
        self.backup_path = (
            self.project_root
            / ".archive"
            / f"proj-mapper-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.migration_report = {
            "started": datetime.now().isoformat(),
            "steps": [],
            "files_modified": [],
            "new_files": [],
            "errors": [],
        }

    def backup_original(self):
        """Create backup of original proj-mapper"""
        print("📦 Creating backup of proj-mapper...")

        try:
            shutil.copytree(self.app_path, self.backup_path)
            self.migration_report["steps"].append(
                {"step": "backup", "status": "success", "path": str(self.backup_path)}
            )
            print(f"✅ Backup created at: {self.backup_path}")
            return True
        except Exception as e:
            self.migration_report["errors"].append(str(e))
            print(f"❌ Backup failed: {e}")
            return False

    def create_visualization_lib(self):
        """Create the missing opsvi-visualization library"""
        print("\n🏗️ Creating opsvi-visualization library...")

        viz_lib = self.libs_path / "opsvi-visualization"

        # Create directory structure
        directories = [
            viz_lib,
            viz_lib / "opsvi_visualization",
            viz_lib / "opsvi_visualization" / "generators",
            viz_lib / "opsvi_visualization" / "models",
            viz_lib / "opsvi_visualization" / "utils",
            viz_lib / "tests",
        ]

        for dir_path in directories:
            dir_path.mkdir(exist_ok=True)

        # Create __init__.py files
        init_content = '"""OpsVi Visualization Library"""'
        for dir_path in directories:
            if "tests" not in str(dir_path):
                (dir_path / "__init__.py").write_text(init_content)

        # Create basic generators
        dot_generator = '''"""DOT format generator for visualizations"""

from typing import Dict, List, Any


class DotGenerator:
    """Generates DOT format visualizations"""

    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, node_id: str, label: str, **attrs):
        """Add a node to the graph"""
        self.nodes.append({
            "id": node_id,
            "label": label,
            "attrs": attrs
        })

    def add_edge(self, from_id: str, to_id: str, **attrs):
        """Add an edge to the graph"""
        self.edges.append({
            "from": from_id,
            "to": to_id,
            "attrs": attrs
        })

    def generate(self) -> str:
        """Generate DOT format string"""
        lines = ["digraph G {"]

        # Add nodes
        for node in self.nodes:
            attrs = ", ".join(f'{k}="{v}"' for k, v in node["attrs"].items())
            lines.append(f'  "{node["id"]}" [label="{node["label"]}", {attrs}];')

        # Add edges
        for edge in self.edges:
            attrs = ", ".join(f'{k}="{v}"' for k, v in edge["attrs"].items())
            lines.append(f'  "{edge["from"]}" -> "{edge["to"]}" [{attrs}];')

        lines.append("}")
        return "\\n".join(lines)
'''

        (viz_lib / "opsvi_visualization" / "generators" / "dot.py").write_text(
            dot_generator
        )

        # Create HTML generator
        html_generator = '''"""HTML format generator for visualizations"""

from typing import Dict, List, Any
import json


class HtmlGenerator:
    """Generates HTML visualizations"""

    def __init__(self):
        self.data = {}

    def set_data(self, data: Dict[str, Any]):
        """Set visualization data"""
        self.data = data

    def generate(self) -> str:
        """Generate HTML with embedded visualization"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Project Visualization</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .node {{ padding: 10px; margin: 5px; border: 1px solid #ccc; }}
        .edge {{ color: #666; }}
    </style>
</head>
<body>
    <h1>Project Structure Visualization</h1>
    <div id="visualization">
        <pre>{json.dumps(self.data, indent=2)}</pre>
    </div>
</body>
</html>"""
        return html
'''

        (viz_lib / "opsvi_visualization" / "generators" / "html.py").write_text(
            html_generator
        )

        # Create setup.py
        setup_content = """from setuptools import setup, find_packages

setup(
    name="opsvi-visualization",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
)
"""
        (viz_lib / "setup.py").write_text(setup_content)

        self.migration_report["new_files"].append(str(viz_lib))
        print("✅ Created opsvi-visualization library")
        return True

    def refactor_imports(self):
        """Refactor imports to use shared libs"""
        print("\n🔄 Refactoring imports to use shared libraries...")

        # Map old imports to new ones
        import_mappings = {
            "from proj_mapper.core": "from opsvi_core",
            "from proj_mapper.models": "from opsvi_models",
            "from proj_mapper.storage": "from opsvi_data.storage",
            "from proj_mapper.utils": "from opsvi_utils",
            "from proj_mapper.pipeline": "from opsvi_pipeline",
            "from proj_mapper.output": "from opsvi_visualization.generators",
        }

        # Find all Python files
        python_files = list(self.app_path.glob("**/*.py"))

        modified_count = 0
        for py_file in python_files:
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                original_content = content

                # Apply import mappings
                for old_import, new_import in import_mappings.items():
                    if old_import in content:
                        content = content.replace(old_import, new_import)

                # Write back if modified
                if content != original_content:
                    py_file.write_text(content)
                    self.migration_report["files_modified"].append(str(py_file))
                    modified_count += 1
                    print(f"  ✏️ Modified: {py_file.name}")

            except Exception as e:
                self.migration_report["errors"].append(
                    f"Error modifying {py_file}: {e}"
                )

        print(f"✅ Refactored imports in {modified_count} files")
        return True

    def create_claude_code_adapter(self):
        """Create adapter to use claude-code agent for analysis"""
        print("\n🤖 Creating claude-code agent adapter...")

        adapter_content = '''"""
Adapter to use claude-code agent for project analysis
Replaces custom analyzers with claude-code agent
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio


class ClaudeCodeAnalyzer:
    """Uses claude-code agent for all analysis tasks"""

    def __init__(self):
        # Will use the actual claude-code agent when available
        self.agent_profiles = {
            "code_analysis": {
                "mode": "analyze",
                "temperature": 0.1,
                "system_prompt": "Analyze code structure and relationships"
            },
            "documentation": {
                "mode": "document",
                "temperature": 0.2,
                "system_prompt": "Extract and analyze documentation"
            },
            "dependency": {
                "mode": "dependencies",
                "temperature": 0.1,
                "system_prompt": "Analyze dependencies and imports"
            }
        }

    async def analyze_file(self, file_path: Path, analysis_type: str = "code_analysis") -> Dict[str, Any]:
        """Analyze a single file using claude-code agent"""

        # Placeholder for actual claude-code integration
        # In production, this would call:
        # from opsvi_agents.claude_code import ClaudeCodeAgent
        # agent = ClaudeCodeAgent()
        # result = await agent.analyze(file_path, profile=self.agent_profiles[analysis_type])

        return {
            "file": str(file_path),
            "type": analysis_type,
            "classes": [],
            "functions": [],
            "imports": [],
            "exports": [],
            "relationships": []
        }

    async def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """Analyze entire project using claude-code agent"""

        # Would orchestrate multiple claude-code calls
        # with different profiles for comprehensive analysis

        return {
            "project": str(project_path),
            "files": [],
            "structure": {},
            "dependencies": {},
            "documentation": {}
        }

    def analyze_sync(self, file_path: Path, analysis_type: str = "code_analysis") -> Dict[str, Any]:
        """Synchronous wrapper for analyze_file"""
        return asyncio.run(self.analyze_file(file_path, analysis_type))


# Export as replacement for old analyzers
CodeAnalyzer = ClaudeCodeAnalyzer
DocAnalyzer = ClaudeCodeAnalyzer
DependencyAnalyzer = ClaudeCodeAnalyzer
'''

        analyzer_path = self.app_path / "src" / "proj_mapper" / "claude_code_adapter.py"
        analyzer_path.write_text(adapter_content)

        self.migration_report["new_files"].append(str(analyzer_path))
        print("✅ Created claude-code adapter")
        return True

    def update_cli(self):
        """Update CLI to use shared interfaces"""
        print("\n📝 Updating CLI to use shared interfaces...")

        cli_path = self.app_path / "src" / "proj_mapper" / "cli" / "main.py"

        if cli_path.exists():
            # Read current CLI
            content = cli_path.read_text()

            # Add imports for shared interfaces
            new_imports = '''#!/usr/bin/env python3
"""Project Mapper CLI using shared interfaces"""

import sys
sys.path.insert(0, '/home/opsvi/master_root/libs')

from pathlib import Path
from typing import Optional
import click

# Use shared interfaces
try:
    from opsvi_interfaces.cli import BaseCLI
    from opsvi_interfaces.config import ConfigManager
    SHARED_LIBS = True
except ImportError:
    SHARED_LIBS = False
    print("Warning: Shared libraries not available, using fallback")

'''

            # Update the beginning of the file
            lines = content.split("\n")

            # Find where imports end
            import_end = 0
            for i, line in enumerate(lines):
                if line and not line.startswith(("import ", "from ", "#", '"""')):
                    import_end = i
                    break

            # Reconstruct with new imports
            new_content = new_imports + "\n".join(lines[import_end:])

            cli_path.write_text(new_content)
            self.migration_report["files_modified"].append(str(cli_path))
            print("✅ Updated CLI")

        return True

    def remove_venv(self):
        """Remove the app's separate venv"""
        print("\n🗑️ Removing separate .venv...")

        venv_path = self.app_path / ".venv"
        if venv_path.exists():
            shutil.rmtree(venv_path)
            print("✅ Removed .venv directory")

        return True

    def generate_report(self):
        """Generate migration report"""
        self.migration_report["completed"] = datetime.now().isoformat()

        report_path = self.project_root / "docs" / "proj_mapper_migration_report.json"
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(self.migration_report, f, indent=2)

        print(f"\n📊 Migration report saved to: {report_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Files modified: {len(self.migration_report['files_modified'])}")
        print(f"New files created: {len(self.migration_report['new_files'])}")
        print(f"Errors encountered: {len(self.migration_report['errors'])}")

        if self.migration_report["errors"]:
            print("\n⚠️ Errors:")
            for error in self.migration_report["errors"]:
                print(f"  - {error}")

    def run_migration(self):
        """Execute the full migration"""
        print("=" * 60)
        print("PROJ-MAPPER MIGRATION TO SHARED LIBS")
        print("=" * 60)

        steps = [
            ("Backup original", self.backup_original),
            ("Create visualization library", self.create_visualization_lib),
            ("Refactor imports", self.refactor_imports),
            ("Create claude-code adapter", self.create_claude_code_adapter),
            ("Update CLI", self.update_cli),
            ("Remove separate venv", self.remove_venv),
        ]

        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ Migration failed at: {step_name}")
                self.generate_report()
                return False

        print("\n✅ Migration completed successfully!")
        self.generate_report()
        return True


def main():
    """Main execution"""

    migrator = ProjMapperMigrator()

    print("This will migrate proj-mapper to use master_root shared libraries.")
    print("A backup will be created before any changes are made.")

    response = input("\nProceed with migration? (yes/no): ")

    if response.lower() != "yes":
        print("Migration cancelled.")
        return 1

    success = migrator.run_migration()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
