# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Markdown Preprocessor Module","description":"Module for preprocessing markdown content into a standardized format for rule generation","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":1,"line_end":14},{"name":"MarkdownPreprocessor Class","description":"Main class for markdown preprocessing","line_start":15,"line_end":486},{"name":"Process Method","description":"Main processing method","line_start":18,"line_end":49},{"name":"Create Overview Section","description":"Method to create standardized overview","line_start":50,"line_end":74},{"name":"Create Context Section","description":"Method to create standardized context","line_start":75,"line_end":93},{"name":"Create Requirements Section","description":"Method to create standardized requirements","line_start":94,"line_end":117},{"name":"Extract Examples","description":"Method to extract code examples","line_start":118,"line_end":159},{"name":"Extract Warnings","description":"Method to extract warnings and cautions","line_start":160,"line_end":204},{"name":"Extract Key Concepts","description":"Method to extract key concepts","line_start":205,"line_end":272},{"name":"Identify Directive Candidates","description":"Method to identify directive statements","line_start":273,"line_end":343},{"name":"Generate Standardized Markdown","description":"Method to generate standardized output","line_start":344,"line_end":434},{"name":"Parse Sections","description":"Method to parse markdown into sections","line_start":435,"line_end":473},{"name":"Standardize Markdown","description":"Method to standardize markdown format","line_start":474,"line_end":486}],"key_elements":[{"name":"MarkdownPreprocessor","description":"Main preprocessor class","line":15},{"name":"process","description":"Main processing method","line":18},{"name":"_create_overview_section","description":"Method to create standardized overview","line":50},{"name":"_create_context_section","description":"Method to create standardized context","line":75},{"name":"_create_requirements_section","description":"Method to create standardized requirements","line":94},{"name":"_extract_examples","description":"Method to extract code examples","line":118},{"name":"_extract_warnings","description":"Method to extract warnings","line":160},{"name":"_extract_key_concepts","description":"Method to extract key concepts","line":205},{"name":"_identify_directive_candidates","description":"Method to identify directive candidates","line":273},{"name":"_generate_standardized_markdown","description":"Method to generate standardized markdown","line":344},{"name":"_parse_sections","description":"Method to parse document sections","line":435},{"name":"_standardize_markdown","description":"Method to standardize markdown content","line":474}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Markdown Preprocessor Module","description":"Module for preprocessing markdown content into a standardized format for rule generation","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":1,"line_end":14},
# {"name":"MarkdownPreprocessor Class","description":"Main class for markdown preprocessing","line_start":15,"line_end":486},
# {"name":"Process Method","description":"Main processing method","line_start":18,"line_end":49},
# {"name":"Create Overview Section","description":"Method to create standardized overview","line_start":50,"line_end":74},
# {"name":"Create Context Section","description":"Method to create standardized context","line_start":75,"line_end":93},
# {"name":"Create Requirements Section","description":"Method to create standardized requirements","line_start":94,"line_end":117},
# {"name":"Extract Examples","description":"Method to extract code examples","line_start":118,"line_end":159},
# {"name":"Extract Warnings","description":"Method to extract warnings and cautions","line_start":160,"line_end":204},
# {"name":"Extract Key Concepts","description":"Method to extract key concepts","line_start":205,"line_end":272},
# {"name":"Identify Directive Candidates","description":"Method to identify directive statements","line_start":273,"line_end":343},
# {"name":"Generate Standardized Markdown","description":"Method to generate standardized output","line_start":344,"line_end":434},
# {"name":"Parse Sections","description":"Method to parse markdown into sections","line_start":435,"line_end":473},
# {"name":"Standardize Markdown","description":"Method to standardize markdown format","line_start":474,"line_end":486}
# ],
# "key_elements":[
# {"name":"MarkdownPreprocessor","description":"Main preprocessor class","line":15},
# {"name":"process","description":"Main processing method","line":18},
# {"name":"_extract_examples","description":"Method to extract code examples","line":118},
# {"name":"_extract_warnings","description":"Method to extract warnings","line":160},
# {"name":"_parse_sections","description":"Method to parse document sections","line":435}
# ]
# }
# FILE_MAP_END

"""
Markdown Preprocessor Module.

This module provides functionality to preprocess markdown content into a standardized format.
"""

import re
import logging
from typing import Dict, Any, List

from .base_preprocessor import BasePreprocessor

