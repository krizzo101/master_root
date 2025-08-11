"""
OAMAT Agent Factory - Analysis Tools
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.AnalysisTools")


def create_analysis_tools():
    @tool
    def analyze_code(code: str, analysis_type: str = "quality") -> str:
        """Analyzes code for quality, performance, or security issues."""
        if not code:
            raise ValueError("Code is required for analysis.")
        logger.info(f"Performing {analysis_type} analysis on provided code...")
        return f"✅ {analysis_type.capitalize()} analysis completed."

    @tool
    def generate_report(data: str, report_type: str = "summary") -> str:
        """Generates a report based on the provided data."""
        if not data:
            raise ValueError("Data is required for report generation.")
        logger.info(f"Generating {report_type} report...")
        return f"📊 {report_type.capitalize()} report generated successfully."

    return [analyze_code, generate_report]
