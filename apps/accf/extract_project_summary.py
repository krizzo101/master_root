#!/usr/bin/env python3
"""
Extract key project information from knowledge.json for analysis
"""

import json
import sys
from pathlib import Path


def extract_project_summary():
    """Extract and format key project information"""

    knowledge_file = Path("knowledge.json")
    if not knowledge_file.exists():
        print("❌ knowledge.json not found!")
        sys.exit(1)

    try:
        with open(knowledge_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading knowledge.json: {e}")
        sys.exit(1)

    # Extract key information
    summary = {
        "project_overview": {
            "metadata": data.get("metadata", {}),
            "total_files": len(data.get("files", [])),
            "file_types": get_file_types(data.get("files", [])),
        },
        "code_quality": {
            "metrics_summary": summarize_metrics(data.get("metrics", {})),
            "complexity_summary": summarize_complexity(data.get("complexity", {})),
            "lint_issues": len(data.get("lint", {}).get("results", [])),
            "security_issues": len(data.get("security", {}).get("results", [])),
        },
        "dependencies": {
            "main_packages": extract_main_packages(data.get("dependencies", [])),
            "total_dependencies": count_total_dependencies(
                data.get("dependencies", [])
            ),
        },
        "git_info": data.get("git", {}),
        "file_structure": data.get("files", [])[:20],  # First 20 files
    }

    return summary


def get_file_types(files):
    """Extract file type distribution"""
    extensions = {}
    for file in files:
        if "." in file:
            ext = file.split(".")[-1].lower()
            extensions[ext] = extensions.get(ext, 0) + 1
        else:
            extensions["no_extension"] = extensions.get("no_extension", 0) + 1
    return dict(sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:10])


def summarize_metrics(metrics):
    """Summarize code metrics"""
    total_loc = 0
    total_sloc = 0
    total_comments = 0

    for file_data in metrics.values():
        if isinstance(file_data, dict):
            total_loc += file_data.get("loc", 0)
            total_sloc += file_data.get("sloc", 0)
            total_comments += file_data.get("comments", 0)

    return {
        "total_lines": total_loc,
        "source_lines": total_sloc,
        "comments": total_comments,
        "files_analyzed": len(metrics),
    }


def summarize_complexity(complexity):
    """Summarize complexity analysis"""
    total_functions = 0
    complexity_scores = []

    for file_data in complexity.values():
        if isinstance(file_data, list):
            for func in file_data:
                if isinstance(func, dict):
                    total_functions += 1
                    complexity_scores.append(func.get("complexity", 0))

    return {
        "total_functions": total_functions,
        "avg_complexity": (
            sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
        ),
        "max_complexity": max(complexity_scores) if complexity_scores else 0,
        "files_analyzed": len(complexity),
    }


def extract_main_packages(dependencies):
    """Extract main package information"""
    main_packages = []
    for dep in dependencies:
        if isinstance(dep, dict) and "package" in dep:
            pkg_info = dep["package"]
            main_packages.append(
                {
                    "name": pkg_info.get("package_name", "Unknown"),
                    "version": pkg_info.get("installed_version", "Unknown"),
                    "dependencies_count": len(dep.get("dependencies", [])),
                }
            )
    return main_packages[:10]  # Top 10 packages


def count_total_dependencies(dependencies):
    """Count total dependencies"""
    total = 0
    for dep in dependencies:
        if isinstance(dep, dict):
            total += len(dep.get("dependencies", []))
    return total


if __name__ == "__main__":
    summary = extract_project_summary()
    print(json.dumps(summary, indent=2))
