# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Concept Extractor Module","description":"Module for extracting key concepts from documentation content","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":1,"line_end":15},{"name":"ConceptExtractor Class","description":"Main class for concept extraction","line_start":16,"line_end":305},{"name":"Preprocess Method","description":"Main method to extract concepts","line_start":19,"line_end":69},{"name":"Extract from Headings","description":"Method to extract concepts from headings","line_start":70,"line_end":105},{"name":"Extract from Formatted Text","description":"Method to extract concepts from formatted text","line_start":106,"line_end":136},{"name":"Extract from Capitalized Phrases","description":"Method to extract concepts from capitalized phrases","line_start":137,"line_end":166},{"name":"Extract from Repeated Phrases","description":"Method to extract concepts from repeated phrases","line_start":167,"line_end":214},{"name":"Deduplicate Concepts","description":"Method to remove duplicate concepts","line_start":215,"line_end":247},{"name":"Validate Input","description":"Method to validate input data","line_start":248,"line_end":270},{"name":"Process Method","description":"Alternative processing method","line_start":271,"line_end":305}],"key_elements":[{"name":"ConceptExtractor","description":"Main class for concept extraction","line":16},{"name":"preprocess","description":"Main processing method","line":19},{"name":"_extract_from_headings","description":"Method to extract from headings","line":70},{"name":"_deduplicate_concepts","description":"Method to remove duplicates","line":215},{"name":"validate_input","description":"Method to validate input data","line":273},{"name":"process","description":"Method to process extracted content","line":296}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Concept Extractor Module","description":"Module for extracting key concepts from documentation content","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":1,"line_end":15},
# {"name":"ConceptExtractor Class","description":"Main class for concept extraction","line_start":16,"line_end":305},
# {"name":"Preprocess Method","description":"Main method to extract concepts","line_start":19,"line_end":69},
# {"name":"Extract from Headings","description":"Method to extract concepts from headings","line_start":70,"line_end":105},
# {"name":"Extract from Formatted Text","description":"Method to extract concepts from formatted text","line_start":106,"line_end":136},
# {"name":"Extract from Capitalized Phrases","description":"Method to extract concepts from capitalized phrases","line_start":137,"line_end":166},
# {"name":"Extract from Repeated Phrases","description":"Method to extract concepts from repeated phrases","line_start":167,"line_end":214},
# {"name":"Deduplicate Concepts","description":"Method to remove duplicate concepts","line_start":215,"line_end":247},
# {"name":"Validate Input","description":"Method to validate input data","line_start":248,"line_end":270},
# {"name":"Process Method","description":"Alternative processing method","line_start":271,"line_end":305}
# ],
# "key_elements":[
# {"name":"ConceptExtractor","description":"Main class for concept extraction","line":16},
# {"name":"preprocess","description":"Main processing method","line":19},
# {"name":"_extract_from_headings","description":"Method to extract from headings","line":70},
# {"name":"_deduplicate_concepts","description":"Method to remove duplicates","line":215}
# ]
# }
# FILE_MAP_END

