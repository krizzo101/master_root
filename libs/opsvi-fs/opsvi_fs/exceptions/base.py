#!/usr/bin/env python3
"""Exceptions for opsvi-fs."""
from __future__ import annotations


class LibraryError(Exception):
    """Base library error."""


class LibraryConfigurationError(LibraryError):
    """Raised for invalid or missing configuration."""


class ProviderError(LibraryError):
    """Raised for provider-specific failures."""
