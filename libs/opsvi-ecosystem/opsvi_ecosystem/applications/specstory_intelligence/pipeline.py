"""
SpecStory Intelligence Pipeline
Main coordinator for real-time atomic decomposition and intelligence extraction
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import signal
import traceback
from typing import Dict, List, Optional, Set

# from .file_monitor import SpecStoryFileWatcher as SpecStoryFileMonitor
from .atomic_parser import AtomicSpecStoryParser
from .database_storage import SpecStoryDatabaseStorage


@dataclass
class ProcessingMetrics:
    """Tracks processing performance metrics"""

    files_processed: int = 0
    components_extracted: int = 0
    relationships_discovered: int = 0
    processing_time_total: float = 0.0
    errors_encountered: int = 0
    last_processed_file: str = ""
    last_processing_time: Optional[datetime] = None

    def update_file_processed(
        self,
        file_path: str,
        components: int,
        relationships: int,
        processing_time: float,
    ):
        """Update metrics after processing a file"""
        self.files_processed += 1
        self.components_extracted += components
        self.relationships_discovered += relationships
        self.processing_time_total += processing_time
        self.last_processed_file = file_path
        self.last_processing_time = datetime.utcnow()

    def update_error(self):
        """Record an error"""
        self.errors_encountered += 1

    def get_summary(self) -> Dict:
        """Get processing summary"""
        avg_processing_time = (
            self.processing_time_total / self.files_processed
            if self.files_processed > 0
            else 0
        )

        return {
            "files_processed": self.files_processed,
            "components_extracted": self.components_extracted,
            "relationships_discovered": self.relationships_discovered,
            "total_processing_time": self.processing_time_total,
            "average_processing_time": avg_processing_time,
            "errors_encountered": self.errors_encountered,
            "last_processed_file": self.last_processed_file,
            "last_processing_time": (
                self.last_processing_time.isoformat()
                if self.last_processing_time
                else None
            ),
            "success_rate": (
                (self.files_processed - self.errors_encountered) / self.files_processed
                if self.files_processed > 0
                else 0
            ),
        }


class SpecStoryIntelligencePipeline:
    """Main pipeline coordinator for real-time SpecStory intelligence"""

    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()

        # Initialize components
        # self.file_monitor = SpecStoryFileMonitor(
        #     watch_directory=self.config["watch_directory"],
        #     file_pattern=self.config["file_pattern"],
        # )
        self.parser = AtomicSpecStoryParser()
        self.storage = SpecStoryDatabaseStorage(
            collection_prefix=self.config["collection_prefix"]
        )

        # Processing state
        self.metrics = ProcessingMetrics()
        self.processing_queue = asyncio.Queue()
        self.processed_files: Set[str] = set()
        self.is_running = False
        self.workers: List[asyncio.Task] = []

        # Logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Advanced Analytics (optional)
        self.advanced_analytics = None
        if self.config.get("enable_advanced_analytics"):
            self._initialize_advanced_analytics()

        # Graceful shutdown
        self._setup_signal_handlers()

    def _default_config(self) -> Dict:
        """Default pipeline configuration"""
        return {
            "watch_directory": ".specstory/history",
            "file_pattern": "*.md",
            "collection_prefix": "specstory",
            "max_workers": 3,
            "batch_size": 5,
            "processing_delay": 1.0,  # seconds
            "enable_metrics": True,
            "enable_real_time_analysis": True,
            "enable_pattern_detection": True,
            "log_level": "INFO",
            # Advanced Analytics Configuration
            "enable_advanced_analytics": True,
            "enable_predictive_intelligence": True,
            "enable_continuous_learning": True,
            "enable_context_compression": True,
            "enable_meta_thinking": True,
            "enable_ai_self_assessment": True,
        }

    def _setup_logging(self):
        """Configure structured logging for pipeline"""
        log_level = getattr(logging, self.config["log_level"], logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("specstory_intelligence.log"),
            ],
        )

    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""

        def signal_handler(signum, frame):
            self.logger.info(
                f"🛑 Received signal {signum}, initiating graceful shutdown..."
            )
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _initialize_advanced_analytics(self):
        """Initialize advanced analytics engines"""
        try:
            from .analytics import (
                AISelfAssessment,
                ContextCompressionEngine,
                ContinuousLearningEngine,
                ConversationAnalyzer,
                MetaThinkingEngine,
                PredictiveIntelligenceEngine,
                SessionConsolidator,
            )

            self.advanced_analytics = {}

            # Initialize engines based on configuration
            if self.config.get("enable_continuous_learning"):
                learning_engine = ContinuousLearningEngine()
                self.advanced_analytics["continuous_learning"] = learning_engine

                if self.config.get("enable_predictive_intelligence"):
                    self.advanced_analytics[
                        "predictive"
                    ] = PredictiveIntelligenceEngine(learning_engine)

            if self.config.get("enable_context_compression"):
                self.advanced_analytics[
                    "context_compression"
                ] = ContextCompressionEngine()

            if self.config.get("enable_meta_thinking"):
                self.advanced_analytics["meta_thinking"] = MetaThinkingEngine()

            if self.config.get("enable_ai_self_assessment"):
                self.advanced_analytics["self_assessment"] = AISelfAssessment()

            # Always include conversation analyzer and session consolidator
            self.advanced_analytics["conversation_analyzer"] = ConversationAnalyzer()
            self.advanced_analytics["session_consolidator"] = SessionConsolidator()

            self.logger.info(
                f"🧠 Initialized {len(self.advanced_analytics)} advanced analytics engines"
            )

        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import advanced analytics: {e}")
            self.advanced_analytics = None
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize advanced analytics: {e}")
            self.advanced_analytics = None

    async def initialize(self) -> bool:
        """Initialize the complete pipeline"""
        try:
            self.logger.info("🚀 Initializing SpecStory Intelligence Pipeline...")

            # Initialize database
            db_success = await self.storage.initialize_database()
            if not db_success:
                self.logger.error("❌ Failed to initialize database")
                return False

            # Initialize file monitor
            # monitor_success = await self.file_monitor.initialize()
            # if not monitor_success:
            #     self.logger.error("❌ Failed to initialize file monitor")
            #     return False

            # Validate watch directory
            watch_path = Path(self.config["watch_directory"])
            if not watch_path.exists():
                self.logger.warning(
                    f"📁 Watch directory {watch_path} does not exist, creating..."
                )
                watch_path.mkdir(parents=True, exist_ok=True)

            self.logger.info("✅ Pipeline initialization complete")
            return True

        except Exception as e:
            self.logger.error(f"❌ Pipeline initialization failed: {e}")
            self.logger.error(traceback.format_exc())
            return False

    async def start(self) -> bool:
        """Start the complete real-time intelligence pipeline"""
        if self.is_running:
            self.logger.warning("⚠️ Pipeline is already running")
            return False

        try:
            # Initialize if not already done
            if not await self.initialize():
                return False

            self.is_running = True
            self.logger.info("🎯 Starting SpecStory Intelligence Pipeline...")

            # Start file monitoring
            # monitor_task = asyncio.create_task(self._run_file_monitor())

            # Start processing workers
            worker_tasks = []
            for i in range(self.config["max_workers"]):
                worker = asyncio.create_task(self._processing_worker(f"worker-{i+1}"))
                worker_tasks.append(worker)

            # Start metrics reporting
            if self.config["enable_metrics"]:
                metrics_task = asyncio.create_task(self._metrics_reporter())
                worker_tasks.append(metrics_task)

            # Start pattern analysis
            if self.config["enable_pattern_detection"]:
                pattern_task = asyncio.create_task(self._pattern_analyzer())
                worker_tasks.append(pattern_task)

            self.workers = [monitor_task] + worker_tasks

            self.logger.info(f"✅ Pipeline started with {len(self.workers)} tasks")

            # Wait for all tasks
            await asyncio.gather(*self.workers, return_exceptions=True)

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to start pipeline: {e}")
            self.logger.error(traceback.format_exc())
            await self.stop()
            return False

    async def stop(self):
        """Gracefully stop the pipeline"""
        if not self.is_running:
            return

        self.logger.info("🛑 Stopping SpecStory Intelligence Pipeline...")
        self.is_running = False

        # Cancel all worker tasks
        for worker in self.workers:
            if not worker.done():
                worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Stop file monitor
        # await self.file_monitor.stop()

        # Print final metrics
        final_metrics = self.metrics.get_summary()
        self.logger.info(f"📊 Final metrics: {final_metrics}")

        self.logger.info("✅ Pipeline stopped gracefully")

    async def _run_file_monitor(self):
        """Run the file monitoring loop"""
        self.logger.info("👁️ Starting file monitor...")

        async for file_event in self.file_monitor.watch_files():
            if not self.is_running:
                break

            file_path = file_event["file_path"]

            # Skip already processed files
            if file_path in self.processed_files:
                continue

            # Add to processing queue
            await self.processing_queue.put(file_event)
            self.logger.info(f"📝 Queued file for processing: {file_path}")

    async def _processing_worker(self, worker_name: str):
        """Process files from the queue"""
        self.logger.info(f"⚡ Starting processing worker: {worker_name}")

        while self.is_running:
            try:
                # Get file from queue with timeout
                file_event = await asyncio.wait_for(
                    self.processing_queue.get(), timeout=5.0
                )

                # Process the file
                await self._process_file(file_event, worker_name)

                # Mark task as done
                self.processing_queue.task_done()

                # Brief pause between files
                await asyncio.sleep(self.config["processing_delay"])

            except asyncio.TimeoutError:
                # No files to process, continue loop
                continue
            except Exception as e:
                self.logger.error(f"❌ Worker {worker_name} error: {e}")
                self.metrics.update_error()
                await asyncio.sleep(5.0)  # Longer pause on error

    async def _process_file(self, file_event: Dict, worker_name: str):
        """Process a single SpecStory file"""
        file_path = file_event["file_path"]

        try:
            start_time = datetime.utcnow()
            self.logger.info(f"🔄 {worker_name} processing: {file_path}")

            # Parse file into atomic components
            components, relationships = await self.parser.parse_file(file_path)

            if not components:
                self.logger.warning(f"⚠️ No components extracted from {file_path}")
                return

            # Store in database
            storage_result = await self.storage.store_parsed_file(
                file_path=file_path,
                components=components,
                relationships=relationships,
                metadata={
                    "processed_by": worker_name,
                    "file_event": file_event,
                    "pipeline_version": "1.0.0",
                },
            )

            if not storage_result.get("success"):
                raise Exception(f"Storage failed: {storage_result.get('error')}")

            # Update metrics
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            self.metrics.update_file_processed(
                file_path=file_path,
                components=len(components),
                relationships=len(relationships),
                processing_time=processing_time,
            )

            # Mark as processed
            self.processed_files.add(file_path)

            self.logger.info(
                f"✅ {worker_name} completed {file_path}: {len(components)} components, {len(relationships)} relationships in {processing_time:.2f}s"
            )

            # Real-time analysis if enabled
            if self.config["enable_real_time_analysis"]:
                await self._analyze_session_real_time(
                    components[0].session_id if components else ""
                )

        except Exception as e:
            self.logger.error(f"❌ Failed to process {file_path}: {e}")
            self.logger.error(traceback.format_exc())
            self.metrics.update_error()

    async def _analyze_session_real_time(self, session_id: str):
        """Perform real-time analysis of session data"""
        if not session_id:
            return

        try:
            # Get session overview
            session_overview = await self.storage.get_session_overview(session_id)

            # Extract insights
            insights = session_overview.get("insights", {})

            # Log significant patterns
            if insights.get("complexity_assessment") == "high":
                self.logger.info(f"🔍 High complexity session detected: {session_id}")

            primary_activities = insights.get("primary_activities", [])
            if len(primary_activities) > 2:
                self.logger.info(
                    f"🎯 Multi-activity session: {session_id} - {primary_activities}"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Real-time analysis failed for session {session_id}: {e}"
            )

    async def _metrics_reporter(self):
        """Periodically report processing metrics"""
        self.logger.info("📊 Starting metrics reporter...")

        while self.is_running:
            try:
                await asyncio.sleep(60)  # Report every minute

                if self.metrics.files_processed > 0:
                    summary = self.metrics.get_summary()
                    self.logger.info(
                        f"📈 Metrics: {summary['files_processed']} files, {summary['components_extracted']} components, {summary['success_rate']:.2%} success rate"
                    )

            except Exception as e:
                self.logger.error(f"❌ Metrics reporter error: {e}")

    async def _pattern_analyzer(self):
        """Analyze patterns across processed files"""
        self.logger.info("🔍 Starting pattern analyzer...")

        while self.is_running:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes

                if (
                    self.metrics.files_processed >= 5
                ):  # Only analyze after sufficient data
                    await self._detect_global_patterns()

            except Exception as e:
                self.logger.error(f"❌ Pattern analyzer error: {e}")

    async def _detect_global_patterns(self):
        """Detect patterns across all processed sessions"""
        try:
            # Query recent components for pattern analysis
            recent_components = await self.storage.query_components(limit=1000)

            if len(recent_components) < 10:
                return

            # Analyze tool usage patterns
            tool_calls = [
                comp
                for comp in recent_components
                if comp.get("component_type") == "tool_call"
            ]

            if tool_calls:
                tool_usage = {}
                for call in tool_calls:
                    tool_name = (
                        call.get("content", {})
                        .get("processed_content", {})
                        .get("tool_name", "unknown")
                    )
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

                # Report most used tools
                most_used = (
                    max(tool_usage.items(), key=lambda x: x[1]) if tool_usage else None
                )
                if most_used:
                    self.logger.info(
                        f"🛠️ Pattern detected - Most used tool: {most_used[0]} ({most_used[1]} times)"
                    )

            # Analyze session complexity trends
            sessions_by_complexity = {"low": 0, "medium": 0, "high": 0}

            # This would be expanded with more sophisticated pattern detection
            self.logger.info(
                f"🔍 Pattern analysis complete: {len(recent_components)} components analyzed"
            )

        except Exception as e:
            self.logger.error(f"❌ Global pattern detection failed: {e}")

    async def process_file_manually(self, file_path: str) -> Dict:
        """Manually process a single file (for testing/debugging)"""
        file_event = {
            "file_path": file_path,
            "event_type": "manual",
            "timestamp": datetime.utcnow().isoformat(),
        }

        await self._process_file(file_event, "manual")
        return self.metrics.get_summary()

    def get_status(self) -> Dict:
        """Get current pipeline status"""
        return {
            "is_running": self.is_running,
            "workers_active": len([w for w in self.workers if not w.done()]),
            "queue_size": self.processing_queue.qsize(),
            "files_processed": len(self.processed_files),
            "metrics": self.metrics.get_summary(),
            "config": self.config,
        }


# Main entry point for standalone execution
async def main():
    """Run the SpecStory Intelligence Pipeline"""

    # Custom configuration
    config = {
        "watch_directory": ".specstory/history",
        "file_pattern": "*.md",
        "collection_prefix": "specstory",
        "max_workers": 2,
        "enable_metrics": True,
        "enable_real_time_analysis": True,
        "enable_pattern_detection": True,
        "log_level": "INFO",
    }

    # Create and run pipeline
    pipeline = SpecStoryIntelligencePipeline(config)

    try:
        # Start the pipeline
        success = await pipeline.start()

        if success:
            print("🚀 SpecStory Intelligence Pipeline is running!")
            print("Press Ctrl+C to stop gracefully...")

            # Keep running until interrupted
            while pipeline.is_running:
                await asyncio.sleep(1)
        else:
            print("❌ Failed to start pipeline")

    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested...")

    finally:
        await pipeline.stop()
        print("✅ Pipeline stopped")


if __name__ == "__main__":
    asyncio.run(main())
