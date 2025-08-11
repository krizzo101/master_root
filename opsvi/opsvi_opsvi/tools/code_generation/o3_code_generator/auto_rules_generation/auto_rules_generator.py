"""
Auto Rules Generator - Main Orchestrator

Orchestrates the complete auto rules generation pipeline:
Codebase Scan → AST Analysis → Pattern Extraction → Rule Generation → Validation → Application
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
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

from .ast_analyzer import ASTAnalyzer, FileAnalysis
from .codebase_scanner import CodebaseMetadata, CodebaseScanner
from .pattern_extractor import PatternAnalysis, PatternExtractor
from .rule_generator_engine import RuleGenerationResult, RuleGeneratorEngine
from .rule_validator import RuleValidator, ValidationReport


@dataclass
class AutoRulesGenerationResult:
    """Complete result of auto rules generation process."""

    success: bool
    generated_rules: List[Any]
    validation_report: Optional[ValidationReport]
    pattern_analysis: Optional[PatternAnalysis]
    codebase_metadata: Optional[CodebaseMetadata]
    output_files: List[Path]
    summary: str
    recommendations: List[str]
    execution_time: float


class AutoRulesGenerator:
    """
    Main orchestrator for the auto rules generation system.

    Coordinates all components to generate comprehensive, current rules
    based on actual codebase patterns.
    """

    def __init__(
        self, base_path: Optional[Path] = None, output_dir: Optional[Path] = None
    ):
        """Initialize the auto rules generator."""
        # Call setup_logger before any get_logger
        setup_logger(LogConfig())
        self.logger = get_logger()

        self.base_path = base_path or Path("src/applications/oamat_sd")
        self.output_dir = output_dir or Path(
            "src/tools/code_generation/o3_code_generator/auto_rules_generation/output"
        )

        # Initialize components
        self.directory_manager = DirectoryManager()
        self.file_generator = FileGenerator(base_output_dir=str(self.output_dir))
        self.output_formatter = OutputFormatter()

        # Initialize analysis components
        self.codebase_scanner = CodebaseScanner(self.base_path)
        self.ast_analyzer = ASTAnalyzer()
        self.pattern_extractor = PatternExtractor()
        self.rule_generator_engine = RuleGeneratorEngine()
        self.rule_validator = RuleValidator()

        # Ensure output directory exists
        self.directory_manager.ensure_directory_exists(self.output_dir)

        self.logger.log_info(
            f"Initialized AutoRulesGenerator for path: {self.base_path}"
        )

    def generate_rules(self, validate_only: bool = False) -> AutoRulesGenerationResult:
        """
        Generate comprehensive rules based on codebase analysis.

        Args:
            validate_only: If True, only validate existing rules without generating new ones

        Returns:
            AutoRulesGenerationResult: Complete result of the generation process
        """
        start_time = datetime.now()
        self.logger.log_info("Starting auto rules generation process")

        try:
            # Phase 1: Codebase Scanning
            self.logger.log_info("Phase 1: Scanning codebase...")
            codebase_metadata = self.codebase_scanner.scan_codebase()

            # Phase 2: AST Analysis
            self.logger.log_info("Phase 2: Performing AST analysis...")
            file_analyses = self._perform_ast_analysis(codebase_metadata)

            # Phase 3: Pattern Extraction
            self.logger.log_info("Phase 3: Extracting patterns...")
            pattern_analysis = self.pattern_extractor.extract_patterns(file_analyses)

            # Phase 4: Rule Generation
            self.logger.log_info("Phase 4: Generating rules...")
            rule_result = self.rule_generator_engine.generate_rules(pattern_analysis)

            # Phase 5: Rule Validation
            self.logger.log_info("Phase 5: Validating rules...")
            validation_report = self.rule_validator.validate_rules(
                rule_result, self.base_path
            )

            # Phase 6: Output Generation
            self.logger.log_info("Phase 6: Generating output files...")
            output_files = self._generate_output_files(
                rule_result, validation_report, pattern_analysis, codebase_metadata
            )

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Generate summary and recommendations
            summary = self._generate_summary(
                rule_result, validation_report, execution_time
            )
            recommendations = self._generate_recommendations(
                validation_report, pattern_analysis
            )

            self.logger.log_info(
                f"Auto rules generation completed in {execution_time:.2f} seconds"
            )

            return AutoRulesGenerationResult(
                success=True,
                generated_rules=rule_result.generated_rules,
                validation_report=validation_report,
                pattern_analysis=pattern_analysis,
                codebase_metadata=codebase_metadata,
                output_files=output_files,
                summary=summary,
                recommendations=recommendations,
                execution_time=execution_time,
            )

        except Exception as e:
            self.logger.log_error(f"Auto rules generation failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()

            return AutoRulesGenerationResult(
                success=False,
                generated_rules=[],
                validation_report=None,
                pattern_analysis=None,
                codebase_metadata=None,
                output_files=[],
                summary=f"Generation failed: {str(e)}",
                recommendations=["Review error logs and fix issues"],
                execution_time=execution_time,
            )

    def _perform_ast_analysis(
        self, codebase_metadata: CodebaseMetadata
    ) -> List[FileAnalysis]:
        """Perform AST analysis on all discovered files."""
        file_analyses = []

        # Get all Python files from the codebase metadata
        all_files = []
        for category_files in codebase_metadata.categories.values():
            all_files.extend(category_files)

        self.logger.log_info(f"Performing AST analysis on {len(all_files)} files")

        for file_metadata in all_files:
            try:
                analysis = self.ast_analyzer.analyze_file(file_metadata.path)
                file_analyses.append(analysis)
            except Exception as e:
                self.logger.log_warning(f"Failed to analyze {file_metadata.path}: {e}")

        self.logger.log_info(f"AST analysis completed for {len(file_analyses)} files")
        return file_analyses

    def _generate_output_files(
        self,
        rule_result: RuleGenerationResult,
        validation_report: ValidationReport,
        pattern_analysis: PatternAnalysis,
        codebase_metadata: CodebaseMetadata,
    ) -> List[Path]:
        """Generate output files with the analysis results."""
        output_files = []

        # Generate comprehensive report
        report_data = {
            "generation_timestamp": datetime.now().isoformat(),
            "codebase_summary": {
                "total_files": codebase_metadata.total_files,
                "total_lines": codebase_metadata.total_lines,
                "categories": {
                    k: len(v) for k, v in codebase_metadata.categories.items()
                },
            },
            "pattern_analysis": {
                "total_violations": len(pattern_analysis.violations),
                "consistency_scores": pattern_analysis.consistency_scores,
                "recommendations": pattern_analysis.recommendations,
            },
            "rule_generation": {
                "total_rules": len(rule_result.generated_rules),
                "rule_hierarchy": {
                    k: len(v) for k, v in rule_result.rule_hierarchy.items()
                },
                "conflict_resolutions": rule_result.conflict_resolutions,
                "confidence_scores": rule_result.confidence_scores,
            },
            "validation": {
                "total_rules": validation_report.total_rules,
                "valid_rules": validation_report.valid_rules,
                "invalid_rules": validation_report.invalid_rules,
                "average_confidence": validation_report.average_confidence,
                "safety_score": validation_report.safety_score,
                "overall_issues": validation_report.overall_issues,
                "overall_warnings": validation_report.overall_warnings,
                "rollback_recommendations": validation_report.rollback_recommendations,
            },
        }

        # Save comprehensive report
        report_path = self.output_dir / "auto_rules_generation_report.json"
        self.file_generator.save_file(
            report_path, self.output_formatter.to_json(report_data, pretty=True)
        )
        output_files.append(report_path)

        # Generate updated project_rules.md
        project_rules_path = self._generate_updated_project_rules(
            rule_result, validation_report
        )
        if project_rules_path:
            output_files.append(project_rules_path)

        # Generate updated universal_rules.md
        universal_rules_path = self._generate_updated_universal_rules(
            rule_result, validation_report
        )
        if universal_rules_path:
            output_files.append(universal_rules_path)

        # Generate detailed validation report
        validation_report_path = self.output_dir / "validation_report.json"
        validation_data = {
            "validation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_rules": validation_report.total_rules,
                "valid_rules": validation_report.valid_rules,
                "invalid_rules": validation_report.invalid_rules,
                "average_confidence": validation_report.average_confidence,
                "safety_score": validation_report.safety_score,
            },
            "detailed_results": {
                rule_name: {
                    "is_valid": result.is_valid,
                    "confidence_score": result.confidence_score,
                    "issues": result.issues,
                    "warnings": result.warnings,
                    "recommendations": result.recommendations,
                    "test_results": result.test_results,
                }
                for rule_name, result in validation_report.validation_results.items()
            },
            "overall_issues": validation_report.overall_issues,
            "overall_warnings": validation_report.overall_warnings,
            "rollback_recommendations": validation_report.rollback_recommendations,
        }

        self.file_generator.save_file(
            validation_report_path,
            self.output_formatter.to_json(validation_data, indent=2),
        )
        output_files.append(validation_report_path)

        return output_files

    def _generate_updated_project_rules(
        self, rule_result: RuleGenerationResult, validation_report: ValidationReport
    ) -> Optional[Path]:
        """Generate updated project_rules.md with new rules."""
        try:
            # Read existing project rules
            project_rules_path = Path(
                "src/tools/code_generation/o3_code_generator/project_rules.md"
            )
            if not project_rules_path.exists():
                self.logger.log_warning("project_rules.md not found, skipping update")
                return None

            with open(project_rules_path, encoding="utf-8") as f:
                existing_content = f.read()

            # Generate new rules content
            new_rules_content = self._format_rules_for_markdown(
                rule_result, validation_report
            )

            # Create updated content
            updated_content = f"""# PROJECT RULES - AUTO-GENERATED

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Auto-Generated**: Yes
**Total Rules**: {len(rule_result.generated_rules)}
**Valid Rules**: {validation_report.valid_rules}
**Safety Score**: {validation_report.safety_score:.2f}

