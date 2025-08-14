"""String manipulation helper utilities for opsvi-foundation.

Provides string manipulation, encoding/decoding, and template rendering.
"""

import base64
import hashlib
import html
import logging
import re
import secrets
import string
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class StringHelper:
    """String manipulation utilities."""

    # Regex patterns
    URL_PATTERN = re.compile(
        r"https?://(?:[-\w.])+(?::\d+)?(?:[/?#]\S*)?", re.IGNORECASE
    )

    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

    @staticmethod
    def slugify(
        text: str,
        separator: str = "-",
        lowercase: bool = True,
        max_length: Optional[int] = None,
    ) -> str:
        """Convert text to URL-friendly slug.

        Args:
            text: Text to slugify
            separator: Separator character
            lowercase: Convert to lowercase
            max_length: Maximum length

        Returns:
            Slugified text
        """
        # Remove HTML tags
        text = StringHelper.HTML_TAG_PATTERN.sub("", text)

        # Replace non-alphanumeric with separator
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", separator, text)

        # Clean up
        text = text.strip(separator)

        if lowercase:
            text = text.lower()

        if max_length:
            text = text[:max_length].rstrip(separator)

        return text

    @staticmethod
    def truncate(
        text: str, length: int, suffix: str = "...", whole_words: bool = True
    ) -> str:
        """Truncate text to specified length.

        Args:
            text: Text to truncate
            length: Maximum length
            suffix: Suffix to append
            whole_words: Truncate at word boundary

        Returns:
            Truncated text
        """
        if len(text) <= length:
            return text

        truncated_length = length - len(suffix)

        if whole_words:
            # Find last space before limit
            last_space = text.rfind(" ", 0, truncated_length)
            if last_space > 0:
                truncated_length = last_space

        return text[:truncated_length].rstrip() + suffix

    @staticmethod
    def strip_html(text: str) -> str:
        """Remove HTML tags from text.

        Args:
            text: Text with HTML

        Returns:
            Text without HTML tags
        """
        # Remove HTML tags
        text = StringHelper.HTML_TAG_PATTERN.sub("", text)

        # Unescape HTML entities
        text = html.unescape(text)

        return text

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text.

        Args:
            text: Text to search

        Returns:
            List of URLs
        """
        return StringHelper.URL_PATTERN.findall(text)

    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """Extract email addresses from text.

        Args:
            text: Text to search

        Returns:
            List of email addresses
        """
        return StringHelper.EMAIL_PATTERN.findall(text)

    @staticmethod
    def camel_to_snake(text: str) -> str:
        """Convert camelCase to snake_case.

        Args:
            text: CamelCase text

        Returns:
            snake_case text
        """
        # Insert underscore before uppercase letters
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    @staticmethod
    def snake_to_camel(text: str, upper_first: bool = True) -> str:
        """Convert snake_case to camelCase.

        Args:
            text: snake_case text
            upper_first: Uppercase first letter (PascalCase)

        Returns:
            camelCase text
        """
        components = text.split("_")

        if upper_first:
            return "".join(x.title() for x in components)
        else:
            return components[0] + "".join(x.title() for x in components[1:])

    @staticmethod
    def encode_base64(data: Union[str, bytes], url_safe: bool = False) -> str:
        """Encode data to base64.

        Args:
            data: Data to encode
            url_safe: Use URL-safe encoding

        Returns:
            Base64 encoded string
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        if url_safe:
            return base64.urlsafe_b64encode(data).decode("ascii")
        else:
            return base64.b64encode(data).decode("ascii")

    @staticmethod
    def decode_base64(encoded: str, url_safe: bool = False) -> bytes:
        """Decode base64 data.

        Args:
            encoded: Base64 encoded string
            url_safe: Use URL-safe decoding

        Returns:
            Decoded bytes
        """
        # Add padding if necessary
        missing_padding = len(encoded) % 4
        if missing_padding:
            encoded += "=" * (4 - missing_padding)

        if url_safe:
            return base64.urlsafe_b64decode(encoded)
        else:
            return base64.b64decode(encoded)

    @staticmethod
    def generate_random_string(
        length: int = 32, alphabet: Optional[str] = None, secure: bool = True
    ) -> str:
        """Generate random string.

        Args:
            length: String length
            alphabet: Characters to use
            secure: Use cryptographically secure random

        Returns:
            Random string
        """
        if alphabet is None:
            alphabet = string.ascii_letters + string.digits

        if secure:
            return "".join(secrets.choice(alphabet) for _ in range(length))
        else:
            import random

            return "".join(random.choice(alphabet) for _ in range(length))

    @staticmethod
    def hash_string(
        text: str, algorithm: str = "sha256", salt: Optional[str] = None
    ) -> str:
        """Hash a string.

        Args:
            text: Text to hash
            algorithm: Hash algorithm
            salt: Optional salt

        Returns:
            Hex digest of hash
        """
        if salt:
            text = salt + text

        text_bytes = text.encode("utf-8")

        if algorithm == "md5":
            return hashlib.md5(text_bytes).hexdigest()
        elif algorithm == "sha1":
            return hashlib.sha1(text_bytes).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(text_bytes).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(text_bytes).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    @staticmethod
    def mask_sensitive(
        text: str, mask_char: str = "*", visible_start: int = 4, visible_end: int = 4
    ) -> str:
        """Mask sensitive information.

        Args:
            text: Text to mask
            mask_char: Character for masking
            visible_start: Visible characters at start
            visible_end: Visible characters at end

        Returns:
            Masked text
        """
        if len(text) <= visible_start + visible_end:
            # Too short to mask meaningfully
            return mask_char * len(text)

        start = text[:visible_start]
        end = text[-visible_end:] if visible_end > 0 else ""
        masked_length = len(text) - visible_start - visible_end

        return start + (mask_char * masked_length) + end

    @staticmethod
    def render_template(
        template: str, context: Dict[str, Any], safe: bool = True
    ) -> str:
        """Simple template rendering.

        Args:
            template: Template string with {variable} placeholders
            context: Variable values
            safe: Escape HTML in values

        Returns:
            Rendered template
        """
        result = template

        for key, value in context.items():
            placeholder = "{" + key + "}"

            # Convert value to string
            str_value = str(value)

            # Escape HTML if requested
            if safe:
                str_value = html.escape(str_value)

            result = result.replace(placeholder, str_value)

        return result


