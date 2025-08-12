#!/usr/bin/env python3
"""
Auto-Attach Module

Provides intelligent file dependency analysis for gatekeeper functionality.
Can be used independently or as part of the gatekeeper agent.
"""

import json
import os
from typing import Any


class AutoAttach:
    """Auto-attach functionality using optimized file dependencies."""

    def __init__(self, dependencies_file: str = ".proj-intel/file_dependencies.json"):
        self.dependencies_file = dependencies_file
        self.data = None
        self.loaded = False

    def load_dependencies(self) -> bool:
        """Load the file dependencies data."""
        try:
            with open(self.dependencies_file, encoding="utf-8") as f:
                self.data = json.load(f)
            self.loaded = True
            return True
        except FileNotFoundError:
            print(f"❌ Dependencies file not found: {self.dependencies_file}")
            print(
                "Run: python scripts/auto_attach_generator.py to generate dependencies"
            )
            return False
        except Exception as e:
            print(f"❌ Error loading dependencies: {e}")
            return False

    def get_file_info(self, file_path: str) -> dict[str, Any]:
        """Get information about a specific file."""
        if not self.loaded:
            return {}

        return self.data["files"].get(file_path, {})

    def find_related_files(
        self, user_files: list[str], verbose: bool = False
    ) -> list[str]:
        """
        Find all related files for the given user files.

        Args:
            user_files: List of file paths provided by the user
            verbose: Whether to print detailed analysis information

        Returns:
            List of related file paths including the original files
        """
        if not self.loaded:
            if verbose:
                print("❌ Dependencies not loaded")
            return user_files

        related_files = set(user_files)

        for user_file in user_files:
            file_info = self.data["files"].get(user_file)
            if not file_info:
                if verbose:
                    print(f"⚠️  File not found in dependencies: {user_file}")
                continue

            if verbose:
                print(f"🔍 Analyzing: {user_file}")

            # Add files that this file imports
            for module in file_info.get("imports", []):
                importers = self.data["indexes"]["by_import"].get(module, [])
                if importers:
                    if verbose:
                        print(f"  ➕ Adding imported files: {len(importers)} files")
                    related_files.update(importers)

            # Add files that import this file
            imported_by = file_info.get("imported_by", [])
            if imported_by:
                if verbose:
                    print(
                        f"  ➕ Adding files that import this: {len(imported_by)} files"
                    )
                related_files.update(imported_by)

            # Add files in the same directory
            directory = file_info.get("directory", "")
            if directory:
                same_dir_files = self.data["indexes"]["by_directory"].get(directory, [])
                if same_dir_files:
                    if verbose:
                        print(
                            f"  ➕ Adding files in same directory: {len(same_dir_files)} files"
                        )
                    related_files.update(same_dir_files)

            # Add configuration files in the same directory
            config_files = self.data["indexes"]["by_type"].get("config", [])
            directory_configs = [f for f in config_files if f.startswith(directory)]
            if directory_configs:
                if verbose:
                    print(
                        f"  ➕ Adding config files in directory: {len(directory_configs)} files"
                    )
                related_files.update(directory_configs)

            # Add test files for this file
            test_files = self.data["indexes"]["by_type"].get("test", [])
            file_name = os.path.basename(user_file).replace(".py", "")
            related_tests = []
            for test_file in test_files:
                test_name = os.path.basename(test_file)
                if (
                    file_name in test_name
                    or test_name.startswith(f"test_{file_name}")
                    or test_name.endswith(f"{file_name}_test.py")
                ):
                    related_tests.append(test_file)

            if related_tests:
                if verbose:
                    print(f"  ➕ Adding related test files: {len(related_tests)} files")
                related_files.update(related_tests)

        result = list(related_files)
        if verbose:
            print(
                f"📊 Total related files found: {len(result)} (original: {len(user_files)})"
            )
        return result

    def filter_files_by_type(
        self, files: list[str], file_types: list[str]
    ) -> list[str]:
        """Filter files by type."""
        if not self.loaded:
            return files

        filtered = []
        for file_path in files:
            file_info = self.data["files"].get(file_path, {})
            if file_info.get("file_type") in file_types:
                filtered.append(file_path)

        return filtered

    def get_files_by_directory(self, directory: str) -> list[str]:
        """Get all files in a specific directory."""
        if not self.loaded:
            return []

        return self.data["indexes"]["by_directory"].get(directory, [])

    def get_files_by_type(self, file_type: str) -> list[str]:
        """Get all files of a specific type."""
        if not self.loaded:
            return []

        return self.data["indexes"]["by_type"].get(file_type, [])

    def get_importers(self, module: str) -> list[str]:
        """Get all files that import a specific module."""
        if not self.loaded:
            return []

        return self.data["indexes"]["by_import"].get(module, [])

    def analyze_file_dependencies(self, file_path: str) -> dict[str, Any]:
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
                "test_files": [],
            },
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
            analysis["related_files"]["same_directory"] = self.data["indexes"][
                "by_directory"
            ].get(directory, [])

        # Find config files in same directory
        config_files = self.data["indexes"]["by_type"].get("config", [])
        if directory:
            analysis["related_files"]["config_files"] = [
                f for f in config_files if f.startswith(directory)
            ]

        # Find related test files
        test_files = self.data["indexes"]["by_type"].get("test", [])
        file_name = os.path.basename(file_path).replace(".py", "")
        for test_file in test_files:
            test_name = os.path.basename(test_file)
            if (
                file_name in test_name
                or test_name.startswith(f"test_{file_name}")
                or test_name.endswith(f"{file_name}_test.py")
            ):
                analysis["related_files"]["test_files"].append(test_file)

        return analysis

    def get_metadata(self) -> dict[str, Any]:
        """Get metadata about the loaded dependencies."""
        if not self.loaded:
            return {}

        return self.data.get("metadata", {})

    def is_loaded(self) -> bool:
        """Check if dependencies are loaded."""
        return self.loaded
