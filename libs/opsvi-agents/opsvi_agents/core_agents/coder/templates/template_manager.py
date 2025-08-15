"""
Template management system for code generation.
"""

from typing import Dict, Any, Optional
import re


class TemplateManager:
    """Manages code templates for various languages and patterns."""
    
    def __init__(self):
        """Initialize template manager."""
        self.templates: Dict[str, str] = {}
        self._register_default_templates()
    
    def _register_default_templates(self):
        """Register default templates."""
        # Python templates
        self.templates["python_class"] = '''class {name}{inheritance}:
    """{docstring}
    
    Attributes:
        {attributes}
    """
    
    def __init__(self{params}):
        """Initialize {name}.
        
        Args:
            {param_docs}
        """
        {super_init}{init_body}
    
    {methods}'''
        
        self.templates["python_function"] = '''def {name}({params}) -> {return_type}:
    """{docstring}
    
    Args:
        {param_docs}
    
    Returns:
        {return_docs}
    
    Raises:
        {raises_docs}
    """
    {body}'''
        
        self.templates["python_async_function"] = '''async def {name}({params}) -> {return_type}:
    """{docstring}
    
    Args:
        {param_docs}
    
    Returns:
        {return_docs}
    """
    {body}'''
        
        # JavaScript templates
        self.templates["javascript_class"] = '''class {name}{extends} {{
    /**
     * {description}
     */
    constructor({params}) {{
        {super_call}{constructor_body}
    }}
    
    {methods}
}}'''
        
        self.templates["typescript_interface"] = '''interface {name}{extends} {{
    {properties}
}}'''
        
        # Design pattern templates
        self.templates["singleton"] = '''class {name}:
    """Singleton pattern implementation."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        {init_body}
        self._initialized = True'''
        
        self.templates["factory"] = '''from abc import ABC, abstractmethod
from typing import Dict, Type

class {base_name}(ABC):
    """Abstract base for factory products."""
    
    @abstractmethod
    def {method_name}(self):
        pass

class {concrete_name}({base_name}):
    """Concrete implementation."""
    
    def {method_name}(self):
        {implementation}

class {factory_name}:
    """Factory for creating {base_name} instances."""
    
    _products: Dict[str, Type[{base_name}]] = {{
        "{product_key}": {concrete_name}
    }}
    
    @classmethod
    def create(cls, product_type: str) -> {base_name}:
        """Create product instance."""
        product_class = cls._products.get(product_type)
        if not product_class:
            raise ValueError(f"Unknown product type: {{product_type}}")
        return product_class()'''
    
    def get_template(self, template_name: str) -> Optional[str]:
        """Get a template by name."""
        return self.templates.get(template_name)
    
    def register_template(self, name: str, template: str):
        """Register a new template."""
        self.templates[name] = template
    
    def apply_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Apply a template with given context."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Simple template substitution
        result = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        # Clean up any remaining placeholders
        result = re.sub(r'\{[^}]+\}', '', result)
        
        return result
    
    def list_templates(self) -> list:
        """List all available templates."""
        return list(self.templates.keys())