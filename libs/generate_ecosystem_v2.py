#!/usr/bin/env python3
"""
OPSVI Library Ecosystem Generator v2
Improved version with proper Jinja2 template processing and variable resolution
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from jinja2 import Template, Environment, BaseLoader


class OpsviEcosystemGeneratorV2:
    def __init__(self, libs_dir: str = "."):
        self.libs_dir = Path(libs_dir)
        self.structure_file = self.libs_dir / "recommended_structure.yaml"
        self.templates_file = self.libs_dir / "templates.yaml"

        # Load configuration
        self.structure = self._load_yaml(self.structure_file)
        self.templates = self._load_yaml(self.templates_file)

        # Extract libraries and naming conventions
        self.libraries = self.structure.get("libraries", {})
        self.naming_conventions = self.structure.get("naming_conventions", {})
        self.library_types = self.structure.get("library_types", {})

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        print(f"Loaded {len(self.libraries)} libraries from structure definition")

    def _load_yaml(self, file_path: Path) -> Dict:
        """Load YAML file with error handling"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}

    def _normalize_template_key(self, template_path: str) -> Optional[str]:
        """Normalize legacy template names like 'core_services.py.j2' -> 'core_services_py'."""
        if not template_path:
            return None
        # Extract the trailing file part
        base = template_path.split("/")[-1]
        # Handle common legacy forms
        if base.endswith(".py.j2"):
            base = base[:-5]  # remove '.py.j2'
            return f"{base}_py"
        if base.endswith(".j2"):
            base = base[:-3]  # remove '.j2'
            mapping = {
                "init.py": "init_py",
                "core_init.py": "core_init_py",
                "config_init.py": "config_init_py",
                "exceptions_init.py": "exceptions_init_py",
                "pyproject.toml": "pyproject_toml",
                "readme.md": "README_md",
            }
            return mapping.get(base, base.replace(".", "_"))
        return None

    def _get_template(self, template_path: str) -> Optional[str]:
        """Get template content from nested path"""
        # Try direct nested lookup
        try:
            keys = template_path.split(".")
            template = self.templates
            for key in keys:
                template = template[key]

            if isinstance(template, dict):
                return template.get("template", "")
            if isinstance(template, str):
                return template
        except (KeyError, TypeError):
            pass

        # Try normalized legacy key
        candidates: List[str] = []
        normalized = self._normalize_template_key(template_path)
        if normalized:
            candidates.extend(
                [
                    f"file_templates.python_files.{normalized}",
                    f"file_templates.config_files.{normalized}",
                    f"file_templates.documentation_files.{normalized}",
                ]
            )
        # Try raw path in known namespaces
        candidates.extend(
            [
                f"file_templates.python_files.{template_path}",
                f"file_templates.config_files.{template_path}",
                f"file_templates.documentation_files.{template_path}",
            ]
        )

        for alt_path in candidates:
            try:
                keys = alt_path.split(".")
                template = self.templates
                for key in keys:
                    template = template[key]
                if isinstance(template, dict):
                    return template.get("template", "")
                if isinstance(template, str):
                    return template
            except (KeyError, TypeError):
                continue

        print(f"Template not found: {template_path}")
        return None

    def _get_library_variables(
        self, library_name: str, library_data: Dict
    ) -> Dict[str, Any]:
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

    def _process_template(
        self, template_content: str, variables: Dict[str, Any]
    ) -> str:
        """Process template with Jinja2 and variable substitution"""
        try:
            # Create Jinja2 template
            template = self.jinja_env.from_string(template_content)

            # Render template with variables
            result = template.render(**variables)

            return result
        except Exception as e:
            print(f"Error processing template: {e}")
            # Fallback to simple string replacement
            result = template_content
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                result = result.replace(placeholder, str(value))
            return result

    def _create_directory_structure(self, library_name: str, library_data: Dict):
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
                init_file.write_text(
                    '"""{} module."""\n\n'.format(subdir.replace("/", "."))
                )

        # Create tests directory
        tests_dir = library_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        print(f"Created directory structure for {library_name}")

    def _generate_file(
        self, file_path: Path, template_path: str, variables: Dict[str, Any]
    ):
        """Generate a file from template"""
        template_content = self._get_template(template_path)
        if not template_content:
            print(f"Warning: Template not found for {template_path}")
            return

        # Process template with variables
        content = self._process_template(template_content, variables)

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Generated {file_path}")

    def _generate_standard_files(self, library_name: str, library_data: Dict):
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
        tests_init_path.write_text('"""Tests for {}."""\n\n'.format(library_name))

        test_file_path = tests_dir / f"test_{package_name}.py"
        self._generate_file(test_file_path, "test_base_py", variables)

    def _generate_library_files(self, library_name: str, library_data: Dict):
        """Generate library-specific files"""
        library_dir = self.libs_dir / library_name
        variables = self._get_library_variables(library_name, library_data)

        # Get files to generate
        files = library_data.get("files", [])

        for file_info in files:
            file_path_str = file_info.get("path", "")
            template_ref = file_info.get("template", "")

            # Process file path with variables
            file_path_str = self._process_template(file_path_str, variables)
            file_path = library_dir / file_path_str

            # Handle template references
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
                    template_path = "init_py"  # Default fallback
            elif isinstance(template_ref, dict):
                # YAML anchor resolved as dict - extract template field
                template_path = template_ref.get("template", "init_py")
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
                        template_path = "init_py"  # Default fallback
            elif isinstance(template_ref, str):
                template_path = template_ref
            else:
                print(
                    f"Warning: Unexpected template reference type for {file_path}: {type(template_ref)}"
                )
                continue

            self._generate_file(file_path, template_path, variables)

    def generate_ecosystem(self):
        """Generate the complete library ecosystem"""
        print("Generating OPSVI Library Ecosystem v2...")
        print("=" * 50)

        for library_name, library_data in self.libraries.items():
            print(f"\nProcessing {library_name}...")

            # Create directory structure
            self._create_directory_structure(library_name, library_data)

            # Generate standard files
            self._generate_standard_files(library_name, library_data)

            # Generate library-specific files
            self._generate_library_files(library_name, library_data)

        print("\n" + "=" * 50)
        print("Ecosystem generation complete!")
        print(f"Generated {len(self.libraries)} libraries")

    def validate_generation(self):
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
    generator = OpsviEcosystemGeneratorV2()
    generator.generate_ecosystem()
    generator.validate_generation()


if __name__ == "__main__":
    main()