logger = logging.getLogger(__name__)


class MarkdownPreprocessor(BasePreprocessor):
    """Preprocess markdown content into standardized format."""

    def process(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the extracted content to standardize markdown.

        Args:
            extracted_content: The extracted content to process

        Returns:
            Processed content with standardized markdown
        """
        if not self.validate_input(extracted_content):
            return {
                "status": "error",
                "message": "Invalid input for markdown preprocessor",
            }

        result = extracted_content.copy()

        # Get content
        content = extracted_content.get("content", "")

        # Parse markdown into sections
        sections = self._parse_sections(content)

        # Add sections to result
        result["sections"] = sections

        # Add standardized markdown
        result["standardized_markdown"] = self._standardize_markdown(content)

        return result

    def _create_overview_section(
        self, sections: Dict[str, str], metadata: Dict[str, Any]
    ) -> str:
        """
        Create a standardized overview section.

        Args:
            sections: Dictionary with section name as key and section content as value
            metadata: Dictionary with metadata

        Returns:
            Standardized overview content
        """
        # Try to find overview in sections with various names
        overview_sections = ["overview", "summary", "introduction", "about"]

        for section_name in overview_sections:
            if section_name in sections:
                return sections[section_name]

        # If no overview section found, try to create one from metadata
        if "description" in metadata:
            return metadata["description"]

        # If still no overview, return empty string
        return ""

    def _create_context_section(self, sections: Dict[str, str]) -> str:
        """
        Create a standardized context section.

        Args:
            sections: Dictionary with section name as key and section content as value

        Returns:
            Standardized context content
        """
        # Try to find context in sections with various names
        context_sections = ["context", "background", "motivation", "purpose"]

        for section_name in context_sections:
            if section_name in sections:
                return sections[section_name]

        return ""

    def _create_requirements_section(self, sections: Dict[str, str]) -> str:
        """
        Create a standardized requirements section.

        Args:
            sections: Dictionary with section name as key and section content as value

        Returns:
            Standardized requirements content
        """
        # Try to find requirements in sections with various names
        requirement_sections = [
            "requirements",
            "guidelines",
            "rules",
            "constraints",
            "implementation",
            "implementation guidelines",
        ]

        combined_content = []

        for section_name in requirement_sections:
            if section_name in sections:
                combined_content.append(sections[section_name])

        return "\n\n".join(combined_content)

    def _extract_examples(
        self, content: str, sections: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """
        Extract examples from content.

        Args:
            content: Full content
            sections: Dictionary with section name as key and section content as value

        Returns:
            List of examples with type and content
        """
        examples = []

        # Check for examples section
        example_sections = ["examples", "example", "usage", "usage examples"]

        example_section_content = ""
        for section_name in example_sections:
            if section_name in sections:
                example_section_content = sections[section_name]
                break

        if example_section_content:
            # Find code blocks in example section
            code_blocks = re.findall(
                r"```(?:(\w+)\n)?(.*?)```", example_section_content, re.DOTALL
            )

            for language, code in code_blocks:
                language = language or "text"
                examples.append({"type": language, "content": code.strip()})

            # If no code blocks found, treat the entire section as an example
            if not code_blocks:
                examples.append(
                    {"type": "text", "content": example_section_content.strip()}
                )

        return examples

    def _extract_warnings(self, content: str, sections: Dict[str, str]) -> List[str]:
        """
        Extract warnings from content.

        Args:
            content: Full content
            sections: Dictionary with section name as key and section content as value

        Returns:
            List of warnings
        """
        warnings = []

        # Check for warnings/dangers section
        warning_sections = ["warnings", "danger", "caution", "important"]

        warning_section_content = ""
        for section_name in warning_sections:
            if section_name in sections:
                warning_section_content = sections[section_name]
                break

        if warning_section_content:
            # Extract list items
            list_items = re.findall(
                r"(?:^|\n)[ \t]*[-*+][ \t]+(.*?)(?=\n[ \t]*[-*+][ \t]+|\n\n|$)",
                warning_section_content,
                re.DOTALL,
            )

            if list_items:
                for item in list_items:
                    warnings.append(item.strip())
            else:
                # If no list items, split by newlines and filter empty lines
                for line in warning_section_content.split("\n"):
                    line = line.strip()
                    if line:
                        warnings.append(line)

        # Also look for uppercase words like WARNING, DANGER, IMPORTANT
        warning_pattern = r"(?:^|\n)(?:WARNING|DANGER|IMPORTANT|CAUTION|NOTE)[:/][ \t]*(.*?)(?=\n\n|$)"
        warning_matches = re.findall(
            warning_pattern, content, re.IGNORECASE | re.DOTALL
        )

        for match in warning_matches:
            warnings.append(match.strip())

        return warnings

    def _extract_key_concepts(
        self, content: str, sections: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Extract key concepts from content.

        Args:
            content: Full content
            sections: Dictionary with section name as key and section content as value

        Returns:
            List of key concepts
        """
        concepts = []

        # Extract terms from heading text (likely key concepts)
        heading_pattern = r"^#{2,3}\s+(.+)$"
        headings = re.findall(heading_pattern, content, re.MULTILINE)

        for heading in headings:
            heading = heading.strip()

            # Filter out common headings that aren't concepts
            common_headings = [
                "overview",
                "introduction",
                "getting started",
                "summary",
                "conclusion",
                "examples",
                "usage",
                "installation",
            ]

            if heading.lower() not in common_headings:
                concepts.append(
                    {"term": heading, "type": "concept", "importance": "high"}
                )

        # Look for terms defined with formatting (bold, italics)
        term_pattern = r"\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|_([^_]+)_"
        formatted_terms = re.findall(term_pattern, content)

        for term_tuple in formatted_terms:
            term = next(t for t in term_tuple if t)
            term = term.strip()

            # Filter out short or common terms
            if len(term) > 3 and term.lower() not in [
                "note",
                "warning",
                "danger",
                "important",
            ]:
                # Check if term is already in concepts
                if not any(c["term"].lower() == term.lower() for c in concepts):
                    concepts.append(
                        {"term": term, "type": "terminology", "importance": "medium"}
                    )

        # Look for capitalized terms that might be important
        capitalized_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        capitalized_terms = re.findall(capitalized_pattern, content)

        for term in capitalized_terms:
            term = term.strip()

            # Filter by length and check if already in concepts
            if len(term) > 5 and not any(
                c["term"].lower() == term.lower() for c in concepts
            ):
                concepts.append(
                    {"term": term, "type": "terminology", "importance": "low"}
                )

        return concepts

    def _identify_directive_candidates(
        self, content: str, sections: Dict[str, str]
    ) -> List[Dict[str, str]]:
        """
        Identify potential directive candidates in content.

        Args:
            content: Full content
            sections: Dictionary with section name as key and section content as value

        Returns:
            List of directive candidates
        """
        directive_candidates = []

        # 1. Look for existing directive-like structures (WHEN/TO/MUST pattern)
        directive_pattern = r"(?:^|\n)(?:.*?)(WHEN|when)\s+(.*?)\s+(TO|to)\s+(.*?)\s+(MUST|SHOULD|must|should)\s+(.*?)(?=\n|$)"
        directive_matches = re.findall(directive_pattern, content, re.DOTALL)

        for match in directive_matches:
            when_word, when_context, to_word, to_purpose, must_word, directive = match
            directive_candidates.append(
                {
                    "type": "explicit",
                    "when_context": when_context.strip(),
                    "to_purpose": to_purpose.strip(),
                    "directive": directive.strip(),
                    "strength": must_word.upper(),
                    "content": f"{when_word} {when_context} {to_word} {to_purpose} {must_word} {directive}".strip(),
                }
            )

        # 2. Look for imperative sentences (likely directives)
        requirements_content = self._create_requirements_section(sections)
        if requirements_content:
            # Split into sentences
            sentences = re.split(r"(?<=[.!?])\s+", requirements_content)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Check if sentence starts with an imperative verb
                imperative_verbs = [
                    "use",
                    "ensure",
                    "avoid",
                    "follow",
                    "implement",
                    "create",
                    "define",
                ]
                if any(sentence.lower().startswith(verb) for verb in imperative_verbs):
                    directive_candidates.append(
                        {
                            "type": "imperative",
                            "content": sentence,
                            "when_context": "",
                            "to_purpose": "",
                            "directive": sentence,
                            "strength": "SHOULD",
                        }
                    )

        # 3. Look for sentences with "must", "should", "always", "never"
        modal_pattern = r"(?:^|\n)(?:.*?)(?:MUST|SHOULD|ALWAYS|NEVER|must|should|always|never)\s+(.*?)(?=\n|$)"
        modal_matches = re.findall(modal_pattern, content, re.DOTALL)

        for match in modal_matches:
            # Check if this matches an already found directive
            if any(match in candidate["content"] for candidate in directive_candidates):
                continue

            directive_candidates.append(
                {
                    "type": "modal",
                    "content": match.strip(),
                    "when_context": "",
                    "to_purpose": "",
                    "directive": match.strip(),
                    "strength": "MUST",
                }
            )

        return directive_candidates

    def _generate_standardized_markdown(
        self, preprocessed_content: Dict[str, Any]
    ) -> str:
        """
        Generate standardized markdown from preprocessed content.

        Args:
            preprocessed_content: Dictionary with preprocessed content

        Returns:
            Standardized markdown content
        """
        metadata = preprocessed_content.get("metadata", {})
        title = metadata.get("title", "Untitled Document")

        # Build standardized markdown
        markdown = f"# {title}\n\n"

        # Add overview
        overview = preprocessed_content.get("overview", "")
        if overview:
            markdown += f"## Overview\n\n{overview}\n\n"

        # Add context
        context = preprocessed_content.get("context", "")
        if context:
            markdown += f"## Context\n\n{context}\n\n"

        # Add requirements
        requirements = preprocessed_content.get("requirements", "")
        if requirements:
            markdown += f"## Requirements\n\n{requirements}\n\n"

        # Add directive candidates
        directive_candidates = preprocessed_content.get("directive_candidates", [])
        if directive_candidates:
            markdown += "## Directive Candidates\n\n"
            for i, candidate in enumerate(directive_candidates, 1):
                markdown += f"### Candidate {i}\n\n"
                markdown += f"- **Content**: {candidate.get('content', '')}\n"
                markdown += f"- **Type**: {candidate.get('type', '')}\n"

                when_context = candidate.get("when_context", "")
                if when_context:
                    markdown += f"- **When Context**: {when_context}\n"

                to_purpose = candidate.get("to_purpose", "")
                if to_purpose:
                    markdown += f"- **To Purpose**: {to_purpose}\n"

                directive = candidate.get("directive", "")
                if directive:
                    markdown += f"- **Directive**: {directive}\n"

                strength = candidate.get("strength", "")
                if strength:
                    markdown += f"- **Strength**: {strength}\n"

                markdown += "\n"

        # Add examples
        examples = preprocessed_content.get("examples", [])
        if examples:
            markdown += "## Examples\n\n"
            for i, example in enumerate(examples, 1):
                example_type = example.get("type", "text")
                example_content = example.get("content", "")

                markdown += f"### Example {i}\n\n"
                markdown += f"```{example_type}\n{example_content}\n```\n\n"

        # Add warnings
        warnings = preprocessed_content.get("warnings", [])
        if warnings:
            markdown += "## Warnings\n\n"
            for warning in warnings:
                markdown += f"- {warning}\n"
            markdown += "\n"

        # Add concepts
        concepts = preprocessed_content.get("concepts", [])
        if concepts:
            markdown += "## Key Concepts\n\n"
            for concept in concepts:
                term = concept.get("term", "")
                concept_type = concept.get("type", "")
                importance = concept.get("importance", "")

                markdown += (
                    f"- **{term}** (Type: {concept_type}, Importance: {importance})\n"
                )
            markdown += "\n"

        return markdown.strip()

    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse markdown content into sections.

        Args:
            content: Markdown content to parse

        Returns:
            List of sections with title and content
        """
        sections = []

        # Split content by headers
        header_pattern = r"^(#{1,6})\s+(.+)$"
        lines = content.split("\n")
        current_section = {"title": "Introduction", "level": 0, "content": ""}

        for line in lines:
            header_match = re.match(header_pattern, line)

            if header_match:
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section.copy())

                # Create new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {"title": title, "level": level, "content": ""}
            else:
                # Add line to current section
                current_section["content"] += line + "\n"

        # Add the last section
        if current_section["content"].strip():
            sections.append(current_section.copy())

        return sections

    def _standardize_markdown(self, content: str) -> str:
        """
        Standardize markdown content.

        Args:
            content: Markdown content to standardize

        Returns:
            Standardized markdown content
        """
        # This is a simple implementation that just returns the original content
        # In a real implementation, this would standardize headers, lists, etc.
        return content
