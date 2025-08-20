"""
Main Python code generator.
"""

from typing import Any, Dict

from ...templates import TemplateManager
from ...types import AnalysisResult
from .api_generator import APIGenerator
from .class_generator import ClassGenerator
from .function_generator import FunctionGenerator
from .model_generator import ModelGenerator
from .test_generator import TestGenerator


class PythonGenerator:
    """Generates Python code based on analysis results."""

    def __init__(self, template_manager: TemplateManager):
        """Initialize Python generator with sub-generators."""
        self.template_manager = template_manager
        self.class_generator = ClassGenerator(template_manager)
        self.function_generator = FunctionGenerator(template_manager)
        self.test_generator = TestGenerator(template_manager)
        self.api_generator = APIGenerator(template_manager)
        self.model_generator = ModelGenerator(template_manager)

    def generate(
        self, description: str, analysis: AnalysisResult, style: Dict[str, Any] = None
    ) -> str:
        """Generate Python code based on description and analysis."""
        style = style or {}
        desc_lower = description.lower()

        # Route to appropriate generator based on description
        if "singleton" in analysis.patterns:
            return self._generate_singleton(description, analysis, style)
        elif "factory" in analysis.patterns:
            return self._generate_factory(description, analysis, style)
        elif "class" in desc_lower:
            return self.class_generator.generate(description, analysis, style)
        elif "test" in desc_lower:
            return self.test_generator.generate(description, analysis, style)
        elif "api" in desc_lower or "endpoint" in desc_lower:
            return self.api_generator.generate(description, analysis, style)
        elif "model" in desc_lower and "database" in desc_lower:
            return self.model_generator.generate(description, analysis, style)
        elif analysis.is_async:
            return self.function_generator.generate_async(description, analysis, style)
        elif "function" in desc_lower or "def" in desc_lower or analysis.operations:
            return self.function_generator.generate(description, analysis, style)
        else:
            # Generate based on detected operations
            if "crud" in analysis.operations:
                return self._generate_crud_operations(description, analysis, style)
            elif "validation" in analysis.operations:
                return self._generate_validator(description, analysis, style)
            else:
                return self._generate_default(description, analysis, style)

    def _generate_singleton(
        self, description: str, analysis: AnalysisResult, style: Dict[str, Any]
    ) -> str:
        """Generate singleton pattern class."""
        entity = analysis.entity or "Manager"

        context = {
            "name": entity,
            "init_body": "        self.data = {}\\n        self.config = {}",
        }

        return self.template_manager.apply_template("singleton", context)

    def _generate_factory(
        self, description: str, analysis: AnalysisResult, style: Dict[str, Any]
    ) -> str:
        """Generate factory pattern implementation."""
        entity = analysis.entity or "Product"

        context = {
            "base_name": f"{entity}Base",
            "concrete_name": f"Concrete{entity}",
            "factory_name": f"{entity}Factory",
            "method_name": "execute",
            "implementation": '        return f"Executing {self.__class__.__name__}"',
            "product_key": "default",
        }

        return self.template_manager.apply_template("factory", context)

    def _generate_crud_operations(
        self, description: str, analysis: AnalysisResult, style: Dict[str, Any]
    ) -> str:
        """Generate CRUD operations."""
        entity = analysis.entity or "item"

        return f'''from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class {entity.capitalize()}Manager:
    """Manager for {entity} CRUD operations."""

    def __init__(self):
        self.storage = {{}}
        self.next_id = 1

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new {entity}."""
        item_id = str(self.next_id)
        self.next_id += 1

        item = {{
            "id": item_id,
            "data": data,
            "created_at": datetime.now().isoformat()
        }}

        self.storage[item_id] = item
        logger.info(f"Created {entity} with ID: {{item_id}}")
        return item

    def read(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Read {entity} by ID."""
        return self.storage.get(item_id)

    def update(self, item_id: str, data: Dict[str, Any]) -> bool:
        """Update {entity}."""
        if item_id in self.storage:
            self.storage[item_id]["data"].update(data)
            self.storage[item_id]["updated_at"] = datetime.now().isoformat()
            logger.info(f"Updated {entity} with ID: {{item_id}}")
            return True
        return False

    def delete(self, item_id: str) -> bool:
        """Delete {entity}."""
        if item_id in self.storage:
            del self.storage[item_id]
            logger.info(f"Deleted {entity} with ID: {{item_id}}")
            return True
        return False

    def list_all(self) -> List[Dict[str, Any]]:
        """List all {entity}s."""
        return list(self.storage.values())'''

    def _generate_validator(
        self, description: str, analysis: AnalysisResult, style: Dict[str, Any]
    ) -> str:
        """Generate validation code."""
        entity = analysis.entity or "data"

        return f'''from typing import Any, Dict, List
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class {entity.capitalize()}Validator:
    """Validator for {entity}."""

    def __init__(self):
        self.rules = {{}}
        self._setup_rules()

    def _setup_rules(self):
        """Setup validation rules."""
        self.rules = {{
            'required': ['id', 'name'],
            'types': {{
                'id': (str, int),
                'name': str,
                'email': str,
                'age': int
            }},
            'patterns': {{
                'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}$',
                'phone': r'^\\+?1?\\d{{9,15}}$'
            }},
            'ranges': {{
                'age': (0, 150),
                'score': (0, 100)
            }}
        }}

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate {entity} data."""
        errors = []
        warnings = []

        # Check required fields
        for field in self.rules.get('required', []):
            if field not in data:
                errors.append(f"Missing required field: {{field}}")

        # Check types
        for field, expected_type in self.rules.get('types', {{}}).items():
            if field in data and not isinstance(data[field], expected_type):
                errors.append(f"Invalid type for {{field}}: expected {{expected_type}}")

        # Check patterns
        for field, pattern in self.rules.get('patterns', {{}}).items():
            if field in data and not re.match(pattern, str(data[field])):
                errors.append(f"Invalid format for {{field}}")

        # Check ranges
        for field, (min_val, max_val) in self.rules.get('ranges', {{}}).items():
            if field in data:
                value = data[field]
                if not (min_val <= value <= max_val):
                    errors.append(f"{{field}} out of range: {{min_val}}-{{max_val}}")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("Validation passed")
        else:
            logger.warning(f"Validation failed with {{len(errors)}} errors")

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)'''

    def _generate_default(
        self, description: str, analysis: AnalysisResult, style: Dict[str, Any]
    ) -> str:
        """Generate default Python code."""
        return f'''"""
{description}
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

def process_data(data: Any) -> Any:
    """Process input data according to requirements.

    Args:
        data: Input data to process

    Returns:
        Processed result
    """
    try:
        # Validate input
        if data is None:
            raise ValueError("Input data cannot be None")

        # Process data
        result = data  # Transform as needed

        logger.info("Successfully processed data")
        return result

    except Exception as e:
        logger.error(f"Error processing data: {{e}}")
        raise

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)

    # Example usage
    sample_data = {{}}  # Add sample data
    result = process_data(sample_data)
    print(f"Result: {{result}}")

if __name__ == "__main__":
    main()'''
