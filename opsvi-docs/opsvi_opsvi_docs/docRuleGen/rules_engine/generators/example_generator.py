# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Example Generator","description":"This module contains utilities for generating rule examples.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"This section imports necessary libraries and modules for the functionality of the example generator.","line_start":3,"line_end":16},{"name":"OpenAI Client Initialization","description":"This section initializes the OpenAI client using the API key from environment variables.","line_start":18,"line_end":18},{"name":"Function: generate_detailed_example","description":"This function generates a detailed example for a rule using specific domain knowledge.","line_start":20,"line_end":102},{"name":"Function: _generate_example_with_retries_and_validation","description":"This function generates an example with retries and validation, ensuring quality and correctness.","line_start":104,"line_end":186},{"name":"Function: _create_fallback_example","description":"This function creates a fallback example when the generation fails.","line_start":188,"line_end":228},{"name":"Function: setup_resources","description":"This function sets up required resources for the example generation.","line_start":230,"line_end":237},{"name":"Function: cleanup_resources","description":"This function cleans up any resources used during the example generation.","line_start":239,"line_end":246}],"key_elements":[{"name":"client","description":"OpenAI client initialized with the API key.","line":18},{"name":"generate_detailed_example","description":"Function to generate a detailed example for a rule.","line":20},{"name":"_generate_example_with_retries_and_validation","description":"Function to generate an example with retries and validation.","line":104},{"name":"_create_fallback_example","description":"Function to create a fallback example when generation fails.","line":188},{"name":"setup_resources","description":"Function to set up required resources.","line":230},{"name":"cleanup_resources","description":"Function to clean up resources.","line":239}]}
"""
# FILE_MAP_END

"""
Example Generator

This module contains utilities for generating rule examples.
"""

import json
import time
from typing import Dict, Any

from openai import OpenAI
import os

from rules_engine.utils.domain_knowledge import get_domain_knowledge
from rules_engine.validators.example_validator import validate_example_quality

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def generate_detailed_example(
    rule_id: str, rule_name: str, category: str, rule_content: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a detailed, realistic example for a rule using specific domain knowledge.

    Args:
        rule_id: ID of the rule
        rule_name: Name of the rule
        category: Category of the rule
        rule_content: The content of the rule generated so far

    Returns:
        Dictionary with title, code, and explanation for the example
    """
    print(f"  Generating detailed example for rule {rule_id}...")

    # Extract key information from rule content for context
    description = rule_content.get("frontmatter", {}).get("description", "")
    overview = rule_content.get("overview", {})
    main_sections = rule_content.get("main_sections", {})

    # Determine domain-specific knowledge to inject based on category and rule
    domain_knowledge = get_domain_knowledge(rule_id, rule_name, category)

    # Prepare a detailed prompt that includes domain context
    system_message = f"""
    You are an expert developer specializing in creating realistic, educative code examples.

    You need to generate a detailed example demonstrating best practices for:
    - Rule ID: {rule_id}
    - Rule Name: {rule_name}
    - Category: {category}
    - Description: {description}

    {domain_knowledge}

    Use tree_of_thought reasoning:
    1. Consider several approaches to demonstrating this rule
    2. Evaluate each approach for clarity, realism, and educational value
    3. Select the most effective approach
    4. Implement a detailed example in the appropriate programming language
    5. Provide a thorough explanation of how the example demonstrates the rule

    Your example must be:
    - Realistic and practical (code that would actually be used in production)
    - Detailed enough to demonstrate the rule's application
    - Well-commented to explain key concepts
    - Idiomatic to the language/domain
    - Focused on best practices
    - Include error handling and edge cases

    Your response must be VALID JSON with 3 fields:
    1. "title": A descriptive title for the example
    2. "code": The complete code example with proper formatting and comments
    3. "explanation": A detailed explanation of how the example demonstrates the rule
    """

    # Context from other sections
    context = json.dumps(
        {"overview": overview, "main_sections": main_sections}, indent=2
    )

    user_message = f"""
    Generate a detailed example for the "{rule_name}" rule in the {category} category.

    Here's the content of the rule so far:
    {context}

    Create an example that clearly demonstrates the principles of this rule, focusing on modern best practices and realistic implementation patterns.

    Return a JSON object with the following structure:
    {{
      "title": "Title for the example",
      "code": "```language\\nDetailed code example\\n```",
      "explanation": "Thorough explanation of the example"
    }}
    """

    # Call the OpenAI API with retries and validation
    return _generate_example_with_retries_and_validation(
        system_message, user_message, rule_id, rule_name, category
    )


