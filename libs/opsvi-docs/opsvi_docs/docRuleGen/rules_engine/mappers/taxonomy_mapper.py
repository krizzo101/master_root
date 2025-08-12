# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Taxonomy Mapper Module","description":"Module for mapping content to taxonomy categories","last_updated":"2025-03-12","type":"code"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Module imports","line_start":22,"line_end":28},{"name":"TaxonomyMapper Class","description":"Main class for taxonomy mapping","line_start":31,"line_end":132},{"name":"map_to_categories Method","description":"Main method to map content to categories","line_start":42,"line_end":97},{"name":"flatten_content Helper Function","description":"Helper function to flatten complex data structures into a string representation","line_start":75,"line_end":97},{"name":"_match_keywords Method","description":"Method to match keywords with content text and calculate a relevance score","line_start":209,"line_end":266},{"name":"_extract_category_keywords Method","description":"Extract keywords from taxonomy categories","line_start":266,"line_end":323}],"key_elements":[{"name":"TaxonomyMapper","description":"Main taxonomy mapping class","line":35},{"name":"__init__","description":"Constructor for initializing the taxonomy mapper","line":40},{"name":"map_to_categories","description":"Content to taxonomy mapping method","line":55},{"name":"_match_keywords","description":"Method to match keywords with content text","line":209},{"name":"_extract_category_keywords","description":"Method to extract keywords from taxonomy categories","line":266}]}
"""
# FILE_MAP_END

# FILE_MAP_BEGIN
# {
# "file_metadata":{"title":"Taxonomy Mapper Module","description":"Module for mapping content to taxonomy categories","last_updated":"2023-03-10","type":"code"},
# "ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.",
# "sections":[
# {"name":"Imports","description":"Module imports","line_start":22,"line_end":28},
# {"name":"TaxonomyMapper Class","description":"Main class for taxonomy mapping","line_start":31,"line_end":132},
# {"name":"map_to_categories Method","description":"Main method to map content to categories","line_start":42,"line_end":97},
# {"name":"match_keywords Method","description":"Method to match keywords with content","line_start":99,"line_end":132}
# ],
# "key_elements":[
# {"name":"TaxonomyMapper","description":"Main taxonomy mapping class","line":31},
# {"name":"map_to_categories","description":"Content to taxonomy mapping method","line":42}
# ]
# }
# FILE_MAP_END

"""
Taxonomy Mapper Module for Documentation Rule Generator.

