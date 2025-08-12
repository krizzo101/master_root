# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Section Generator","description":"This module contains utilities for generating rule sections using the OpenAI API.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary libraries and modules for the functionality of the section generator.","line_start":3,"line_end":16},{"name":"Logging Configuration","description":"Configures logging for the module to track events and errors.","line_start":18,"line_end":22},{"name":"OpenAI Client Initialization","description":"Initializes the OpenAI client using an API key from environment variables.","line_start":24,"line_end":26},{"name":"Function: generate_rule_section","description":"Generates a specific section of a rule using the OpenAI API.","line_start":28,"line_end":78},{"name":"Function: _get_section_instructions","description":"Retrieves instructions for generating a specific section of a rule.","line_start":80,"line_end":168},{"name":"Function: _call_openai_with_retries","description":"Calls the OpenAI API with retries in case of failure.","line_start":170,"line_end":218},{"name":"Function: _generate_frontmatter","description":"Generates the frontmatter section with dynamically created glob patterns.","line_start":220,"line_end":351},{"name":"Function: _create_section_generation_prompt","description":"Creates the prompt for generating a rule section.","line_start":353,"line_end":455},{"name":"Function: _generate_section_content","description":"Generates section content using the OpenAI API.","line_start":457,"line_end":505}],"key_elements":[{"name":"generate_rule_section","description":"Function to generate a specific section of a rule using OpenAI API.","line":31},{"name":"_get_section_instructions","description":"Function to get instructions for generating a specific section.","line":80},{"name":"_call_openai_with_retries","description":"Function to call the OpenAI API with retries.","line":169},{"name":"_generate_frontmatter","description":"Function to generate the frontmatter section with glob patterns.","line":219},{"name":"_create_section_generation_prompt","description":"Function to create the prompt for generating a rule section.","line":352},{"name":"_generate_section_content","description":"Function to generate section content using the OpenAI API.","line":456},{"name":"client","description":"OpenAI client initialized with the API key.","line":26},{"name":"logger","description":"Logger instance for tracking events and errors.","line":22}]}
"""
# FILE_MAP_END

"""
Section Generator

This module contains utilities for generating rule sections.
"""

import json
import time
from typing import Dict, Any, Optional
import logging

from openai import OpenAI
import os

from rules_engine.utils.reasoning import apply_reasoning_method
from rules_engine.validators.section_validator import (
    post_process_danger_section,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize the OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def generate_rule_section(
    rule_id: str,
    rule_name: str,
    section: str,
    category: str,
    previous_sections: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a specific section of a rule using OpenAI API

    Args:
        rule_id: The ID of the rule (e.g., '1050')
        rule_name: The name of the rule (e.g., 'LLM API Integration')
        section: The section to generate ('frontmatter', 'metadata', 'overview', etc.)
        category: The category the rule belongs to
        previous_sections: Previously generated sections for context

    Returns:
        Dictionary containing the generated section content
    """
    if section == "frontmatter":
        return _generate_frontmatter(rule_id, rule_name, category)

    try:
        # Get section-specific instructions
        section_instructions = _get_section_instructions(
            rule_id, rule_name, section, category
        )[section]

        # Create the prompt
        prompt = _create_section_generation_prompt(
            rule_id,
            rule_name,
            section,
            category,
            section_instructions,
            previous_sections,
        )

        # Generate the content
        generated_content = _generate_section_content(prompt, section, rule_name)

        # Return the generated content
        return generated_content
    except Exception as e:
        print(f"Error generating {section} for rule {rule_id}: {str(e)}")
        return {}


