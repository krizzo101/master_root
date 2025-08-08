#!/usr/bin/env python3
"""
OPSVI Library Ecosystem Generator v2
Registry-based template processing using YAML-defined templates only.

This generator consumes:
- recommended_structure.yaml (structure, libraries, categories, anchors)
- templates.yaml (single source of truth for templates)
- file_manifest.yaml (optional, additional files per type/library)

Backwards compatibility with .j2 paths has been removed.
All template references must be registry keys or nested registry paths.
"""

import argparse
from pathlib import Path
from typing import Any, cast

import yaml
from jinja2 import BaseLoader, Environment


class OpsviEcosystemGeneratorV2:
    def __init__(
        self,
        libs_dir: str = ".",
        file_manifest: str | None = None,
        touch_missing: bool = True,
        strict: bool = True,
        only: list[str] | None = None,
        only_type: list[str] | None = None,
        update_existing: bool = True,
        dry_run: bool = False,
        diff_only: bool = False,
    ):
        self.libs_dir = Path(libs_dir)
        self.structure_file = self.libs_dir / "recommended_structure.yaml"
        self.templates_file = self.libs_dir / "templates.yaml"
        self.file_manifest_file = (
            Path(file_manifest)
            if file_manifest
            else self.libs_dir / "file_manifest.yaml"
        )

        # Load configuration
        self.structure = self._load_yaml(self.structure_file)
        self.templates = self._load_yaml(self.templates_file)
        self.file_manifest = (
            self._load_yaml(self.file_manifest_file)
            if self.file_manifest_file.exists()
            else {}
        )
        self.touch_missing = touch_missing
        self.strict = strict
        self.only = set(only or [])
        self.only_type = set(only_type or [])
        self.update_existing = update_existing
        self.dry_run = dry_run
        self.diff_only = diff_only

        # Extract libraries and naming conventions
        self.libraries = self.structure.get("libraries", {})
        self.naming_conventions = self.structure.get("naming_conventions", {})
        self.library_types = self.structure.get("library_types", {})

        # Initialize template environment (Jinja2 rendering over YAML registry)
        self.jinja_env = Environment(
            loader=BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        print(f"Loaded {len(self.libraries)} libraries from structure definition")

    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """Load YAML file with error handling"""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    return {}
                # Cast is safe after isinstance check
                return cast(dict[str, Any], data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}

    def _get_template(self, template_path: str) -> str | None:
        """Get template content from registry.

        Accepts nested paths (e.g., 'file_templates.python_files.init_py')
        or short keys (e.g., 'init_py').
        """
        # Try direct nested lookup
        try:
            keys = template_path.split(".")
            template = self.templates
            for key in keys:
                template = template[key]
            if isinstance(template, dict):
                value = template.get("template")
                return value if isinstance(value, str) else None
            elif isinstance(template, str):
                return template
        except (KeyError, TypeError):
            pass

        # Try short key in known namespaces
        candidates: list[str] = [
            f"file_templates.python_files.{template_path}",
            f"file_templates.config_files.{template_path}",
            f"file_templates.documentation_files.{template_path}",
        ]

        for alt_path in candidates:
            try:
                keys = alt_path.split(".")
                template = self.templates
                for key in keys:
                    template = template[key]
                if isinstance(template, dict):
                    value = template.get("template")
                    return value if isinstance(value, str) else None
                elif isinstance(template, str):
                    return template
            except (KeyError, TypeError):
                continue

        print(f"Template not found: {template_path}")
        return None

    def _validate_template_refs(self) -> None:
        """Validate that all template references in structure and manifest exist in the registry.

        Raises ValueError if any reference is missing and strict mode is enabled.
        """
        missing: list[str] = []

        def check_ref(ref: Any) -> None:
            if isinstance(ref, str):
                # Anchors handled later; only validate registry keys and nested paths
                if ref.startswith("*"):
                    return
                if self._get_template(ref) is None:
                    missing.append(ref)
            elif isinstance(ref, dict):
                t = ref.get("template") if "template" in ref else None
                if (
                    t
                    and not str(t).startswith("*")
                    and self._get_template(str(t)) is None
                ):
                    missing.append(str(t))

        # From libraries in structure
        for _, data in (self.libraries or {}).items():
            for file_info in data.get("files") or []:
                check_ref(file_info.get("template"))

        # From manifest by type and library
        lt = (
            (self.file_manifest.get("library_types") or {})
            if self.file_manifest
            else {}
        )
        for _, entry in (lt or {}).items():
            for fi in entry.get("files") or []:
                check_ref(fi.get("template"))
        libs = (self.file_manifest.get("libraries") or {}) if self.file_manifest else {}
        for _, entry in (libs or {}).items():
            for fi in entry.get("files") or []:
                check_ref(fi.get("template"))

        if missing:
            msg = f"Missing templates in registry: {sorted(set(missing))}"
            if self.strict:
                raise ValueError(msg)
            print(f"WARNING: {msg}")

    def _get_library_variables(
        self, library_name: str, library_data: dict
    ) -> dict[str, Any]:
        """Generate comprehensive variables for a library"""
        # Convert kebab-case to snake_case for package name
        package_name = library_name.replace("-", "_")

        # Generate class names
        library_class_name = "".join(
            word.capitalize() for word in library_name.split("-")
        )
        main_class_name = f"{library_class_name}Manager"
        config_class_name = f"{library_class_name}Config"
        exception_class_name = f"{library_class_name}Error"

        # Generate export lists aligned with templates
        core_exports = f"{main_class_name}"
        config_exports = f"{library_class_name}Settings, get_settings"
        exception_exports = (
            f"{library_class_name}Error, {library_class_name}ConfigurationError"
        )

        # Library-specific exports based on type
        library_type = library_data.get("type", "service")
        service_exports = ""
        rag_exports = ""
        manager_exports = ""

        if library_type == "service":
            service_exports = f"{library_class_name}Provider"
        elif library_type == "rag":
            rag_exports = f"{library_class_name}Provider"
        elif library_type == "manager":
            manager_exports = f"{library_class_name}Coordinator"

        return {
            # Basic info
            "library_name": library_name,
            "package_name": package_name,
            "library_description": library_data.get("description", ""),
            "library_type": library_type,
            "version": "0.1.0",
            "author": "OPSVI Team",
            "email": "team@opsvi.com",
            # Class names
            "library_class_name": library_class_name,
            "main_class_name": main_class_name,
            "config_class_name": config_class_name,
            "exception_class_name": exception_class_name,
            # Convenience for templates expecting these
            "class_name": main_class_name,
            "component_name": library_name,
            # Environment and config
            "env_prefix": f"OPSVI_{package_name.upper()}_",
            "homepage_url": f"https://github.com/opsvi/{library_name}",
            "repository_url": f"https://github.com/opsvi/{library_name}",
            "documentation_url": f"https://docs.opsvi.com/{library_name}",
            "bug_tracker_url": f"https://github.com/opsvi/{library_name}/issues",
            # Exports
            "core_exports": core_exports,
            "config_exports": config_exports,
            "exception_exports": exception_exports,
            "service_exports": service_exports,
            "rag_exports": rag_exports,
            "manager_exports": manager_exports,
            # Export lists for __all__
            "core_exports_list": core_exports,
            "config_exports_list": config_exports,
            "exception_exports_list": exception_exports,
            "service_exports_list": service_exports,
            "rag_exports_list": rag_exports,
            "manager_exports_list": manager_exports,
            # Optional exports used by some templates
            "schema_exports": "",
            "schema_exports_list": "",
            "embedding_exports": "",
            "embedding_exports_list": "",
            "processor_exports": "",
            "processor_exports_list": "",
            "scheduler_exports": "",
            "scheduler_exports_list": "",
            # Dependencies
            "library_dependencies": "opsvi-foundation>=0.1.0",
            # Descriptions
            "detailed_description": f"Comprehensive {library_name} library for the OPSVI ecosystem",
            "component_description": f"Core {library_name} functionality",
            "class_description": f"Base class for {library_name} components",
            "detailed_class_description": f"Provides base functionality for all {library_name} components",
            "utils_description": f"Utility functions for {library_name}",
            "tests_description": f"Tests for {library_name} components",
            # Features and examples
            "library_features": f"Core {library_name} functionality, configuration management, error handling",
            "usage_example": f"from {package_name} import {main_class_name}",
            "library_env_vars": f"OPSVI_{package_name.upper()}_ENABLED=true",
            "library_config_example": f"{config_class_name}(enabled=True)",
            # Documentation
            "contributing_guidelines": "Please read CONTRIBUTING.md for development guidelines",
            "license_info": "MIT License - see LICENSE file for details",
            "changelog": "See CHANGELOG.md for version history",
            # Conditional flags (separate from export strings)
            "has_service_exports": bool(service_exports),
            "has_rag_exports": bool(rag_exports),
            "has_manager_exports": bool(manager_exports),
        }

    def _get_manifest_files(
        self, library_name: str, library_data: dict
    ) -> list[dict[str, Any]]:
        """Return additional files from file_manifest for the given library.

        Structure:
        library_types:
          core:
            files: [{ path: "{{package_name}}/utils/helpers.py", template: "utils_helpers_py" }]
          service:
            files: [...]
        libraries:
          opsvi-llm:
            files: [...]
        """
        manifest = self.file_manifest or {}
        lib_type = library_data.get("type", "service")

        results: list[dict[str, Any]] = []
        type_entry = (manifest.get("library_types", {}) or {}).get(lib_type, {}) or {}
        results.extend(type_entry.get("files", []) or [])

        lib_entry = (manifest.get("libraries", {}) or {}).get(library_name, {}) or {}
        results.extend(lib_entry.get("files", []) or [])

        return results

    def _process_template(
        self, template_content: str, variables: dict[str, Any]
    ) -> str:
        """Render template content strictly via the registry renderer (Jinja2).

        No legacy fallbacks. Fail fast on errors.
        """
        template = self.jinja_env.from_string(template_content)
        return template.render(**variables)

    def _create_directory_structure(
        self, library_name: str, library_data: dict
    ) -> None:
        """Create directory structure for a library"""
        library_dir = self.libs_dir / library_name
        package_name = library_name.replace("-", "_")
        package_dir = library_dir / package_name

        # Create directories
        library_dir.mkdir(exist_ok=True)
        package_dir.mkdir(exist_ok=True)

        # Create subdirectories based on library type
        library_type = library_data.get("type", "service")
        type_config = self.library_types.get(library_type, {})
        directory_structure = type_config.get("directory_structure", [])

        for subdir in directory_structure:
            # Strip '{{package_name}}/' prefix and trailing slashes
            sub = subdir.replace("{{package_name}}/", "").strip("/")
            if not sub:
                continue
            subdir_path = package_dir / sub
            subdir_path.mkdir(exist_ok=True)
            # Create __init__.py for each subdirectory
            init_file = subdir_path / "__init__.py"
            if not init_file.exists():
                module_name = subdir.replace("/", ".")
                init_file.write_text(f'"""{module_name} module."""\n\n')

        # Create tests directory
        tests_dir = library_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        print(f"Created directory structure for {library_name}")

    def _generate_file(
        self, file_path: Path, template_path: str, variables: dict[str, Any]
    ) -> None:
        """Generate a file from template"""
        template_content = self._get_template(template_path)
        if not template_content:
            print(f"Warning: Template not found for {template_path}")
            if self.touch_missing:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                header = (
                    '"""AUTO-GENERATED STUB\n'
                    f"Path: {file_path.name}\n"
                    f"Template missing: {template_path}\n"
                    "This file is intended to be populated by the agentic coder.\n"
                    '"""\n\n'
                )
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(header)
                print(f"Touched {file_path} (missing template)")
            return

        # Process template with variables
        content = self._process_template(template_content, variables)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Dry-run or diff-only behavior
        if self.dry_run or self.diff_only:
            status = "NEW"
            if file_path.exists():
                old = file_path.read_text(encoding="utf-8")
                status = "UNCHANGED" if old == content else "CHANGED"
            print(f"PLAN {status}: {file_path} <- {template_path}")
            return

        # Respect update_existing flag
        if file_path.exists() and not self.update_existing:
            print(f"SKIP (exists): {file_path}")
            return

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Generated {file_path}")

    def _generate_standard_files(self, library_name: str, library_data: dict) -> None:
        """Generate standard files that every library should have"""
        library_dir = self.libs_dir / library_name
        package_name = library_name.replace("-", "_")
        variables = self._get_library_variables(library_name, library_data)

        # Generate pyproject.toml
        pyproject_path = library_dir / "pyproject.toml"
        self._generate_file(pyproject_path, "pyproject_toml", variables)

        # Generate README.md
        readme_path = library_dir / "README.md"
        self._generate_file(readme_path, "README_md", variables)

        # Generate package __init__.py
        package_init_path = library_dir / package_name / "__init__.py"
        self._generate_file(package_init_path, "init_py", variables)

        # Generate core files
        core_dir = library_dir / package_name / "core"
        core_dir.mkdir(exist_ok=True)

        core_init_path = core_dir / "__init__.py"
        self._generate_file(core_init_path, "core_init_py", variables)

        core_base_path = core_dir / "base.py"
        self._generate_file(core_base_path, "core_base_py", variables)

        # Generate config files
        config_dir = library_dir / package_name / "config"
        config_dir.mkdir(exist_ok=True)

        config_init_path = config_dir / "__init__.py"
        self._generate_file(config_init_path, "config_init_py", variables)

        config_settings_path = config_dir / "settings.py"
        self._generate_file(config_settings_path, "config_settings_py", variables)

        # Generate exceptions
        exceptions_dir = library_dir / package_name / "exceptions"
        exceptions_dir.mkdir(exist_ok=True)

        exceptions_init_path = exceptions_dir / "__init__.py"
        self._generate_file(exceptions_init_path, "exceptions_init_py", variables)

        exceptions_base_path = exceptions_dir / "base.py"
        self._generate_file(exceptions_base_path, "exceptions_base_py", variables)

        # Generate tests
        tests_dir = library_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        tests_init_path = tests_dir / "__init__.py"
        tests_init_path.write_text(f'"""Tests for {library_name}."""\n\n')

        test_file_path = tests_dir / f"test_{package_name}.py"
        self._generate_file(test_file_path, "test_base_py", variables)

    def _generate_library_files(self, library_name: str, library_data: dict) -> None:
        """Generate library-specific files"""
        library_dir = self.libs_dir / library_name
        variables = self._get_library_variables(library_name, library_data)

        # Get files to generate
        files = list(library_data.get("files", []) or [])
        # Extend with manifest-defined files
        files.extend(self._get_manifest_files(library_name, library_data))

        for file_info in files:
            file_path_str = file_info.get("path", "")
            template_ref = file_info.get("template", "")

            # Process file path with variables
            file_path_str = self._process_template(file_path_str, variables)
            file_path = library_dir / file_path_str

            # Handle template references (anchors or registry keys)
            if isinstance(template_ref, str) and template_ref.startswith("*"):
                # YAML anchor reference - extract the anchor name and map to template
                anchor_name = template_ref[1:]  # Remove the *
                if anchor_name == "base_init":
                    template_path = "init_py"
                elif anchor_name == "base_core_init":
                    template_path = "core_init_py"
                elif anchor_name == "base_config_init":
                    template_path = "config_init_py"
                elif anchor_name == "base_exceptions_init":
                    template_path = "exceptions_init_py"
                elif anchor_name == "base_pyproject":
                    template_path = "pyproject_toml"
                elif anchor_name == "base_readme":
                    template_path = "README_md"
                else:
                    raise ValueError(f"Unknown YAML anchor reference: {anchor_name}")
            elif isinstance(template_ref, dict):
                # YAML anchor resolved as dict - extract template field
                template_value = template_ref.get("template")
                if not isinstance(template_value, str):
                    raise ValueError(
                        f"Missing or invalid 'template' in dict for {file_path}"
                    )
                template_path = template_value
                if template_path.startswith("*"):
                    # Handle nested anchor reference
                    anchor_name = template_path[1:]
                    if anchor_name == "base_init":
                        template_path = "init_py"
                    elif anchor_name == "base_core_init":
                        template_path = "core_init_py"
                    elif anchor_name == "base_config_init":
                        template_path = "config_init_py"
                    elif anchor_name == "base_exceptions_init":
                        template_path = "exceptions_init_py"
                    elif anchor_name == "base_pyproject":
                        template_path = "pyproject_toml"
                    elif anchor_name == "base_readme":
                        template_path = "README_md"
                    else:
                        raise ValueError(
                            f"Unknown YAML anchor reference: {anchor_name}"
                        )
            elif isinstance(template_ref, str):
                template_path = template_ref
            else:
                print(
                    f"Warning: Unexpected template reference type for {file_path}: {type(template_ref)}"
                )
                continue

            self._generate_file(file_path, template_path, variables)

    def generate_ecosystem(self) -> None:
        """Generate the complete library ecosystem"""
        print("Generating OPSVI Library Ecosystem v2...")
        print("=" * 50)

        # Validate template references up front
        self._validate_template_refs()

        for library_name, library_data in self.libraries.items():
            if self.only and library_name not in self.only:
                continue
            if self.only_type:
                lib_type = library_data.get("type", "service")
                if lib_type not in self.only_type:
                    continue
            print(f"\nProcessing {library_name}...")

            # Create directory structure
            self._create_directory_structure(library_name, library_data)

            # Generate standard files
            self._generate_standard_files(library_name, library_data)

            # Generate library-specific files
            self._generate_library_files(library_name, library_data)

        print("\n" + "=" * 50)
        print("Ecosystem generation complete!")
        print(f"Processed {len(self.libraries)} libraries (filters may apply)")

    def validate_generation(self) -> None:
        """Validate that all libraries were generated correctly"""
        print("\nValidating generation...")

        for library_name in self.libraries.keys():
            library_dir = self.libs_dir / library_name
            package_name = library_name.replace("-", "_")
            package_dir = library_dir / package_name

            if not library_dir.exists():
                print(f"❌ Missing library directory: {library_name}")
                continue

            if not package_dir.exists():
                print(f"❌ Missing package directory: {package_name}")
                continue

            # Check for required files
            required_files = [
                "pyproject.toml",
                "README.md",
                f"{package_name}/__init__.py",
                f"{package_name}/core/__init__.py",
                f"{package_name}/core/base.py",
                f"{package_name}/config/__init__.py",
                f"{package_name}/config/settings.py",
                f"{package_name}/exceptions/__init__.py",
                f"{package_name}/exceptions/base.py",
                "tests/__init__.py",
                f"tests/test_{package_name}.py",
            ]

            missing_files = []
            for file_path in required_files:
                if not (library_dir / file_path).exists():
                    missing_files.append(file_path)

            if missing_files:
                print(f"❌ {library_name}: Missing files: {missing_files}")
            else:
                print(f"✅ {library_name}: All files present")


def main():
    parser = argparse.ArgumentParser(description="OPSVI Ecosystem Generator v2")
    parser.add_argument(
        "--libs-dir",
        dest="libs_dir",
        default="libs",
        help="Directory containing structure/templates (default: libs)",
    )
    parser.add_argument(
        "--file-manifest",
        dest="file_manifest",
        default=None,
        help="Optional YAML manifest defining extra low-level files to scaffold",
    )
    parser.add_argument(
        "--no-touch-missing",
        dest="touch_missing",
        action="store_false",
        help="Do not create stub files when templates are missing",
    )
    parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Do not fail on missing template references (prints warnings instead)",
    )
    parser.add_argument(
        "--only",
        dest="only",
        nargs="*",
        default=None,
        help="Only process these libraries by name",
    )
    parser.add_argument(
        "--type",
        dest="only_type",
        nargs="*",
        default=None,
        help="Only process libraries of these types (core, service, rag, manager)",
    )
    parser.add_argument(
        "--no-update-existing",
        dest="update_existing",
        action="store_false",
        help="Do not overwrite existing files",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Plan-only: print actions without writing files",
    )
    parser.add_argument(
        "--diff",
        dest="diff_only",
        action="store_true",
        help="Print summary of files that would change",
    )
    args = parser.parse_args()

    generator = OpsviEcosystemGeneratorV2(
        libs_dir=args.libs_dir,
        file_manifest=args.file_manifest,
        touch_missing=args.touch_missing,
        strict=args.strict,
        only=args.only,
        only_type=args.only_type,
        update_existing=args.update_existing,
        dry_run=args.dry_run,
        diff_only=args.diff_only,
    )
    generator.generate_ecosystem()
    generator.validate_generation()


if __name__ == "__main__":
    main()
