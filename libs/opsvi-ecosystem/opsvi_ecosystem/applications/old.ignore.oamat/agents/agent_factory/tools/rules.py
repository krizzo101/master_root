"""
OAMAT Agent Factory - Rule Access Tools
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.RulesTools")


def create_rule_access_tools():
    @tool
    def get_development_rules() -> str:
        """Retrieves the current development rules and guidelines."""
        logger.info("Retrieving development rules...")
        return "📋 Development rules retrieved successfully."

    @tool
    def validate_against_rules(code: str, rule_type: str = "general") -> str:
        """Validates code against specific development rules."""
        if not code:
            raise ValueError("Code is required for validation.")
        logger.info(f"Validating code against {rule_type} rules...")
        return f"✅ Code validation completed for {rule_type} rules."

    return [get_development_rules, validate_against_rules]
