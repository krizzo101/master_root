"""
Rules Integration for OAMAT Agents

This module provides functionality to embed development rules, coding standards,
security practices, and testing requirements into agent environments.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("OAMAT.RulesIntegration")


class RulesManager:
    """Manages development rules and their integration into agent environments"""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize rules manager with project root directory"""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.rules_dir = self.project_root / ".cursor" / "rules"
        self.cached_rules = {}
        self.rule_categories = {
            "development": [
                "800-development-best-practices",
                "801-typescript-development-standards",
                "803-python-dev-standards",
            ],
            "security": ["930-security-standards"],
            "testing": ["940-testing-standards"],
            "documentation": ["300-documentation-standards"],
            "performance": ["002-tool-usage-and-optimize"],
            "architecture": ["955-oamat-workflow-architecture"],
        }

    def load_rules_for_category(self, category: str) -> Dict[str, Any]:
        """Load all rules for a specific category"""
        if category not in self.rule_categories:
            logger.warning(f"Unknown rule category: {category}")
            return {}

        rules = {}
        for rule_name in self.rule_categories[category]:
            rule_content = self.load_rule(rule_name)
            if rule_content:
                rules[rule_name] = rule_content

        return rules

    def load_rule(self, rule_name: str) -> Optional[str]:
        """Load a specific rule by name"""
        if rule_name in self.cached_rules:
            return self.cached_rules[rule_name]

        # Try both .mdc and .md extensions
        for ext in [".mdc", ".md"]:
            rule_path = self.rules_dir / f"{rule_name}{ext}"
            if rule_path.exists():
                try:
                    with open(rule_path, encoding="utf-8") as f:
                        content = f.read()
                    self.cached_rules[rule_name] = content
                    logger.debug(f"Loaded rule: {rule_name}")
                    return content
                except Exception as e:
                    logger.error(f"Error loading rule {rule_name}: {e}")

        logger.warning(f"Rule not found: {rule_name}")
        return None

    def get_agent_rules(self, agent_role: str) -> Dict[str, str]:
        """Get relevant rules for a specific agent role"""
        role_rule_mapping = {
            "coder": ["development", "security"],
            "frontend_developer": ["development", "security", "performance"],
            "backend_developer": ["development", "security", "performance"],
            "database": ["development", "security", "performance"],
            "tester": ["testing", "development", "security"],
            "deployer": ["security", "development", "architecture"],
            "doc": ["documentation", "development"],
            "reviewer": ["development", "security", "testing"],
            "architect": ["architecture", "development", "security", "performance"],
            "technical_writer": ["documentation"],
            "researcher": ["performance"],
            "requirements_analyst": ["development", "documentation"],
            "utility": ["development"],
        }

        relevant_categories = role_rule_mapping.get(agent_role, ["development"])
        agent_rules = {}

        for category in relevant_categories:
            category_rules = self.load_rules_for_category(category)
            agent_rules.update(category_rules)

        return agent_rules

    def format_rules_for_prompt(self, rules: Dict[str, str]) -> str:
        """Format rules for inclusion in agent prompts"""
        if not rules:
            return ""

        formatted_rules = []
        formatted_rules.append("## 📋 DEVELOPMENT STANDARDS & BEST PRACTICES")
        formatted_rules.append(
            "You MUST follow these project standards in all generated code and recommendations:"
        )
        formatted_rules.append("")

        for rule_name, rule_content in rules.items():
            # Extract key sections from rule content
            rule_summary = self._extract_rule_summary(rule_content)
            formatted_rules.append(f"### {rule_name.upper()}")
            formatted_rules.append(rule_summary)
            formatted_rules.append("")

        formatted_rules.append("## 🚀 IMPLEMENTATION REQUIREMENTS")
        formatted_rules.append("- Apply security best practices in all code")
        formatted_rules.append("- Follow language-specific coding standards")
        formatted_rules.append("- Include comprehensive error handling")
        formatted_rules.append("- Implement proper logging and monitoring")
        formatted_rules.append("- Write production-ready, maintainable code")
        formatted_rules.append("- Include appropriate documentation")
        formatted_rules.append("")

        return "\n".join(formatted_rules)

    def _extract_rule_summary(self, rule_content: str) -> str:
        """Extract key points from rule content for prompt inclusion"""
        lines = rule_content.split("\n")
        summary_lines = []

        # Look for key patterns in the rule content
        in_key_section = False
        for line in lines:
            line = line.strip()

            # Key section indicators
            if any(
                keyword in line.lower()
                for keyword in [
                    "## core",
                    "## key",
                    "## mandatory",
                    "## critical",
                    "### requirements",
                    "### standards",
                    "### patterns",
                ]
            ):
                in_key_section = True
                continue

            # End of key section
            if line.startswith("#") and in_key_section:
                in_key_section = False

            # Collect important bullet points
            if line.startswith("- ") or line.startswith("* "):
                summary_lines.append(line)
            elif line.startswith("**") and line.endswith("**"):
                summary_lines.append(f"- {line}")

            # Limit summary length
            if len(summary_lines) >= 8:
                break

        return (
            "\n".join(summary_lines[:8])
            if summary_lines
            else "Follow established best practices"
        )

    def inject_rules_into_agent_spec(
        self, agent_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Inject relevant rules into an agent specification"""
        agent_role = agent_spec.get(
            "role", agent_spec.get("agent_role", agent_spec.get("name", ""))
        )

        if not agent_role:
            logger.warning("No agent role found in spec, cannot inject rules")
            return agent_spec

        # Get relevant rules for this agent
        agent_rules = self.get_agent_rules(agent_role)

        if agent_rules:
            # Format rules for prompt inclusion
            rules_section = self.format_rules_for_prompt(agent_rules)

            # Inject into capabilities
            if "capabilities" not in agent_spec:
                agent_spec["capabilities"] = []
            agent_spec["capabilities"].append(
                "Follows project development standards and best practices"
            )

            # Add rules context to the spec
            agent_spec["development_rules"] = {
                "rules_content": rules_section,
                "applicable_rules": list(agent_rules.keys()),
                "rule_categories": list(self.rule_categories.keys()),
            }

            logger.info(
                f"Injected {len(agent_rules)} rules into {agent_role} agent spec"
            )
        else:
            logger.warning(f"No rules found for agent role: {agent_role}")

        return agent_spec

    def create_rules_aware_prompt(self, base_prompt: str, agent_role: str) -> str:
        """Create a rules-aware prompt by injecting relevant standards"""
        agent_rules = self.get_agent_rules(agent_role)

        if not agent_rules:
            return base_prompt

        rules_section = self.format_rules_for_prompt(agent_rules)

        # Construct rules-aware prompt
        enhanced_prompt = f"""
{rules_section}

## 🎯 YOUR TASK
{base_prompt}

## ⚠️ CRITICAL REMINDERS
- ALWAYS apply the development standards listed above
- Generate production-ready, maintainable code
- Include proper error handling and security measures
- Follow language-specific best practices
- Document your implementation decisions
"""

        return enhanced_prompt

    def get_system_prompt(self, agent_role: str) -> str:
        """Generate a system prompt for an agent role with relevant rules embedded"""
        # Get relevant rules for this agent role
        agent_rules = self.get_agent_rules(agent_role)

        # Create a base system prompt for the role
        role_prompts = {
            "planner": "You are a planning specialist. Analyze requirements and create detailed project plans.",
            "coder": "You are a software engineer. Write clean, efficient, and well-documented code.",
            "reviewer": "You are a code reviewer. Analyze code quality, security, and best practices.",
            "tester": "You are a testing specialist. Design and implement comprehensive test strategies.",
            "deployer": "You are a deployment specialist. Configure and manage application deployments.",
            "doc": "You are a technical writer. Create clear, comprehensive documentation.",
            "architect": "You are a software architect. Design system architecture and technical specifications.",
            "researcher": "You are a research specialist. Conduct thorough research and analysis.",
            "analyst": "You are a requirements analyst. Analyze and document project requirements.",
            "frontend_developer": "You are a frontend developer. Create user interfaces and user experiences.",
            "backend_developer": "You are a backend developer. Build server-side logic and APIs.",
            "database": "You are a database specialist. Design and optimize database systems.",
            "utility": "You are a utility agent. Perform various support tasks as needed.",
        }

        base_prompt = role_prompts.get(
            agent_role, f"You are a {agent_role} specialist."
        )

        # If we have rules for this role, create a rules-aware prompt
        if agent_rules:
            return self.create_rules_aware_prompt(base_prompt, agent_role)
        else:
            return base_prompt

    def get_rules_retriever_tool(self):
        """Create a tool for retrieving project rules and standards"""
        from langchain_core.tools import tool

        @tool
        def get_project_rules(category: str = "development") -> str:
            """
            Retrieve project rules and standards for a specific category.

            Args:
                category: The rule category to retrieve (development, security, testing, etc.)

            Returns:
                Formatted rules content for the specified category
            """
            try:
                rules = self.load_rules_for_category(category)
                if not rules:
                    return f"No rules found for category: {category}"

                formatted_rules = self.format_rules_for_prompt(rules)
                return (
                    f"📋 Project rules for '{category}' category:\n\n{formatted_rules}"
                )
            except Exception as e:
                logger.error(f"Error retrieving rules for category {category}: {e}")
                return f"Error retrieving rules: {str(e)}"

        return get_project_rules


# Global rules manager instance
_rules_manager = None


def get_rules_manager() -> RulesManager:
    """Get global rules manager instance"""
    global _rules_manager
    if _rules_manager is None:
        _rules_manager = RulesManager()
    return _rules_manager


def inject_rules_into_spec(agent_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to inject rules into agent spec"""
    return get_rules_manager().inject_rules_into_agent_spec(agent_spec)


def create_rules_aware_prompt(base_prompt: str, agent_role: str) -> str:
    """Convenience function to create rules-aware prompt"""
    return get_rules_manager().create_rules_aware_prompt(base_prompt, agent_role)
