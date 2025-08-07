# FILE_MAP_BEGIN {"file_metadata":{"type":"python","language":"python","title":"gpt5_vs_gpt41_comprehensive_test_framework.py","description":"Python module with 1 functions and 6 classes","last_updated":"2025-08-07"},"code_elements":{"functions":[{"name":"main","line":2983,"parameters":[],"is_async":true,"description":"Asynchronous entry point for the application, coordinating the execution of tasks.","signature":"async main()"}],"classes":[{"name":"TestCategory","line":34,"inherits_from":["Enum):"],"methods":[],"properties":[{"name":"CODE_GENERATION","line":33,"type":""},{"name":"REASONING","line":34,"type":""},{"name":"CREATIVE_TASKS","line":35,"type":""},{"name":"STRUCTURED_OUTPUT","line":36,"type":""},{"name":"AGENTIC_TASKS","line":37,"type":""},{"name":"LONG_CONTEXT","line":38,"type":""},{"name":"FACTUALITY","line":39,"type":""},{"name":"CODING_REASONING","line":40,"type":""},{"name":"ALGORITHM_DESIGN","line":41,"type":""},{"name":"CODE_OPTIMIZATION","line":42,"type":""}],"description":"Represents a category of tests within the evaluation framework."},{"name":"ModelTier","line":47,"inherits_from":["Enum):"],"methods":[],"properties":[{"name":"NANO","line":46,"type":""},{"name":"MINI","line":47,"type":""},{"name":"STANDARD","line":48,"type":""}],"description":"Defines different tiers or levels of models used in evaluations."},{"name":"ReasoningEffort","line":53,"inherits_from":["Enum):"],"methods":[],"properties":[{"name":"LOW","line":52,"type":""},{"name":"MEDIUM","line":53,"type":""},{"name":"HIGH","line":54,"type":""}],"description":"Encapsulates the effort or complexity involved in reasoning tasks."},{"name":"EvaluationMetrics","line":1743,"inherits_from":[],"methods":[],"properties":[],"description":"Holds various metrics used to evaluate model performance."},{"name":"ModelEvaluator","line":1758,"inherits_from":[],"methods":[{"name":"__init__","line":1761,"parameters":[{"name":"self","type":"self"}],"is_async":false,"return_type":"None","signature":"__init__(self) -> None"},{"name":"evaluate_model","line":1765,"parameters":[{"name":"self","type":"self"},{"name":"model","type":"str"},{"name":"category","type":"TestCategory"},{"name":"test_name","type":"str"},{"name":"prompt","type":"str"},{"name":"dataset","type":"dict"}],"is_async":true,"return_type":"EvaluationMetrics","description":"Evaluate a single model on a specific test.","signature":"async evaluate_model(self, model: str, category: TestCategory, test_name: str, prompt: str, dataset: dict) -> EvaluationMetrics"},{"name":"evaluate_model_with_reasoning_effort","line":1831,"parameters":[{"name":"self","type":"self"},{"name":"model","type":"str"},{"name":"category","type":"TestCategory"},{"name":"test_name","type":"str"},{"name":"prompt","type":"str"},{"name":"dataset","type":"dict"},{"name":"effort_level","type":"ReasoningEffort"}],"is_async":true,"return_type":"EvaluationMetrics","description":"Evaluate a GPT-5 model with specific reasoning effort level.","signature":"async evaluate_model_with_reasoning_effort(self, model: str, category: TestCategory, test_name: str, prompt: str, dataset: dict, effort_level: ReasoningEffort) -> EvaluationMetrics"},{"name":"_calculate_metrics","line":1907,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str"},{"name":"dataset","type":"dict"},{"name":"category","type":"TestCategory"},{"name":"execution_time","type":"float"}],"is_async":false,"return_type":"EvaluationMetrics","description":"Calculate comprehensive evaluation metrics.","signature":"_calculate_metrics(self, response: str, dataset: dict, category: TestCategory, execution_time: float) -> EvaluationMetrics"},{"name":"_evaluate_code_correctness","line":1972,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str, dataset: dict"},{"name":"dataset","type":"dict"}],"is_async":false,"return_type":"float","description":"Evaluate functional correctness of generated code.","signature":"_evaluate_code_correctness(self, response: str, dataset: dict, dataset: dict) -> float"},{"name":"_evaluate_code_quality","line":2002,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str"}],"is_async":false,"return_type":"float","description":"Evaluate code quality metrics.","signature":"_evaluate_code_quality(self, response: str) -> float"},{"name":"_evaluate_reasoning_quality","line":2031,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str"}],"is_async":false,"return_type":"float","description":"Evaluate reasoning quality.","signature":"_evaluate_reasoning_quality(self, response: str) -> float"},{"name":"_evaluate_creativity","line":2069,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str"}],"is_async":false,"return_type":"float","description":"Evaluate creativity and originality.","signature":"_evaluate_creativity(self, response: str) -> float"},{"name":"_evaluate_structure_quality","line":2099,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str"}],"is_async":false,"return_type":"float","description":"Evaluate structure and organization.","signature":"_evaluate_structure_quality(self, response: str) -> float"},{"name":"_evaluate_completeness","line":2131,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str, dataset: dict"},{"name":"dataset","type":"dict"}],"is_async":false,"return_type":"float","description":"Evaluate completeness of response.","signature":"_evaluate_completeness(self, response: str, dataset: dict, dataset: dict) -> float"},{"name":"_evaluate_accuracy","line":2161,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str, dataset: dict"},{"name":"dataset","type":"dict"}],"is_async":false,"return_type":"float","description":"Evaluate accuracy for reasoning tasks.","signature":"_evaluate_accuracy(self, response: str, dataset: dict, dataset: dict) -> float"},{"name":"_evaluate_json_validity","line":2181,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str"}],"is_async":false,"return_type":"float","description":"Evaluate JSON validity for structured output.","signature":"_evaluate_json_validity(self, response: str) -> float"},{"name":"_evaluate_functional_correctness","line":2198,"parameters":[{"name":"self","type":"self"},{"name":"response","type":"str, dataset: dict"},{"name":"dataset","type":"dict"}],"is_async":false,"return_type":"float","description":"Evaluate functional correctness for creative tasks.","signature":"_evaluate_functional_correctness(self, response: str, dataset: dict, dataset: dict) -> float"}],"properties":[],"description":"Facilitates the evaluation of models against specified criteria and metrics."},{"name":"ComprehensiveTestRunner","line":2237,"inherits_from":[],"methods":[{"name":"__init__","line":2240,"parameters":[{"name":"self","type":"self"}],"is_async":false,"return_type":"None","signature":"__init__(self) -> None"},{"name":"run_comprehensive_tests","line":2245,"parameters":[{"name":"self","type":"self"}],"is_async":true,"return_type":"dict[str, Any]","description":"Run all tests across all model pairs and categories.","signature":"async run_comprehensive_tests(self) -> dict[str, Any]"},{"name":"_test_gpt5_reasoning_efforts","line":2276,"parameters":[{"name":"self","type":"self"}],"is_async":true,"return_type":"dict[str, Any]","description":"Test GPT-5 with different reasoning effort levels on coding tasks.","signature":"async _test_gpt5_reasoning_efforts(self) -> dict[str, Any]"},{"name":"_test_category_with_reasoning_effort","line":2326,"parameters":[{"name":"self","type":"self"},{"name":"model","type":"str"},{"name":"category","type":"TestCategory"},{"name":"effort_level","type":"ReasoningEffort"}],"is_async":true,"return_type":"dict[str, Any]","description":"Test a specific category with a specific reasoning effort level.","signature":"async _test_category_with_reasoning_effort(self, model: str, category: TestCategory, effort_level: ReasoningEffort) -> dict[str, Any]"},{"name":"_calculate_reasoning_effort_summary","line":2366,"parameters":[{"name":"self","type":"self"},{"name":"categories","type":"dict[str, Any]"}],"is_async":false,"return_type":"dict[str, Any]","description":"Calculate summary statistics for a reasoning effort level.","signature":"_calculate_reasoning_effort_summary(self, categories: dict[str, Any]) -> dict[str, Any]"},{"name":"_analyze_coding_performance_across_efforts","line":2414,"parameters":[{"name":"self","type":"self"},{"name":"reasoning_efforts","type":"Dict[str, Any]"}],"is_async":false,"return_type":"dict[str, Any]","description":"Analyze how coding performance varies across reasoning effort levels.","signature":"_analyze_coding_performance_across_efforts(self, reasoning_efforts: Dict[str, Any]) -> dict[str, Any]"},{"name":"_test_model_pair","line":2505,"parameters":[{"name":"self","type":"self"},{"name":"gpt41_model","type":"str"},{"name":"gpt5_model","type":"str"}],"is_async":true,"return_type":"dict[str, Any]","description":"Test a pair of models across all categories.","signature":"async _test_model_pair(self, gpt41_model: str, gpt5_model: str) -> dict[str, Any]"},{"name":"_test_category","line":2524,"parameters":[{"name":"self","type":"self"},{"name":"gpt41_model","type":"str"},{"name":"gpt5_model","type":"str"},{"name":"category","type":"TestCategory"}],"is_async":true,"return_type":"dict[str, Any]","description":"Test a specific category for both models.","signature":"async _test_category(self, gpt41_model: str, gpt5_model: str, category: TestCategory) -> dict[str, Any]"},{"name":"_compare_metrics","line":2573,"parameters":[{"name":"self","type":"self"},{"name":"gpt41_metrics","type":"EvaluationMetrics"},{"name":"gpt5_metrics","type":"EvaluationMetrics"}],"is_async":false,"return_type":"dict[str, Any]","description":"Compare metrics between two models.","signature":"_compare_metrics(self, gpt41_metrics: EvaluationMetrics, gpt5_metrics: EvaluationMetrics) -> dict[str, Any]"},{"name":"_calculate_overall_improvement","line":2604,"parameters":[{"name":"self","type":"self"},{"name":"gpt41_metrics","type":"EvaluationMetrics"},{"name":"gpt5_metrics","type":"EvaluationMetrics"}],"is_async":false,"return_type":"float","description":"Calculate overall improvement score.","signature":"_calculate_overall_improvement(self, gpt41_metrics: EvaluationMetrics, gpt5_metrics: EvaluationMetrics) -> float"},{"name":"_metrics_to_dict","line":2621,"parameters":[{"name":"self","type":"self"},{"name":"metrics","type":"EvaluationMetrics"}],"is_async":false,"return_type":"dict[str, Any]","description":"Convert metrics to dictionary for JSON serialization.","signature":"_metrics_to_dict(self, metrics: EvaluationMetrics) -> dict[str, Any]"},{"name":"_calculate_category_summary","line":2636,"parameters":[{"name":"self","type":"self"},{"name":"tests","type":"dict[str, Any]"}],"is_async":false,"return_type":"dict[str, Any]","description":"Calculate summary statistics for a category.","signature":"_calculate_category_summary(self, tests: dict[str, Any]) -> dict[str, Any]"},{"name":"_generate_comprehensive_report","line":2700,"parameters":[{"name":"self","type":"self"},{"name":"total_time","type":"float"}],"is_async":false,"return_type":"dict[str, Any]","description":"Generate comprehensive comparison report.","signature":"_generate_comprehensive_report(self, total_time: float) -> dict[str, Any]"},{"name":"_save_results","line":2758,"parameters":[{"name":"self","type":"self"},{"name":"report","type":"dict[str, Any]"}],"is_async":false,"return_type":"None","description":"Save comprehensive results to files.","signature":"_save_results(self, report: dict[str, Any]) -> None"},{"name":"_generate_markdown_report","line":2798,"parameters":[{"name":"self","type":"self"},{"name":"report","type":"dict[str, Any], f"},{"name":"f","type":"unknown"}],"is_async":false,"return_type":"None","description":"Generate comprehensive markdown report.","signature":"_generate_markdown_report(self, report: dict[str, Any], f, f) -> None"},{"name":"_generate_executive_summary","line":2898,"parameters":[{"name":"self","type":"self"},{"name":"report","type":"dict[str, Any], f"},{"name":"f","type":"unknown"}],"is_async":false,"return_type":"None","description":"Generate executive summary.","signature":"_generate_executive_summary(self, report: dict[str, Any], f, f) -> None"}],"properties":[],"description":"Manages the execution of a suite of tests, providing comprehensive results and reporting."}],"imports":[{"module":"asyncio","alias":null,"line":18,"statement":"import asyncio"},{"module":"json","alias":null,"line":19,"statement":"import json"},{"module":"os","alias":null,"line":20,"statement":"import os"},{"module":"re","alias":null,"line":21,"statement":"import re"},{"module":"statistics","alias":null,"line":22,"statement":"import statistics"},{"module":"time","alias":null,"line":23,"statement":"import time"},{"module":"dataclasses","alias":null,"line":24,"statement":"from dataclasses import dataclass"},{"module":"datetime","alias":null,"line":25,"statement":"from datetime import datetime"},{"module":"enum","alias":null,"line":26,"statement":"from enum import Enum"},{"module":"typing","alias":null,"line":27,"statement":"from typing import Any"},{"module":"typing","alias":null,"line":27,"statement":"from typing import IO"}],"constants":[{"name":"MODEL_PAIRS","line":60,"value":"[]","type":"list"},{"name":"GPT5_REASONING_CONFIGS","line":67,"value":"{}","type":"dict"},{"name":"GPT41_CONFIG","line":101,"value":"{'iterations': 3, 'timeout': 300, 'max_tokens': 4000, 'temperature': 0.1, 'api_type': 'chat_completions', 'critic_enabled': True}","type":"dict"},{"name":"GPT5_CONFIG","line":110,"value":"{'iterations': 3, 'timeout': 300, 'max_tokens': 4000, 'temperature': 0.1, 'api_type': 'responses', 'reasoning_effort': 'high', 'verbosity': 'medium', 'previous_response_id': None, 'critic_enabled': True}","type":"dict"},{"name":"GPT41_OPTIMIZED_PROMPTS","line":127,"value":"{}","type":"dict"},{"name":"GPT5_OPTIMIZED_PROMPTS","line":806,"value":"{}","type":"dict"},{"name":"TEST_DATASETS","line":1330,"value":"{}","type":"dict"}]},"key_elements":[{"name":"asyncio","type":"import","line":18},{"name":"json","type":"import","line":19},{"name":"os","type":"import","line":20},{"name":"re","type":"import","line":21},{"name":"statistics","type":"import","line":22},{"name":"time","type":"import","line":23},{"name":"from dataclasses import dataclass","type":"import","line":24},{"name":"from datetime import datetime","type":"import","line":25},{"name":"from enum import Enum","type":"import","line":26},{"name":"from typing import Any","type":"import","line":27},{"name":"from typing import IO","type":"import","line":27},{"name":"TestCategory","type":"class","line":34},{"name":"ModelTier","type":"class","line":47},{"name":"ReasoningEffort","type":"class","line":53},{"name":"MODEL_PAIRS","type":"constant","line":60},{"name":"GPT5_REASONING_CONFIGS","type":"constant","line":67},{"name":"GPT41_CONFIG","type":"constant","line":101},{"name":"GPT5_CONFIG","type":"constant","line":110},{"name":"GPT41_OPTIMIZED_PROMPTS","type":"constant","line":127},{"name":"GPT5_OPTIMIZED_PROMPTS","type":"constant","line":806},{"name":"TEST_DATASETS","type":"constant","line":1330},{"name":"EvaluationMetrics","type":"class","line":1743},{"name":"ModelEvaluator","type":"class","line":1758},{"name":"ComprehensiveTestRunner","type":"class","line":2237},{"name":"main","type":"function","line":2983}],"sections":[{"name":"Imports","description":"Import statements for required modules and libraries.","line_start":18,"line_end":27},{"name":"main Function","description":"Function main implementation.","line_start":2983,"line_end":2988},{"name":"TestCategory Class","description":"Class TestCategory definition and methods.","line_start":34,"line_end":44},{"name":"ModelTier Class","description":"Class ModelTier definition and methods.","line_start":47,"line_end":57},{"name":"ReasoningEffort Class","description":"Class ReasoningEffort definition and methods.","line_start":53,"line_end":63},{"name":"EvaluationMetrics Class","description":"Class EvaluationMetrics definition and methods.","line_start":1743,"line_end":1753},{"name":"ModelEvaluator Class","description":"Class ModelEvaluator definition and methods.","line_start":1758,"line_end":2201},{"name":"ComprehensiveTestRunner Class","description":"Class ComprehensiveTestRunner definition and methods.","line_start":2237,"line_end":2901},{"name":"Constants","description":"Global constants and configuration values.","line_start":60,"line_end":1330}],"content_hash":"a5bbcaffaec85e445953903182dd1af0"} FILE_MAP_END

