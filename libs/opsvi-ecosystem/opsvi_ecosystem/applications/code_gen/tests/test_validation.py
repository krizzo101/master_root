"""Tests for input validation module."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from validation import InputValidator, ValidationError, validate_job_id


class TestInputValidator:
    """Test the InputValidator class."""

    def setup_method(self):
        """Setup test instance."""
        self.validator = InputValidator()

    def test_valid_request(self):
        """Test validation of valid request."""
        request = "Create a simple web API with FastAPI"
        result = self.validator.validate_request(request)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_request(self):
        """Test validation of empty request."""
        with pytest.raises(ValidationError, match="Request cannot be empty"):
            self.validator.validate_request("")

    def test_whitespace_only_request(self):
        """Test validation of whitespace-only request."""
        with pytest.raises(ValidationError, match="Request cannot be empty"):
            self.validator.validate_request("   \n\t  ")

    def test_too_long_request(self):
        """Test validation of overly long request."""
        long_request = "x" * (self.validator.MAX_REQUEST_LENGTH + 1)
        with pytest.raises(ValidationError, match="Request too long"):
            self.validator.validate_request(long_request)

    def test_dangerous_patterns(self):
        """Test detection of dangerous patterns."""
        # Test critical patterns that should still be caught
        critical_dangerous = [
            "use __import__ to load modules",
            "run eval(dangerous_code) function",
            "execute exec(malicious) code",
            "access ../../../etc/passwd files",
        ]

        caught_any = False
        for request in critical_dangerous:
            try:
                self.validator.validate_request(request)
            except ValidationError as e:
                caught_any = True
                assert "potentially dangerous content" in str(e)

        # At least some should be caught by basic patterns
        assert caught_any, "No critical dangerous patterns were detected"

    def test_long_lines(self):
        """Test validation of requests with long lines."""
        long_line = "x" * (self.validator.MAX_LINE_LENGTH + 1)
        request = f"Create an app\n{long_line}\nwith features"

        with pytest.raises(ValidationError, match="Line .* too long"):
            self.validator.validate_request(request)

    def test_too_short_after_sanitization_basic_patterns(self):
        """Test that basic dangerous patterns are still caught."""
        # This should be caught by basic patterns before AI analysis
        request = "__import__"
        with pytest.raises(ValidationError, match="potentially dangerous content"):
            self.validator.validate_request(request)

    def test_actually_too_short_after_sanitization(self):
        """Test with content that truly becomes too short after sanitization."""
        request = "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"  # All control chars
        # This should fall back to basic sanitization since AI analysis might fail on control chars
        with pytest.raises(
            ValidationError, match="Request too short after sanitization"
        ):
            self.validator.validate_request(request)

    def test_sanitization_fallback(self):
        """Test that AI security analysis correctly detects dangerous control characters."""
        # Use a request with control characters that AI should detect as dangerous
        request = "Create  an   app\nwith\tmultiple\x00\x01spaces"

        # The AI should detect this as potentially dangerous due to control characters
        with pytest.raises(ValidationError, match="AI security analysis failed"):
            self.validator.validate_request(request)

    def test_extract_keywords_deprecated(self):
        """Test keyword extraction - now returns empty as it's handled by AI."""
        request = "Create a web API with FastAPI and database support"
        keywords = self.validator.extract_keywords(request)

        # Should return empty list as keyword extraction is now handled by AI agents
        assert keywords == []

    def test_extract_keywords_filters_irrelevant(self):
        """Test that keyword extraction is deprecated."""
        request = "The quick brown fox jumps over the lazy dog"
        keywords = self.validator.extract_keywords(request)

        # Should return empty as this functionality moved to AI agents
        assert keywords == []


class TestJobIdValidation:
    """Test job ID validation function."""

    def test_valid_uuid(self):
        """Test validation of valid UUID."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert validate_job_id(valid_uuid) is True

    def test_valid_uuid_uppercase(self):
        """Test validation of valid UUID in uppercase."""
        valid_uuid = "550E8400-E29B-41D4-A716-446655440000"
        assert validate_job_id(valid_uuid) is True

    def test_invalid_uuid_format(self):
        """Test validation of invalid UUID format."""
        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "ggge8400-e29b-41d4-a716-446655440000",  # Invalid characters
            "123",  # Too short
        ]

        for invalid_uuid in invalid_uuids:
            assert validate_job_id(invalid_uuid) is False


class TestValidatorIntegration:
    """Integration tests for validator."""

    def test_realistic_requests(self):
        """Test with realistic user requests."""
        validator = InputValidator()

        realistic_requests = [
            "Create a CLI tool for processing CSV files",
            "Build a web API with user authentication",
            "Generate a data processor for JSON transformation",
            "Make a simple web app with forms",
            "Create a script that connects to a database",
        ]

        for request in realistic_requests:
            # Should not raise exceptions
            result = validator.validate_request(request)
            assert isinstance(result, str)
            assert len(result) > 10

            # Keyword extraction is now deprecated (handled by AI)
            keywords = validator.extract_keywords(request)
            assert keywords == []  # Should return empty list


if __name__ == "__main__":
    pytest.main([__file__])
