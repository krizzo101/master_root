#!/usr/bin/env python3
"""
Automated analysis of all custom projects in intake/custom/
"""
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


def run_project_intelligence(project_path: str) -> dict[str, Any]:
    """Run project intelligence analysis on a single project."""
    project_name = os.path.basename(project_path)
    print(f"🔍 Starting analysis of {project_name}...")

    start_time = time.time()
    try:
        result = subprocess.run(
            [
                "project-intelligence",
                "full-package",
                "--project-path",
                project_path,
                "--enhanced",
                "--pretty-json",
            ],
            capture_output=True,
            text=True,
            cwd="/home/opsvi/master_root",
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {project_name} completed in {duration:.2f}s")
            return {
                "project": project_name,
                "path": project_path,
                "status": "success",
                "duration": duration,
                "stdout": result.stdout,
            }
        else:
            print(f"❌ {project_name} failed in {duration:.2f}s")
            return {
                "project": project_name,
                "path": project_path,
                "status": "error",
                "duration": duration,
                "stderr": result.stderr,
            }
    except Exception as e:  # noqa: BLE001
        duration = time.time() - start_time
        print(f"💥 {project_name} crashed in {duration:.2f}s: {e}")
        return {
            "project": project_name,
            "path": project_path,
            "status": "crashed",
            "duration": duration,
            "error": str(e),
        }


def analyze_project_data(project_path: str) -> dict[str, Any] | None:
    """Read and analyze the project intelligence data."""
    intel_path = Path(project_path) / ".proj-intel" / "project_analysis.pretty.json"

    if not intel_path.exists():
        return None

    try:
        with open(intel_path, encoding="utf-8") as f:
            data = json.load(f)

        # Extract key information
        purpose = data.get("project_purpose", {}).get("summary", "Unknown purpose")

        # Get file count and structure
        file_elements = data.get("file_elements", {})
        total_files = file_elements.get("total_files", 0)

        # Get dependencies
        dependencies = data.get("dependencies", {})

        # Get architecture info
        agent_arch = data.get("agent_architecture", {})

        return {
            "name": os.path.basename(project_path),
            "purpose": purpose,
            "total_files": total_files,
            "dependencies": dependencies,
            "architecture": agent_arch,
            "file_elements": file_elements,
        }
    except Exception as e:  # noqa: BLE001
        print(f"Error reading data for {project_path}: {e}")
        return None


def main() -> None:
    custom_dir = Path("/home/opsvi/master_root/intake/custom")

    # Find all project directories (excluding .proj-intel)
    projects: list[str] = [
        str(p) for p in custom_dir.iterdir() if p.is_dir() and p.name != ".proj-intel"
    ]

    print(f"📊 Found {len(projects)} projects to analyze:")
    for project in projects:
        print(f"  - {os.path.basename(project)}")

    # Run analysis in parallel
    workers = min(4, len(projects)) or 1
    print(f"\n🚀 Starting parallel analysis with {workers} workers...")

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all jobs
        future_to_project = {
            executor.submit(run_project_intelligence, project): project
            for project in projects
        }

        # Collect results as they complete
        for future in as_completed(future_to_project):
            result = future.result()
            results.append(result)

    # Summary
    successful = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]

    print("\n📈 Analysis Summary:")
    print(f"  ✅ Successful: {len(successful)}")
    print(f"  ❌ Failed: {len(failed)}")

    if failed:
        print("\n❌ Failed projects:")
        for result in failed:
            print(f"  - {result.get('project')}: {result.get('status')}")

    # Analyze the data
    print("\n🔍 Reading project intelligence data...")
    project_data: list[dict[str, Any]] = []
    for project in projects:
        data = analyze_project_data(project)
        if data:
            project_data.append(data)

    # Save summary
    summary_file = custom_dir / "project_analysis_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_results": results,
                "project_data": project_data,
                "timestamp": time.time(),
            },
            f,
            indent=2,
        )

    print(f"💾 Summary saved to: {summary_file}")

    # Print quick overview
    print("\n📋 Project Overview:")
    for data in project_data:
        purpose = data.get("purpose", "")
        preview = (purpose[:77] + "...") if len(purpose) > 80 else purpose
        print(f"  {data.get('name')}: {data.get('total_files')} files - {preview}")


if __name__ == "__main__":
    main()
