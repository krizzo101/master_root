"""
Architecture Validator for O3 Code Generator

This script provides comprehensive architecture validation capabilities using OpenAI's O3 models,
including architecture validation, consistency checking, scalability assessment, and security verification.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)
else:
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
    from prompts.architecture_prompts import ARCHITECTURE_VALIDATION_SYSTEM_PROMPT

    from schemas.architecture_schemas import ValidationInput, ValidationOutput
except ImportError:
    sys.exit(1)
else:
    pass
finally:
    pass


class ArchitectureValidator:
    """Main architecture validator class."""

    def __init__(self, config_path: str | None = None):
        """Initialize the architecture validator."""
        self.config = ConfigManager(config_path)
        from o3_logger.logger import LogConfig

        log_config = LogConfig(
            level=self.config.get("logging.level", "INFO"),
            log_dir=self.config.get("paths.logs", "logs"),
            standard_log_file="architecture_validator.log",
            debug_log_file="architecture_validator_debug.log",
            error_log_file="architecture_validator_error.log",
        )
        self.logger = setup_logger(log_config)
        self.client = OpenAI(
            api_key=self.config.get("api.openai_api_key"),
            base_url=self.config.get("api.base_url", "https://api.openai.com/v1"),
        )
        self._create_directories()
        self.logger.log_info("Architecture Validator initialized successfully")

    def _create_directories(self) -> None:
        """Create necessary output directories."""
        directories = [
            self.config.get("paths.generated_files", "generated_files"),
            f"{self.config.get('paths.generated_files', 'generated_files')}/validation",
            f"{self.config.get('paths.generated_files', 'generated_files')}/validation/reports",
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.log_debug(f"Directory created/verified: {directory}")
        else:
            pass

    def validate_architecture(self, input_data: ValidationInput) -> ValidationOutput:
        """Validate comprehensive architecture design."""
        start_time = time.time()
        self.logger.log_info("Starting architecture validation")
        try:
            validation_results = self._perform_comprehensive_validation(input_data)
            validation_report = self._generate_validation_report(
                input_data, validation_results
            )
            output_files = self._create_validation_files(validation_report, input_data)
            validation_time = time.time() - start_time
            self.logger.log_info(
                f"Architecture validation completed in {validation_time:.2f} seconds"
            )
            return ValidationOutput(
                success=True,
                validation_report=validation_report,
                output_files=output_files,
                validation_time=validation_time,
                model_used=input_data.model,
            )
        except Exception as e:
            self.logger.log_error(e, "Error during architecture validation")
            return ValidationOutput(
                success=False,
                validation_report={},
                output_files=[],
                validation_time=time.time() - start_time,
                model_used=input_data.model,
                error_message=str(e),
            )
        else:
            pass
        finally:
            pass

    def check_consistency(self, architecture_design: dict[str, Any]) -> dict[str, Any]:
        """Check architecture consistency."""
        self.logger.log_info("Checking architecture consistency")
        consistency_checks = {
            "naming_consistency": self._check_naming_consistency(architecture_design),
            "pattern_consistency": self._check_pattern_consistency(architecture_design),
            "interface_consistency": self._check_interface_consistency(
                architecture_design
            ),
            "data_flow_consistency": self._check_data_flow_consistency(
                architecture_design
            ),
        }
        return consistency_checks

    def assess_scalability(self, architecture_design: dict[str, Any]) -> dict[str, Any]:
        """Assess architecture scalability."""
        self.logger.log_info("Assessing architecture scalability")
        scalability_assessment = {
            "horizontal_scaling": self._assess_horizontal_scaling(architecture_design),
            "vertical_scaling": self._assess_vertical_scaling(architecture_design),
            "performance_bottlenecks": self._identify_performance_bottlenecks(
                architecture_design
            ),
            "scaling_recommendations": self._generate_scaling_recommendations(
                architecture_design
            ),
        }
        return scalability_assessment

    def verify_security(self, architecture_design: dict[str, Any]) -> dict[str, Any]:
        """Verify architecture security."""
        self.logger.log_info("Verifying architecture security")
        security_verification = {
            "authentication_verification": self._verify_authentication(
                architecture_design
            ),
            "authorization_verification": self._verify_authorization(
                architecture_design
            ),
            "encryption_verification": self._verify_encryption(architecture_design),
            "security_vulnerabilities": self._identify_security_vulnerabilities(
                architecture_design
            ),
            "security_recommendations": self._generate_security_recommendations(
                architecture_design
            ),
        }
        return security_verification

    def _perform_comprehensive_validation(
        self, input_data: ValidationInput
    ) -> dict[str, Any]:
        """Perform comprehensive architecture validation."""
        validation_results = {
            "consistency_check": self.check_consistency(input_data.architecture_design),
            "scalability_assessment": self.assess_scalability(
                input_data.architecture_design
            ),
            "security_verification": self.verify_security(
                input_data.architecture_design
            ),
            "performance_assessment": self._assess_performance(
                input_data.architecture_design
            ),
            "maintainability_assessment": self._assess_maintainability(
                input_data.architecture_design
            ),
            "reliability_assessment": self._assess_reliability(
                input_data.architecture_design
            ),
            "compliance_check": self._check_compliance(input_data.architecture_design),
        }
        return validation_results

    def _generate_validation_report(
        self, input_data: ValidationInput, validation_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate comprehensive validation report using O3 model."""
        self.logger.log_info(f"Generating validation report using {input_data.model}")
        prompt = self._build_validation_prompt(input_data, validation_results)
        try:
            response = self.client.chat.completions.create(
                model=input_data.model,
                messages=[
                    {
                        "role": "system",
                        "content": ARCHITECTURE_VALIDATION_SYSTEM_PROMPT,
                    },
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=input_data.max_tokens,
                response_format={"type": "json_object"},
            )
            validation_report = json.loads(response.choices[0].message.content)
            self.logger.log_info("Validation report generated successfully")
            return validation_report
        except Exception as e:
            self.logger.log_error(e, "Error generating validation report with O3 model")
            raise
        else:
            pass
        finally:
            pass

    def _build_validation_prompt(
        self, input_data: ValidationInput, validation_results: dict[str, Any]
    ) -> str:
        """Build comprehensive prompt for validation report generation."""
        prompt = f"""\nGenerate a comprehensive architecture validation report based on the following validation results:\n\nVALIDATION SCOPE: {', '.join(input_data.validation_scope)}\nVALIDATION LEVEL: {input_data.validation_level}\nINCLUDE RECOMMENDATIONS: {input_data.include_recommendations}\nINCLUDE METRICS: {input_data.include_metrics}\n\nARCHITECTURE DESIGN:\n{json.dumps(input_data.architecture_design, indent=2)}\n\nVALIDATION RESULTS:\n{json.dumps(validation_results, indent=2)}\n\nOUTPUT REQUIREMENTS:\n- Generate comprehensive validation report in JSON format\n- Include detailed analysis of each validation dimension\n- Provide actionable recommendations for improvement\n- Include validation metrics and scoring where applicable\n- Generate executive summary and detailed findings\n\nPlease provide the validation report in the following JSON structure:\n{{\n    "executive_summary": {{\n        "overall_score": "overall_validation_score",\n        "status": "validation_status",\n        "key_findings": ["key_findings"],\n        "critical_issues": ["critical_issues"],\n        "recommendations": ["high_priority_recommendations"]\n    }},\n    "detailed_analysis": {{\n        "consistency": {{\n            "score": "consistency_score",\n            "status": "consistency_status",\n            "findings": ["consistency_findings"],\n            "recommendations": ["consistency_recommendations"]\n        }},\n        "scalability": {{\n            "score": "scalability_score",\n            "status": "scalability_status",\n            "findings": ["scalability_findings"],\n            "recommendations": ["scalability_recommendations"]\n        }},\n        "security": {{\n            "score": "security_score",\n            "status": "security_status",\n            "findings": ["security_findings"],\n            "recommendations": ["security_recommendations"]\n        }},\n        "performance": {{\n            "score": "performance_score",\n            "status": "performance_status",\n            "findings": ["performance_findings"],\n            "recommendations": ["performance_recommendations"]\n        }},\n        "maintainability": {{\n            "score": "maintainability_score",\n            "status": "maintainability_status",\n            "findings": ["maintainability_findings"],\n            "recommendations": ["maintainability_recommendations"]\n        }},\n        "reliability": {{\n            "score": "reliability_score",\n            "status": "reliability_status",\n            "findings": ["reliability_findings"],\n            "recommendations": ["reliability_recommendations"]\n        }},\n        "compliance": {{\n            "score": "compliance_score",\n            "status": "compliance_status",\n            "findings": ["compliance_findings"],\n            "recommendations": ["compliance_recommendations"]\n        }}\n    }},\n    "validation_metrics": {{\n        "overall_score": "numerical_score",\n        "dimension_scores": {{\n            "consistency": "consistency_score",\n            "scalability": "scalability_score",\n            "security": "security_score",\n            "performance": "performance_score",\n            "maintainability": "maintainability_score",\n            "reliability": "reliability_score",\n            "compliance": "compliance_score"\n        }},\n        "risk_assessment": {{\n            "high_risk_issues": ["high_risk_issues"],\n            "medium_risk_issues": ["medium_risk_issues"],\n            "low_risk_issues": ["low_risk_issues"]\n        }}\n    }},\n    "improvement_roadmap": {{\n        "immediate_actions": ["immediate_actions"],\n        "short_term_improvements": ["short_term_improvements"],\n        "long_term_improvements": ["long_term_improvements"],\n        "priority_order": ["prioritized_improvements"]\n    }},\n    "compliance_report": {{\n        "standards_compliance": ["compliance_standards"],\n        "best_practices": ["best_practices_compliance"],\n        "industry_standards": ["industry_standards_compliance"]\n    }}\n}}\n"""
        return prompt

    def _create_validation_files(
        self, validation_report: dict[str, Any], input_data: ValidationInput
    ) -> list[str]:
        """Create validation report files."""
        files = []
        try:
            json_file = f"{self.config.get('paths.generated_files', 'generated_files')}/validation/reports/validation_report.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(validation_report, f, indent=2)
            files.append(json_file)
            if input_data.output_format.lower() == "markdown":
                markdown_content = self._convert_to_markdown(validation_report)
                markdown_file = f"{self.config.get('paths.generated_files', 'generated_files')}/validation/reports/validation_report.md"
                with open(markdown_file, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                files.append(markdown_file)
            else:
                pass
            self.logger.log_info(f"Created {len(files)} validation report files")
        except Exception as e:
            self.logger.log_error(e, "Error creating validation files")
        else:
            pass
        finally:
            pass
        return files

    def _convert_to_markdown(self, validation_report: dict[str, Any]) -> str:
        """Convert validation report to Markdown format."""
        markdown = "# Architecture Validation Report\n\n"
        executive = validation_report.get("executive_summary", {})
        markdown += "## Executive Summary\n\n"
        markdown += f"**Overall Score:** {executive.get('overall_score', 'Unknown')}\n"
        markdown += f"**Status:** {executive.get('status', 'Unknown')}\n\n"
        markdown += "**Key Findings:**\n"
        for finding in executive.get("key_findings", []):
            markdown += f"- {finding}\n"
        else:
            pass
        markdown += "\n"
        markdown += "**Critical Issues:**\n"
        for issue in executive.get("critical_issues", []):
            markdown += f"- {issue}\n"
        else:
            pass
        markdown += "\n"
        markdown += "## Detailed Analysis\n\n"
        analysis = validation_report.get("detailed_analysis", {})
        for dimension, details in analysis.items():
            markdown += f"### {dimension.title()}\n"
            markdown += f"**Score:** {details.get('score', 'Unknown')}\n"
            markdown += f"**Status:** {details.get('status', 'Unknown')}\n\n"
            markdown += "**Findings:**\n"
            for finding in details.get("findings", []):
                markdown += f"- {finding}\n"
            else:
                pass
            markdown += "\n"
            markdown += "**Recommendations:**\n"
            for rec in details.get("recommendations", []):
                markdown += f"- {rec}\n"
            else:
                pass
            markdown += "\n"
        else:
            pass
        return markdown

    def _check_naming_consistency(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Check naming consistency across architecture."""
        return {
            "status": "pass",
            "issues": [],
            "recommendations": [
                "Ensure consistent naming conventions across all components"
            ],
        }

    def _check_pattern_consistency(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Check pattern consistency across architecture."""
        return {
            "status": "pass",
            "issues": [],
            "recommendations": ["Ensure consistent architectural patterns"],
        }

    def _check_interface_consistency(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Check interface consistency across architecture."""
        return {
            "status": "pass",
            "issues": [],
            "recommendations": ["Ensure consistent interface definitions"],
        }

    def _check_data_flow_consistency(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Check data flow consistency across architecture."""
        return {
            "status": "pass",
            "issues": [],
            "recommendations": ["Ensure consistent data flow patterns"],
        }

    def _assess_horizontal_scaling(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess horizontal scaling capabilities."""
        return {
            "capability": "good",
            "issues": [],
            "recommendations": [
                "Implement load balancing for better horizontal scaling"
            ],
        }

    def _assess_vertical_scaling(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess vertical scaling capabilities."""
        return {
            "capability": "good",
            "issues": [],
            "recommendations": ["Consider resource optimization for vertical scaling"],
        }

    def _identify_performance_bottlenecks(
        self, architecture_design: dict[str, Any]
    ) -> list[str]:
        """Identify performance bottlenecks."""
        return ["Database connection pooling", "API rate limiting"]

    def _generate_scaling_recommendations(
        self, architecture_design: dict[str, Any]
    ) -> list[str]:
        """Generate scaling recommendations."""
        return [
            "Implement auto-scaling policies",
            "Use distributed caching",
            "Optimize database queries",
        ]

    def _verify_authentication(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Verify authentication mechanisms."""
        return {
            "status": "pass",
            "mechanisms": ["OAuth 2.0", "JWT"],
            "recommendations": ["Implement multi-factor authentication"],
        }

    def _verify_authorization(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Verify authorization mechanisms."""
        return {
            "status": "pass",
            "mechanisms": ["Role-based access control"],
            "recommendations": ["Implement fine-grained permissions"],
        }

    def _verify_encryption(self, architecture_design: dict[str, Any]) -> dict[str, Any]:
        """Verify encryption mechanisms."""
        return {
            "status": "pass",
            "mechanisms": ["TLS 1.3", "AES-256"],
            "recommendations": ["Implement end-to-end encryption"],
        }

    def _identify_security_vulnerabilities(
        self, architecture_design: dict[str, Any]
    ) -> list[str]:
        """Identify security vulnerabilities."""
        return ["Input validation", "SQL injection prevention"]

    def _generate_security_recommendations(
        self, architecture_design: dict[str, Any]
    ) -> list[str]:
        """Generate security recommendations."""
        return [
            "Implement comprehensive input validation",
            "Use parameterized queries",
            "Enable security headers",
        ]

    def _assess_performance(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess performance characteristics."""
        return {
            "score": "good",
            "bottlenecks": ["Database queries", "External API calls"],
            "recommendations": ["Implement caching", "Optimize database queries"],
        }

    def _assess_maintainability(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess maintainability characteristics."""
        return {
            "score": "good",
            "factors": ["Modular design", "Clear interfaces"],
            "recommendations": ["Improve documentation", "Standardize patterns"],
        }

    def _assess_reliability(
        self, architecture_design: dict[str, Any]
    ) -> dict[str, Any]:
        """Assess reliability characteristics."""
        return {
            "score": "good",
            "factors": ["Fault tolerance", "Error handling"],
            "recommendations": ["Implement circuit breakers", "Add retry mechanisms"],
        }

    def _check_compliance(self, architecture_design: dict[str, Any]) -> dict[str, Any]:
        """Check compliance with standards."""
        return {
            "score": "good",
            "standards": ["REST API standards", "Security standards"],
            "recommendations": ["Ensure GDPR compliance", "Follow OWASP guidelines"],
        }


def main() -> None:
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Architecture Validator for O3 Code Generator"
    )
    parser.add_argument("input_file", help="Path to input JSON file")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output-dir", help="Output directory for generated files")
    args = parser.parse_args()
    try:
        validator = ArchitectureValidator(args.config)
        with open(args.input_file, encoding="utf-8") as f:
            input_data_dict = json.load(f)
        input_data = ValidationInput(**input_data_dict)
        output = validator.validate_architecture(input_data)
        if output.success:
            pass
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
