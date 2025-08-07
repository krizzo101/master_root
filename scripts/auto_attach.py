#!/usr/bin/env python3
"""
Auto-Attach Script

Uses the optimized file_dependencies.json to automatically find and attach
related files for the consult agent gatekeeper functionality.
"""

import json
import os
import sys
from typing import List, Set, Dict, Any
from pathlib import Path


class AutoAttach:
    """Auto-attach functionality using optimized file dependencies."""

    def __init__(self, dependencies_file: str = ".proj-intel/file_dependencies.json"):
        self.dependencies_file = dependencies_file
        self.data = None
        self.loaded = False

    def load_dependencies(self) -> bool:
        """Load the file dependencies data."""
        try:
            with open(self.dependencies_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.loaded = True
            print(f"✅ Loaded dependencies for {self.data['metadata']['total_files']} files")
            return True
        except FileNotFoundError:
            print(f"❌ Dependencies file not found: {self.dependencies_file}")
            print("Run: python scripts/auto_attach_generator.py to generate dependencies")
            return False
        except Exception as e:
            print(f"❌ Error loading dependencies: {e}")
            return False

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a specific file."""
        if not self.loaded:
            return {}

        return self.data["files"].get(file_path, {})

    def find_related_files(self, user_files: List[str]) -> List[str]:
        """
        Find all related files for the given user files.

        Args:
            user_files: List of file paths provided by the user

        Returns:
            List of related file paths including the original files
        """
        if not self.loaded:
            print("❌ Dependencies not loaded")
            return user_files

        related_files = set(user_files)

        for user_file in user_files:
            file_info = self.data["files"].get(user_file)
            if not file_info:
                print(f"⚠️  File not found in dependencies: {user_file}")
                continue

            print(f"🔍 Analyzing: {user_file}")

            # Add files that this file imports
            for module in file_info.get("imports", []):
                importers = self.data["indexes"]["by_import"].get(module, [])
                if importers:
                    print(f"  ➕ Adding imported files: {len(importers)} files")
                    related_files.update(importers)

            # Add files that import this file
            imported_by = file_info.get("imported_by", [])
            if imported_by:
                print(f"  ➕ Adding files that import this: {len(imported_by)} files")
                related_files.update(imported_by)

            # Add files in the same directory
            directory = file_info.get("directory", "")
            if directory:
                same_dir_files = self.data["indexes"]["by_directory"].get(directory, [])
                if same_dir_files:
                    print(f"  ➕ Adding files in same directory: {len(same_dir_files)} files")
                    related_files.update(same_dir_files)

            # Add configuration files in the same directory
            config_files = self.data["indexes"]["by_type"].get("config", [])
            directory_configs = [f for f in config_files if f.startswith(directory)]
            if directory_configs:
                print(f"  ➕ Adding config files in directory: {len(directory_configs)} files")
                related_files.update(directory_configs)

            # Add test files for this file
            test_files = self.data["indexes"]["by_type"].get("test", [])
            file_name = os.path.basename(user_file).replace('.py', '')
            related_tests = []
            for test_file in test_files:
                test_name = os.path.basename(test_file)
                if (file_name in test_name or
                    test_name.startswith(f"test_{file_name}") or
                    test_name.endswith(f"{file_name}_test.py")):
                    related_tests.append(test_file)

            if related_tests:
                print(f"  ➕ Adding related test files: {len(related_tests)} files")
                related_files.update(related_tests)

        result = list(related_files)
        print(f"📊 Total related files found: {len(result)} (original: {len(user_files)})")
        return result

    def filter_files_by_type(self, files: List[str], file_types: List[str]) -> List[str]:
        """Filter files by type."""
        if not self.loaded:
            return files

        filtered = []
        for file_path in files:
            file_info = self.data["files"].get(file_path, {})
            if file_info.get("file_type") in file_types:
                filtered.append(file_path)

        return filtered

    def get_files_by_directory(self, directory: str) -> List[str]:
        """Get all files in a specific directory."""
        if not self.loaded:
            return []

        return self.data["indexes"]["by_directory"].get(directory, [])

    def get_files_by_type(self, file_type: str) -> List[str]:
        """Get all files of a specific type."""
        if not self.loaded:
            return []

        return self.data["indexes"]["by_type"].get(file_type, [])

    def get_importers(self, module: str) -> List[str]:
        """Get all files that import a specific module."""
        if not self.loaded:
            return []

        return self.data["indexes"]["by_import"].get(module, [])

    def analyze_file_dependencies(self, file_path: str) -> Dict[str, Any]:
        """Analyze dependencies for a single file."""
        if not self.loaded:
            return {}

        file_info = self.data["files"].get(file_path, {})
        if not file_info:
            return {}

        analysis = {
            "file_path": file_path,
            "file_type": file_info.get("file_type"),
            "line_count": file_info.get("line_count"),
            "directory": file_info.get("directory"),
            "imports": file_info.get("imports", []),
            "imported_by": file_info.get("imported_by", []),
            "related_files": {
                "imported_files": [],
                "importing_files": [],
                "same_directory": [],
                "config_files": [],
                "test_files": []
            }
        }

        # Find imported files
        for module in file_info.get("imports", []):
            importers = self.data["indexes"]["by_import"].get(module, [])
            analysis["related_files"]["imported_files"].extend(importers)

        # Find importing files
        analysis["related_files"]["importing_files"] = file_info.get("imported_by", [])

        # Find same directory files
        directory = file_info.get("directory", "")
        if directory:
            analysis["related_files"]["same_directory"] = self.data["indexes"]["by_directory"].get(directory, [])

        # Find config files in same directory
        config_files = self.data["indexes"]["by_type"].get("config", [])
        if directory:
            analysis["related_files"]["config_files"] = [f for f in config_files if f.startswith(directory)]

        # Find related test files
        test_files = self.data["indexes"]["by_type"].get("test", [])
        file_name = os.path.basename(file_path).replace('.py', '')
        for test_file in test_files:
            test_name = os.path.basename(test_file)
            if (file_name in test_name or
                test_name.startswith(f"test_{file_name}") or
                test_name.endswith(f"{file_name}_test.py")):
                analysis["related_files"]["test_files"].append(test_file)

        return analysis


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-attach related files")
    parser.add_argument("files", nargs="+", help="Files to find related files for")
    parser.add_argument("--dependencies", default=".proj-intel/file_dependencies.json",
                       help="Path to file_dependencies.json")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--analyze", action="store_true", help="Show detailed analysis")

    args = parser.parse_args()

    auto_attach = AutoAttach(args.dependencies)

    if not auto_attach.load_dependencies():
        return 1

    print(f"🔍 Finding related files for: {args.files}")
    related_files = auto_attach.find_related_files(args.files)

    if args.analyze:
        print("\n📋 Detailed Analysis:")
        for file_path in args.files:
            analysis = auto_attach.analyze_file_dependencies(file_path)
            if analysis:
                print(f"\n📄 {file_path}:")
                print(f"   Type: {analysis['file_type']}")
                print(f"   Lines: {analysis['line_count']}")
                print(f"   Directory: {analysis['directory']}")
                print(f"   Imports: {len(analysis['imports'])} modules")
                print(f"   Imported by: {len(analysis['imported_by'])} files")
                print(f"   Related files: {len(analysis['related_files']['imported_files'])} imported, "
                      f"{len(analysis['related_files']['importing_files'])} importing, "
                      f"{len(analysis['related_files']['same_directory'])} same dir, "
                      f"{len(analysis['related_files']['config_files'])} config, "
                      f"{len(analysis['related_files']['test_files'])} test")

    print(f"\n📋 Related files ({len(related_files)} total):")
    for file_path in sorted(related_files):
        file_info = auto_attach.get_file_info(file_path)
        file_type = file_info.get("file_type", "unknown")
        print(f"  {file_path} ({file_type})")

    if args.output:
        result = {
            "input_files": args.files,
            "related_files": related_files,
            "total_count": len(related_files),
            "analysis": {}
        }

        if args.analyze:
            for file_path in args.files:
                result["analysis"][file_path] = auto_attach.analyze_file_dependencies(file_path)

        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    exit(main())
