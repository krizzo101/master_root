# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Markdown to Rule Transformer Module","description":"This module provides functions to transform markdown content extracted from documentation standards into rule format.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Documentation","description":"Docstring providing an overview of the module's purpose.","line_start":2,"line_end":6},{"name":"Imports","description":"Import statements for required libraries and modules.","line_start":8,"line_end":13},{"name":"Logging Configuration","description":"Configuration of logging for the module.","line_start":15,"line_end":19},{"name":"Function: transform_to_rule_content","description":"Transforms extracted documentation content into rule content structure.","line_start":22,"line_end":99},{"name":"Function: generate_rule_description","description":"Generates a WHEN/TO/MUST description for a documentation rule.","line_start":100,"line_end":147},{"name":"Function: transform_overview","description":"Transforms overview content into rule format.","line_start":148,"line_end":173},{"name":"Function: transform_requirements","description":"Transforms requirements into rule format.","line_start":174,"line_end":214},{"name":"Function: transform_examples","description":"Transforms examples into rule format.","line_start":215,"line_end":257},{"name":"Function: transform_danger","description":"Transforms danger statements into rule format.","line_start":258,"line_end":299},{"name":"Function: transform_principles","description":"Transforms principles into rule format.","line_start":300,"line_end":336},{"name":"Function: transform_structure","description":"Transforms structure information into rule format.","line_start":337,"line_end":367},{"name":"Function: transform_templates","description":"Transforms templates into rule format.","line_start":368,"line_end":390},{"name":"Function: transform_workflow","description":"Transforms workflow information into rule format.","line_start":391,"line_end":410},{"name":"Function: transform_formatting","description":"Transforms formatting information into rule format.","line_start":411,"line_end":445},{"name":"Class: MarkdownToRuleTransformer","description":"Class to transform markdown content into structured rule format.","line_start":438,"line_end":765}],"key_elements":[{"name":"transform_to_rule_content","description":"Transforms extracted documentation content into rule content structure.","line":22},{"name":"generate_rule_description","description":"Generates a WHEN/TO/MUST description for a documentation rule.","line":100},{"name":"transform_overview","description":"Transforms overview content into rule format.","line":148},{"name":"transform_requirements","description":"Transforms requirements into rule format.","line":174},{"name":"transform_examples","description":"Transforms examples into rule format.","line":215},{"name":"transform_danger","description":"Transforms danger statements into rule format.","line":258},{"name":"transform_principles","description":"Transforms principles into rule format.","line":300},{"name":"transform_structure","description":"Transforms structure information into rule format.","line":337},{"name":"transform_templates","description":"Transforms templates into rule format.","line":368},{"name":"transform_workflow","description":"Transforms workflow information into rule format.","line":391},{"name":"transform_formatting","description":"Transforms formatting information into rule format.","line":411},{"name":"MarkdownToRuleTransformer","description":"Class to transform markdown content into structured rule format.","line":438}]}
"""
# FILE_MAP_END

"""
Markdown to Rule Transformer Module for Documentation Rule Generator.