# Convenience functions
def slugify(
    text: str,
    separator: str = "-",
    lowercase: bool = True,
    max_length: Optional[int] = None,
) -> str:
    """Convert text to URL-friendly slug."""
    return StringHelper.slugify(text, separator, lowercase, max_length)


def truncate(
    text: str, length: int, suffix: str = "...", whole_words: bool = True
) -> str:
    """Truncate text to specified length."""
    return StringHelper.truncate(text, length, suffix, whole_words)


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return StringHelper.strip_html(text)


def extract_urls(text: str) -> List[str]:
    """Extract URLs from text."""
    return StringHelper.extract_urls(text)


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text."""
    return StringHelper.extract_emails(text)


def camel_to_snake(text: str) -> str:
    """Convert camelCase to snake_case."""
    return StringHelper.camel_to_snake(text)


def snake_to_camel(text: str, upper_first: bool = True) -> str:
    """Convert snake_case to camelCase."""
    return StringHelper.snake_to_camel(text, upper_first)


def encode_base64(data: Union[str, bytes], url_safe: bool = False) -> str:
    """Encode data to base64."""
    return StringHelper.encode_base64(data, url_safe)


def decode_base64(encoded: str, url_safe: bool = False) -> bytes:
    """Decode base64 data."""
    return StringHelper.decode_base64(encoded, url_safe)


def generate_random_string(
    length: int = 32, alphabet: Optional[str] = None, secure: bool = True
) -> str:
    """Generate random string."""
    return StringHelper.generate_random_string(length, alphabet, secure)


def hash_string(
    text: str, algorithm: str = "sha256", salt: Optional[str] = None
) -> str:
    """Hash a string."""
    return StringHelper.hash_string(text, algorithm, salt)


def mask_sensitive(
    text: str, mask_char: str = "*", visible_start: int = 4, visible_end: int = 4
) -> str:
    """Mask sensitive information."""
    return StringHelper.mask_sensitive(text, mask_char, visible_start, visible_end)


def render_template(template: str, context: Dict[str, Any], safe: bool = True) -> str:
    """Simple template rendering."""
    return StringHelper.render_template(template, context, safe)


__all__ = [
    "StringHelper",
    "slugify",
    "truncate",
    "strip_html",
    "extract_urls",
    "extract_emails",
    "camel_to_snake",
    "snake_to_camel",
    "encode_base64",
    "decode_base64",
    "generate_random_string",
    "hash_string",
    "mask_sensitive",
    "render_template",
]
