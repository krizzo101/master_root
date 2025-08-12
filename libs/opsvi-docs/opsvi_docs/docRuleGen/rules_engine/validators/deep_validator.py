# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Deep Validator Module","description":"This module provides a validator for deeper rule analysis, including conceptual coherence, completeness, and effectiveness.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary modules and classes for the deep validator.","line_start":3,"line_end":13},{"name":"DeepValidator Class","description":"Defines the DeepValidator class which extends RuleValidator and implements various validation methods.","line_start":15,"line_end":290}],"key_elements":[{"name":"DeepValidator","description":"Class for deeper rule analysis validation.","line":16},{"name":"__init__","description":"Constructor for initializing the DeepValidator.","line":24},{"name":"validate","description":"Main method to perform deep validation on rule content.","line":35},{"name":"_check_conceptual_coherence","description":"Checks for conceptual coherence across the rule.","line":83},{"name":"_check_completeness","description":"Checks for completeness of the rule.","line":148},{"name":"_check_effectiveness","description":"Checks for effectiveness of the rule.","line":187},{"name":"_extract_key_terms","description":"Extracts key terms from text for comparison.","line":243},{"name":"_are_similar","description":"Checks if two text strings are conceptually similar.","line":269}]}
"""
# FILE_MAP_END

"""
Deep Validator Module.