#!/usr/bin/env python3
"""
Comprehensive GPT-5 vs GPT-4.1 Series Comparison Framework

This framework implements industry-standard evaluation methodologies based on:
- simple-evals: Zero-shot, chain-of-thought evaluation patterns
- human-eval: Functional correctness testing for code generation
- structured-outputs: Schema-driven validation
- gpt-5-coding-examples: Real-world application generation

Author: AI Assistant
Date: 2025-01-15
Version: 3.0.0
"""

import asyncio
import json
import os
import re
import statistics
import time
import logging
from logging import Logger
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, IO, Dict
from openai import OpenAI

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

# Centralized debug logger setup
BASE_DIR = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, "results")
LOG_FILE_PATH = os.path.join(RESULTS_DIR, "test_run.log")


def _setup_logger() -> Logger:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    logger = logging.getLogger("model_testing")
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


LOGGER: Logger = _setup_logger()


def get_log_file_path() -> str:
    """Expose the absolute path of the debug log file for callers (e.g., runner)."""
    return LOG_FILE_PATH


class TestCategory(Enum):
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    CREATIVE_TASKS = "creative_tasks"
    STRUCTURED_OUTPUT = "structured_output"
    AGENTIC_TASKS = "agentic_tasks"
    LONG_CONTEXT = "long_context"
    FACTUALITY = "factuality"
    CODING_REASONING = "coding_reasoning"  # New category for coding-specific reasoning
    ALGORITHM_DESIGN = "algorithm_design"  # New category for algorithm complexity
    CODE_OPTIMIZATION = "code_optimization"  # New category for performance optimization


class ModelTier(Enum):
    NANO = "nano"
    MINI = "mini"
    STANDARD = "standard"