"""
Concept Extractor Module.

This module provides functionality to extract key concepts from content.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from collections import Counter

from .base_preprocessor import BasePreprocessor

logger = logging.getLogger(__name__)


class ConceptExtractor(BasePreprocessor):
    """Extract key concepts from content."""

    def preprocess(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key concepts from content.

        Args:
            extracted_content: Extracted content from extractor

        Returns:
            Dictionary with extracted concepts
        """
        # Validate input
        if not self.validate_input(extracted_content):
            logger.error("Invalid input for concept extractor")
            return {"status": "error", "error": "Invalid input for concept extractor"}

        # Get content and sections
        content = extracted_content.get("content", "")
        sections = extracted_content.get("sections", {})

        # Extract core concepts using various techniques
        concepts = []

        # Extract from headings
        heading_concepts = self._extract_from_headings(content)
        concepts.extend(heading_concepts)

        # Extract from formatted text (bold, italic)
        formatted_concepts = self._extract_from_formatted_text(content)
        concepts.extend(formatted_concepts)

        # Extract from capitalized phrases
        capitalized_concepts = self._extract_from_capitalized_phrases(content)
        concepts.extend(capitalized_concepts)

        # Extract from repeated phrases
        repeated_concepts = self._extract_from_repeated_phrases(content)
        concepts.extend(repeated_concepts)

        # Remove duplicates while preserving the highest importance
        unique_concepts = self._deduplicate_concepts(concepts)

        # Update the extracted content
        result = extracted_content.copy()
        result["concepts"] = unique_concepts
        result["status"] = "success"

        return result

    def _extract_from_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract concepts from headings.

        Args:
            content: Content to extract concepts from

        Returns:
            List of concepts extracted from headings
        """
        concepts = []

        # Extract level 2 and 3 headings
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
                "warning",
                "context",
                "prerequisites",
                "requirements",
                "dependencies",
            ]

            if heading.lower() not in common_headings:
                concepts.append(
                    {
                        "term": heading,
                        "type": "concept",
                        "importance": "high",
                        "source": "heading",
                    }
                )

        return concepts

    def _extract_from_formatted_text(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract concepts from formatted text (bold, italic).

        Args:
            content: Content to extract concepts from

        Returns:
            List of concepts extracted from formatted text
        """
        concepts = []

        # Look for terms defined with formatting (bold, italics)
        term_pattern = r"\*\*([^*]+)\*\*|\*([^*]+)\*|__([^_]+)__|_([^_]+)_"
        formatted_terms = re.findall(term_pattern, content)

        for term_tuple in formatted_terms:
            term = next((t for t in term_tuple if t), "")
            term = term.strip()

            # Filter out short or common terms
            if len(term) > 3 and term.lower() not in [
                "note",
                "warning",
                "danger",
                "important",
            ]:
                concepts.append(
                    {
                        "term": term,
                        "type": "terminology",
                        "importance": "medium",
                        "source": "formatting",
                    }
                )

        return concepts

    def _extract_from_capitalized_phrases(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract concepts from capitalized phrases.

        Args:
            content: Content to extract concepts from

        Returns:
            List of concepts extracted from capitalized phrases
        """
        concepts = []

        # Look for capitalized terms that might be important
        capitalized_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        capitalized_terms = re.findall(capitalized_pattern, content)

        for term in capitalized_terms:
            term = term.strip()

            # Filter by length
            if len(term) > 5:
                concepts.append(
                    {
                        "term": term,
                        "type": "terminology",
                        "importance": "medium",
                        "source": "capitalization",
                    }
                )

        return concepts

    def _extract_from_repeated_phrases(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract concepts from repeated phrases.

        Args:
            content: Content to extract concepts from

        Returns:
            List of concepts extracted from repeated phrases
        """
        concepts = []

        # Tokenize content into sentences
        sentences = re.split(r"[.!?]\s+", content)

        # Extract phrases (2-3 words)
        phrases = []
        for sentence in sentences:
            words = sentence.split()
            for i in range(len(words) - 1):
                if i < len(words) - 2:
                    # 3-word phrase
                    phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                    phrases.append(phrase.lower())

                # 2-word phrase
                phrase = f"{words[i]} {words[i+1]}"
                phrases.append(phrase.lower())

        # Count phrases
        phrase_counter = Counter(phrases)

        # Select repeated phrases (frequency > 2)
        for phrase, count in phrase_counter.items():
            if count > 2 and len(phrase) > 5:
                # Check if it's a meaningful phrase (not common stopwords)
                stopwords = [
                    "of the",
                    "in the",
                    "to the",
                    "on the",
                    "and the",
                    "is a",
                    "as a",
                ]
                if not any(stopword in phrase for stopword in stopwords):
                    concepts.append(
                        {
                            "term": phrase,
                            "type": "phrase",
                            "importance": "low",
                            "source": "repetition",
                            "frequency": count,
                        }
                    )

        return concepts

    def _deduplicate_concepts(
        self, concepts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate concepts while preserving the highest importance.

        Args:
            concepts: List of concepts

        Returns:
            Deduplicated list of concepts
        """
        if not concepts:
            return []

        # Map importance to numeric values
        importance_map = {"high": 3, "medium": 2, "low": 1}

        # Group concepts by lowercase term
        grouped_concepts = {}
        for concept in concepts:
            term = concept["term"].lower()
            importance = concept.get("importance", "low")
            importance_value = importance_map.get(importance, 0)

            if term not in grouped_concepts or importance_value > importance_map.get(
                grouped_concepts[term]["importance"], 0
            ):
                grouped_concepts[term] = concept

        # Convert back to list
        return list(grouped_concepts.values())

    def validate_input(self, extracted_content: Dict[str, Any]) -> bool:
        """
        Validate the input extracted content.

        Args:
            extracted_content: Extracted content to validate

        Returns:
            True if the content is valid, False otherwise
        """
        # Check for required fields
        if not extracted_content:
            return False

        if extracted_content.get("status") != "success":
            return False

        # For concept extraction, we need either content or sections
        if "content" not in extracted_content and "sections" not in extracted_content:
            return False

        return True

    def process(self, extracted_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the extracted content to identify concepts.

        Args:
            extracted_content: The extracted content to process

        Returns:
            Processed content with identified concepts
        """
        if not self.validate_input(extracted_content):
            return {
                "status": "error",
                "message": "Invalid input for concept extraction",
            }

        result = extracted_content.copy()

        # Extract text from content or sections
        text = ""
        if "content" in extracted_content:
            text = extracted_content["content"]
        elif "sections" in extracted_content:
            # Concatenate all section content
            for section in extracted_content["sections"]:
                if "content" in section:
                    text += section["content"] + "\n\n"

        # Extract concepts from the text
        concepts = self._extract_concepts(text)

        # Add concepts to the result
        result["concepts"] = concepts

        return result
