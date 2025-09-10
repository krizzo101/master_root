#!/usr/bin/env python3
"""
Run the Chat Analytics Dashboard

Usage:
    python run_dashboard.py [--port PORT] [--host HOST] [--debug]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from opsvi_monitoring.chat_analytics.web.dashboard import app


def main():
    parser = argparse.ArgumentParser(description="Run Chat Analytics Dashboard")
    parser.add_argument(
        "--port", type=int, default=5001, help="Port to run on (default: 5001)"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")

    args = parser.parse_args()

    print(f"Starting Chat Analytics Dashboard on http://{args.host}:{args.port}")
    print("Press CTRL+C to stop")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