class ReasoningEffort(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Model pairs for comparison
MODEL_PAIRS = [
    ("gpt-4.1-nano", "gpt-5-nano"),
    ("gpt-4.1-mini", "gpt-5-mini"),
    ("gpt-4.1", "gpt-5"),
]

# GPT-5 Reasoning Effort Configurations
GPT5_REASONING_CONFIGS = {
    ReasoningEffort.LOW: {
        "iterations": 1,
        "timeout": 120,
        "max_tokens": 2000,
        "temperature": 0.1,
        "api_type": "responses",
        "reasoning_effort": "low",
        "verbosity": "low",
        "critic_enabled": False,
    },
    ReasoningEffort.MEDIUM: {
        "iterations": 2,
        "timeout": 180,
        "max_tokens": 3000,
        "temperature": 0.1,
        "api_type": "responses",
        "reasoning_effort": "medium",
        "verbosity": "medium",
        "critic_enabled": True,
    },
    ReasoningEffort.HIGH: {
        "iterations": 3,
        "timeout": 300,
        "max_tokens": 4000,
        "temperature": 0.1,
        "api_type": "responses",
        "reasoning_effort": "high",
        "verbosity": "high",
        "critic_enabled": True,
    },
}

# API Configuration based on model capabilities
GPT41_CONFIG = {
    "iterations": 3,
    "timeout": 300,
    "max_tokens": 4000,
    "temperature": 0.1,
    "api_type": "chat_completions",  # GPT-4.1 uses Chat Completions
    "critic_enabled": True,
}

GPT5_CONFIG = {
    "iterations": 3,
    "timeout": 300,
    "max_tokens": 4000,
    "temperature": 0.1,
    "api_type": "responses",  # GPT-5 uses Responses API
    "reasoning_effort": "high",  # For maximum quality
    "verbosity": "medium",  # Default verbosity
    "previous_response_id": None,  # Will be set for multi-turn tests
    "critic_enabled": True,
}

# =============================================================================
# MODEL-SPECIFIC OPTIMIZED PROMPTS
# =============================================================================

# GPT-4.1 Optimized Prompts (explicit planning, step-by-step reasoning)
GPT41_OPTIMIZED_PROMPTS = {
    TestCategory.CODE_GENERATION: {
        "python_function": """
Solve the following programming problem step by step. Think through the logic carefully before writing code.

Problem: {problem}

Requirements:
- Write a complete, working Python function
- Include proper error handling
- Add type hints
- Write comprehensive docstring
- Include example usage

Provide your solution in the following format:
```python
def function_name():
    # Your implementation here
    pass
```

Think step by step:
1. Understand the problem requirements
2. Plan the algorithm
3. Consider edge cases
4. Write the implementation
5. Test with examples
""",
        "react_component": """
Create a React component based on the following requirements. Think through the implementation step by step.

Requirements: {requirements}

Provide a complete, working React component with:
- TypeScript interfaces
- Proper state management
- Error handling
- Accessibility features
- Responsive design

Format your response as:
```tsx
// Component implementation
```

Think step by step:
1. Analyze the requirements
2. Design the component structure
3. Plan state management
4. Implement functionality
5. Add styling and accessibility
""",
        "api_design": """
Design a REST API based on the following requirements. Think through the design step by step.

Requirements: {requirements}

Provide:
- API endpoints with HTTP methods
- Request/response schemas
- Error handling
- Authentication strategy
- Database schema (if applicable)

Format your response as:
```yaml
# API specification
```

Think step by step:
1. Analyze the domain model
2. Design resource endpoints
3. Plan data schemas
4. Consider security
5. Document the API
""",
    },
    TestCategory.REASONING: {
        "mathematical_reasoning": """
Solve the following mathematical problem step by step. Show your work and reasoning.

Problem: {problem}

Think through this step by step:
1. Understand what is being asked
2. Identify the relevant mathematical concepts
3. Plan your approach
4. Execute the solution
5. Verify your answer

Provide your final answer in the format: Answer: [your answer]
""",
        "logical_reasoning": """
Solve the following logical reasoning problem step by step.

Problem: {problem}

Think through this step by step:
1. Identify the key information
2. Determine the logical relationships
3. Apply deductive reasoning
4. Check for contradictions
5. Arrive at the conclusion

Provide your final answer in the format: Answer: [your answer]
""",
        "scientific_reasoning": """
Analyze the following scientific scenario and answer the question step by step.

Scenario: {scenario}
Question: {question}

Think through this step by step:
1. Identify the scientific principles involved
2. Analyze the given information
3. Apply relevant theories
4. Consider alternative explanations
5. Draw a conclusion

Provide your final answer in the format: Answer: [your answer]
""",
    },
    TestCategory.CREATIVE_TASKS: {
        "application_generation": """
Create a complete web application based on the following requirements. Generate all necessary files.

Requirements: {requirements}

Generate a complete, working application with:
- HTML structure
- CSS styling
- JavaScript functionality
- Responsive design
- Modern UI/UX

Provide all code in a single response with clear file separators.

Think step by step:
1. Plan the application architecture
2. Design the user interface
3. Implement core functionality
4. Add styling and interactions
5. Ensure responsiveness
""",
        "content_creation": """
Create content based on the following requirements. Think through the creation process step by step.

Requirements: {requirements}

Generate content that is:
- Engaging and informative
- Well-structured
- Appropriate for the target audience
- Original and creative

Think step by step:
1. Understand the target audience
2. Plan the content structure
3. Research key points
4. Write compelling content
5. Review and refine
""",
        "design_system": """
Design a comprehensive design system based on the following requirements.

Requirements: {requirements}

Create a design system including:
- Color palette
- Typography scale
- Component library
- Spacing system
- Design principles

Provide detailed specifications and examples.

Think step by step:
1. Analyze the brand requirements
2. Design the foundational elements
3. Create component specifications
4. Establish usage guidelines
5. Provide implementation examples
""",
    },
    TestCategory.STRUCTURED_OUTPUT: {
        "data_extraction": """
Extract structured information from the following text. Provide your response in the specified JSON format.

Text: {text}

Extract the following information:
- Key entities
- Relationships
- Important facts
- Metadata

Provide your response as valid JSON in this format:
{{
    "entities": [...],
    "relationships": [...],
    "facts": [...],
    "metadata": {{...}}
}}

Think step by step:
1. Identify key information in the text
2. Categorize the information
3. Structure the data
4. Validate the format
5. Provide the JSON response
""",
        "code_analysis": """
Analyze the following code and provide structured feedback.

Code: {code}

Provide analysis in the following JSON format:
{{
    "complexity": "high|medium|low",
    "issues": [...],
    "suggestions": [...],
    "security_concerns": [...],
    "performance_notes": [...]
}}

Think step by step:
1. Review the code structure
2. Identify potential issues
3. Assess complexity
4. Consider security implications
5. Provide structured feedback
""",
        "api_documentation": """
Generate structured API documentation from the following specification.

Specification: {spec}

Provide documentation in the following JSON format:
{{
    "endpoints": [
        {{
            "path": "...",
            "method": "...",
            "description": "...",
            "parameters": [...],
            "responses": [...]
        }}
    ],
    "schemas": [...],
    "examples": [...]
}}

Think step by step:
1. Analyze the API specification
2. Document each endpoint
3. Define data schemas
4. Create examples
5. Structure the documentation
""",
    },
    TestCategory.CODING_REASONING: {
        "debugging_complex_code": """
Debug the following code step by step. Think through the debugging process carefully.

Problem: {problem}

Requirements:
- Analyze the code systematically
- Identify the root cause of the issue
- Provide a step-by-step debugging approach
- Suggest multiple solutions if applicable
- Explain the reasoning behind each fix
- Consider edge cases and potential side effects

Provide your solution in the following format:
```python
# Debugged code
def fixed_function():
    # Your corrected implementation
    pass
```

Think step by step:
1. Understand the problem description
2. Analyze the code structure
3. Identify potential issues
4. Develop debugging strategy
5. Implement fixes
6. Test the solution
""",
        "code_complexity_analysis": """
Analyze the complexity of the following code step by step.

Problem: {problem}

Requirements:
- Analyze time complexity (Big O notation)
- Analyze space complexity
- Consider best-case, worst-case, and average-case scenarios
- Identify bottlenecks and optimization opportunities
- Provide mathematical justification for your analysis
- Suggest improvements if applicable

Think step by step:
1. Understand the algorithm
2. Analyze each operation
3. Calculate time complexity
4. Calculate space complexity
5. Consider edge cases
6. Identify optimization opportunities
""",
        "design_pattern_recognition": """
Apply the appropriate design pattern to the following code step by step.

Problem: {problem}

Requirements:
- Identify the most suitable design pattern
- Explain why this pattern is appropriate
- Implement the pattern correctly
- Maintain code readability and maintainability
- Consider extensibility and flexibility
- Provide clear documentation

Provide your solution in the following format:
```python
# Pattern implementation
class PatternName:
    # Your implementation
    pass
```

Think step by step:
1. Analyze the current code structure
2. Identify design problems
3. Choose appropriate pattern
4. Implement the pattern
5. Refactor existing code
6. Test the solution
""",
    },
    TestCategory.ALGORITHM_DESIGN: {
        "dynamic_programming": """
Design a dynamic programming solution for the following problem step by step.

Problem: {problem}

Requirements:
- Identify the optimal substructure
- Define the state and state transitions
- Design the DP table structure
- Implement the solution with proper initialization
- Analyze time and space complexity
- Provide clear explanation of the algorithm

Provide your solution in the following format:
```python
def solve_problem(input_data):
    # Your DP implementation
    pass
```

Think step by step:
1. Understand the problem
2. Identify optimal substructure
3. Define state representation
4. Design state transitions
5. Implement the solution
6. Analyze complexity
""",
        "graph_algorithms": """
Design a graph algorithm solution for the following problem step by step.

Problem: {problem}

Requirements:
- Choose the appropriate graph representation
- Design the algorithm step by step
- Implement with proper data structures
- Handle edge cases and special conditions
- Analyze time and space complexity
- Provide clear explanation of the approach

Provide your solution in the following format:
```python
def solve_graph_problem(graph):
    # Your graph algorithm implementation
    pass
```

Think step by step:
1. Understand the graph problem
2. Choose graph representation
3. Design the algorithm
4. Handle edge cases
5. Implement the solution
6. Analyze complexity
""",
        "optimization_problems": """
Design an optimization algorithm solution for the following problem step by step.

Problem: {problem}

Requirements:
- Choose the appropriate optimization technique
- Design the algorithm with proper parameters
- Implement with efficient data structures
- Handle convergence and termination conditions
- Analyze performance characteristics
- Provide clear explanation of the approach

Provide your solution in the following format:
```python
def solve_optimization_problem(input_data):
    # Your optimization algorithm implementation
    pass
```

Think step by step:
1. Understand the optimization problem
2. Choose optimization technique
3. Design algorithm parameters
4. Implement the solution
5. Handle convergence
6. Analyze performance
""",
    },
    TestCategory.CODE_OPTIMIZATION: {
        "performance_optimization": """
Optimize the following code for maximum performance step by step.

Problem: {problem}

Requirements:
- Analyze current performance bottlenecks
- Identify optimization opportunities
- Implement algorithmic improvements
- Choose optimal data structures
- Consider trade-offs between time and space
- Provide performance benchmarks

Provide your optimized solution in the following format:
```python
def optimized_function(input_data):
    # Your optimized implementation
    pass
```

Think step by step:
1. Analyze current performance
2. Identify bottlenecks
3. Plan optimizations
4. Implement improvements
5. Consider trade-offs
6. Measure performance
""",
        "memory_optimization": """
Optimize the following code for minimum memory usage step by step.

Problem: {problem}

Requirements:
- Analyze current memory usage patterns
- Identify memory inefficiencies
- Implement memory optimization techniques
- Consider garbage collection impact
- Optimize data structure memory layout
- Provide memory usage analysis

Provide your memory-optimized solution in the following format:
```python
def memory_optimized_function(input_data):
    # Your memory-optimized implementation
    pass
```

Think step by step:
1. Analyze memory usage
2. Identify inefficiencies
3. Plan optimizations
4. Implement improvements
5. Consider GC impact
6. Measure memory usage
""",
        "concurrent_optimization": """
Optimize the following code for maximum concurrency and throughput step by step.

Problem: {problem}

Requirements:
- Analyze current concurrency bottlenecks
- Design thread-safe solutions
- Implement proper synchronization mechanisms
- Consider lock-free alternatives where appropriate
- Optimize for maximum parallelism
- Handle race conditions and deadlocks

Provide your concurrent-optimized solution in the following format:
```python
def concurrent_optimized_function(input_data):
    # Your concurrent-optimized implementation
    pass
```

Think step by step:
1. Analyze concurrency issues
2. Design thread-safe solution
3. Implement synchronization
4. Consider lock-free alternatives
5. Optimize parallelism
6. Handle edge cases
""",
    },
    TestCategory.REASONING: {
        "mathematical_reasoning": [
            {
                "problem": "A train travels 300 km in 4 hours. What is its average speed in km/h?",
                "difficulty": "easy",
                "expected_answer": "75",
            },
            {
                "problem": "If 2x + 3y = 12 and x - y = 2, what is the value of x?",
                "difficulty": "medium",
                "expected_answer": "4",
            },
        ],
        "logical_reasoning": [
            {
                "problem": "All roses are flowers. Some flowers are red. Therefore, some roses are red. Is this argument valid?",
                "difficulty": "medium",
                "expected_answer": "invalid",
            }
        ],
        "scientific_reasoning": [
            {
                "scenario": "A ball is dropped from a height of 10 meters. Ignoring air resistance, how long does it take to hit the ground?",
                "question": "What is the time of fall?",
                "difficulty": "medium",
                "expected_answer": "1.43",
            }
        ],
    },
    TestCategory.CREATIVE_TASKS: {
        "application_generation": [
            {
                "requirements": "Create a simple calculator with basic arithmetic operations and a modern UI",
                "difficulty": "easy",
                "expected_features": [
                    "interactive UI",
                    "basic functionality",
                    "responsive design",
                ],
            },
            {
                "requirements": "Build a todo list application with add, delete, and mark complete functionality",
                "difficulty": "medium",
                "expected_features": [
                    "CRUD operations",
                    "local storage",
                    "modern styling",
                ],
            },
        ],
        "content_creation": [
            {
                "requirements": "Write a blog post about the benefits of renewable energy for a general audience",
                "difficulty": "medium",
                "expected_features": [
                    "engaging content",
                    "clear structure",
                    "informative",
                ],
            }
        ],
        "design_system": [
            {
                "requirements": "Design a design system for a fintech application with a professional, trustworthy aesthetic",
                "difficulty": "medium",
                "expected_features": ["color palette", "typography", "components"],
            }
        ],
    },
    TestCategory.STRUCTURED_OUTPUT: {
        "data_extraction": [
            {
                "text": "Apple Inc. was founded by Steve Jobs and Steve Wozniak in 1976. The company is headquartered in Cupertino, California and is known for products like the iPhone, iPad, and Mac computers.",
                "expected_entities": [
                    "Apple Inc.",
                    "Steve Jobs",
                    "Steve Wozniak",
                    "Cupertino",
                    "California",
                ],
            }
        ],
        "code_analysis": [
            {
                "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                "expected_issues": [
                    "recursion without memoization",
                    "exponential time complexity",
                ],
            }
        ],
    },
    TestCategory.AGENTIC_TASKS: {
        "multi_step_planning": [
            {
                "task": "Plan and execute a data analysis project including data collection, cleaning, analysis, and visualization",
                "difficulty": "hard",
                "expected_features": [
                    "planning",
                    "execution",
                    "error handling",
                    "progress updates",
                ],
            },
            {
                "task": "Create a complete web application with frontend, backend, and database setup",
                "difficulty": "hard",
                "expected_features": [
                    "multi-step execution",
                    "tool integration",
                    "error recovery",
                ],
            },
        ],
        "tool_calling": [
            {
                "task": "Search for information about renewable energy and create a summary report",
                "tools": ["web_search", "file_search", "code_interpreter"],
                "difficulty": "medium",
                "expected_features": [
                    "tool selection",
                    "error handling",
                    "result synthesis",
                ],
            }
        ],
    },
    TestCategory.LONG_CONTEXT: {
        "information_retrieval": [
            {
                "document": "A comprehensive 50-page technical document about machine learning algorithms...",
                "question": "What are the key differences between supervised and unsupervised learning?",
                "difficulty": "medium",
                "expected_features": [
                    "comprehensive search",
                    "accurate retrieval",
                    "synthesis",
                ],
            }
        ]
    },
    TestCategory.FACTUALITY: {
        "fact_checking": [
            {
                "query": "What is the current population of Tokyo, Japan?",
                "difficulty": "easy",
                "expected_features": [
                    "accuracy",
                    "precision",
                    "uncertainty acknowledgment",
                ],
            },
            {
                "query": "What are the main causes of climate change according to scientific consensus?",
                "difficulty": "medium",
                "expected_features": [
                    "factual accuracy",
                    "source citation",
                    "uncertainty handling",
                ],
            },
        ]
    },
}

