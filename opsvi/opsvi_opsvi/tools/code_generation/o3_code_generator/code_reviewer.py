"""
Code Reviewer - AI-powered code review and analysis using OpenAI's O3 models.

This module performs comprehensive code reviews, analyzing code quality, security,
performance, maintainability, and adherence to best practices using OpenAI's O3 models.
"""

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
    ConfigManager,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import get_logger
from src.tools.code_generation.o3_code_generator.schemas.code_reviewer_input_schema import (
    CodeReviewInput,
)
from src.tools.code_generation.o3_code_generator.schemas.code_reviewer_output_schema import (
    CodeReviewOutput,
)
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)
from src.tools.code_generation.o3_code_generator.utils.file_generator import (
    FileGenerator,
)
from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
    OutputFormatter,
)
from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
    PromptBuilder,
)


class CodeParser:
    """Parses and analyzes code files."""

    def __init__(self) -> None:
        """
        Initialize CodeParser.

        Attributes:
            logger: O3Logger instance for logging.
        """
        self.logger = get_logger()

    def parse_file(self, file_path: Path) -> dict[str, object]:
        """
        Parse a code file and extract relevant information.

        Args:
            file_path: Path to the code file

        Returns:
            Dictionary containing parsed code information
        """
        self.logger.log_info(f"Parsing file: {file_path}")
        try:
            content = file_path.read_text(encoding="utf-8")
            file_info: dict[str, object] = {
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix,
                "size": len(content),
                "lines": len(content.splitlines()),
                "content": content,
                "language": self._detect_language(file_path),
                "structure": self._analyze_structure(content, file_path.suffix),
            }
            return file_info
        except Exception as e:
            self.logger.log_error(f"Failed to parse file {file_path}: {e}")
            raise RuntimeError(f"Parsing failed for {file_path}") from e
        else:
            pass
        finally:
            pass

    def _detect_language(self, file_path: Path) -> str:
        """
        Detect the programming language based on file extension.

        Args:
            file_path: Path to the file

        Returns:
            Detected programming language
        """
        extension_map: dict[str, str] = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "react",
            ".tsx": "react",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".sql": "sql",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".md": "markdown",
        }
        return extension_map.get(file_path.suffix.lower(), "unknown")

    def _analyze_structure(self, content: str, extension: str) -> dict[str, object]:
        """
        Analyze the structure of the code.

        Args:
            content: File content
            extension: File extension

        Returns:
            Dictionary containing structure analysis
        """
        structure: dict[str, object] = {
            "functions": [],
            "classes": [],
            "imports": [],
            "comments": [],
            "complexity": 0,
        }
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if extension == ".py" and (
                stripped.startswith("def ") or stripped.startswith("async def ")
            ):
                name = stripped.split("(")[0].split()[-1]
                structure["functions"].append({"line": i, "name": name})
            elif (
                extension in {".js", ".ts", ".jsx", ".tsx"} and "function " in stripped
            ):
                name = stripped.split("function ")[1].split("(")[0]
                structure["functions"].append({"line": i, "name": name})
            else:
                pass
            if extension == ".py" and stripped.startswith("class "):
                name = stripped.split("class ")[1].split("(")[0].split(":")[0]
                structure["classes"].append({"line": i, "name": name})
            elif extension in {".js", ".ts", ".jsx", ".tsx"} and "class " in stripped:
                name = stripped.split("class ")[1].split()[0]
                structure["classes"].append({"line": i, "name": name})
            else:
                pass
            if extension == ".py" and (
                stripped.startswith("import ") or stripped.startswith("from ")
            ):
                structure["imports"].append({"line": i, "content": stripped})
            else:
                pass
            if stripped.startswith(("#", "//", "/*")):
                structure["comments"].append({"line": i, "content": stripped})
            else:
                pass
        else:
            pass
        structure["complexity"] = len(
            [
                ln
                for ln in lines
                if ln.strip() and (not ln.strip().startswith(("#", "//", "/*")))
            ]
        )
        return structure