This module maps content to taxonomy categories.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TaxonomyMapper:
    """
    Maps content to taxonomy categories.
    """

    def __init__(self, taxonomy: Dict[str, Any] = None):
        """
        Initialize the taxonomy mapper.

        Args:
            taxonomy: Taxonomy dictionary
        """
        self.taxonomy = taxonomy

        # Extract category keywords
        self.category_keywords = self._extract_category_keywords()

        logger.info("Initialized TaxonomyMapper")
        logger.debug(
            f"Taxonomy categories: {len(self.category_keywords.keys()) if self.category_keywords else 0}"
        )

    def map_to_categories(self, content: Dict[str, Any]) -> Dict[str, float]:
        """
        Map content to taxonomy categories.

        Args:
            content: Extracted content dictionary containing text and metadata

        Returns:
            Dictionary mapping category IDs to confidence scores (normalized between 0-1)
        """
        file_path = content.get("file_path", "unknown")
        logger.info(f"Mapping content from {file_path} to taxonomy categories")

        # Return empty result if no taxonomy
        if not self.taxonomy or not self.category_keywords:
            logger.warning("No taxonomy available for mapping")
            return {}

        try:
            # Helper function to convert complex objects to string representation
            def flatten_content(obj, prefix="", max_depth=10, current_depth=0):
                """
                Recursively flatten complex data structures (dicts, lists) into a string representation.

                Args:
                    obj: The object to flatten (dict, list, or primitive type)
                    prefix: String prefix to prepend to each item (used in recursion)
                    max_depth: Maximum recursion depth to prevent stack overflow
                    current_depth: Current recursion depth (used internally)

                Returns:
                    String representation of the object with keys and values
                """
                # Early return for None
                if obj is None:
                    return ""

                # Prevent excessive recursion
                if current_depth >= max_depth:
                    return f"{prefix}[complex_structure] "

                result = ""

                # Handle dictionary content (common in YAML/JSON)
                if isinstance(obj, dict):
                    # Empty dict check
                    if not obj:
                        return f"{prefix}[empty_dict] "

                    # Process each key-value pair
                    for key, value in obj.items():
                        # Skip None keys
                        if key is None:
                            continue

                        key_str = str(key).strip()

                        # Handle nested structures recursively
                        if isinstance(value, (dict, list)):
                            result += flatten_content(
                                value,
                                f"{prefix}{key_str} ",
                                max_depth,
                                current_depth + 1,
                            )
                        else:
                            # Handle primitive values
                            if value is not None:
                                result += f"{prefix}{key_str} {value} "
                            else:
                                result += f"{prefix}{key_str} "

                # Handle list content
                elif isinstance(obj, list):
                    # Empty list check
                    if not obj:
                        return f"{prefix}[empty_list] "

                    # Process each item
                    for item in obj:
                        # Handle nested structures recursively
                        if isinstance(item, (dict, list)):
                            result += flatten_content(
                                item, prefix, max_depth, current_depth + 1
                            )
                        else:
                            # Handle primitive values
                            if item is not None:
                                result += f"{prefix}{item} "

                # Handle primitive types
                else:
                    result += f"{prefix}{obj} "

                return result

            # Extract text for matching
            text = ""

            # Add content
            if "content" in content:
                # Handle case where content is a complex object (dict, list, etc.)
                if isinstance(content["content"], (dict, list)):
                    text += flatten_content(content["content"])
                else:
                    # Handle string content
                    text += str(content["content"]) + " "

            # Add title
            if "title" in content:
                if content["title"]:
                    text += str(content["title"]) + " "

            # Add concepts
            if "concepts" in content and isinstance(content["concepts"], list):
                for concept in content["concepts"]:
                    if (
                        isinstance(concept, dict)
                        and "term" in concept
                        and concept["term"]
                    ):
                        text += str(concept["term"]) + " "

            # Early return if no text to match
            if not text.strip():
                logger.warning(f"No text content to match for {file_path}")
                return {}

            # Normalize text - convert to lowercase and replace multiple spaces with single space
            text = re.sub(r"\s+", " ", text.lower()).strip()

            # Match against each category
            category_scores = {}

            for category_id, keywords in self.category_keywords.items():
                # Skip categories with no keywords
                if not keywords:
                    continue

                score = self._match_keywords(text, keywords)

                # Only include categories with non-zero scores
                if score > 0.0:
                    category_scores[category_id] = score

            # Early return if no matches
            if not category_scores:
                logger.info(f"No category matches found for {file_path}")
                return {}

            # Normalize scores
            total_score = sum(category_scores.values())
            if total_score > 0:
                for category_id in category_scores:
                    category_scores[category_id] /= total_score

            logger.info(f"Mapped content to {len(category_scores)} categories")
            return category_scores

        except Exception as e:
            logger.error(f"Error mapping content to categories: {str(e)}")
            return {}

    def _match_keywords(self, text: str, keywords: List[str]) -> float:
        """
        Match keywords with content text and calculate a relevance score.

        The method uses multiple scoring strategies:
        1. Exact matches: Words that match exactly (with word boundaries)
        2. Partial matches: Words that appear as substrings
        3. Word proximity: Multiple keywords appearing close together

        Args:
            text: Content text (should be pre-normalized to lowercase)
            keywords: List of keywords to match against

        Returns:
            Float representing the match score (higher = better match)
        """
        # Early returns for edge cases
        if not text or not keywords:
            return 0.0

        # Count keyword occurrences
        total_score = 0.0
        matched_keywords = set()

        for keyword in keywords:
            if not keyword or len(keyword) < 3:  # Skip very short keywords
                continue

            keyword = keyword.lower()  # Ensure keyword is lowercase

            # Exact matches get higher score
            exact_pattern = rf"\b{re.escape(keyword)}\b"
            exact_count = len(re.findall(exact_pattern, text))

            if exact_count > 0:
                # Score is higher for exact matches
                keyword_score = exact_count * 2.0
                total_score += keyword_score
                matched_keywords.add(keyword)
            else:
                # Partial matches get lower score
                partial_pattern = rf"{re.escape(keyword)}"
                partial_count = len(re.findall(partial_pattern, text))

                if partial_count > 0:
                    keyword_score = partial_count * 0.5
                    total_score += keyword_score
                    matched_keywords.add(keyword)

        # Apply bonus for matching multiple distinct keywords
        if len(matched_keywords) > 1:
            # Bonus increases with more matched keywords
            diversity_bonus = min(len(matched_keywords) * 0.5, 3.0)
            total_score += diversity_bonus

        return total_score

    def _extract_category_keywords(self) -> Dict[str, List[str]]:
        """
        Extract keywords from taxonomy categories.

        Returns:
            Dictionary mapping category IDs to keyword lists
        """
        keywords = {}

        if not self.taxonomy:
            return keywords

        try:
            # Process each category
            for category in self.taxonomy.get("categories", []):
                category_id = category.get("name", "")
                if not category_id:
                    continue

                # Extract keywords from category name and description
                category_keywords = []

                # Add category name words
                name_words = re.findall(r"\b\w+\b", category.get("name", "").lower())
                category_keywords.extend([w for w in name_words if len(w) > 3])

                # Add description words
                desc_words = re.findall(
                    r"\b\w+\b", category.get("description", "").lower()
                )
                category_keywords.extend([w for w in desc_words if len(w) > 3])

                # Process each rule in the category
                for rule in category.get("rules", []):
                    rule_id = rule.get("id", "")
                    if not rule_id:
                        continue

                    # Create rule keywords
                    rule_keywords = []

                    # Add rule name words
                    name_words = re.findall(r"\b\w+\b", rule.get("name", "").lower())
                    rule_keywords.extend([w for w in name_words if len(w) > 3])

                    # Add description words
                    desc_words = re.findall(
                        r"\b\w+\b", rule.get("description", "").lower()
                    )
                    rule_keywords.extend([w for w in desc_words if len(w) > 3])

                    # Add to keywords
                    keywords[rule_id] = rule_keywords

                # Add category keywords
                keywords[category_id] = category_keywords

            return keywords

        except Exception as e:
            logger.error(f"Error extracting category keywords: {str(e)}")
            return {}