## EXISTING RULES

{existing_content}

## AUTO-GENERATED RULES

{new_rules_content}

## VALIDATION SUMMARY

- **Total Rules**: {validation_report.total_rules}
- **Valid Rules**: {validation_report.valid_rules}
- **Invalid Rules**: {validation_report.invalid_rules}
- **Average Confidence**: {validation_report.average_confidence:.2f}
- **Safety Score**: {validation_report.safety_score:.2f}

### Issues Found
{chr(10).join(f"- {issue}" for issue in validation_report.overall_issues)}

### Warnings
{chr(10).join(f"- {warning}" for warning in validation_report.overall_warnings)}

### Rollback Recommendations
{chr(10).join(f"- {rec}" for rec in validation_report.rollback_recommendations)}
"""

            # Save updated project rules
            updated_rules_path = self.output_dir / "updated_project_rules.md"
            self.file_generator.save_file(updated_rules_path, updated_content)

            return updated_rules_path

        except Exception as e:
            self.logger.log_error(f"Failed to generate updated project rules: {e}")
            return None

    def _generate_updated_universal_rules(
        self, rule_result: RuleGenerationResult, validation_report: ValidationReport
    ) -> Optional[Path]:
        """Generate updated universal_rules.md with new rules."""
        try:
            # Read existing universal rules
            universal_rules_path = Path(
                "src/tools/code_generation/o3_code_generator/universal_rules.md"
            )
            if not universal_rules_path.exists():
                self.logger.log_warning("universal_rules.md not found, skipping update")
                return None

            with open(universal_rules_path, encoding="utf-8") as f:
                existing_content = f.read()

            # Generate new universal rules content
            universal_rules = [
                rule
                for rule in rule_result.generated_rules
                if rule.rule_type in ["important", "optional"]
            ]
            new_rules_content = self._format_rules_for_markdown(
                RuleGenerationResult(
                    generated_rules=universal_rules,
                    rule_hierarchy=rule_result.rule_hierarchy,
                    conflict_resolutions=rule_result.conflict_resolutions,
                    confidence_scores=rule_result.confidence_scores,
                    recommendations=rule_result.recommendations,
                ),
                validation_report,
            )

            # Create updated content
            updated_content = f"""# UNIVERSAL RULES - AUTO-GENERATED

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Auto-Generated**: Yes
**Total Rules**: {len(universal_rules)}
**Valid Rules**: {validation_report.valid_rules}
**Safety Score**: {validation_report.safety_score:.2f}

