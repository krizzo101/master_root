# FILE_MAP_BEGIN
"""
{"file_metadata":{"title":"Domain Knowledge Utility","description":"This module provides domain-specific knowledge for different types of rules.","last_updated":"2025-03-12","type":"python"},"ai_instructions":"When reading this file, identify the section you need and use the read_file tool to read the specific line range indicated. DO NOT proceed without reading the relevant sections.","sections":[{"name":"Imports","description":"Imports necessary type definitions for type hinting.","line_start":3,"line_end":5},{"name":"get_domain_knowledge Function","description":"Function to retrieve domain-specific knowledge based on rule ID, name, and category.","line_start":6,"line_end":153},{"name":"get_example_language Function","description":"Function to retrieve the preferred programming language for examples based on the category.","line_start":154,"line_end":173}],"key_elements":[{"name":"get_domain_knowledge","description":"Function to retrieve domain-specific knowledge based on rule ID, name, and category.","line":10},{"name":"get_example_language","description":"Function to retrieve the preferred programming language for examples based on the category.","line":154},{"name":"base_knowledge","description":"String containing base knowledge applicable to all rules.","line":23},{"name":"category_knowledge","description":"Dictionary mapping categories to specific domain knowledge.","line":29},{"name":"rule_specific_knowledge","description":"Dictionary mapping specific rule IDs to targeted knowledge.","line":66},{"name":"specific_knowledge","description":"Knowledge retrieved based on the provided rule ID.","line":126},{"name":"category_specific","description":"Knowledge retrieved based on the provided category.","line":127},{"name":"combined_knowledge","description":"Final combined knowledge string to be returned by the function.","line":129},{"name":"language_map","description":"Dictionary mapping categories to preferred programming languages.","line":156}]}
"""
# FILE_MAP_END

"""
Domain Knowledge Utility

This module provides domain-specific knowledge for different types of rules.
"""


def get_domain_knowledge(rule_id: str, rule_name: str, category: str) -> str:
    """
    Get domain-specific knowledge for a rule based on its ID, name, and category.

    Args:
        rule_id: The ID of the rule
        rule_name: The name of the rule
        category: The category of the rule

    Returns:
        A string containing domain-specific knowledge for the rule
    """
    # Base knowledge that applies to all rules
    base_knowledge = """
    Ensure your example demonstrates:
    - Clear code organization
    - Proper error handling
    - Appropriate comments
    - Best practices for the specific domain
    """

    # Map categories to specific domain knowledge
    category_knowledge = {
        "Core": """
        Core rules apply to fundamental development practices:
        - Focus on code organization and structure
        - Emphasize maintainability and readability
        - Consider performance implications
        - Include proper documentation
        """,
        "LLM Integration": """
        When demonstrating LLM integration:
        - Show proper prompt engineering practices
        - Include context management techniques
        - Demonstrate error handling for API failures
        - Show best practices for parsing and validating responses
        - Include examples of handling rate limiting and timeouts
        - Demonstrate prompt templating and dynamic prompt generation
        """,
        "Multi-Agent": """
        When demonstrating multi-agent systems:
        - Show coordination patterns between agents
        - Include proper message passing and communication protocols
        - Demonstrate state management across agents
        - Show conflict resolution approaches
        - Include handling for agent failure scenarios
        - Demonstrate asynchronous processing models
        """,
        "Knowledge Management": """
        When demonstrating knowledge management:
        - Show efficient knowledge retrieval patterns
        - Include knowledge persistence strategies
        - Demonstrate knowledge validation techniques
        - Show approaches for knowledge updating
        - Include context-aware knowledge retrieval
        """,
        "Python Engine": """
        When demonstrating Python engine functionality:
        - Focus on Pythonic code patterns
        - Demonstrate proper use of data structures
        - Include type hints and documentation
        - Show efficient algorithmic approaches
        - Include proper error handling with specific exceptions
        - Demonstrate performance considerations
        """,
        "System Interface": """
        When demonstrating system interfaces:
        - Show clean API design
        - Include proper interface documentation
        - Demonstrate abstraction techniques
        - Show version compatibility handling
        - Include robust error handling at boundaries
        - Demonstrate proper resource management
        """,
    }

    # Map specific rule IDs to targeted knowledge
    rule_specific_knowledge = {
        "030": """
        When demonstrating reasoning methods:
        - Show examples of formal reasoning approaches
        - Include step-by-step problem decomposition
        - Demonstrate tree-of-thought reasoning
        - Show self-critique and verification steps
        - Include traceability of decision-making
        """,
        "020": """
        When demonstrating response structure:
        - Show clear organization of information
        - Demonstrate progressive disclosure techniques
        - Include proper formatting and information hierarchy
        - Show adaptive response patterns based on context
        """,
        "1055": """
        When demonstrating prompt engineering:
        - Show techniques for prompt clarity and specificity
        - Include examples of context injection
        - Demonstrate methods for preventing prompt injection
        - Show progression from basic to optimized prompts
        - Include techniques for reducing token usage while maintaining quality
        """,
        "1150": """
        When demonstrating knowledge retrieval:
        - Show efficient indexing techniques
        - Include semantic search implementations
        - Demonstrate caching strategies
        - Show approaches for handling large knowledge bases
        - Include relevance scoring methods
        """,
        "1100": """
        When demonstrating agent architecture:
        - Show modular component design
        - Include dependency injection patterns
        - Demonstrate event-driven communication
        - Show state management approaches
        - Include testing strategies for agent components
        """,
    }

    # Combine knowledge based on category and rule ID
    specific_knowledge = rule_specific_knowledge.get(rule_id, "")
    category_specific = category_knowledge.get(category, "")

    combined_knowledge = f"""
    DOMAIN KNOWLEDGE:
    {base_knowledge}

    {category_specific}

    {specific_knowledge}
    """

    return combined_knowledge


def get_example_language(category: str) -> str:
    """
    Get the preferred programming language for examples based on the category.

    Args:
        category: The category of the rule

    Returns:
        The preferred programming language for the category
    """
    # Default language mapping
    language_map = {
        "Core": "python",
        "LLM Integration": "python",
        "Multi-Agent": "python",
        "Knowledge Management": "python",
        "Python Engine": "python",
        "System Interface": "python",
    }

    return language_map.get(category, "python")
