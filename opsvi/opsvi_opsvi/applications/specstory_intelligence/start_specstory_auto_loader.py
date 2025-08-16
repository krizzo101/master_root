#!/usr/bin/env python3
"""
SpecStory Auto-Loader Launcher - Enhanced with Conversation Intelligence
Continuously monitors .specstory/history and loads conversations with atomic parsing and intelligence analysis
"""

import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Also add the current application path for relative imports
current_app_path = Path(__file__).parent
sys.path.insert(0, str(current_app_path))

try:
    from auto_loader.server import SpecStoryAutoLoaderServer
except ImportError:
    # Fallback to absolute import
    from src.applications.specstory_intelligence.auto_loader.server import (
        SpecStoryAutoLoaderServer,
    )


async def main():
    """Main launcher function"""
    print("🚀 SpecStory Auto-Loader with Conversation Intelligence")
    print("=" * 60)
    print("🧩 Engine: Atomic Parser (15 component types)")
    print("🧠 Intelligence: Advanced conversation analysis")
    print("🗄️  Database: ArangoDB with intelligence storage")
    print("👁️  Monitoring: .specstory/history directory")
    print()

    # Initialize server
    server = SpecStoryAutoLoaderServer(
        history_dir=".specstory/history",
        db_host="http://127.0.0.1:8550",
        db_username="root",
        db_password="change_me",
        db_name="_system",
    )

    # Run server
    await server.run_server()


def status():
    """Show server status"""
    server = SpecStoryAutoLoaderServer()
    server.status()


def scan_only():
    """Scan files without starting server"""

    async def scan():
        server = SpecStoryAutoLoaderServer()
        print("🔍 Scanning existing files only (no server mode)...")

        # Initialize database
        await server.db_storage.initialize_database()

        # Scan files
        await server.scan_existing_files()
        print("✅ Scan complete")

    asyncio.run(scan())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="SpecStory Auto-Loader with Conversation Intelligence"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show server status and exit"
    )
    parser.add_argument(
        "--scan-only", action="store_true", help="Scan existing files once and exit"
    )

    args = parser.parse_args()

    if args.status:
        status()
    elif args.scan_only:
        scan_only()
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n👋 Auto-loader stopped by user")
        except Exception as e:
            print(f"💥 Error: {e}")
            sys.exit(1)
