#!/usr/bin/env python3
"""
Claude Chat Import Execution Script

Executes the phased import of Claude chat logs into the Unified Context System
with comprehensive monitoring, error handling, and progress tracking.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Add project root to path
sys.path.insert(0, "/home/opsvi/master_root/apps/project-context")

from src.project_context.ingestion.adapters.chat_adapter import ChatAdapter
from src.project_context.ingestion.base_adapter import AdapterConfig, BatchMode
from src.project_context.ingestion.database import IngestionDatabase
from src.project_context.ingestion.monitoring import IngestionMonitor
from src.project_context.ingestion.pipeline import IngestionPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("claude_chat_import.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class ClaudeChatImporter:
    """Manages the complete Claude chat import process with phased execution."""

    def __init__(self, config_file: str = "config/claude_chat_import_config.yaml"):
        """Initialize the importer with configuration."""
        self.config_file = config_file
        self.config = self._load_config()
        self.monitor = IngestionMonitor()
        self.database = IngestionDatabase()
        self.pipeline = None

        # Statistics tracking
        self.stats = {
            "phase": None,
            "files_processed": 0,
            "messages_processed": 0,
            "errors_encountered": 0,
            "start_time": None,
            "end_time": None,
            "processing_speed": 0.0,
            "problematic_files": [],
        }

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path(self.config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    async def initialize(self) -> None:
        """Initialize the importer components."""
        logger.info("🚀 Initializing Claude Chat Importer")

        # Initialize database
        await self.database.initialize()

        # Create adapter configuration
        adapter_config = self._create_adapter_config()

        # Initialize pipeline
        self.pipeline = IngestionPipeline(database=self.database, monitor=self.monitor)
        await self.pipeline.initialize()

        # Register chat adapter
        chat_adapter = ChatAdapter(adapter_config)
        self.pipeline.register_adapter(chat_adapter)

        logger.info("✅ Initialization complete")

    def _create_adapter_config(self) -> AdapterConfig:
        """Create adapter configuration from loaded config."""
        config = self.config["adapter_config"]
        source_config = self.config["source_config"]

        return AdapterConfig(
            adapter_id=config["adapter_id"],
            source_type=config["source_type"],
            batch_mode=BatchMode.STREAMING
            if config["batch_mode"] == "streaming"
            else BatchMode.BATCH,
            batch_size=config["batch_size"],
            generate_embeddings=config["generate_embeddings"],
            generate_summaries=config["generate_summaries"],
            extract_relationships=config["extract_relationships"],
            skip_duplicates=config["skip_duplicates"],
            source_config=source_config,
        )

    async def execute_full_import(self) -> Dict[str, Any]:
        """Execute the complete phased import process."""
        logger.info("🎯 Starting full Claude chat import process")

        total_start_time = time.time()
        phase_results = {}

        try:
            # Execute each phase in order
            for phase_name, phase_config in self.config["import_phases"].items():
                logger.info(f"📋 Starting {phase_config['name']}")

                result = await self.execute_phase(phase_name, phase_config)
                phase_results[phase_name] = result

                # Brief pause between phases
                await asyncio.sleep(5)

            # Generate final summary
            total_time = time.time() - total_start_time
            summary = self._generate_import_summary(phase_results, total_time)

            logger.info("🎉 Full import process completed successfully")
            return summary

        except Exception as e:
            logger.error(f"❌ Import process failed: {str(e)}")
            raise

    async def execute_phase(
        self, phase_name: str, phase_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single import phase."""
        self.stats["phase"] = phase_name
        self.stats["start_time"] = datetime.now()

        logger.info(f"🔄 Executing {phase_config['name']}")
        logger.info(f"📊 Description: {phase_config['description']}")

        try:
            # Find files matching phase criteria
            target_files = await self._find_files_for_phase(phase_config["criteria"])

            if not target_files:
                logger.warning(f"⚠️  No files found matching criteria for {phase_name}")
                return {"status": "skipped", "reason": "no_files_found"}

            logger.info(f"📁 Found {len(target_files)} files for processing")

            # Configure adapter for this phase
            await self._configure_adapter_for_phase(phase_config)

            # Process files
            results = await self._process_files(target_files, phase_config)

            # Update statistics
            self.stats["end_time"] = datetime.now()
            processing_time = (
                self.stats["end_time"] - self.stats["start_time"]
            ).total_seconds()
            self.stats["processing_speed"] = self.stats["messages_processed"] / max(
                processing_time, 1
            )

            logger.info(f"✅ Phase {phase_name} completed successfully")
            logger.info(
                f"📈 Processed {self.stats['messages_processed']} messages in {processing_time:.1f}s"
            )
            logger.info(
                f"⚡ Processing speed: {self.stats['processing_speed']:.1f} messages/second"
            )

            return {
                "status": "completed",
                "files_processed": self.stats["files_processed"],
                "messages_processed": self.stats["messages_processed"],
                "processing_time_seconds": processing_time,
                "processing_speed": self.stats["processing_speed"],
                "errors": self.stats["errors_encountered"],
                "problematic_files": self.stats["problematic_files"],
            }

        except Exception as e:
            logger.error(f"❌ Phase {phase_name} failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "files_processed": self.stats["files_processed"],
                "messages_processed": self.stats["messages_processed"],
            }

    async def _find_files_for_phase(self, criteria: Dict[str, Any]) -> List[Path]:
        """Find files matching the phase criteria."""
        logger.info("🔍 Scanning for files matching phase criteria")

        base_path = Path(self.config["source_config"]["watch_directories"][0])
        all_files = list(base_path.glob("**/*.jsonl"))

        matching_files = []

        for file_path in all_files:
            try:
                # Check modification time
                file_stat = file_path.stat()
                file_age_days = (
                    datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
                ).days

                modified_within = criteria.get("modified_within_days")
                if modified_within and file_age_days > modified_within:
                    continue

                # Quick check for message count (approximate)
                with open(file_path, "r") as f:
                    line_count = sum(1 for line in f if line.strip())

                min_messages = criteria.get("min_message_count", 0)
                if line_count < min_messages:
                    continue

                # Calculate priority score (simplified)
                priority_score = self._calculate_file_priority(
                    file_path, file_stat, line_count
                )

                min_priority = criteria.get("priority_score_min", 0.0)
                max_priority = criteria.get("priority_score_max", 1.0)

                if not (min_priority <= priority_score <= max_priority):
                    continue

                matching_files.append(file_path)

            except Exception as e:
                logger.warning(f"⚠️  Error evaluating file {file_path}: {str(e)}")
                continue

        # Sort by priority (highest first)
        matching_files.sort(
            key=lambda f: self._calculate_file_priority(f, f.stat(), None), reverse=True
        )

        return matching_files

    def _calculate_file_priority(
        self, file_path: Path, file_stat: Any, line_count: Optional[int] = None
    ) -> float:
        """Calculate priority score for a file (0-1, higher is better)."""
        score = 0.0

        # Recency score (0-0.4)
        file_age_days = (
            datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)
        ).days
        if file_age_days < 7:
            score += 0.4
        elif file_age_days < 30:
            score += 0.3
        elif file_age_days < 90:
            score += 0.2

        # Size score (0-0.3)
        file_size_mb = file_stat.st_size / (1024 * 1024)
        if file_size_mb > 1:
            score += 0.3
        elif file_size_mb > 0.5:
            score += 0.2
        elif file_size_mb > 0.1:
            score += 0.1

        # Content indicators (0-0.3)
        filename = file_path.name.lower()
        if any(
            keyword in filename for keyword in ["hecaton", "project", "master", "phase"]
        ):
            score += 0.2

        if line_count and line_count > 50:
            score += 0.1

        return min(1.0, score)

    async def _configure_adapter_for_phase(self, phase_config: Dict[str, Any]) -> None:
        """Configure the adapter for the specific phase requirements."""
        # This could adjust batch sizes, timeouts, etc. based on phase
        # For now, we use the base configuration
        pass

    async def _process_files(
        self, files: List[Path], phase_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process the list of files for the current phase."""
        logger.info(f"🔄 Processing {len(files)} files")

        processed_files = 0
        processed_messages = 0
        errors = 0

        # Process files in batches
        batch_size = self.config["processing"].get("file_batch_size", 10)

        for i in range(0, len(files), batch_size):
            batch_files = files[i : i + batch_size]
            logger.info(
                f"📦 Processing batch {i//batch_size + 1}/{(len(files)-1)//batch_size + 1}"
            )

            try:
                # Create temporary directory list for this batch
                temp_dirs = []
                for file_path in batch_files:
                    temp_dirs.append(str(file_path.parent))

                # Update adapter configuration for this batch
                adapter = self.pipeline.get_adapter("claude_chat_import")
                adapter.config.source_config["watch_directories"] = list(set(temp_dirs))

                # Process the batch
                batch_results = await self.pipeline.process_batch()

                # Update statistics
                batch_files_processed = len(batch_files)
                batch_messages = batch_results.get("items_processed", 0)

                processed_files += batch_files_processed
                processed_messages += batch_messages

                logger.info(
                    f"✅ Batch completed: {batch_files_processed} files, {batch_messages} messages"
                )

                # Brief pause between batches
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Batch processing failed: {str(e)}")
                errors += 1

                # Add problematic files to stats
                for file_path in batch_files:
                    self.stats["problematic_files"].append(
                        {
                            "file": str(file_path),
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        # Update global stats
        self.stats["files_processed"] = processed_files
        self.stats["messages_processed"] = processed_messages
        self.stats["errors_encountered"] = errors

        return {
            "files_processed": processed_files,
            "messages_processed": processed_messages,
            "errors": errors,
        }

    def _generate_import_summary(
        self, phase_results: Dict[str, Any], total_time: float
    ) -> Dict[str, Any]:
        """Generate comprehensive import summary."""
        total_files = sum(r.get("files_processed", 0) for r in phase_results.values())
        total_messages = sum(
            r.get("messages_processed", 0) for r in phase_results.values()
        )
        total_errors = sum(r.get("errors", 0) for r in phase_results.values())

        summary = {
            "import_completed_at": datetime.now().isoformat(),
            "total_processing_time_seconds": total_time,
            "total_processing_time_hours": total_time / 3600,
            "overall_stats": {
                "total_files_processed": total_files,
                "total_messages_processed": total_messages,
                "total_errors": total_errors,
                "overall_processing_speed": total_messages / max(total_time, 1),
                "success_rate": 1 - (total_errors / max(total_files, 1)),
            },
            "phase_results": phase_results,
            "configuration": {
                "batch_size": self.config["adapter_config"]["batch_size"],
                "parallel_workers": self.config["adapter_config"][
                    "max_concurrent_workers"
                ],
                "embeddings_enabled": self.config["adapter_config"][
                    "generate_embeddings"
                ],
                "relationships_enabled": self.config["adapter_config"][
                    "extract_relationships"
                ],
            },
            "recommendations": self._generate_recommendations(
                phase_results, total_time
            ),
        }

        # Save summary to file
        summary_file = f"claude_chat_import_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"📄 Import summary saved to: {summary_file}")

        return summary

    def _generate_recommendations(
        self, phase_results: Dict[str, Any], total_time: float
    ) -> List[str]:
        """Generate recommendations based on import results."""
        recommendations = []

        # Performance recommendations
        avg_speed = sum(
            r.get("processing_speed", 0) for r in phase_results.values()
        ) / len(phase_results)
        if avg_speed < 10:
            recommendations.append(
                "Consider increasing batch size or parallel workers for better performance"
            )

        # Error rate recommendations
        total_files = sum(r.get("files_processed", 0) for r in phase_results.values())
        total_errors = sum(r.get("errors", 0) for r in phase_results.values())
        if total_errors > 0 and total_files > 0:
            error_rate = total_errors / total_files
            if error_rate > 0.05:
                recommendations.append(
                    "High error rate detected - review problematic files and error logs"
                )

        # Time-based recommendations
        if total_time > 24 * 3600:  # More than 24 hours
            recommendations.append(
                "Long processing time - consider increasing parallelization"
            )

        return recommendations


async def main():
    """Main execution function."""
    logger.info("🎬 Starting Claude Chat Import Process")

    try:
        # Initialize importer
        importer = ClaudeChatImporter()
        await importer.initialize()

        # Execute full import
        summary = await importer.execute_full_import()

        # Print final summary
        logger.info("=" * 60)
        logger.info("📊 IMPORT COMPLETE - FINAL SUMMARY")
        logger.info("=" * 60)
        logger.info(
            f"✅ Total Files Processed: {summary['overall_stats']['total_files_processed']:,}"
        )
        logger.info(
            f"💬 Total Messages Processed: {summary['overall_stats']['total_messages_processed']:,}"
        )
        logger.info(
            f"⏱️  Total Processing Time: {summary['total_processing_time_hours']:.2f} hours"
        )
        logger.info(
            f"⚡ Overall Processing Speed: {summary['overall_stats']['overall_processing_speed']:.1f} messages/second"
        )
        logger.info(
            f"📈 Success Rate: {summary['overall_stats']['success_rate']*100:.1f}%"
        )

        if summary["recommendations"]:
            logger.info("\n🔍 Recommendations:")
            for rec in summary["recommendations"]:
                logger.info(f"  • {rec}")

        logger.info("🎉 Import process completed successfully!")

    except Exception as e:
        logger.error(f"💥 Import process failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
