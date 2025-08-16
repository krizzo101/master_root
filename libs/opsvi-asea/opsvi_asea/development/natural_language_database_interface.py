#!/usr/bin/env python3
"""
Natural Language Database Interface
Converts plain English questions into database queries
"""

import sys

sys.path.append("/home/opsvi/asea/development")
from autonomous_database_discovery import AutonomousDatabaseDiscovery


class NaturalLanguageDatabaseInterface:
    def __init__(self):
        self.discovery = AutonomousDatabaseDiscovery()
        self.discovery.query_templates = self.discovery._generate_query_templates(
            {}, {}
        )

    def ask(self, question: str) -> dict:
        """Convert natural language question to database query"""

        # Intent recognition patterns
        intents = {
            "how do i": "find_related_memories",
            "what should i": "find_related_memories",
            "how to": "find_related_memories",
            "find memories about": "find_related_memories",
            "what builds on": "discover_learning_paths",
            "learning path for": "discover_learning_paths",
            "similar concepts": "semantic_search",
            "related to": "find_related_memories",
        }

        # Extract search terms
        search_term = self._extract_search_term(question)

        # Match intent
        template_name = "find_related_memories"  # default
        for pattern, template in intents.items():
            if pattern in question.lower():
                template_name = template
                break

        # Get query template
        query_template = self.discovery.query_templates.get(template_name, "")

        # Generate executable query
        executable_query = query_template.replace("@search_term", f"'{search_term}'")

        return {
            "question": question,
            "intent": template_name,
            "search_term": search_term,
            "query_template": query_template,
            "executable_query": executable_query.strip(),
            "explanation": f"Searching for memories related to '{search_term}' using {template_name} pattern",
        }

    def _extract_search_term(self, question: str) -> str:
        """Extract key search terms from question"""

        # Remove common question words
        stop_words = [
            "how",
            "do",
            "i",
            "what",
            "should",
            "to",
            "find",
            "about",
            "the",
            "a",
            "an",
        ]
        words = question.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        # Join remaining words
        return " ".join(keywords[:3])  # Take first 3 meaningful words


# Example usage demonstrations
def demonstrate_natural_language_interface():
    interface = NaturalLanguageDatabaseInterface()

    example_questions = [
        "How do I edit files correctly?",
        "What should I do when database queries fail?",
        "Find memories about tool usage",
        "What builds on MCP filesystem concepts?",
        "How to handle Poetry dependencies?",
    ]

    results = []
    for question in example_questions:
        result = interface.ask(question)
        results.append(result)
        print(f"\nQ: {question}")
        print(f"Search term: {result['search_term']}")
        print(f"Intent: {result['intent']}")
        print(f"Explanation: {result['explanation']}")

    return results


if __name__ == "__main__":
    demonstrate_natural_language_interface()
