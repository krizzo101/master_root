#!/usr/bin/env python3
"""
Main entry point for IDE Context Bridge Service.

Provides CLI interface for starting and managing the bridge service.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

import click
import uvicorn

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import core modules (always available)
from bridge_service.config import (
    create_sample_config,
    get_default_config_path,
    load_config,
    print_config_summary,
)

# Try to import modules with external dependencies
try:
    from bridge_service.auth import initialize_auth
    from bridge_service.server import create_bridge_server

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    MISSING_DEPENDENCY_ERROR = str(e)


# Global server instance for signal handling
bridge_server = None


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


def handle_shutdown_signal(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")

    if bridge_server:
        asyncio.create_task(bridge_server.cleanup())

    sys.exit(0)


@click.group()
@click.version_option()
def cli():
    """IDE Context Bridge - Intelligent code assistance service."""
    pass


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
@click.option("--host", default=None, help="Host to bind to (overrides config)")
@click.option(
    "--port", type=int, default=None, help="Port to bind to (overrides config)"
)
@click.option(
    "--log-level", default=None, help="Log level (DEBUG, INFO, WARNING, ERROR)"
)
@click.option("--log-file", help="Log file path")
@click.option("--daemon", is_flag=True, help="Run as daemon")
@click.option("--pid-file", help="PID file path when running as daemon")
def start(config, host, port, log_level, log_file, daemon, pid_file):
    """Start the IDE Context Bridge service."""
    global bridge_server

    # Check if dependencies are available
    if not DEPENDENCIES_AVAILABLE:
        click.echo("✗ Missing required dependencies!", err=True)
        click.echo(f"Error: {MISSING_DEPENDENCY_ERROR}", err=True)
        click.echo("\nPlease install dependencies with:")
        click.echo("  pip install -r requirements.txt")
        sys.exit(1)

    # Load configuration
    config_path = config or get_default_config_path()
    bridge_config = load_config(config_path)

    # Override config with CLI options
    if host:
        bridge_config.server.host = host
    if port:
        bridge_config.server.port = port
    if log_level:
        bridge_config.logging.level = log_level.upper()
    if log_file:
        bridge_config.logging.file_path = log_file

    # Setup logging
    setup_logging(
        log_level=bridge_config.logging.level, log_file=bridge_config.logging.file_path
    )

    logger = logging.getLogger(__name__)

    # Handle daemon mode
    if daemon:
        try:
            import daemon
            import lockfile

            # Create daemon context
            with daemon.DaemonContext(
                pidfile=lockfile.FileLock(pid_file) if pid_file else None,
                signal_map={
                    signal.SIGTERM: handle_shutdown_signal,
                    signal.SIGINT: handle_shutdown_signal,
                },
            ):
                asyncio.run(run_server(bridge_config))
        except ImportError:
            logger.error("python-daemon package required for daemon mode")
            sys.exit(1)
    else:
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, handle_shutdown_signal)
        signal.signal(signal.SIGTERM, handle_shutdown_signal)

        # Run server
        try:
            asyncio.run(run_server(bridge_config))
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
            sys.exit(1)


async def run_server(config):
    """Run the bridge server with proper initialization and cleanup."""
    global bridge_server
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting IDE Context Bridge Service...")
        print_config_summary(config)

        # Initialize authentication
        auth_manager = initialize_auth(config)
        logger.info(
            f"Authentication initialized (required: {auth_manager.require_auth})"
        )

        # Create and initialize server
        bridge_server = await create_bridge_server(config)
        logger.info(
            f"Server initialized, listening on {config.server.host}:{config.server.port}"
        )

        # Start the FastAPI server
        uvicorn_config = uvicorn.Config(
            app=bridge_server.app,
            host=config.server.host,
            port=config.server.port,
            log_level=config.logging.level.lower(),
            access_log=True,
            ws_ping_interval=20,
            ws_ping_timeout=20,
            ws_max_size=16777216,  # 16MB
            timeout_keep_alive=30,
        )

        server = uvicorn.Server(uvicorn_config)

        # Run server
        await server.serve()

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise
    finally:
        if bridge_server:
            await bridge_server.cleanup()


@cli.command()
@click.argument("config_path", default="./bridge-config.yaml")
def init_config(config_path):
    """Create a sample configuration file."""
    try:
        create_sample_config(config_path)
        click.echo(f"✓ Created sample configuration at: {config_path}")
        click.echo("\nEdit the configuration file and then start the service with:")
        click.echo(f"  ide-context-bridge start --config {config_path}")
    except Exception as e:
        click.echo(f"✗ Failed to create configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", help="Configuration file to validate")
def validate(config):
    """Validate configuration file."""
    config_path = config or get_default_config_path()

    if not config_path:
        click.echo("✗ No configuration file found", err=True)
        sys.exit(1)

    try:
        bridge_config = load_config(config_path)
        click.echo(f"✓ Configuration file {config_path} is valid")

        # Show summary
        print_config_summary(bridge_config)

    except Exception as e:
        click.echo(f"✗ Configuration validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def status(config, format):
    """Check service status and health."""
    import json

    import aiohttp

    # Load configuration to get service URL
    config_path = config or get_default_config_path()
    bridge_config = load_config(config_path) if config_path else None

    if not bridge_config:
        click.echo("✗ No configuration found", err=True)
        sys.exit(1)

    base_url = f"http://{bridge_config.server.host}:{bridge_config.server.port}"

    async def check_status():
        try:
            async with aiohttp.ClientSession() as session:
                # Health check
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()

                        if format == "json":
                            click.echo(json.dumps(health_data, indent=2))
                        else:
                            status_icon = (
                                "✓" if health_data["status"] == "healthy" else "✗"
                            )
                            click.echo(
                                f"{status_icon} Service Status: {health_data['status']}"
                            )
                            click.echo(f"  Version: {health_data['version']}")
                            click.echo(
                                f"  Active Connections: {health_data['active_connections']}"
                            )
                            click.echo(
                                f"  Active Sessions: {health_data['active_sessions']}"
                            )
                            click.echo(f"  Timestamp: {health_data['timestamp']}")
                    else:
                        click.echo(
                            f"✗ Health check failed with status {response.status}",
                            err=True,
                        )
                        sys.exit(1)

        except aiohttp.ClientConnectorError:
            click.echo("✗ Service is not running or not reachable", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"✗ Status check failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(check_status())


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
def stop(config):
    """Stop the IDE Context Bridge service."""
    # This would typically send a signal to a running daemon
    # For now, just inform the user
    click.echo("To stop the service, use Ctrl+C if running in foreground mode")
    click.echo("For daemon mode, use: kill -TERM <pid>")


@cli.command()
@click.option("--config", "-c", help="Configuration file path")
@click.option(
    "--format",
    type=click.Choice(["prometheus", "json"]),
    default="json",
    help="Output format",
)
def metrics(config, format):
    """Get service metrics."""
    import json

    import aiohttp

    # Load configuration
    config_path = config or get_default_config_path()
    bridge_config = load_config(config_path) if config_path else None

    if not bridge_config:
        click.echo("✗ No configuration found", err=True)
        sys.exit(1)

    base_url = f"http://{bridge_config.server.host}:{bridge_config.server.port}"

    async def get_metrics():
        try:
            async with aiohttp.ClientSession() as session:
                endpoint = "/metrics" if format == "prometheus" else "/metrics"
                async with session.get(f"{base_url}{endpoint}") as response:
                    if response.status == 200:
                        if format == "prometheus":
                            content = await response.text()
                            click.echo(content)
                        else:
                            content = await response.json()
                            click.echo(json.dumps(content, indent=2, default=str))
                    else:
                        click.echo(
                            f"✗ Metrics request failed with status {response.status}",
                            err=True,
                        )
                        sys.exit(1)

        except aiohttp.ClientConnectorError:
            click.echo("✗ Service is not running or not reachable", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"✗ Metrics request failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(get_metrics())


@cli.command()
@click.option("--count", type=int, default=1, help="Number of API keys to generate")
def generate_key(count):
    """Generate new API key(s)."""
    try:
        from bridge_service.auth import generate_api_key
    except ImportError:
        # Fallback implementation using only standard library
        import secrets

        def generate_api_key():
            return secrets.token_urlsafe(32)

    if count == 1:
        key = generate_api_key()
        click.echo(f"Generated API Key: {key}")
        click.echo(
            "\nAdd this to your configuration file under security.allowed_api_keys"
        )
    else:
        click.echo(f"Generated {count} API Keys:")
        for i in range(count):
            key = generate_api_key()
            click.echo(f"  {i+1}: {key}")
        click.echo(
            "\nAdd these to your configuration file under security.allowed_api_keys"
        )


if __name__ == "__main__":
    cli()
