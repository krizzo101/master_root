"""
Dependency Manager for Code Generation Application

Automatically starts, manages, and monitors all required dependencies:
- Redis server
- Celery worker
- Database initialization

Ensures the application runs as designed without manual setup.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import redis

from config import get_config

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages application dependencies automatically."""

    def __init__(self):
        self.config = get_config()
        self.redis_process: subprocess.Popen | None = None
        self.celery_process: subprocess.Popen | None = None
        self.shutdown_event = threading.Event()

    def start_all_dependencies(self) -> bool:
        """Start all required dependencies. Returns True if successful."""
        logger.info("Starting dependency manager...")

        # 1. Initialize database
        if not self._init_database():
            return False

        # 2. Start Redis if not running
        if not self._ensure_redis_running():
            return False

        # 3. Start Celery worker
        if not self._start_celery_worker():
            return False

        # 4. Register shutdown handlers
        self._register_shutdown_handlers()

        logger.info("All dependencies started successfully")
        return True

    def _init_database(self) -> bool:
        """Initialize the database."""
        try:
            from database import init_db

            init_db()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

    def _ensure_redis_running(self) -> bool:
        """Ensure Redis is running, start it if necessary."""
        # First check if Redis is already running
        if self._test_redis_connection():
            logger.info("Redis server already running")
            return True

        logger.info("Redis not running, attempting to start...")

        # Try to start Redis server
        redis_cmd = self._get_redis_start_command()
        if not redis_cmd:
            logger.error("Could not determine how to start Redis on this system")
            return False

        try:
            self.redis_process = subprocess.Popen(
                redis_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            # Wait for Redis to start
            for attempt in range(30):  # 30 second timeout
                if self._test_redis_connection():
                    logger.info("Redis server started successfully")
                    return True
                time.sleep(1)

            logger.error("Redis failed to start within timeout")
            return False

        except Exception as e:
            logger.error(f"Failed to start Redis: {e}")
            return False

    def _get_redis_start_command(self) -> list[str] | None:
        """Get the appropriate Redis start command for this system."""
        # Try different Redis start methods
        commands_to_try = [
            ["redis-server", "--daemonize", "no"],  # Standard Redis
            ["redis-server"],  # Simple Redis
            ["/usr/bin/redis-server"],  # System Redis
            ["/usr/local/bin/redis-server"],  # Homebrew Redis
        ]

        for cmd in commands_to_try:
            try:
                # Test if command exists
                result = subprocess.run(
                    [cmd[0], "--version"], capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found Redis at: {cmd[0]}")
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        # Try to install Redis if not found
        return self._try_install_redis()

    def _try_install_redis(self) -> list[str] | None:
        """Attempt to install Redis automatically."""
        logger.info("Redis not found, attempting automatic installation...")

        install_commands = {
            "linux": [
                "bash",
                "-c",
                "sudo apt-get update && sudo apt-get install -y redis-server",
            ],
            "darwin": ["brew", "install", "redis"],
        }

        platform = sys.platform
        if platform.startswith("linux"):
            platform = "linux"
        elif platform == "darwin":
            platform = "darwin"
        else:
            logger.error(f"Automatic Redis installation not supported on {platform}")
            return None

        install_cmd = install_commands.get(platform)
        if not install_cmd:
            return None

        try:
            logger.info(f"Installing Redis with: {' '.join(install_cmd)}")
            result = subprocess.run(install_cmd, timeout=300)  # 5 minute timeout

            if result.returncode == 0:
                logger.info("Redis installed successfully")
                return ["redis-server"]
            else:
                logger.error("Redis installation failed")
                return None

        except Exception as e:
            logger.error(f"Redis installation error: {e}")
            return None

    def _test_redis_connection(self) -> bool:
        """Test if Redis is accessible."""
        try:
            client = redis.Redis.from_url(self.config.redis_url)
            client.ping()
            return True
        except Exception:
            return False

    def _start_celery_worker(self) -> bool:
        """Start the Celery worker process."""
        try:
            # Get the current working directory
            app_dir = Path(__file__).parent

            # Start Celery worker
            log_level = os.environ.get("LOG_LEVEL", "info").lower()
            celery_log_file = os.environ.get("CELERY_LOG_FILE")

            # Set up environment for Celery worker with correct Python path
            celery_env = os.environ.copy()
            # Add src/ directory to PYTHONPATH so Celery can find shared.mcp
            src_dir = (
                app_dir.parent.parent
            )  # Go up from code_gen to applications to src
            if "PYTHONPATH" in celery_env:
                celery_env["PYTHONPATH"] = f"{src_dir}:{celery_env['PYTHONPATH']}"
            else:
                celery_env["PYTHONPATH"] = str(src_dir)

            logger.info(f"Celery PYTHONPATH set to: {celery_env['PYTHONPATH']}")

            celery_cmd = [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "applications.code_gen.task_queue",
                "worker",
                f"--loglevel={log_level}",
                "--concurrency=1",  # Single worker for debugging
            ]

            # Add log file if specified
            if celery_log_file:
                celery_cmd.extend([f"--logfile={celery_log_file}"])

            logger.info(f"Starting Celery worker: {' '.join(celery_cmd)}")

            # Prepare stdout/stderr handling
            if celery_log_file:
                # Log to file, capture minimal stdout/stderr
                stdout_handler = subprocess.DEVNULL
                stderr_handler = subprocess.DEVNULL
            else:
                # Log to pipes for capture
                stdout_handler = subprocess.PIPE
                stderr_handler = subprocess.PIPE

            self.celery_process = subprocess.Popen(
                celery_cmd,
                cwd=src_dir,  # Run from src directory so imports work correctly
                env=celery_env,
                stdout=stdout_handler,
                stderr=stderr_handler,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            # Give Celery a moment to start
            time.sleep(3)

            if self.celery_process.poll() is None:
                logger.info("Celery worker started successfully")
                return True
            else:
                logger.error("Celery worker failed to start")
                return False

        except Exception as e:
            logger.error(f"Failed to start Celery worker: {e}")
            return False

    def _register_shutdown_handlers(self):
        """Register handlers to cleanly shut down dependencies."""

        def shutdown_handler(signum, frame):
            logger.info("Received shutdown signal, cleaning up dependencies...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

    def shutdown(self):
        """Shutdown all managed dependencies."""
        logger.info("Shutting down dependencies...")
        self.shutdown_event.set()

        # Stop Celery worker
        if self.celery_process and self.celery_process.poll() is None:
            logger.info("Stopping Celery worker...")
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(self.celery_process.pid), signal.SIGTERM)
                else:
                    self.celery_process.terminate()
                self.celery_process.wait(timeout=10)
                logger.info("Celery worker stopped")
            except Exception as e:
                logger.warning(f"Error stopping Celery worker: {e}")

        # Stop Redis if we started it
        if self.redis_process and self.redis_process.poll() is None:
            logger.info("Stopping Redis server...")
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(self.redis_process.pid), signal.SIGTERM)
                else:
                    self.redis_process.terminate()
                self.redis_process.wait(timeout=10)
                logger.info("Redis server stopped")
            except Exception as e:
                logger.warning(f"Error stopping Redis server: {e}")

    def health_check(self) -> dict[str, bool]:
        """Check the health of all dependencies."""
        health = {}

        # Check Redis
        health["redis"] = self._test_redis_connection()

        # Check Celery worker
        health["celery"] = (
            self.celery_process is not None and self.celery_process.poll() is None
        )

        # Check database
        try:
            from database import get_session
            from sqlalchemy import text

            with get_session() as session:
                session.execute(text("SELECT 1"))
            health["database"] = True
        except Exception:
            health["database"] = False

        return health


# Global dependency manager instance
_dependency_manager: DependencyManager | None = None


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance."""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager


def start_dependencies() -> bool:
    """Start all application dependencies."""
    return get_dependency_manager().start_all_dependencies()


def shutdown_dependencies():
    """Shutdown all application dependencies."""
    if _dependency_manager:
        _dependency_manager.shutdown()


def health_check_dependencies() -> dict[str, bool]:
    """Check the health of all dependencies."""
    return get_dependency_manager().health_check()
