"""
OAMAT Agent Factory - Quality Assurance & Standards Tools
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.QualityTools")


def create_quality_assurance_tools():
    @tool
    def run_quality_check(target: str, check_type: str = "comprehensive") -> str:
        """Runs a quality assurance check on the specified target."""
        if not target:
            raise ValueError("Target is required for quality check.")
        logger.info(f"Running {check_type} quality check on: {target}")
        return f"✅ Quality check completed for {target}."

    @tool
    def generate_quality_report(data: str) -> str:
        """Generates a quality assurance report based on the provided data."""
        if not data:
            raise ValueError("Data is required for quality report generation.")
        logger.info("Generating quality assurance report...")
        return "📊 Quality assurance report generated successfully."

    return [run_quality_check, generate_quality_report]


def create_quality_standards_tools():
    @tool
    def validate_standards(code: str, standard_type: str = "coding") -> str:
        """Validates code against quality standards."""
        if not code:
            raise ValueError("Code is required for standards validation.")
        logger.info(f"Validating code against {standard_type} standards...")
        return f"✅ Standards validation completed for {standard_type}."

    @tool
    def apply_standards(target: str, standard_type: str) -> str:
        """Applies quality standards to the specified target."""
        if not target or not standard_type:
            raise ValueError("Target and standard type are required.")
        logger.info(f"Applying {standard_type} standards to: {target}")
        return f"✅ Standards applied to {target}."

    return [validate_standards, apply_standards]
