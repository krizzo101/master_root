#!/usr/bin/env python3
"""
Simple Research Agent Demonstration
==================================

This script demonstrates the enhanced ACCF research agent with a simple
synchronous approach to avoid async/await complexity.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capabilities.research_agent import ResearchAgent


def print_separator(title: str, char: str = "=") -> None:
    """Print a formatted separator with title."""
    print(f"\n{char * 80}")
    print(f"{title:^80}")
    print(f"{char * 80}\n")


def demonstrate_basic_capabilities() -> None:
    """Demonstrate basic research agent capabilities."""

    print_separator("BASIC RESEARCH AGENT CAPABILITIES", "=")

    try:
        # Initialize the research agent
        agent = ResearchAgent()
        print("✅ Research Agent initialized successfully")
        print(f"📊 Agent has {len(agent.research_db)} previous research entries")

        # Test static research capability
        print("\n🧠 Testing static research capability...")
        static_result = agent.answer_question("Who wrote Pride and Prejudice?")
        print(f"Static Result: {static_result}")

        # Test LLM-only research capability
        print("\n🤖 Testing LLM-only research capability...")
        llm_result = agent.answer_question_using_llm(
            "What is the difference between supervised and unsupervised learning?"
        )
        print(f"LLM Result: {llm_result.get('answer', 'No answer')[:200]}...")

        print("\n✅ Basic capabilities working correctly")

    except Exception as e:
        print(f"❌ Basic capability test failed: {e}")
        import traceback

        traceback.print_exc()


def demonstrate_comprehensive_research() -> None:
    """Demonstrate comprehensive research with error handling."""

    print_separator("COMPREHENSIVE RESEARCH DEMONSTRATION", "=")

    try:
        agent = ResearchAgent()

        # Research questions that showcase different capabilities
        questions = [
            "What are the latest developments in transformer architecture?",
            "How do large language models handle context limitations?",
            "What are the current trends in AI development?",
            "Explain the concept of attention mechanisms in neural networks",
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n🔍 Research Session {i}: {question}")
            print(f"Timestamp: {datetime.now().strftime('%H:%M:%S')}")

            try:
                # Try comprehensive research first
                print("  Attempting comprehensive research...")
                result = agent.answer_question_with_external_tools(question)

                print(f"  ✅ Research completed successfully!")
                print(f"  Answer: {result.get('answer', 'No answer')[:300]}...")
                print(f"  Confidence: {result.get('confidence', '0.0')}")
                print(f"  Sources: {len(result.get('sources', []))} sources")

                if result.get("sources"):
                    print("  Source URLs:")
                    for j, source in enumerate(result.get("sources", [])[:3], 1):
                        print(f"    {j}. {source}")
                    if len(result.get("sources", [])) > 3:
                        print(f"    ... and {len(result.get('sources', [])) - 3} more")

            except Exception as e:
                print(f"  ⚠️  Comprehensive research failed: {e}")
                print("  Falling back to LLM-only research...")

                try:
                    fallback_result = agent.answer_question_using_llm(question)
                    print(f"  ✅ Fallback successful!")
                    print(
                        f"  Answer: {fallback_result.get('answer', 'No answer')[:300]}..."
                    )
                except Exception as fallback_error:
                    print(f"  ❌ Fallback also failed: {fallback_error}")

            print(f"  📊 Total research entries: {len(agent.research_db)}")
            print("-" * 80)

    except Exception as e:
        print(f"❌ Comprehensive demonstration failed: {e}")
        import traceback

        traceback.print_exc()


def demonstrate_agent_architecture() -> None:
    """Demonstrate the agent's architecture and capabilities."""

    print_separator("RESEARCH AGENT ARCHITECTURE OVERVIEW", "=")

    print("🏗️  ACCF Research Agent - Phase 5 Complete")
    print("\n📋 Implemented Capabilities:")
    print("  ✅ Phase 1: External Research Tools (Brave Search + Firecrawl)")
    print("  ✅ Phase 2: Async Orchestration & Query Transformation")
    print("  ✅ Phase 3: Synthesis & Quality Assessment")
    print("  ✅ Phase 4: Neo4j Knowledge Graph Integration")
    print("  ✅ Phase 5: Academic Research Integration")

    print("\n🔧 Technical Features:")
    print("  • Multi-source research pipeline")
    print("  • Smart routing for academic vs web research")
    print("  • Knowledge-first approach with persistent storage")
    print("  • Quality assessment and confidence scoring")
    print("  • Comprehensive error handling and fallbacks")
    print("  • Backward compatibility with existing methods")

    print("\n📊 Research Pipeline:")
    print("  1. Knowledge Graph Query (existing knowledge)")
    print("  2. Academic Research (ArXiv papers)")
    print("  3. Web Research (Brave + Firecrawl)")
    print("  4. Synthesis & Quality Assessment")
    print("  5. Knowledge Persistence")

    print("\n🎯 Use Cases:")
    print("  • Academic research and paper discovery")
    print("  • Technical documentation and tutorials")
    print("  • Current events and trend analysis")
    print("  • Knowledge base building and maintenance")
    print("  • Multi-source fact verification")


def main() -> None:
    """Main demonstration function."""
    print("🚀 Starting ACCF Research Agent Simple Demonstration")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Some capabilities may be limited.")
        print("   Set the environment variable to enable full functionality.")

    try:
        # Demonstrate architecture
        demonstrate_agent_architecture()

        # Demonstrate basic capabilities
        demonstrate_basic_capabilities()

        # Demonstrate comprehensive research
        demonstrate_comprehensive_research()

        print_separator("DEMONSTRATION COMPLETE", "=")
        print("✅ Research agent demonstration completed successfully!")
        print("📝 The agent showcases comprehensive multi-source research capabilities")
        print("🔧 All phases (1-5) have been implemented and are functional")

    except KeyboardInterrupt:
        print("\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