class SecurityAnalyzer:
    """Analyzes code for security vulnerabilities."""

    def __init__(self) -> None:
        """
        Initialize SecurityAnalyzer.

        Attributes:
            logger: O3Logger instance for logging.
            client: OpenAI client instance.
            prompt_builder: PromptBuilder instance for building prompts.
        """
        self.logger = get_logger()
        self.client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt_builder = PromptBuilder()

    def analyze_security(self, file_info: dict[str, object]) -> list[dict[str, object]]:
        """
        Analyze code for security vulnerabilities.

        Args:
            file_info: Parsed file information

        Returns:
            List of security issues found
        """
        self.logger.log_info(f"Analyzing security for: {file_info['path']}")
        try:
            prompt = self.prompt_builder.build_analysis_prompt(
                input_data=None,
                analysis_data=file_info,
                system_prompt="You are a security expert analyzing code for vulnerabilities.",
                instructions=None,
            )
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1,
            )
            result = response.choices[0].message.content.strip()
            return json.loads(result) if result and result != "[]" else []
        except Exception as e:
            self.logger.log_error(
                f"Failed to analyze security for {file_info['path']}: {e}"
            )
            raise RuntimeError(
                f"Security analysis failed for {file_info['path']}"
            ) from e
        else:
            pass
        finally:
            pass


class QualityAnalyzer:
    """Analyzes code quality and best practices."""

    def __init__(self) -> None:
        """
        Initialize QualityAnalyzer.

        Attributes:
            logger: O3Logger instance for logging.
            client: OpenAI client instance.
            prompt_builder: PromptBuilder instance for building prompts.
        """
        self.logger = get_logger()
        self.client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt_builder = PromptBuilder()

    def analyze_quality(self, file_info: dict[str, object]) -> dict[str, object]:
        """
        Analyze code quality and adherence to best practices.

        Args:
            file_info: Parsed file information

        Returns:
            Dictionary containing quality analysis
        """
        self.logger.log_info(f"Analyzing quality for: {file_info['path']}")
        try:
            prompt = self.prompt_builder.build_analysis_prompt(
                input_data=None,
                analysis_data=file_info,
                system_prompt="You are a senior software engineer analyzing code quality.",
                instructions=None,
            )
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.2,
            )
            result = response.choices[0].message.content.strip()
            return json.loads(result) if result else {}
        except Exception as e:
            self.logger.log_error(
                f"Failed to analyze quality for {file_info['path']}: {e}"
            )
            raise RuntimeError(
                f"Quality analysis failed for {file_info['path']}"
            ) from e
        else:
            pass
        finally:
            pass


class PerformanceAnalyzer:
    """Analyzes code for performance issues."""

    def __init__(self) -> None:
        """
        Initialize PerformanceAnalyzer.

        Attributes:
            logger: O3Logger instance for logging.
            client: OpenAI client instance.
            prompt_builder: PromptBuilder instance for building prompts.
        """
        self.logger = get_logger()
        self.client: OpenAI = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt_builder = PromptBuilder()

    def analyze_performance(
        self, file_info: dict[str, object]
    ) -> list[dict[str, object]]:
        """
        Analyze code for performance issues.

        Args:
            file_info: Parsed file information

        Returns:
            List of performance issues found
        """
        self.logger.log_info(f"Analyzing performance for: {file_info['path']}")
        try:
            prompt = self.prompt_builder.build_analysis_prompt(
                input_data=None,
                analysis_data=file_info,
                system_prompt="You are a performance optimization expert.",
                instructions=None,
            )
            response = self.client.chat.completions.create(
                model="o3-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.2,
            )
            result = response.choices[0].message.content.strip()
            return json.loads(result) if result and result != "[]" else []
        except Exception as e:
            self.logger.log_error(
                f"Failed to analyze performance for {file_info['path']}: {e}"
            )
            raise RuntimeError(
                f"Performance analysis failed for {file_info['path']}"
            ) from e
        else:
            pass
        finally:
            pass


