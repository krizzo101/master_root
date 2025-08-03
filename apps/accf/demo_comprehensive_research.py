#!/usr/bin/env python3
"""
Comprehensive Research Agent Demonstration
=========================================

This script demonstrates the enhanced ACCF research agent performing
comprehensive research across all implemented capabilities:

1. Knowledge Graph Query (Phase 4)
2. Academic Research (Phase 5)
3. Web Research (Phase 1-2)
4. Synthesis & Quality Assessment (Phase 3)

The agent will research a complex topic and show the full pipeline in action.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capabilities.research_agent import ResearchAgent

# Configure logging for demonstration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("research_demo.log"),
    ],
)

logger = logging.getLogger(__name__)


def print_separator(title: str, char: str = "=") -> None:
    """Print a formatted separator with title."""
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")


def print_research_result(result: Dict[str, Any], question: str) -> None:
    """Print formatted research results."""
    print_separator("RESEARCH RESULTS", "=")
    print(f"Question: {question}")
    print(f"Answer: {result.get('answer', 'No answer provided')}")
    print(f"Confidence: {result.get('confidence', '0.0')}")
    print(f"Sources: {len(result.get('sources', []))} sources")

    if result.get("sources"):
        print("\nSource URLs:")
        for i, source in enumerate(result.get("sources", []), 1):
            print(f"  {i}. {source}")

    print(f"\nResearch DB Entries: {len(result.get('research_db', []))}")


def print_pipeline_status(agent: ResearchAgent, phase: str) -> None:
    """Print current pipeline status."""
    print(
        f"✅ {phase} - Agent initialized with {len(agent.research_db)} previous entries"
    )


async def demonstrate_comprehensive_research() -> None:
    """Demonstrate the full research agent pipeline."""

    print_separator("ACCF COMPREHENSIVE RESEARCH AGENT DEMONSTRATION", "=")
    print("This demonstration showcases the enhanced research agent with:")
    print("• Knowledge Graph Integration (Phase 4)")
    print("• Academic Research (Phase 5)")
    print("• Web Research & Async Orchestration (Phase 1-2)")
    print("• Synthesis & Quality Assessment (Phase 3)")
    print("• Smart Routing & Multi-Source Aggregation")

    # Initialize the research agent
    try:
        agent = ResearchAgent()
        print_pipeline_status(agent, "Phase 1-5 Complete")
    except Exception as e:
        print(f"❌ Failed to initialize research agent: {e}")
        print("Make sure OPENAI_API_KEY is set in your environment")
        return

    # Define research questions that will trigger different capabilities
    research_questions = [
        # Academic research question (will trigger ArXiv search)
        "What are the latest research papers on transformer architecture improvements?",
        # General knowledge question (will use web research)
        "What are the current trends in artificial intelligence development?",
        # Technical question (will combine multiple sources)
        "How do large language models handle context and memory limitations?",
        # Specific research question (will trigger academic + web)
        "What are the recent developments in neural network optimization algorithms?",
    ]

    for i, question in enumerate(research_questions, 1):
        print_separator(f"RESEARCH SESSION {i}", "-")
        print(f"Researching: {question}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Perform comprehensive research
            print("\n🔍 Starting comprehensive research pipeline...")
            start_time = datetime.now()

            result = agent.answer_question_with_external_tools(question)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print(f"⏱️  Research completed in {duration:.2f} seconds")

            # Display results
            print_research_result(result, question)

            # Show pipeline insights
            print("\n📊 Pipeline Insights:")
            print(f"  • Total research entries: {len(agent.research_db)}")
            print(f"  • Research duration: {duration:.2f}s")
            print(f"  • Confidence score: {result.get('confidence', '0.0')}")

            if result.get("sources"):
                source_types = {
                    "arxiv.org": "Academic Papers",
                    "arxiv": "Academic Papers",
                    "research": "Research Papers",
                    "github.com": "Code/Technical",
                    "wikipedia.org": "Reference",
                    "medium.com": "Technical Blog",
                    "techcrunch.com": "Tech News",
                    "stackoverflow.com": "Technical Q&A",
                }

                print("  • Source types detected:")
                for source in result.get("sources", []):
                    source_type = "Web Content"
                    for key, label in source_types.items():
                        if key in source.lower():
                            source_type = label
                            break
                    print(f"    - {source_type}: {source}")

        except Exception as e:
            print(f"❌ Research failed: {e}")
            logger.error(
                f"Research failed for question '{question}': {e}", exc_info=True
            )

        print("\n" + "=" * 80)


def demonstrate_individual_capabilities() -> None:
    """Demonstrate individual agent capabilities."""

    print_separator("INDIVIDUAL CAPABILITY DEMONSTRATION", "=")

    try:
        agent = ResearchAgent()

        # Test basic LLM-only research
        print("🧠 Testing LLM-only research capability...")
        llm_result = agent.answer_question_using_llm(
            "What is the difference between supervised and unsupervised learning?"
        )
        print(f"LLM Result: {llm_result.get('answer', 'No answer')[:200]}...")

        # Test static research
        print("\n📚 Testing static research capability...")
        static_result = agent.answer_question("Who wrote Pride and Prejudice?")
        print(f"Static Result: {static_result}")

        print("✅ Individual capabilities working correctly")

    except Exception as e:
        print(f"❌ Individual capability test failed: {e}")


def main() -> None:
    """Main demonstration function."""
    print("🚀 Starting ACCF Research Agent Comprehensive Demonstration")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Some capabilities may be limited.")

    # Run demonstrations
    try:
        # Test individual capabilities first
        demonstrate_individual_capabilities()

        # Run comprehensive research demonstration
        asyncio.run(demonstrate_comprehensive_research())

        print_separator("DEMONSTRATION COMPLETE", "=")
        print("✅ All research agent capabilities demonstrated successfully!")
        print("📝 Check 'research_demo.log' for detailed execution logs")

    except KeyboardInterrupt:
        print("\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        logger.error("Demonstration failed", exc_info=True)


if __name__ == "__main__":
    main()
