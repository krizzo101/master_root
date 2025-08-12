# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Transformation Manager Module","description":"This module provides functionality for coordinating transformations from preprocessed document content to rule-ready formats.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Import necessary modules and libraries for the transformation manager.","line_start":3,"line_end":14},{"name":"TransformationManager Class","description":"Class that coordinates transformations from preprocessed content to rule-ready formats.","line_start":15,"line_end":368}],"key_elements":[{"name":"TransformationManager","description":"Class responsible for managing transformations.","line":17},{"name":"__init__","description":"Constructor for initializing the transformation manager.","line":25},{"name":"transform","description":"Method to transform content to rule-ready format.","line":39},{"name":"register_transformer","description":"Method to register a transformer for a specific document type.","line":168},{"name":"get_supported_types","description":"Method to get a list of supported document types.","line":179},{"name":"_extract_title","description":"Method to extract title from preprocessed content.","line":188},{"name":"_extract_description","description":"Method to extract description from preprocessed content.","line":206},{"name":"_create_overview","description":"Method to create overview section from preprocessed content.","line":230},{"name":"_create_context","description":"Method to create context section from preprocessed content.","line":254},{"name":"_create_requirements","description":"Method to create requirements section from preprocessed content.","line":282},{"name":"_extract_examples","description":"Method to extract examples from preprocessed content.","line":311},{"name":"_extract_warnings","description":"Method to extract warnings from preprocessed content.","line":351}]}
"""
# FILE_MAP_END

"""
Transformation Manager Module.

This module provides functionality for coordinating transformations
from preprocessed document content to rule-ready formats.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import re

from .markdown_to_rule import MarkdownToRuleTransformer

logger = logging.getLogger(__name__)


