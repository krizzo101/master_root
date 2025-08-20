"""Core greeting logic."""

import re
from typing import Optional

from hello_cli.config import Config
from hello_cli.errors import ValidationError


class Greeter:
    """Handles greeting generation and formatting."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize greeter with configuration.

        Args:
            config: Configuration object
        """
        self.config = config or Config()

    def validate_name(self, name: str) -> str:
        """Validate and sanitize name input.

        Args:
            name: Name to validate

        Returns:
            Validated name

        Raises:
            ValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise ValidationError("Name cannot be empty")

        # Remove excess whitespace
        name = " ".join(name.split())

        # Check length
        if len(name) > 100:
            raise ValidationError("Name is too long (max 100 characters)")

        # Check for invalid characters (allow letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            raise ValidationError("Name contains invalid characters")

        return name

    def greet(
        self, name: str, style: Optional[str] = None, uppercase: Optional[bool] = None
    ) -> str:
        """Generate greeting message.

        Args:
            name: Name to greet
            style: Style to use (plain, emoji, banner)
            uppercase: Whether to uppercase the output

        Returns:
            Formatted greeting message
        """
        # Validate name
        name = self.validate_name(name)

        # Get style and uppercase settings
        style = style or self.config.get("default_style", "plain")
        uppercase = (
            uppercase if uppercase is not None else self.config.get("uppercase", False)
        )

        # Get greeting template
        styles = self.config.get("styles", {})
        if style not in styles:
            raise ValidationError(f"Unknown style: {style}")

        template = styles[style]
        greeting = self.config.get("greeting", "Hello")

        # Format message
        message = template.format(greeting=greeting, name=name)

        # Apply uppercase if needed
        if uppercase:
            message = message.upper()

        return message
