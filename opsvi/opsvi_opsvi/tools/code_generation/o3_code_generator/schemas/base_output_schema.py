"""
Base output schema for validation framework integration.

All generator outputs inherit from BaseGeneratorOutput to ensure consistent
success/error reporting and validation framework integration.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BaseGeneratorOutput(BaseModel):
    """
    Base output schema that all generators must inherit from.

    Provides standardized success/error reporting and validation framework integration.
    """

    success: bool = Field(
        True, description="Whether the operation completed successfully"
    )
    error_message: Optional[str] = Field(
        None, description="Detailed error message if operation failed"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-fatal warnings and recommendations"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context and metrics"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the operation completed"
    )

    def add_warning(self, message: str) -> None:
        """Add a warning message to the output."""
        self.warnings.append(message)

    def mark_failed(self, error_message: str) -> None:
        """Mark the operation as failed with an error message."""
        self.success = False
        self.error_message = error_message

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata information."""
        self.metadata[key] = value

    def is_successful(self) -> bool:
        """Check if the operation was successful."""
        return self.success and self.error_message is None

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
