#!/usr/bin/env python3
"""Example usage of the unified context ingestion pipeline."""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.project_context.ingestion import (
    AdapterRegistry,
    ChatAdapter,
    CodeAdapter,
    ConfigManager,
    PipelineOrchestrator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def basic_pipeline_example():
    """Basic example of running the ingestion pipeline."""
    print("=== Basic Pipeline Example ===")

    # Create orchestrator without config file (uses defaults)
    orchestrator = PipelineOrchestrator()

    try:
        # Initialize the orchestrator
        await orchestrator.initialize()

        # Get status
        status = await orchestrator.get_status()
        print(f"Registered adapters: {len(status['registry']['adapters'])}")

        # Run for a short time (5 seconds)
        print("Starting pipeline for 5 seconds...")
        await orchestrator.start(adapter_ids=["chat"], wait=False)
        await asyncio.sleep(5)

        # Get final status
        status = await orchestrator.get_status()
        print(f"Pipeline status: {status['pipeline']}")

    finally:
        await orchestrator.cleanup()


async def config_based_example():
    """Example using configuration file."""
    print("\n=== Configuration-Based Example ===")

    # Create a sample config
    config_path = Path("sample_config.yaml")

    # Create orchestrator with config
    orchestrator = PipelineOrchestrator()

    # Create template configuration
    orchestrator.create_template_config(config_path)
    print(f"Created template config: {config_path}")

    try:
        # Load with config
        orchestrator = PipelineOrchestrator(config_path=config_path)
        await orchestrator.initialize()

        print("Pipeline initialized with configuration")

        # Show registered adapters
        status = await orchestrator.get_status()
        print("Available adapters:")
        for adapter_id in status["registry"]["adapters"]:
            print(f"  - {adapter_id}")

    finally:
        await orchestrator.cleanup()
        # Clean up config file
        if config_path.exists():
            config_path.unlink()


async def manual_setup_example():
    """Example of manually setting up pipeline components."""
    print("\n=== Manual Setup Example ===")

    # Create individual components
    config_manager = ConfigManager()
    registry = AdapterRegistry()

    # Register adapters manually
    chat_config = ChatAdapter.default_config()
    code_config = CodeAdapter.default_config()

    registry.register_adapter("chat", ChatAdapter, chat_config)
    registry.register_adapter("code", CodeAdapter, code_config)

    print(f"Registered {len(registry.list_adapters())} adapters manually")

    # Validate adapters
    validation_results = registry.validate_adapters()
    print(f"Valid adapters: {len(validation_results['valid_adapters'])}")
    print(f"Invalid adapters: {len(validation_results['invalid_adapters'])}")

    if validation_results["invalid_adapters"]:
        print("Validation errors:")
        for error in validation_results["validation_errors"]:
            print(f"  - {error['adapter_id']}: {error['error']}")


async def monitoring_example():
    """Example demonstrating monitoring capabilities."""
    print("\n=== Monitoring Example ===")

    from src.project_context.ingestion.monitoring import PipelineMonitor

    # Create and start monitor
    monitor = PipelineMonitor()

    try:
        await monitor.start()

        # Record some sample metrics
        await monitor.record_pipeline_metric("throughput", 42.5)
        await monitor.record_pipeline_metric("error_rate", 0.02)
        await monitor.record_adapter_metric("chat", "processing_rate", 15.0)

        # Get monitoring status
        status = await monitor.get_monitoring_status()
        print("Monitoring status:")
        print(f"  - Metrics count: {status['metrics_count']}")
        print(f"  - Active alerts: {status['active_alerts_count']}")

        # Show some metrics
        if status["metrics_summary"]:
            print("Sample metrics:")
            for metric_name, metric_data in list(status["metrics_summary"].items())[:3]:
                print(f"  - {metric_name}: {metric_data['latest_value']}")

    finally:
        await monitor.stop()


async def context_manager_example():
    """Example using context manager for automatic lifecycle management."""
    print("\n=== Context Manager Example ===")

    orchestrator = PipelineOrchestrator()

    # Use context manager for automatic cleanup
    async with orchestrator.managed_lifecycle(adapter_ids=["chat"]):
        print("Pipeline running in context manager...")

        # Do some work
        await asyncio.sleep(2)

        # Get status
        status = await orchestrator.get_status()
        print(f"Pipeline running: {status['orchestrator']['running']}")

    print("Pipeline automatically cleaned up")


async def main():
    """Run all examples."""
    print("Unified Context Ingestion Pipeline Examples")
    print("=" * 50)

    try:
        await basic_pipeline_example()
        await config_based_example()
        await manual_setup_example()
        await monitoring_example()
        await context_manager_example()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
