"""Example usage of the comprehensive deduplication system.

This example demonstrates how to use the deduplication system with various
configurations and monitoring capabilities for different use cases.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta
from typing import List

from src.project_context.ingestion.deduplication_monitor import (
    QualityAnalyzer,
    create_dashboard,
    create_production_monitor,
)
from src.project_context.ingestion.deduplication_system import (
    ComprehensiveDeduplicator,
    DeduplicationConfig,
    create_deduplicator,
)
from src.project_context.models.common import ContextItem


def create_sample_data() -> List[ContextItem]:
    """Create sample data with known duplicates for testing."""
    items = []
    base_time = datetime.utcnow() - timedelta(hours=1)

    # Create exact duplicates
    original_content = (
        "def calculate_total(items): return sum(item.price for item in items)"
    )
    for i in range(3):
        item = ContextItem(
            source_type="code",
            source_id=f"file_1_duplicate_{i}",
            entity_type="function",
            timestamp=base_time + timedelta(minutes=i * 5),
            content=original_content,
            title="calculate_total function",
            file_path="src/calculator.py",
            function_name="calculate_total",
        )
        items.append(item)

    # Create semantic duplicates (similar but not identical)
    similar_contents = [
        "def compute_sum(items): return sum(i.price for i in items)",
        "def total_price(item_list): return sum(item.price for item in item_list)",
        "def calculate_price_sum(items): return sum(x.price for x in items)",
    ]

    for i, content in enumerate(similar_contents):
        item = ContextItem(
            source_type="code",
            source_id=f"semantic_duplicate_{i}",
            entity_type="function",
            timestamp=base_time + timedelta(minutes=10 + i * 3),
            content=content,
            title="price calculation function",
            file_path=f"src/module_{i}.py",
            function_name=f"function_{i}",
            embedding=[random.random() for _ in range(384)],  # Simulate embedding
        )
        items.append(item)

    # Create temporal cluster (chat messages in sequence)
    chat_messages = [
        "I'm having trouble with the payment calculation",
        "The total isn't computing correctly",
        "Found the issue - missing tax calculation",
        "Fixed the payment calculation bug",
    ]

    for i, message in enumerate(chat_messages):
        item = ContextItem(
            source_type="chat",
            source_id=f"chat_message_{i}",
            entity_type="message",
            timestamp=base_time + timedelta(minutes=20 + i * 2),
            content=message,
            actor_id="user_123",
            session_id="session_abc",
            embedding=[random.random() for _ in range(384)],
        )
        items.append(item)

    # Add some unique items
    unique_contents = [
        "class DatabaseManager: def __init__(self): pass",
        "async def fetch_user_data(user_id): return await db.get_user(user_id)",
        "LOG: Application started successfully",
        "ERROR: Database connection failed",
    ]

    for i, content in enumerate(unique_contents):
        item = ContextItem(
            source_type=["code", "code", "monitor", "error"][i],
            source_id=f"unique_item_{i}",
            entity_type=["class", "function", "log", "error"][i],
            timestamp=base_time + timedelta(minutes=30 + i * 5),
            content=content,
            embedding=[random.random() for _ in range(384)] if i < 2 else None,
        )
        items.append(item)

    return items


async def basic_deduplication_example():
    """Basic deduplication example with default settings."""
    print("=== Basic Deduplication Example ===")

    # Create sample data
    items = create_sample_data()
    print(f"Created {len(items)} sample items")

    # Create deduplicator with default settings
    deduplicator = create_deduplicator()

    # Process deduplication
    result = await deduplicator.deduplicate_items(items)

    # Display results
    print(f"Total items processed: {result.total_items}")
    print(f"Exact duplicates found: {result.exact_duplicates}")
    print(f"Semantic duplicates found: {result.semantic_duplicates}")
    print(f"Temporal clusters created: {result.temporal_clusters}")
    print(f"Items merged: {result.merged_items}")
    print(f"Processing time: {result.processing_time_seconds:.2f} seconds")
    print(f"Quality score: {result.quality_score:.2f}")

    # Show duplicate groups
    print(f"\nFound {len(result.duplicate_groups)} duplicate groups:")
    for i, group in enumerate(result.duplicate_groups):
        print(
            f"  Group {i+1}: {group.total_items} items, "
            f"confidence: {group.confidence:.2f}, "
            f"strategy: {group.merge_strategy}"
        )


async def advanced_configuration_example():
    """Advanced deduplication with custom configuration."""
    print("\n=== Advanced Configuration Example ===")

    # Custom configuration for aggressive deduplication
    config = DeduplicationConfig(
        embedding_similarity_threshold=0.85,  # Lower threshold for more matches
        content_similarity_threshold=0.75,
        temporal_window_minutes=30,  # Shorter temporal window
        auto_merge_threshold=0.90,  # Lower auto-merge threshold
        confidence_threshold=0.75,
        batch_size=50,
    )

    # Create deduplicator with custom config
    deduplicator = ComprehensiveDeduplicator(config)

    # Create larger sample dataset
    items = []
    for _ in range(5):  # Multiply sample data
        items.extend(create_sample_data())

    print(f"Processing {len(items)} items with aggressive configuration")

    # Process with monitoring
    monitor = create_production_monitor()
    result = await deduplicator.deduplicate_items(items)
    monitor.record_operation(result)

    # Display results
    print(f"Advanced deduplication results:")
    print(f"  Exact duplicates: {result.exact_duplicates}")
    print(f"  Semantic duplicates: {result.semantic_duplicates}")
    print(f"  Processing time: {result.processing_time_seconds:.2f}s")
    print(f"  Items/second: {result.total_items/result.processing_time_seconds:.1f}")

    # Show performance metrics
    current_metrics = monitor.get_current_metrics()
    if current_metrics:
        print(f"  Performance score: {current_metrics.items_per_second:.1f} items/sec")
        print(f"  Quality score: {current_metrics.quality_score:.2f}")


async def quality_monitoring_example():
    """Example of quality monitoring and assessment."""
    print("\n=== Quality Monitoring Example ===")

    # Create deduplicator and items
    deduplicator = create_deduplicator(
        embedding_threshold=0.90, temporal_window_minutes=45
    )
    items = create_sample_data()

    # Process deduplication
    result = await deduplicator.deduplicate_items(items)

    # Create quality analyzer
    analyzer = QualityAnalyzer()

    # Assess quality (without ground truth)
    quality_assessment = await analyzer.assess_quality(result)

    print("Quality Assessment Results:")
    print(f"  Overall score: {quality_assessment.overall_score:.2f}")
    print(f"  Accuracy score: {quality_assessment.accuracy_score:.2f}")
    print(f"  Efficiency score: {quality_assessment.efficiency_score:.2f}")
    print(f"  Reliability score: {quality_assessment.reliability_score:.2f}")

    if quality_assessment.recommendations:
        print("  Recommendations:")
        for rec in quality_assessment.recommendations:
            print(f"    - {rec}")

    if quality_assessment.warning_flags:
        print("  Warning flags:")
        for warning in quality_assessment.warning_flags:
            print(f"    ! {warning}")


async def dashboard_monitoring_example():
    """Example of dashboard monitoring with alerts."""
    print("\n=== Dashboard Monitoring Example ===")

    # Create dashboard
    dashboard = create_dashboard()

    # Process multiple deduplication operations
    deduplicator = create_deduplicator()

    for i in range(3):
        print(f"Processing batch {i+1}...")
        items = create_sample_data()

        # Vary processing to trigger different conditions
        if i == 1:
            # Create a challenging dataset for batch 2
            items.extend(items * 3)  # More duplicates

        result = await deduplicator.deduplicate_items(items)
        dashboard.performance_monitor.record_operation(result)

    # Generate status report
    status_report = await dashboard.generate_status_report()

    print("Dashboard Status Report:")
    print(f"  System status: {status_report['system_status']}")
    print(f"  Report timestamp: {status_report['timestamp']}")

    if status_report.get("current_metrics"):
        metrics = status_report["current_metrics"]
        print(
            f"  Current processing speed: {metrics['items_per_second']:.1f} items/sec"
        )
        print(f"  Current quality score: {metrics['quality_score']:.2f}")

    if status_report.get("active_alerts"):
        alerts = status_report["active_alerts"]
        print(f"  Active alerts: {len(alerts)}")
        for alert in alerts:
            print(f"    - {alert['severity'].upper()}: {alert['message']}")

    # Alert summary
    alert_summary = status_report.get("alert_summary", {})
    if alert_summary:
        print("  Alert summary:")
        for key, count in alert_summary.items():
            print(f"    {key}: {count}")


async def performance_comparison_example():
    """Compare performance across different configurations."""
    print("\n=== Performance Comparison Example ===")

    # Test different configurations
    configs = {
        "conservative": DeduplicationConfig(
            embedding_similarity_threshold=0.95,
            auto_merge_threshold=0.95,
            batch_size=100,
        ),
        "balanced": DeduplicationConfig(
            embedding_similarity_threshold=0.90,
            auto_merge_threshold=0.90,
            batch_size=500,
        ),
        "aggressive": DeduplicationConfig(
            embedding_similarity_threshold=0.85,
            auto_merge_threshold=0.85,
            batch_size=1000,
        ),
    }

    # Create test dataset
    items = []
    for _ in range(10):
        items.extend(create_sample_data())

    print(f"Testing with {len(items)} items across different configurations:")

    results = {}
    for name, config in configs.items():
        print(f"  Testing {name} configuration...")

        deduplicator = ComprehensiveDeduplicator(config)
        result = await deduplicator.deduplicate_items(items.copy())

        results[name] = result

        print(f"    Processing time: {result.processing_time_seconds:.2f}s")
        print(
            f"    Items/second: {result.total_items/result.processing_time_seconds:.1f}"
        )
        print(
            f"    Total duplicates: {result.exact_duplicates + result.semantic_duplicates}"
        )
        print(f"    Quality score: {result.quality_score:.2f}")

    # Find best performing configuration
    best_performance = max(
        results.items(), key=lambda x: x[1].total_items / x[1].processing_time_seconds
    )
    best_quality = max(results.items(), key=lambda x: x[1].quality_score)

    print(
        f"  Best performance: {best_performance[0]} "
        f"({best_performance[1].total_items/best_performance[1].processing_time_seconds:.1f} items/sec)"
    )
    print(
        f"  Best quality: {best_quality[0]} "
        f"(score: {best_quality[1].quality_score:.2f})"
    )


async def main():
    """Run all examples."""
    print("Comprehensive Deduplication System Examples")
    print("=" * 50)

    await basic_deduplication_example()
    await advanced_configuration_example()
    await quality_monitoring_example()
    await dashboard_monitoring_example()
    await performance_comparison_example()

    print("\n" + "=" * 50)
    print("All examples completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
