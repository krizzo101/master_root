"""
Comprehensive Context Items Populator for Unified Context System.

This script populates the context_items table from all available data sources:
- .proj-intel data (code intelligence)
- Chat logs (SQLite database + text files)
- Monitoring metrics
- IDE context snapshots
- System events

Features:
- Batch processing for large datasets
- Data validation and deduplication
- Progress tracking and error handling
- Flexible source configuration
- Resumable ingestion
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import asyncpg
import psycopg2
from psycopg2.extras import Json

# Add project root to path
sys.path.insert(0, "/home/opsvi/master_root")

from scripts.proj_intel_reader import ProjectIntelReader


class ContextItemsPopulator:
    """
    Comprehensive populator for the context_items table.
    Ingests data from all sources into the unified PostgreSQL schema.
    """

    def __init__(
        self,
        postgres_url: str = "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        batch_size: int = 1000,
        max_workers: int = 5,
        resume_from_checkpoint: bool = True,
    ):
        self.postgres_url = postgres_url
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.resume_from_checkpoint = resume_from_checkpoint

        # Database connections
        self.pg_conn = psycopg2.connect(postgres_url)
        self.pg_conn.autocommit = True
        self.pg_pool = None

        # Data sources configuration
        self.data_sources = {
            "proj_intel": {
                "paths": [
                    "/home/opsvi/master_root/.proj-intel",
                    "/home/opsvi/master_root/libs/.proj-intel",
                    "/home/opsvi/master_root/apps/hecaton/.proj-intel",
                    "/home/opsvi/master_root/apps/tetra/.proj-intel",
                ],
                "enabled": True,
                "priority": 1,
            },
            "chat_logs": {
                "sqlite_path": "/home/opsvi/master_root/chat_logs.db",
                "text_logs": [
                    "/home/opsvi/master_root/chat_improvement_log.txt",
                    "/home/opsvi/master_root/dashboard_chat_log.txt",
                    "/home/opsvi/master_root/unified_context_chat_log.txt",
                ],
                "enabled": True,
                "priority": 2,
            },
            "monitoring": {
                "log_paths": [
                    "/home/opsvi/master_root/apps/knowledge_system/ingestion_monitor.log",
                ],
                "enabled": True,
                "priority": 3,
            },
            "ide_context": {
                "enabled": False,  # Enable when IDE bridge is active
                "priority": 4,
            },
        }

        # Processing statistics
        self.stats = {
            "total_processed": 0,
            "total_inserted": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "sources_processed": set(),
            "start_time": datetime.now(),
            "last_checkpoint": None,
        }

        # Deduplication tracking
        self.processed_hashes: Set[str] = set()
        self.checkpoint_file = "/tmp/context_items_checkpoint.json"

    async def init_async(self):
        """Initialize async PostgreSQL pool for batch operations."""
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_url, min_size=self.max_workers, max_size=self.max_workers * 2
        )

    async def close_async(self):
        """Close async connections."""
        if self.pg_pool:
            await self.pg_pool.close()

    def close(self):
        """Close sync connections."""
        if self.pg_conn:
            self.pg_conn.close()

    # ============================================
    # CHECKPOINT & RESUME FUNCTIONALITY
    # ============================================

    def load_checkpoint(self) -> Dict[str, Any]:
        """Load processing checkpoint from disk."""
        if not self.resume_from_checkpoint or not Path(self.checkpoint_file).exists():
            return {}

        try:
            with open(self.checkpoint_file, "r") as f:
                checkpoint = json.load(f)
                self.processed_hashes = set(checkpoint.get("processed_hashes", []))
                print(
                    f"📋 Loaded checkpoint with {len(self.processed_hashes)} processed items"
                )
                return checkpoint
        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            return {}

    def save_checkpoint(self):
        """Save current processing state to checkpoint file."""
        try:
            checkpoint = {
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats.copy(),
                "processed_hashes": list(self.processed_hashes),
            }
            # Convert set to list for JSON serialization
            checkpoint["stats"]["sources_processed"] = list(
                self.stats["sources_processed"]
            )

            with open(self.checkpoint_file, "w") as f:
                json.dump(checkpoint, f, indent=2, default=str)

            self.stats["last_checkpoint"] = datetime.now()
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")

    # ============================================
    # DATA VALIDATION & DEDUPLICATION
    # ============================================

    def generate_content_hash(
        self, content: str, source_id: str, timestamp: datetime
    ) -> str:
        """Generate a unique hash for content deduplication."""
        hash_input = f"{content}:{source_id}:{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]

    def is_duplicate(self, content_hash: str) -> bool:
        """Check if content has already been processed."""
        return content_hash in self.processed_hashes

    def validate_context_item(self, item: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate a context item before insertion."""
        required_fields = ["source_type", "source_id", "entity_type", "timestamp"]

        for field in required_fields:
            if field not in item or item[field] is None:
                return False, f"Missing required field: {field}"

        # Validate timestamp
        if not isinstance(item["timestamp"], datetime):
            return False, "Timestamp must be datetime object"

        # Validate content length
        content = item.get("content", "")
        if len(content) > 100000:  # 100KB limit
            item["content"] = content[:100000] + "... [truncated]"
            item["summary"] = f"Large content truncated from {len(content)} chars"

        return True, None

    # ============================================
    # PROJ-INTEL DATA INGESTION
    # ============================================

    async def ingest_proj_intel_data(self) -> int:
        """Ingest all .proj-intel data into context_items."""
        print("🔄 Starting .proj-intel data ingestion...")
        items_ingested = 0

        for proj_intel_path in self.data_sources["proj_intel"]["paths"]:
            if not Path(proj_intel_path).exists():
                print(f"⚠️  Path not found: {proj_intel_path}")
                continue

            print(f"   Processing: {proj_intel_path}")
            items_ingested += await self._process_proj_intel_directory(proj_intel_path)

        self.stats["sources_processed"].add("proj_intel")
        return items_ingested

    async def _process_proj_intel_directory(self, proj_intel_path: str) -> int:
        """Process a single .proj-intel directory."""
        try:
            reader = ProjectIntelReader(proj_intel_path)
            items_to_insert = []
            items_processed = 0

            for file_path in reader.reverse_index.keys():
                try:
                    items = reader.read_by_path(file_path)

                    for item in items:
                        context_item = self._convert_proj_intel_to_context_item(
                            item, file_path, proj_intel_path
                        )

                        if context_item:
                            is_valid, error = self.validate_context_item(context_item)
                            if not is_valid:
                                print(f"❌ Invalid item: {error}")
                                self.stats["total_errors"] += 1
                                continue

                            content_hash = context_item["content_hash"]
                            if self.is_duplicate(content_hash):
                                self.stats["total_skipped"] += 1
                                continue

                            items_to_insert.append(context_item)
                            self.processed_hashes.add(content_hash)

                            # Batch insert
                            if len(items_to_insert) >= self.batch_size:
                                await self._batch_insert_context_items(items_to_insert)
                                items_processed += len(items_to_insert)
                                items_to_insert = []

                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")
                    self.stats["total_errors"] += 1

            # Insert remaining items
            if items_to_insert:
                await self._batch_insert_context_items(items_to_insert)
                items_processed += len(items_to_insert)

            return items_processed

        except Exception as e:
            print(f"❌ Error processing directory {proj_intel_path}: {e}")
            self.stats["total_errors"] += 1
            return 0

    def _convert_proj_intel_to_context_item(
        self, item: Dict, file_path: str, proj_intel_path: str
    ) -> Optional[Dict]:
        """Convert .proj-intel item to context_items format."""
        try:
            collector = item.get("collector", "")
            data = item.get("data", {})
            timestamp = item.get("timestamp")

            if not timestamp:
                # Use file modification time as fallback
                try:
                    mtime = os.path.getmtime(file_path)
                    timestamp = datetime.fromtimestamp(mtime)
                except:
                    timestamp = datetime.now()
            elif isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    timestamp = datetime.now()

            # Create unique source_id including data content for uniqueness
            data_signature = hashlib.md5(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()[:8]
            source_id = hashlib.md5(
                f"{file_path}:{collector}:{timestamp}:{data_signature}".encode()
            ).hexdigest()

            # Generate content for searchability
            content_parts = []
            if collector:
                content_parts.append(f"Collector: {collector}")

            if "functions" in data:
                functions = [f.get("name", "unknown") for f in data["functions"]]
                content_parts.append(f"Functions: {', '.join(functions[:10])}")

            if "classes" in data:
                classes = [c.get("name", "unknown") for c in data["classes"]]
                content_parts.append(f"Classes: {', '.join(classes[:10])}")

            if "imports" in data:
                imports = [
                    i.get("name", i.get("module", "unknown")) for i in data["imports"]
                ]
                content_parts.append(f"Imports: {', '.join(imports[:10])}")

            content = (
                "; ".join(content_parts)
                if content_parts
                else json.dumps(data, indent=2)
            )

            content_hash = self.generate_content_hash(content, source_id, timestamp)

            return {
                "source_type": "code",
                "source_id": source_id,
                "entity_type": collector.lower().replace("collector", "")
                if collector
                else "unknown",
                "timestamp": timestamp,
                "title": f"{collector}: {Path(file_path).name}",
                "content": content,
                "content_hash": content_hash,
                "file_path": file_path,
                "project_id": Path(proj_intel_path).parent.name,
                "metrics": {
                    "collector": collector,
                    "data_size": len(json.dumps(data)),
                    "function_count": len(data.get("functions", [])),
                    "class_count": len(data.get("classes", [])),
                    "import_count": len(data.get("imports", [])),
                },
                "source_data": data,
                "tags": ["proj-intel", collector.lower() if collector else "unknown"],
            }

        except Exception as e:
            print(f"❌ Error converting proj-intel item: {e}")
            return None

    # ============================================
    # CHAT LOGS INGESTION
    # ============================================

    async def ingest_chat_logs(self) -> int:
        """Ingest chat logs from SQLite database and text files."""
        print("🔄 Starting chat logs ingestion...")
        total_ingested = 0

        # Process SQLite database
        if Path(self.data_sources["chat_logs"]["sqlite_path"]).exists():
            total_ingested += await self._process_sqlite_chat_logs()

        # Process text log files
        for log_file in self.data_sources["chat_logs"]["text_logs"]:
            if Path(log_file).exists():
                total_ingested += await self._process_text_chat_log(log_file)

        self.stats["sources_processed"].add("chat_logs")
        return total_ingested

    async def _process_sqlite_chat_logs(self) -> int:
        """Process chat logs from SQLite database."""
        try:
            sqlite_path = self.data_sources["chat_logs"]["sqlite_path"]
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            items_to_insert = []
            items_processed = 0

            for table in tables:
                try:
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()

                    for row in rows:
                        context_item = self._convert_sqlite_row_to_context_item(
                            dict(row), table, sqlite_path
                        )

                        if context_item:
                            is_valid, error = self.validate_context_item(context_item)
                            if not is_valid:
                                self.stats["total_errors"] += 1
                                continue

                            content_hash = context_item["content_hash"]
                            if self.is_duplicate(content_hash):
                                self.stats["total_skipped"] += 1
                                continue

                            items_to_insert.append(context_item)
                            self.processed_hashes.add(content_hash)

                            # Batch insert
                            if len(items_to_insert) >= self.batch_size:
                                await self._batch_insert_context_items(items_to_insert)
                                items_processed += len(items_to_insert)
                                items_to_insert = []

                except Exception as e:
                    print(f"❌ Error processing table {table}: {e}")
                    self.stats["total_errors"] += 1

            # Insert remaining items
            if items_to_insert:
                await self._batch_insert_context_items(items_to_insert)
                items_processed += len(items_to_insert)

            conn.close()
            return items_processed

        except Exception as e:
            print(f"❌ Error processing SQLite chat logs: {e}")
            self.stats["total_errors"] += 1
            return 0

    def _convert_sqlite_row_to_context_item(
        self, row: Dict, table_name: str, sqlite_path: str
    ) -> Optional[Dict]:
        """Convert SQLite row to context_items format."""
        try:
            # Handle different table schemas
            timestamp = None
            content = ""
            source_id = ""

            # Extract timestamp (try different field names)
            for ts_field in ["timestamp", "created_at", "started_at", "time"]:
                if ts_field in row and row[ts_field]:
                    try:
                        if isinstance(row[ts_field], str):
                            timestamp = datetime.fromisoformat(
                                row[ts_field].replace("Z", "+00:00")
                            )
                        else:
                            timestamp = datetime.fromtimestamp(row[ts_field])
                        break
                    except:
                        continue

            if not timestamp:
                timestamp = datetime.now()

            # Extract content and source_id based on table type
            if table_name == "chat_sessions":
                source_id = row.get("id", str(hash(str(row))))
                content = f"Session: {source_id}, Project: {row.get('project_path', 'unknown')}"
                if row.get("model_used"):
                    content += f", Model: {row['model_used']}"

            elif table_name in ["messages", "chat_messages"]:
                source_id = row.get("id", row.get("message_id", str(hash(str(row)))))
                content = row.get("content", row.get("message", ""))
                if len(content) > 1000:
                    content = content[:1000] + "... [truncated]"

            else:
                # Generic handling
                source_id = row.get("id", str(hash(str(row))))
                content = json.dumps(row, default=str, indent=2)

            content_hash = self.generate_content_hash(content, source_id, timestamp)

            return {
                "source_type": "chat",
                "source_id": source_id,
                "entity_type": table_name,
                "timestamp": timestamp,
                "title": f"{table_name}: {source_id}",
                "content": content,
                "content_hash": content_hash,
                "session_id": row.get("session_id", row.get("id")),
                "actor_type": "human" if "user" in str(row).lower() else "ai",
                "metrics": {
                    "table": table_name,
                    "row_size": len(str(row)),
                    "tokens": row.get("total_tokens", row.get("tokens_used")),
                    "cost": row.get("total_cost", row.get("cost")),
                },
                "source_data": row,
                "tags": ["chat", table_name, "sqlite"],
            }

        except Exception as e:
            print(f"❌ Error converting SQLite row: {e}")
            return None

    async def _process_text_chat_log(self, log_file_path: str) -> int:
        """Process a text-based chat log file."""
        try:
            print(f"   Processing text log: {log_file_path}")
            items_to_insert = []

            with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Split into logical chunks (by timestamp patterns, user/assistant, etc.)
            chunks = self._split_chat_log_content(content)

            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 10:  # Skip very short chunks
                    continue

                # Extract or generate timestamp
                timestamp = self._extract_timestamp_from_chunk(chunk) or datetime.now()

                source_id = hashlib.md5(f"{log_file_path}:{i}".encode()).hexdigest()[
                    :12
                ]
                content_hash = self.generate_content_hash(chunk, source_id, timestamp)

                if self.is_duplicate(content_hash):
                    self.stats["total_skipped"] += 1
                    continue

                context_item = {
                    "source_type": "chat",
                    "source_id": source_id,
                    "entity_type": "text_log",
                    "timestamp": timestamp,
                    "title": f"Chat Log: {Path(log_file_path).name}:{i}",
                    "content": chunk[:5000],  # Limit content size
                    "content_hash": content_hash,
                    "file_path": log_file_path,
                    "actor_type": self._detect_actor_type(chunk),
                    "metrics": {
                        "chunk_index": i,
                        "chunk_size": len(chunk),
                        "log_file": Path(log_file_path).name,
                    },
                    "source_data": {"chunk": chunk},
                    "tags": ["chat", "text-log", Path(log_file_path).stem],
                }

                is_valid, error = self.validate_context_item(context_item)
                if not is_valid:
                    self.stats["total_errors"] += 1
                    continue

                items_to_insert.append(context_item)
                self.processed_hashes.add(content_hash)

                # Batch insert
                if len(items_to_insert) >= self.batch_size:
                    await self._batch_insert_context_items(items_to_insert)
                    items_to_insert = []

            # Insert remaining items
            if items_to_insert:
                await self._batch_insert_context_items(items_to_insert)

            return len(chunks)

        except Exception as e:
            print(f"❌ Error processing text chat log {log_file_path}: {e}")
            self.stats["total_errors"] += 1
            return 0

    def _split_chat_log_content(self, content: str) -> List[str]:
        """Split chat log content into logical chunks."""
        # Split by common patterns: timestamps, user/assistant markers, etc.
        import re

        # Try to split by timestamp patterns first
        timestamp_pattern = r"\d{4}-\d{2}-\d{2}[\s\tT]\d{2}:\d{2}:\d{2}"
        chunks = re.split(timestamp_pattern, content)

        if len(chunks) > 1:
            return [chunk.strip() for chunk in chunks if chunk.strip()]

        # Fallback: split by user/assistant patterns
        user_patterns = [r"\nUser:", r"\nHuman:", r"\nuser:", r"\nhuman:"]
        assistant_patterns = [
            r"\nAssistant:",
            r"\nClaude:",
            r"\nassistant:",
            r"\nclaude:",
        ]

        for pattern in user_patterns + assistant_patterns:
            chunks = re.split(pattern, content)
            if len(chunks) > 1:
                return [chunk.strip() for chunk in chunks if chunk.strip()]

        # Final fallback: split by double newlines
        chunks = content.split("\n\n")
        return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 10]

    def _extract_timestamp_from_chunk(self, chunk: str) -> Optional[datetime]:
        """Extract timestamp from a text chunk."""
        import re

        # Common timestamp patterns
        patterns = [
            r"(\d{4}-\d{2}-\d{2}[\s\tT]\d{2}:\d{2}:\d{2})",
            r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})",
            r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, chunk[:200])  # Look in first 200 chars
            if match:
                try:
                    ts_str = match.group(1)
                    return datetime.fromisoformat(ts_str.replace("T", " "))
                except:
                    continue

        return None

    def _detect_actor_type(self, chunk: str) -> str:
        """Detect if chunk is from human, AI, or system."""
        chunk_lower = chunk.lower()

        if any(
            word in chunk_lower
            for word in ["user:", "human:", "you:", "i need", "can you"]
        ):
            return "human"
        elif any(
            word in chunk_lower for word in ["assistant:", "claude:", "i'll", "let me"]
        ):
            return "ai"
        else:
            return "system"

    # ============================================
    # MONITORING DATA INGESTION
    # ============================================

    async def ingest_monitoring_data(self) -> int:
        """Ingest monitoring and system metrics."""
        print("🔄 Starting monitoring data ingestion...")
        total_ingested = 0

        for log_path in self.data_sources["monitoring"]["log_paths"]:
            if Path(log_path).exists():
                total_ingested += await self._process_monitoring_log(log_path)

        # Add system metrics
        total_ingested += await self._collect_system_metrics()

        self.stats["sources_processed"].add("monitoring")
        return total_ingested

    async def _process_monitoring_log(self, log_path: str) -> int:
        """Process a monitoring log file."""
        try:
            print(f"   Processing monitoring log: {log_path}")
            items_to_insert = []

            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for i, line in enumerate(lines):
                if len(line.strip()) < 10:
                    continue

                timestamp = datetime.now() - timedelta(
                    minutes=len(lines) - i
                )  # Approximate timing
                source_id = (
                    f"monitor_{hashlib.md5(f'{log_path}:{i}'.encode()).hexdigest()[:8]}"
                )

                content_hash = self.generate_content_hash(line, source_id, timestamp)

                if self.is_duplicate(content_hash):
                    self.stats["total_skipped"] += 1
                    continue

                # Extract metrics from log line
                metrics = self._parse_log_metrics(line)

                context_item = {
                    "source_type": "monitor",
                    "source_id": source_id,
                    "entity_type": "log_entry",
                    "timestamp": timestamp,
                    "title": f"Monitor: {Path(log_path).name}",
                    "content": line.strip(),
                    "content_hash": content_hash,
                    "file_path": log_path,
                    "severity": self._detect_log_severity(line),
                    "metrics": metrics,
                    "source_data": {"log_line": line.strip(), "line_number": i},
                    "tags": ["monitoring", "log", Path(log_path).stem],
                }

                is_valid, error = self.validate_context_item(context_item)
                if not is_valid:
                    self.stats["total_errors"] += 1
                    continue

                items_to_insert.append(context_item)
                self.processed_hashes.add(content_hash)

                # Batch insert
                if len(items_to_insert) >= self.batch_size:
                    await self._batch_insert_context_items(items_to_insert)
                    items_to_insert = []

            # Insert remaining items
            if items_to_insert:
                await self._batch_insert_context_items(items_to_insert)

            return len(lines)

        except Exception as e:
            print(f"❌ Error processing monitoring log {log_path}: {e}")
            self.stats["total_errors"] += 1
            return 0

    def _parse_log_metrics(self, log_line: str) -> Dict[str, Any]:
        """Extract metrics from a log line."""
        import re

        metrics = {}

        # Look for numeric values
        numbers = re.findall(r"(\d+\.?\d*)", log_line)
        if numbers:
            metrics["numeric_values"] = [float(n) for n in numbers]

        # Look for common metric patterns
        if "error" in log_line.lower():
            metrics["error_count"] = 1
        if "warning" in log_line.lower():
            metrics["warning_count"] = 1
        if "mb" in log_line.lower() or "memory" in log_line.lower():
            metrics["memory_related"] = True
        if "cpu" in log_line.lower() or "%cpu" in log_line.lower():
            metrics["cpu_related"] = True

        return metrics

    def _detect_log_severity(self, log_line: str) -> str:
        """Detect severity level from log line."""
        line_lower = log_line.lower()

        if any(word in line_lower for word in ["error", "fail", "fatal", "critical"]):
            return "error"
        elif any(word in line_lower for word in ["warn", "warning"]):
            return "warning"
        elif any(word in line_lower for word in ["info", "information"]):
            return "info"
        elif any(word in line_lower for word in ["debug", "trace"]):
            return "debug"
        else:
            return "info"

    async def _collect_system_metrics(self) -> int:
        """Collect current system metrics as context items."""
        try:
            import psutil

            timestamp = datetime.now()
            metrics_data = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
            }

            source_id = f"system_metrics_{int(timestamp.timestamp())}"
            content = json.dumps(metrics_data, indent=2)
            content_hash = self.generate_content_hash(content, source_id, timestamp)

            if self.is_duplicate(content_hash):
                return 0

            context_item = {
                "source_type": "system",
                "source_id": source_id,
                "entity_type": "metrics",
                "timestamp": timestamp,
                "title": "System Metrics Snapshot",
                "content": content,
                "content_hash": content_hash,
                "metrics": metrics_data,
                "source_data": metrics_data,
                "tags": ["system", "metrics", "snapshot"],
            }

            is_valid, error = self.validate_context_item(context_item)
            if is_valid:
                await self._batch_insert_context_items([context_item])
                self.processed_hashes.add(content_hash)
                return 1

            return 0

        except ImportError:
            print("⚠️  psutil not available, skipping system metrics")
            return 0
        except Exception as e:
            print(f"❌ Error collecting system metrics: {e}")
            return 0

    # ============================================
    # BATCH INSERTION & DATABASE OPERATIONS
    # ============================================

    async def _batch_insert_context_items(self, items: List[Dict[str, Any]]):
        """Batch insert context items using asyncpg COPY with duplicate handling."""
        if not items:
            return

        if not self.pg_pool:
            await self.init_async()

        try:
            async with self.pg_pool.acquire() as conn:
                # Use individual INSERT ON CONFLICT for better duplicate handling
                successful_inserts = 0

                for item in items:
                    try:
                        result = await conn.execute(
                            """
                            INSERT INTO context_items (
                                source_type, source_id, entity_type, timestamp,
                                timestamp_end, title, content, content_hash,
                                summary, project_id, file_path, line_start,
                                line_end, function_name, class_name, actor_id,
                                actor_type, session_id, severity, tags,
                                metrics, source_data
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                                $11, $12, $13, $14, $15, $16, $17, $18,
                                $19, $20, $21, $22
                            )
                            ON CONFLICT (source_type, source_id) DO UPDATE SET
                                content = EXCLUDED.content,
                                content_hash = EXCLUDED.content_hash,
                                metrics = EXCLUDED.metrics,
                                source_data = EXCLUDED.source_data,
                                ingested_at = NOW()
                            """,
                            item["source_type"],
                            item["source_id"],
                            item["entity_type"],
                            item["timestamp"],
                            item.get("timestamp_end"),
                            item.get("title"),
                            item.get("content"),
                            item.get("content_hash"),
                            item.get("summary"),
                            item.get("project_id"),
                            item.get("file_path"),
                            item.get("line_start"),
                            item.get("line_end"),
                            item.get("function_name"),
                            item.get("class_name"),
                            item.get("actor_id"),
                            item.get("actor_type"),
                            item.get("session_id"),
                            item.get("severity"),
                            item.get("tags", []),
                            json.dumps(item.get("metrics", {})),
                            json.dumps(item.get("source_data", {})),
                        )
                        successful_inserts += 1

                    except Exception as item_error:
                        print(
                            f"   ⚠️  Failed to insert item {item['source_id']}: {item_error}"
                        )
                        self.stats["total_errors"] += 1

                self.stats["total_inserted"] += successful_inserts
                if successful_inserts > 0:
                    print(
                        f"   ✅ Batch inserted {successful_inserts}/{len(items)} context items"
                    )

        except Exception as e:
            print(f"❌ Batch insert failed: {e}")
            self.stats["total_errors"] += len(items)
            raise

    # ============================================
    # MAIN ORCHESTRATION
    # ============================================

    async def run_full_ingestion(self) -> Dict[str, Any]:
        """Run complete ingestion from all data sources."""
        print("🚀 Starting comprehensive context items population...")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Max workers: {self.max_workers}")
        print(f"   Resume from checkpoint: {self.resume_from_checkpoint}")

        # Load checkpoint
        checkpoint = self.load_checkpoint()

        try:
            await self.init_async()

            # Clear existing data if not resuming
            if not checkpoint:
                print("🗑️  Clearing existing context_items data...")
                await self._clear_existing_data()

            # Process each data source in priority order
            sources = sorted(
                self.data_sources.items(), key=lambda x: x[1].get("priority", 999)
            )

            for source_name, config in sources:
                if not config.get("enabled", False):
                    print(f"⏭️  Skipping disabled source: {source_name}")
                    continue

                if source_name in checkpoint.get("stats", {}).get(
                    "sources_processed", []
                ):
                    print(f"⏭️  Skipping completed source: {source_name}")
                    continue

                print(f"\n📊 Processing source: {source_name}")

                if source_name == "proj_intel":
                    await self.ingest_proj_intel_data()
                elif source_name == "chat_logs":
                    await self.ingest_chat_logs()
                elif source_name == "monitoring":
                    await self.ingest_monitoring_data()

                # Save checkpoint after each source
                self.save_checkpoint()

            # Final statistics and validation
            await self._generate_final_report()

            print("\n🎉 Context items population completed successfully!")
            return self.stats

        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
            import traceback

            traceback.print_exc()
            raise

        finally:
            await self.close_async()
            self.close()

    async def _clear_existing_data(self):
        """Clear existing context_items data (optional)."""
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM context_items WHERE source_type IN ('code', 'chat', 'monitor', 'system')"
            )
            print("   Cleared existing context_items data")

    async def _generate_final_report(self):
        """Generate final ingestion report with statistics."""
        print("\n📈 Final Ingestion Report:")
        print(f"   Total processed: {self.stats['total_processed']}")
        print(f"   Total inserted: {self.stats['total_inserted']}")
        print(f"   Total skipped (duplicates): {self.stats['total_skipped']}")
        print(f"   Total errors: {self.stats['total_errors']}")
        print(f"   Sources processed: {', '.join(self.stats['sources_processed'])}")

        duration = datetime.now() - self.stats["start_time"]
        print(f"   Total duration: {duration}")

        # Query final counts from database
        with self.pg_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT source_type, COUNT(*) as count
                FROM context_items
                GROUP BY source_type
                ORDER BY count DESC
            """
            )
            counts = cursor.fetchall()

        print("\n📊 Context items by source type:")
        for source_type, count in counts:
            print(f"   {source_type}: {count:,} items")


# ============================================
# CLI INTERFACE
# ============================================


async def main():
    """Main CLI interface for the context items populator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate context_items table from all sources"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for insertions"
    )
    parser.add_argument(
        "--max-workers", type=int, default=5, help="Maximum async workers"
    )
    parser.add_argument(
        "--no-resume", action="store_true", help="Don't resume from checkpoint"
    )
    parser.add_argument(
        "--clear-data", action="store_true", help="Clear existing data before ingestion"
    )
    parser.add_argument(
        "--postgres-url",
        default="postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        help="PostgreSQL connection URL",
    )

    args = parser.parse_args()

    populator = ContextItemsPopulator(
        postgres_url=args.postgres_url,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        resume_from_checkpoint=not args.no_resume,
    )

    try:
        stats = await populator.run_full_ingestion()
        print(f"\n✅ Ingestion completed successfully!")
        print(f"Final stats: {json.dumps(stats, indent=2, default=str)}")

    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
