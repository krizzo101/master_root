"""Quality Tools for MCP - Code quality metrics and analysis."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..db.connections import get_db


async def get_tests() -> Dict[str, Any]:
    """Find test files, map to source files, and include test coverage information.

    Description: Test file mapping from code_elements
    Query monitoring_metrics for quality data
    Aggregate from code_elements complexity scores

    Returns:
        Dictionary containing test file mappings, coverage info,
        test type classifications, and quality metrics.
    """

    try:
        db = await get_db()
        project_root = Path.cwd()

        result = {
            "test_files": [],
            "source_mappings": {},
            "test_types": {
                "unit": [],
                "integration": [],
                "functional": [],
                "other": [],
            },
            "coverage_info": {},
            "quality_metrics": {},
            "complexity_analysis": {},
            "stats": {
                "total_test_files": 0,
                "total_source_files_with_tests": 0,
                "test_coverage_estimate": None,
                "avg_test_file_complexity": None,
                "total_test_coverage": None,
            },
        }

        # Query test files from code_elements database
        test_files_db = await db.fetch_many(
            """
            SELECT
                file_path,
                element_name,
                line_start,
                line_end,
                complexity_score,
                test_coverage,
                language,
                last_modified,
                content_hash
            FROM code_elements
            WHERE file_path ~* '(test_.*\\.py|.*_test\\.py|tests/.*\\.py|test/.*\\.py)'
            AND element_type = 'file'
            ORDER BY file_path
        """
        )

        # Get quality metrics from monitoring_metrics for test-related data
        test_quality_metrics = await db.fetch_many(
            """
            SELECT
                metric_name,
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value,
                COUNT(*) as measurement_count
            FROM monitoring_metrics
            WHERE metric_name IN (
                'test_coverage', 'test_execution_time', 'test_success_rate',
                'test_failure_count', 'test_pass_count', 'test_duration'
            )
            AND time >= NOW() - INTERVAL '30 days'
            GROUP BY metric_name
            ORDER BY metric_name
        """
        )

        # Get complexity analysis for test files
        test_complexity_stats = await db.fetch_one(
            """
            SELECT
                AVG(complexity_score) as avg_complexity,
                MIN(complexity_score) as min_complexity,
                MAX(complexity_score) as max_complexity,
                COUNT(*) as test_file_count,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY complexity_score) as median_complexity
            FROM code_elements
            WHERE file_path ~* '(test_.*\\.py|.*_test\\.py|tests/.*\\.py|test/.*\\.py)'
            AND complexity_score IS NOT NULL
        """
        )

        # Get test coverage data from code_elements
        coverage_stats = await db.fetch_one(
            """
            SELECT
                AVG(test_coverage) as avg_coverage,
                MIN(test_coverage) as min_coverage,
                MAX(test_coverage) as max_coverage,
                COUNT(*) FILTER (WHERE test_coverage > 0) as files_with_coverage,
                COUNT(*) as total_files
            FROM code_elements
            WHERE test_coverage IS NOT NULL
        """
        )

        result["stats"]["total_test_files"] = len(test_files_db)

        # Process test files from database
        for test_file_record in test_files_db:
            file_path = test_file_record["file_path"]

            # Try to get file system info for additional details
            fs_test_info = {}
            try:
                path_obj = Path(file_path)
                if path_obj.exists():
                    fs_test_info = {
                        "size": path_obj.stat().st_size,
                        "absolute_path": str(path_obj.absolute()),
                    }
            except Exception:
                pass

            test_info = {
                "path": file_path,
                "absolute_path": fs_test_info.get("absolute_path", file_path),
                "size": fs_test_info.get("size", 0),
                "type": _classify_test_type(Path(file_path)),
                "complexity_score": float(test_file_record["complexity_score"])
                if test_file_record["complexity_score"]
                else None,
                "test_coverage": float(test_file_record["test_coverage"])
                if test_file_record["test_coverage"]
                else None,
                "language": test_file_record["language"],
                "last_modified": str(test_file_record["last_modified"])
                if test_file_record["last_modified"]
                else None,
                "mapped_sources": await _find_db_source_mappings(db, file_path),
            }

            result["test_files"].append(test_info)

            # Add to type classification
            test_type = test_info["type"]
            if test_type in result["test_types"]:
                result["test_types"][test_type].append(file_path)
            else:
                result["test_types"]["other"].append(file_path)

            # Build source mappings
            for source_file in test_info["mapped_sources"]:
                if source_file not in result["source_mappings"]:
                    result["source_mappings"][source_file] = []
                result["source_mappings"][source_file].append(file_path)

        # If database is empty, fallback to filesystem scan
        if not test_files_db:
            try:
                fallback_result = await _fallback_filesystem_test_scan(project_root)
                result["test_files"] = fallback_result["test_files"]
                result["test_types"] = fallback_result["test_types"]
                result["source_mappings"] = fallback_result["source_mappings"]
            except Exception as e:
                print(f"Fallback filesystem scan failed: {e}")
                # Continue with empty results

        result["stats"]["total_source_files_with_tests"] = len(
            result["source_mappings"]
        )

        # Populate quality metrics
        result["quality_metrics"] = {
            metric["metric_name"]: {
                "average": float(metric["avg_value"]) if metric["avg_value"] else 0,
                "minimum": float(metric["min_value"]) if metric["min_value"] else 0,
                "maximum": float(metric["max_value"]) if metric["max_value"] else 0,
                "measurements": metric["measurement_count"],
            }
            for metric in test_quality_metrics
        }

        # Populate complexity analysis
        if test_complexity_stats:
            result["complexity_analysis"] = {
                "average_complexity": float(test_complexity_stats["avg_complexity"])
                if test_complexity_stats["avg_complexity"]
                else 0,
                "min_complexity": float(test_complexity_stats["min_complexity"])
                if test_complexity_stats["min_complexity"]
                else 0,
                "max_complexity": float(test_complexity_stats["max_complexity"])
                if test_complexity_stats["max_complexity"]
                else 0,
                "median_complexity": float(test_complexity_stats["median_complexity"])
                if test_complexity_stats["median_complexity"]
                else 0,
                "test_file_count": test_complexity_stats["test_file_count"] or 0,
            }

        # Populate coverage info
        if coverage_stats:
            result["coverage_info"] = {
                "average_coverage": float(coverage_stats["avg_coverage"])
                if coverage_stats["avg_coverage"]
                else 0,
                "min_coverage": float(coverage_stats["min_coverage"])
                if coverage_stats["min_coverage"]
                else 0,
                "max_coverage": float(coverage_stats["max_coverage"])
                if coverage_stats["max_coverage"]
                else 0,
                "files_with_coverage": coverage_stats["files_with_coverage"] or 0,
                "total_files": coverage_stats["total_files"] or 0,
                "coverage_percentage": round(
                    (
                        coverage_stats["files_with_coverage"]
                        / coverage_stats["total_files"]
                        * 100
                    ),
                    2,
                )
                if coverage_stats["total_files"] > 0
                else 0,
            }

        # Add filesystem coverage detection as fallback
        fs_coverage_info = _find_coverage_info(project_root)
        if fs_coverage_info:
            result["coverage_info"]["filesystem_coverage"] = fs_coverage_info
            if not result["stats"]["test_coverage_estimate"]:
                result["stats"]["test_coverage_estimate"] = fs_coverage_info.get(
                    "overall_coverage"
                )

        # Update stats
        result["stats"].update(
            {
                "total_test_files": len(result["test_files"]),
                "total_source_files_with_tests": len(result["source_mappings"]),
                "test_coverage_estimate": result["coverage_info"].get(
                    "average_coverage"
                )
                or result["stats"]["test_coverage_estimate"],
                "avg_test_file_complexity": result["complexity_analysis"].get(
                    "average_complexity"
                ),
                "total_test_coverage": result["coverage_info"].get(
                    "coverage_percentage"
                ),
            }
        )

        return result

    except Exception as e:
        return {
            "error": f"Failed to analyze tests: {str(e)}",
            "test_files": [],
            "source_mappings": {},
            "test_types": {
                "unit": [],
                "integration": [],
                "functional": [],
                "other": [],
            },
            "coverage_info": {},
            "quality_metrics": {},
            "complexity_analysis": {},
            "stats": {"total_test_files": 0, "total_source_files_with_tests": 0},
        }


async def get_config() -> Dict[str, Any]:
    """Configuration overview from code_elements with quality data and complexity scores.

    Provides a comprehensive configuration overview including:
    - Quality metrics from monitoring_metrics
    - Complexity scores aggregated from code_elements
    - Configuration files and their contents

    Returns:
        Dictionary containing configuration overview with quality and complexity data.
    """
    import configparser
    import json
    import os
    import re
    from pathlib import Path

    config_overview = {
        "quality_metrics": {},
        "complexity_stats": {},
        "configuration_files": [],
        "code_element_stats": {},
        "summary": {
            "total_config_files": 0,
            "avg_complexity": 0.0,
            "quality_score": None,
            "total_code_elements": 0,
        },
    }

    try:
        db = await get_db()

        # Query monitoring_metrics for quality data
        quality_data = await db.fetch_many(
            """
            SELECT
                metric_name,
                AVG(CAST(value AS FLOAT)) as avg_value,
                MIN(CAST(value AS FLOAT)) as min_value,
                MAX(CAST(value AS FLOAT)) as max_value,
                COUNT(*) as measurement_count,
                MAX(timestamp) as latest_timestamp
            FROM monitoring_metrics
            WHERE metric_name IN (
                'code_quality_score', 'technical_debt_ratio', 'maintainability_index',
                'duplication_ratio', 'test_coverage', 'cyclomatic_complexity',
                'code_smells', 'security_hotspots', 'reliability_rating'
            )
            GROUP BY metric_name
            ORDER BY metric_name
        """
        )

        # Store quality metrics
        for metric in quality_data:
            config_overview["quality_metrics"][metric["metric_name"]] = {
                "average": round(
                    float(metric["avg_value"]) if metric["avg_value"] else 0, 2
                ),
                "minimum": round(
                    float(metric["min_value"]) if metric["min_value"] else 0, 2
                ),
                "maximum": round(
                    float(metric["max_value"]) if metric["max_value"] else 0, 2
                ),
                "measurements": metric["measurement_count"],
                "latest_timestamp": str(metric["latest_timestamp"])
                if metric["latest_timestamp"]
                else None,
            }

        # Aggregate complexity scores from code_elements
        complexity_data = await db.fetch_one(
            """
            SELECT
                COUNT(*) as total_elements,
                AVG(complexity) as avg_complexity,
                MIN(complexity) as min_complexity,
                MAX(complexity) as max_complexity,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY complexity) as median_complexity,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY complexity) as p95_complexity,
                COUNT(*) FILTER (WHERE complexity > 10) as high_complexity_count,
                COUNT(*) FILTER (WHERE complexity <= 5) as low_complexity_count,
                COUNT(*) FILTER (WHERE complexity BETWEEN 6 AND 10) as medium_complexity_count
            FROM code_elements
            WHERE complexity IS NOT NULL AND complexity > 0
        """
        )

        if complexity_data:
            config_overview["complexity_stats"] = {
                "total_elements": complexity_data["total_elements"] or 0,
                "average_complexity": round(
                    float(complexity_data["avg_complexity"])
                    if complexity_data["avg_complexity"]
                    else 0,
                    2,
                ),
                "minimum_complexity": float(complexity_data["min_complexity"])
                if complexity_data["min_complexity"]
                else 0,
                "maximum_complexity": float(complexity_data["max_complexity"])
                if complexity_data["max_complexity"]
                else 0,
                "median_complexity": round(
                    float(complexity_data["median_complexity"])
                    if complexity_data["median_complexity"]
                    else 0,
                    2,
                ),
                "p95_complexity": round(
                    float(complexity_data["p95_complexity"])
                    if complexity_data["p95_complexity"]
                    else 0,
                    2,
                ),
                "high_complexity_elements": complexity_data["high_complexity_count"]
                or 0,
                "medium_complexity_elements": complexity_data["medium_complexity_count"]
                or 0,
                "low_complexity_elements": complexity_data["low_complexity_count"] or 0,
            }

        # Get complexity distribution by element type
        complexity_by_type = await db.fetch_many(
            """
            SELECT
                element_type,
                COUNT(*) as element_count,
                AVG(complexity) as avg_complexity,
                MAX(complexity) as max_complexity
            FROM code_elements
            WHERE complexity IS NOT NULL AND element_type IS NOT NULL
            GROUP BY element_type
            ORDER BY avg_complexity DESC
        """
        )

        config_overview["complexity_by_type"] = [
            {
                "element_type": row["element_type"],
                "count": row["element_count"],
                "avg_complexity": round(
                    float(row["avg_complexity"]) if row["avg_complexity"] else 0, 2
                ),
                "max_complexity": float(row["max_complexity"])
                if row["max_complexity"]
                else 0,
            }
            for row in complexity_by_type
        ]

        # Find configuration files
        config_files = await db.fetch_many(
            """
            SELECT file_path, language, line_count, last_modified, complexity
            FROM code_elements
            WHERE file_path ~* '\\.(env|config|settings|conf|yaml|yml|json|ini|toml)$'
            OR file_path ~* '(config|settings|env)\\.'
            OR name IN ('settings', 'config', 'configuration')
            ORDER BY file_path
        """
        )

        # Store configuration file info
        for file_info in config_files:
            file_obj = {
                "path": file_info["file_path"],
                "language": file_info.get("language", "unknown"),
                "lines": file_info.get("line_count", 0),
                "complexity": float(file_info["complexity"])
                if file_info.get("complexity")
                else 0,
                "last_modified": str(file_info["last_modified"])
                if file_info.get("last_modified")
                else None,
            }
            config_overview["configuration_files"].append(file_obj)

        # Get overall code element statistics
        element_stats = await db.fetch_one(
            """
            SELECT
                COUNT(*) as total_elements,
                COUNT(DISTINCT file_path) as total_files,
                COUNT(DISTINCT language) as total_languages,
                SUM(line_count) as total_lines,
                AVG(line_count) as avg_lines_per_element
            FROM code_elements
            WHERE line_count IS NOT NULL
        """
        )

        if element_stats:
            config_overview["code_element_stats"] = {
                "total_elements": element_stats["total_elements"] or 0,
                "total_files": element_stats["total_files"] or 0,
                "total_languages": element_stats["total_languages"] or 0,
                "total_lines": element_stats["total_lines"] or 0,
                "avg_lines_per_element": round(
                    float(element_stats["avg_lines_per_element"])
                    if element_stats["avg_lines_per_element"]
                    else 0,
                    2,
                ),
            }

        # Update summary
        config_overview["summary"].update(
            {
                "total_config_files": len(config_overview["configuration_files"]),
                "avg_complexity": config_overview["complexity_stats"].get(
                    "average_complexity", 0
                ),
                "quality_score": config_overview["quality_metrics"]
                .get("code_quality_score", {})
                .get("average"),
                "total_code_elements": config_overview["code_element_stats"].get(
                    "total_elements", 0
                ),
            }
        )

        return config_overview

    except Exception as e:
        return {"error": f"Failed to get configuration overview: {str(e)}"}


async def get_quality_metrics() -> Dict[str, Any]:
    """Get comprehensive code quality statistics and metrics.

    Returns:
        Dictionary containing quality metrics, complexity distribution, and health scores.
    """
    try:
        db = await get_db()

        # Get complexity metrics from code_elements
        complexity_stats = await db.fetch_one(
            """
            SELECT
                AVG(complexity) as avg_complexity,
                MIN(complexity) as min_complexity,
                MAX(complexity) as max_complexity,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY complexity) as median_complexity,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY complexity) as p95_complexity,
                COUNT(*) FILTER (WHERE complexity > 10) as high_complexity_count,
                COUNT(*) as total_elements
            FROM code_elements
            WHERE complexity IS NOT NULL
        """
        )

        # Get complexity distribution by language
        complexity_by_language = await db.fetch_many(
            """
            SELECT
                language,
                COUNT(*) as element_count,
                AVG(complexity) as avg_complexity,
                MAX(complexity) as max_complexity
            FROM code_elements
            WHERE complexity IS NOT NULL AND language IS NOT NULL
            GROUP BY language
            ORDER BY avg_complexity DESC
        """
        )

        # Get quality metrics from monitoring_metrics table
        quality_metrics = await db.fetch_many(
            """
            SELECT
                metric_name,
                AVG(CAST(value AS FLOAT)) as avg_value,
                MIN(CAST(value AS FLOAT)) as min_value,
                MAX(CAST(value AS FLOAT)) as max_value,
                COUNT(*) as measurement_count
            FROM monitoring_metrics
            WHERE metric_name IN (
                'code_quality_score', 'technical_debt_ratio', 'maintainability_index',
                'duplication_ratio', 'test_coverage', 'cyclomatic_complexity'
            )
            GROUP BY metric_name
            ORDER BY metric_name
        """
        )

        # Calculate health score based on various factors
        health_factors = {
            "complexity": 0.0,
            "test_coverage": 0.0,
            "documentation": 0.0,
            "structure": 0.0,
        }

        # Complexity health (lower is better, score inverted)
        if complexity_stats and complexity_stats["avg_complexity"]:
            avg_complexity = float(complexity_stats["avg_complexity"])
            # Score: 100 for complexity <= 5, decreasing to 0 for complexity >= 20
            health_factors["complexity"] = max(
                0, min(100, (20 - avg_complexity) * (100 / 15))
            )

        # Test coverage from metrics
        test_coverage_metric = next(
            (m for m in quality_metrics if m["metric_name"] == "test_coverage"), None
        )
        if test_coverage_metric:
            health_factors["test_coverage"] = min(
                100, test_coverage_metric["avg_value"]
            )

        # Documentation score (rough estimate based on docstrings)
        doc_stats = await db.fetch_one(
            """
            SELECT
                COUNT(*) FILTER (WHERE element_type IN ('function', 'class', 'method')) as documentable_elements,
                COUNT(*) FILTER (
                    WHERE element_type IN ('function', 'class', 'method')
                    AND (content LIKE $1 OR content LIKE $2)
                ) as documented_elements
            FROM code_elements
        """,
            '%"""%',
            "%'''%",
        )

        if doc_stats and doc_stats["documentable_elements"] > 0:
            doc_ratio = (
                doc_stats["documented_elements"] / doc_stats["documentable_elements"]
            )
            health_factors["documentation"] = doc_ratio * 100

        # Structure score based on file organization
        structure_stats = await db.fetch_one(
            """
            SELECT
                COUNT(DISTINCT file_path) as total_files,
                COUNT(DISTINCT CASE WHEN file_path ~* '/__init__\\.py$' THEN file_path END) as package_files,
                COUNT(DISTINCT CASE WHEN element_type = 'class' THEN file_path END) as files_with_classes,
                COUNT(DISTINCT CASE WHEN element_type = 'function' THEN file_path END) as files_with_functions
            FROM code_elements
        """
        )

        if structure_stats and structure_stats["total_files"] > 0:
            structure_ratio = (
                structure_stats["files_with_classes"]
                + structure_stats["files_with_functions"]
            ) / structure_stats["total_files"]
            health_factors["structure"] = min(100, structure_ratio * 100)

        # Calculate overall health score
        overall_health = sum(health_factors.values()) / len(health_factors)

        # Get file statistics
        file_stats = await db.fetch_one(
            """
            SELECT
                COUNT(DISTINCT file_path) as total_files,
                AVG(line_count) as avg_lines_per_file,
                SUM(line_count) as total_lines,
                COUNT(DISTINCT language) as languages_count
            FROM code_elements
            WHERE line_count IS NOT NULL
        """
        )

        return {
            "complexity_metrics": {
                "average": float(complexity_stats["avg_complexity"])
                if complexity_stats and complexity_stats["avg_complexity"]
                else 0,
                "minimum": float(complexity_stats["min_complexity"])
                if complexity_stats and complexity_stats["min_complexity"]
                else 0,
                "maximum": float(complexity_stats["max_complexity"])
                if complexity_stats and complexity_stats["max_complexity"]
                else 0,
                "median": float(complexity_stats["median_complexity"])
                if complexity_stats and complexity_stats["median_complexity"]
                else 0,
                "p95": float(complexity_stats["p95_complexity"])
                if complexity_stats and complexity_stats["p95_complexity"]
                else 0,
                "high_complexity_files": complexity_stats["high_complexity_count"]
                if complexity_stats
                else 0,
                "total_elements": complexity_stats["total_elements"]
                if complexity_stats
                else 0,
            },
            "complexity_by_language": [
                {
                    "language": lang["language"],
                    "element_count": lang["element_count"],
                    "avg_complexity": float(lang["avg_complexity"])
                    if lang["avg_complexity"]
                    else 0,
                    "max_complexity": float(lang["max_complexity"])
                    if lang["max_complexity"]
                    else 0,
                }
                for lang in complexity_by_language
            ],
            "quality_metrics": {
                metric["metric_name"]: {
                    "average": float(metric["avg_value"]) if metric["avg_value"] else 0,
                    "minimum": float(metric["min_value"]) if metric["min_value"] else 0,
                    "maximum": float(metric["max_value"]) if metric["max_value"] else 0,
                    "measurements": metric["measurement_count"],
                }
                for metric in quality_metrics
            },
            "health_score": {
                "overall": round(overall_health, 1),
                "factors": {k: round(v, 1) for k, v in health_factors.items()},
                "grade": (
                    "A"
                    if overall_health >= 90
                    else "B"
                    if overall_health >= 80
                    else "C"
                    if overall_health >= 70
                    else "D"
                    if overall_health >= 60
                    else "F"
                ),
            },
            "file_statistics": {
                "total_files": file_stats["total_files"] if file_stats else 0,
                "avg_lines_per_file": round(float(file_stats["avg_lines_per_file"]), 1)
                if file_stats and file_stats["avg_lines_per_file"]
                else 0,
                "total_lines": file_stats["total_lines"] if file_stats else 0,
                "languages_count": file_stats["languages_count"] if file_stats else 0,
            },
            "documentation_stats": doc_stats if doc_stats else {},
            "generated_at": "now()",
        }

    except Exception as e:
        return {"error": f"Failed to get quality metrics: {str(e)}"}


