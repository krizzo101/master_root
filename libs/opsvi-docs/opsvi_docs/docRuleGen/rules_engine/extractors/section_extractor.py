# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Section Extractor Module","description":"Module for extracting and structuring sections from documentation content for conversion to rule format","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports and Constants","description":"Module imports and section type definitions","line_start":1,"line_end":48},{"name":"Extract Rule Sections","description":"Main function to extract sections from a document","line_start":49,"line_end":85},{"name":"Extract Sections for Rule Type","description":"Function to extract sections based on rule type","line_start":86,"line_end":124},{"name":"Extract Overview","description":"Function to extract overview section","line_start":125,"line_end":186},{"name":"Extract Principles","description":"Function to extract principles section","line_start":187,"line_end":239},{"name":"Extract Requirements","description":"Function to extract requirements section","line_start":240,"line_end":302},{"name":"Extract Dangers","description":"Function to extract dangers/warnings section","line_start":303,"line_end":381},{"name":"Extract Structure","description":"Function to extract structure section","line_start":382,"line_end":428},{"name":"Extract Templates","description":"Function to extract templates section","line_start":429,"line_end":477},{"name":"Extract Workflow","description":"Function to extract workflow section","line_start":478,"line_end":528},{"name":"Extract Formatting","description":"Function to extract formatting section","line_start":529,"line_end":591}],"key_elements":[{"name":"SECTION_TYPES","description":"Dictionary of section types to extract","line":19},{"name":"extract_rule_sections","description":"Main extraction function","line":49},{"name":"extract_sections_for_rule_type","description":"Function to process sections by rule type","line":86},{"name":"extract_overview","description":"Function to extract overview content","line":125},{"name":"extract_principles","description":"Function to extract principles from sections","line":187},{"name":"extract_requirements","description":"Function to extract requirements from sections","line":240},{"name":"extract_dangers","description":"Function to extract danger statements","line":303},{"name":"extract_structure","description":"Function to extract structure information","line":382},{"name":"extract_templates","description":"Function to extract templates from sections","line":429},{"name":"extract_workflow","description":"Function to extract workflow information","line":478},{"name":"extract_formatting","description":"Function to extract formatting information","line":529}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Section Extractor Module","description":"Module for extracting and structuring sections from documentation content for conversion to rule format","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports and Constants","description":"Module imports and section type definitions","line_start":1,"line_end":48},
# {"name":"Extract Rule Sections","description":"Main function to extract sections from a document","line_start":49,"line_end":85},
# {"name":"Extract Sections for Rule Type","description":"Function to extract sections based on rule type","line_start":86,"line_end":124},
# {"name":"Extract Overview","description":"Function to extract overview section","line_start":125,"line_end":186},
# {"name":"Extract Principles","description":"Function to extract principles section","line_start":187,"line_end":239},
# {"name":"Extract Requirements","description":"Function to extract requirements section","line_start":240,"line_end":302},
# {"name":"Extract Dangers","description":"Function to extract dangers/warnings section","line_start":303,"line_end":381},
# {"name":"Extract Structure","description":"Function to extract structure section","line_start":382,"line_end":428},
# {"name":"Extract Templates","description":"Function to extract templates section","line_start":429,"line_end":477},
# {"name":"Extract Workflow","description":"Function to extract workflow section","line_start":478,"line_end":528},
# {"name":"Extract Formatting","description":"Function to extract formatting section","line_start":529,"line_end":591}
# ],
# "key_elements":[
# {"name":"SECTION_TYPES","description":"Dictionary of section types to extract","line":19},
# {"name":"extract_rule_sections","description":"Main extraction function","line":49},
# {"name":"extract_sections_for_rule_type","description":"Function to process sections by rule type","line":86},
# {"name":"extract_overview","description":"Function to extract overview content","line":125}
# ]
# }
# FILE_MAP_END

"""
Section Extractor Module for Documentation Rule Generator.

This module provides functions to extract and structure sections from documentation
content for conversion to rule format.
"""