def _get_section_instructions(
    rule_id: str, rule_name: str, section: str, category: str
) -> Dict[str, Dict[str, Any]]:
    """
    Get the instructions for generating a specific section.

    Args:
        rule_id: The ID of the rule (e.g., '1050')
        rule_name: The name of the rule (e.g., 'LLM API Integration')
        section: The section to generate ('frontmatter', 'metadata', 'overview', etc.)
        category: The category the rule belongs to

    Returns:
        Dictionary with section-specific instructions
    """
    return {
        "frontmatter": {
            "description": "Generate the description and globs for the rule frontmatter. The description MUST follow the format 'MUST [ACTION] WHEN [TRIGGER] TO [PURPOSE]' and be under 100 characters.",
            "structure": {
                "description": "MUST [ACTION] WHEN [TRIGGER] TO [PURPOSE]",
                "globs": ["list of file patterns this rule applies to"],
            },
        },
        "metadata": {
            "description": "Generate the metadata section for the rule, including taxonomy information, tags, priority, and inheritance.",
            "structure": {
                "rule_id": f"{rule_id}-{rule_name.lower().replace(' ', '-')}",
                "taxonomy": {
                    "category": category,
                    "parent": f"{category}Rule",
                    "ancestors": ["Rule", f"{category}Rule"],
                    "children": [f"List of potential child rules for {rule_name}"],
                },
                "tags": ["Relevant tags for this rule"],
                "priority": "Numeric priority (1-100)",
                "inherits": ["IDs of rules this inherits from"],
            },
        },
        "overview": {
            "description": "Generate the overview section describing the rule's purpose, application, and importance.",
            "structure": {
                "purpose": "Clear statement of the rule's purpose",
                "application": "When and how the rule should be applied",
                "importance": "Why this rule matters in the context of the system",
            },
        },
        "main_sections": {
            "description": f"Generate 2-3 main content sections for the {rule_name} rule with detailed requirements.",
            "structure": {
                "section_name1": {
                    "description": "Description of first section",
                    "requirements": [
                        "List of specific requirements",
                        "Each item should be a clear, actionable statement",
                    ],
                },
                "section_name2": {
                    "description": "Description of second section",
                    "requirements": [
                        "List of specific requirements",
                        "Each item should be a clear, actionable statement",
                    ],
                },
            },
        },
        "examples": {
            "description": f"Generate a code example that demonstrates good implementation of the {rule_name} rule.",
            "structure": {
                "title": "Title for the example",
                "code": "```language\nActual code sample\n```",
                "explanation": "Explanation of why this is a good implementation",
            },
        },
        "danger": {
            "description": "Generate the danger section listing critical violations and risks related to this rule.",
            "structure": {
                "critical_violations": [
                    "List of things that should NEVER be done (start each with NEVER)",
                    "Each violation should be specific and directly related to this rule",
                ],
                "specific_risks": [
                    "Detailed consequences of violating this rule",
                    "Each item should describe a clear, specific risk",
                ],
            },
        },
    }


def _call_openai_with_retries(
    system_message: str, user_message: str, section: str, rule_id: str
) -> Dict[str, Any]:
    """
    Call the OpenAI API with retries.

    Args:
        system_message: The system message for the API call
        user_message: The user message for the API call
        section: The section being generated
        rule_id: The ID of the rule

    Returns:
        Dictionary with the generated content
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.debug(
                f"Sending request to OpenAI API for rule {rule_id}, section {section}:"
            )
            logger.debug(f"System message: {system_message[:200]}...")
            logger.debug(f"User message: {user_message[:200]}...")

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
            content = response.choices[0].message.content
            logger.debug(
                f"Received response from OpenAI API for rule {rule_id}, section {section}:"
            )
            logger.debug(f"Response (first 200 chars): {content[:200]}...")

            generated_content = json.loads(content)
            logger.info(
                f"Successfully parsed JSON response for rule {rule_id}, section {section}"
            )
            return generated_content

        except Exception as e:
            logger.warning(
                f"Error generating {section} for rule {rule_id}, attempt {attempt+1}/{max_retries}: {str(e)}"
            )
            if attempt < max_retries - 1:
                time.sleep(2)  # Add a short delay before retrying
            else:
                logger.error(
                    f"Failed to generate {section} for rule {rule_id} after {max_retries} attempts"
                )
                raise


def _generate_frontmatter(
    rule_id: str, rule_name: str, category: str
) -> Dict[str, Any]:
    """
    Generate the frontmatter section with dynamically created glob patterns.

    Args:
        rule_id: The ID of the rule (e.g., '1050')
        rule_name: The name of the rule (e.g., 'LLM API Integration')
        category: The category the rule belongs to

    Returns:
        Dictionary with the frontmatter content including description and globs
    """
    # Define category-specific glob patterns
    category_glob_patterns = {
        "Core System": ["**/*"],
        "Code Quality": ["**/*.{js,ts,py,java,c,cpp,cs,go,rb,php,rust}"],
        "Content Generation": ["**/*.{js,ts,py,java,c,cpp,cs,go,rb,php,rust}"],
        "Architecture": [
            "**/docs/architecture/**",
            "**/ARCHITECTURE.md",
            "**/design/**",
        ],
        "Testing": ["**/test/**", "**/*test*.*", "**/*.spec.*", "**/*.test.*"],
        "Documentation": ["**/*.md", "**/*.markdown", "**/docs/**"],
        "Development Process": [".github/**", ".gitlab/**", "workflow/**"],
        "Python Development": ["**/*.py", "**/requirements.txt", "**/setup.py"],
        "LLM Integration": ["**/llm/**", "**/*llm*.*", "**/prompts/**"],
        "Multi-Agent Systems": ["**/agents/**", "**/orchestration/**"],
        "Knowledge Management": [
            "**/knowledge/**",
            "**/retrieval/**",
            "**/embeddings/**",
        ],
        "Web and API": ["**/api/**", "**/routes/**", "**/controllers/**"],
        "Frontend Development": [
            "**/*.{jsx,tsx,vue,svelte,html,css}",
            "**/components/**",
        ],
        "CI/CD and DevOps": [
            "**/.github/workflows/**",
            "**/.gitlab-ci.yml",
            "**/Jenkinsfile",
        ],
    }

    # Create a system prompt for generating the description that emphasizes AI interpretability
    system_prompt = """You are a rule description generator for AI assistants integrated into IDEs.
