"""
Dependency Analyzer - AI-powered dependency analysis and optimization using OpenAI's O3 models.

This script analyzes project dependencies for security vulnerabilities, version conflicts,
unused dependencies, and provides intelligent recommendations for optimization.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Optional

import yaml

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
    pass
try:
    from openai import OpenAI
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
        ConfigManager,
    )
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from o3_logger.logger import setup_logger
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass
try:
    from schemas.dependency_analyzer_input_schema import DependencyAnalysisInput
    from schemas.dependency_analyzer_output_schema import DependencyAnalysisOutput
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class DependencyParser:
    """Parses dependency files from different project types."""

    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def parse_requirements_txt(self, file_path: Path) -> dict[str, Any]:
        """
        Parse requirements.txt file.

        Args:
            file_path: Path to requirements.txt

        Returns:
            Dictionary containing parsed dependencies
        """
        self.logger.log_info(f"Parsing requirements.txt: {file_path}")
        dependencies = {"direct": [], "dev": [], "optional": []}
        try:
            with open(file_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line_clean = line.strip()
                    if not line_clean or line_clean.startswith("#"):
                        continue
                    else:
                        pass
                    dep_info = self._parse_python_dependency(line_clean)
                    if dep_info:
                        dependencies["direct"].append(dep_info)
                    else:
                        pass
                else:
                    pass
        except Exception as e:
            self.logger.log_error(f"Failed to parse requirements.txt: {e}")
        else:
            pass
        finally:
            pass
        return dependencies

    def parse_package_json(self, file_path: Path) -> dict[str, Any]:
        """
        Parse package.json file.

        Args:
            file_path: Path to package.json

        Returns:
            Dictionary containing parsed dependencies
        """
        self.logger.log_info(f"Parsing package.json: {file_path}")
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            dependencies = {"direct": [], "dev": [], "optional": []}
            for dep_name, version in data.get("dependencies", {}).items():
                dep_info = self._parse_node_dependency(dep_name, version)
                dependencies["direct"].append(dep_info)
            else:
                pass
            for dep_name, version in data.get("devDependencies", {}).items():
                dep_info = self._parse_node_dependency(dep_name, version)
                dependencies["dev"].append(dep_info)
            else:
                pass
            return dependencies
        except Exception as e:
            self.logger.log_error(f"Failed to parse package.json: {e}")
            return {"direct": [], "dev": [], "optional": []}
        else:
            pass
        finally:
            pass

    def parse_pyproject_toml(self, file_path: Path) -> dict[str, Any]:
        """
        Parse pyproject.toml file.

        Args:
            file_path: Path to pyproject.toml

        Returns:
            Dictionary containing parsed dependencies
        """
        self.logger.log_info(f"Parsing pyproject.toml: {file_path}")
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            dependencies = {"direct": [], "dev": [], "optional": []}
            project_deps = data.get("project", {}).get("dependencies", [])
            for dep in project_deps:
                dep_info = self._parse_python_dependency(dep)
                if dep_info:
                    dependencies["direct"].append(dep_info)
                else:
                    pass
            else:
                pass
            optional_deps = data.get("project", {}).get("optional-dependencies", {})
            for group_name, deps in optional_deps.items():
                for dep in deps:
                    dep_info = self._parse_python_dependency(dep)
                    if dep_info:
                        dep_info["group"] = group_name
                        dependencies["optional"].append(dep_info)
                    else:
                        pass
                else:
                    pass
            else:
                pass
            return dependencies
        except Exception as e:
            self.logger.log_error(f"Failed to parse pyproject.toml: {e}")
            return {"direct": [], "dev": [], "optional": []}
        else:
            pass
        finally:
            pass

    def _parse_python_dependency(self, dep_string: str) -> Optional[dict[str, Any]]:
        """
        Parse a Python dependency string.

        Args:
            dep_string: Dependency string (e.g., "requests>=2.31.0")

        Returns:
            Dictionary containing dependency information
        """
        try:
            if "==" in dep_string:
                name, version = dep_string.split("==", 1)
                constraint = "=="
            elif ">=" in dep_string:
                name, version = dep_string.split(">=", 1)
                constraint = ">="
            elif "<=" in dep_string:
                name, version = dep_string.split("<=", 1)
                constraint = "<="
            elif "~=" in dep_string:
                name, version = dep_string.split("~=", 1)
                constraint = "~="
            elif "!=" in dep_string:
                name, version = dep_string.split("!=", 1)
                constraint = "!="
            else:
                name = dep_string
                version = None
                constraint = None
            return {
                "name": name.strip(),
                "version": version.strip() if version else None,
                "constraint": constraint,
                "type": "python",
            }
        except Exception as e:
            self.logger.log_error(
                f"Failed to parse Python dependency '{dep_string}': {e}"
            )
            return None
        else:
            pass
        finally:
            pass

    def _parse_node_dependency(self, name: str, version: str) -> dict[str, Any]:
        """
        Parse a Node.js dependency.

        Args:
            name: Package name
            version: Version string

        Returns:
            Dictionary containing dependency information
        """
        return {"name": name, "version": version, "type": "nodejs"}


class SecurityScanner:
    """Scans dependencies for security vulnerabilities."""

    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def scan_vulnerabilities(
        self, dependencies: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Scan dependencies for security vulnerabilities.

        Args:
            dependencies: Dictionary of dependencies

        Returns:
            List of vulnerability information
        """
        self.logger.log_info("Scanning dependencies for vulnerabilities")
        vulnerabilities = []
        all_deps = []
        for dep_type, deps in dependencies.items():
            for dep in deps:
                dep["dep_type"] = dep_type
                all_deps.append(dep)
            else:
                pass
        else:
            pass
        for dep in all_deps:
            vuln_info = self._analyze_dependency_vulnerability(dep)
            if vuln_info:
                vulnerabilities.append(vuln_info)
            else:
                pass
        else:
            pass
        return vulnerabilities

    def _analyze_dependency_vulnerability(
        self, dep: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """
        Analyze a single dependency for vulnerabilities using O3 model.

        Args:
            dep: Dependency information

        Returns:
            Vulnerability information if found
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            prompt = f"""\nAnalyze the following dependency for potential security vulnerabilities:\n\nDependency: {dep['name']}\nVersion: {dep.get('version', 'Not specified')}\nType: {dep['type']}\nDependency Type: {dep.get('dep_type', 'direct')}\n\nConsider:\n1. Known CVEs for this package\n2. Version-specific vulnerabilities\n3. Supply chain risks\n4. License compliance issues\n5. Maintenance status\n\nReturn a JSON object with:\n- vulnerability_found: boolean\n- severity: "low", "medium", "high", "critical"\n- description: string\n- cve_ids: list of strings\n- recommendation: string\n- affected_versions: string\n\nIf no vulnerabilities found, return null.\n"""
            response = client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security expert analyzing software dependencies for vulnerabilities.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=16000,
                temperature=0.1,
            )
            result = response.choices[0].message.content.strip()
            if result and result != "null":
                return json.loads(result)
            else:
                pass
        except Exception as e:
            self.logger.log_error(
                f"Failed to analyze vulnerability for {dep['name']}: {e}"
            )
        else:
            pass
        finally:
            pass
        return None


class DependencyOptimizer:
    """Provides optimization recommendations for dependencies."""

    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def analyze_dependencies(self, dependencies: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze dependencies and provide optimization recommendations.

        Args:
            dependencies: Dictionary of dependencies

        Returns:
            Dictionary containing analysis results and recommendations
        """
        self.logger.log_info("Analyzing dependencies for optimization")
        analysis = {
            "unused_dependencies": [],
            "outdated_dependencies": [],
            "conflicting_dependencies": [],
            "recommendations": [],
            "optimization_score": 0,
        }
        analysis["unused_dependencies"] = self._find_unused_dependencies(dependencies)
        analysis["outdated_dependencies"] = self._find_outdated_dependencies(
            dependencies
        )
        analysis["conflicting_dependencies"] = self._find_conflicting_dependencies(
            dependencies
        )
        analysis["recommendations"] = self._generate_recommendations(analysis)
        analysis["optimization_score"] = self._calculate_optimization_score(analysis)
        return analysis

    def _find_unused_dependencies(
        self, dependencies: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Find potentially unused dependencies.

        Args:
            dependencies: Dictionary of dependencies

        Returns:
            List of potentially unused dependencies
        """
        unused = []
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            dep_list = []
            for dep_type, deps in dependencies.items():
                for dep in deps:
                    dep_list.append(f"{dep['name']} ({dep.get('version', 'latest')})")
                else:
                    pass
            else:
                pass
            prompt = f'\nAnalyze the following dependencies and identify which ones are likely to be unused or redundant:\n\nDependencies:\n{chr(10).join(dep_list)}\n\nConsider:\n1. Common unused patterns\n2. Redundant packages\n3. Development-only dependencies in production\n4. Obsolete packages\n5. Alternative packages that are more popular\n\nReturn a JSON array of objects with:\n- name: package name\n- reason: why it might be unused\n- confidence: "low", "medium", "high"\n- recommendation: what to do about it\n'
            response = client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a dependency optimization expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            result = response.choices[0].message.content.strip()
            if result:
                unused = json.loads(result)
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Failed to analyze unused dependencies: {e}")
        else:
            pass
        finally:
            pass
        return unused

    def _find_outdated_dependencies(
        self, dependencies: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Find outdated dependencies.

        Args:
            dependencies: Dictionary of dependencies

        Returns:
            List of outdated dependencies
        """
        outdated = []
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            dep_list = []
            for dep_type, deps in dependencies.items():
                for dep in deps:
                    dep_list.append(f"{dep['name']} {dep.get('version', 'latest')}")
                else:
                    pass
            else:
                pass
            prompt = f'\nAnalyze the following dependencies and identify which ones are likely to be outdated:\n\nDependencies:\n{chr(10).join(dep_list)}\n\nConsider:\n1. Version age and release frequency\n2. Security updates available\n3. Breaking changes in newer versions\n4. Performance improvements\n5. Bug fixes\n\nReturn a JSON array of objects with:\n- name: package name\n- current_version: current version\n- latest_version: latest available version\n- age_days: estimated days since last update\n- priority: "low", "medium", "high"\n- update_recommendation: string\n'
            response = client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a dependency management expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            result = response.choices[0].message.content.strip()
            if result:
                outdated = json.loads(result)
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Failed to analyze outdated dependencies: {e}")
        else:
            pass
        finally:
            pass
        return outdated

    def _find_conflicting_dependencies(
        self, dependencies: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Find conflicting dependencies.

        Args:
            dependencies: Dictionary of dependencies

        Returns:
            List of conflicting dependencies
        """
        conflicts = []
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            dep_list = []
            for dep_type, deps in dependencies.items():
                for dep in deps:
                    dep_list.append(f"{dep['name']} {dep.get('version', 'latest')}")
                else:
                    pass
            else:
                pass
            prompt = f'\nAnalyze the following dependencies and identify potential conflicts:\n\nDependencies:\n{chr(10).join(dep_list)}\n\nConsider:\n1. Version conflicts between packages\n2. Incompatible dependency chains\n3. Duplicate packages with different versions\n4. License conflicts\n5. Architecture conflicts\n\nReturn a JSON array of objects with:\n- conflict_type: "version", "license", "architecture", "duplicate"\n- packages: array of conflicting package names\n- description: description of the conflict\n- severity: "low", "medium", "high"\n- resolution: suggested resolution\n'
            response = client.chat.completions.create(
                model="o3-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a dependency conflict resolution expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=16000,
                temperature=0.2,
            )
            result = response.choices[0].message.content.strip()
            if result:
                conflicts = json.loads(result)
            else:
                pass
        except Exception as e:
            self.logger.log_error(f"Failed to analyze conflicting dependencies: {e}")
        else:
            pass
        finally:
            pass
        return conflicts

    def _generate_recommendations(self, analysis: dict[str, Any]) -> list[str]:
        """
        Generate optimization recommendations.

        Args:
            analysis: Analysis results

        Returns:
            List of recommendations
        """
        recommendations = []
        if analysis["unused_dependencies"]:
            recommendations.append(
                "Remove unused dependencies to reduce bundle size and security surface"
            )
        else:
            pass
        if analysis["outdated_dependencies"]:
            recommendations.append(
                "Update outdated dependencies to get security patches and performance improvements"
            )
        else:
            pass
        if analysis["conflicting_dependencies"]:
            recommendations.append(
                "Resolve dependency conflicts to ensure stable builds"
            )
        else:
            pass
        recommendations.extend(
            [
                "Use dependency pinning for reproducible builds",
                "Regularly audit dependencies for security vulnerabilities",
                "Consider using dependency management tools",
                "Monitor dependency updates and breaking changes",
            ]
        )
        return recommendations

    def _calculate_optimization_score(self, analysis: dict[str, Any]) -> int:
        """
        Calculate optimization score (0-100).

        Args:
            analysis: Analysis results

        Returns:
            Optimization score
        """
        score = 100
        score -= len(analysis["unused_dependencies"]) * 5
        score -= len(analysis["outdated_dependencies"]) * 3
        score -= len(analysis["conflicting_dependencies"]) * 10
        return max(0, score)


class DependencyAnalyzer:
    """Main class for dependency analysis."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize with configuration."""
        self.config_manager = ConfigManager(config_path)
        try:
            self.logger = get_logger()
        except RuntimeError:
            log_config = self.config_manager.get_logging_config()
            setup_logger(log_config)
            self.logger = get_logger()
        else:
            pass
        finally:
            pass
        self.parser = DependencyParser(self.logger)
        self.scanner = SecurityScanner(self.logger)
        self.optimizer = DependencyOptimizer(self.logger)
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Create necessary directories."""
        directories = ["analysis_reports", "logs"]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        else:
            pass

    def analyze_project(
        self, input_data: DependencyAnalysisInput
    ) -> DependencyAnalysisOutput:
        """
        Analyze project dependencies.

        Args:
            input_data: Dependency analysis input data

        Returns:
            Dependency analysis output with results
        """
        self.logger.log_info(
            f"Starting dependency analysis for: {input_data.project_path}"
        )
        try:
            project_path = Path(input_data.project_path)
            if not project_path.exists():
                raise ValueError(f"Project path does not exist: {project_path}")
            else:
                pass
            dependencies = self._parse_project_dependencies(project_path)
            vulnerabilities = self.scanner.scan_vulnerabilities(dependencies)
            optimization = self.optimizer.analyze_dependencies(dependencies)
            report = self._generate_analysis_report(
                dependencies, vulnerabilities, optimization, input_data
            )
            report_path = self._save_analysis_report(report, project_path)
            self.logger.log_info(
                f"Dependency analysis completed successfully: {report_path}"
            )
            return DependencyAnalysisOutput(
                success=True,
                project_path=str(project_path),
                dependencies=dependencies,
                vulnerabilities=vulnerabilities,
                optimization=optimization,
                report_path=str(report_path),
                error_message=None,
            )
        except Exception as e:
            self.logger.log_error(f"Dependency analysis failed: {e}")
            return DependencyAnalysisOutput(
                success=False,
                project_path="",
                dependencies={},
                vulnerabilities=[],
                optimization={},
                report_path="",
                error_message=str(e),
            )
        else:
            pass
        finally:
            pass

    def _parse_project_dependencies(self, project_path: Path) -> dict[str, Any]:
        """
        Parse all dependency files in the project.

        Args:
            project_path: Path to the project

        Returns:
            Dictionary containing all dependencies
        """
        dependencies = {"direct": [], "dev": [], "optional": []}
        requirements_files = list(project_path.glob("requirements*.txt"))
        for req_file in requirements_files:
            deps = self.parser.parse_requirements_txt(req_file)
            dependencies["direct"].extend(deps["direct"])
            dependencies["dev"].extend(deps["dev"])
            dependencies["optional"].extend(deps["optional"])
        else:
            pass
        pyproject_file = project_path / "pyproject.toml"
        if pyproject_file.exists():
            deps = self.parser.parse_pyproject_toml(pyproject_file)
            dependencies["direct"].extend(deps["direct"])
            dependencies["dev"].extend(deps["dev"])
            dependencies["optional"].extend(deps["optional"])
        else:
            pass
        package_file = project_path / "package.json"
        if package_file.exists():
            deps = self.parser.parse_package_json(package_file)
            dependencies["direct"].extend(deps["direct"])
            dependencies["dev"].extend(deps["dev"])
            dependencies["optional"].extend(deps["optional"])
        else:
            pass
        return dependencies

    def _generate_analysis_report(
        self,
        dependencies: dict[str, Any],
        vulnerabilities: list[dict[str, Any]],
        optimization: dict[str, Any],
        input_data: DependencyAnalysisInput,
    ) -> dict[str, Any]:
        """
        Generate comprehensive analysis report.

        Args:
            dependencies: Parsed dependencies
            vulnerabilities: Found vulnerabilities
            optimization: Optimization analysis
            input_data: Input data

        Returns:
            Analysis report
        """
        report = {
            "project_path": str(input_data.project_path),
            "analysis_timestamp": self._get_current_timestamp(),
            "summary": {
                "total_dependencies": len(dependencies["direct"])
                + len(dependencies["dev"])
                + len(dependencies["optional"]),
                "direct_dependencies": len(dependencies["direct"]),
                "dev_dependencies": len(dependencies["dev"]),
                "optional_dependencies": len(dependencies["optional"]),
                "vulnerabilities_found": len(vulnerabilities),
                "optimization_score": optimization["optimization_score"],
            },
            "dependencies": dependencies,
            "vulnerabilities": vulnerabilities,
            "optimization": optimization,
            "recommendations": optimization["recommendations"],
        }
        return report

    def _save_analysis_report(self, report: dict[str, Any], project_path: Path) -> Path:
        """
        Save analysis report to file.

        Args:
            report: Analysis report
            project_path: Project path

        Returns:
            Path to saved report
        """
        timestamp = self._get_current_timestamp().replace(":", "-").replace(" ", "_")
        report_filename = f"dependency_analysis_{timestamp}.json"
        report_path = Path("analysis_reports") / report_filename
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return report_path

    def _get_current_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze project dependencies with AI-powered insights"
    )
    parser.add_argument("project_path", help="Path to the project to analyze")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--output", "-o", help="Output directory for reports")
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "html", "markdown"],
        default="json",
        help="Output format for reports",
    )
    args = parser.parse_args()
    input_data = DependencyAnalysisInput(
        project_path=args.project_path,
        output_format=args.format,
        output_directory=args.output,
    )
    analyzer = DependencyAnalyzer(args.config)
    result = analyzer.analyze_project(input_data)
    if result.success:
        if result.vulnerabilities:
            for vuln in result.vulnerabilities[:5]:
                pass
            else:
                pass
        else:
            pass
        if result.optimization["recommendations"]:
            for rec in result.optimization["recommendations"][:3]:
                pass
            else:
                pass
        else:
            pass
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
else:
    pass
