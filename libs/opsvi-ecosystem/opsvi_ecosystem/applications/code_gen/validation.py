"""Input validation and sanitization for code generation requests."""

import re
from typing import List, Optional
import html
import logging

from ai_agents import analyze_request_security_with_ai

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class InputValidator:
    """Validates and sanitizes user input for code generation."""

    # Basic security patterns as safety net (kept minimal)
    CRITICAL_PATTERNS = [
        r"__import__",
        r"eval\s*\(",
        r"exec\s*\(",
        r"\.\./",  # Path traversal
    ]

    # Maximum lengths
    MAX_REQUEST_LENGTH = 10000
    MAX_LINE_LENGTH = 1000

    def __init__(self):
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.CRITICAL_PATTERNS
        ]

    def validate_request(self, request: str) -> str:
        """
        Validate and sanitize a user request using AI analysis and basic patterns.

        Args:
            request: Raw user input

        Returns:
            Sanitized request string

        Raises:
            ValidationError: If input is invalid or potentially dangerous
        """
        if not request or not request.strip():
            raise ValidationError("Request cannot be empty")

        # Check length limits
        if len(request) > self.MAX_REQUEST_LENGTH:
            raise ValidationError(
                f"Request too long: {len(request)} > {self.MAX_REQUEST_LENGTH}"
            )

        # Check for critical patterns (safety net)
        for pattern in self.compiled_patterns:
            if pattern.search(request):
                raise ValidationError(
                    f"Request contains potentially dangerous content: {pattern.pattern}"
                )

        # Check line length
        lines = request.split("\n")
        for i, line in enumerate(lines):
            if len(line) > self.MAX_LINE_LENGTH:
                raise ValidationError(
                    f"Line {i+1} too long: {len(line)} > {self.MAX_LINE_LENGTH}"
                )

        # Detect embedded control characters (excluding newline/tab) early
        if any(ord(ch) < 32 and ch not in "\n\t" for ch in request):
            sanitized_tmp = self._sanitize_string(request)
            if len(sanitized_tmp.strip()) < 10:
                raise ValidationError("Request too short after sanitization")
            else:
                raise ValidationError(
                    "AI security analysis failed: Control characters detected"
                )

        # Enhanced AI-powered security analysis
        try:
            security_analysis = analyze_request_security_with_ai(request)

            # Only block if risk level is high OR sanitized content is too short
            if not security_analysis.is_safe:
                sanitized_tmp = self._sanitize_string(request)
                if len(sanitized_tmp.strip()) < 10:
                    raise ValidationError("Request too short after sanitization")
                if security_analysis.risk_level.lower() == "high":
                    logger.warning(
                        f"AI detected unsafe request: {security_analysis.concerns}"
                    )
                    raise ValidationError(
                        f"AI security analysis failed: {', '.join(security_analysis.concerns)}"
                    )
                # If control characters detected in original request, treat as unsafe
                if any(ord(ch) < 32 and ch not in "\n\t" for ch in request):
                    raise ValidationError(
                        "AI security analysis failed: Control characters detected"
                    )

        except ValidationError:
            raise
        except Exception as e:  # noqa: BLE001
            # If AI analysis fails for any reason, fall back to basic sanitization
            logger.warning(
                "AI security analysis failed, using basic sanitization: %s", str(e)
            )
            sanitized = self._sanitize_string(request)
            if len(sanitized.strip()) < 10:
                raise ValidationError("Request too short after sanitization")
            return sanitized

        # If analysis deemed safe or medium risk, sanitize lightly and return
        sanitized_final = self._sanitize_string(request)
        if len(sanitized_final.strip()) < 10:
            raise ValidationError("Request too short after sanitization")
        return sanitized_final

    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string by removing/escaping potentially dangerous content."""
        # HTML escape
        text = html.escape(text)

        # Remove null bytes and control characters (except newlines and tabs)
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text.strip())

        return text

    def extract_keywords(self, request: str) -> List[str]:
        """Extract safe keywords from request - now just delegates to AI analysis."""
        logger.info("Keyword extraction now handled by AI project type detection")
        # This method is kept for backward compatibility but AI agents handle semantic analysis
        return []


def validate_job_id(job_id: str) -> bool:
    """Validate that a job ID is properly formatted UUID."""
    uuid_pattern = re.compile(
        r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.IGNORECASE
    )
    return bool(uuid_pattern.match(job_id))


# Global validator instance
validator = InputValidator()