class TransformationManager:
    """
    Coordinate transformations from preprocessed content to rule-ready formats.

    This class manages the selection and application of appropriate transformers
    based on document type and desired output format.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the transformation manager.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.transformers = {"markdown": MarkdownToRuleTransformer(config)}

        logger.info("Initialized transformation manager")

    def transform(
        self,
        content: Dict[str, Any],
        taxonomy: Optional[Dict[str, Any]] = None,
        use_llm: bool = False,
        llm_orchestrator=None,
    ) -> Dict[str, Any]:
        """
        Transform content to rule-ready format.

        Args:
            content: Preprocessed document content
            taxonomy: Optional taxonomy information
            use_llm: Whether to use LLM for enhanced transformation
            llm_orchestrator: LLM orchestrator instance

        Returns:
            Transformed content ready for rule generation
        """
        if not content:
            logger.error("No content provided for transformation")
            return {"status": "error", "error": "No content provided"}

        document_type = content.get("document_type", "").lower()

        if not document_type:
            # Try to infer document type from file extension
            file_path = content.get("file_path", "")
            _, ext = os.path.splitext(file_path)

            if ext.lower() in [".md", ".markdown"]:
                document_type = "markdown"
            elif ext.lower() in [".rst", ".rest"]:
                document_type = "rst"
            elif ext.lower() in [".txt"]:
                document_type = "text"
            elif ext.lower() in [".html", ".htm"]:
                document_type = "html"
            else:
                document_type = "text"  # Default

            logger.info(f"Inferred document type: {document_type}")

        # Select transformer
        transformer = self.transformers.get(document_type)
        if not transformer:
            logger.warning(
                f"No transformer available for document type: {document_type}"
            )

            # Fall back to markdown transformer
            transformer = self.transformers.get("markdown")
            if not transformer:
                logger.error("No fallback transformer available")
                return {
                    "status": "error",
                    "error": f"No transformer available for document type: {document_type}",
                }

        # Use LLM-enhanced transformation if requested and available
        if use_llm and llm_orchestrator:
            logger.info("Using LLM-enhanced transformation")

            try:
                # Generate rule content using LLM
                rule_type = "standard"  # Can be overridden based on document analysis

                # Determine rule type from taxonomy if available
                if taxonomy:
                    # Check if this is a parent rule based on concepts
                    has_child_concepts = False
                    for hierarchy in taxonomy.get("hierarchies", []):
                        if "parent" in hierarchy and "child" in hierarchy:
                            has_child_concepts = True
                            break

                    if has_child_concepts:
                        rule_type = "parent"

                # Use LLM to generate rule
                llm_result = llm_orchestrator.generate_rule(
                    doc_content=content, taxonomy=taxonomy or {}, rule_type=rule_type
                )

                if llm_result and "content" in llm_result and "error" not in llm_result:
                    # Create transformed content with LLM-generated rule
                    transformed = {
                        "rule_content": llm_result["content"],
                        "document_type": document_type,
                        "source_path": content.get("file_path", ""),
                        "source_document": content,
                        "taxonomy": taxonomy,
                        "llm_generated": True,
                        "status": "success",  # Add status field for successful transformation
                    }

                    # Extract rule ID and name if possible
                    rule_content = llm_result["content"]
                    first_line = rule_content.split("\n")[0] if rule_content else ""

                    if ":" in first_line:
                        id_name = first_line.split(":")[0].strip()
                        if "-" in id_name:
                            parts = id_name.split("-", 1)
                            transformed["rule_id"] = parts[0]
                            transformed["rule_name"] = "-".join(parts[1:])

                    logger.info("Successfully transformed content using LLM")
                    return transformed
                else:
                    error_msg = (
                        llm_result.get("error", "Unknown error in LLM generation")
                        if isinstance(llm_result, dict)
                        else "Failed LLM transformation"
                    )
                    logger.error(f"LLM transformation failed: {error_msg}")
                    return {"status": "error", "error": error_msg}

            except Exception as e:
                logger.error(f"Error in LLM transformation: {str(e)}")
                # Fall back to standard transformation
                logger.info("Falling back to standard transformation")

        # Use standard transformation
        logger.info(f"Transforming content using {document_type} transformer")
        result = transformer.transform(content, taxonomy)

        # Add status field to the result
        if isinstance(result, dict):
            if "error" in result:
                result["status"] = "error"
            else:
                result["status"] = "success"

        return result

    def register_transformer(self, document_type: str, transformer):
        """
        Register a transformer for a specific document type.

        Args:
            document_type: Type of document (e.g., markdown, rst)
            transformer: Transformer instance
        """
        self.transformers[document_type.lower()] = transformer
        logger.info(f"Registered transformer for document type: {document_type}")

    def get_supported_types(self) -> List[str]:
        """
        Get list of supported document types.

        Returns:
            List of supported document types
        """
        return list(self.transformers.keys())

    def _extract_title(self, preprocessed_content: Dict[str, Any]) -> str:
        """
        Extract title from preprocessed content.

        Args:
            preprocessed_content: Preprocessed content

        Returns:
            Extracted title
        """
        # Try to get title from sections
        sections = preprocessed_content.get("sections", [])
        if sections and sections[0]["level"] == 1:
            return sections[0]["title"]

        # Fallback to metadata
        return preprocessed_content.get("metadata", {}).get("title", "Untitled Rule")

    def _extract_description(self, preprocessed_content: Dict[str, Any]) -> str:
        """
        Extract description from preprocessed content.

        Args:
            preprocessed_content: Preprocessed content

        Returns:
            Extracted description
        """
        # Try to get description from overview section
        sections = preprocessed_content.get("sections", [])
        for section in sections:
            if section["title"].lower() == "overview":
                return section["content"].strip()

        # Fallback to first paragraph of content
        content = preprocessed_content.get("content", "")
        paragraphs = content.split("\n\n")
        if len(paragraphs) > 1:
            return paragraphs[1].strip()

        return ""

    def _create_overview(self, preprocessed_content: Dict[str, Any]) -> str:
        """
        Create overview section from preprocessed content.

        Args:
            preprocessed_content: Preprocessed content

        Returns:
            Overview section content
        """
        # Try to get overview from sections
        sections = preprocessed_content.get("sections", [])
        for section in sections:
            if section["title"].lower() == "overview":
                return section["content"].strip()

        # Fallback to first paragraph of content
        content = preprocessed_content.get("content", "")
        paragraphs = content.split("\n\n")
        if len(paragraphs) > 1:
            return paragraphs[1].strip()

        return ""

    def _create_context(self, preprocessed_content: Dict[str, Any]) -> str:
        """
        Create context section from preprocessed content.

        Args:
            preprocessed_content: Preprocessed content

        Returns:
            Context section content
        """
        # Try to find context-related sections
        context_sections = ["context", "background", "introduction"]
        sections = preprocessed_content.get("sections", [])

        for section in sections:
            if section["title"].lower() in context_sections:
                return section["content"].strip()

        # If no specific context section, create one from concepts
        concepts = preprocessed_content.get("concepts", [])
        if concepts:
            context = "This rule addresses the following concepts:\n\n"
            for concept in concepts:
                context += f"- {concept.get('term', '')}\n"
            return context

        return ""

    def _create_requirements(self, preprocessed_content: Dict[str, Any]) -> str:
        """
        Create requirements section from preprocessed content.

        Args:
            preprocessed_content: Preprocessed content

        Returns:
            Requirements section content
        """
        # Try to find requirements-related sections
        requirement_sections = ["requirements", "guidelines", "rules", "standards"]
        sections = preprocessed_content.get("sections", [])

        requirements = ""
        for section in sections:
            if section["title"].lower() in requirement_sections:
                requirements += section["content"].strip() + "\n\n"

        # If no specific requirements section, create one from directives
        if not requirements:
            directives = preprocessed_content.get("directive_candidates", [])
            if directives:
                requirements = "The following requirements must be followed:\n\n"
                for directive in directives:
                    requirements += f"- {directive.get('content', '')}\n"

        return requirements.strip()

    def _extract_examples(
        self, preprocessed_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract examples from preprocessed content.

        Args:
            preprocessed_content: Preprocessed content

        Returns:
            List of examples
        """
        examples = []

        # Try to find examples section
        sections = preprocessed_content.get("sections", [])
        for section in sections:
            if section["title"].lower() == "examples":
                # Extract code blocks from the section
                code_blocks = re.findall(
                    r"```(\w*)\n(.*?)```", section["content"], re.DOTALL
                )
                for language, code in code_blocks:
                    examples.append(
                        {"language": language or "text", "content": code.strip()}
                    )

        # If no examples found, look for code blocks in the content
        if not examples:
            content = preprocessed_content.get("content", "")
            code_blocks = re.findall(r"```(\w*)\n(.*?)```", content, re.DOTALL)

            # Filter out code blocks that are likely examples (look for Python code patterns)
            for language, code in code_blocks:
                # Python code-specific patterns
                if language.lower() == "python" or re.search(
                    r"\bdef\b|\bclass\b|import\s+|=\s*", code
                ):
                    examples.append(
                        {"language": language or "python", "content": code.strip()}
                    )

        return examples

    def _extract_warnings(self, preprocessed_content: Dict[str, Any]) -> List[str]:
        """
        Extract warnings from preprocessed content.

        Args:
            preprocessed_content: Preprocessed content

        Returns:
            List of warnings
        """
        warnings = []

        # Try to find warnings section
        sections = preprocessed_content.get("sections", [])
        for section in sections:
            if section["title"].lower() == "warnings":
                # Extract bullet points from the section
                bullet_points = re.findall(r"[-*]\s+(.*?)(?:\n|$)", section["content"])
                warnings.extend([point.strip() for point in bullet_points])

        return warnings
