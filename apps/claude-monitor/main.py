#!/usr/bin/env python3
"""
Claude Monitor - Main Application
Ties together the backend monitoring service and console UI.
Provides unified entry point with CLI arguments for different modes.
"""

import argparse
import asyncio
import logging
import multiprocessing as mp
import os
import signal
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional

import uvicorn

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from backend.monitoring_service import app as monitoring_app
from console.terminal_ui import TerminalUI

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ClaudeMonitor:
    """Main Claude Monitor application coordinator"""

    def __init__(self, args):
        self.args = args
        self.backend_process: Optional[mp.Process] = None
        self.ui_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()

    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def start_backend_service(self):
        """Start the backend monitoring service in a separate process"""

        def run_backend():
            """Run backend service"""
            try:
                logger.info("Starting backend monitoring service...")
                uvicorn.run(
                    monitoring_app,
                    host=self.args.host,
                    port=self.args.port,
                    log_level=self.args.log_level.lower(),
                    access_log=self.args.access_log,
                )
            except Exception as e:
                logger.error(f"Backend service error: {e}")

        self.backend_process = mp.Process(target=run_backend)
        self.backend_process.start()
        logger.info(
            f"Backend service started on {self.args.host}:{self.args.port} (PID: {self.backend_process.pid})"
        )

    async def start_console_ui(self):
        """Start the console UI"""
        try:
            logger.info("Starting console UI...")
            websocket_url = f"ws://{self.args.host}:{self.args.port}/ws"
            ui = TerminalUI(websocket_url=websocket_url)
            await ui.run()
        except Exception as e:
            logger.error(f"Console UI error: {e}")
            await self.shutdown()

    async def start_web_ui(self):
        """Start web UI (placeholder for future implementation)"""
        logger.info("Web UI mode selected")
        logger.info(
            f"Backend API available at: http://{self.args.host}:{self.args.port}"
        )
        logger.info("Web UI not yet implemented. Use --console mode for now.")
        logger.info("Press Ctrl+C to stop the backend service.")

        # Just keep the backend running
        try:
            while not self.shutdown_event.is_set():
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.shutdown()

    async def run_backend_only(self):
        """Run only the backend service"""
        logger.info("Backend-only mode")
        logger.info(
            f"Monitoring API available at: http://{self.args.host}:{self.args.port}"
        )
        logger.info("Health check: http://{self.args.host}:{self.args.port}/health")
        logger.info(
            "Dashboard data: http://{self.args.host}:{self.args.port}/api/dashboard"
        )
        logger.info("Press Ctrl+C to stop.")

        try:
            while not self.shutdown_event.is_set():
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("Initiating graceful shutdown...")

        # Stop UI task if running
        if self.ui_task and not self.ui_task.done():
            logger.info("Stopping console UI...")
            self.ui_task.cancel()
            try:
                await self.ui_task
            except asyncio.CancelledError:
                pass

        # Stop backend process if running
        if self.backend_process:
            try:
                # Check if process is valid and alive before attempting shutdown
                if (
                    hasattr(self.backend_process, "_popen")
                    and self.backend_process._popen is not None
                ):
                    if self.backend_process.is_alive():
                        logger.info("Stopping backend service...")
                        self.backend_process.terminate()

                        # Wait for graceful termination with timeout
                        try:
                            self.backend_process.join(timeout=5)
                        except (OSError, ValueError) as e:
                            logger.warning(f"Error during graceful shutdown: {e}")

                        # Force kill if still alive
                        if self.backend_process.is_alive():
                            logger.warning(
                                "Backend service did not stop gracefully, forcing termination..."
                            )
                            try:
                                self.backend_process.kill()
                                self.backend_process.join(timeout=2)
                            except (OSError, ValueError) as e:
                                logger.error(f"Error during force kill: {e}")
                    else:
                        logger.info("Backend process already terminated")
                else:
                    logger.info(
                        "Backend process not properly initialized, skipping shutdown"
                    )

            except (AttributeError, OSError, ValueError) as e:
                logger.warning(f"Process shutdown error (non-critical): {e}")
            finally:
                # Always reset the process reference
                self.backend_process = None

        self.shutdown_event.set()
        logger.info("Shutdown complete")

    async def run(self):
        """Main application run method"""
        self.setup_signal_handlers()

        try:
            if self.args.mode == "console":
                # Start backend service
                self.start_backend_service()

                # Wait a moment for backend to start
                await asyncio.sleep(2)

                # Start console UI
                self.ui_task = asyncio.create_task(self.start_console_ui())
                await self.ui_task

            elif self.args.mode == "web":
                # Start backend service
                self.start_backend_service()

                # Wait a moment for backend to start
                await asyncio.sleep(2)

                # Start web UI (or just keep backend running for now)
                await self.start_web_ui()

            elif self.args.mode == "backend":
                # Start only backend service
                self.start_backend_service()

                # Wait a moment for backend to start
                await asyncio.sleep(2)

                # Keep running until shutdown
                await self.run_backend_only()

        except Exception as e:
            logger.error(f"Application error: {e}")
            await self.shutdown()
        finally:
            # Ensure cleanup
            await self.shutdown()


