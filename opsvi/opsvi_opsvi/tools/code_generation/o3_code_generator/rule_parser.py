"""Dynamic rule parser for project compliance checking.

This module provides functionality to parse machine-readable rule definitions
from project_rules.md and convert them into structured data for the AlignmentScanner.
"""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Optional

import yaml

from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)


@dataclass
class Rule:
    """Represents a single compliance rule."""

    id: str
    type: str  # 'regex', 'ast', 'import', 'structure'
    pattern: Optional[str] = None  # For regex rules
    check: Optional[str] = None  # For AST rules
    message: str = ""
    severity: str = "error"  # 'error', 'warning', 'info'
    category: str = "general"


@dataclass
class BrokenImport:
    """Represents a broken import pattern and its fix."""

    pattern: str
    replacement: str
    message: str


@dataclass
class RuleConfig:
    """Complete rule configuration parsed from project_rules.md."""

    rules: List[Rule]
    broken_imports: List[BrokenImport]
    ignore_dirs: List[str]


class RuleParser:
    """Parses dynamic rules from project_rules.md with YAML frontmatter."""

    def __init__(self, rules_file: Optional[Path] = None) -> None:
        """Initialize the rule parser.

        Args:
            rules_file: Path to project_rules.md file. If None, uses default location.
        """
        try:
            self.logger = get_logger()
        except RuntimeError:
            setup_logger(LogConfig())
            self.logger = get_logger()

        self.rules_file = rules_file or Path(
            "src/tools/code_generation/o3_code_generator/docs/project_rules.md"
        )
        self.logger.log_info(f"Initialized RuleParser for file: {self.rules_file}")

    def parse_rules(self) -> RuleConfig:
        """Parse rules from project_rules.md with YAML frontmatter.

        Returns:
            RuleConfig containing all parsed rules and configuration.

        Raises:
            FileNotFoundError: If rules file doesn't exist.
            yaml.YAMLError: If YAML frontmatter is invalid.
        """
        if not self.rules_file.exists():
            raise FileNotFoundError(f"Rules file not found: {self.rules_file}")

        content = self.rules_file.read_text(encoding="utf-8")

        # Extract YAML frontmatter
        yaml_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not yaml_match:
            raise ValueError("No YAML frontmatter found in rules file")

        yaml_content = yaml_match.group(1)

        try:
            config_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in rules file: {e}")

        self.logger.log_info("Successfully parsed YAML frontmatter from rules file")

        # Parse rules
        rules = []
        for rule_data in config_data.get("rules", []):
            rule = Rule(
                id=rule_data["id"],
                type=rule_data["type"],
                pattern=rule_data.get("pattern"),
                check=rule_data.get("check"),
                message=rule_data.get("message", ""),
                severity=rule_data.get("severity", "error"),
                category=rule_data.get("category", "general"),
            )
            rules.append(rule)

        # Parse broken imports
        broken_imports = []
        for import_data in config_data.get("broken_imports", []):
            broken_import = BrokenImport(
                pattern=import_data["pattern"],
                replacement=import_data["replacement"],
                message=import_data.get("message", ""),
            )
            broken_imports.append(broken_import)

        # Parse ignore directories
        ignore_dirs = config_data.get("ignore_dirs", [])

        rule_config = RuleConfig(
            rules=rules, broken_imports=broken_imports, ignore_dirs=ignore_dirs
        )

        self.logger.log_info(
            f"Parsed {len(rules)} rules, {len(broken_imports)} broken imports, {len(ignore_dirs)} ignore dirs"
        )
        return rule_config

    def get_rules_by_type(self, rule_config: RuleConfig, rule_type: str) -> List[Rule]:
        """Get all rules of a specific type.

        Args:
            rule_config: Parsed rule configuration.
            rule_type: Type of rules to retrieve ('regex', 'ast', etc.).

        Returns:
            List of rules matching the specified type.
        """
        return [rule for rule in rule_config.rules if rule.type == rule_type]

    def get_rules_by_category(
        self, rule_config: RuleConfig, category: str
    ) -> List[Rule]:
        """Get all rules of a specific category.

        Args:
            rule_config: Parsed rule configuration.
            category: Category of rules to retrieve ('imports', 'logging', etc.).

        Returns:
            List of rules matching the specified category.
        """
        return [rule for rule in rule_config.rules if rule.category == category]

    def validate_rule_config(self, rule_config: RuleConfig) -> List[str]:
        """Validate the parsed rule configuration.

        Args:
            rule_config: Rule configuration to validate.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors = []

        # Check for duplicate rule IDs
        rule_ids = [rule.id for rule in rule_config.rules]
        duplicates = set([x for x in rule_ids if rule_ids.count(x) > 1])
        if duplicates:
            errors.append(f"Duplicate rule IDs found: {duplicates}")

        # Validate rule types
        valid_types = {"regex", "ast", "import", "structure"}
        for rule in rule_config.rules:
            if rule.type not in valid_types:
                errors.append(
                    f"Invalid rule type '{rule.type}' for rule '{rule.id}'. Valid types: {valid_types}"
                )

            # Check that regex rules have patterns
            if rule.type == "regex" and not rule.pattern:
                errors.append(f"Regex rule '{rule.id}' missing pattern")

            # Check that AST rules have check methods
            if rule.type == "ast" and not rule.check:
                errors.append(f"AST rule '{rule.id}' missing check method")

        # Validate severity levels
        valid_severities = {"error", "warning", "info"}
        for rule in rule_config.rules:
            if rule.severity not in valid_severities:
                errors.append(
                    f"Invalid severity '{rule.severity}' for rule '{rule.id}'. Valid severities: {valid_severities}"
                )

        return errors


if __name__ == "__main__":
    # Test the rule parser
    setup_logger(LogConfig())
    parser = RuleParser()

    try:
        config = parser.parse_rules()
        print(f"✅ Successfully parsed {len(config.rules)} rules")

        # Validate configuration
        errors = parser.validate_rule_config(config)
        if errors:
            print("❌ Validation errors:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ Rule configuration is valid")

        # Show some examples
        regex_rules = parser.get_rules_by_type(config, "regex")
        ast_rules = parser.get_rules_by_type(config, "ast")

        print("\n📊 Rule breakdown:")
        print(f"   - Regex rules: {len(regex_rules)}")
        print(f"   - AST rules: {len(ast_rules)}")
        print(f"   - Broken imports: {len(config.broken_imports)}")
        print(f"   - Ignore directories: {len(config.ignore_dirs)}")

    except Exception as e:
        print(f"❌ Error parsing rules: {e}")
        raise SystemExit(1)