This module provides a validator for deeper rule analysis, including
conceptual coherence, completeness, and effectiveness.
"""

import logging
import re
from typing import Dict, Any, List, Optional

from .rule_validator import RuleValidator

logger = logging.getLogger(__name__)


class DeepValidator(RuleValidator):
    """
    Validator for deeper rule analysis.

    This validator checks rule coherence, completeness, and effectiveness
    beyond basic structural validation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the deep validator.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

        logger.info("Initialized deep validator")

    def validate(
        self, rule_content: str, rule_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform deep validation on rule content.

        Args:
            rule_content: Content of the rule to validate
            rule_path: Optional path to the rule file

        Returns:
            Dictionary with validation results
        """
        logger.info(f"Performing deep validation on rule: {rule_path or 'unnamed'}")

        issues = []

        # Extract frontmatter and sections
        frontmatter = self._extract_frontmatter(rule_content)
        sections = self._extract_sections(rule_content)

        # Check conceptual coherence
        coherence_issues = self._check_conceptual_coherence(frontmatter, sections)
        issues.extend(coherence_issues)

        # Check completeness
        completeness_issues = self._check_completeness(frontmatter, sections)
        issues.extend(completeness_issues)

        # Check effectiveness
        effectiveness_issues = self._check_effectiveness(frontmatter, sections)
        issues.extend(effectiveness_issues)

        # Determine overall status
        status = "pass" if not issues else "fail"

        result = {
            "status": status,
            "pass": status == "pass",
            "issues": issues,
            "analysis": {
                "conceptual_coherence": len(coherence_issues) == 0,
                "completeness": len(completeness_issues) == 0,
                "effectiveness": len(effectiveness_issues) == 0,
            },
        }

        logger.info(f"Deep validation complete. Status: {result['status']}")
        return result

    def _check_conceptual_coherence(
        self, frontmatter: Dict[str, Any], sections: Dict[str, str]
    ) -> List[str]:
        """
        Check for conceptual coherence across the rule.

        Args:
            frontmatter: Extracted frontmatter
            sections: Extracted sections

        Returns:
            List of identified issues
        """
        issues = []

        # Check if directive is consistent throughout the rule
        directive = None

        # Extract directive from description
        description = frontmatter.get("description", "")
        if description and self._has_directive_pattern(description):
            directive = self._extract_directive(description)

        # Check for directive in requirements section
        if "requirements" in sections and self._has_directive_pattern(
            sections["requirements"]
        ):
            requirements_directive = self._extract_directive(sections["requirements"])

            # Compare with description directive
            if directive:
                # Check when context
                if directive.get("when") and requirements_directive.get("when"):
                    if not self._are_similar(
                        directive["when"], requirements_directive["when"]
                    ):
                        issues.append(
                            "Inconsistent WHEN context between description and requirements"
                        )

                # Check to purpose
                if directive.get("to") and requirements_directive.get("to"):
                    if not self._are_similar(
                        directive["to"], requirements_directive["to"]
                    ):
                        issues.append(
                            "Inconsistent TO purpose between description and requirements"
                        )

                # Check directive
                if directive.get("directive") and requirements_directive.get(
                    "directive"
                ):
                    if not self._are_similar(
                        directive["directive"], requirements_directive["directive"]
                    ):
                        issues.append(
                            "Inconsistent directive between description and requirements"
                        )

        # Check if overview aligns with directive
        if directive and "overview" in sections:
            overview = sections["overview"]

            # Check if overview mentions key terms from directive
            when_terms = self._extract_key_terms(directive.get("when", ""))
            to_terms = self._extract_key_terms(directive.get("to", ""))
            directive_terms = self._extract_key_terms(directive.get("directive", ""))

            # Combine all terms
            all_terms = when_terms + to_terms + directive_terms

            # Count how many terms are mentioned in overview
            mentioned_count = sum(
                1 for term in all_terms if term.lower() in overview.lower()
            )
            mention_ratio = mentioned_count / len(all_terms) if all_terms else 0

            if mention_ratio < 0.3 and len(all_terms) > 2:
                issues.append("Overview does not adequately address directive concepts")

        return issues

    def _check_completeness(
        self, frontmatter: Dict[str, Any], sections: Dict[str, str]
    ) -> List[str]:
        """
        Check for completeness of the rule.

        Args:
            frontmatter: Extracted frontmatter
            sections: Extracted sections

        Returns:
            List of identified issues
        """
        issues = []

        # Check for minimum section content lengths
        section_min_lengths = {"overview": 100, "context": 100, "requirements": 100}

        for section, min_length in section_min_lengths.items():
            if section in sections and len(sections[section].strip()) < min_length:
                issues.append(
                    f"{section.title()} section is too brief (< {min_length} chars)"
                )

        # Check for specific content in sections
        if "context" in sections:
            context = sections["context"]
            if not re.search(
                r"(?:use case|scenario|situation|when to apply|apply when)",
                context,
                re.IGNORECASE,
            ):
                issues.append(
                    "Context section does not clearly specify when to apply the rule"
                )

        if "requirements" in sections:
            requirements = sections["requirements"]
            if not re.search(
                r"(?:must|should|shall|required to|need to)",
                requirements,
                re.IGNORECASE,
            ):
                issues.append(
                    "Requirements section does not clearly specify mandatory actions"
                )

        return issues

    def _check_effectiveness(
        self, frontmatter: Dict[str, Any], sections: Dict[str, str]
    ) -> List[str]:
        """
        Check for effectiveness of the rule.

        Args:
            frontmatter: Extracted frontmatter
            sections: Extracted sections

        Returns:
            List of identified issues
        """
        issues = []

        # Check if there are examples that demonstrate the rule
        has_examples = False
        for section_name in sections:
            if "example" in section_name.lower():
                has_examples = True
                section_content = sections[section_name]

                # Check if examples are substantive
                if len(section_content.strip()) < 100:
                    issues.append("Examples section is not substantive enough")

                # Check for code examples
                if "```" not in section_content and not re.search(
                    r"^\s*[-*]\s+", section_content, re.MULTILINE
                ):
                    issues.append(
                        "Examples section lacks concrete examples (code blocks or bullet points)"
                    )

        if not has_examples:
            issues.append("Rule lacks examples section")

        # Check if there's a danger/warning section for potential issues
        has_warnings = False
        for section_name in sections:
            if any(
                term in section_name.lower()
                for term in ["danger", "warning", "caution"]
            ):
                has_warnings = True

                # Check if warnings are substantive
                section_content = sections[section_name]
                if len(section_content.strip()) < 50:
                    issues.append(
                        f"{section_name.title()} section is not substantive enough"
                    )

        # For critical rules, warnings should be present
        if "id" in frontmatter:
            rule_id = frontmatter["id"]
            # Check if rule is in certain critical categories (1xx, 3xx, 5xx)
            critical_prefixes = ["1", "3", "5"]
            first_digit = str(rule_id)[0] if str(rule_id).isdigit() else ""

            if first_digit in critical_prefixes and not has_warnings:
                issues.append("Critical rule lacks warnings/dangers section")

        return issues

    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from text for comparison.

        Args:
            text: Text to extract terms from

        Returns:
            List of key terms
        """
        # Remove stop words
        stop_words = [
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "if",
            "then",
            "than",
            "for",
            "with",
            "without",
            "to",
            "from",
            "in",
            "out",
            "by",
            "on",
            "off",
            "up",
            "down",
            "over",
            "under",
            "of",
            "at",
        ]

        # Split into words, remove punctuation
        import re

        words = re.findall(r"\b\w+\b", text.lower())

        # Filter out stop words and short words
        key_terms = [word for word in words if word not in stop_words and len(word) > 3]

        return key_terms

    def _are_similar(self, text1: str, text2: str) -> bool:
        """
        Check if two text strings are conceptually similar.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            True if texts are similar, False otherwise
        """
        # Extract key terms
        terms1 = set(self._extract_key_terms(text1))
        terms2 = set(self._extract_key_terms(text2))

        # Calculate Jaccard similarity
        intersection = terms1.intersection(terms2)
        union = terms1.union(terms2)

        similarity = len(intersection) / len(union) if union else 0

        # Consider similar if above threshold
        return similarity >= 0.3