def create_argument_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Claude Monitor - Comprehensive monitoring for Claude processes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with console UI (default)
  %(prog)s --console               # Run with console UI
  %(prog)s --web                   # Run with web UI (future)
  %(prog)s --backend               # Run backend service only
  %(prog)s --port 8080             # Use custom port
  %(prog)s --host 0.0.0.0         # Bind to all interfaces
  %(prog)s --log-level DEBUG       # Enable debug logging
        """,
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--console",
        action="store_const",
        const="console",
        dest="mode",
        help="Run with console UI (default)",
    )
    mode_group.add_argument(
        "--web",
        action="store_const",
        const="web",
        dest="mode",
        help="Run with web UI (future implementation)",
    )
    mode_group.add_argument(
        "--backend",
        action="store_const",
        const="backend",
        dest="mode",
        help="Run backend service only",
    )

    # Server configuration
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to bind the backend service (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the backend service (default: 8000)",
    )

    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )
    parser.add_argument(
        "--access-log",
        action="store_true",
        help="Enable access logging for backend service",
    )

    # Development options
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (backend only)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Set default mode
    parser.set_defaults(mode="console")

    return parser


def validate_environment():
    """Validate environment and dependencies"""
    errors = []

    # Check if database path exists
    db_path = Path("/home/opsvi/master_root/chat_logs.db")
    if not db_path.exists():
        errors.append(f"Database not found at {db_path}. Some features may not work.")

    # Check if we can import required modules
    try:
        import docker
    except ImportError:
        errors.append(
            "Docker python library not found. Docker monitoring will be disabled."
        )

    try:
        import psutil
    except ImportError:
        errors.append("psutil library not found. System monitoring will be limited.")

    try:
        import rich
    except ImportError:
        errors.append("Rich library not found. Console UI will not work.")

    try:
        import fastapi
        import uvicorn
    except ImportError:
        errors.append("FastAPI/Uvicorn not found. Backend service will not work.")

    if errors:
        logger.warning("Environment validation warnings:")
        for error in errors:
            logger.warning(f"  - {error}")

    return len(errors) == 0 or all("not found" not in error for error in errors)


async def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("=== Claude Monitor Starting ===")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Backend: {args.host}:{args.port}")
    logger.info(f"Log Level: {args.log_level}")

    # Validate environment
    if not validate_environment():
        logger.error(
            "Environment validation failed. Some features may not work correctly."
        )
        if not args.debug:
            logger.info("Use --debug flag for more details.")

    # Create and run application
    app = ClaudeMonitor(args)

    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    logger.info("=== Claude Monitor Stopped ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
