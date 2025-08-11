# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Reasoning Methods","description":"This module contains utilities for applying reasoning methods to rule generation.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Module Description","description":"Contains the module-level docstring describing the purpose of the module.","line_start":2,"line_end":5},{"name":"apply_reasoning_method Function","description":"Defines the function that applies reasoning methods based on section complexity.","line_start":7,"line_end":56}],"key_elements":[{"name":"apply_reasoning_method","description":"Function that applies appropriate reasoning method based on section complexity.","line":8}]}
"""
# FILE_MAP_END

"""
Reasoning Methods

This module contains utilities for applying reasoning methods to rule generation.
"""


def apply_reasoning_method(
    rule_id: str, rule_name: str, section: str, category: str
) -> str:
    """
    Apply appropriate reasoning method based on section complexity,
    following rule 030-reasoning-methods guidelines.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule
        section: The section being generated
        category: The category of the rule

    Returns:
        String with reasoning instructions to add to the prompt
    """
    # Determine section complexity
    complex_sections = ["main_sections", "examples", "danger"]
    moderate_sections = ["metadata", "overview"]
    simple_sections = ["frontmatter"]

    if section in complex_sections:
        # For complex sections, use tree_of_thought reasoning
        reasoning = """
        Use tree_of_thought reasoning to approach this task:
        1. Enumerate several possible approaches for this section
        2. For each approach, analyze its pros and cons
        3. Identify any constraints or edge cases that must be addressed
        4. Select the most appropriate approach based on your analysis
        5. Implement the selected approach thoroughly

        Ensure your output is comprehensive and considers the broader context of the rule.
        """
    elif section in moderate_sections:
        # For moderate sections, use chain_of_thought reasoning
        reasoning = """
        Use chain_of_thought reasoning to approach this task:
        1. Break down the section generation into logical steps
        2. Consider the dependencies between elements
        3. Identify any potential edge cases
        4. Construct the section step by step

        Ensure your output is coherent and addresses all required components.
        """
    else:
        # For simple sections, use basic validation
        reasoning = """
        Approach this task methodically:
        1. Identify the essential elements needed
        2. Ensure all elements follow the required format
        3. Validate the output against the required structure

        Keep the output focused and precise.
        """

    return reasoning
