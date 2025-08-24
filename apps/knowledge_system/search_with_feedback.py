#!/usr/bin/env python3
"""
Interactive Search with Feedback - This is how the system gets smarter
Use this for actual searches so the system learns what helps
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root")

import time

from apps.knowledge_system.adaptive_learning import AdaptiveLearningSystem, UsageContext
from apps.knowledge_system.unified_intelligent_search import UnifiedIntelligentSearch


def search_and_learn(query: str, limit: int = 5):
    """
    Search with immediate feedback loop
    This is how I make the system smarter
    """

    search = UnifiedIntelligentSearch()
    learning = AdaptiveLearningSystem()

    print(f"\nSearching: '{query}'")
    print("=" * 80)

    start_time = time.time()
    results = search.search(query, limit=limit, expand_context=False)
    search_time = time.time() - start_time

    if not results:
        print("No results found.")
        search.close()
        learning.close()
        return

    # Display results with intelligence indicators
    knowledge_ids = []
    for i, result in enumerate(results, 1):
        knowledge_ids.append(result.knowledge_id)

        print(f"\n{i}. {result.source[:70]}")
        print(f"   Score: {result.combined_score:.3f} ", end="")

        # Show which intelligence components are active
        indicators = []
        if result.vector_score > 0.5:
            indicators.append(f"V:{result.vector_score:.2f}")
        if result.graph_score > 0:
            indicators.append(f"G:{result.graph_score:.2f}")
        if result.semantic_score > 0:
            indicators.append(f"S:{result.semantic_score:.2f}")
        if result.learning_score > 0:
            indicators.append(f"L:{result.learning_score:.2f}")

        print(f"({' '.join(indicators)})")
        print(f"   {result.relevance_explanation}")

    # Get feedback
    print("\n" + "-" * 80)
    print("FEEDBACK (this makes the system smarter):")
    print("  [1-5] - Mark result N as helpful")
    print("  [a]   - All results were helpful")
    print("  [n]   - None were helpful")
    print("  [s]   - Skip feedback")

    feedback = input("Your feedback: ").strip().lower()

    # Process feedback
    helpful_ids = []
    task_completed = False

    if feedback == "a":
        helpful_ids = knowledge_ids
        task_completed = True
        print("✓ Marked all as helpful")
    elif feedback == "n":
        task_completed = False
        print("✗ Marked as unhelpful - system will learn")
    elif feedback == "s":
        print("Skipped feedback")
        search.close()
        learning.close()
        return
    elif feedback.isdigit():
        idx = int(feedback) - 1
        if 0 <= idx < len(knowledge_ids):
            helpful_ids = [knowledge_ids[idx]]
            task_completed = True
            print(f"✓ Marked result {feedback} as helpful")

    # Record the learning session
    if feedback != "s":
        context = UsageContext(
            query=query,
            knowledge_ids=knowledge_ids,
            strategy_used="unified",
            task_completed=task_completed,
            time_to_solution=search_time if task_completed else None,
        )

        learning.record_usage_session(context)

        # Boost helpful results specifically
        if helpful_ids and task_completed:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                "bolt://localhost:7687", auth=("neo4j", "password")
            )
            with driver.session() as session:
                for kid in helpful_ids:
                    session.run(
                        """
                        MATCH (k:Knowledge {knowledge_id: $kid})
                        SET k.success_count = COALESCE(k.success_count, 0) + 1,
                            k.confidence_score = CASE
                                WHEN k.confidence_score + 0.05 > 1.0 THEN 1.0
                                ELSE k.confidence_score + 0.05
                            END
                    """,
                        kid=kid,
                    )
            driver.close()
            print(f"Boosted {len(helpful_ids)} helpful results")

    # Show learning stats
    stats = learning.get_learning_statistics()
    print(f"\nSystem Learning Stats:")
    print(f"  Total sessions: {stats['sessions']['total']}")
    print(f"  Success rate: {stats['sessions']['success_rate']:.1%}")

    search.close()
    learning.close()


def test_with_feedback():
    """Test that the system actually improves with feedback"""

    print("TESTING SEARCH WITH FEEDBACK LOOP")
    print("=" * 80)
    print("This is how the system becomes intelligent - through use\n")

    # Test queries
    test_queries = [
        "How to handle streaming errors in AsyncOpenAI",
        "Exception handling best practices",
        "OpenAI client initialization",
    ]

    for query in test_queries:
        search_and_learn(query, limit=3)
        print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Use as command line tool
        query = " ".join(sys.argv[1:])
        search_and_learn(query)
    else:
        # Run test
        test_with_feedback()
