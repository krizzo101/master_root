#!/usr/bin/env python3
"""
Orchestrator Manager - Handles automatic Celery worker startup and database initialization.

Based on Celery documentation research:
- Uses `celery multi` for proper worker daemonization
- Implements `app.control.ping()` for worker status checking  
- Provides non-blocking worker startup via subprocess
- Ensures proper database connection initialization
- Follows production-ready patterns from Celery docs
"""

import sys
import logging
import subprocess
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from .celery_app import app
from .core import Orchestrator
from .workflow import WorkflowManager
from .database import ArangoDBClient
from .plugins.types import PluginConfig

logger = logging.getLogger(__name__)


class OrchestratorManager:
    """
    Manages the complete orchestrator lifecycle including:
    - Automatic Celery worker startup/management
    - Database connection initialization
    - Orchestrator configuration and execution
    - Health monitoring and status reporting
    """

    def __init__(
        self,
        plugin_dir: str,
        app_name: str = "asea_orchestrator.celery_app",
        worker_concurrency: int = 2,
        log_level: str = "INFO",
        auto_start_workers: bool = True,
        db_config: Optional[Dict[str, Any]] = None,
    ):
        self.plugin_dir = plugin_dir
        self.app_name = app_name
        self.worker_concurrency = worker_concurrency
        self.log_level = log_level
        self.auto_start_workers = auto_start_workers

        # Database configuration
        self.db_config = db_config or {
            "host": "http://127.0.0.1:8529",
            "database": "asea_prod_db",
            "username": "root",
            "password": "arango_dev_password",
        }

        # Components
        self.workflow_manager = self._create_default_workflow_manager()
        self.orchestrator: Optional[Orchestrator] = None
        self.db_client: Optional[ArangoDBClient] = None

        # Worker management
        self.worker_pids: List[int] = []
        self.worker_names: List[str] = []

        # Status tracking
        self._initialized = False
        self._workers_started = False
        self._db_connected = False

    def _create_default_workflow_manager(self) -> WorkflowManager:
        """
        Create WorkflowManager with default workflow definitions.
        """
        default_workflows = {
            "simple_test": {
                "steps": [
                    {
                        "plugin_name": "logger",
                        "parameters": {"message": "Test workflow step"},
                        "inputs": {},
                        "outputs": {"result": "log_result"},
                    }
                ]
            },
            "cognitive_enhancement": {
                "steps": [
                    {
                        "plugin_name": "budget_manager",
                        "parameters": {"operation": "estimate_cost"},
                        "inputs": {},
                        "outputs": {"cost_estimate": "budget_analysis"},
                    },
                    {
                        "plugin_name": "workflow_intelligence",
                        "parameters": {"analyze_workflow": True},
                        "inputs": {"budget_data": "budget_analysis"},
                        "outputs": {"optimization": "workflow_optimization"},
                    },
                    {
                        "plugin_name": "logger",
                        "parameters": {"message": "Cognitive enhancement complete"},
                        "inputs": {
                            "budget": "budget_analysis",
                            "optimization": "workflow_optimization",
                        },
                        "outputs": {"result": "final_result"},
                    },
                ]
            },
        }
        return WorkflowManager(default_workflows)

    async def initialize(self) -> bool:
        """
        Initialize the complete orchestrator system.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("🚀 Initializing ASEA Orchestrator Manager...")

            # Step 1: Check and start workers if needed
            if self.auto_start_workers:
                workers_ready = await self._ensure_workers_running()
                if not workers_ready:
                    logger.error("❌ Failed to ensure workers are running")
                    return False

            # Step 2: Initialize database connection
            db_ready = await self._initialize_database()
            if not db_ready:
                logger.warning(
                    "⚠️ Database initialization failed, continuing without persistence"
                )

            # Step 3: Create orchestrator with database client
            self.orchestrator = Orchestrator(self.plugin_dir, self.workflow_manager)
            if self.db_client and self._db_connected:
                self.orchestrator.db_client = self.db_client
                self.orchestrator._db_connected = True
                logger.info("✅ Orchestrator configured with database persistence")
            else:
                logger.info("✅ Orchestrator configured without database persistence")

            self._initialized = True
            logger.info("🎉 ASEA Orchestrator Manager initialization complete!")

            # Status report
            await self._print_status_report()

            return True

        except Exception as e:
            logger.error(f"❌ Orchestrator Manager initialization failed: {e}")
            return False

    async def _ensure_workers_running(self) -> bool:
        """
        Ensure Celery workers are running, start them if needed.

        Returns:
            bool: True if workers are available, False otherwise
        """
        try:
            logger.info("🔍 Checking Celery worker status...")

            # Check if workers are already running using app.control.ping()
            try:
                # Use timeout to avoid hanging
                ping_result = app.control.ping(timeout=2.0)
                if ping_result:
                    active_workers = [list(worker.keys())[0] for worker in ping_result]
                    logger.info(
                        f"✅ Found {len(active_workers)} active workers: {active_workers}"
                    )
                    self._workers_started = True
                    return True
                else:
                    logger.info("📭 No active workers found")

            except Exception as ping_error:
                logger.info(
                    f"📭 Worker ping failed (expected if no workers): {ping_error}"
                )

            # Start workers using celery multi (production pattern from docs)
            logger.info(f"🔧 Starting {self.worker_concurrency} Celery workers...")

            success = await self._start_workers_via_multi()
            if success:
                # Wait a moment for workers to initialize
                await asyncio.sleep(3)

                # Verify workers started successfully
                verification_result = await self._verify_workers_started()
                if verification_result:
                    self._workers_started = True
                    logger.info("✅ Workers started and verified successfully")
                    return True
                else:
                    logger.error("❌ Worker verification failed")
                    return False
            else:
                logger.error("❌ Failed to start workers")
                return False

        except Exception as e:
            logger.error(f"❌ Error ensuring workers running: {e}")
            return False

    async def _start_workers_via_multi(self) -> bool:
        """
        Start workers using 'celery multi' command (recommended production pattern).

        Returns:
            bool: True if command executed successfully, False otherwise
        """
        try:
            # Get the current working directory (should be asea_orchestrator)
            cwd = Path(__file__).parent.parent.parent  # Go up to asea_orchestrator root

            # Create log and pid directories
            log_dir = cwd / "logs"
            pid_dir = cwd / "pids"
            log_dir.mkdir(exist_ok=True)
            pid_dir.mkdir(exist_ok=True)

            # Build celery multi command based on documentation patterns
            cmd = [
                "celery",
                "-A",
                self.app_name,
                "multi",
                "start",
                str(self.worker_concurrency),
                "-l",
                self.log_level,
                "-c",
                "1",  # 1 process per worker for better control
                f"--pidfile={pid_dir}/%n.pid",
                f"--logfile={log_dir}/%n%I.log",
            ]

            logger.info(f"🔧 Executing: {' '.join(cmd)}")
            logger.info(f"📁 Working directory: {cwd}")

            # Execute command
            result = subprocess.run(
                cmd, cwd=str(cwd), capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                logger.info("✅ Celery multi start command completed successfully")
                if result.stdout:
                    logger.info(f"📤 stdout: {result.stdout}")
                return True
            else:
                logger.error(
                    f"❌ Celery multi start failed with return code {result.returncode}"
                )
                logger.error(f"📥 stderr: {result.stderr}")
                if result.stdout:
                    logger.error(f"📤 stdout: {result.stdout}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("❌ Celery multi start command timed out")
            return False
        except FileNotFoundError:
            logger.error("❌ 'celery' command not found. Is Celery installed?")
            return False
        except Exception as e:
            logger.error(f"❌ Error starting workers via multi: {e}")
            return False

    async def _verify_workers_started(self) -> bool:
        """
        Verify that workers started successfully using app.control.ping().

        Returns:
            bool: True if workers respond to ping, False otherwise
        """
        try:
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    logger.info(
                        f"🔍 Verifying workers (attempt {attempt + 1}/{max_attempts})..."
                    )

                    ping_result = app.control.ping(timeout=2.0)
                    if ping_result:
                        active_workers = [
                            list(worker.keys())[0] for worker in ping_result
                        ]
                        logger.info(f"✅ Workers responding: {active_workers}")

                        if len(active_workers) >= self.worker_concurrency:
                            logger.info(
                                f"🎉 All {self.worker_concurrency} workers verified!"
                            )
                            return True
                        else:
                            logger.info(
                                f"⏳ Only {len(active_workers)}/{self.worker_concurrency} workers responding, waiting..."
                            )
                    else:
                        logger.info("⏳ No worker responses yet, waiting...")

                except Exception as ping_error:
                    logger.info(f"⏳ Ping attempt {attempt + 1} failed: {ping_error}")

                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)

            logger.error("❌ Worker verification failed after all attempts")
            return False

        except Exception as e:
            logger.error(f"❌ Error verifying workers: {e}")
            return False

    async def _initialize_database(self) -> bool:
        """
        Initialize database connection.

        Returns:
            bool: True if database connected successfully, False otherwise
        """
        try:
            logger.info("📡 Initializing database connection...")

            self.db_client = ArangoDBClient(**self.db_config)
            connected = await self.db_client.connect()

            if connected:
                self._db_connected = True
                logger.info("✅ Database connection established")
                return True
            else:
                logger.warning("⚠️ Database connection failed")
                return False

        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            return False

    async def _print_status_report(self):
        """Print comprehensive status report."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 ASEA ORCHESTRATOR MANAGER STATUS REPORT")
        logger.info("=" * 60)

        # Worker status
        try:
            ping_result = app.control.ping(timeout=2.0)
            if ping_result:
                active_workers = [list(worker.keys())[0] for worker in ping_result]
                logger.info(f"🔧 Workers: {len(active_workers)} active")
                for worker in active_workers:
                    logger.info(f"   ✅ {worker}")
            else:
                logger.info("🔧 Workers: None active")
        except Exception:
            logger.info("🔧 Workers: Status check failed")

        # Database status
        db_status = "✅ Connected" if self._db_connected else "❌ Disconnected"
        logger.info(f"📊 Database: {db_status}")

        # Orchestrator status
        orch_status = "✅ Ready" if self._initialized else "❌ Not initialized"
        logger.info(f"🎛️ Orchestrator: {orch_status}")

        # Plugin status
        if self.orchestrator:
            plugin_count = len(self.orchestrator.plugin_manager.plugins)
            logger.info(f"🔌 Plugins: {plugin_count} loaded")
        else:
            logger.info("🔌 Plugins: Not loaded")

        logger.info("=" * 60)

    async def run_workflow(
        self,
        workflow_name: str,
        plugin_configs: Dict[str, PluginConfig],
        initial_state: Dict[str, Any] = None,
        run_id: str = None,
    ) -> Dict[str, Any]:
        """
        Run a workflow using the orchestrator.

        Args:
            workflow_name: Name of workflow to run
            plugin_configs: Plugin configurations
            initial_state: Initial workflow state
            run_id: Optional run ID for resuming

        Returns:
            Dict containing workflow results
        """
        if not self._initialized:
            raise RuntimeError(
                "OrchestratorManager not initialized. Call initialize() first."
            )

        if not self.orchestrator:
            raise RuntimeError("Orchestrator not available")

        # Configure plugins
        self.orchestrator.temp_configure_plugins(plugin_configs)

        # Run workflow
        return await self.orchestrator.run_workflow(
            workflow_name=workflow_name,
            initial_state=initial_state or {},
            run_id=run_id,
        )

    async def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status information.

        Returns:
            Dict containing status information
        """
        status = {
            "initialized": self._initialized,
            "workers_started": self._workers_started,
            "database_connected": self._db_connected,
            "active_workers": [],
            "plugin_count": 0,
            "workflows_available": [],
        }

        # Check active workers
        try:
            ping_result = app.control.ping(timeout=2.0)
            if ping_result:
                status["active_workers"] = [
                    list(worker.keys())[0] for worker in ping_result
                ]
        except Exception:
            pass

        # Plugin and workflow info
        if self.orchestrator:
            status["plugin_count"] = len(self.orchestrator.plugin_manager.plugins)
            status["workflows_available"] = list(self.workflow_manager.workflows.keys())

        return status

    async def shutdown(self):
        """Graceful shutdown of the orchestrator manager."""
        logger.info("🛑 Shutting down ASEA Orchestrator Manager...")

        # Disconnect database
        if self.db_client:
            await self.db_client.disconnect()
            logger.info("📊 Database disconnected")

        # Note: We don't stop workers automatically as they may be used by other processes
        # Use `celery multi stop` manually if needed

        logger.info("✅ ASEA Orchestrator Manager shutdown complete")


# Convenience function for easy usage
async def create_orchestrator_manager(
    plugin_dir: str, auto_start_workers: bool = True, **kwargs
) -> OrchestratorManager:
    """
    Create and initialize an OrchestratorManager.

    Args:
        plugin_dir: Directory containing plugins
        auto_start_workers: Whether to auto-start Celery workers
        **kwargs: Additional configuration options

    Returns:
        Initialized OrchestratorManager instance
    """
    manager = OrchestratorManager(
        plugin_dir=plugin_dir, auto_start_workers=auto_start_workers, **kwargs
    )

    success = await manager.initialize()
    if not success:
        raise RuntimeError("Failed to initialize OrchestratorManager")

    return manager


if __name__ == "__main__":
    """Demo usage of OrchestratorManager"""
    import sys
    from pathlib import Path

    # Add src to path for imports
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

    async def demo():
        plugin_dir = str(Path(__file__).parent / "plugins" / "available")

        try:
            manager = await create_orchestrator_manager(
                plugin_dir=plugin_dir, auto_start_workers=True
            )

            status = await manager.get_status()
            print("\n🎉 OrchestratorManager Demo Complete!")
            print(f"Status: {status}")

            await manager.shutdown()

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(demo())