## EXISTING UNIVERSAL RULES

{existing_content}

## AUTO-GENERATED UNIVERSAL RULES

{new_rules_content}

## VALIDATION SUMMARY

- **Total Rules**: {len(universal_rules)}
- **Valid Rules**: {validation_report.valid_rules}
- **Invalid Rules**: {validation_report.invalid_rules}
- **Average Confidence**: {validation_report.average_confidence:.2f}
- **Safety Score**: {validation_report.safety_score:.2f}
"""

            # Save updated universal rules
            updated_rules_path = self.output_dir / "updated_universal_rules.md"
            self.file_generator.save_file(updated_rules_path, updated_content)

            return updated_rules_path

        except Exception as e:
            self.logger.log_error(f"Failed to generate updated universal rules: {e}")
            return None

    def _format_rules_for_markdown(
        self, rule_result: RuleGenerationResult, validation_report: ValidationReport
    ) -> str:
        """Format rules for markdown output."""
        markdown_content = []

        # Group rules by type
        for rule_type in ["critical", "important", "optional"]:
            rules_of_type = [
                rule
                for rule in rule_result.generated_rules
                if rule.rule_type == rule_type
            ]

            if not rules_of_type:
                continue

            markdown_content.append(f"### {rule_type.upper()} RULES")
            markdown_content.append("")

            for i, rule in enumerate(rules_of_type, 1):
                validation_result = validation_report.validation_results.get(
                    rule.rule_name
                )
                is_valid = validation_result.is_valid if validation_result else False
                confidence = rule.confidence_score

                # Rule header
                status_icon = "✅" if is_valid else "❌"
                markdown_content.append(f"#### {i}. {rule.rule_name} {status_icon}")
                markdown_content.append("")

                # Rule text
                markdown_content.append(f"**Rule**: {rule.rule_text}")
                markdown_content.append("")

                # Metadata
                markdown_content.append(f"**Confidence**: {confidence:.2f}")
                markdown_content.append(f"**Pattern Basis**: {rule.pattern_basis}")
                markdown_content.append("")

                # Examples
                if rule.examples:
                    markdown_content.append("**Examples**:")
                    for example in rule.examples:
                        markdown_content.append(f"- {example}")
                    markdown_content.append("")

                # Rationale
                markdown_content.append(f"**Rationale**: {rule.rationale}")
                markdown_content.append("")

                # Validation issues
                if validation_result and validation_result.issues:
                    markdown_content.append("**Issues**:")
                    for issue in validation_result.issues:
                        markdown_content.append(f"- {issue}")
                    markdown_content.append("")

                # Recommendations
                if validation_result and validation_result.recommendations:
                    markdown_content.append("**Recommendations**:")
                    for rec in validation_result.recommendations:
                        markdown_content.append(f"- {rec}")
                    markdown_content.append("")

                markdown_content.append("---")
                markdown_content.append("")

        return "\n".join(markdown_content)

    def _generate_summary(
        self,
        rule_result: RuleGenerationResult,
        validation_report: ValidationReport,
        execution_time: float,
    ) -> str:
        """Generate a summary of the generation process."""
        return f"""
