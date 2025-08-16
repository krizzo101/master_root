#!/usr/bin/env python3
"""
Auto-Attach File Generator

Generates optimized file_dependencies.json from existing project_map.yaml
for use by the auto-attach script functionality.
"""

import json
import yaml
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Any
from datetime import datetime
import time


class AutoAttachGenerator:
    """Generates optimized file dependencies for auto-attach functionality."""

    def __init__(self, project_map_path: str, output_path: str):
        self.project_map_path = project_map_path
        self.output_path = output_path
        self.project_map_data = None
        self.files_data = {}
        self.indexes = {
            "by_directory": {},
            "by_import": {},
            "by_type": {}
        }

    def load_project_map(self) -> bool:
        """Load and parse the project map YAML file."""
        try:
            with open(self.project_map_path, 'r', encoding='utf-8') as f:
                self.project_map_data = yaml.safe_load(f)
            return True
        except Exception as e:
            print(f"Error loading project map: {e}")
            return False

    def classify_file_type(self, file_path: str) -> str:
        """Classify file type based on path and patterns."""
        path_lower = file_path.lower()

        # Test files
        if (re.match(r'test_.*\.py$', os.path.basename(file_path)) or
            re.match(r'.*_test\.py$', os.path.basename(file_path)) or
            re.match(r'.*Test\.py$', os.path.basename(file_path)) or
            re.match(r'.*_spec\.py$', os.path.basename(file_path)) or
            re.match(r'.*Spec\.py$', os.path.basename(file_path))):
            return "test"

        # Configuration files
        config_patterns = [
            'package.json', 'requirements.txt', 'pyproject.toml', 'setup.py',
            '.env', 'config.py', 'settings.py', '*.yaml', '*.yml', '*.toml',
            '*.ini', '*.cfg', '*.conf'
        ]
        for pattern in config_patterns:
            if pattern.startswith('*'):
                if path_lower.endswith(pattern[1:]):
                    return "config"
            elif os.path.basename(file_path) == pattern:
                return "config"

        # Documentation files
        doc_patterns = ['.md', '.rst', '.txt']
        for ext in doc_patterns:
            if path_lower.endswith(ext):
                return "documentation"

        # Source files (Python)
        if path_lower.endswith('.py'):
            return "source"

        # Default to source for unknown types
        return "source"

    def normalize_import(self, import_statement: str, current_file: str) -> str:
        """Normalize import statement to module name."""
        # Remove file extensions
        module = import_statement.replace('.py', '')

        # Handle relative imports (simplified)
        if module.startswith('.'):
            # Convert relative import to absolute based on current file
            current_dir = os.path.dirname(current_file).replace('/', '.')
            if current_dir:
                module = current_dir + module
            else:
                module = module[1:]  # Remove leading dot

        # Handle aliased imports
        if ' as ' in module:
            module = module.split(' as ')[0]

        # Handle from imports
        if module.startswith('from '):
            parts = module.split(' ')
            if len(parts) >= 2:
                module = parts[1]

        return module.strip()

    def extract_imports_from_filemap(self, filemap_json: str, file_path: str) -> List[str]:
        """Extract normalized imports from filemap JSON string."""
        try:
            filemap = json.loads(filemap_json)
            imports = []

            # Extract imports from code_elements
            if 'code_elements' in filemap and 'imports' in filemap['code_elements']:
                for imp in filemap['code_elements']['imports']:
                    if 'module' in imp:
                        normalized = self.normalize_import(imp['module'], file_path)
                        if normalized and normalized not in imports:
                            imports.append(normalized)

            return imports
        except (json.JSONDecodeError, KeyError):
            return []

    def process_files(self):
        """Process files from project map and build optimized structure."""
        if not self.project_map_data or 'files' not in self.project_map_data:
            print("No files data found in project map")
            return

        # Process each file
        for file_info in self.project_map_data['files']:
            if not isinstance(file_info, dict) or 'path' not in file_info:
                continue

            file_path = file_info['path']
            line_count = file_info.get('line_count', 0)
            filemap_json = file_info.get('filemap', '{}')

            # Extract imports
            imports = self.extract_imports_from_filemap(filemap_json, file_path)

            # Determine directory
            directory = os.path.dirname(file_path)

            # Classify file type
            file_type = self.classify_file_type(file_path)

            # Store file data
            self.files_data[file_path] = {
                "imports": imports,
                "imported_by": [],  # Will be populated later
                "directory": directory,
                "file_type": file_type,
                "line_count": line_count
            }

            # Build directory index
            if directory not in self.indexes["by_directory"]:
                self.indexes["by_directory"][directory] = []
            self.indexes["by_directory"][directory].append(file_path)

            # Build type index
            if file_type not in self.indexes["by_type"]:
                self.indexes["by_type"][file_type] = []
            self.indexes["by_type"][file_type].append(file_path)

        # Build import index and imported_by relationships
        self.build_import_relationships()

    def build_import_relationships(self):
        """Build bidirectional import relationships."""
        # First pass: build import index
        for file_path, file_info in self.files_data.items():
            for module in file_info["imports"]:
                if module not in self.indexes["by_import"]:
                    self.indexes["by_import"][module] = []
                self.indexes["by_import"][module].append(file_path)

        # Second pass: build imported_by relationships
        for file_path, file_info in self.files_data.items():
            # Find what files import this file
            imported_by = []
            for module, importers in self.indexes["by_import"].items():
                # Check if this file corresponds to the module
                if self.file_matches_module(file_path, module):
                    imported_by.extend(importers)

            # Remove duplicates and self-references
            imported_by = list(set(imported_by) - {file_path})
            self.files_data[file_path]["imported_by"] = imported_by

    def file_matches_module(self, file_path: str, module: str) -> bool:
        """Check if a file path corresponds to a module name."""
        # Convert file path to module format
        file_module = file_path.replace('/', '.').replace('.py', '')

        # Handle different module formats
        if module == file_module:
            return True

        # Handle package __init__.py files
        if file_path.endswith('/__init__.py'):
            package_module = file_path[:-12].replace('/', '.')  # Remove /__init__.py
            if module == package_module:
                return True

        return False

    def generate_metadata(self) -> Dict[str, Any]:
        """Generate metadata for the output file."""
        return {
            "generated_at": datetime.now().isoformat(),
            "total_files": len(self.files_data),
            "base_path": self.project_map_data.get('base_path', ''),
            "schema_version": "1.0.0",
            "file_size_bytes": 0,  # Will be calculated after writing
            "generation_time_ms": 0  # Will be calculated
        }

    def generate_output(self) -> Dict[str, Any]:
        """Generate the complete output structure."""
        return {
            "files": self.files_data,
            "indexes": self.indexes,
            "metadata": self.generate_metadata()
        }

    def save_output(self, output_data: Dict[str, Any]):
        """Save the output to JSON file."""
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            # Update file size in metadata
            file_size = os.path.getsize(self.output_path)
            output_data["metadata"]["file_size_bytes"] = file_size

            # Write updated metadata
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"Generated auto-attach file: {self.output_path}")
            print(f"Total files: {len(self.files_data)}")
            print(f"File size: {file_size} bytes")

        except Exception as e:
            print(f"Error saving output: {e}")

    def run(self) -> bool:
        """Run the complete generation process."""
        start_time = time.time()

        print(f"Loading project map from: {self.project_map_path}")
        if not self.load_project_map():
            return False

        print("Processing files...")
        self.process_files()

        print("Generating output...")
        output_data = self.generate_output()

        # Calculate generation time
        generation_time = int((time.time() - start_time) * 1000)
        output_data["metadata"]["generation_time_ms"] = generation_time

        print(f"Saving output to: {self.output_path}")
        self.save_output(output_data)

        print(f"Generation completed in {generation_time}ms")
        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate auto-attach optimized file dependencies")
    parser.add_argument("--project-map", default=".proj-intel/project_map.yaml",
                       help="Path to project_map.yaml file")
    parser.add_argument("--output", default=".proj-intel/file_dependencies.json",
                       help="Output path for file_dependencies.json")

    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    generator = AutoAttachGenerator(args.project_map, args.output)
    success = generator.run()

    if success:
        print("✅ Auto-attach file generation completed successfully")
    else:
        print("❌ Auto-attach file generation failed")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
