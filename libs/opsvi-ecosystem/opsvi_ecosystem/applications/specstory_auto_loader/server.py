#!/usr/bin/env python3
"""
SpecStory Auto-Loader Server - Consolidated Version
Uses the atomic parser engine for complete decomposition and database storage
"""

import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / "shared" / "database"))
sys.path.append(
    str(Path(__file__).parent.parent.parent / "shared" / "interfaces" / "database")
)

from consolidated_arango import ConsolidatedArangoDB
from database_storage import SimplifiedSpecStoryStorage
from specstory_intelligence.atomic_parser import AtomicSpecStoryParser
from specstory_intelligence.conversation_intelligence import (
    ConversationIntelligenceEngine,
)


class SpecStoryFileHandler(FileSystemEventHandler):
    """Handle file system events for SpecStory files"""

    def __init__(self, loader_server):
        self.loader_server = loader_server
        self.debounce_delay = 0.5
        self.pending_changes = {}

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule_processing(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            self._schedule_processing(event.src_path)

    def _schedule_processing(self, filepath: str):
        """Schedule file processing with debouncing"""
        # Cancel any existing timer for this file
        if filepath in self.pending_changes:
            self.pending_changes[filepath].cancel()

        # Schedule new processing
        loop = asyncio.get_event_loop()
        timer = loop.call_later(
            self.debounce_delay,
            lambda: asyncio.create_task(
                self.loader_server.handle_file_change(filepath)
            ),
        )
        self.pending_changes[filepath] = timer


class SpecStoryAutoLoaderServer:
    """Continuously running server using atomic parser engine"""

    def __init__(
        self,
        history_dir: str = ".cursor/import",
        db_host: str = "http://127.0.0.1:8550",
        db_username: str = "root",
        db_password: str = "change_me",
        db_name: str = "_system",
    ):
        self.history_dir = Path(history_dir)

        # Initialize database client
        self.db_client = ConsolidatedArangoDB(
            host=db_host, username=db_username, password=db_password, database=db_name
        )

        # Initialize atomic parser, intelligence engine, and database storage
        self.atomic_parser = AtomicSpecStoryParser()
        self.intelligence_engine = ConversationIntelligenceEngine()
        self.db_storage = SimplifiedSpecStoryStorage(
            self.db_client, collection_prefix="specstory"
        )

        # Track file states to detect changes
        self.file_states: dict[str, dict] = {}
        self.state_file = Path(".specstory_loader_state.json")

        # Load previous state if exists
        self.load_state()

        # File monitoring
        self.observer = Observer()
        self.handler = SpecStoryFileHandler(self)

        # Statistics
        self.stats = {
            "files_processed": 0,
            "components_created": 0,
            "relationships_created": 0,
            "errors": 0,
            "start_time": None,
        }

        print("🚀 SpecStory Auto-Loader Server initialized")
        print(f"📁 Monitoring: {self.history_dir.absolute()}")
        print(f"🗄️  Database: {db_host}/{db_name}")
        print("🧩 Engine: Atomic Parser with complete decomposition")

    def load_state(self):
        """Load previous file states from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    self.file_states = json.load(f)
                print(f"📋 Loaded state for {len(self.file_states)} files")
            except Exception as e:
                print(f"⚠️  Could not load state: {e}")
                self.file_states = {}

    def save_state(self):
        """Save current file states to disk"""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.file_states, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save state: {e}")

    def get_file_stats(self, filepath: str) -> dict:
        """Get file statistics for tracking"""
        try:
            stat = os.stat(filepath)
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            return {
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "hash": hashlib.md5(content.encode()).hexdigest(),
                "line_count": len(content.splitlines()),
                "last_processed": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            print(f"⚠️  Error getting stats for {filepath}: {e}")
            return {}

    def has_file_changed(self, filepath: str) -> bool:
        """Check if file has changed since last processing"""
        current_stats = self.get_file_stats(filepath)
        if not current_stats:
            return False

        previous_stats = self.file_states.get(filepath, {})

        # Check if hash changed (content changed)
        return current_stats.get("hash") != previous_stats.get("hash")

    def is_specstory_file(self, filepath: str) -> bool:
        """Check if file is a valid SpecStory conversation (including cleaned files)"""
        try:
            with open(filepath, encoding="utf-8") as f:
                first_lines = [
                    f.readline().strip() for _ in range(10)
                ]  # Read more lines

            # Check for SpecStory markers (both original and cleaned formats)
            content = "\n".join(first_lines)
            specstory_markers = [
                "<!-- Generated by SpecStory -->",
                "_**User**_",
                "_**Assistant**_",
                "<function_calls>",
                "Human:",
                "Assistant:",
                "<!-- FILE_MAP_BEGIN",  # Cleaned file marker
                "## ",  # Cleaned files often start with headers
            ]

            # Also check if filename suggests it's a cleaned SpecStory file
            filename = Path(filepath).name
            is_cleaned_file = filename.endswith(".md") and any(
                pattern in filename
                for pattern in [
                    "Z-",  # Timestamp pattern
                    "_part",  # Chunked file pattern
                ]
            )

            return (
                any(marker in content for marker in specstory_markers)
                or is_cleaned_file
            )

        except Exception:
            return False

    async def process_file(self, filepath: str) -> bool:
        """Process a single SpecStory file using atomic parser"""
        try:
            print(f"🔄 Processing: {Path(filepath).name}")

            # Validate file
            if not self.is_specstory_file(filepath):
                print(f"⏭️  Not a SpecStory file: {filepath}")
                return False

            # Read file content
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                print(f"⏭️  Skipping empty file: {filepath}")
                return False

            # Parse with atomic parser
            components, relationships = await self.atomic_parser.parse_file(filepath)

            if not components:
                print(f"⚠️  No components extracted from: {filepath}")
                return False

            # Perform conversation intelligence analysis
            print("🧠 Analyzing conversation intelligence...")
            intelligence = await self.intelligence_engine.analyze_conversation(
                components
            )

            # Generate intelligence summary
            summary = self.intelligence_engine.generate_intelligence_summary(
                intelligence
            )

            # Store in database with intelligence data
            session_result = await self.db_storage.store_parsed_file(
                file_path=filepath,
                components=components,
                relationships=relationships,
                intelligence=intelligence,
                intelligence_summary=summary,
            )

            if session_result.get("success"):
                # Update file state
                self.file_states[filepath] = self.get_file_stats(filepath)
                self.save_state()

                # Update statistics
                self.stats["files_processed"] += 1
                self.stats["components_created"] += len(components)
                self.stats["relationships_created"] += len(relationships)

                print(f"✅ Loaded: {Path(filepath).name}")
                print(f"   📊 Session: {session_result.get('session_id', 'unknown')}")
                print(f"   🧩 Components: {len(components)}")
                print(f"   🔗 Relationships: {len(relationships)}")
                print(
                    f"   🎯 Atomic Types: {len(set(c.component_type.value for c in components))}"
                )

                # Show intelligence insights
                if intelligence.insight_patterns:
                    print(
                        f"   💡 Insights: {len(intelligence.insight_patterns)} patterns found"
                    )
                if intelligence.recursive_loops:
                    print(
                        f"   🔄 Recursive patterns: {len(intelligence.recursive_loops)}"
                    )
                if intelligence.meta_cognitive_moments:
                    print(
                        f"   🧠 Meta-cognitive moments: {len(intelligence.meta_cognitive_moments)}"
                    )
                if intelligence.philosophical_explorations:
                    print(
                        f"   🤔 Philosophical depth: {len(intelligence.philosophical_explorations)}"
                    )

                return True
            else:
                print(f"❌ Failed to store: {filepath}")
                print(f"   Error: {session_result.get('error', 'Unknown error')}")
                self.stats["errors"] += 1
                return False

        except Exception as e:
            print(f"💥 Error processing {filepath}: {e}")
            self.stats["errors"] += 1
            return False

    async def handle_file_change(self, filepath: str):
        """Handle file system change event"""
        if self.has_file_changed(filepath):
            print(f"📝 File changed: {Path(filepath).name}")
            await self.process_file(filepath)
        else:
            print(f"⚡ File touched but unchanged: {Path(filepath).name}")

    async def scan_existing_files(self):
        """Scan and process all existing files in history directory"""
        if not self.history_dir.exists():
            print(f"⚠️  History directory does not exist: {self.history_dir}")
            return

        md_files = list(self.history_dir.glob("*.md"))
        print(f"🔍 Found {len(md_files)} markdown files")

        processed = 0
        skipped = 0

        for filepath in md_files:
            filepath_str = str(filepath)

            if self.has_file_changed(filepath_str):
                if await self.process_file(filepath_str):
                    processed += 1
                else:
                    print(f"⚠️  Failed to process: {filepath.name}")
            else:
                print(f"⚡ Already processed: {filepath.name}")
                skipped += 1

        print(f"📈 Scan complete: {processed} processed, {skipped} skipped")

    def start_monitoring(self):
        """Start file system monitoring"""
        if not self.history_dir.exists():
            print(f"⚠️  Creating history directory: {self.history_dir}")
            self.history_dir.mkdir(parents=True, exist_ok=True)

        self.observer.schedule(self.handler, str(self.history_dir), recursive=False)
        self.observer.start()
        print(f"👁️  Started monitoring: {self.history_dir}")

    def stop_monitoring(self):
        """Stop file system monitoring"""
        self.observer.stop()
        self.observer.join()
        print("🛑 Stopped monitoring")

    async def run_server(self):
        """Run the auto-loader server"""
        print("🚀 Starting SpecStory Auto-Loader Server...")

        try:
            # Test database connection
            try:
                # Simple connection test
                result = self.db_client.search(
                    "content", "heuristics", content="test", limit=1
                )
                print("✅ Database connected successfully")
            except Exception as db_error:
                print(f"❌ Database connection failed: {db_error}")
                return

            # Initialize database storage
            await self.db_storage.initialize_database()

            # Track start time
            self.stats["start_time"] = datetime.now(timezone.utc)

            # Scan existing files first
            print("\n📂 Scanning existing files...")
            await self.scan_existing_files()

            # Start monitoring for changes
            print("\n👁️  Starting file monitoring...")
            self.start_monitoring()

            print("\n🎯 Auto-loader server running! Press Ctrl+C to stop.")
            print("📝 Watching for new conversations and file changes...")
            print("🧩 Using atomic parser for complete decomposition")

            # Keep server running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested...")

        except Exception as e:
            print(f"💥 Server error: {e}")
        finally:
            self.stop_monitoring()
            print("👋 SpecStory Auto-Loader Server stopped")

    def status(self):
        """Show server status"""
        print("📊 SpecStory Auto-Loader Status:")
        print(f"   📁 Monitoring: {self.history_dir.absolute()}")
        print(f"   📋 Tracked files: {len(self.file_states)}")
        print("   🧩 Engine: Atomic Parser (15 component types)")

        # Statistics
        if self.stats["start_time"]:
            uptime = datetime.now(timezone.utc) - self.stats["start_time"]
            print(f"   ⏱️  Uptime: {uptime}")

        print(f"   📈 Files processed: {self.stats['files_processed']}")
        print(f"   🧩 Components created: {self.stats['components_created']}")
        print(f"   🔗 Relationships created: {self.stats['relationships_created']}")
        print(f"   ❌ Errors: {self.stats['errors']}")

        # Database status
        try:
            result = self.db_client.search(
                "content", "heuristics", content="test", limit=1
            )
            print("   🗄️  Database: ✅ Connected")
        except Exception as e:
            print(f"   🗄️  Database: ❌ Connection failed - {e}")

        # Recent files
        if self.file_states:
            recent_files = sorted(
                self.file_states.items(),
                key=lambda x: x[1].get("last_processed", ""),
                reverse=True,
            )[:5]

            print("   📝 Recent files:")
            for filepath, stats in recent_files:
                filename = Path(filepath).name
                processed_time = stats.get("last_processed", "unknown")[:19]
                print(f"      {filename} - {processed_time}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="SpecStory Auto-Loader Server (Atomic Engine)"
    )
    parser.add_argument(
        "--history-dir",
        default=".cursor/import",
        help="Directory to monitor for SpecStory files",
    )
    parser.add_argument(
        "--db-host", default="http://127.0.0.1:8550", help="ArangoDB host URL"
    )
    parser.add_argument("--db-username", default="root", help="Database username")
    parser.add_argument("--db-password", default="change_me", help="Database password")
    parser.add_argument("--db-name", default="_system", help="Database name")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument(
        "--scan-only", action="store_true", help="Scan existing files once and exit"
    )

    args = parser.parse_args()

    # Create server instance
    server = SpecStoryAutoLoaderServer(
        history_dir=args.history_dir,
        db_host=args.db_host,
        db_username=args.db_username,
        db_password=args.db_password,
        db_name=args.db_name,
    )

    if args.status:
        server.status()
    elif args.scan_only:
        asyncio.run(server.scan_existing_files())
    else:
        asyncio.run(server.run_server())


if __name__ == "__main__":
    main()