This module provides functions to transform markdown content extracted from
documentation standards into rule format.
"""

import re
from typing import Dict, List, Any, Optional
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def transform_to_rule_content(
    extracted_content: Dict[str, Any], rule_type: str
) -> Dict[str, Any]:
    """
    Transform extracted documentation content into rule content structure.

    Args:
        extracted_content: Extracted documentation content
        rule_type: Type of documentation rule

    Returns:
        Structured rule content
    """
    if "error" in extracted_content:
        logger.error(f"Error transforming content: {extracted_content['error']}")
        return {"error": extracted_content["error"]}

    rule_id = extracted_content.get("rule_id", "")
    rule_name = extracted_content.get("rule_name", "")

    logger.info(f"Transforming content for rule {rule_id}: {rule_name}")

    # Create the basic rule structure
    rule_content = {
        "rule_name": rule_name.replace("-", " ").title(),
        "overview": transform_overview(extracted_content.get("overview", {})),
        "requirements": transform_requirements(
            extracted_content.get("requirements", []), rule_type
        ),
        "examples": transform_examples(
            extracted_content.get("examples", []), rule_type
        ),
        "danger": transform_danger(extracted_content.get("danger", {}), rule_type),
    }

    # Add specialized sections based on rule type
    if "principles" in extracted_content:
        rule_content["principles"] = transform_principles(
            extracted_content["principles"], rule_type
        )

    if "structure" in extracted_content:
        rule_content["structure"] = transform_structure(
            extracted_content["structure"], rule_type
        )

    if "templates" in extracted_content:
        rule_content["templates"] = transform_templates(
            extracted_content["templates"], rule_type
        )

    if "workflow" in extracted_content:
        rule_content["workflow"] = transform_workflow(
            extracted_content["workflow"], rule_type
        )

    if "formatting" in extracted_content:
        rule_content["formatting"] = transform_formatting(
            extracted_content["formatting"], rule_type
        )

    # Add related rules if there's a parent
    if "parent_rule" in extracted_content:
        parent_id = extracted_content["parent_rule"]
        rule_content["related_rules"] = [
            f"See parent rule: [{parent_id}-{parent_id.split('-')[0]}]"
        ]

    # Add metadata
    rule_content["metadata"] = {
        "rule_id": rule_id,
        "type": "documentation",
        "sources": [source["file"] for source in extracted_content.get("sources", [])],
    }

    return rule_content


def generate_rule_description(rule_type: str, content: Dict[str, Any]) -> str:
    """
    Generate a WHEN/TO/MUST description for a documentation rule.

    Args:
        rule_type: Type of documentation rule
        content: Extracted content for the rule

    Returns:
        Formatted rule description
    """
    # Split the rule type into words for better readability
    rule_words = rule_type.replace("-", " ").split()

    # Default values
    when_clause = f"creating {rule_type.replace('-', ' ')} documentation"
    to_clause = "ensure consistency and quality"

    # Try to extract a better purpose from the content
    overview = content.get("overview", {})
    if overview.get("purpose"):
        purpose = overview["purpose"]
        purpose_match = re.search(
            r"(?:to|for)\s+(.+?)(?:\.|\n|$)", purpose, re.IGNORECASE
        )
        if purpose_match:
            to_clause = purpose_match.group(1).strip()

    # Determine if we need to include 'THESE' in the description
    # Include 'THESE' in most rule descriptions since they provide specific standards
    # For parent rules with child rules, or rules with specific requirements
    has_requirements = (
        content.get("requirements")
        or content.get("principles")
        or content.get("structure")
        or content.get("formatting")
    )
    is_parent_rule = (
        "parent_rule" not in content.get("metadata", {}) and has_requirements
    )

    # Only include 'THESE' if the rule provides specific standards
    if is_parent_rule or has_requirements:
        # Generate the full description with "THESE"
        return f"WHEN {when_clause} TO {to_clause} you MUST follow THESE {rule_type.replace('-', ' ')} standards"
    else:
        # Generate the description without "THESE" for more general rules
        return f"WHEN {when_clause} TO {to_clause} you MUST follow {rule_type.replace('-', ' ')} standards"


def transform_overview(overview: Dict[str, str]) -> Dict[str, str]:
    """
    Transform overview content into rule format.

    Args:
        overview: Extracted overview content

    Returns:
        Transformed overview
    """
    transformed = {}

    # Format the purpose as a structured statement if it's not already
    purpose = overview.get("purpose", "")
    if purpose and not purpose.upper().startswith("MUST "):
        purpose = (
            f"MUST {purpose[0].lower()}{purpose[1:]}" if len(purpose) > 1 else purpose
        )

    transformed["purpose"] = purpose
    transformed["application"] = overview.get("application", "")
    transformed["importance"] = overview.get("importance", "")

    return transformed


def transform_requirements(
    requirements: List[str], rule_type: str
) -> Dict[str, List[str]]:
    """
    Transform requirements into rule format.

    Args:
        requirements: Extracted requirements
        rule_type: Type of documentation rule

    Returns:
        Transformed requirements
    """
    # Split into should, must, and may requirements
    must_reqs = []
    should_reqs = []
    may_reqs = []

    for req in requirements:
        req = req.strip()
        if "MUST" in req.upper() or "SHALL" in req.upper() or "REQUIRED" in req.upper():
            must_reqs.append(req)
        elif "SHOULD" in req.upper() or "RECOMMENDED" in req.upper():
            should_reqs.append(req)
        elif "MAY" in req.upper() or "OPTIONAL" in req.upper():
            may_reqs.append(req)
        else:
            # If no directive, assume it's a MUST
            if not req.upper().startswith("MUST "):
                req = f"MUST {req[0].lower()}{req[1:]}" if len(req) > 1 else req
            must_reqs.append(req)

    # Generate one more requirement if we have very few
    if len(must_reqs) < 2:
        must_reqs.append(
            f"MUST follow {rule_type.replace('-', ' ')} standards for all documentation"
        )

    return {"critical": must_reqs, "recommended": should_reqs, "optional": may_reqs}


def transform_examples(examples: List[str], rule_type: str) -> List[Dict[str, str]]:
    """
    Transform examples into rule format.

    Args:
        examples: Extracted examples
        rule_type: Type of documentation rule

    Returns:
        Transformed examples
    """
    transformed = []

    for i, example in enumerate(examples):
        # Clean up example content
        example = example.strip()

        # Add a title if it doesn't have one
        title_match = re.match(r"^#+\s+(.+)$", example, re.MULTILINE)
        title = (
            title_match.group(1)
            if title_match
            else f"{rule_type.replace('-', ' ').title()} Example"
        )

        # Remove the title from the content if it's included
        if title_match:
            example = re.sub(r"^#+\s+.+$", "", example, 1, re.MULTILINE).strip()

        transformed.append({"title": title, "content": example})

    # If no examples provided, create a placeholder
    if not transformed:
        transformed.append(
            {
                "title": f"{rule_type.replace('-', ' ').title()} Example",
                "content": f"This is a placeholder example for {rule_type.replace('-', ' ')}.",
            }
        )

    return transformed


def transform_danger(
    danger: Dict[str, List[str]], rule_type: str
) -> Dict[str, List[str]]:
    """
    Transform danger statements into rule format.

    Args:
        danger: Extracted danger statements
        rule_type: Type of documentation rule

    Returns:
        Transformed danger statements
    """
    critical = danger.get("critical_violations", [])
    risks = danger.get("specific_risks", [])

    # Ensure all critical violations start with NEVER
    for i, violation in enumerate(critical):
        if not violation.upper().startswith("NEVER "):
            critical[i] = (
                f"NEVER {violation[0].lower()}{violation[1:]}"
                if len(violation) > 1
                else violation
            )

    # Generate at least two critical violations if none exist
    if not critical:
        critical = [
            f"NEVER ignore the {rule_type.replace('-', ' ')} standards when creating documentation",
            f"NEVER create documentation without proper {rule_type.replace('-', ' ')} structure",
        ]

    # Generate at least two risks if none exist
    if not risks:
        risks = [
            f"Poor {rule_type.replace('-', ' ')} can lead to confusion and misunderstanding",
            f"Inconsistent {rule_type.replace('-', ' ')} increases maintenance burden",
        ]

    return {"critical_violations": critical, "specific_risks": risks}


def transform_principles(
    principles: List[Dict[str, str]], rule_type: str
) -> Dict[str, Any]:
    """
    Transform principles into rule format.

    Args:
        principles: Extracted principles
        rule_type: Type of documentation rule

    Returns:
        Transformed principles
    """
    transformed = {"core_principles": []}

    for principle in principles:
        name = principle.get("name", "")
        description = principle.get("description", "")

        if name:
            transformed["core_principles"].append(
                {"name": name, "description": description}
            )
        elif description:
            # No name provided, use first sentence as name
            sentences = re.split(r"(?<=\.)(?:\s+)", description)
            if sentences:
                name = sentences[0]
                rest = " ".join(sentences[1:]) if len(sentences) > 1 else ""

                transformed["core_principles"].append(
                    {"name": name, "description": rest or name}
                )

    return transformed


def transform_structure(structure: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
    """
    Transform structure information into rule format.

    Args:
        structure: Extracted structure information
        rule_type: Type of documentation rule

    Returns:
        Transformed structure
    """
    transformed = {
        "description": structure.get("organization", ""),
        "elements": [],
        "examples": {},
    }

    # Convert patterns to elements
    for pattern in structure.get("patterns", []):
        transformed["elements"].append({"description": pattern})

    # Add examples
    for key, example in structure.get("examples", {}).items():
        transformed["examples"][key] = {
            "language": example.get("language", "text"),
            "content": example.get("code", ""),
        }

    return transformed


def transform_templates(templates: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
    """
    Transform templates into rule format.

    Args:
        templates: Extracted templates
        rule_type: Type of documentation rule

    Returns:
        Transformed templates
    """
    transformed = {"description": templates.get("description", ""), "templates": {}}

    # Add templates
    for name, template in templates.get("templates", {}).items():
        transformed["templates"][name] = {
            "language": template.get("language", "markdown"),
            "content": template.get("code", ""),
        }

    return transformed


def transform_workflow(workflow: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
    """
    Transform workflow information into rule format.

    Args:
        workflow: Extracted workflow information
        rule_type: Type of documentation rule

    Returns:
        Transformed workflow
    """
    transformed = {
        "description": workflow.get("description", ""),
        "steps": workflow.get("steps", []),
        "roles": workflow.get("roles", []),
    }

    return transformed


def transform_formatting(formatting: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
    """
    Transform formatting information into rule format.

    Args:
        formatting: Extracted formatting information
        rule_type: Type of documentation rule

    Returns:
        Transformed formatting
    """
    transformed = {
        "description": formatting.get("description", ""),
        "rules": formatting.get("rules", []),
        "examples": {},
    }

    # Add examples
    for key, example in formatting.get("examples", {}).items():
        transformed["examples"][key] = {
            "language": example.get("language", "markdown"),
            "content": example.get("code", ""),
        }

    return transformed


class MarkdownToRuleTransformer:
    """
    Transform markdown content into structured rule format.

    This class analyzes markdown content and extracts key components
    to create a structured rule representation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the markdown to rule transformer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        logger.info("Initialized markdown to rule transformer")

    def transform(
        self, content: Dict[str, Any], taxonomy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform markdown content into rule structure.

        Args:
            content: Preprocessed markdown content
            taxonomy: Optional taxonomy information

        Returns:
            Transformed content ready for rule generation
        """
        logger.info("Transforming markdown content into rule structure")

        if not content or not isinstance(content, dict):
            logger.error("Invalid content provided for transformation")
            return {"status": "error", "error": "Invalid content provided"}

        # Extract markdown content
        markdown_content = content.get("content", "")
        if not markdown_content:
            logger.error("No markdown content found in input")
            return {"status": "error", "error": "No markdown content found"}

        # Extract concepts from taxonomy if available
        concepts = []
        if taxonomy and "concepts" in taxonomy:
            concepts = taxonomy["concepts"]
        elif "concepts" in content:
            concepts = content["concepts"]

        # Extract key components
        title = self._extract_title(markdown_content, content)
        description = self._extract_description(markdown_content, content)
        rule_id = self._generate_rule_id(title, content, taxonomy)
        rule_name = self._generate_rule_name(title, content, taxonomy)

        # Extract sections
        sections = self._extract_sections(markdown_content)

        # Generate rule content
        rule_content = self._generate_rule_content(
            rule_id,
            rule_name,
            title,
            description,
            sections,
            concepts,
            content,
            taxonomy,
        )

        # Create the transformed content structure
        transformed = {
            "status": "success",  # Add success status
            "rule_id": rule_id,
            "rule_name": rule_name,
            "title": title,
            "description": description,
            "rule_content": rule_content,
            "document_type": content.get("document_type", "markdown"),
            "source_path": content.get("file_path", ""),
            "metadata": {
                "id": rule_id,
                "name": rule_name,
                "title": title,
                "description": description,
                "type": "documentation",
            },
        }

        logger.info(f"Successfully transformed content for rule {rule_id}: {rule_name}")
        return transformed

    def _extract_title(self, markdown_content: str, content: Dict[str, Any]) -> str:
        """Extract title from markdown content."""
        # Try to get from metadata
        if "title" in content:
            return content["title"]

        # Try to extract from first heading
        heading_match = re.search(r"^#\s+(.+)$", markdown_content, re.MULTILINE)
        if heading_match:
            return heading_match.group(1).strip()

        # Fall back to filename
        if "file_path" in content:
            import os

            filename = os.path.basename(content["file_path"])
            return os.path.splitext(filename)[0].replace("_", " ").title()

        return "Untitled Rule"

    def _extract_description(
        self, markdown_content: str, content: Dict[str, Any]
    ) -> str:
        """Extract description from markdown content."""
        # Try to get from metadata
        if "description" in content:
            return content["description"]

        # Try to extract first paragraph after title
        lines = markdown_content.split("\n")
        in_paragraph = False
        description = []

        for line in lines:
            if re.match(r"^#\s+", line):  # Skip headings
                in_paragraph = True
                continue

            if in_paragraph and line.strip():
                description.append(line.strip())

            if in_paragraph and description and not line.strip():
                break

        if description:
            return " ".join(description)

        # Extract first non-empty line as fallback
        for line in lines:
            if line.strip() and not line.startswith("#"):
                return line.strip()

        return "No description available"

    def _generate_rule_id(
        self, title: str, content: Dict[str, Any], taxonomy: Optional[Dict[str, Any]]
    ) -> str:
        """Generate rule ID based on content and taxonomy."""
        # Try to extract from existing ID in content
        if "id" in content:
            return content["id"]

        # Try to extract from filename if it starts with a number
        if "file_path" in content:
            import os

            filename = os.path.basename(content["file_path"])
            id_match = re.match(r"^(\d{3})-", filename)
            if id_match:
                return id_match.group(1)

        # Generate based on taxonomy domain if available
        if taxonomy:
            primary_topics = taxonomy.get("primary_topics", [])
            if primary_topics:
                topic = primary_topics[0].lower()

                # Map topic to ID range
                topic_ranges = {
                    "meta": (1, 49),
                    "methodology": (50, 99),
                    "setup": (100, 149),
                    "requirements": (150, 199),
                    "design": (200, 249),
                    "documentation": (250, 299),
                    "development": (300, 349),
                    "quality": (350, 399),
                    "testing": (400, 449),
                    "bug": (450, 499),
                    "security": (500, 549),
                    "performance": (550, 599),
                    "refactoring": (600, 649),
                    "versioning": (650, 699),
                    "review": (700, 749),
                    "finalization": (750, 799),
                    "tools": (800, 849),
                    "automation": (850, 899),
                    "project": (900, 949),
                    "experimental": (950, 999),
                }

                # Find matching range
                for key, (start, end) in topic_ranges.items():
                    if key in topic or any(key in t.lower() for t in primary_topics):
                        import random

                        return f"{random.randint(start, end):03d}"

        # Default to random ID in the project range
        import random

        return f"{random.randint(900, 949):03d}"

    def _generate_rule_name(
        self, title: str, content: Dict[str, Any], taxonomy: Optional[Dict[str, Any]]
    ) -> str:
        """Generate rule name based on content and taxonomy."""
        # Try to extract from existing name in content
        if "name" in content:
            return content["name"]

        # Generate from title
        name = title.lower()

        # Remove special characters and replace spaces with hyphens
        name = re.sub(r"[^\w\s-]", "", name)
        name = re.sub(r"\s+", "-", name)

        # Limit length
        if len(name) > 50:
            name = name[:50]

        return name

    def _extract_sections(self, markdown_content: str) -> Dict[str, str]:
        """Extract sections from markdown content."""
        sections = {}
        current_section = "overview"
        current_content = []

        lines = markdown_content.split("\n")

        for line in lines:
            # Check if line is a heading
            heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)

            if heading_match:
                # Save current section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                    current_content = []

                # Determine new section name
                heading_level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip().lower()

                # Map heading to section
                if heading_level == 1:
                    current_section = "title"
                elif "overview" in heading_text or "introduction" in heading_text:
                    current_section = "overview"
                elif "context" in heading_text or "when" in heading_text:
                    current_section = "context"
                elif "requirement" in heading_text or "must" in heading_text:
                    current_section = "requirements"
                elif "example" in heading_text:
                    current_section = "examples"
                elif "warning" in heading_text or "caution" in heading_text:
                    current_section = "warnings"
                else:
                    # Use heading text as section name
                    current_section = re.sub(r"[^\w\s-]", "", heading_text).replace(
                        " ", "_"
                    )
            else:
                current_content.append(line)

        # Save final section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _generate_rule_content(
        self,
        rule_id: str,
        rule_name: str,
        title: str,
        description: str,
        sections: Dict[str, str],
        concepts: List[Dict[str, Any]],
        content: Dict[str, Any],
        taxonomy: Optional[Dict[str, Any]],
    ) -> str:
        """Generate rule content in the standard format."""
        # Start with rule header
        rule_content = [
            f"{rule_id}-{rule_name}: WHEN creating, editing, or accessing ANY file TO ensure consistency you MUST follow these guidelines"
        ]

        # Add overview section
        if "overview" in sections:
            rule_content.append("\n## Overview\n")
            rule_content.append(sections["overview"])
        else:
            rule_content.append("\n## Overview\n")
            rule_content.append(description)

        # Add context section
        if "context" in sections:
            rule_content.append("\n## Context\n")
            rule_content.append(sections["context"])

        # Add requirements section
        if "requirements" in sections:
            rule_content.append("\n## Requirements\n")
            rule_content.append(sections["requirements"])

        # Add examples section
        if "examples" in sections:
            rule_content.append("\n## Examples\n")
            rule_content.append(sections["examples"])

        # Add warnings section
        if "warnings" in sections:
            rule_content.append("\n## Warnings\n")
            rule_content.append(sections["warnings"])

        # Add other sections
        for section_name, section_content in sections.items():
            if section_name not in [
                "overview",
                "context",
                "requirements",
                "examples",
                "warnings",
                "title",
            ]:
                rule_content.append(f"\n## {section_name.replace('_', ' ').title()}\n")
                rule_content.append(section_content)

        # Join all sections
        return "\n".join(rule_content)