Auto Rules Generation Summary
============================

Execution Time: {execution_time:.2f} seconds
Total Rules Generated: {len(rule_result.generated_rules)}
Valid Rules: {validation_report.valid_rules}
Invalid Rules: {validation_report.invalid_rules}
Average Confidence: {validation_report.average_confidence:.2f}
Safety Score: {validation_report.safety_score:.2f}

Rule Distribution:
- Critical: {len(rule_result.rule_hierarchy.get('critical', []))}
- Important: {len(rule_result.rule_hierarchy.get('important', []))}
- Optional: {len(rule_result.rule_hierarchy.get('optional', []))}

Issues Found: {len(validation_report.overall_issues)}
Warnings: {len(validation_report.overall_warnings)}
Rollback Recommendations: {len(validation_report.rollback_recommendations)}
"""

    def _generate_recommendations(
        self, validation_report: ValidationReport, pattern_analysis: PatternAnalysis
    ) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        # Add validation-based recommendations
        recommendations.extend(validation_report.rollback_recommendations)

        # Add pattern-based recommendations
        recommendations.extend(pattern_analysis.recommendations)

        # Add general recommendations
        if validation_report.invalid_rules > 0:
            recommendations.append(
                f"Review and fix {validation_report.invalid_rules} invalid rules"
            )

        if validation_report.average_confidence < 0.7:
            recommendations.append(
                "Improve rule confidence by gathering more pattern data"
            )

        if validation_report.safety_score < 0.8:
            recommendations.append("Address safety concerns before implementing rules")

        return recommendations
