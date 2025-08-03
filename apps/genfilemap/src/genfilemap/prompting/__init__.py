"""
Prompting module for genfilemap.

This package contains prompt templates and generators for different file types.
"""

from genfilemap.prompting.prompts import (
    get_code_system_message,
    get_code_user_prompt,
    get_documentation_system_message,
    get_documentation_user_prompt
)

__all__ = [
    "get_code_system_message",
    "get_code_user_prompt",
    "get_documentation_system_message",
    "get_documentation_user_prompt"
] 