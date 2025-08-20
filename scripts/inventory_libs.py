#!/usr/bin/env python3
"""
Comprehensive inventory of opsvi libraries
Assesses state, dependencies, and relevance
"""

import ast
import json
import os
import subprocess
from pathlib import Path


def get_library_info(lib_path):
    """Get comprehensive info about a library"""
    lib_name = lib_path.name
    module_name = lib_name.replace("-", "_")

    info = {
        "name": lib_name,
        "path": str(lib_path),
        "has_setup": (lib_path / "setup.py").exists(),
        "has_init": (lib_path / module_name / "__init__.py").exists(),
        "py_files": len(list(lib_path.rglob("*.py"))),
        "test_files": len(list(lib_path.rglob("test_*.py"))),
        "dependencies": [],
        "imports_claude_code": False,
        "imports_llm": False,
        "imports_mcp": False,
        "has_readme": (lib_path / "README.md").exists(),
        "has_claude_md": (lib_path / "CLAUDE.md").exists(),
        "likely_deprecated": False,
        "purpose": None,
        "state": "unknown",
    }

    # Check setup.py for dependencies
    setup_file = lib_path / "setup.py"
    if setup_file.exists():
        try:
            content = setup_file.read_text()
            if "install_requires" in content:
                # Simple extraction (not perfect but good enough)
                start = content.find("install_requires")
                if start != -1:
                    bracket_start = content.find("[", start)
                    bracket_end = content.find("]", bracket_start)
                    if bracket_start != -1 and bracket_end != -1:
                        deps_str = content[bracket_start : bracket_end + 1]
                        try:
                            deps = ast.literal_eval(deps_str)
                            info["dependencies"] = deps
                        except:
                            pass
        except:
            pass

    # Check for imports in Python files
    for py_file in lib_path.rglob("*.py"):
        try:
            content = py_file.read_text()
            if "claude_code" in content or "claude-code" in content:
                info["imports_claude_code"] = True
            if "opsvi_llm" in content or "opsvi-llm" in content:
                info["imports_llm"] = True
            if "opsvi_mcp" in content or "opsvi-mcp" in content:
                info["imports_mcp"] = True
        except:
            pass

    # Try to determine purpose from README or docstrings
    readme = lib_path / "README.md"
    if readme.exists():
        try:
            content = readme.read_text()
            lines = content.split("\n")
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    info["purpose"] = line.strip()[:100]
                    break
        except:
            pass

    # Check init file for docstring if no README
    if not info["purpose"]:
        init_file = lib_path / module_name / "__init__.py"
        if init_file.exists():
            try:
                content = init_file.read_text()
                if '"""' in content:
                    start = content.find('"""')
                    end = content.find('"""', start + 3)
                    if start != -1 and end != -1:
                        docstring = content[start + 3 : end].strip()
                        if docstring:
                            info["purpose"] = docstring.split("\n")[0][:100]
            except:
                pass

    # Assess state
    if info["has_setup"] and info["has_init"]:
        if info["test_files"] > 0:
            info["state"] = "complete"
        elif info["py_files"] > 5:
            info["state"] = "functional"
        else:
            info["state"] = "minimal"
    elif info["has_init"]:
        info["state"] = "partial"
    else:
        info["state"] = "stub"

    # Check if likely deprecated based on patterns
    deprecated_patterns = ["agent", "kb", "memory", "redis", "postgres", "celery"]
    for pattern in deprecated_patterns:
        if pattern in lib_name.lower() and not lib_name == "opsvi-agents":
            info["likely_deprecated"] = True
            break

    return info


def categorize_libraries(libraries):
    """Categorize libraries by their role and relevance"""
    categories = {
        "core_infrastructure": [],
        "llm_and_mcp": [],
        "likely_deprecated": [],
        "utilities": [],
        "incomplete_stubs": [],
        "unknown": [],
    }

    for lib in libraries:
        name = lib["name"]

        # Core infrastructure (always needed)
        if name in [
            "opsvi-core",
            "opsvi-data",
            "opsvi-fs",
            "opsvi-auth",
            "opsvi-api",
            "opsvi-config",
            "opsvi-logging",
        ]:
            categories["core_infrastructure"].append(lib)
        # LLM and MCP related (standardized interfaces)
        elif name in ["opsvi-llm", "opsvi-mcp", "opsvi-interfaces"]:
            categories["llm_and_mcp"].append(lib)
        # Likely deprecated (replaced by claude-code or opsvi-llm)
        elif lib["likely_deprecated"] or name in [
            "opsvi-agents",
            "opsvi-kb",
            "opsvi-memory",
            "opsvi-auto-forge",
        ]:
            categories["likely_deprecated"].append(lib)
        # Incomplete stubs
        elif lib["state"] in ["stub", "partial"] and lib["py_files"] < 5:
            categories["incomplete_stubs"].append(lib)
        # Utilities
        elif name in [
            "opsvi-visualization",
            "opsvi-docs",
            "opsvi-tools",
            "opsvi-testing",
            "opsvi-monitoring",
        ]:
            categories["utilities"].append(lib)
        else:
            categories["unknown"].append(lib)

    return categories