Your task is to generate a clear, concise, algorithmically processable description for a rule that follows the format:
MUST [ACTION] WHEN [TRIGGER] TO [PURPOSE]

The description must:
1. Be under 100 characters for efficient processing
2. Use explicit directive verbs (MUST, SHOULD, NEVER) that an AI can clearly interpret
3. Clearly state the precise condition/trigger when the rule applies
4. Explain the concrete purpose/benefit
5. Follow the MUST/WHEN/TO format precisely
6. Use unambiguous language that an AI assistant can reliably interpret

Remember that these rules will be consumed by an AI assistant in an IDE, so clarity and algorithmic processability are essential.

Example good descriptions:
- MUST validate inputs WHEN processing user data TO prevent security vulnerabilities
- MUST document functions WHEN writing code TO ensure maintainability
- MUST handle exceptions WHEN errors occur TO prevent application crashes
"""

    user_prompt = f"""Generate a description for rule {rule_id}: {rule_name} in the {category} category.
The description must follow the MUST/WHEN/TO format and be under 100 characters.
The rule will be consumed by an AI assistant in an IDE, so it must be clear and explicit."""

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        description = completion.choices[0].message.content.strip()

        # Ensure the description follows the format
        if not (
            "MUST" in description and "WHEN" in description and "TO" in description
        ):
            description = f"MUST FOLLOW {rule_name} standards WHEN implementing related functionality TO ensure quality and consistency"

        # Get the appropriate glob patterns
        globs = []
        for cat_key, patterns in category_glob_patterns.items():
            if (
                cat_key.lower() in category.lower()
                or category.lower() in cat_key.lower()
            ):
                globs = patterns
                break

        # If no matching category, use a default generic pattern
        if not globs:
            globs = ["**/*"]

        # Create rule-specific patterns based on name
        rule_words = rule_name.lower().replace("-", " ").split()
        for word in rule_words:
            if len(word) > 3:  # Only use meaningful words
                if category == "Documentation":
                    globs.append(f"**/*{word}*/**")
                    globs.append(f"**/{word}/**")
                elif "Python" in category:
                    globs.append(f"**/*{word}*/**/*.py")
                    globs.append(f"**/{word}/**/*.py")
                elif "API" in category or "Web" in category:
                    globs.append(f"**/api/**/*{word}*/**")
                    globs.append(f"**/{word}/**")
                else:
                    globs.append(f"**/*{word}*/**")
                    globs.append(f"**/{word}/**")

        return {
            "description": description,
            "globs": list(set(globs)),  # Remove duplicates
        }
    except Exception as e:
        print(f"Error generating frontmatter for rule {rule_id}: {str(e)}")
        return {
            "description": f"MUST FOLLOW {rule_name} standards WHEN implementing related functionality TO ensure quality and consistency",
            "globs": ["**/*"],
        }


def _create_section_generation_prompt(
    rule_id: str,
    rule_name: str,
    section: str,
    category: str,
    section_instructions: Dict[str, Any],
    previous_sections: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Create the prompt for generating a rule section.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule
        section: The section to generate
        category: The category the rule belongs to
        section_instructions: Instructions specific to this section
        previous_sections: Previously generated sections for context

    Returns:
        Dictionary with system and user messages
    """
    # Apply appropriate reasoning method
    reasoning_instructions = apply_reasoning_method(
        rule_id, rule_name, section, category
    )

    # Build context from previous sections if available
    context = ""
    if previous_sections:
        context = "Previously generated sections:\n"
        for section_name, section_content in previous_sections.items():
            context += f"\n{section_name}: {json.dumps(section_content, indent=2)}\n"

    # Prepare the system message with context from 010 rule and 030 reasoning methods
    system_message = f"""
    You are an expert in creating Cursor IDE rule files for AI assistants according to strict formatting requirements.
    
    ## Project-Specific Context
    You are currently generating rules for the Rule Generator Enhancement Project. This project aims to:

    1. Enhance the existing rule generation system to support hierarchical parent/child rules
    2. Integrate documentation content when generating rules
    3. Create proper directory and file organization for different rule types
    4. Support parallel generation workflows for efficiency

    The rules you are generating now (ID: {rule_id}, Name: {rule_name}) are project-specific rules in the 900-999 range, 
    which will guide the implementation of the enhanced rule generation system. These rules will ultimately be used to 
    generate documentation standard rules based on comprehensive guidelines in the docs/doc-standards/ directory.

    When generating rule content, focus on specific implementation requirements related to:
    - Parent/child rule relationships and hierarchy
    - Documentation content extraction and integration
    - Rule file path management and directory organization
    - Parallel workflow management for efficiency
    - Consistency validation across rule sets
    
    ## Rule Structure Requirements
    Rules must follow the format specified in rule 012 for standalone rules:
    1. Frontmatter must be exactly 4 lines: opening '---', description following MUST-WHEN-TO format, globs as array, closing '---'
    2. Title with version tag
    3. Main sections as JSON
    4. Examples section with concrete code examples
    5. Danger section with explicit NEVER statements
    
    You are generating the '{section}' section for rule {rule_id} ({rule_name}).
    {section_instructions.get("description", f"Generate content for {section} section")}
    
    {reasoning_instructions}
    
    IMPORTANT: These rules will be consumed by an AI assistant integrated in an IDE, so they must:
    1. Use explicit directives (MUST, SHOULD, NEVER)
    2. Have clear algorithmic decision criteria 
    3. Avoid ambiguity that could lead to inconsistent interpretation
    
    Your response must be VALID JSON that matches the expected structure.
    """

    # Add specific instructions for danger section to improve quality and fix structure
    if section == "danger":
        system_message += """
        IMPORTANT for danger section:
        1. DO NOT nest objects within the danger section - the critical_violations and specific_risks arrays should be at the root level
        2. Each critical violation MUST start with "NEVER" and be specific to this rule
        3. Provide AT LEAST 4-6 critical violations for comprehensive coverage
        4. Provide AT LEAST 3-5 specific risks describing concrete consequences
        5. Make violations very specific to the exact rule, not generic programming advice
        """

    # Create the user message with the structured format request
    user_message = f"""
    Generate the '{section}' section for rule {rule_id} ({rule_name}) in category {category} according to the following structure:
    
    {json.dumps(section_instructions.get("structure", {}), indent=2)}
    
    {context}
    
    The rule will be consumed by an AI assistant in an IDE, so it must be clear, explicit, and algorithmically processable.
    Return ONLY valid JSON that can be directly integrated into the rule file.
    """

    return {"system": system_message, "user": user_message}


def _generate_section_content(
    prompt: Dict[str, str], section: str, rule_name: str
) -> Dict[str, Any]:
    """
    Generate section content using the OpenAI API.

    Args:
        prompt: Dictionary with system and user messages
        section: The section being generated
        rule_name: The name of the rule

    Returns:
        Dictionary with the generated content
    """
    # Call the OpenAI API with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt["system"]},
                    {"role": "user", "content": prompt["user"]},
                ],
                temperature=0.7,
            )

            # Extract and parse the JSON response
            generated_content = json.loads(response.choices[0].message.content)

            # Post-process the danger section to fix common issues
            if section == "danger" and isinstance(generated_content, dict):
                generated_content = post_process_danger_section(
                    generated_content, rule_name
                )

            return generated_content

        except Exception as e:
            if attempt < max_retries - 1:
                print(
                    f"Error generating {section}, retrying ({attempt+1}/{max_retries}): {str(e)}"
                )
                time.sleep(2)  # Add a short delay before retrying
            else:
                print(
                    f"Failed to generate {section} after {max_retries} attempts: {str(e)}"
                )
                raise
