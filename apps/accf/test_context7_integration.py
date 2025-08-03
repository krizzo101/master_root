#!/usr/bin/env python3
"""
Test script to debug Context7 integration in the research agent.
"""

import asyncio
import json
import logging
from capabilities.research_agent import ResearchAgent
from capabilities.tools.context7_tool import Context7Tool

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_context7_direct():
    """Test Context7 tool directly."""
    print("=== Testing Context7 Tool Directly ===")

    try:
        context7_tool = Context7Tool()

        # Test with specific library names
        test_libraries = ["openai", "react", "next.js", "fastapi"]

        for library in test_libraries:
            print(f"\n--- Testing library: {library} ---")
            try:
                result = await context7_tool.search_and_get_docs(library, tokens=2000)
                print(f"✅ Success: {result.library_id}")
                print(f"Content length: {len(result.content)} chars")
                print(f"Content preview: {result.content[:200]}...")
            except Exception as e:
                print(f"❌ Failed: {e}")

    except Exception as e:
        print(f"❌ Context7 tool initialization failed: {e}")


def test_research_agent_query_generation():
    """Test the research agent's query generation logic."""
    print("\n=== Testing Research Agent Query Generation ===")

    try:
        agent = ResearchAgent()

        # Test questions that should trigger Context7
        test_questions = [
            "How do I implement authentication in the OpenAI Python SDK?",
            "What are the best practices for React hooks?",
            "How to set up a Next.js project with TypeScript?",
            "What are the latest features in FastAPI?",
        ]

        for question in test_questions:
            print(f"\n--- Testing question: {question} ---")

            # Test if Context7 should be used
            should_use = agent._should_use_context7_docs(question)
            print(f"Should use Context7: {should_use}")

            if should_use:
                # Test web context extraction (simulated)
                web_context = "OpenAI Python SDK documentation shows authentication methods. React hooks provide state management."

                # Test query generation
                try:
                    queries = agent._generate_context7_queries(question, web_context)
                    print(f"Generated queries: {queries}")

                    # Test Context7 gathering
                    if queries:
                        print("Testing Context7 gathering...")
                        results = agent._gather_context7_docs_with_queries(queries)
                        print(f"Context7 results: {len(results)} found")
                        for result in results:
                            print(
                                f"  - {result.library_id}: {len(result.content)} chars"
                            )

                except Exception as e:
                    print(f"❌ Query generation/gathering failed: {e}")
                    import traceback

                    traceback.print_exc()

    except Exception as e:
        print(f"❌ Research agent test failed: {e}")
        import traceback

        traceback.print_exc()


async def test_full_research_pipeline():
    """Test the full research pipeline with Context7 integration."""
    print("\n=== Testing Full Research Pipeline ===")

    try:
        agent = ResearchAgent()

        # Test a question that should trigger Context7
        question = "How do I implement authentication in the OpenAI Python SDK?"

        print(f"Testing question: {question}")

        # Run the full pipeline
        result = agent.answer_question_with_external_tools(question)

        print(f"Answer: {result.get('answer', 'No answer')[:500]}...")
        print(f"Confidence: {result.get('confidence', 'Unknown')}")
        print(f"Sources: {result.get('sources', [])}")

    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all tests."""
    print("🔍 Context7 Integration Debug Test")
    print("=" * 60)

    # Test 1: Direct Context7 tool
    asyncio.run(test_context7_direct())

    # Test 2: Research agent query generation
    test_research_agent_query_generation()

    # Test 3: Full research pipeline
    asyncio.run(test_full_research_pipeline())

    print("\n" + "=" * 60)
    print("✅ Debug test completed")


if __name__ == "__main__":
    main()
