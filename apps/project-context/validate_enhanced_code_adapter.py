#!/usr/bin/env python3
"""Validation script for enhanced code adapter integration with unified schema.

This script validates that the enhanced code adapter works correctly with the
unified PostgreSQL + TimescaleDB + pgvector schema and produces the expected
data structures for storage and analysis.
"""

import asyncio
import json
import logging
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the enhanced code adapter and related components
try:
    from src.project_context.ingestion.adapters.embedding_generator import (
        EmbeddingGenerator,
    )
    from src.project_context.ingestion.adapters.enhanced_code_adapter import (
        EnhancedCodeAdapter,
    )
    from src.project_context.ingestion.adapters.language_parsers import (
        language_registry,
    )
    from src.project_context.ingestion.base_adapter import AdapterConfig, BatchMode
    from src.project_context.models.common import ContextItem
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please ensure you're running from the project root directory")
    sys.exit(1)


class ValidationResults:
    """Container for validation results."""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.performance_metrics = {}

    def add_test(
        self,
        test_name: str,
        passed: bool,
        error: str = None,
        metrics: Dict[str, Any] = None,
    ):
        """Add a test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            logger.info(f"✓ {test_name}")
        else:
            self.tests_failed += 1
            logger.error(f"✗ {test_name}: {error}")
            self.failures.append({"test": test_name, "error": error})

        if metrics:
            self.performance_metrics[test_name] = metrics

    def print_summary(self):
        """Print validation summary."""
        print(f"\n{'=' * 60}")
        print("ENHANCED CODE ADAPTER VALIDATION RESULTS")
        print(f"{'=' * 60}")
        print(f"Tests Run:    {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(
            f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%"
            if self.tests_run > 0
            else "N/A"
        )

        if self.failures:
            print(f"\nFAILURES:")
            for failure in self.failures:
                print(f"  - {failure['test']}: {failure['error']}")

        if self.performance_metrics:
            print(f"\nPERFORMANCE METRICS:")
            for test_name, metrics in self.performance_metrics.items():
                print(f"  {test_name}:")
                for metric, value in metrics.items():
                    print(f"    {metric}: {value}")


def create_test_files(temp_dir: Path) -> Dict[str, Path]:
    """Create comprehensive test files for validation."""
    test_files = {}

    # Python file with comprehensive features
    python_file = temp_dir / "sample_python.py"
    python_file.write_text(
        """
import asyncio
import json
from typing import List, Optional, Dict, Any

class DataProcessor:
    \"\"\"Process data with async methods.\"\"\"

    def __init__(self, config: dict):
        self.config = config
        self.processed_count = 0

    async def process_data(self, data: List[str]) -> Optional[List[str]]:
        \"\"\"Process a list of data items.\"\"\"
        if not data:
            return None

        results = []
        for item in data:
            processed = await self._process_item(item)
            if processed:
                results.append(processed)

        self.processed_count += len(results)
        return results

    async def _process_item(self, item: str) -> Optional[str]:
        \"\"\"Process single item.\"\"\"
        try:
            await asyncio.sleep(0.01)
            return item.upper()
        except Exception as e:
            print(f"Error: {e}")
            return None

def main():
    processor = DataProcessor({"timeout": 30})
    return asyncio.run(processor.process_data(["hello", "world"]))
"""
    )
    test_files["python"] = python_file

    # JavaScript file
    js_file = temp_dir / "sample_javascript.js"
    js_file.write_text(
        """
const express = require('express');

class ApiServer {
    constructor(port = 3000) {
        this.app = express();
        this.port = port;
    }

    setupRoutes() {
        this.app.get('/health', async (req, res) => {
            res.json({ status: 'ok', timestamp: new Date() });
        });
    }

    async start() {
        return new Promise(resolve => {
            this.server = this.app.listen(this.port, resolve);
        });
    }
}

const createServer = (config) => new ApiServer(config.port);

