#!/usr/bin/env python3
"""
SpecStory Auto-Loader Server - Consolidated Version
Uses the atomic parser engine for complete decomposition and database storage
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Add paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))
os.environ["PYTHONPATH"] = str(project_root)
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

from src.applications.specstory_intelligence.atomic_parser import AtomicSpecStoryParser
from src.applications.specstory_intelligence.auto_loader.code_chunker import (
    chunk_code_file,
)
from src.applications.specstory_intelligence.auto_loader.database_storage import (
    SimplifiedSpecStoryStorage,
)
from src.applications.specstory_intelligence.conversation_intelligence import (
    ConversationIntelligenceEngine,
)
from src.shared.interfaces.database.arango_interface import (
    DirectArangoDB as ArangoInterface,
)

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

CODE_FILE_EXTENSIONS = [".py"]  # Extend as needed


class SpecStoryFileHandler(FileSystemEventHandler):
    """Handle file system events for SpecStory and code files"""

    def __init__(self, loader_server):
        self.loader_server = loader_server
        self.debounce_delay = 0.5
        self.pending_changes = {}

    def on_modified(self, event):
        if not event.is_directory and (
            event.src_path.endswith(".md") or self._is_code_file(event.src_path)
        ):
            self._schedule_processing(event.src_path)

    def on_created(self, event):
        if not event.is_directory and (
            event.src_path.endswith(".md") or self._is_code_file(event.src_path)
        ):
            self._schedule_processing(event.src_path)

    def _is_code_file(self, filepath: str) -> bool:
        _, ext = os.path.splitext(filepath)
        return ext in CODE_FILE_EXTENSIONS

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


class CodeChunkComponent:
    def __init__(self, data: dict):
        self.data = data
        self.session_id = data.get("session_id")
        self._component_type = data.get("component_type", "code_chunk")

    def to_arango_document(self):
        return self.data

    @property
    def component_type(self):
        class _Value:
            def __init__(self, value):
                self.value = value

        return _Value(self._component_type)


class CodeChunkRelationship:
    def __init__(self, data: dict):
        self.data = data

    def to_arango_edge(self):
        return self.data


class SpecStoryAutoLoaderServer:
    """Continuously running server using atomic parser engine"""

    def __init__(
        self,
        history_dir: str = ".specstory/history",
        db_host: str = "http://127.0.0.1:8550",
        db_username: str = "root",
        db_password: str = "change_me",
        db_name: str = "_system",
    ):
        self.history_dir = Path(history_dir)

        # Initialize database client
        self.db_client = ArangoInterface(
            host=db_host, username=db_username, password=db_password, database=db_name
        )

        # Initialize atomic parser, intelligence engine, and database storage
        self.atomic_parser = AtomicSpecStoryParser()
        self.intelligence_engine = ConversationIntelligenceEngine()
        self.db_storage = SimplifiedSpecStoryStorage(
            self.db_client, collection_prefix="specstory"
        )

        # Track file states to detect changes
        self.file_states: Dict[str, Dict] = {}
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

    def get_file_stats(self, filepath: str) -> Dict:
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
        """Check if file is a valid SpecStory conversation"""
        try:
            with open(filepath, encoding="utf-8") as f:
                first_lines = [f.readline().strip() for _ in range(5)]

            # Check for SpecStory markers
            content = "\n".join(first_lines)
            specstory_markers = [
                "<!-- Generated by SpecStory -->",
                "_**User**_",
                "_**Assistant**_",
                "<function_calls>",
                "Human:",
                "Assistant:",
            ]

            return any(marker in content for marker in specstory_markers)

        except Exception:
            return False

    async def process_file(self, filepath: str) -> bool:
        """Process a single SpecStory or code file"""
        try:
            print(f"\U0001f504 Processing: {Path(filepath).name}")

            _, ext = os.path.splitext(filepath)
            if ext == ".md":
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
                components, relationships = await self.atomic_parser.parse_file(
                    filepath
                )

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
                    print(
                        f"   📊 Session: {session_result.get('session_id', 'unknown')}"
                    )
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
            elif ext in CODE_FILE_EXTENSIONS:
                # Process code file
                with open(filepath, encoding="utf-8") as f:
                    code = f.read()
                chunks, calls, imports = chunk_code_file(filepath)
                if not chunks:
                    print(f"\u26a0\ufe0f  No code chunks extracted from: {filepath}")
                    return False
                # Generate a session_id for this code file
                session_id = f"code_{abs(hash(filepath))}_{int(time.time())}"
                components = []
                relationships = []
                # --- NEW: Create file node ---
                file_node_id = f"{filepath}#file"
                file_node = CodeChunkComponent(
                    {
                        "component_type": "file",
                        "file_path": filepath,
                        "language": ext.lstrip("."),
                        "session_id": session_id,
                        "created": datetime.now(timezone.utc).isoformat(),
                        "updated": datetime.now(timezone.utc).isoformat(),
                        "_key": file_node_id.replace("/", "_"),
                        "name": Path(filepath).name,
                    }
                )
                components.append(file_node)
                # --- END NEW ---
                chunk_name_to_key = {}
                for idx, chunk in enumerate(chunks):
                    component = dict(chunk)
                    component["component_type"] = "code_chunk"
                    component["file_path"] = filepath
                    component["language"] = ext.lstrip(".")
                    component["order"] = idx
                    component["session_id"] = session_id
                    # Give each chunk a unique _key
                    component["_key"] = f"{filepath}#chunk{idx}".replace("/", "_")
                    chunk_name_to_key[component["name"]] = component["_key"]
                    components.append(CodeChunkComponent(component))
                    # --- NEW: Relationship from chunk to file node ---
                    relationships.append(
                        CodeChunkRelationship(
                            {
                                "from": f"{filepath}#chunk{idx}",
                                "to": file_node_id,
                                "type": "belongs_to_file",
                            }
                        )
                    )
                    # --- END NEW ---
                # --- NEW: Add 'calls' relationships between code chunks ---
                for caller, callee in calls:
                    if caller in chunk_name_to_key and callee in chunk_name_to_key:
                        relationships.append(
                            CodeChunkRelationship(
                                {
                                    "from": chunk_name_to_key[caller],
                                    "to": chunk_name_to_key[callee],
                                    "type": "calls",
                                }
                            )
                        )
                # --- NEW: Add 'imports' relationships from file node to imported modules/files ---
                for imported in imports:
                    # Assume imported is a module name; try to find a file node for it
                    imported_file_node_id = None
                    # Try .py file in same directory
                    imported_path = str(Path(filepath).parent / (imported + ".py"))
                    imported_file_node_id = f"{imported_path}#file"
                    relationships.append(
                        CodeChunkRelationship(
                            {
                                "from": file_node_id,
                                "to": imported_file_node_id,
                                "type": "imports",
                            }
                        )
                    )
                # Store in database (reuse storage logic, adapt as needed)
                session_result = await self.db_storage.store_parsed_file(
                    file_path=filepath,
                    components=components,
                    relationships=relationships,
                    metadata={"ingestion_type": "code"},
                )
                if session_result.get("success"):
                    self.file_states[filepath] = self.get_file_stats(filepath)
                    self.save_state()
                    self.stats["files_processed"] += 1
                    self.stats["components_created"] += len(components)
                    self.stats["relationships_created"] += len(relationships)
                    print(f"\u2705 Loaded code file: {Path(filepath).name}")
                    return True
                else:
                    print(f"\u274c Failed to store code file: {filepath}")
                    print(f"   Error: {session_result.get('error', 'Unknown error')}")
                    self.stats["errors"] += 1
                    return False
            else:
                print(f"\u23ed\ufe0f  Unsupported file type: {filepath}")
                return False
        except Exception as e:
            print(f"\U0001f4a5 Error processing {filepath}: {e}")
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
        """Scan and process all existing files in history directory with progress indicator (recursive, with ignore patterns)"""
        if not self.history_dir.exists():
            print(f"⚠️  History directory does not exist: {self.history_dir}")
            return

        # Directories to ignore (gitignore-style)
        IGNORE_DIRS = {
            ".git",
            "venv",
            ".venv",
            "node_modules",
            "__pycache__",
            "dist",
            "build",
        }
        IGNORE_SUFFIXES = (".egg-info",)

        # Recursive scan for .md and code files
        files = list(self.history_dir.rglob("*.md"))
        for ext in CODE_FILE_EXTENSIONS:
            files.extend(self.history_dir.rglob(f"*{ext}"))

        # Filter out files in ignored directories or with ignored suffixes
        def is_ignored(path):
            parts = set(path.parts)
            if parts & IGNORE_DIRS:
                return True
            for part in path.parts:
                if part.endswith(IGNORE_SUFFIXES):
                    return True
            return False

        files = [f for f in files if not is_ignored(f)]

        print(f"🔍 Found {len(files)} files (markdown + code, recursive, filtered)")

        processed = 0
        skipped = 0

        iterator = (
            tqdm(files, desc="Processing files", unit="file")
            if TQDM_AVAILABLE
            else files
        )
        total = len(files)
        for idx, filepath in enumerate(iterator, 1):
            filepath_str = str(filepath)

            if self.has_file_changed(filepath_str):
                if await self.process_file(filepath_str):
                    processed += 1
                else:
                    print(f"⚠️  Failed to process: {filepath.name}")
            else:
                print(f"⚡ Already processed: {filepath.name}")
                skipped += 1

            if not TQDM_AVAILABLE:
                # Simple progress display
                percent = (idx / total) * 100 if total else 100
                sys.stdout.write(f"\rProgress: {idx}/{total} ({percent:.1f}%)")
                sys.stdout.flush()
        if not TQDM_AVAILABLE:
            print()  # Newline after progress

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
                collections = self.db_client.list_collections()
                print(f"✅ Database connected successfully. Collections: {collections}")
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
            collections = self.db_client.list_collections()
            print(f"   🗄️  Database: ✅ Connected. Collections: {collections}")
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
        default=".specstory/history",
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
    # Ensure project root and app root are in sys.path for direct execution
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    app_root = current_file.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(app_root) not in sys.path:
        sys.path.insert(0, str(app_root))
    # Also add shared interfaces path
    shared_db_path = project_root / "src" / "shared" / "interfaces" / "database"
    if str(shared_db_path) not in sys.path:
        sys.path.insert(0, str(shared_db_path))
    main()
