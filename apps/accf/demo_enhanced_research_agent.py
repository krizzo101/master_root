#!/usr/bin/env python3
"""
Enhanced Research Agent Demo
============================

Demonstrates the comprehensive research agent with:
- Intelligent sequential research workflow
- Context7 technical documentation integration
- Smart query generation based on web context
- Multi-source synthesis and storage
"""

import asyncio
import logging
import sys
from typing import Dict, Any

from capabilities.research_agent import ResearchAgent


def setup_logging():
    """Setup logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("enhanced_research_demo.log"),
        ],
    )


def print_section(title: str, content: Any, separator: bool = True):
    """Print a formatted section."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

    if isinstance(content, dict):
        for key, value in content.items():
            print(f"\n{key}:")
            if isinstance(value, list):
                for i, item in enumerate(value[:3], 1):  # Show first 3 items
                    print(f"  {i}. {str(item)[:100]}...")
                if len(value) > 3:
                    print(f"  ... and {len(value) - 3} more")
            else:
                print(f"  {str(value)[:200]}...")
    elif isinstance(content, list):
        for i, item in enumerate(content[:5], 1):  # Show first 5 items
            print(f"{i}. {str(item)[:100]}...")
        if len(content) > 5:
            print(f"... and {len(content) - 5} more")
    else:
        print(str(content)[:500] + "..." if len(str(content)) > 500 else str(content))

    if separator:
        print("-" * 60)


def demo_research_workflow():
    """Demonstrate the enhanced research workflow."""
    print("🚀 Enhanced Research Agent Demo")
    print("=" * 60)

    # Initialize the research agent
    try:
        agent = ResearchAgent()
        print("✅ Research Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Research Agent: {e}")
        return

    # Test questions that should trigger different research paths
    test_questions = [
        {
            "question": "What are the latest developments in transformer architecture for natural language processing?",
            "description": "Academic + Web Research (should trigger ArXiv + web search)",
        },
        {
            "question": "How do I implement authentication in the OpenAI Python SDK?",
            "description": "Technical Documentation + Web Research (should trigger Context7 + web search)",
        },
        {
            "question": "What are the best practices for implementing RAG systems with LangChain?",
            "description": "Technical Documentation + Academic + Web Research (should trigger all sources)",
        },
    ]

    for i, test_case in enumerate(test_questions, 1):
        print(f"\n{'#'*80}")
        print(f"TEST CASE {i}: {test_case['description']}")
        print(f"Question: {test_case['question']}")
        print(f"{'#'*80}")

        try:
            # Run the enhanced research workflow
            result = agent.answer_question_with_external_tools(test_case["question"])

            # Display results
            print_section(
                "RESEARCH RESULTS",
                {
                    "Answer": result.get("answer", "No answer generated"),
                    "Confidence": result.get("confidence", "Unknown"),
                    "Sources Used": len(result.get("sources", [])),
                    "Total Sources": result.get("total_sources", 0),
                },
            )

            if "sources" in result:
                print_section(
                    "SOURCE BREAKDOWN",
                    {
                        "Knowledge Graph": len(
                            [s for s in result["sources"] if "neo4j" in s.lower()]
                        ),
                        "Web Pages": len(
                            [
                                s
                                for s in result["sources"]
                                if "http" in s and "context7" not in s
                            ]
                        ),
                        "Academic Papers": len(
                            [s for s in result["sources"] if "arxiv" in s.lower()]
                        ),
                        "Technical Docs": len(
                            [s for s in result["sources"] if "context7" in s.lower()]
                        ),
                    },
                )

            # Show detailed source information
            if "sources" in result and result["sources"]:
                print_section(
                    "DETAILED SOURCES", result["sources"][:5]
                )  # Show first 5 sources

        except Exception as e:
            print(f"❌ Research failed: {e}")
            logging.exception("Research error")


def demo_intelligent_query_generation():
    """Demonstrate the intelligent query generation capabilities."""
    print("\n🧠 Intelligent Query Generation Demo")
    print("=" * 60)

    try:
        agent = ResearchAgent()

        # Test the query generation methods
        test_question = "How to implement machine learning models with PyTorch for computer vision tasks?"

        print(f"Original Question: {test_question}")

        # Simulate web context (in real usage, this would come from web search results)
        mock_web_context = """
        Title: PyTorch Tutorial: Getting Started with Deep Learning
        Description: Learn how to build neural networks with PyTorch
        Content: PyTorch is a popular deep learning framework that provides...
        Title: Computer Vision with PyTorch: A Complete Guide
        Description: Comprehensive guide to implementing CV models
        Content: Computer vision tasks include image classification, object detection...
        """

        # Test ArXiv query generation
        arxiv_queries = agent._generate_arxiv_queries(test_question, mock_web_context)
        print_section("Generated ArXiv Queries", arxiv_queries)

        # Test Context7 query generation
        context7_queries = agent._generate_context7_queries(
            test_question, mock_web_context
        )
        print_section("Generated Context7 Queries", context7_queries)

        # Test heuristics
        print_section(
            "Research Heuristics",
            {
                "Should use academic research": agent._should_use_academic_research(
                    test_question
                ),
                "Should use technical docs": agent._should_use_context7_docs(
                    test_question
                ),
            },
        )

    except Exception as e:
        print(f"❌ Query generation demo failed: {e}")
        logging.exception("Query generation error")


def demo_context7_integration():
    """Demonstrate Context7 integration."""
    print("\n📚 Context7 Integration Demo")
    print("=" * 60)

    try:
        from capabilities.tools.context7_tool import Context7Tool

        tool = Context7Tool()

        # Test library resolution
        test_libraries = ["openai", "react", "pytorch"]

        for library in test_libraries:
            print(f"\nTesting library resolution for: {library}")
            try:
                # Note: This would require actual MCP server setup
                print(f"  Would resolve: {library} -> Context7 library ID")
            except Exception as e:
                print(f"  ❌ Resolution failed: {e}")

        print("\nNote: Full Context7 integration requires MCP server setup")

    except Exception as e:
        print(f"❌ Context7 demo failed: {e}")
        logging.exception("Context7 error")


def main():
    """Main demo function."""
    setup_logging()

    print("🎯 Enhanced Research Agent - Comprehensive Demo")
    print("=" * 80)
    print("\nThis demo showcases the enhanced research agent with:")
    print("• Intelligent sequential research workflow")
    print("• Context7 technical documentation integration")
    print("• Smart query generation based on web context")
    print("• Multi-source synthesis and storage")
    print("• Vector database integration for RAG")

    # Run demos
    demo_research_workflow()
    demo_intelligent_query_generation()
    demo_context7_integration()

    print("\n" + "=" * 80)
    print("🎉 Demo Complete!")
    print("\nKey Enhancements Implemented:")
    print("✅ Context7 MCP tool integration")
    print("✅ Intelligent query generation")
    print("✅ Sequential research workflow")
    print("✅ Web context extraction")
    print("✅ Multi-source synthesis")
    print("✅ Enhanced architecture")
    print(
        "\nThe research agent now provides comprehensive, context-aware research capabilities!"
    )


if __name__ == "__main__":
    main()