module.exports = { ApiServer, createServer };
"""
    )
    test_files["javascript"] = js_file

    return test_files


async def run_validation():
    """Run comprehensive validation of the enhanced code adapter."""
    results = ValidationResults()

    logger.info("Starting Enhanced Code Adapter Validation")
    logger.info("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_files = create_test_files(temp_path)

        # Test 1: Adapter Initialization
        try:
            config = AdapterConfig(
                adapter_id="validation_test",
                source_type="code",
                batch_mode=BatchMode.BATCH,
                batch_size=10,
                generate_embeddings=True,
                source_config={
                    "scan_directories": [str(temp_path)],
                    "include_patterns": ["*.py", "*.js"],
                    "enable_advanced_analysis": True,
                    "parallel_processing": False,
                    "enable_file_watching": False,
                },
            )

            adapter = EnhancedCodeAdapter(config)
            await adapter.initialize()
            results.add_test("Adapter Initialization", True)

        except Exception as e:
            results.add_test("Adapter Initialization", False, str(e))
            return results

        # Test 2: File Discovery
        try:
            items = []
            async for item in adapter.fetch_items(limit=5):
                items.append(item)

            success = len(items) >= len(test_files)
            results.add_test(
                "File Discovery",
                success,
                None if success else f"Expected {len(test_files)}, found {len(items)}",
            )

        except Exception as e:
            results.add_test("File Discovery", False, str(e))

        # Test 3: Symbol Extraction
        try:
            with open(test_files["python"]) as f:
                content = f.read()

            symbols = adapter.extract_symbols(
                content, str(test_files["python"]), "python"
            )

            success = (
                len(symbols.get("functions", [])) >= 2
                and len(symbols.get("classes", [])) >= 1
                and "complexity_metrics" in symbols
            )

            results.add_test(
                "Symbol Extraction",
                success,
                None if success else "Insufficient symbols extracted",
            )

        except Exception as e:
            results.add_test("Symbol Extraction", False, str(e))

        # Test 4: Item Transformation
        try:
            raw_item = {
                "file_path": str(test_files["python"]),
                "content": open(test_files["python"]).read(),
                "encoding": "utf-8",
                "file_stats": {"size": 1000, "modified": datetime.now()},
                "title": "sample.py",
            }

            context_item = await adapter.transform_item(raw_item)

            success = (
                isinstance(context_item, ContextItem)
                and context_item.source_type == "code"
                and context_item.metrics is not None
            )

            results.add_test(
                "Item Transformation",
                success,
                None if success else "Invalid ContextItem structure",
            )

        except Exception as e:
            results.add_test("Item Transformation", False, str(e))

        # Test 5: Language Detection
        try:
            python_detected = adapter._detect_language(
                str(test_files["python"]), "def test(): pass"
            )
            js_detected = adapter._detect_language(
                str(test_files["javascript"]), "function test() {}"
            )

            success = python_detected == "python" and js_detected == "javascript"
            results.add_test(
                "Language Detection",
                success,
                None if success else f"Python: {python_detected}, JS: {js_detected}",
            )

        except Exception as e:
            results.add_test("Language Detection", False, str(e))

        # Test 6: Embedding Generation
        try:
            generator = EmbeddingGenerator({"cache_embeddings": False})
            embedding = await generator.generate_embedding("def hello(): pass", "code")

            success = (
                embedding is not None
                and isinstance(embedding, list)
                and len(embedding) > 0
            )

            results.add_test(
                "Embedding Generation",
                success,
                None if success else "No embedding generated",
            )

        except Exception as e:
            results.add_test("Embedding Generation", False, str(e))

        # Cleanup
        try:
            await adapter.cleanup()
            results.add_test("Cleanup", True)
        except Exception as e:
            results.add_test("Cleanup", False, str(e))

    return results


def main():
    """Main validation entry point."""
    try:
        results = asyncio.run(run_validation())
        results.print_summary()

        exit_code = 0 if results.tests_failed == 0 else 1

        if exit_code == 0:
            logger.info("\n🎉 Enhanced Code Adapter validation passed!")
        else:
            logger.error(f"\n❌ {results.tests_failed} test(s) failed.")

        return exit_code

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