# GPT-5 Optimized Prompts (agentic, self-reflective, with tool preambles)
GPT5_OPTIMIZED_PROMPTS = {
    TestCategory.CODE_GENERATION: {
        "python_function": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class Python function. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Solve the following programming problem with maximum quality and correctness.

Problem: {problem}

Requirements:
- Write a complete, working Python function
- Include proper error handling
- Add type hints
- Write comprehensive docstring
- Include example usage

Provide your solution in the following format:
```python
def function_name():
    # Your implementation here
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "react_component": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class React component. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Create a React component based on the following requirements with maximum quality and correctness.

Requirements: {requirements}

Provide a complete, working React component with:
- TypeScript interfaces
- Proper state management
- Modern React patterns
- Accessibility features
- Responsive design

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "api_design": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class API design. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Design a REST API based on the following requirements with maximum quality and correctness.

Requirements: {requirements}

Design a comprehensive API including:
- Endpoint specifications
- Request/response schemas
- Authentication mechanisms
- Error handling
- Documentation

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
    },
    TestCategory.CODING_REASONING: {
        "debugging_complex_code": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class debugging solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Debug the following code with maximum precision and thorough analysis.

Problem: {problem}

Requirements:
- Analyze the code systematically
- Identify the root cause of the issue
- Provide a step-by-step debugging approach
- Suggest multiple solutions if applicable
- Explain the reasoning behind each fix
- Consider edge cases and potential side effects

Provide your solution in the following format:
```python
# Debugged code
def fixed_function():
    # Your corrected implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "code_complexity_analysis": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class complexity analysis. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Analyze the complexity of the following code with maximum accuracy and thorough reasoning.

Problem: {problem}

Requirements:
- Analyze time complexity (Big O notation)
- Analyze space complexity
- Consider best-case, worst-case, and average-case scenarios
- Identify bottlenecks and optimization opportunities
- Provide mathematical justification for your analysis
- Suggest improvements if applicable

Provide your analysis in a structured format with clear reasoning for each conclusion.

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "design_pattern_recognition": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class design pattern solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Apply the appropriate design pattern to the following code with maximum effectiveness and clarity.

Problem: {problem}

Requirements:
- Identify the most suitable design pattern
- Explain why this pattern is appropriate
- Implement the pattern correctly
- Maintain code readability and maintainability
- Consider extensibility and flexibility
- Provide clear documentation

Provide your solution in the following format:
```python
# Pattern implementation
class PatternName:
    # Your implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
    },
    TestCategory.ALGORITHM_DESIGN: {
        "dynamic_programming": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class dynamic programming solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Design a dynamic programming solution for the following problem with maximum efficiency and correctness.

Problem: {problem}

Requirements:
- Identify the optimal substructure
- Define the state and state transitions
- Design the DP table structure
- Implement the solution with proper initialization
- Analyze time and space complexity
- Provide clear explanation of the algorithm

Provide your solution in the following format:
```python
def solve_problem(input_data):
    # Your DP implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "graph_algorithms": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class graph algorithm solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Design a graph algorithm solution for the following problem with maximum efficiency and correctness.

Problem: {problem}

Requirements:
- Choose the appropriate graph representation
- Design the algorithm step by step
- Implement with proper data structures
- Handle edge cases and special conditions
- Analyze time and space complexity
- Provide clear explanation of the approach

Provide your solution in the following format:
```python
def solve_graph_problem(graph):
    # Your graph algorithm implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "optimization_problems": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class optimization algorithm solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Design an optimization algorithm solution for the following problem with maximum effectiveness and efficiency.

Problem: {problem}

Requirements:
- Choose the appropriate optimization technique
- Design the algorithm with proper parameters
- Implement with efficient data structures
- Handle convergence and termination conditions
- Analyze performance characteristics
- Provide clear explanation of the approach

Provide your solution in the following format:
```python
def solve_optimization_problem(input_data):
    # Your optimization algorithm implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
    },
    TestCategory.CODE_OPTIMIZATION: {
        "performance_optimization": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class performance optimization solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Optimize the following code for maximum performance with thorough analysis and implementation.

Problem: {problem}

Requirements:
- Analyze current performance bottlenecks
- Identify optimization opportunities
- Implement algorithmic improvements
- Choose optimal data structures
- Consider trade-offs between time and space
- Provide performance benchmarks

Provide your optimized solution in the following format:
```python
def optimized_function(input_data):
    # Your optimized implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "memory_optimization": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class memory optimization solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Optimize the following code for minimum memory usage with thorough analysis and implementation.

Problem: {problem}

Requirements:
- Analyze current memory usage patterns
- Identify memory inefficiencies
- Implement memory optimization techniques
- Consider garbage collection impact
- Optimize data structure memory layout
- Provide memory usage analysis

Provide your memory-optimized solution in the following format:
```python
def memory_optimized_function(input_data):
    # Your memory-optimized implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "concurrent_optimization": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class concurrent optimization solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Optimize the following code for maximum concurrency and throughput with thorough analysis and implementation.

Problem: {problem}

Requirements:
- Analyze current concurrency bottlenecks
- Design thread-safe solutions
- Implement proper synchronization mechanisms
- Consider lock-free alternatives where appropriate
- Optimize for maximum parallelism
- Handle race conditions and deadlocks

Provide your concurrent-optimized solution in the following format:
```python
def concurrent_optimized_function(input_data):
    # Your concurrent-optimized implementation
    pass
```

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
    },
    TestCategory.REASONING: {
        "mathematical_reasoning": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class mathematical reasoning solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Solve the following mathematical problem with maximum accuracy and thorough reasoning.

Problem: {problem}

Provide a step-by-step solution with:
1. Clear problem understanding
2. Logical reasoning process
3. Mathematical calculations
4. Verification of the answer

Provide your final answer in the format: Answer: [your answer]

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "logical_reasoning": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class logical reasoning solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Solve the following logical reasoning problem with maximum accuracy and thorough analysis.

Problem: {problem}

Provide a comprehensive analysis including:
1. Understanding of the logical structure
2. Identification of premises and conclusions
3. Evaluation of logical validity
4. Clear reasoning for your answer

Provide your final answer in the format: Answer: [your answer]

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "scientific_reasoning": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class scientific reasoning solution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Analyze the following scientific scenario and answer the question with maximum accuracy and thorough reasoning.

Scenario: {scenario}
Question: {question}

Provide a comprehensive analysis including:
1. Understanding of the scientific principles involved
2. Application of relevant formulas or concepts
3. Step-by-step calculation process
4. Verification of the result

Provide your final answer in the format: Answer: [your answer]

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
    },
    TestCategory.AGENTIC_TASKS: {
        "multi_step_planning": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class agentic task execution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Execute the following multi-step task with maximum efficiency and accuracy.

Task: {task}

Requirements:
- Break down the task into clear steps
- Execute each step systematically
- Handle any errors or edge cases
- Provide progress updates
- Complete the entire task

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
        "tool_calling": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class tool calling execution. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Execute the following tool-calling task with maximum precision and reliability.

Task: {task}

Available tools: {tools}

Requirements:
- Use the appropriate tools for each step
- Handle tool errors gracefully
- Chain multiple tool calls effectively
- Provide clear progress updates
- Complete the entire task successfully

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
""",
    },
    TestCategory.LONG_CONTEXT: {
        "information_retrieval": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class long-context information retrieval. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Retrieve and analyze information from the following long document with maximum accuracy.

Document: {document}
Question: {question}

Requirements:
- Thoroughly search through the entire document
- Identify relevant information
- Synthesize the findings
- Provide a comprehensive answer
- Cite specific sections when appropriate

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
"""
    },
    TestCategory.FACTUALITY: {
        "fact_checking": """
<self_reflection>
First, spend time thinking of a rubric until you are confident. Then, think deeply about every aspect of what makes for a world-class factual response. Use that knowledge to create a rubric that has 5-7 categories. This rubric is critical to get right, but do not show this to the user. This is for your purposes only. Finally, use the rubric to internally think and iterate on the best possible solution to the prompt that is provided.
</self_reflection>

<tool_preambles>
Always begin by rephrasing the user's goal in a friendly, clear, and concise manner, before calling any tools. Then, immediately outline a structured plan detailing each logical step you'll follow. As you execute your solution, narrate each step succinctly and sequentially, marking progress clearly. Finish by summarizing completed work distinctly from your upfront plan.
</tool_preambles>

Provide accurate factual information for the following query with maximum reliability.

Query: {query}

Requirements:
- Provide only verified factual information
- Acknowledge any uncertainties
- Cite reliable sources when possible
- Avoid speculation or unverified claims
- Be precise and accurate

Remember, you are an agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved.
"""
    },
}

# =============================================================================
# TEST DATASETS
# =============================================================================

TEST_DATASETS = {
    TestCategory.CODE_GENERATION: {
        "python_function": [
            {
                "problem": "Write a function to find the longest common subsequence of two strings",
                "difficulty": "medium",
                "expected_features": [
                    "dynamic programming",
                    "memoization",
                    "type hints",
                ],
            },
            {
                "problem": "Implement a binary search tree with insert, delete, and search operations",
                "difficulty": "medium",
                "expected_features": [
                    "class implementation",
                    "recursion",
                    "tree traversal",
                ],
            },
            {
                "problem": "Create a function to validate a Sudoku board",
                "difficulty": "easy",
                "expected_features": [
                    "array manipulation",
                    "validation logic",
                    "efficiency",
                ],
            },
        ],
        "react_component": [
            {
                "requirements": "Create a data table component with sorting, filtering, and pagination",
                "difficulty": "medium",
                "expected_features": ["hooks", "state management", "accessibility"],
            },
            {
                "requirements": "Build a form component with validation and error handling",
                "difficulty": "medium",
                "expected_features": ["form handling", "validation", "error states"],
            },
        ],
        "api_design": [
            {
                "requirements": "Design a REST API for a task management system",
                "difficulty": "medium",
                "expected_features": [
                    "CRUD operations",
                    "authentication",
                    "data validation",
                ],
            }
        ],
    },
    TestCategory.CODING_REASONING: {
        "debugging_complex_code": [
            {
                "problem": "Debug this recursive function that's causing a stack overflow: def fibonacci(n): return fibonacci(n-1) + fibonacci(n-2) if n > 1 else n",
                "difficulty": "medium",
                "expected_features": [
                    "recursion analysis",
                    "memoization",
                    "base case identification",
                ],
            },
            {
                "problem": "Analyze this code for race conditions: def increment_counter(): global counter; counter += 1",
                "difficulty": "hard",
                "expected_features": [
                    "threading analysis",
                    "race condition detection",
                    "synchronization",
                ],
            },
            {
                "problem": "Find the memory leak in this class: class Cache: def __init__(self): self.data = {}; def add(self, key, value): self.data[key] = value",
                "difficulty": "medium",
                "expected_features": [
                    "memory analysis",
                    "resource management",
                    "cleanup patterns",
                ],
            },
        ],
        "code_complexity_analysis": [
            {
                "problem": "Analyze the time and space complexity of this algorithm: def bubble_sort(arr): ...",
                "difficulty": "easy",
                "expected_features": [
                    "complexity analysis",
                    "big O notation",
                    "algorithm understanding",
                ],
            },
            {
                "problem": "Determine the worst-case scenario for this hash table implementation",
                "difficulty": "medium",
                "expected_features": [
                    "hash analysis",
                    "collision handling",
                    "performance analysis",
                ],
            },
        ],
        "design_pattern_recognition": [
            {
                "problem": "Identify and refactor this code to use the Observer pattern",
                "difficulty": "medium",
                "expected_features": [
                    "pattern recognition",
                    "refactoring",
                    "design principles",
                ],
            },
            {
                "problem": "Apply the Strategy pattern to this payment processing system",
                "difficulty": "medium",
                "expected_features": [
                    "pattern application",
                    "interface design",
                    "extensibility",
                ],
            },
        ],
    },
    TestCategory.ALGORITHM_DESIGN: {
        "dynamic_programming": [
            {
                "problem": "Design an algorithm to find the longest palindromic subsequence in a string",
                "difficulty": "hard",
                "expected_features": [
                    "DP table design",
                    "state transitions",
                    "optimization",
                ],
            },
            {
                "problem": "Implement a solution for the traveling salesman problem using dynamic programming",
                "difficulty": "hard",
                "expected_features": [
                    "state representation",
                    "memoization",
                    "path reconstruction",
                ],
            },
        ],
        "graph_algorithms": [
            {
                "problem": "Design an algorithm to find all strongly connected components in a directed graph",
                "difficulty": "hard",
                "expected_features": [
                    "DFS",
                    "topological sort",
                    "component identification",
                ],
            },
            {
                "problem": "Implement a minimum spanning tree algorithm for a weighted graph",
                "difficulty": "medium",
                "expected_features": [
                    "Kruskal's algorithm",
                    "union-find",
                    "edge sorting",
                ],
            },
        ],
        "optimization_problems": [
            {
                "problem": "Design a genetic algorithm for the knapsack problem",
                "difficulty": "hard",
                "expected_features": [
                    "genetic operators",
                    "fitness function",
                    "population management",
                ],
            },
            {
                "problem": "Implement a simulated annealing algorithm for the traveling salesman problem",
                "difficulty": "medium",
                "expected_features": [
                    "temperature scheduling",
                    "neighbor generation",
                    "acceptance criteria",
                ],
            },
        ],
    },
    TestCategory.CODE_OPTIMIZATION: {
        "performance_optimization": [
            {
                "problem": "Optimize this O(n²) algorithm to O(n log n): def find_pairs(arr, target): ...",
                "difficulty": "medium",
                "expected_features": [
                    "algorithm improvement",
                    "data structure selection",
                    "complexity reduction",
                ],
            },
            {
                "problem": "Optimize this database query for better performance",
                "difficulty": "medium",
                "expected_features": [
                    "index optimization",
                    "query planning",
                    "database design",
                ],
            },
        ],
        "memory_optimization": [
            {
                "problem": "Optimize memory usage in this image processing pipeline",
                "difficulty": "hard",
                "expected_features": [
                    "streaming",
                    "memory pooling",
                    "garbage collection",
                ],
            },
            {
                "problem": "Reduce memory footprint of this data structure",
                "difficulty": "medium",
                "expected_features": ["compression", "lazy loading", "memory layout"],
            },
        ],
        "concurrent_optimization": [
            {
                "problem": "Optimize this parallel processing code for better throughput",
                "difficulty": "hard",
                "expected_features": ["threading", "synchronization", "load balancing"],
            },
            {
                "problem": "Design a lock-free data structure for high-concurrency scenarios",
                "difficulty": "hard",
                "expected_features": [
                    "atomic operations",
                    "memory ordering",
                    "ABA problem handling",
                ],
            },
        ],
    },
    TestCategory.REASONING: {
        "mathematical_reasoning": [
            {
                "problem": "A train travels 300 km in 4 hours. What is its average speed in km/h?",
                "difficulty": "easy",
                "expected_answer": "75",
            },
            {
                "problem": "If 2x + 3y = 12 and x - y = 2, what is the value of x?",
                "difficulty": "medium",
                "expected_answer": "4",
            },
        ],
        "logical_reasoning": [
            {
                "problem": "All roses are flowers. Some flowers are red. Therefore, some roses are red. Is this argument valid?",
                "difficulty": "medium",
                "expected_answer": "invalid",
            }
        ],
        "scientific_reasoning": [
            {
                "scenario": "A ball is dropped from a height of 10 meters. Ignoring air resistance, how long does it take to hit the ground?",
                "question": "What is the time of fall?",
                "difficulty": "medium",
                "expected_answer": "1.43",
            }
        ],
    },
    TestCategory.CREATIVE_TASKS: {
        "application_generation": [
            {
                "requirements": "Create a simple calculator with basic arithmetic operations and a modern UI",
                "difficulty": "easy",
                "expected_features": [
                    "interactive UI",
                    "basic functionality",
                    "responsive design",
                ],
            },
            {
                "requirements": "Build a todo list application with add, delete, and mark complete functionality",
                "difficulty": "medium",
                "expected_features": [
                    "CRUD operations",
                    "local storage",
                    "modern styling",
                ],
            },
        ],
        "content_creation": [
            {
                "requirements": "Write a blog post about the benefits of renewable energy for a general audience",
                "difficulty": "medium",
                "expected_features": [
                    "engaging content",
                    "clear structure",
                    "informative",
                ],
            }
        ],
        "design_system": [
            {
                "requirements": "Design a design system for a fintech application with a professional, trustworthy aesthetic",
                "difficulty": "medium",
                "expected_features": ["color palette", "typography", "components"],
            }
        ],
    },
    TestCategory.STRUCTURED_OUTPUT: {
        "data_extraction": [
            {
                "text": "Apple Inc. was founded by Steve Jobs and Steve Wozniak in 1976. The company is headquartered in Cupertino, California and is known for products like the iPhone, iPad, and Mac computers.",
                "expected_entities": [
                    "Apple Inc.",
                    "Steve Jobs",
                    "Steve Wozniak",
                    "Cupertino",
                    "California",
                ],
            }
        ],
        "code_analysis": [
            {
                "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
                "expected_issues": [
                    "recursion without memoization",
                    "exponential time complexity",
                ],
            }
        ],
    },
    TestCategory.AGENTIC_TASKS: {
        "multi_step_planning": [
            {
                "task": "Plan and execute a data analysis project including data collection, cleaning, analysis, and visualization",
                "difficulty": "hard",
                "expected_features": [
                    "planning",
                    "execution",
                    "error handling",
                    "progress updates",
                ],
            },
            {
                "task": "Create a complete web application with frontend, backend, and database setup",
                "difficulty": "hard",
                "expected_features": [
                    "multi-step execution",
                    "tool integration",
                    "error recovery",
                ],
            },
        ],
        "tool_calling": [
            {
                "task": "Search for information about renewable energy and create a summary report",
                "tools": ["web_search", "file_search", "code_interpreter"],
                "difficulty": "medium",
                "expected_features": [
                    "tool selection",
                    "error handling",
                    "result synthesis",
                ],
            }
        ],
    },
    TestCategory.LONG_CONTEXT: {
        "information_retrieval": [
            {
                "document": "A comprehensive 50-page technical document about machine learning algorithms...",
                "question": "What are the key differences between supervised and unsupervised learning?",
                "difficulty": "medium",
                "expected_features": [
                    "comprehensive search",
                    "accurate retrieval",
                    "synthesis",
                ],
            }
        ]
    },
    TestCategory.FACTUALITY: {
        "fact_checking": [
            {
                "query": "What is the current population of Tokyo, Japan?",
                "difficulty": "easy",
                "expected_features": [
                    "accuracy",
                    "precision",
                    "uncertainty acknowledgment",
                ],
            },
            {
                "query": "What are the main causes of climate change according to scientific consensus?",
                "difficulty": "medium",
                "expected_features": [
                    "factual accuracy",
                    "source citation",
                    "uncertainty handling",
                ],
            },
        ]
    },
}