def _generate_example_with_retries_and_validation(
    system_message: str, user_message: str, rule_id: str, rule_name: str, category: str
) -> Dict[str, Any]:
    """
    Generate an example with retries and validation.

    Args:
        system_message: The system message for the API call
        user_message: The user message for the API call
        rule_id: The ID of the rule
        rule_name: The name of the rule
        category: The category of the rule

    Returns:
        Dictionary with the generated example
    """
    # Determine appropriate language based on category
    language_preferences = {
        "LLM Integration": "python",
        "Multi-Agent": "python",
        "Python Engine": "python",
        "Knowledge Management": "python",
        "System Interface": "python",
        "Core": "python",
    }

    # Try to get a detailed example with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
            )

            # Extract and parse the JSON response
            example = json.loads(response.choices[0].message.content)

            # Verify the example has all required fields
            if (
                "title" not in example
                or "code" not in example
                or "explanation" not in example
            ):
                raise ValueError("Example missing required fields")

            # Ensure code is properly formatted with language tag if not already
            code = example["code"]
            if not code.startswith("```"):
                preferred_language = language_preferences.get(category, "python")
                example["code"] = f"```{preferred_language}\n{code}\n```"

            # Validate example quality
            example_quality = validate_example_quality(
                example, rule_id, rule_name, category
            )

            if not example_quality["is_valid"]:
                # Try again with feedback
                if attempt < max_retries - 1:
                    print(
                        f"  ! Example quality issues: {example_quality['feedback']}, regenerating..."
                    )
                    # Add feedback to user message for next attempt
                    user_message += f"\n\nPrevious attempt had the following issues: {example_quality['feedback']}\nPlease address these issues in your response."
                    continue
                else:
                    print(
                        f"  ! Example quality issues after max retries: {example_quality['feedback']}"
                    )

            print(f"  ✓ Generated detailed example for rule {rule_id}")
            return example

        except Exception as e:
            if attempt < max_retries - 1:
                print(
                    f"  ! Error generating example for rule {rule_id}, retrying ({attempt+1}/{max_retries}): {str(e)}"
                )
                time.sleep(2)
            else:
                print(
                    f"  ! Failed to generate detailed example after {max_retries} attempts: {str(e)}"
                )
                # Return a fallback example
                return _create_fallback_example(rule_id, rule_name)


def _create_fallback_example(rule_id: str, rule_name: str) -> Dict[str, Any]:
    """
    Create a fallback example when generation fails.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule

    Returns:
        Dictionary with a basic fallback example
    """
    rule_snake_case = rule_name.lower().replace(" ", "_")

    return {
        "title": f"Example Implementation of {rule_name}",
        "code": f"""```python
# Example demonstrating {rule_name} principles

# This is a fallback example as the detailed generation failed
def implement_{rule_snake_case}():
    '''
    Demonstrate the key principles of {rule_name}.

    This function shows a basic pattern for implementing
    the requirements from the rule.
    '''
    try:
        # Initialize resources
        resources = setup_resources()

        # Main implementation
        result = process_with_{rule_snake_case}_principles(resources)

        # Cleanup
        cleanup_resources(resources)

        return result
    except Exception as e:
        # Error handling
        print(f"Error in {rule_snake_case} implementation: {{e}}")
        raise

def setup_resources():
    '''Set up required resources.'''
    return {"status": "initialized"}

def process_with_{rule_snake_case}_principles(resources):
    '''Process using the principles from {rule_name}.'''
    # Implementation would go here
    return {"status": "success"}

def cleanup_resources(resources):
    '''Clean up any resources.'''
    resources["status"] = "cleaned"

if __name__ == "__main__":
    implement_{rule_snake_case}()
```""",
        "explanation": f"This example demonstrates the key principles of {rule_name}, including proper implementation of the requirements outlined in the rule. The structure follows best practices with proper error handling, resource management, and clean organization. In a real implementation, you would replace the placeholder functions with actual code that implements the specific requirements of {rule_name}.",
    }