def _classify_test_type(test_file: Path) -> str:
    """Classify test type based on file path and name."""
    path_str = str(test_file).lower()

    # Check path components for type indicators
    if any(part in path_str for part in ["integration", "e2e", "end-to-end"]):
        return "integration"
    elif any(part in path_str for part in ["functional", "acceptance", "feature"]):
        return "functional"
    elif any(part in path_str for part in ["unit", "units"]):
        return "unit"
    elif "test" in path_str:
        # Default to unit tests if in a test directory but no specific type
        return "unit"
    else:
        return "other"


def _find_source_mappings(test_file: Path, project_root: Path) -> List[str]:
    """Find likely source files that correspond to this test file."""

    mappings = []

    try:
        # Strategy 1: Direct name mapping
        # test_foo.py -> foo.py
        # foo_test.py -> foo.py
        test_name = test_file.stem

        if test_name.startswith("test_"):
            source_name = test_name[5:]  # Remove 'test_' prefix
        elif test_name.endswith("_test"):
            source_name = test_name[:-5]  # Remove '_test' suffix
        else:
            source_name = test_name

        # Look for source files with the same name
        possible_source_files = list(project_root.glob(f"**/{source_name}.py"))

        for source_file in possible_source_files:
            # Skip if it's another test file
            if not any(
                part in str(source_file).lower() for part in ["test", "__pycache__"]
            ):
                rel_path = str(source_file.relative_to(project_root))
                mappings.append(rel_path)

        # Strategy 2: Look inside test file for imports
        try:
            with open(test_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Find import statements that might indicate source files
            import_patterns = [
                r"from\s+([^\s]+)\s+import",
                r"import\s+([^\s,]+)",
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Convert module path to file path
                    if "." in match and not match.startswith("."):
                        # Convert something like 'myapp.core.utils' to 'myapp/core/utils.py'
                        file_path = match.replace(".", "/") + ".py"
                        potential_file = project_root / file_path

                        if potential_file.exists() and potential_file.is_file():
                            rel_path = str(potential_file.relative_to(project_root))
                            if rel_path not in mappings:
                                mappings.append(rel_path)

        except (OSError, UnicodeDecodeError):
            # If we can't read the file, skip the import analysis
            pass

        # Strategy 3: Mirror directory structure
        # If test is in tests/unit/core/test_parser.py
        # Look for src/core/parser.py
        test_parts = test_file.parts
        if "tests" in test_parts:
            # Find the tests directory index
            tests_idx = None
            for i, part in enumerate(test_parts):
                if part == "tests":
                    tests_idx = i
                    break

            if tests_idx is not None:
                # Get the path after tests/
                remaining_parts = test_parts[tests_idx + 1 :]

                # Skip type directories like 'unit', 'integration'
                filtered_parts = []
                for part in remaining_parts:
                    if part.lower() not in ["unit", "integration", "functional", "e2e"]:
                        filtered_parts.append(part)

                if filtered_parts:
                    # Replace the test filename with source filename
                    test_filename = filtered_parts[-1]
                    if test_filename.startswith("test_"):
                        source_filename = test_filename[5:]
                    elif test_filename.endswith("_test.py"):
                        source_filename = test_filename[:-8] + ".py"
                    else:
                        source_filename = test_filename

                    # Look in common source directories
                    source_dirs = ["src", "lib", project_root.name]

                    for src_dir in source_dirs:
                        source_path_parts = (
                            [src_dir] + list(filtered_parts[:-1]) + [source_filename]
                        )
                        potential_source = project_root / Path(*source_path_parts)

                        if potential_source.exists() and potential_source.is_file():
                            rel_path = str(potential_source.relative_to(project_root))
                            if rel_path not in mappings:
                                mappings.append(rel_path)

    except Exception:
        # If any strategy fails, return what we have so far
        pass

    return mappings


def _find_coverage_info(project_root: Path) -> Optional[Dict[str, Any]]:
    """Look for test coverage information."""

    coverage_info = {}

    # Look for common coverage files
    coverage_files = [
        ".coverage",
        "coverage.xml",
        "coverage.json",
        "htmlcov/index.html",
        "coverage-reports/index.html",
    ]

    found_files = []
    for coverage_file in coverage_files:
        coverage_path = project_root / coverage_file
        if coverage_path.exists():
            found_files.append(str(coverage_path.relative_to(project_root)))

    if found_files:
        coverage_info["coverage_files"] = found_files

        # Try to extract coverage percentage if possible
        coverage_info["overall_coverage"] = _extract_coverage_percentage(
            project_root, found_files
        )

    # Look for pytest.ini, tox.ini, or setup.cfg for test configuration
    config_files = []
    for config_file in ["pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml"]:
        config_path = project_root / config_file
        if config_path.exists():
            config_files.append(str(config_path.relative_to(project_root)))

    if config_files:
        coverage_info["test_config_files"] = config_files

    return coverage_info if coverage_info else None


def _extract_coverage_percentage(
    project_root: Path, coverage_files: List[str]
) -> Optional[float]:
    """Try to extract coverage percentage from coverage files."""

    try:
        # Try to read coverage.xml if available
        for file_path in coverage_files:
            if file_path.endswith("coverage.xml"):
                coverage_xml = project_root / file_path
                try:
                    with open(coverage_xml, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for line coverage in XML
                    match = re.search(r'line-rate="([0-9.]+)"', content)
                    if match:
                        return float(match.group(1)) * 100

                except (OSError, ValueError):
                    continue

        # Try to read HTML coverage if available
        for file_path in coverage_files:
            if "index.html" in file_path:
                coverage_html = project_root / file_path
                try:
                    with open(coverage_html, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Look for coverage percentage in HTML
                    patterns = [r"(\d+)%", r"coverage:\s*(\d+(?:\.\d+)?)%"]

                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            # Take the last/highest percentage found
                            return float(matches[-1])

                except (OSError, ValueError):
                    continue

    except Exception:
        pass

    return None


async def _process_config_file(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Process a configuration file and extract key values."""
    try:
        file_ext = path_obj.suffix.lower()
        file_name = path_obj.name.lower()

        if file_ext == ".env" or file_name.startswith(".env"):
            _process_env_file(path_obj, config_overview)
        elif file_ext in [".py"] and ("settings" in file_name or "config" in file_name):
            await _process_python_config_file(path_obj, config_overview)
        elif file_ext in [".yaml", ".yml"]:
            _process_yaml_file(path_obj, config_overview)
        elif file_ext == ".json":
            _process_json_file(path_obj, config_overview)
        elif file_ext in [".ini", ".cfg"]:
            _process_ini_file(path_obj, config_overview)
        elif file_ext == ".toml":
            _process_toml_file(path_obj, config_overview)

    except Exception as e:
        print(f"Error processing config file {path_obj}: {e}")


def _process_env_file(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Process .env files and extract environment variables."""
    try:
        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        env_vars = {}
        for line_no, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Mask sensitive values
                if any(
                    sensitive in key.lower()
                    for sensitive in ["password", "secret", "key", "token"]
                ):
                    value = "***REDACTED***"
                elif len(value) > 100:
                    value = value[:50] + "...[truncated]"

                env_vars[key] = value

        if env_vars:
            config_overview["env_vars"][
                str(path_obj.relative_to(Path.cwd()))
            ] = env_vars

    except Exception as e:
        print(f"Error processing env file {path_obj}: {e}")


async def _process_python_config_file(
    path_obj: Path, config_overview: Dict[str, Any]
) -> None:
    """Process Python configuration files and extract settings."""
    try:
        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        settings = {}

        # Look for simple variable assignments
        assignment_pattern = r"^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$"
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            match = re.match(assignment_pattern, line)
            if match:
                key, value = match.groups()
                # Try to evaluate simple values
                try:
                    # Only evaluate simple literals
                    if (
                        value.startswith(("True", "False", "None"))
                        or value.isdigit()
                        or (value.startswith('"') and value.endswith('"'))
                        or (value.startswith("'") and value.endswith("'"))
                    ):
                        eval_value = eval(value)
                        settings[key] = str(eval_value)
                    else:
                        settings[key] = value[:100] + (
                            "..." if len(value) > 100 else ""
                        )
                except:
                    settings[key] = value[:100] + ("..." if len(value) > 100 else "")

        if settings:
            config_overview["python_settings"][
                str(path_obj.relative_to(Path.cwd()))
            ] = settings

    except Exception as e:
        print(f"Error processing Python config file {path_obj}: {e}")


def _process_yaml_file(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Process YAML configuration files."""
    try:
        import yaml

        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            data = yaml.safe_load(f)

        if data and isinstance(data, dict):
            # Flatten and sanitize the data
            flattened = _flatten_dict(data)
            config_overview["yaml_config"][
                str(path_obj.relative_to(Path.cwd()))
            ] = flattened

    except ImportError:
        # YAML not available, try basic parsing
        _process_yaml_file_basic(path_obj, config_overview)
    except Exception as e:
        print(f"Error processing YAML file {path_obj}: {e}")


def _process_yaml_file_basic(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Basic YAML processing without PyYAML library."""
    try:
        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        yaml_data = {}
        current_section = None

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line and not line.startswith(" "):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if value:
                    yaml_data[key] = value
                else:
                    current_section = key
                    yaml_data[key] = {}
            elif current_section and line.startswith(" ") and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if value:
                    yaml_data[current_section][key] = value

        if yaml_data:
            config_overview["yaml_config"][
                str(path_obj.relative_to(Path.cwd()))
            ] = yaml_data

    except Exception as e:
        print(f"Error processing YAML file {path_obj}: {e}")


def _process_json_file(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Process JSON configuration files."""
    try:
        import json

        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)

        if data and isinstance(data, dict):
            flattened = _flatten_dict(data)
            config_overview["json_config"][
                str(path_obj.relative_to(Path.cwd()))
            ] = flattened

    except Exception as e:
        print(f"Error processing JSON file {path_obj}: {e}")


def _process_ini_file(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Process INI/CFG configuration files."""
    try:
        import configparser

        config = configparser.ConfigParser()
        config.read(path_obj, encoding="utf-8")

        ini_data = {}
        for section_name in config.sections():
            section_data = {}
            for key, value in config[section_name].items():
                section_data[key] = value
            ini_data[section_name] = section_data

        if ini_data:
            config_overview["ini_config"][
                str(path_obj.relative_to(Path.cwd()))
            ] = ini_data

    except Exception as e:
        print(f"Error processing INI file {path_obj}: {e}")


def _process_toml_file(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Process TOML configuration files (pyproject.toml, etc.)."""
    try:
        import toml

        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            data = toml.load(f)

        if data and isinstance(data, dict):
            flattened = _flatten_dict(data)
            config_overview["project_config"][
                str(path_obj.relative_to(Path.cwd()))
            ] = flattened

    except ImportError:
        # TOML library not available, try basic parsing
        _process_toml_file_basic(path_obj, config_overview)
    except Exception as e:
        print(f"Error processing TOML file {path_obj}: {e}")


def _process_toml_file_basic(path_obj: Path, config_overview: Dict[str, Any]) -> None:
    """Basic TOML processing without toml library."""
    try:
        with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        toml_data = {}
        current_section = None

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Section header
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1]
                current_section = section_name
                toml_data[section_name] = {}
            # Key-value pair
            elif "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"'")

                if current_section:
                    toml_data[current_section][key] = value
                else:
                    toml_data[key] = value

        if toml_data:
            config_overview["project_config"][
                str(path_obj.relative_to(Path.cwd()))
            ] = toml_data

    except Exception as e:
        print(f"Error processing TOML file {path_obj}: {e}")


def _flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten a nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            # Convert to string and truncate if too long
            str_value = str(v)
            if len(str_value) > 200:
                str_value = str_value[:200] + "...[truncated]"
            items.append((new_key, str_value))
    return dict(items)


async def _fallback_filesystem_search(config_overview: Dict[str, Any]) -> None:
    """Fallback filesystem search for configuration files when database is empty."""
    try:
        project_root = Path.cwd()

        # Common configuration file patterns
        config_patterns = [
            "**/.env*",
            "**/config.*",
            "**/settings.*",
            "**/*.config.*",
            "**/pyproject.toml",
            "**/setup.cfg",
            "**/setup.py",
            "**/*.ini",
            "**/*.yaml",
            "**/*.yml",
            "**/*.json",
        ]

        found_files = set()

        # Search for configuration files
        for pattern in config_patterns:
            try:
                for file_path in project_root.glob(pattern):
                    if (
                        file_path.is_file()
                        and file_path.stat().st_size < 1024 * 1024
                        and not any(  # Max 1MB
                            part.startswith(".")
                            and part not in [".env", ".env.local", ".env.example"]
                            for part in file_path.parts
                        )
                        and "__pycache__" not in str(file_path)
                    ):
                        found_files.add(file_path)
            except Exception as e:
                print(f"Error searching pattern {pattern}: {e}")
                continue

        # Process found files
        for file_path in found_files:
            # Check if already processed
            rel_path = str(file_path.relative_to(project_root))
            if not any(rel_path == f["path"] for f in config_overview["files"]):
                file_info = {
                    "path": rel_path,
                    "size": file_path.stat().st_size,
                    "modified": str(file_path.stat().st_mtime),
                    "type": file_path.suffix[1:] if file_path.suffix else "unknown",
                }
                config_overview["files"].append(file_info)

                # Process the file content
                if file_path.stat().st_size < 512 * 1024:  # Max 512KB
                    await _process_config_file(file_path, config_overview)

    except Exception as e:
        print(f"Error in fallback filesystem search: {e}")


async def _find_db_source_mappings(db, test_file_path: str) -> List[str]:
    """Find source files that correspond to this test file using database queries."""

    mappings = []

    try:
        # Strategy 1: Direct name mapping
        # test_foo.py -> foo.py
        # foo_test.py -> foo.py
        test_filename = Path(test_file_path).stem

        if test_filename.startswith("test_"):
            source_name = test_filename[5:]  # Remove 'test_' prefix
        elif test_filename.endswith("_test"):
            source_name = test_filename[:-5]  # Remove '_test' suffix
        else:
            source_name = test_filename

        # Look for source files with the same name in database
        source_files = await db.fetch_many(
            """
            SELECT DISTINCT file_path
            FROM code_elements
            WHERE file_path ~* $1
            AND NOT file_path ~* '(test_.*\\.py|.*_test\\.py|tests/.*\\.py|test/.*\\.py)'
            AND element_type = 'file'
        """,
            f".*{source_name}\\.py$",
        )

        for record in source_files:
            mappings.append(record["file_path"])

        # Strategy 2: Look for related source files based on similar naming patterns
        # Since we don't have content in the code_elements table, we'll use naming heuristics
        if source_name:
            similar_files = await db.fetch_many(
                """
                SELECT DISTINCT file_path
                FROM code_elements
                WHERE file_path ~* $1
                AND NOT file_path ~* '(test_.*\\.py|.*_test\\.py|tests/.*\\.py|test/.*\\.py)'
                AND element_type = 'file'
                LIMIT 10
            """,
                f".*{source_name}.*\\.py$",
            )

            for record in similar_files:
                if record["file_path"] not in mappings:
                    mappings.append(record["file_path"])

        # Strategy 3: Mirror directory structure
        # If test is in tests/unit/core/test_parser.py
        # Look for src/core/parser.py
        test_parts = Path(test_file_path).parts
        if "tests" in test_parts:
            # Find the tests directory index
            tests_idx = None
            for i, part in enumerate(test_parts):
                if part == "tests":
                    tests_idx = i
                    break

            if tests_idx is not None:
                # Get the path after tests/
                remaining_parts = test_parts[tests_idx + 1 :]

                # Skip type directories like 'unit', 'integration'
                filtered_parts = []
                for part in remaining_parts:
                    if part.lower() not in ["unit", "integration", "functional", "e2e"]:
                        filtered_parts.append(part)

                if filtered_parts:
                    # Replace the test filename with source filename
                    test_filename = filtered_parts[-1]
                    if test_filename.startswith("test_"):
                        source_filename = test_filename[5:]
                    elif test_filename.endswith("_test.py"):
                        source_filename = test_filename[:-8] + ".py"
                    else:
                        source_filename = test_filename

                    # Look in common source directories
                    source_dirs = ["src", "lib"]

                    for src_dir in source_dirs:
                        source_path_parts = (
                            [src_dir] + list(filtered_parts[:-1]) + [source_filename]
                        )
                        potential_source = "/".join(source_path_parts)

                        # Check if this file exists in database
                        source_records = await db.fetch_many(
                            """
                            SELECT file_path
                            FROM code_elements
                            WHERE file_path = $1
                            AND element_type = 'file'
                        """,
                            potential_source,
                        )

                        if source_records:
                            rel_path = source_records[0]["file_path"]
                            if rel_path not in mappings:
                                mappings.append(rel_path)

    except Exception:
        # If any strategy fails, return what we have so far
        pass

    return mappings


async def _fallback_filesystem_test_scan(project_root: Path) -> Dict[str, Any]:
    """Fallback filesystem scan for test files when database is empty."""

    result = {
        "test_files": [],
        "test_types": {"unit": [], "integration": [], "functional": [], "other": []},
        "source_mappings": {},
    }

    try:
        # Find all test files using common patterns
        test_patterns = [
            "**/test_*.py",
            "**/*_test.py",
            "**/tests/*.py",
            "**/test/**/*.py",
        ]

        test_files = []
        for pattern in test_patterns:
            test_files.extend(project_root.glob(pattern))

        # Remove duplicates and filter out __pycache__ and similar
        test_files = list(
            set(
                [
                    f
                    for f in test_files
                    if f.is_file()
                    and not any(
                        part.startswith(".") or part == "__pycache__"
                        for part in f.parts
                    )
                ]
            )
        )

        # Process each test file
        for test_file in test_files:
            rel_path = str(test_file.relative_to(project_root))

            test_info = {
                "path": rel_path,
                "absolute_path": str(test_file),
                "size": test_file.stat().st_size,
                "type": _classify_test_type(test_file),
                "complexity_score": None,
                "test_coverage": None,
                "language": "python",
                "last_modified": None,
                "mapped_sources": _find_source_mappings(test_file, project_root),
            }

            result["test_files"].append(test_info)

            # Add to type classification
            test_type = test_info["type"]
            if test_type in result["test_types"]:
                result["test_types"][test_type].append(rel_path)
            else:
                result["test_types"]["other"].append(rel_path)

            # Build source mappings
            for source_file in test_info["mapped_sources"]:
                if source_file not in result["source_mappings"]:
                    result["source_mappings"][source_file] = []
                result["source_mappings"][source_file].append(rel_path)

    except Exception as e:
        print(f"Error in fallback filesystem test scan: {e}")

    return result