class CodeReviewer:
    """Main class for code review and analysis."""

    def __init__(self, config_path: str | None = None) -> None:
        """
        Initialize CodeReviewer.

        Args:
            config_path: Optional path to configuration file

        Attributes:
            config_manager: ConfigManager instance
            logger: O3Logger instance
            parser: CodeParser instance
            security_analyzer: SecurityAnalyzer instance
            quality_analyzer: QualityAnalyzer instance
            performance_analyzer: PerformanceAnalyzer instance
            directory_manager: DirectoryManager instance
            file_generator: FileGenerator instance
            output_formatter: OutputFormatter instance
        """
        self.logger = get_logger()
        self.config_manager = ConfigManager(config_path)
        self.parser = CodeParser()
        self.security_analyzer = SecurityAnalyzer()
        self.quality_analyzer = QualityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.directory_manager = DirectoryManager()
        self.file_generator = FileGenerator()
        self.output_formatter = OutputFormatter()
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Create necessary directories for reports and logs."""
        self.directory_manager.create_module_directories(
            module_name="code_reviewer", additional_dirs=["review_reports", "logs"]
        )

    def review_code(self, input_data: CodeReviewInput) -> CodeReviewOutput:
        """
        Perform comprehensive code review.

        Args:
            input_data: Code review input data

        Returns:
            Code review output with results
        """
        self.logger.log_info(f"Starting code review for: {input_data.file_path}")
        try:
            file_path = Path(input_data.file_path)
            if not file_path.exists():
                raise ValueError(f"File does not exist: {file_path}")
            else:
                pass
            file_info = self.parser.parse_file(file_path)
            security_issues: list[dict[str, object]] = []
            if input_data.include_security_analysis:
                security_issues = self.security_analyzer.analyze_security(file_info)
            else:
                pass
            quality_analysis: dict[str, object] = {}
            if input_data.include_quality_analysis:
                quality_analysis = self.quality_analyzer.analyze_quality(file_info)
            else:
                pass
            performance_issues: list[dict[str, object]] = []
            if input_data.include_performance_analysis:
                performance_issues = self.performance_analyzer.analyze_performance(
                    file_info
                )
            else:
                pass
            review = self._generate_comprehensive_review(
                file_info,
                security_issues,
                quality_analysis,
                performance_issues,
                input_data,
            )
            report_path = self._save_review_report(review, file_path)
            self.logger.log_info(f"Code review completed successfully: {report_path}")
            return CodeReviewOutput(
                success=True,
                file_path=str(file_path),
                security_issues=security_issues,
                quality_analysis=quality_analysis,
                performance_issues=performance_issues,
                review_summary=review["summary"],
                report_path=str(report_path),
                error_message=None,
            )
        except Exception as e:
            self.logger.log_error(f"Code review failed: {e}")
            return CodeReviewOutput(
                success=False,
                file_path="",
                security_issues=[],
                quality_analysis={},
                performance_issues=[],
                review_summary={},
                report_path="",
                error_message=str(e),
            )
        else:
            pass
        finally:
            pass

    def _generate_comprehensive_review(
        self,
        file_info: dict[str, object],
        security_issues: list[dict[str, object]],
        quality_analysis: dict[str, object],
        performance_issues: list[dict[str, object]],
        input_data: CodeReviewInput,
    ) -> dict[str, object]:
        """
        Generate comprehensive review summary.

        Args:
            file_info: Parsed file information
            security_issues: Found security issues
            quality_analysis: Quality analysis results
            performance_issues: Found performance issues
            input_data: Input data

        Returns:
            Comprehensive review data structure
        """
        security_score = max(0, 100 - len(security_issues) * 10)
        quality_score = quality_analysis.get("overall_score", 0)
        performance_score = max(0, 100 - len(performance_issues) * 5)
        overall_score = (security_score + quality_score + performance_score) // 3
        summary: dict[str, object] = {
            "file_info": {
                "name": file_info["name"],
                "language": file_info["language"],
                "size": file_info["size"],
                "lines": file_info["lines"],
            },
            "scores": {
                "overall": overall_score,
                "security": security_score,
                "quality": quality_score,
                "performance": performance_score,
            },
            "issues_summary": {
                "security_issues": len(security_issues),
                "quality_issues": len(quality_analysis.get("issues", [])),
                "performance_issues": len(performance_issues),
                "total_issues": len(security_issues)
                + len(quality_analysis.get("issues", []))
                + len(performance_issues),
            },
            "recommendations": self._generate_recommendations(
                security_issues, quality_analysis, performance_issues
            ),
            "priority_actions": self._identify_priority_actions(
                security_issues, quality_analysis, performance_issues
            ),
        }
        return {
            "file_info": file_info,
            "security_analysis": {"issues": security_issues, "score": security_score},
            "quality_analysis": quality_analysis,
            "performance_analysis": {
                "issues": performance_issues,
                "score": performance_score,
            },
            "summary": summary,
            "review_timestamp": self._get_current_timestamp(),
        }

    def _generate_recommendations(
        self,
        security_issues: list[dict[str, object]],
        quality_analysis: dict[str, object],
        performance_issues: list[dict[str, object]],
    ) -> list[str]:
        """
        Generate actionable recommendations.

        Args:
            security_issues: Security issues found
            quality_analysis: Quality analysis results
            performance_issues: Performance issues found

        Returns:
            List of recommendations
        """
        recs: list[str] = []
        if security_issues:
            if any(issue.get("severity") == "critical" for issue in security_issues):
                recs.append("🔴 CRITICAL: Address security vulnerabilities immediately")
            else:
                recs.append("🟡 Review and fix security issues identified")
        else:
            pass
        if quality_analysis.get("overall_score", 0) < 70:
            recs.append("📝 Improve code quality and readability")
        else:
            pass
        if quality_analysis.get("issues"):
            recs.append("🔧 Address code quality issues identified")
        else:
            pass
        if performance_issues:
            recs.append("⚡ Optimize performance bottlenecks identified")
        else:
            pass
        if not recs:
            recs.append("✅ Code quality is good, continue with current practices")
        else:
            pass
        return recs

    def _identify_priority_actions(
        self,
        security_issues: list[dict[str, object]],
        quality_analysis: dict[str, object],
        performance_issues: list[dict[str, object]],
    ) -> list[str]:
        """
        Identify priority actions to take.

        Args:
            security_issues: Security issues found
            quality_analysis: Quality analysis results
            performance_issues: Performance issues found

        Returns:
            List of priority actions
        """
        actions: list[str] = []
        critical_security = [
            i for i in security_issues if i.get("severity") == "critical"
        ]
        high_security = [i for i in security_issues if i.get("severity") == "high"]
        for issue in critical_security:
            actions.append(f"🔴 FIX CRITICAL: {issue.get('description', '')}")
        else:
            pass
        for issue in high_security:
            actions.append(f"🟠 FIX HIGH: {issue.get('description', '')}")
        else:
            pass
        for issue in quality_analysis.get("issues", [])[:3]:
            if issue.get("severity") == "high":
                actions.append(f"🔧 IMPROVE: {issue.get('description', '')}")
            else:
                pass
        else:
            pass
        for issue in performance_issues:
            if issue.get("severity") == "critical":
                actions.append(f"⚡ OPTIMIZE: {issue.get('description', '')}")
            else:
                pass
        else:
            pass
        return actions

    def _save_review_report(self, review: dict[str, object], file_path: Path) -> Path:
        """
        Save review report to file.

        Args:
            review: Review data
            file_path: Original file path

        Returns:
            Path to saved report
        """
        timestamp = self._get_current_timestamp().replace(":", "-").replace(" ", "_")
        filename = f"code_review_{file_path.stem}_{timestamp}.json"
        report_dir = Path("review_reports")
        self.directory_manager.ensure_directory_exists(report_dir)
        report_path = report_dir / filename
        content = self.output_formatter.to_json(review, pretty=True)
        self.file_generator.save_file(content, report_path)
        return report_path

    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp string.

        Returns:
            Current timestamp in 'YYYY-MM-DD HH:MM:SS' format
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    """
    CLI entry point for AI-powered code review.
    """
    logger = get_logger()
    parser = argparse.ArgumentParser(
        description="Perform AI-powered code review and analysis"
    )
    parser.add_argument("file_path", help="Path to the file to review")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument(
        "--no-security", action="store_true", help="Skip security analysis"
    )
    parser.add_argument(
        "--no-quality", action="store_true", help="Skip quality analysis"
    )
    parser.add_argument(
        "--no-performance", action="store_true", help="Skip performance analysis"
    )
    args = parser.parse_args()
    input_data = CodeReviewInput(
        file_path=args.file_path,
        include_security_analysis=not args.no_security,
        include_quality_analysis=not args.no_quality,
        include_performance_analysis=not args.no_performance,
        output_format="json",
        output_directory=None,
    )
    reviewer = CodeReviewer(args.config)
    result = reviewer.review_code(input_data)
    if result.success:
        logger.log_info("✅ Code review completed successfully!")
        logger.log_info(f"📁 File: {result.file_path}")
        scores = result.review_summary["scores"]
        logger.log_info(
            f"📊 Scores - Overall: {scores['overall']}/100 | Security: {scores['security']}/100 | Quality: {scores['quality']}/100 | Performance: {scores['performance']}/100"
        )
        logger.log_info(f"📄 Report saved to: {result.report_path}")
        issues = result.review_summary["issues_summary"]
        logger.log_info(
            f"🔍 Issues Found - Security: {issues['security_issues']}, Quality: {issues['quality_issues']}, Performance: {issues['performance_issues']}, Total: {issues['total_issues']}"
        )
        for action in result.review_summary.get("priority_actions", [])[:5]:
            logger.log_info(f"🎯 Priority Action: {action}")
        else:
            pass
        for rec in result.review_summary.get("recommendations", []):
            logger.log_info(f"💡 Recommendation: {rec}")
        else:
            pass
    else:
        logger.log_error(f"❌ Code review failed: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
else:
    pass