import re
from typing import Dict, List, Any
import logging
from .markdown_parser import parse_markdown_file

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Section types that we want to extract for rule generation
SECTION_TYPES = {
    "overview": ["overview", "introduction", "purpose", "summary"],
    "principles": [
        "principles",
        "core principles",
        "guidelines",
        "standards",
        "requirements",
    ],
    "implementation": [
        "implementation",
        "process",
        "workflow",
        "usage",
        "practice",
        "application",
    ],
    "examples": ["examples", "sample", "illustration", "demo"],
    "structure": ["structure", "organization", "format", "layout"],
    "content": ["content", "sections", "components", "elements"],
    "metadata": ["metadata", "properties", "attributes"],
    "naming": ["naming", "convention", "nomenclature", "terminology"],
    "validation": ["validation", "verification", "testing", "quality check"],
    "tools": ["tools", "tooling", "utilities", "software", "applications"],
}


def extract_rule_sections(doc_path: str, rule_type: str) -> Dict[str, Any]:
    """
    Extract relevant sections from a documentation file based on rule type.

    Args:
        doc_path: Path to the documentation file
        rule_type: Type of rule to generate (determines which sections to prioritize)

    Returns:
        Dictionary of extracted sections mapped to rule components
    """
    try:
        logger.info(f"Extracting sections from {doc_path} for rule type: {rule_type}")
        parsed_content = parse_markdown_file(doc_path)
        if "error" in parsed_content:
            logger.error(f"Error parsing file {doc_path}: {parsed_content['error']}")
            return {"error": parsed_content["error"]}

        # Extract specific sections based on rule type
        sections = parsed_content["sections"]
        examples = parsed_content["examples"]

        # Map documentation sections to rule components
        rule_sections = extract_sections_for_rule_type(sections, examples, rule_type)

        # Include metadata about the source
        rule_sections["_source"] = {
            "file_path": doc_path,
            "title": parsed_content["title"],
        }

        return rule_sections
    except Exception as e:
        logger.error(f"Error extracting rule sections from {doc_path}: {str(e)}")
        return {"error": str(e)}


def extract_sections_for_rule_type(
    sections: Dict[str, Any], examples: List[Dict[str, str]], rule_type: str
) -> Dict[str, Any]:
    """
    Extract specific sections based on rule type.

    Args:
        sections: Dictionary of parsed markdown sections
        examples: List of extracted examples
        rule_type: Type of rule to generate

    Returns:
        Dictionary of sections mapped to rule components
    """
    # Start with basic mapping
    rule_sections = {
        "overview": extract_overview(sections, rule_type),
        "examples": [ex["content"] for ex in examples],
        "requirements": extract_requirements(sections, rule_type),
        "danger": extract_dangers(sections, rule_type),
    }

    # Add type-specific sections
    if rule_type == "documentation-principles":
        rule_sections["principles"] = extract_principles(sections)
    elif (
        rule_type == "directory-organization" or rule_type == "file-naming-conventions"
    ):
        rule_sections["structure"] = extract_structure(sections)
    elif "template" in rule_type:
        rule_sections["templates"] = extract_templates(sections)
    elif "process" in rule_type:
        rule_sections["workflow"] = extract_workflow(sections)
    elif "style" in rule_type or "format" in rule_type:
        rule_sections["formatting"] = extract_formatting(sections)

    return rule_sections


def extract_overview(sections: Dict[str, Any], rule_type: str) -> Dict[str, str]:
    """
    Extract overview information from sections.

    Args:
        sections: Dictionary of parsed markdown sections
        rule_type: Type of rule being generated

    Returns:
        Dictionary with overview information
    """
    overview = {"purpose": "", "application": "", "importance": ""}

    # Look for an Overview or Introduction section
    for title, section in sections.items():
        title_lower = title.lower()
        if any(
            keyword in title_lower
            for keyword in ["overview", "introduction", "purpose"]
        ):
            # Extract purpose from the first paragraph
            content = section["content"]

            # Try to find explicit purpose statement
            purpose_match = re.search(
                r"(?:purpose|goal|aim).*?:?\s*(.*?)(?:\n\n|\n##|\Z)",
                content,
                re.IGNORECASE | re.DOTALL,
            )
            if purpose_match:
                overview["purpose"] = purpose_match.group(1).strip()

            # Try to find application information
            application_match = re.search(
                r"(?:applies to|application|used for|applies when).*?:?\s*(.*?)(?:\n\n|\n##|\Z)",
                content,
                re.IGNORECASE | re.DOTALL,
            )
            if application_match:
                overview["application"] = application_match.group(1).strip()

            # Try to find importance information
            importance_match = re.search(
                r"(?:importance|significance|why|benefits).*?:?\s*(.*?)(?:\n\n|\n##|\Z)",
                content,
                re.IGNORECASE | re.DOTALL,
            )
            if importance_match:
                overview["importance"] = importance_match.group(1).strip()

            # If we couldn't find specific parts, use paragraphs
            paragraphs = re.split(r"\n\s*\n", content)
            if not overview["purpose"] and len(paragraphs) > 0:
                overview["purpose"] = paragraphs[0].strip()
            if not overview["application"] and len(paragraphs) > 1:
                overview["application"] = paragraphs[1].strip()
            if not overview["importance"] and len(paragraphs) > 2:
                overview["importance"] = paragraphs[2].strip()

    return overview