def main():
    libs_dir = Path("/home/opsvi/master_root/libs")

    # Get all opsvi libraries
    opsvi_libs = sorted(
        [d for d in libs_dir.iterdir() if d.is_dir() and d.name.startswith("opsvi-")]
    )

    print(f"Found {len(opsvi_libs)} opsvi libraries\n")

    # Gather info on each library
    all_libs = []
    for lib_path in opsvi_libs:
        info = get_library_info(lib_path)
        all_libs.append(info)

    # Categorize libraries
    categories = categorize_libraries(all_libs)

    # Print summary
    print("=" * 80)
    print("LIBRARY INVENTORY SUMMARY")
    print("=" * 80)

    print("\n📦 CORE INFRASTRUCTURE (Keep - Essential)")
    print("-" * 40)
    for lib in categories["core_infrastructure"]:
        status = "✓" if lib["state"] in ["complete", "functional"] else "⚠"
        print(
            f"{status} {lib['name']:25} State: {lib['state']:10} Files: {lib['py_files']:3}"
        )
        if lib["purpose"]:
            print(f"  └─ {lib['purpose']}")

    print("\n🤖 LLM & MCP INTERFACES (Keep - Standardized)")
    print("-" * 40)
    for lib in categories["llm_and_mcp"]:
        status = "✓" if lib["state"] in ["complete", "functional"] else "⚠"
        print(
            f"{status} {lib['name']:25} State: {lib['state']:10} Files: {lib['py_files']:3}"
        )
        if lib["purpose"]:
            print(f"  └─ {lib['purpose']}")

    print("\n🔧 UTILITIES (Keep - Useful)")
    print("-" * 40)
    for lib in categories["utilities"]:
        status = "✓" if lib["state"] in ["complete", "functional"] else "⚠"
        print(
            f"{status} {lib['name']:25} State: {lib['state']:10} Files: {lib['py_files']:3}"
        )
        if lib["purpose"]:
            print(f"  └─ {lib['purpose']}")

    print("\n⚠️ LIKELY DEPRECATED (Migrate/Remove)")
    print("-" * 40)
    for lib in categories["likely_deprecated"]:
        print(f"✗ {lib['name']:25} State: {lib['state']:10} Files: {lib['py_files']:3}")
        if lib["purpose"]:
            print(f"  └─ {lib['purpose']}")
        replacement = ""
        if "agent" in lib["name"].lower():
            replacement = "→ Use: opsvi-mcp (claude-code agent)"
        elif "kb" in lib["name"].lower() or "memory" in lib["name"].lower():
            replacement = "→ Use: Neo4j knowledge base"
        if replacement:
            print(f"  {replacement}")

    print("\n❓ INCOMPLETE STUBS (Remove or Complete)")
    print("-" * 40)
    for lib in categories["incomplete_stubs"]:
        print(f"✗ {lib['name']:25} State: {lib['state']:10} Files: {lib['py_files']:3}")

    print("\n🔍 UNKNOWN/UNCATEGORIZED (Review)")
    print("-" * 40)
    for lib in categories["unknown"]:
        status = "?"
        print(
            f"{status} {lib['name']:25} State: {lib['state']:10} Files: {lib['py_files']:3}"
        )
        if lib["purpose"]:
            print(f"  └─ {lib['purpose']}")

    # Statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    total_files = sum(lib["py_files"] for lib in all_libs)
    total_tests = sum(lib["test_files"] for lib in all_libs)
    with_setup = sum(1 for lib in all_libs if lib["has_setup"])
    complete = sum(1 for lib in all_libs if lib["state"] == "complete")

    print(f"Total Libraries: {len(all_libs)}")
    print(f"Total Python Files: {total_files}")
    print(f"Total Test Files: {total_tests}")
    print(f"Libraries with setup.py: {with_setup}/{len(all_libs)}")
    print(f"Complete Libraries: {complete}/{len(all_libs)}")

    # Save detailed report
    report_path = libs_dir.parent / "docs" / "LIBRARY_INVENTORY.json"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(
            {
                "total_libraries": len(all_libs),
                "categories": {
                    k: [lib["name"] for lib in v] for k, v in categories.items()
                },
                "detailed": all_libs,
            },
            f,
            indent=2,
        )

    print(f"\n📄 Detailed report saved to: {report_path}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("\n1. IMMEDIATE ACTIONS:")
    print("   - Complete setup.py for core libraries missing it")
    print("   - Remove incomplete stub libraries with <5 files")
    print("   - Migrate agent-based libraries to opsvi-mcp")

    print("\n2. CONSOLIDATION TARGETS:")
    duplicates = [
        ("opsvi-comm", "opsvi-communication"),
        ("opsvi-coord", "opsvi-coordination"),
    ]
    for dup in duplicates:
        if all(any(lib["name"] == d for lib in all_libs) for d in dup):
            print(f"   - Merge {dup[0]} and {dup[1]}")

    print("\n3. STANDARDIZATION:")
    print("   - All apps should use opsvi-llm for LLM interfaces")
    print("   - All apps should use opsvi-mcp for claude-code agent")
    print("   - Replace custom memory/KB with Neo4j integration")

    return categories, all_libs


if __name__ == "__main__":
    main()
