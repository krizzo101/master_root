#!/usr/bin/env python3
"""
Demonstration of the Unified Context System Ingestion Pipeline.

This script shows how to:
1. Set up and configure the ingestion pipeline
2. Register and configure different adapters
3. Run the pipeline with monitoring
4. Handle errors and manage adapter lifecycle
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from project_context.ingestion import (
    AdapterConfig,
    AdapterRegistry,
    BatchMode,
    ChatAdapter,
    CodeAdapter,
    DataTransformer,
    ErrorAdapter,
    GitAdapter,
    IngestionPipeline,
)
from project_context.ingestion.pipeline import PipelineConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_pipeline_demo():
    """Basic pipeline demonstration."""
    print("=== Basic Pipeline Demo ===")

    # Initialize core components
    registry = AdapterRegistry()
    transformer = DataTransformer()
    pipeline_config = PipelineConfig(
        max_concurrent_adapters=4,
        batch_commit_size=500,
        health_check_interval=30,
        auto_restart_failed_adapters=True,
    )
    pipeline = IngestionPipeline(registry, transformer, pipeline_config)

    # Configure and register chat adapter
    chat_config = ChatAdapter.default_config()
    chat_config.source_config.update(
        {
            "input_format": "jsonl",
            "watch_directories": ["./sample_data/chat"],
            "file_patterns": ["*.jsonl"],
            "include_system_messages": True,
        }
    )
    registry.register_adapter("chat", ChatAdapter, chat_config)

    # Configure and register code adapter
    code_config = CodeAdapter.default_config()
    code_config.source_config.update(
        {
            "scan_directories": ["./src"],
            "include_patterns": ["*.py", "*.js", "*.md"],
            "exclude_patterns": ["__pycache__/**", "*.pyc"],
            "max_file_size_mb": 5,
            "track_changes": True,
        }
    )
    registry.register_adapter("code", CodeAdapter, code_config)

    # Show registry status
    registry_status = registry.get_registry_status()
    print(f"Registry status: {registry_status['total_registered']} adapters registered")
    for adapter_id in registry_status["adapters"]:
        info = registry.get_adapter_info(adapter_id)
        print(f"  - {adapter_id}: {info['source_type']} ({info['batch_mode']})")

    # Start pipeline with managed context
    print("\nStarting pipeline...")
    try:
        async with pipeline.managed_pipeline():
            print("Pipeline started successfully")

            # Monitor for 30 seconds
            for i in range(6):
                await asyncio.sleep(5)

                status = await pipeline.get_status()
                print(f"\nStatus update {i+1}:")
                print(
                    f"  - Items ingested: {status['pipeline']['total_items_ingested']}"
                )
                print(f"  - Items failed: {status['pipeline']['total_items_failed']}")
                print(f"  - Adapters running: {status['pipeline']['adapters_running']}")
                print(
                    f"  - Average throughput: {status['pipeline']['average_throughput']:.1f} items/sec"
                )

                # Show adapter details
                for adapter_id, adapter_status in status["adapters"].items():
                    health = "✓" if adapter_status["is_healthy"] else "✗"
                    processed = adapter_status["metrics"]["total_items_processed"]
                    rate = adapter_status["metrics"]["current_processing_rate"]
                    print(
                        f"    {adapter_id}: {health} {processed} items ({rate:.1f}/sec)"
                    )

        print("\nPipeline stopped successfully")

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise


async def custom_adapter_demo():
    """Demonstrate creating a custom adapter."""
    print("\n=== Custom Adapter Demo ===")

    from datetime import datetime
    from typing import Any, AsyncIterator, Dict

    from project_context.ingestion.base_adapter import BaseAdapter
    from project_context.models.common import ContextItem

    class LogFileAdapter(BaseAdapter):
        """Custom adapter for ingesting application logs."""

        @classmethod
        def default_config(cls):
            return AdapterConfig(
                adapter_id="logs",
                source_type="logs",
                batch_mode=BatchMode.BATCH,
                batch_size=100,
                source_config={
                    "log_directory": "./logs",
                    "log_pattern": "app-*.log",
                    "parse_format": "timestamp level message",
                },
            )

        async def initialize(self):
            self.logger.info("Initializing log file adapter")
            self.log_dir = Path(self.config.source_config["log_directory"])

        async def fetch_items(
            self, since=None, until=None, limit=None
        ) -> AsyncIterator[Dict[str, Any]]:
            pattern = self.config.source_config["log_pattern"]
            count = 0

            if self.log_dir.exists():
                for log_file in self.log_dir.glob(pattern):
                    with open(log_file, "r") as f:
                        for line_num, line in enumerate(f, 1):
                            if limit and count >= limit:
                                return

                            # Simple log parsing
                            parts = line.strip().split(" ", 2)
                            if len(parts) >= 3:
                                yield {
                                    "file": str(log_file),
                                    "line": line_num,
                                    "timestamp": parts[0],
                                    "level": parts[1],
                                    "message": parts[2],
                                }
                                count += 1

        async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
            item = self.transformer.create_base_context_item(
                source_type="logs",
                source_id=f"{raw_item['file']}:{raw_item['line']}",
                raw_data=raw_item,
            )

            item.title = f"{raw_item['level']}: {raw_item['message'][:100]}"
            item.content = raw_item["message"]
            item.file_path = raw_item["file"]
            item.line_start = raw_item["line"]
            item.severity = raw_item["level"].lower()
            item.entity_type = "log_entry"
            item.tags = ["log", raw_item["level"].lower()]

            return await self.transformer.transform_item(item)

        async def cleanup(self):
            self.logger.info("Cleaning up log file adapter")

    # Register and test the custom adapter
    registry = AdapterRegistry()
    transformer = DataTransformer()
    pipeline = IngestionPipeline(registry, transformer)

    # Create sample log directory and files
    sample_log_dir = Path("./sample_logs")
    sample_log_dir.mkdir(exist_ok=True)

    sample_log = sample_log_dir / "app-demo.log"
    with open(sample_log, "w") as f:
        f.write("2025-01-17T10:00:01 INFO Application started\\n")
        f.write("2025-01-17T10:00:02 DEBUG Loading configuration\\n")
        f.write("2025-01-17T10:00:03 ERROR Failed to connect to database\\n")
        f.write("2025-01-17T10:00:04 WARN Retrying database connection\\n")
        f.write("2025-01-17T10:00:05 INFO Database connected successfully\\n")

    # Configure and register custom adapter
    log_config = LogFileAdapter.default_config()
    log_config.source_config["log_directory"] = str(sample_log_dir)
    registry.register_adapter("logs", LogFileAdapter, log_config)

    print("Custom adapter registered, testing...")

    # Test the adapter
    adapter = registry.get_adapter("logs")
    await adapter.initialize()

    items_processed = 0
    async for raw_item in adapter.fetch_items(limit=5):
        context_item = await adapter.transform_item(raw_item)
        print(f"  - {context_item.entity_type}: {context_item.title}")
        items_processed += 1

    print(f"Custom adapter processed {items_processed} items")

    await adapter.cleanup()

    # Clean up sample files
    sample_log.unlink()
    sample_log_dir.rmdir()


async def relationship_detection_demo():
    """Demonstrate relationship detection capabilities."""
    print("\n=== Relationship Detection Demo ===")

    from datetime import datetime, timedelta
    from uuid import uuid4

    from project_context.models.common import ContextItem

    # Create sample context items
    now = datetime.utcnow()

    # Chat message items
    chat_item1 = ContextItem(
        id=uuid4(),
        source_type="chat",
        source_id="msg_1",
        entity_type="message",
        title="How do I fix this bug?",
        content="I'm getting a TypeError in my Python code. Can anyone help?",
        timestamp=now,
        actor_id="user123",
        session_id="conversation_1",
        metrics={"message_type": "question"},
    )

    chat_item2 = ContextItem(
        id=uuid4(),
        source_type="chat",
        source_id="msg_2",
        entity_type="message",
        title="Check your variable types",
        content="That error usually means you're using the wrong type. Check line 45.",
        timestamp=now + timedelta(minutes=2),
        actor_id="helper456",
        session_id="conversation_1",
        metrics={"message_type": "response", "parent_message_id": "msg_1"},
    )

    # Code file item
    code_item = ContextItem(
        id=uuid4(),
        source_type="code",
        source_id="src/main.py",
        entity_type="source_file",
        title="main.py",
        content="def process_data(items):\\n    result = []\\n    for item in items:\\n        result.append(str(item))  # Line 45\\n    return result",
        timestamp=now + timedelta(hours=-1),
        file_path="src/main.py",
        line_start=42,
        line_end=46,
        metrics={"language": "python", "functions": ["process_data"]},
    )

    # Error item
    error_item = ContextItem(
        id=uuid4(),
        source_type="error",
        source_id="error_001",
        entity_type="error",
        title="TypeError in main.py",
        content='TypeError: can only concatenate str (not \\"int\\") to str\\nFile \\"src/main.py\\", line 45, in process_data',
        timestamp=now + timedelta(minutes=-30),
        file_path="src/main.py",
        line_start=45,
        severity="high",
        metrics={"error_type": "TypeError", "stack_trace": "..."},
    )

    # Test relationship detection
    context_items = [chat_item1, chat_item2, code_item, error_item]

    print("Testing relationship detection...")

    # Initialize adapters for relationship detection
    chat_adapter = ChatAdapter(ChatAdapter.default_config())
    code_adapter = CodeAdapter(CodeAdapter.default_config())
    error_adapter = ErrorAdapter(ErrorAdapter.default_config())

    await chat_adapter.initialize()
    await code_adapter.initialize()
    await error_adapter.initialize()

    # Detect relationships for each item
    for i, item in enumerate(context_items):
        context_window = (
            context_items[:i] + context_items[i + 1 :]
        )  # All except current

        if item.source_type == "chat":
            relationships = await chat_adapter.detect_relationships(
                item, context_window
            )
        elif item.source_type == "code":
            relationships = await code_adapter.detect_relationships(
                item, context_window
            )
        elif item.source_type == "error":
            relationships = await error_adapter.detect_relationships(
                item, context_window
            )
        else:
            relationships = []

        print(f"\\n{item.entity_type} '{item.title}' relationships:")
        for rel_type, target_id, confidence in relationships:
            target_item = next((x for x in context_items if x.id == target_id), None)
            target_title = target_item.title if target_item else "Unknown"
            print(f"  - {rel_type} → '{target_title}' (confidence: {confidence:.2f})")

    # Cleanup
    await chat_adapter.cleanup()
    await code_adapter.cleanup()
    await error_adapter.cleanup()


async def monitoring_demo():
    """Demonstrate monitoring and health check capabilities."""
    print("\n=== Monitoring Demo ===")

    registry = AdapterRegistry()
    transformer = DataTransformer()
    pipeline = IngestionPipeline(registry, transformer)

    # Register a simple adapter for monitoring
    config = AdapterConfig(
        adapter_id="test",
        source_type="test",
        batch_mode=BatchMode.STREAMING,
        max_items_per_second=10,  # Low rate for demo
    )

    class MonitoringTestAdapter(BaseAdapter):
        async def initialize(self):
            pass

        async def fetch_items(self, since=None, until=None, limit=None):
            # Generate test items slowly
            for i in range(100):
                await asyncio.sleep(0.1)  # 10 items/second
                yield {"id": f"test_{i}", "content": f"Test item {i}"}

        async def transform_item(self, raw_item):
            item = self.transformer.create_base_context_item(
                "test", raw_item["id"], raw_item
            )
            item.title = f"Test item {raw_item['id']}"
            item.content = raw_item["content"]
            return item

        async def cleanup(self):
            pass

    registry.register_adapter("test", MonitoringTestAdapter, config)

    print("Starting monitoring demo (will run for 20 seconds)...")

    async with pipeline.managed_pipeline(["test"]):
        # Monitor for 20 seconds
        for i in range(4):
            await asyncio.sleep(5)

            status = await pipeline.get_status()

            print(f"\\n--- Monitoring Update {i+1} ---")
            print(f"Pipeline uptime: {status['pipeline']['uptime_seconds']:.1f}s")
            print(f"Total items ingested: {status['pipeline']['total_items_ingested']}")
            print(
                f"Average throughput: {status['pipeline']['average_throughput']:.2f} items/sec"
            )

            # Adapter details
            for adapter_id, adapter_status in status["adapters"].items():
                metrics = adapter_status["metrics"]
                print(f"\\nAdapter '{adapter_id}':")
                print(f"  Status: {adapter_status['status']}")
                print(f"  Healthy: {'Yes' if adapter_status['is_healthy'] else 'No'}")
                print(f"  Items processed: {metrics['total_items_processed']}")
                print(f"  Current rate: {metrics['current_processing_rate']:.2f}/sec")
                print(f"  Average rate: {metrics['average_processing_rate']:.2f}/sec")
                print(f"  Errors: {metrics['total_items_failed']}")

        # Test pause/resume
        print("\\nTesting pause/resume...")
        await pipeline.pause_adapter("test")
        print("Adapter paused")
        await asyncio.sleep(2)

        await pipeline.resume_adapter("test")
        print("Adapter resumed")
        await asyncio.sleep(3)

    print("Monitoring demo completed")


async def main():
    """Run all demonstrations."""
    print("Unified Context System - Ingestion Pipeline Demonstration")
    print("=" * 60)

    try:
        # Run demonstrations
        await basic_pipeline_demo()
        await custom_adapter_demo()
        await relationship_detection_demo()
        await monitoring_demo()

        print("\\n" + "=" * 60)
        print("All demonstrations completed successfully!")

    except KeyboardInterrupt:
        print("\\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