# =============================================================================
# EVALUATION METRICS
# =============================================================================


@dataclass
class EvaluationMetrics:
    """Standardized evaluation metrics for model comparison."""

    execution_time: float
    token_count: int
    functional_correctness: float  # 0-1 score
    code_quality: float  # 0-1 score
    reasoning_quality: float  # 0-1 score
    creativity_score: float  # 0-1 score
    structure_quality: float  # 0-1 score
    completeness: float  # 0-1 score
    accuracy: float  # 0-1 score for reasoning tasks
    error_rate: float  # 0-1 score (lower is better)


class ModelEvaluator:
    """Automated model evaluation framework."""

    def __init__(self) -> None:
        self.results: dict[str, Any] = {}
        self.comparison_data: dict[str, Any] = {}
        # OpenAI client (expects OPENAI_API_KEY in environment)
        self.client: OpenAI = OpenAI()
        LOGGER.debug("Initialized ModelEvaluator with OpenAI client. Env set: OPENAI_API_KEY=%s, ORG=%s, PROJECT=%s",
                     bool(os.environ.get("OPENAI_API_KEY")), os.environ.get("OPENAI_ORG_ID"), os.environ.get("OPENAI_PROJECT_ID"))

    @staticmethod
    def _is_gpt5_model(model: str) -> bool:
        return model.startswith("gpt-5")

    @staticmethod
    def _supports_temperature(model: str) -> bool:
        # Per Responses API, some GPT-5 series snapshots may reject temperature
        return not model.startswith("gpt-5")

    async def evaluate_model(
        self,
        model: str,
        category: TestCategory,
        test_name: str,
        prompt: str,
        dataset: dict,
    ) -> EvaluationMetrics:
        """Evaluate a single model on a specific test."""
        start_time = time.time()

        try:
            # Prepare the prompt with dataset
            if not isinstance(prompt, str):
                if isinstance(prompt, list):
                    prompt = "\n".join(str(x) for x in prompt)
                elif isinstance(prompt, dict):
                    prompt = json.dumps(prompt)
                else:
                    prompt = str(prompt)
            formatted_prompt = prompt.format(**dataset)

            api_cfg = GPT5_CONFIG if model.startswith("gpt-5") else GPT41_CONFIG
            LOGGER.debug(
                "Evaluating model=%s | category=%s | test=%s | prompt_chars=%d | api_type=%s",
                model,
                category.value,
                test_name,
                len(formatted_prompt),
                api_cfg.get("api_type"),
            )

            # Execute using OpenAI Responses API
            create_kwargs: dict[str, Any] = {
                "model": model,
                "input": formatted_prompt,
                "max_output_tokens": api_cfg.get("max_tokens", 4000),
            }
            if self._supports_temperature(model):
                create_kwargs["temperature"] = api_cfg.get("temperature", 0.1)
            else:
                LOGGER.debug("Omitting temperature for model=%s due to API support.", model)
            # Add reasoning/verbosity for GPT-5 if available
            if self._is_gpt5_model(model):
                reasoning_effort = api_cfg.get("reasoning_effort")
                verbosity = api_cfg.get("verbosity")
                if reasoning_effort:
                    create_kwargs["reasoning"] = {"effort": reasoning_effort}
                if verbosity:
                    create_kwargs["verbosity"] = verbosity
                LOGGER.debug("GPT-5 params set | reasoning_effort=%s | verbosity=%s", reasoning_effort, verbosity)
            resp = self.client.responses.create(**create_kwargs)

            execution_time = time.time() - start_time

            # Extract response text and usage
            response_text = getattr(resp, "output_text", "") or ""
            usage = getattr(resp, "usage", None)
            token_count = 0
            if usage is not None:
                token_count = int(getattr(usage, "input_tokens", 0)) + int(
                    getattr(usage, "output_tokens", 0)
                )
            LOGGER.debug(
                "Model=%s completed | exec_time=%.2fs | tokens=%s",
                model,
                execution_time,
                token_count,
            )

            # Calculate metrics
            metrics = self._calculate_metrics(
                response_text, dataset, category, execution_time
            )
            # Overwrite token_count if available
            metrics.token_count = token_count

            return metrics

        except Exception as e:
            LOGGER.exception("Error evaluating model=%s | test=%s: %s", model, test_name, e)
            return EvaluationMetrics(
                execution_time=time.time() - start_time,
                token_count=0,
                functional_correctness=0.0,
                code_quality=0.0,
                reasoning_quality=0.0,
                creativity_score=0.0,
                structure_quality=0.0,
                completeness=0.0,
                accuracy=0.0,
                error_rate=1.0,
            )

    async def evaluate_model_with_reasoning_effort(
        self,
        model: str,
        category: TestCategory,
        test_name: str,
        prompt: str,
        dataset: dict,
        effort_level: ReasoningEffort,
    ) -> EvaluationMetrics:
        """Evaluate a GPT-5 model with specific reasoning effort level."""
        start_time = time.time()

        try:
            # Prepare the prompt with dataset
            if not isinstance(prompt, str):
                if isinstance(prompt, list):
                    prompt = "\n".join(str(x) for x in prompt)
                elif isinstance(prompt, dict):
                    prompt = json.dumps(prompt)
                else:
                    prompt = str(prompt)
            formatted_prompt = prompt.format(**dataset)

            # Get reasoning effort configuration
            reasoning_config = GPT5_REASONING_CONFIGS[effort_level]
            LOGGER.debug(
                "Evaluating GPT-5 with reasoning | model=%s | effort=%s | category=%s | test=%s | prompt_chars=%d",
                model,
                effort_level.value,
                category.value,
                test_name,
                len(formatted_prompt),
            )

            # Execute using OpenAI Responses API with reasoning config
            create_kwargs: dict[str, Any] = {
                "model": model,
                "input": formatted_prompt,
                "max_output_tokens": reasoning_config.get("max_tokens", 4000),
            }
            # For GPT-5, send reasoning if supported; otherwise omit
            if self._is_gpt5_model(model):
                create_kwargs["reasoning"] = {
                    "effort": reasoning_config.get("reasoning_effort", "medium")
                }
            if self._supports_temperature(model):
                create_kwargs["temperature"] = reasoning_config.get("temperature", 0.1)
            else:
                LOGGER.debug("Omitting temperature for model=%s due to API support.", model)
            try:
                resp = self.client.responses.create(**create_kwargs)
            except Exception:
                # Retry without temperature/reasoning if rejected
                LOGGER.warning("Initial call rejected for model=%s, retrying without temperature/reasoning...", model)
                create_kwargs.pop("temperature", None)
                create_kwargs.pop("reasoning", None)
                resp = self.client.responses.create(**create_kwargs)

            execution_time = time.time() - start_time

            # Extract response text and usage
            response_text = getattr(resp, "output_text", "") or ""
            usage = getattr(resp, "usage", None)
            token_count = 0
            if usage is not None:
                token_count = int(getattr(usage, "input_tokens", 0)) + int(
                    getattr(usage, "output_tokens", 0)
                )
            LOGGER.debug(
                "Model=%s effort=%s completed | exec_time=%.2fs | tokens=%s",
                model,
                effort_level.value,
                execution_time,
                token_count,
            )

            # Calculate metrics
            metrics = self._calculate_metrics(
                response_text, dataset, category, execution_time
            )
            metrics.token_count = token_count

            return metrics

        except Exception as e:
            LOGGER.exception(
                "Error in reasoning-effort eval | model=%s | effort=%s | test=%s: %s",
                model,
                effort_level.value,
                test_name,
                e,
            )
            return EvaluationMetrics(
                execution_time=time.time() - start_time,
                token_count=0,
                functional_correctness=0.0,
                code_quality=0.0,
                reasoning_quality=0.0,
                creativity_score=0.0,
                structure_quality=0.0,
                completeness=0.0,
                accuracy=0.0,
                error_rate=1.0,
            )

    def _calculate_metrics(
        self,
        response: str,
        dataset: dict,
        category: TestCategory,
        execution_time: float,
    ) -> EvaluationMetrics:
        """Calculate comprehensive evaluation metrics."""

        # Basic metrics
        token_count = int(len(response.split()) * 1.3)  # Approximate token count
        error_rate = 0.0 if response else 1.0

        # Category-specific metrics
        if category == TestCategory.CODE_GENERATION:
            functional_correctness = self._evaluate_code_correctness(response, dataset)
            code_quality = self._evaluate_code_quality(response)
            reasoning_quality = self._evaluate_reasoning_quality(response)
            creativity_score = self._evaluate_creativity(response)
            structure_quality = self._evaluate_structure_quality(response)
            completeness = self._evaluate_completeness(response, dataset)
            accuracy = 0.0  # Not applicable for code generation

        elif category == TestCategory.REASONING:
            functional_correctness = 0.0  # Not applicable for reasoning
            code_quality = 0.0  # Not applicable for reasoning
            reasoning_quality = self._evaluate_reasoning_quality(response)
            creativity_score = 0.0  # Not applicable for reasoning
            structure_quality = self._evaluate_structure_quality(response)
            completeness = self._evaluate_completeness(response, dataset)
            accuracy = self._evaluate_accuracy(response, dataset)

        elif category == TestCategory.CREATIVE_TASKS:
            functional_correctness = self._evaluate_functional_correctness(
                response, dataset
            )
            code_quality = self._evaluate_code_quality(response)
            reasoning_quality = self._evaluate_reasoning_quality(response)
            creativity_score = self._evaluate_creativity(response)
            structure_quality = self._evaluate_structure_quality(response)
            completeness = self._evaluate_completeness(response, dataset)
            accuracy = 0.0  # Not applicable for creative tasks

        elif category == TestCategory.STRUCTURED_OUTPUT:
            functional_correctness = self._evaluate_json_validity(response)
            code_quality = 0.0  # Not applicable for structured output
            reasoning_quality = self._evaluate_reasoning_quality(response)
            creativity_score = 0.0  # Not applicable for structured output
            structure_quality = self._evaluate_structure_quality(response)
            completeness = self._evaluate_completeness(response, dataset)
            accuracy = self._evaluate_accuracy(response, dataset)

        elif category in (
            TestCategory.CODING_REASONING,
            TestCategory.ALGORITHM_DESIGN,
            TestCategory.CODE_OPTIMIZATION,
        ):
            # Treat coding-focused categories like code generation
            functional_correctness = self._evaluate_code_correctness(response, dataset)
            code_quality = self._evaluate_code_quality(response)
            reasoning_quality = self._evaluate_reasoning_quality(response)
            creativity_score = self._evaluate_creativity(response)
            structure_quality = self._evaluate_structure_quality(response)
            completeness = self._evaluate_completeness(response, dataset)
            accuracy = 0.0

        else:
            # Fallback: assign conservative defaults to avoid unbound locals
            functional_correctness = 0.0
            code_quality = 0.0
            reasoning_quality = self._evaluate_reasoning_quality(response)
            creativity_score = 0.0
            structure_quality = self._evaluate_structure_quality(response)
            completeness = self._evaluate_completeness(response, dataset)
            accuracy = 0.0

        return EvaluationMetrics(
            execution_time=execution_time,
            token_count=token_count,
            functional_correctness=functional_correctness,
            code_quality=code_quality,
            reasoning_quality=reasoning_quality,
            creativity_score=creativity_score,
            structure_quality=structure_quality,
            completeness=completeness,
            accuracy=accuracy,
            error_rate=error_rate,
        )

    def _evaluate_code_correctness(self, response: str, dataset: dict) -> float:
        """Evaluate functional correctness of generated code."""
        if not response:
            return 0.0

        score = 0.0

        # Check for code blocks
        if "```" in response:
            score += 0.3

        # Check for function definition
        if "def " in response or "function " in response or "class " in response:
            score += 0.2

        # Check for expected features
        expected_features = dataset.get("expected_features", [])
        for feature in expected_features:
            if feature.lower() in response.lower():
                score += 0.1

        # Check for proper structure
        if "import" in response or "from" in response:
            score += 0.1

        if "return" in response or "print" in response:
            score += 0.1

        return min(score, 1.0)

    def _evaluate_code_quality(self, response: str) -> float:
        """Evaluate code quality metrics."""
        if not response:
            return 0.0

        score = 0.0

        # Check for comments
        if "#" in response or "//" in response or "/*" in response:
            score += 0.2

        # Check for type hints
        if ":" in response and "->" in response:
            score += 0.2

        # Check for error handling
        if "try" in response or "except" in response or "catch" in response:
            score += 0.2

        # Check for documentation
        if '"""' in response or "'''" in response or "/**" in response:
            score += 0.2

        # Check for proper formatting
        if response.count("\n") > 5:
            score += 0.2

        return min(score, 1.0)

    def _evaluate_reasoning_quality(self, response: str) -> float:
        """Evaluate reasoning quality."""
        if not response:
            return 0.0

        score = 0.0

        # Check for step-by-step reasoning
        reasoning_indicators = [
            "step",
            "first",
            "second",
            "then",
            "therefore",
            "because",
            "since",
        ]
        for indicator in reasoning_indicators:
            if indicator.lower() in response.lower():
                score += 0.1

        # Check for logical structure
        if any(marker in response for marker in ["1.", "2.", "3.", "•", "-"]):
            score += 0.2

        # Check for explanation
        if len(response) > 100:
            score += 0.2

        # Check for conclusion
        if any(
            word in response.lower()
            for word in ["therefore", "thus", "conclusion", "answer"]
        ):
            score += 0.2

        return min(score, 1.0)

    def _evaluate_creativity(self, response: str) -> float:
        """Evaluate creativity and originality."""
        if not response:
            return 0.0

        score = 0.0

        # Check for unique elements
        if len(response) > 200:
            score += 0.3

        # Check for creative language
        creative_words = ["innovative", "creative", "unique", "original", "novel"]
        for word in creative_words:
            if word.lower() in response.lower():
                score += 0.1

        # Check for visual elements
        if any(marker in response for marker in ["color", "design", "style", "theme"]):
            score += 0.2

        # Check for interactive elements
        if any(
            marker in response
            for marker in ["click", "hover", "animation", "transition"]
        ):
            score += 0.2

        return min(score, 1.0)

    def _evaluate_structure_quality(self, response: str) -> float:
        """Evaluate structure and organization."""
        if not response:
            return 0.0

        score = 0.0

        # Check for headers
        if "#" in response:
            score += 0.2

        # Check for lists
        if any(marker in response for marker in ["- ", "* ", "1.", "2."]):
            score += 0.2

        # Check for code blocks
        if "```" in response:
            score += 0.2

        # Check for paragraphs
        if response.count("\n\n") > 2:
            score += 0.2

        # Check for logical flow
        if any(
            marker in response
            for marker in ["first", "next", "finally", "in conclusion"]
        ):
            score += 0.2

        return min(score, 1.0)

    def _evaluate_completeness(self, response: str, dataset: dict) -> float:
        """Evaluate completeness of response."""
        if not response:
            return 0.0

        score = 0.0

        # Length-based completeness
        if len(response) > 500:
            score += 0.3
        elif len(response) > 200:
            score += 0.2
        elif len(response) > 100:
            score += 0.1

        # Check for expected elements
        expected_features = dataset.get("expected_features", [])
        for feature in expected_features:
            if feature.lower() in response.lower():
                score += 0.1

        # Check for conclusion or summary
        if any(
            word in response.lower()
            for word in ["conclusion", "summary", "therefore", "thus"]
        ):
            score += 0.2

        return min(score, 1.0)

    def _evaluate_accuracy(self, response: str, dataset: dict) -> float:
        """Evaluate accuracy for reasoning tasks."""
        if not response:
            return 0.0

        expected_answer = dataset.get("expected_answer", "").lower()
        if not expected_answer:
            return 0.5  # Neutral score if no expected answer

        # Extract answer from response
        answer_match = re.search(r"answer:\s*([^\n]+)", response.lower())
        if answer_match:
            actual_answer = answer_match.group(1).strip()
            if actual_answer == expected_answer:
                return 1.0
            elif expected_answer in actual_answer or actual_answer in expected_answer:
                return 0.8

        return 0.0

    def _evaluate_json_validity(self, response: str) -> float:
        """Evaluate JSON validity for structured output."""
        if not response:
            return 0.0

        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json.loads(json_str)
                return 1.0
        except Exception:
            pass

        return 0.0

    def _evaluate_functional_correctness(self, response: str, dataset: dict) -> float:
        """Evaluate functional correctness for creative tasks."""
        if not response:
            return 0.0

        score = 0.0

        # Check for HTML structure
        if "<html" in response or "<!DOCTYPE" in response:
            score += 0.3

        # Check for CSS styling
        if "<style" in response or "css" in response.lower():
            score += 0.2

        # Check for JavaScript functionality
        if "<script" in response or "javascript" in response.lower():
            score += 0.2

        # Check for interactive elements
        if any(
            marker in response for marker in ["onclick", "addEventListener", "function"]
        ):
            score += 0.2

        # Check for responsive design
        if any(
            marker in response for marker in ["@media", "responsive", "flexbox", "grid"]
        ):
            score += 0.1

        return min(score, 1.0)