def extract_principles(sections: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract principles from sections.

    Args:
        sections: Dictionary of parsed markdown sections

    Returns:
        List of principles with their descriptions
    """
    principles = []

    for title, section in sections.items():
        title_lower = title.lower()

        # Look for principles sections or subsections named after principles
        if any(
            keyword in title_lower
            for keyword in ["principle", "guideline", "standard", "rule"]
        ):
            content = section["content"]

            # Try to extract individual principles
            # Look for headers or bold text that might indicate principle names
            principle_matches = re.finditer(
                r"(?:^|\n)(?:\*\*|\#{3,6}\s)(.*?)(?:\*\*|$)(?:\s*\n)+(.*?)(?=\n\s*(?:\*\*|\#{3,6}\s)|\Z)",
                content,
                re.DOTALL,
            )

            for match in principle_matches:
                principle_name = match.group(1).strip()
                principle_desc = match.group(2).strip()
                principles.append(
                    {"name": principle_name, "description": principle_desc}
                )

            # If we couldn't find structured principles, look for list items
            if not principles:
                list_items = re.findall(
                    r"(?:^|\n)[*\-+]\s+(.*?)(?=\n[*\-+]|\Z)", content, re.DOTALL
                )
                for item in list_items:
                    principles.append(
                        {
                            "name": "",  # No explicit name in list items
                            "description": item.strip(),
                        }
                    )

    return principles


def extract_requirements(sections: Dict[str, Any], rule_type: str) -> List[str]:
    """
    Extract requirements from sections.

    Args:
        sections: Dictionary of parsed markdown sections
        rule_type: Type of rule being generated

    Returns:
        List of requirement statements
    """
    requirements = []

    # Look for sections that might contain requirements
    for title, section in sections.items():
        title_lower = title.lower()

        if any(
            keyword in title_lower
            for keyword in [
                "requirement",
                "guideline",
                "standard",
                "best practice",
                "must",
                "should",
            ]
        ):
            content = section["content"]

            # Look for list items which are common for requirements
            list_items = re.findall(
                r"(?:^|\n)[*\-+]\s+(.*?)(?=\n[*\-+]|\Z)", content, re.DOTALL
            )
            for item in list_items:
                # Format as a requirement if it's not already
                item = item.strip()
                if not re.match(
                    r"^(?:MUST|SHOULD|MAY|SHALL|REQUIRED|RECOMMENDED|OPTIONAL)",
                    item,
                    re.IGNORECASE,
                ):
                    if "must" in item.lower() or "should" in item.lower():
                        # It already has modal verbs, just capitalize
                        item = re.sub(
                            r"\b(must|should)\b",
                            lambda m: m.group(1).upper(),
                            item,
                            flags=re.IGNORECASE,
                        )
                    else:
                        # Add MUST if no modal verb is present
                        item = (
                            f"MUST {item[0].lower()}{item[1:]}"
                            if len(item) > 1
                            else f"MUST {item}"
                        )

                requirements.append(item)

    return requirements


def extract_dangers(
    sections: Dict[str, Any], rule_type: str = "documentation"
) -> Dict[str, List[str]]:
    """
    Extract danger statements and critical violations.

    Args:
        sections: Dictionary of parsed markdown sections
        rule_type: Type of rule being generated (default: "documentation")

    Returns:
        Dictionary with critical violations and specific risks
    """
    danger = {"critical_violations": [], "specific_risks": []}

    # Look for danger, warning, caution sections
    for title, section in sections.items():
        title_lower = title.lower()

        if any(
            keyword in title_lower
            for keyword in ["danger", "warning", "caution", "risk", "pitfall"]
        ):
            content = section["content"]

            # Extract list items
            list_items = re.findall(
                r"(?:^|\n)[*\-+]\s+(.*?)(?=\n[*\-+]|\Z)", content, re.DOTALL
            )

            for item in list_items:
                item = item.strip()

                # Format as a danger statement if it's not already
                if not re.match(
                    r"^(?:NEVER|DO NOT|AVOID|WARNING)", item, re.IGNORECASE
                ):
                    item = (
                        f"NEVER {item[0].lower()}{item[1:]}"
                        if len(item) > 1
                        else f"NEVER {item}"
                    )

                # Categorize based on severity indicators
                if re.search(
                    r"(?:critical|severe|crucial|essential|never|always|must)",
                    item,
                    re.IGNORECASE,
                ):
                    danger["critical_violations"].append(item)
                else:
                    danger["specific_risks"].append(item)

    # Fallback - ensure we have at least a few items
    if not danger["critical_violations"] and danger["specific_risks"]:
        # Promote some risks to critical violations
        danger["critical_violations"] = danger["specific_risks"][:2]
        danger["specific_risks"] = danger["specific_risks"][2:]

    # Generate some if none were found
    if not danger["critical_violations"]:
        rule_type_words = re.findall(r"[a-z]+", rule_type)
        if rule_type_words:
            danger["critical_violations"] = [
                f"NEVER ignore the {rule_type.replace('-', ' ')} standards when creating documentation",
                f"NEVER create documentation without following proper {rule_type.replace('-', ' ')} guidelines",
            ]

    if not danger["specific_risks"]:
        rule_type_words = re.findall(r"[a-z]+", rule_type)
        if rule_type_words:
            danger["specific_risks"] = [
                f"Inconsistent {rule_type.replace('-', ' ')} can confuse readers and make documentation harder to use",
                f"Poor {rule_type.replace('-', ' ')} can lead to increased maintenance costs and technical debt",
            ]

    return danger


def extract_structure(sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structure and organization information.

    Args:
        sections: Dictionary of parsed markdown sections

    Returns:
        Dictionary with structure information
    """
    structure = {"organization": "", "patterns": [], "examples": {}}

    # Look for structure-related sections
    for title, section in sections.items():
        title_lower = title.lower()

        if any(
            keyword in title_lower
            for keyword in ["structure", "organization", "hierarchy", "layout"]
        ):
            content = section["content"]

            # Extract first paragraph as general organization description
            first_para = re.match(r"^(.*?)(?:\n\n|\Z)", content, re.DOTALL)
            if first_para:
                structure["organization"] = first_para.group(1).strip()

            # Extract patterns (often in lists)
            list_items = re.findall(
                r"(?:^|\n)[*\-+]\s+(.*?)(?=\n[*\-+]|\Z)", content, re.DOTALL
            )
            if list_items:
                structure["patterns"] = [item.strip() for item in list_items]

            # Extract code blocks as examples
            code_blocks = re.finditer(r"```([a-z]*)\n(.*?)```", content, re.DOTALL)
            for i, match in enumerate(code_blocks):
                lang = match.group(1) or "text"
                code = match.group(2).strip()
                structure["examples"][f"example_{i+1}"] = {
                    "language": lang,
                    "code": code,
                }

    return structure


def extract_templates(sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract templates from sections.

    Args:
        sections: Dictionary of parsed markdown sections

    Returns:
        Dictionary with template information
    """
    templates = {"description": "", "templates": {}}

    # Look for template-related sections
    for title, section in sections.items():
        title_lower = title.lower()

        if any(
            keyword in title_lower
            for keyword in ["template", "format", "structure", "skeleton"]
        ):
            content = section["content"]

            # Extract first paragraph as template description
            first_para = re.match(r"^(.*?)(?:\n\n|\Z)", content, re.DOTALL)
            if first_para:
                templates["description"] = first_para.group(1).strip()

            # Extract code blocks as templates
            code_blocks = re.finditer(r"```([a-z]*)\n(.*?)```", content, re.DOTALL)
            for i, match in enumerate(code_blocks):
                lang = match.group(1) or "text"
                code = match.group(2).strip()

                # Try to find a name for this template
                template_name = f"template_{i+1}"
                content_before = content[: match.start()]
                name_match = re.search(
                    r"(?:^|\n)(#+\s+([^\n]+))\s*$", content_before, re.MULTILINE
                )
                if name_match:
                    template_name = (
                        name_match.group(2).strip().lower().replace(" ", "_")
                    )

                templates["templates"][template_name] = {"language": lang, "code": code}

    return templates


def extract_workflow(sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract workflow and process information.

    Args:
        sections: Dictionary of parsed markdown sections

    Returns:
        Dictionary with workflow information
    """
    workflow = {"description": "", "steps": [], "roles": []}

    # Look for process-related sections
    for title, section in sections.items():
        title_lower = title.lower()

        if any(
            keyword in title_lower
            for keyword in ["process", "workflow", "procedure", "steps", "lifecycle"]
        ):
            content = section["content"]

            # Extract first paragraph as description
            first_para = re.match(r"^(.*?)(?:\n\n|\Z)", content, re.DOTALL)
            if first_para:
                workflow["description"] = first_para.group(1).strip()

            # Extract ordered lists as steps
            steps = re.findall(
                r"(?:^|\n)\d+\.\s+(.*?)(?=\n\d+\.|\Z)", content, re.DOTALL
            )
            if steps:
                workflow["steps"] = [step.strip() for step in steps]

            # Extract roles from role or responsibility sections
            if "role" in title_lower or "responsib" in title_lower:
                roles = re.finditer(
                    r"(?:^|\n)(?:\*\*|\#{3,6}\s)(.*?)(?:\*\*|$)(?:\s*\n)+(.*?)(?=\n\s*(?:\*\*|\#{3,6}\s)|\Z)",
                    content,
                    re.DOTALL,
                )
                for match in roles:
                    role_name = match.group(1).strip()
                    role_desc = match.group(2).strip()
                    workflow["roles"].append(
                        {"name": role_name, "description": role_desc}
                    )

    return workflow


def extract_formatting(sections: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract formatting and style information.

    Args:
        sections: Dictionary of parsed markdown sections

    Returns:
        Dictionary with formatting information
    """
    formatting = {"description": "", "rules": [], "examples": {}}

    # Look for formatting-related sections
    for title, section in sections.items():
        title_lower = title.lower()

        if any(
            keyword in title_lower
            for keyword in ["format", "style", "writing", "grammar", "convention"]
        ):
            content = section["content"]

            # Extract first paragraph as description
            first_para = re.match(r"^(.*?)(?:\n\n|\Z)", content, re.DOTALL)
            if first_para:
                formatting["description"] = first_para.group(1).strip()

            # Extract lists as formatting rules
            list_items = re.findall(
                r"(?:^|\n)[*\-+]\s+(.*?)(?=\n[*\-+]|\Z)", content, re.DOTALL
            )
            if list_items:
                formatting["rules"] = [item.strip() for item in list_items]

            # Extract code blocks as examples
            code_blocks = re.finditer(r"```([a-z]*)\n(.*?)```", content, re.DOTALL)
            for i, match in enumerate(code_blocks):
                lang = match.group(1) or "text"
                code = match.group(2).strip()

                # Try to determine if this is a good or bad example
                example_type = "example"
                content_before = content[: match.start()]
                if re.search(
                    r"(?:good|correct|preferred|recommended)",
                    content_before,
                    re.IGNORECASE,
                ):
                    example_type = "good_example"
                elif re.search(
                    r"(?:bad|incorrect|avoid|not recommended)",
                    content_before,
                    re.IGNORECASE,
                ):
                    example_type = "bad_example"

                formatting["examples"][f"{example_type}_{i+1}"] = {
                    "language": lang,
                    "code": code,
                }

    return formatting
