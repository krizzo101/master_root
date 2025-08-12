"""
Rule Loader for OAMAT Agents

This module loads development standards, testing requirements, security best practices,
and other rules from the .cursor/rules directory to embed them into agent prompts
for better quality and compliance in generated code.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OAMAT.RuleLoader")


class RuleLoader:
    """Loads and manages development rules for agent prompt injection"""

    def __init__(self, rules_directory: str = ".cursor/rules"):
        """
        Initialize RuleLoader with rules directory

        Args:
            rules_directory: Path to directory containing rule files
        """
        # If rules directory is relative, make it relative to project root
        if not os.path.isabs(rules_directory):
            # Find project root by looking for .cursor directory
            current_path = Path.cwd()
            project_root = current_path
            while project_root != project_root.parent:
                if (project_root / ".cursor").exists():
                    break
                project_root = project_root.parent

            # If we found .cursor directory, use it; otherwise use current directory
            if (project_root / ".cursor").exists():
                rules_directory = str(project_root / rules_directory)

        self.rules_directory = Path(rules_directory)
        self.loaded_rules = {}
        self.rule_cache = {}

        # Load rules on initialization
        self._load_all_rules()

    def _load_all_rules(self):
        """Load all available rule files from the rules directory"""
        if not self.rules_directory.exists():
            logger.warning(f"Rules directory not found: {self.rules_directory}")
            return

        try:
            # Load both .md and .mdc files (Cursor rule files use .mdc extension)
            for pattern in ["*.md", "*.mdc"]:
                for rule_file in self.rules_directory.glob(pattern):
                    rule_name = rule_file.stem
                    rule_content = self._load_rule_file(rule_file)
                    if rule_content:
                        self.loaded_rules[rule_name] = rule_content
                        logger.debug(f"Loaded rule: {rule_name}")

            logger.info(f"Loaded {len(self.loaded_rules)} development rules")
        except Exception as e:
            logger.error(f"Error loading rules: {e}")

    def _load_rule_file(self, rule_file: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a single rule file"""
        try:
            with open(rule_file, encoding="utf-8") as f:
                content = f.read()

            # Extract metadata and content
            rule_data = {
                "name": rule_file.stem,
                "path": str(rule_file),
                "content": content,
                "size": len(content),
                "categories": self._extract_categories(content),
                "priority": self._extract_priority(content),
                "applicable_to": self._extract_applicable_agents(content),
            }

            return rule_data
        except Exception as e:
            logger.error(f"Failed to load rule file {rule_file}: {e}")
            return None

    def _extract_categories(self, content: str) -> List[str]:
        """Extract rule categories from content"""
        categories = []

        # Look for common development categories
        content_lower = content.lower()
        if "typescript" in content_lower or "react" in content_lower:
            categories.append("frontend")
        if (
            "python" in content_lower
            or "flask" in content_lower
            or "fastapi" in content_lower
        ):
            categories.append("backend")
        if (
            "testing" in content_lower
            or "pytest" in content_lower
            or "jest" in content_lower
        ):
            categories.append("testing")
        if "security" in content_lower or "owasp" in content_lower:
            categories.append("security")
        if "docker" in content_lower or "deployment" in content_lower:
            categories.append("deployment")
        if "documentation" in content_lower or "readme" in content_lower:
            categories.append("documentation")

        return categories

    def _extract_priority(self, content: str) -> int:
        """Extract priority from rule content (1=highest, 10=lowest)"""
        # Check for priority indicators
        content_lower = content.lower()
        if "critical" in content_lower or "mandatory" in content_lower:
            return 1
        elif "important" in content_lower or "required" in content_lower:
            return 2
        elif "recommended" in content_lower:
            return 3
        else:
            return 5  # Default priority

    def _extract_applicable_agents(self, content: str) -> List[str]:
        """Extract which agent roles this rule applies to"""
        applicable = []
        content_lower = content.lower()

        # Map content to agent roles
        agent_keywords = {
            "coder": ["coding", "development", "implementation", "programming"],
            "frontend_developer": [
                "frontend",
                "react",
                "typescript",
                "css",
                "html",
                "ui",
            ],
            "backend_developer": ["backend", "api", "server", "database", "python"],
            "tester": ["testing", "pytest", "jest", "qa", "quality"],
            "reviewer": ["review", "code review", "quality", "standards"],
            "deployer": ["deployment", "docker", "ci/cd", "infrastructure"],
            "doc": ["documentation", "readme", "api docs"],
        }

        for agent_role, keywords in agent_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                applicable.append(agent_role)

        # If no specific agents identified, apply to all
        if not applicable:
            applicable = ["all"]

        return applicable

    def get_rules_for_agent(
        self, agent_role: str, categories: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get applicable rules for a specific agent role

        Args:
            agent_role: The agent role (e.g., 'coder', 'tester', 'reviewer')
            categories: Optional list of categories to filter by

        Returns:
            List of applicable rules sorted by priority
        """
        applicable_rules = []

        for rule_name, rule_data in self.loaded_rules.items():
            # Check if rule applies to this agent
            if (
                agent_role in rule_data["applicable_to"]
                or "all" in rule_data["applicable_to"]
            ):
                # Filter by categories if specified
                if categories:
                    if any(cat in rule_data["categories"] for cat in categories):
                        applicable_rules.append(rule_data)
                else:
                    applicable_rules.append(rule_data)

        # Sort by priority (lower number = higher priority)
        applicable_rules.sort(key=lambda x: x["priority"])

        return applicable_rules

    def format_rules_for_prompt(
        self,
        agent_role: str,
        categories: List[str] = None,
        max_rules: int = 5,
        max_chars: int = 2000,
    ) -> str:
        """
        Format rules for injection into agent prompts

        Args:
            agent_role: The agent role
            categories: Optional categories to filter by
            max_rules: Maximum number of rules to include
            max_chars: Maximum total characters for all rules

        Returns:
            Formatted rules string for prompt injection
        """
        rules = self.get_rules_for_agent(agent_role, categories)

        if not rules:
            return ""

        # Limit number of rules
        rules = rules[:max_rules]

        formatted_rules = "\n**DEVELOPMENT STANDARDS & REQUIREMENTS:**\n"
        formatted_rules += (
            "The following standards MUST be followed in your implementation:\n\n"
        )

        current_chars = len(formatted_rules)

        for rule in rules:
            # Extract key sections from rule content
            rule_summary = self._extract_rule_summary(rule["content"])

            rule_text = f"• **{rule['name'].replace('-', ' ').title()}**:\n"
            rule_text += f"  {rule_summary}\n\n"

            # Check if adding this rule would exceed character limit
            if current_chars + len(rule_text) > max_chars:
                break

            formatted_rules += rule_text
            current_chars += len(rule_text)

        formatted_rules += "⚠️ **COMPLIANCE REQUIRED**: All generated code must comply with these standards.\n"

        return formatted_rules

    def _extract_rule_summary(self, content: str) -> str:
        """Extract a summary of key points from rule content"""
        lines = content.split("\n")
        summary_lines = []

        # Look for bullet points, numbered lists, or key sections
        for line in lines[:20]:  # Only check first 20 lines
            line = line.strip()
            if (
                line.startswith("- ")
                or line.startswith("* ")
                or line.startswith("• ")
                or line.startswith(("1.", "2.", "3.", "4.", "5."))
            ):
                summary_lines.append(line[2:].strip())
            elif line.startswith("#") and len(line) < 100:
                # Include headers
                summary_lines.append(line.replace("#", "").strip())

        # If no structured content found, take first few sentences
        if not summary_lines:
            sentences = content.replace("\n", " ").split(".")[:3]
            summary_lines = [s.strip() for s in sentences if s.strip()]

        # Limit total length
        summary = ". ".join(summary_lines[:5])
        if len(summary) > 300:
            summary = summary[:297] + "..."

        return summary

    def get_rule_categories(self) -> List[str]:
        """Get all available rule categories"""
        categories = set()
        for rule_data in self.loaded_rules.values():
            categories.update(rule_data["categories"])
        return sorted(list(categories))

    def get_available_rules(self) -> List[str]:
        """Get list of all available rule names"""
        return list(self.loaded_rules.keys())

    def refresh_rules(self):
        """Reload all rules from disk"""
        self.loaded_rules = {}
        self.rule_cache = {}
        self._load_all_rules()


# Global rule loader instance
rule_loader = RuleLoader()


def get_rules_for_agent(agent_role: str, categories: List[str] = None) -> str:
    """
    Convenience function to get formatted rules for an agent

    Args:
        agent_role: The agent role
        categories: Optional categories to filter by

    Returns:
        Formatted rules string for prompt injection
    """
    return rule_loader.format_rules_for_prompt(agent_role, categories)


def get_security_rules() -> str:
    """Get security-specific rules for any agent"""
    return rule_loader.format_rules_for_prompt("all", ["security"], max_rules=3)


def get_testing_rules() -> str:
    """Get testing-specific rules for any agent"""
    return rule_loader.format_rules_for_prompt("all", ["testing"], max_rules=3)
