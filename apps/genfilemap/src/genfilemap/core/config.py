
import os
from typing import Optional, Dict, Any

class Config:
    """Configuration class for file map generation."""

    def __init__(self,
                 min_lines: int = 50,
                 max_lines: int = 1000,
                 report_path: Optional[str] = None,
                 api_key: Optional[str] = None,
                 model: str = "gpt-4.1-mini",
                 enable_validation: bool = False,
                 validation_model: Optional[str] = None,
                 strict_validation: bool = False,
                 abort_on_validation_failure: bool = False):
        """
        Initialize configuration.

        Args:
            min_lines: Minimum number of lines for a file to be processed
            max_lines: Maximum number of lines for a file to be processed
            report_path: Path to write the JSON report
            api_key: OpenAI API key
            model: Model to use for file map generation
            enable_validation: Whether to validate generated file maps
            validation_model: Model to use for validation (defaults to same as generation model)
            strict_validation: Whether to use stricter validation criteria
            abort_on_validation_failure: Whether to abort processing if validation fails
        """
        self.min_lines = min_lines
        self.max_lines = max_lines
        self.report_path = report_path
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.enable_validation = enable_validation
        self.validation_model = validation_model or model
        self.strict_validation = strict_validation
        self.abort_on_validation_failure = abort_on_validation_failure

        if not self.api_key:
            raise ValueError("API key must be provided either in config or OPENAI_API_KEY environment variable")

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """
        Create a Config instance from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            Config instance
        """
        return cls(
            min_lines=config_dict.get("min_lines", 50),
            max_lines=config_dict.get("max_lines", 1000),
            report_path=config_dict.get("report_path"),
            api_key=config_dict.get("api_key"),
            model=config_dict.get("model", "gpt-4.1-mini"),
            enable_validation=config_dict.get("enable_validation", False),
            validation_model=config_dict.get("validation_model"),
            strict_validation=config_dict.get("strict_validation", False),
            abort_on_validation_failure=config_dict.get("abort_on_validation_failure", False)
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary.

        Returns:
            Dictionary representation of config
        """
        return {
            "min_lines": self.min_lines,
            "max_lines": self.max_lines,
            "report_path": self.report_path,
            "api_key": "***" if self.api_key else None,  # Mask API key
            "model": self.model,
            "enable_validation": self.enable_validation,
            "validation_model": self.validation_model,
            "strict_validation": self.strict_validation,
            "abort_on_validation_failure": self.abort_on_validation_failure
        }