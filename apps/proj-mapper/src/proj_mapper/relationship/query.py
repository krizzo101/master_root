"""Relationship Query Module.

This module provides a query interface for filtering and searching relationships.
"""

from typing import List, Dict, Any, Optional, Callable, Set


class RelationshipQuery:
    """Query interface for relationship data.
    
    This class provides methods to filter and search relationships based on various
    attributes such as source/target IDs, relationship types, and confidence scores.
    """
    
    def __init__(self):
        """Initialize a new query object with no filters."""
        self._filters: List[Callable[[Dict[str, Any]], bool]] = []
    
    def filter_source_id(self, source_ids: List[str]) -> 'RelationshipQuery':
        """Filter relationships by source ID.
        
        Args:
            source_ids: List of source IDs to match
            
        Returns:
            Self for method chaining
        """
        source_id_set = set(source_ids)
        self._filters.append(lambda rel: rel.get('source_id') in source_id_set)
        return self
    
    def filter_target_id(self, target_ids: List[str]) -> 'RelationshipQuery':
        """Filter relationships by target ID.
        
        Args:
            target_ids: List of target IDs to match
            
        Returns:
            Self for method chaining
        """
        target_id_set = set(target_ids)
        self._filters.append(lambda rel: rel.get('target_id') in target_id_set)
        return self
    
    def filter_relationship_type(self, types: List[str]) -> 'RelationshipQuery':
        """Filter relationships by relationship type.
        
        Args:
            types: List of relationship types to match
            
        Returns:
            Self for method chaining
        """
        type_set = set(types)
        self._filters.append(lambda rel: rel.get('relationship_type') in type_set)
        return self
    
    def filter_min_confidence(self, min_confidence: float) -> 'RelationshipQuery':
        """Filter relationships by minimum confidence score.
        
        Args:
            min_confidence: Minimum confidence score (0.0 to 1.0)
            
        Returns:
            Self for method chaining
        """
        self._filters.append(lambda rel: rel.get('confidence', 0.0) >= min_confidence)
        return self
    
    def filter_source_type(self, source_types: List[str]) -> 'RelationshipQuery':
        """Filter relationships by source element type.
        
        Args:
            source_types: List of source element types to match
            
        Returns:
            Self for method chaining
        """
        type_set = set(source_types)
        
        def check_source_type(rel: Dict[str, Any]) -> bool:
            metadata = rel.get('metadata', {})
            source_type = metadata.get('source_type') 
            return source_type in type_set
        
        self._filters.append(check_source_type)
        return self
    
    def filter_target_type(self, target_types: List[str]) -> 'RelationshipQuery':
        """Filter relationships by target element type.
        
        Args:
            target_types: List of target element types to match
            
        Returns:
            Self for method chaining
        """
        type_set = set(target_types)
        
        def check_target_type(rel: Dict[str, Any]) -> bool:
            metadata = rel.get('metadata', {})
            target_type = metadata.get('target_type')
            return target_type in type_set
        
        self._filters.append(check_target_type)
        return self
    
    def filter_metadata(self, key: str, value: Any) -> 'RelationshipQuery':
        """Filter relationships by metadata key-value pair.
        
        Args:
            key: Metadata key to check
            value: Value to match
            
        Returns:
            Self for method chaining
        """
        self._filters.append(lambda rel: rel.get('metadata', {}).get(key) == value)
        return self
    
    def execute(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the query against the provided relationships.
        
        This method applies all filters to the provided relationships and
        returns the filtered results.
        
        Args:
            relationships: List of relationship dictionaries to filter
            
        Returns:
            Filtered list of relationships
        """
        results = relationships
        
        # Apply all filters in sequence
        for filter_func in self._filters:
            results = [rel for rel in results if filter_func(rel)]
        
        return results 