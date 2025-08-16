#!/usr/bin/env python3
"""Start the code generation app with debug logging to files."""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime


def main():
    """Start the app with debug logging."""
    app_dir = Path(__file__).parent
    os.chdir(app_dir)

    # Create logs directory
    logs_dir = app_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Generate timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("🚀 Starting Code Generation App with Debug Logging")
    print(f"📁 Working directory: {app_dir}")
    print(f"📝 Logs will be written to: {logs_dir}")
    print("")

    # Set environment variables for debug logging
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(
                app_dir.parent.parent
            ),  # Point to src/ directory for absolute imports
            "LOG_LEVEL": "DEBUG",
            "LOG_FILE": str(logs_dir / f"app_{timestamp}.log"),
            "CELERY_LOG_FILE": str(logs_dir / f"celery_{timestamp}.log"),
        }
    )

    print("🎯 Starting with these settings:")
    print(f"   • Web Interface: http://localhost:8010")
    print(f"   • App Log File: {env['LOG_FILE']}")
    print(f"   • Celery Log File: {env['CELERY_LOG_FILE']}")
    print(f"   • Debug Level: {env['LOG_LEVEL']}")
    print("")
    print("🔍 To monitor logs in real-time:")
    print(f"   tail -f {env['LOG_FILE']}")
    print(f"   tail -f {env['CELERY_LOG_FILE']}")
    print("")
    print("▶️  Starting application...")
    print("")

    try:
        # Start the main application with enhanced logging (no auto-reload in production)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "applications.code_gen.main",
                "--log-level",
                "DEBUG",
                "--no-reload",
            ],
            env=env,
            cwd=app_dir.parent.parent,  # Run from src/ directory for module imports
        )
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Application failed to start: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
