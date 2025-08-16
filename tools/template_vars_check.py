#!/usr/bin/env python3
"""
template_vars_check.py — Validate that variables used in templates exist in the
declared variable schema (libs/variable_schema.yaml).

Checks:
- Collects Jinja-style variables from templates under file_templates.* in
  libs/templates.yaml (e.g., {{var}}) and simple {% if var %} usages.
- Loads libs/variable_schema.yaml and verifies each variable is declared.

Exit codes:
 0 = OK
 2 = Missing variables
 3 = YAML load error or unexpected failure
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
IF_PATTERN = re.compile(r"\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%\}")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {}
    return data


def collect_template_strings(d: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(d, dict):
        for k, v in d.items():
            if k == "template" and isinstance(v, str):
                strings.append(v)
            else:
                strings.extend(collect_template_strings(v))
    elif isinstance(d, list):
        for item in d:
            strings.extend(collect_template_strings(item))
    return strings


def collect_used_variables(templates_yaml: dict[str, Any]) -> set[str]:
    used: set[str] = set()
    file_templates = templates_yaml.get("file_templates", {})
    for section in ("python_files", "config_files", "documentation_files"):
        strings = collect_template_strings(file_templates.get(section, {}))
        for s in strings:
            used.update(VAR_PATTERN.findall(s))
            used.update(IF_PATTERN.findall(s))
    return used


def collect_declared_variables(schema_yaml: dict[str, Any]) -> set[str]:
    declared: set[str] = set()
    # Expect mapping: variables: { name: { ... }, ... }
    variables = schema_yaml.get("variables")
    if isinstance(variables, dict):
        declared.update(variables.keys())
    # Also include a common baseline often supplied at runtime by the generator
    declared.update(
        {
            "library_name",
            "package_name",
            "library_description",
            "version",
            "author",
            "email",
            "env_prefix",
            "library_class_name",
            "main_class_name",
            "config_class_name",
            "exception_class_name",
            "component_name",
            "component_description",
            "detailed_description",
            "class_description",
            "detailed_class_description",
            "component_config_fields",
            "component_init_fields",
            "component_init_logic",
            "component_shutdown_logic",
            "component_health_check_logic",
            "component_methods",
            "library_specific_settings",
            "additional_validators",
            "library_specific_exceptions",
            "utils_description",
            "library_specific_utilities",
            "tests_description",
            "component_specific_tests",
            "library_dependencies",
            "homepage_url",
            "repository_url",
            "documentation_url",
            "bug_tracker_url",
            "library_features",
            "usage_example",
            "library_env_vars",
            "library_config_example",
            "api_methods",
            "config_fields",
            "contributing_guidelines",
            "license_info",
            "changelog",
            # Export lists
            "core_exports",
            "config_exports",
            "exception_exports",
            "core_exports_list",
            "config_exports_list",
            "exception_exports_list",
            "service_exports",
            "service_exports_list",
            "schema_exports",
            "schema_exports_list",
            "rag_exports",
            "rag_exports_list",
            "embedding_exports",
            "embedding_exports_list",
            "processor_exports",
            "processor_exports_list",
            "manager_exports",
            "manager_exports_list",
            # Flags used in templates
            "has_service_exports",
            "has_rag_exports",
            "has_manager_exports",
        }
    )
    return declared


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    templates_path = repo / "libs" / "templates.yaml"
    schema_path = repo / "libs" / "variable_schema.yaml"

    try:
        templates_yaml = load_yaml(templates_path)
        schema_yaml = load_yaml(schema_path)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: YAML load failed — {e}")
        return 3

    used = collect_used_variables(templates_yaml)
    declared = collect_declared_variables(schema_yaml)

    missing = sorted([v for v in used if v not in declared])
    if missing:
        print("ERROR: Undeclared variables used in templates:")
        for v in missing:
            print(f"  - {v}")
        print(
            "\nHint: Add entries under 'variables:' in libs/variable_schema.yaml or adjust templates."
        )
        return 2

    print(
        "OK: All template variables are declared in variable_schema.yaml or generator baseline."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