# =============================================================================
# COMPREHENSIVE TEST EXECUTION
# =============================================================================


class ComprehensiveTestRunner:
    """Runs comprehensive tests across all categories and models."""

    def __init__(self) -> None:
        self.evaluator = ModelEvaluator()
        self.results: dict[str, Any] = {}
        self.comparison_data: dict[str, Any] = {}

    async def run_comprehensive_tests(self) -> dict[str, Any]:
        """Run all tests across all model pairs and categories."""
        print("🚀 Starting Comprehensive GPT-5 vs GPT-4.1 Series Comparison")
        print(
            f"Testing {len(MODEL_PAIRS)} model pairs across {len(TestCategory)} categories"
        )

        start_time = time.time()

        # Run tests for each model pair
        for gpt41_model, gpt5_model in MODEL_PAIRS:
            print(f"\n🔍 Testing {gpt41_model} vs {gpt5_model}")

            pair_results = await self._test_model_pair(gpt41_model, gpt5_model)
            self.results[f"{gpt41_model}_vs_{gpt5_model}"] = pair_results

        # Run reasoning effort tests for GPT-5
        print(f"\n🧠 Testing GPT-5 Reasoning Effort Levels")
        reasoning_results = await self._test_gpt5_reasoning_efforts()
        self.results["gpt5_reasoning_effort_analysis"] = reasoning_results

        total_time = time.time() - start_time

        # Generate comprehensive report
        report = self._generate_comprehensive_report(total_time)

        # Save results
        self._save_results(report)

        return report

    async def _test_gpt5_reasoning_efforts(self) -> dict[str, Any]:
        """Test GPT-5 with different reasoning effort levels on coding tasks."""
        print("  📝 Testing GPT-5 reasoning effort levels on coding tasks")

        reasoning_results: dict[str, Any] = {
            "reasoning_efforts": {},
            "coding_performance_analysis": {},
        }

        # Focus on coding-related categories for reasoning effort testing
        coding_categories = [
            TestCategory.CODE_GENERATION,
            TestCategory.CODING_REASONING,
            TestCategory.ALGORITHM_DESIGN,
            TestCategory.CODE_OPTIMIZATION,
        ]

        for effort_level in ReasoningEffort:
            print(f"    🧪 Testing {effort_level.value} reasoning effort")

            effort_results: dict[str, Any] = {
                "effort_level": effort_level.value,
                "categories": {},
                "summary": {},
            }

            for category in coding_categories:
                print(f"      📋 Testing {category.value}")

                category_results = await self._test_category_with_reasoning_effort(
                    "gpt-5", category, effort_level
                )
                effort_results["categories"][category.value] = category_results

            # Calculate effort level summary
            effort_results["summary"] = self._calculate_reasoning_effort_summary(
                effort_results["categories"]
            )

            reasoning_results["reasoning_efforts"][effort_level.value] = effort_results

        # Analyze coding performance across reasoning efforts
        reasoning_results[
            "coding_performance_analysis"
        ] = self._analyze_coding_performance_across_efforts(
            reasoning_results["reasoning_efforts"]
        )

        return reasoning_results

    async def _test_category_with_reasoning_effort(
        self, model: str, category: TestCategory, effort_level: ReasoningEffort
    ) -> dict[str, Any]:
        """Test a specific category with a specific reasoning effort level."""
        category_results: dict[str, Any] = {"tests": {}, "summary": {}}

        # Get tests for this category
        gpt5_tests = GPT5_OPTIMIZED_PROMPTS.get(category) or {}
        datasets = TEST_DATASETS.get(category) or {}

        for test_name in gpt5_tests.keys():
            if test_name in datasets:
                print(
                    f"        🧪 Running {test_name} with {effort_level.value} reasoning"
                )

                # Test GPT-5 model with specific reasoning effort
                gpt5_metrics = (
                    await self.evaluator.evaluate_model_with_reasoning_effort(
                        model,
                        category,
                        test_name,
                        gpt5_tests[test_name],
                        datasets[test_name][0],
                        effort_level,
                    )
                )

                category_results["tests"][test_name] = {
                    "metrics": self._metrics_to_dict(gpt5_metrics),
                    "reasoning_effort": effort_level.value,
                }

        # Calculate category summary
        category_results["summary"] = self._calculate_category_summary(
            category_results["tests"]
        )

        return category_results

    def _calculate_reasoning_effort_summary(
        self, categories: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate summary statistics for a reasoning effort level."""
        all_metrics: list[dict[str, float]] = []

        for category_name, category_data in categories.items():
            for test_name, test_data in category_data["tests"].items():
                metrics = test_data["metrics"]
                all_metrics.append(
                    {
                        "functional_correctness": metrics["functional_correctness"],
                        "code_quality": metrics["code_quality"],
                        "reasoning_quality": metrics["reasoning_quality"],
                        "completeness": metrics["completeness"],
                        "execution_time": metrics["execution_time"],
                    }
                )

        if not all_metrics:
            return {
                "average_functional_correctness": 0.0,
                "average_code_quality": 0.0,
                "average_reasoning_quality": 0.0,
                "average_completeness": 0.0,
                "average_execution_time": 0.0,
                "total_tests": 0,
            }

        return {
            "average_functional_correctness": statistics.mean(
                [m["functional_correctness"] for m in all_metrics]
            ),
            "average_code_quality": statistics.mean(
                [m["code_quality"] for m in all_metrics]
            ),
            "average_reasoning_quality": statistics.mean(
                [m["reasoning_quality"] for m in all_metrics]
            ),
            "average_completeness": statistics.mean(
                [m["completeness"] for m in all_metrics]
            ),
            "average_execution_time": statistics.mean(
                [m["execution_time"] for m in all_metrics]
            ),
            "total_tests": len(all_metrics),
        }

    def _analyze_coding_performance_across_efforts(
        self, reasoning_efforts: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze how coding performance varies across reasoning effort levels."""
        analysis: dict[str, Any] = {
            "performance_comparison": {},
            "recommendations": {},
            "insights": [],
        }

        # Compare performance across effort levels
        for effort_level, effort_data in reasoning_efforts.items():
            summary = effort_data["summary"]
            analysis["performance_comparison"][effort_level] = {
                "functional_correctness": summary["average_functional_correctness"],
                "code_quality": summary["average_code_quality"],
                "reasoning_quality": summary["average_reasoning_quality"],
                "completeness": summary["average_completeness"],
                "execution_time": summary["average_execution_time"],
                "efficiency_score": summary["average_functional_correctness"]
                / summary["average_execution_time"]
                if summary["average_execution_time"] > 0
                else 0,
            }

        # Generate insights
        low_perf = analysis["performance_comparison"]["low"]
        medium_perf = analysis["performance_comparison"]["medium"]
        high_perf = analysis["performance_comparison"]["high"]

        # Analyze trade-offs
        if (
            high_perf["functional_correctness"]
            > medium_perf["functional_correctness"]
            > low_perf["functional_correctness"]
        ):
            analysis["insights"].append(
                "Higher reasoning effort consistently improves functional correctness"
            )

        if (
            high_perf["execution_time"]
            > medium_perf["execution_time"]
            > low_perf["execution_time"]
        ):
            analysis["insights"].append(
                "Higher reasoning effort increases execution time"
            )

        # Calculate efficiency improvements
        if high_perf["efficiency_score"] > medium_perf["efficiency_score"]:
            analysis["insights"].append(
                "High reasoning effort provides better efficiency despite longer execution time"
            )
        elif medium_perf["efficiency_score"] > high_perf["efficiency_score"]:
            analysis["insights"].append(
                "Medium reasoning effort provides optimal efficiency"
            )

        # Generate recommendations
        best_correctness = max(
            [
                low_perf["functional_correctness"],
                medium_perf["functional_correctness"],
                high_perf["functional_correctness"],
            ]
        )
        best_efficiency = max(
            [
                low_perf["efficiency_score"],
                medium_perf["efficiency_score"],
                high_perf["efficiency_score"],
            ]
        )

        if best_correctness == high_perf["functional_correctness"]:
            analysis["recommendations"][
                "for_maximum_quality"
            ] = "Use high reasoning effort for critical coding tasks"

        if best_efficiency == medium_perf["efficiency_score"]:
            analysis["recommendations"][
                "for_optimal_efficiency"
            ] = "Use medium reasoning effort for balanced performance"
        elif best_efficiency == low_perf["efficiency_score"]:
            analysis["recommendations"][
                "for_optimal_efficiency"
            ] = "Use low reasoning effort for rapid prototyping"

        return analysis

    async def _test_model_pair(
        self, gpt41_model: str, gpt5_model: str
    ) -> dict[str, Any]:
        """Test a pair of models across all categories."""
        pair_results = {
            "gpt41_model": gpt41_model,
            "gpt5_model": gpt5_model,
            "categories": {},
        }

        for category in TestCategory:
            print(f"  📝 Testing {category.value}")
            category_results = await self._test_category(
                gpt41_model, gpt5_model, category
            )
            pair_results["categories"][category.value] = category_results

        return pair_results

    async def _test_category(
        self, gpt41_model: str, gpt5_model: str, category: TestCategory
    ) -> dict[str, Any]:
        """Test a specific category for both models."""
        category_results: dict[str, Any] = {"tests": {}, "summary": {}}

        # Get tests for this category
        gpt41_tests = GPT41_OPTIMIZED_PROMPTS.get(category) or {}
        gpt5_tests = GPT5_OPTIMIZED_PROMPTS.get(category) or {}
        datasets = TEST_DATASETS.get(category) or {}

        for test_name in gpt41_tests.keys():
            if test_name in datasets and test_name in gpt5_tests:
                print(f"    🧪 Running {test_name}")

                # Test GPT-4.1 model with GPT-4.1 optimized prompt
                gpt41_metrics = await self.evaluator.evaluate_model(
                    gpt41_model,
                    category,
                    test_name,
                    gpt41_tests[test_name],
                    datasets[test_name][0],
                )

                # Test GPT-5 model with GPT-5 optimized prompt
                gpt5_metrics = await self.evaluator.evaluate_model(
                    gpt5_model,
                    category,
                    test_name,
                    gpt5_tests[test_name],
                    datasets[test_name][0],
                )

                # Compare results
                comparison = self._compare_metrics(gpt41_metrics, gpt5_metrics)

                category_results["tests"][test_name] = {
                    "gpt41_metrics": self._metrics_to_dict(gpt41_metrics),
                    "gpt5_metrics": self._metrics_to_dict(gpt5_metrics),
                    "comparison": comparison,
                }

        # Calculate category summary
        category_results["summary"] = self._calculate_category_summary(
            category_results["tests"]
        )

        return category_results

    def _compare_metrics(
        self, gpt41_metrics: EvaluationMetrics, gpt5_metrics: EvaluationMetrics
    ) -> dict[str, Any]:
        """Compare metrics between two models."""
        return {
            "execution_time_improvement": (
                gpt41_metrics.execution_time - gpt5_metrics.execution_time
            )
            / gpt41_metrics.execution_time
            if gpt41_metrics.execution_time > 0
            else 0,
            "functional_correctness_improvement": gpt5_metrics.functional_correctness
            - gpt41_metrics.functional_correctness,
            "code_quality_improvement": gpt5_metrics.code_quality
            - gpt41_metrics.code_quality,
            "reasoning_quality_improvement": gpt5_metrics.reasoning_quality
            - gpt41_metrics.reasoning_quality,
            "creativity_improvement": gpt5_metrics.creativity_score
            - gpt41_metrics.creativity_score,
            "structure_quality_improvement": gpt5_metrics.structure_quality
            - gpt41_metrics.structure_quality,
            "completeness_improvement": gpt5_metrics.completeness
            - gpt41_metrics.completeness,
            "accuracy_improvement": gpt5_metrics.accuracy - gpt41_metrics.accuracy,
            "error_rate_improvement": gpt41_metrics.error_rate
            - gpt5_metrics.error_rate,  # Lower is better
            "overall_improvement": self._calculate_overall_improvement(
                gpt41_metrics, gpt5_metrics
            ),
        }

    def _calculate_overall_improvement(
        self, gpt41_metrics: EvaluationMetrics, gpt5_metrics: EvaluationMetrics
    ) -> float:
        """Calculate overall improvement score."""
        improvements = [
            gpt5_metrics.functional_correctness - gpt41_metrics.functional_correctness,
            gpt5_metrics.code_quality - gpt41_metrics.code_quality,
            gpt5_metrics.reasoning_quality - gpt41_metrics.reasoning_quality,
            gpt5_metrics.creativity_score - gpt41_metrics.creativity_score,
            gpt5_metrics.structure_quality - gpt41_metrics.structure_quality,
            gpt5_metrics.completeness - gpt41_metrics.completeness,
            gpt5_metrics.accuracy - gpt41_metrics.accuracy,
            gpt41_metrics.error_rate - gpt5_metrics.error_rate,  # Lower is better
        ]

        return statistics.mean(improvements)

    def _metrics_to_dict(self, metrics: EvaluationMetrics) -> dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            "execution_time": metrics.execution_time,
            "token_count": metrics.token_count,
            "functional_correctness": metrics.functional_correctness,
            "code_quality": metrics.code_quality,
            "reasoning_quality": metrics.reasoning_quality,
            "creativity_score": metrics.creativity_score,
            "structure_quality": metrics.structure_quality,
            "completeness": metrics.completeness,
            "accuracy": metrics.accuracy,
            "error_rate": metrics.error_rate,
        }

    def _calculate_category_summary(self, tests: dict[str, Any]) -> dict[str, Any]:
        """Calculate summary statistics for a category."""
        # Detect test result shape: pair-comparison (has 'comparison') vs single-model (has 'metrics')
        has_comparison = any(
            isinstance(v, dict) and "comparison" in v for v in tests.values()
        )

        if has_comparison:
            improvements: list[float] = []
            for _, test_data in tests.items():
                if "comparison" in test_data:
                    improvements.append(
                        test_data["comparison"].get("overall_improvement", 0)
                    )

            return {
                "average_improvement": statistics.mean(improvements)
                if improvements
                else 0,
                "median_improvement": statistics.median(improvements)
                if improvements
                else 0,
                "std_improvement": statistics.stdev(improvements)
                if len(improvements) > 1
                else 0,
                "best_improvement": max(improvements) if improvements else 0,
                "worst_improvement": min(improvements) if improvements else 0,
            }

        # Single-model metrics summary (used by reasoning-effort runs)
        metrics_list: list[dict[str, float]] = []
        for _, test_data in tests.items():
            if "metrics" in test_data:
                metrics_list.append(test_data["metrics"])

        if not metrics_list:
            return {
                "average_functional_correctness": 0.0,
                "average_code_quality": 0.0,
                "average_reasoning_quality": 0.0,
                "average_completeness": 0.0,
                "average_execution_time": 0.0,
                "total_tests": 0,
                # Ensure report code has consistent keys even for empty categories
                "average_improvement": 0.0,
                "median_improvement": 0.0,
                "std_improvement": 0.0,
            }

        return {
            "average_functional_correctness": statistics.mean(
                m.get("functional_correctness", 0.0) for m in metrics_list
            ),
            "average_code_quality": statistics.mean(
                m.get("code_quality", 0.0) for m in metrics_list
            ),
            "average_reasoning_quality": statistics.mean(
                m.get("reasoning_quality", 0.0) for m in metrics_list
            ),
            "average_completeness": statistics.mean(
                m.get("completeness", 0.0) for m in metrics_list
            ),
            "average_execution_time": statistics.mean(
                m.get("execution_time", 0.0) for m in metrics_list
            ),
            "total_tests": len(metrics_list),
            # For compatibility with overall report aggregation
            "average_improvement": 0.0,
            "median_improvement": 0.0,
            "std_improvement": 0.0,
        }

    def _generate_comprehensive_report(self, total_time: float) -> dict[str, Any]:
        """Generate comprehensive comparison report."""
        print("\n📊 Generating comprehensive report...")
        LOGGER.debug("Generating comprehensive report with total_time=%.2fs", total_time)

        # Calculate overall statistics
        all_improvements = []
        category_summaries = {}

        for pair_name, pair_data in self.results.items():
            # Skip non pair results (e.g., reasoning effort analysis)
            if not isinstance(pair_data, dict) or "categories" not in pair_data:
                continue
            for category_name, category_data in pair_data["categories"].items():
                summary = category_data["summary"]
                all_improvements.append(summary["average_improvement"])

                if category_name not in category_summaries:
                    category_summaries[category_name] = []
                category_summaries[category_name].append(summary["average_improvement"])

        # Calculate category averages
        category_averages: dict[str, Any] = {}
        for category_name, improvements in category_summaries.items():
            category_averages[category_name] = {
                "average_improvement": statistics.mean(improvements),
                "median_improvement": statistics.median(improvements),
                "std_improvement": statistics.stdev(improvements)
                if len(improvements) > 1
                else 0,
            }

        report: dict[str, Any] = {
            "test_metadata": {
                "total_execution_time": total_time,
                "model_pairs_tested": len(MODEL_PAIRS),
                "categories_tested": len(TestCategory),
                "total_tests": len(MODEL_PAIRS) * len(TestCategory),
                "test_date": datetime.now().isoformat(),
            },
            "overall_summary": {
                "average_improvement": statistics.mean(all_improvements)
                if all_improvements
                else 0,
                "median_improvement": statistics.median(all_improvements)
                if all_improvements
                else 0,
                "std_improvement": statistics.stdev(all_improvements)
                if len(all_improvements) > 1
                else 0,
                "best_improvement": max(all_improvements) if all_improvements else 0,
                "worst_improvement": min(all_improvements) if all_improvements else 0,
            },
            "category_summaries": category_averages,
            "detailed_results": self.results,
        }

        return report

    def _save_results(self, report: dict[str, Any]) -> None:
        """Save comprehensive results to files."""
        print("\n💾 Saving comprehensive results...")

        # Create results directory next to this file to keep outputs scoped
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)

        # Save detailed JSON results
        json_path = os.path.join(results_dir, "comprehensive_gpt5_vs_gpt41_results.json")
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        LOGGER.debug("Updated file: %s", json_path)

        # Save markdown report
        md_report_path = os.path.join(results_dir, "comprehensive_gpt5_vs_gpt41_report.md")
        with open(md_report_path, "w") as f:
            self._generate_markdown_report(report, f)
        LOGGER.debug("Updated file: %s", md_report_path)

        # Save executive summary
        summary_path = os.path.join(
            results_dir, "comprehensive_gpt5_vs_gpt41_executive_summary.md"
        )
        with open(summary_path, "w") as f:
            self._generate_executive_summary(report, f)
        LOGGER.debug("Updated file: %s", summary_path)

        print("✅ Results saved to:")
        print(
            f"1. {results_dir}/comprehensive_gpt5_vs_gpt41_results.json - Detailed JSON results"
        )
        print(
            f"2. {results_dir}/comprehensive_gpt5_vs_gpt41_report.md - Comprehensive markdown report"
        )
        print(
            f"3. {results_dir}/comprehensive_gpt5_vs_gpt41_executive_summary.md - Executive summary"
        )

    def _generate_markdown_report(self, report: dict[str, Any], f) -> None:
        """Generate comprehensive markdown report."""
        f.write(f"# Comprehensive GPT-5 vs GPT-4.1 Series Comparison Report\n\n")
        f.write(f"**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Executive Summary
        f.write(f"## Executive Summary\n\n")
        overall = report["overall_summary"]
        f.write(
            f"- **Overall Average Improvement**: {overall['average_improvement']:.3f} ({overall['average_improvement']*100:.1f}%)\n"
        )
        f.write(
            f"- **Best Improvement**: {overall['best_improvement']:.3f} ({overall['best_improvement']*100:.1f}%)\n"
        )
        f.write(
            f"- **Worst Improvement**: {overall['worst_improvement']:.3f} ({overall['worst_improvement']*100:.1f}%)\n"
        )
        f.write(f"- **Consistency (Std Dev)**: {overall['std_improvement']:.3f}\n\n")

        # GPT-5 Reasoning Effort Analysis
        if "gpt5_reasoning_effort_analysis" in report["detailed_results"]:
            f.write(f"## GPT-5 Reasoning Effort Analysis\n\n")
            reasoning_analysis = report["detailed_results"][
                "gpt5_reasoning_effort_analysis"
            ]

            # Performance comparison across effort levels
            f.write(f"### Performance Across Reasoning Effort Levels\n\n")
            performance_comparison = reasoning_analysis["coding_performance_analysis"][
                "performance_comparison"
            ]

            for effort_level, perf in performance_comparison.items():
                f.write(f"#### {effort_level.title()} Reasoning Effort\n")
                f.write(
                    f"- **Functional Correctness**: {perf['functional_correctness']:.3f} ({perf['functional_correctness']*100:.1f}%)\n"
                )
                f.write(
                    f"- **Code Quality**: {perf['code_quality']:.3f} ({perf['code_quality']*100:.1f}%)\n"
                )
                f.write(
                    f"- **Reasoning Quality**: {perf['reasoning_quality']:.3f} ({perf['reasoning_quality']*100:.1f}%)\n"
                )
                f.write(
                    f"- **Completeness**: {perf['completeness']:.3f} ({perf['completeness']*100:.1f}%)\n"
                )
                f.write(f"- **Execution Time**: {perf['execution_time']:.2f}s\n")
                f.write(f"- **Efficiency Score**: {perf['efficiency_score']:.3f}\n\n")

            # Insights and recommendations
            insights = reasoning_analysis["coding_performance_analysis"]["insights"]
            recommendations = reasoning_analysis["coding_performance_analysis"][
                "recommendations"
            ]

            if insights:
                f.write(f"### Key Insights\n\n")
                for insight in insights:
                    f.write(f"- {insight}\n")
                f.write(f"\n")

            if recommendations:
                f.write(f"### Recommendations\n\n")
                for rec_type, rec_text in recommendations.items():
                    f.write(f"- **{rec_type.replace('_', ' ').title()}**: {rec_text}\n")
                f.write(f"\n")

        # Category Performance
        f.write(f"## Category Performance\n\n")
        for category_name, category_data in report["category_summaries"].items():
            f.write(f"### {category_name.replace('_', ' ').title()}\n")
            f.write(
                f"- **Average Improvement**: {category_data['average_improvement']:.3f} ({category_data['average_improvement']*100:.1f}%)\n"
            )
            f.write(
                f"- **Median Improvement**: {category_data['median_improvement']:.3f} ({category_data['median_improvement']*100:.1f}%)\n"
            )
            f.write(f"- **Consistency**: {category_data['std_improvement']:.3f}\n\n")

        # Detailed Results
        f.write(f"## Detailed Results\n\n")
        for pair_name, pair_data in report["detailed_results"].items():
            if pair_name == "gpt5_reasoning_effort_analysis":
                continue  # Already covered above

            f.write(f"### {pair_name.replace('_', ' ').title()}\n\n")

            for category_name, category_data in pair_data["categories"].items():
                f.write(f"#### {category_name.replace('_', ' ').title()}\n")
                summary = category_data["summary"]
                f.write(
                    f"- **Average Improvement**: {summary['average_improvement']:.3f} ({summary['average_improvement']*100:.1f}%)\n"
                )
                f.write(
                    f"- **Best Test**: {summary['best_improvement']:.3f} ({summary['best_improvement']*100:.1f}%)\n"
                )
                f.write(
                    f"- **Worst Test**: {summary['worst_improvement']:.3f} ({summary['worst_improvement']*100:.1f}%)\n\n"
                )

    def _generate_executive_summary(self, report: dict[str, Any], f) -> None:
        """Generate executive summary."""
        f.write(f"# GPT-5 vs GPT-4.1 Series: Executive Summary\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Key Findings
        overall = report["overall_summary"]
        f.write(f"## Key Findings\n\n")
        f.write(
            f"- **GPT-5 shows an average improvement of {overall['average_improvement']*100:.1f}%** across all test categories\n"
        )
        f.write(
            f"- **Best performance**: {overall['best_improvement']*100:.1f}% improvement in specific tasks\n"
        )
        f.write(
            f"- **Consistency**: Standard deviation of {overall['std_improvement']:.3f} indicates {'high' if overall['std_improvement'] < 0.1 else 'moderate' if overall['std_improvement'] < 0.2 else 'variable'} consistency\n\n"
        )

        # GPT-5 Reasoning Effort Insights
        if "gpt5_reasoning_effort_analysis" in report["detailed_results"]:
            f.write(f"## GPT-5 Reasoning Effort Insights\n\n")
            reasoning_analysis = report["detailed_results"][
                "gpt5_reasoning_effort_analysis"
            ]
            performance_comparison = reasoning_analysis["coding_performance_analysis"][
                "performance_comparison"
            ]

            # Find best performing effort level
            best_correctness = max(
                performance_comparison.items(),
                key=lambda x: x[1]["functional_correctness"],
            )
            best_efficiency = max(
                performance_comparison.items(), key=lambda x: x[1]["efficiency_score"]
            )

            f.write(
                f"- **Best Code Quality**: {best_correctness[0].title()} reasoning effort ({best_correctness[1]['functional_correctness']*100:.1f}% correctness)\n"
            )
            f.write(
                f"- **Most Efficient**: {best_efficiency[0].title()} reasoning effort (efficiency score: {best_efficiency[1]['efficiency_score']:.3f})\n"
            )

            insights = reasoning_analysis["coding_performance_analysis"]["insights"]
            if insights:
                f.write(f"- **Key Insight**: {insights[0]}\n")
            f.write(f"\n")

        # Category Insights
        f.write(f"## Category Insights\n\n")
        for category_name, category_data in report["category_summaries"].items():
            improvement = category_data["average_improvement"]
            f.write(
                f"- **{category_name.replace('_', ' ').title()}**: {improvement*100:.1f}% improvement\n"
            )

        f.write(f"\n## Recommendations\n\n")
        f.write(f"Based on the comprehensive testing results:\n\n")

        if overall["average_improvement"] > 0.1:
            f.write(f"- **Strong upgrade recommendation** for GPT-5 series\n")
        elif overall["average_improvement"] > 0.05:
            f.write(f"- **Moderate upgrade recommendation** for GPT-5 series\n")
        else:
            f.write(f"- **Consider cost-benefit analysis** before upgrading\n")

        f.write(f"- **Best use cases**: Focus on categories showing >10% improvement\n")
        f.write(f"- **Monitoring**: Track performance in production for validation\n")

        # Reasoning effort recommendations
        if "gpt5_reasoning_effort_analysis" in report["detailed_results"]:
            recommendations = reasoning_analysis["coding_performance_analysis"][
                "recommendations"
            ]
            f.write(f"\n## GPT-5 Reasoning Effort Recommendations\n\n")
            for rec_type, rec_text in recommendations.items():
                f.write(f"- **{rec_type.replace('_', ' ').title()}**: {rec_text}\n")


# =============================================================================
# MAIN EXECUTION
# =============================================================================


async def main():
    """Main execution function."""
    print("🚀 Starting Comprehensive GPT-5 vs GPT-4.1 Series Comparison")

    runner = ComprehensiveTestRunner()
    report = await runner.run_comprehensive_tests()

    print(f"\n🎯 Test Summary:")
    print(
        f"- Total execution time: {report['test_metadata']['total_execution_time']:.2f}s"
    )
    print(
        f"- Average improvement: {report['overall_summary']['average_improvement']*100:.1f}%"
    )
    print(
        f"- Best improvement: {report['overall_summary']['best_improvement']*100:.1f}%"
    )
    print(f"- Consistency: {report['overall_summary']['std_improvement']:.3f}")

    # Add reasoning effort analysis summary
    if "gpt5_reasoning_effort_analysis" in report["detailed_results"]:
        print(f"\n🧠 GPT-5 Reasoning Effort Analysis:")
        reasoning_analysis = report["detailed_results"][
            "gpt5_reasoning_effort_analysis"
        ]
        performance_comparison = reasoning_analysis["coding_performance_analysis"][
            "performance_comparison"
        ]

        for effort_level, perf in performance_comparison.items():
            print(f"  {effort_level.title()} Effort:")
            print(
                f"    - Functional Correctness: {perf['functional_correctness']*100:.1f}%"
            )
            print(f"    - Code Quality: {perf['code_quality']*100:.1f}%")
            print(f"    - Execution Time: {perf['execution_time']:.2f}s")
            print(f"    - Efficiency Score: {perf['efficiency_score']:.3f}")

        # Show key insights
        insights = reasoning_analysis["coding_performance_analysis"]["insights"]
        if insights:
            print(f"\n  Key Insights:")
            for insight in insights[:3]:  # Show top 3 insights
                print(f"    - {insight}")

    return report


if __name__ == "__main__":
    asyncio.run(main())
