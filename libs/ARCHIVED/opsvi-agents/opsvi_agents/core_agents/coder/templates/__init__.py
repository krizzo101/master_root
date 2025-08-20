"""
Template management for code generation.
"""

from .javascript_templates import JavaScriptTemplates
from .python_templates import PythonTemplates
from .template_manager import TemplateManager

__all__ = ["TemplateManager", "PythonTemplates", "JavaScriptTemplates"]
