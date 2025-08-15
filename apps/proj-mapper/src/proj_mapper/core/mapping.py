from proj_mapper.models.code import (
    CodeElement, 
    CodeReference,
    Location,
    LocationModel,
    CodeElementType
) 
from typing import Optional, Union, Dict, Any

def add_reference(self, source_id: str, target_id: str, ref_type: str,
                      location: Optional[Union[Location, LocationModel]] = None, confidence: float = 1.0) -> None:
        """Add a reference between two code elements.
        
        Args:
            source_id: ID of the source element
            target_id: ID of the target element
            ref_type: Type of reference
            location: Optional location of the reference (Location or LocationModel)
            confidence: Confidence score for this reference
        """
        # Skip if source or target doesn't exist
        if source_id not in self.elements or target_id not in self.elements:
            logger.warning(f"Cannot create reference: {source_id} -> {target_id} (missing element)")
            return
            
        # Get the source element
        source_element = self.elements[source_id]
        
        # Create location model if a location is provided
        location_model = None
        if location:
            if isinstance(location, Location):
                location_model = LocationModel.from_location(location)
            else:
                location_model = location
        
        # Add reference to the source element
        source_element.add_reference(
            reference_id=target_id, 
            reference_type=ref_type,
            location=location_model,
            confidence=confidence
        )
        
        # Update the source element
        self.elements[source_id] = source_element
        
        # Add the reference to our internal reference tracking
        self.references.append({
            "source_id": source_id,
            "target_id": target_id,
            "type": ref_type,
            "confidence": confidence
        }) 