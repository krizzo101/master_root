#!/usr/bin/env python3
"""Main entry point for the Code Generation Utility."""
import argparse
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).parent))
from applications.code_gen.logging_config import setup_logging

from config import config, reload_config


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Code Generation Utility - Automated Python project generation"
    )

    # Server options
    parser.add_argument(
        "--host", default=config.host, help=f"Host to bind to (default: {config.host})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.port,
        help=f"Port to bind to (default: {config.port})",
    )
    parser.add_argument(
        "--debug", action="store_true", default=config.debug, help="Enable debug mode"
    )
    parser.add_argument(
        "--no-reload", action="store_true", help="Disable auto-reload (production mode)"
    )
    parser.add_argument(
        "--no-research", action="store_true", help="Disable research insights gathering"
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=config.log_level,
        help=f"Log level (default: {config.log_level})",
    )
    parser.add_argument("--log-file", help="Log file path (default: console only)")

    # Configuration
    parser.add_argument(
        "--reload-config",
        action="store_true",
        help="Reload configuration from environment variables",
    )
    parser.add_argument(
        "--show-config", action="store_true", help="Show current configuration and exit"
    )

    args = parser.parse_args()

    # Reload config if requested
    if args.reload_config:
        reload_config()

    # Override config with command line arguments
    config.host = args.host
    config.port = args.port
    config.debug = args.debug
    config.log_level = args.log_level

    # Always disable reload for production stability (file generation causes restarts)
    enable_reload = False

    if args.log_file:
        config.log_file = Path(args.log_file)

    # Setup logging with updated config
    setup_logging(config.log_level, config.log_file)

    # Show config if requested
    if args.show_config:
        print("Current Configuration:")
        print(f"  Host: {config.host}")
        print(f"  Port: {config.port}")
        print(f"  Debug: {config.debug}")
        print(f"  Log Level: {config.log_level}")
        print(f"  Log File: {config.log_file}")
        print(f"  Job Output Dir: {config.job_output_dir}")
        print(f"  Max Concurrent Jobs: {config.max_concurrent_jobs}")
        print(f"  Job Timeout: {config.job_timeout_seconds}s")
        print(f"  Rate Limit: {config.rate_limit_requests}/{config.rate_limit_window}s")
        print(f"  Max Request Size: {config.max_request_size} bytes")
        print(f"  OpenAI API Key: {'Set' if config.openai_api_key else 'Not set'}")
        return 0

    # Validate OpenAI API key
    if not config.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not set. This is required for AI features.")
        print("   Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return 1

    # Start all dependencies first
    print("🔧 Starting dependencies...")
    from applications.code_gen.dependency_manager import (
        shutdown_dependencies,
        start_dependencies,
    )

    if not start_dependencies():
        print("❌ Failed to start dependencies. Exiting.")
        return 1

    print("✅ All dependencies started successfully")

    # Start the server
    print(f"🚀 Starting Code Generation Utility on {config.host}:{config.port}")
    print(f"📁 Job output directory: {config.job_output_dir}")
    print(f"🐛 Debug mode: {config.debug}")
    print("\n📡 Available endpoints:")
    print("  POST /chat - Create new generation job")
    print("  GET /status/{job_id} - Check job status")
    print("  GET /artifacts/{job_id} - Download project artifacts")
    print("  GET /health - Health check")
    print("  GET /metrics - Application metrics")
    print("  GET /info - Application information")
    print("  WS /ws/{job_id} - Real-time progress updates")
    print(f"\n🎯 Ready! Visit http://localhost:{config.port} for the web interface")
    print("Press Ctrl+C to stop the server")

    try:
        uvicorn.run(
            "applications.code_gen.api:app",
            host=config.host,
            port=config.port,
            log_level=config.log_level.lower(),
            access_log=True,
            reload=enable_reload,
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    finally:
        # Always clean up dependencies
        try:
            shutdown_dependencies()
            print("✅ Dependency cleanup complete")
        except Exception as cleanup_error:
            print(f"⚠️  Warning during cleanup: {cleanup_error}")

        return 0


if __name__ == "__main__":
    sys.exit(main())
