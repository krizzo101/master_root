"""AI optimization utilities for Project Mapper.

This module provides functionality for optimizing map outputs for AI model
consumption, including tokenization estimation and optimization strategies.
"""

import logging
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Union

from proj_mapper.models.relationship import RelationshipType
from proj_mapper.output.config import GeneratorConfig

# Configure logging
logger = logging.getLogger(__name__)


class TokenizationEstimator:
    """Estimator for token counts in AI models.
    
    This class provides methods for estimating the number of tokens that
    different data structures will consume in AI models.
    """
    
    def __init__(self, chars_per_token: float = 4.0):
        """Initialize the token estimator.
        
        Args:
            chars_per_token: Average characters per token (GPT models average ~4)
        """
        self.chars_per_token = chars_per_token
    
    def estimate_tokens(self, data: Any) -> int:
        """Estimate the number of tokens in the data.
        
        Args:
            data: The data to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if data is None:
            return 0
            
        if isinstance(data, str):
            return self._estimate_string_tokens(data)
        elif isinstance(data, (int, float, bool)):
            return 1
        elif isinstance(data, Mapping):
            return self._estimate_dict_tokens(data)
        elif isinstance(data, Sequence) and not isinstance(data, str):
            return self._estimate_sequence_tokens(data)
        else:
            # For custom objects, convert to string and estimate
            return self._estimate_string_tokens(str(data))
    
    def _estimate_string_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a string.
        
        Args:
            text: The string to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Basic estimation based on character count
        token_count = len(text) / self.chars_per_token
        
        # Add extra tokens for newlines and special characters
        newline_count = text.count('\n')
        token_count += newline_count * 0.5  # Newlines often consume extra tokens
        
        # Add extra tokens for code blocks, which are often tokenized differently
        code_blocks = re.findall(r'```[^`]*```', text)
        for block in code_blocks:
            # Code blocks often have more tokens due to special characters
            token_count += len(block) * 0.1
        
        return max(1, int(token_count))
    
    def _estimate_dict_tokens(self, data: Mapping) -> int:
        """Estimate the number of tokens in a dictionary.
        
        Args:
            data: The dictionary to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Start with tokens for braces and commas
        token_count = 2  # { and }
        
        # Add tokens for each key-value pair
        for key, value in data.items():
            # Each key and colon
            token_count += self.estimate_tokens(str(key)) + 1  # +1 for the colon
            # Each value and comma
            token_count += self.estimate_tokens(value) + 1  # +1 for the comma
        
        return max(2, int(token_count))
    
    def _estimate_sequence_tokens(self, data: Sequence) -> int:
        """Estimate the number of tokens in a sequence.
        
        Args:
            data: The sequence to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Start with tokens for brackets and commas
        token_count = 2  # [ and ]
        
        # Add tokens for each item
        for item in data:
            token_count += self.estimate_tokens(item) + 1  # +1 for the comma
        
        return max(2, int(token_count))


class AIOptimizer:
    """Optimizer for AI model consumption.
    
    This class provides methods for optimizing map structures to be more
    efficiently consumed by AI models.
    """
    
    def __init__(self, config: Optional[GeneratorConfig] = None):
        """Initialize the AI optimizer.
        
        Args:
            config: The generator configuration
        """
        self.config = config or GeneratorConfig()
        self.token_estimator = TokenizationEstimator()
    
    def optimize_map(self, map_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a map structure for AI consumption.
        
        Args:
            map_structure: The map structure to optimize
            
        Returns:
            The optimized map structure
        """
        logger.info("Optimizing map for AI consumption")
        
        # Create a copy of the map to avoid modifying the original
        optimized = map_structure.copy()
        
        # Apply optimizations based on configuration
        if self.config.include_code:
            optimized = self._optimize_code_elements(optimized)
        
        if self.config.include_documentation:
            optimized = self._optimize_documentation_elements(optimized)
        
        # Always optimize relationships
        optimized = self._optimize_relationships(optimized)
        
        # Add AI-specific metadata
        optimized = self._add_ai_metadata(optimized)
        
        # Estimate total tokens
        total_tokens = self.token_estimator.estimate_tokens(optimized)
        logger.info(f"Optimized map estimated size: {total_tokens} tokens")
        
        # Update statistics
        if "statistics" not in optimized:
            optimized["statistics"] = {}
        
        optimized["statistics"]["estimated_tokens"] = total_tokens
        
        return optimized
    
    def _optimize_code_elements(self, map_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize code elements for AI consumption.
        
        Args:
            map_structure: The map structure to optimize
            
        Returns:
            The optimized map structure
        """
        code_elements = map_structure.get("code_elements", [])
        
        if not code_elements:
            return map_structure
        
        optimized_elements = []
        
        for element in code_elements:
            # Create a copy of the element
            optimized = element.copy()
            
            # Truncate very long content if present
            if "content" in optimized and isinstance(optimized["content"], str):
                content = optimized["content"]
                content_tokens = self.token_estimator.estimate_tokens(content)
                
                # If content is very long, truncate it
                if content_tokens > 1000:  # threshold for truncation
                    lines = content.split('\n')
                    if len(lines) > 50:
                        # Keep the first and last 20 lines
                        truncated = '\n'.join(lines[:20] + ['...'] + lines[-20:])
                        optimized["content"] = truncated
                        optimized["content_truncated"] = True
                        optimized["original_content_tokens"] = content_tokens
            
            # Optimize function signatures
            if optimized.get("type") == "function" and "signatures" in optimized:
                signatures = optimized["signatures"]
                if isinstance(signatures, list) and len(signatures) > 5:
                    # Keep only the most important signatures
                    optimized["signatures"] = signatures[:5]
                    optimized["signatures_truncated"] = True
                    optimized["original_signature_count"] = len(signatures)
            
            optimized_elements.append(optimized)
        
        map_structure["code_elements"] = optimized_elements
        return map_structure
    
    def _optimize_documentation_elements(self, map_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize documentation elements for AI consumption.
        
        Args:
            map_structure: The map structure to optimize
            
        Returns:
            The optimized map structure
        """
        doc_elements = map_structure.get("documentation_elements", [])
        
        if not doc_elements:
            return map_structure
        
        optimized_elements = []
        
        for element in doc_elements:
            # Create a copy of the element
            optimized = element.copy()
            
            # Optimize large content
            if "content" in optimized and isinstance(optimized["content"], str):
                content = optimized["content"]
                content_tokens = self.token_estimator.estimate_tokens(content)
                
                # If content is very long, create a summary
                if content_tokens > 1000:  # threshold for summarization
                    # Extract first paragraph as summary
                    paragraphs = content.split('\n\n')
                    if len(paragraphs) > 1:
                        summary = paragraphs[0].strip()
                        if len(summary) > 200:
                            summary = summary[:200] + '...'
                        
                        optimized["summary"] = summary
                        
                        # Truncate the content but keep first few paragraphs
                        if len(paragraphs) > 3:
                            truncated = '\n\n'.join(paragraphs[:3] + ['...'])
                            optimized["content"] = truncated
                            optimized["content_truncated"] = True
                            optimized["original_content_tokens"] = content_tokens
            
            optimized_elements.append(optimized)
        
        map_structure["documentation_elements"] = optimized_elements
        return map_structure
    
    def _optimize_relationships(self, map_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize relationships for AI consumption.
        
        Args:
            map_structure: The map structure to optimize
            
        Returns:
            The optimized map structure
        """
        relationships = map_structure.get("relationships", [])
        
        if not relationships:
            return map_structure
        
        # If there are too many relationships, prioritize by confidence
        if len(relationships) > 100:  # threshold for optimization
            # Sort by confidence (highest first)
            relationships.sort(key=lambda r: r.get("confidence", 0), reverse=True)
            
            # Keep track of important relationships to preserve
            important_types = {
                RelationshipType.IMPLEMENTS.name,
                RelationshipType.IMPORTS.name,
                RelationshipType.INHERITS.name,
                RelationshipType.DOCUMENTED_BY.name,
                RelationshipType.DOCUMENTS.name
            }
            
            # Keep all important relationships and top N of others
            important = [r for r in relationships if r.get("type") in important_types]
            others = [r for r in relationships if r.get("type") not in important_types]
            
            # Keep top relationships, with bias toward important types
            optimized_relationships = important + others[:100 - len(important)]
            
            map_structure["relationships"] = optimized_relationships
            map_structure["relationships_truncated"] = True
            map_structure["original_relationship_count"] = len(relationships)
        
        return map_structure
    
    def _add_ai_metadata(self, map_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Add AI-specific metadata to the map.
        
        Args:
            map_structure: The map structure to augment
            
        Returns:
            The augmented map structure
        """
        # Make sure we have a metadata section
        if "metadata" not in map_structure:
            map_structure["metadata"] = {}
        
        metadata = map_structure["metadata"]
        
        # Add AI-specific guidance
        metadata["ai_guidance"] = {
            "map_purpose": "This map provides a structured representation of the project's "
                           "code and documentation elements and their relationships.",
            "usage_tips": [
                "Start by examining the project metadata and statistics",
                "Use the relationships to understand dependencies between components",
                "Refer to the content of elements for implementation details",
                "Consider confidence scores when evaluating relationship strength"
            ],
            "token_optimization": "This map has been optimized for token efficiency "
                                  "while preserving the most important information."
        }
        
        # Add prompting suggestions
        metadata["prompting_suggestions"] = {
            "code_understanding": "Using this map, explain how {component} works and its role in the project",
            "dependency_analysis": "Based on this map, what are the key dependencies of {component}?",
            "documentation_query": "What documentation exists for {feature} according to this map?",
            "implementation_question": "How is {feature} implemented according to this map?"
        }
        
        return map_structure 