"""
Template management for code generation.
"""

from .template_manager import TemplateManager
from .python_templates import PythonTemplates
from .javascript_templates import JavaScriptTemplates

__all__ = [
    "TemplateManager",
    "PythonTemplates",
    "JavaScriptTemplates"
]