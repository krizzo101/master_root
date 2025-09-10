"""
.proj-intel to PostgreSQL ingestion pipeline.
Imports project intelligence data into the code_elements table.
"""

import asyncio
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import psycopg2
from psycopg2.extras import Json

# Add project root to path
sys.path.insert(0, "/home/opsvi/master_root")

from scripts.proj_intel_reader import ProjectIntelReader


class ProjectIntelIngester:
    """Ingests .proj-intel data into PostgreSQL code_elements table."""

    def __init__(
        self,
        proj_intel_path: str = "/home/opsvi/master_root/.proj-intel",
        postgres_url: str = "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
    ):
        self.proj_intel_path = proj_intel_path
        self.postgres_url = postgres_url
        self.reader = ProjectIntelReader(proj_intel_path)

        # PostgreSQL connections
        self.pg_conn = psycopg2.connect(postgres_url)
        self.pg_conn.autocommit = True
        self.pg_pool = None

        # Statistics
        self.stats = {
            "files_processed": 0,
            "elements_inserted": 0,
            "errors": 0,
            "skipped": 0,
        }

    async def init_async(self):
        """Initialize async PostgreSQL pool for batch operations."""
        self.pg_pool = await asyncpg.create_pool(
            self.postgres_url, min_size=5, max_size=20
        )

    def ingest_file_elements(self, clear_existing: bool = False) -> Dict[str, int]:
        """Ingest FileElementsCollector data into code_elements table."""
        print("🔄 Starting file elements ingestion...")

        with self.pg_conn.cursor() as cursor:
            # Clear existing data to avoid duplicates (optional)
            if clear_existing:
                cursor.execute("DELETE FROM code_elements")
                print("🗑️  Cleared existing code_elements data")

            # Process all files with FileElementsCollector data
            for file_path in self.reader.reverse_index.keys():
                try:
                    self._process_file_elements(cursor, file_path)
                    self.stats["files_processed"] += 1

                    if self.stats["files_processed"] % 100 == 0:
                        print(f"   Processed {self.stats['files_processed']} files...")

                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")
                    self.stats["errors"] += 1

        print(f"✅ File elements ingestion complete!")
        print(f"   📊 Stats: {self.stats}")
        return self.stats

    def _process_file_elements(self, cursor, file_path: str):
        """Process file elements data for a single file."""
        items = self.reader.read_by_path(file_path)

        for item in items:
            data = item.get("data", {})

            # Check if this item has file elements data (functions, classes, imports)
            if any(key in data for key in ["functions", "classes", "imports"]):
                self._insert_file_elements(cursor, file_path, data)

    def _insert_file_elements(self, cursor, file_path: str, file_data: Dict[str, Any]):
        """Insert file elements into PostgreSQL."""
        # Extract file-level information
        language = file_data.get("language", "") or self._detect_language_from_path(
            file_path
        )
        line_count = file_data.get("line_count", 0)
        content_hash = file_data.get("content_hash", "")

        # Insert file-level element
        cursor.execute(
            """
            INSERT INTO code_elements (
                file_path, element_type, element_name, language,
                last_modified, content_hash, proj_intel_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_path, element_type, element_name, line_start)
            DO UPDATE SET
                content_hash = EXCLUDED.content_hash,
                proj_intel_data = EXCLUDED.proj_intel_data,
                last_modified = EXCLUDED.last_modified
        """,
            (
                file_path,
                "file",
                Path(file_path).name,
                language,
                datetime.now(),
                content_hash,
                Json(file_data),
            ),
        )
        self.stats["elements_inserted"] += 1

        # Insert functions
        for func in file_data.get("functions", []):
            self._insert_function_element(cursor, file_path, func, file_data)

        # Insert classes
        for cls in file_data.get("classes", []):
            self._insert_class_element(cursor, file_path, cls, file_data)

        # Insert imports
        for imp in file_data.get("imports", []):
            self._insert_import_element(cursor, file_path, imp, file_data)

    def _insert_function_element(
        self, cursor, file_path: str, func: Dict, file_data: Dict
    ):
        """Insert a function element."""
        try:
            cursor.execute(
                """
                INSERT INTO code_elements (
                    file_path, element_type, element_name, signature,
                    docstring, line_start, line_end, complexity_score,
                    language, proj_intel_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_path, element_type, element_name, line_start)
                DO UPDATE SET
                    signature = EXCLUDED.signature,
                    docstring = EXCLUDED.docstring,
                    complexity_score = EXCLUDED.complexity_score,
                    proj_intel_data = EXCLUDED.proj_intel_data
            """,
                (
                    file_path,
                    "function",
                    func.get("name", ""),
                    func.get("signature", ""),
                    func.get("docstring", ""),
                    func.get("line_start", 0),
                    func.get("line_end", 0),
                    func.get("complexity", 0),
                    file_data.get("language", ""),
                    Json(func),
                ),
            )
            self.stats["elements_inserted"] += 1

        except Exception as e:
            print(
                f"Warning: Failed to insert function {func.get('name', 'unknown')}: {e}"
            )
            self.stats["errors"] += 1

    def _insert_class_element(self, cursor, file_path: str, cls: Dict, file_data: Dict):
        """Insert a class element."""
        try:
            cursor.execute(
                """
                INSERT INTO code_elements (
                    file_path, element_type, element_name, signature,
                    docstring, line_start, line_end, language, proj_intel_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_path, element_type, element_name, line_start)
                DO UPDATE SET
                    signature = EXCLUDED.signature,
                    docstring = EXCLUDED.docstring,
                    proj_intel_data = EXCLUDED.proj_intel_data
            """,
                (
                    file_path,
                    "class",
                    cls.get("name", ""),
                    cls.get("signature", ""),
                    cls.get("docstring", ""),
                    cls.get("line_start", 0),
                    cls.get("line_end", 0),
                    file_data.get("language", ""),
                    Json(cls),
                ),
            )
            self.stats["elements_inserted"] += 1

        except Exception as e:
            print(f"Warning: Failed to insert class {cls.get('name', 'unknown')}: {e}")
            self.stats["errors"] += 1

    def _insert_import_element(
        self, cursor, file_path: str, imp: Dict, file_data: Dict
    ):
        """Insert an import element."""
        try:
            import_name = imp.get("name", "") or imp.get("module", "")
            if not import_name:
                return

            cursor.execute(
                """
                INSERT INTO code_elements (
                    file_path, element_type, element_name, signature,
                    line_start, language, proj_intel_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_path, element_type, element_name, line_start)
                DO UPDATE SET
                    signature = EXCLUDED.signature,
                    proj_intel_data = EXCLUDED.proj_intel_data
            """,
                (
                    file_path,
                    "import",
                    import_name,
                    imp.get("statement", ""),
                    imp.get("line_number", 0),
                    file_data.get("language", ""),
                    Json(imp),
                ),
            )
            self.stats["elements_inserted"] += 1

        except Exception as e:
            print(f"Warning: Failed to insert import {imp}: {e}")
            self.stats["errors"] += 1

    async def batch_ingest_context_items(self):
        """Ingest .proj-intel data into context_items table for unified queries."""
        if not self.pg_pool:
            await self.init_async()

        print("🔄 Starting batch ingestion to context_items...")

        items_to_insert = []

        # Process all .proj-intel data
        for file_path in self.reader.reverse_index.keys():
            try:
                items = self.reader.read_by_path(file_path)

                for item in items:
                    if item.get("kind") == "collector_item":
                        context_item = self._convert_to_context_item(item, file_path)
                        if context_item:
                            items_to_insert.append(context_item)

                        # Batch insert every 1000 items
                        if len(items_to_insert) >= 1000:
                            await self._batch_insert_context_items(items_to_insert)
                            items_to_insert = []

            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                self.stats["errors"] += 1

        # Insert remaining items
        if items_to_insert:
            await self._batch_insert_context_items(items_to_insert)

        print(
            f"✅ Context items ingestion complete! Inserted {self.stats['elements_inserted']} items"
        )

    def _convert_to_context_item(self, item: Dict, file_path: str) -> Optional[Dict]:
        """Convert .proj-intel item to context_items format."""
        collector = item.get("collector", "")
        data = item.get("data", {})
        timestamp = item.get("timestamp")

        if not timestamp:
            timestamp = datetime.now()
        elif isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()

        # Create unique source_id
        source_id = hashlib.md5(
            f"{file_path}:{collector}:{timestamp}".encode()
        ).hexdigest()

        return {
            "source_type": "code",
            "source_id": source_id,
            "entity_type": collector.lower().replace("collector", ""),
            "timestamp": timestamp,
            "title": f"{collector}: {Path(file_path).name}",
            "content": json.dumps(data, indent=2),
            "content_hash": hashlib.md5(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()[:16],
            "file_path": file_path,
            "metrics": {"collector": collector, "data_size": len(json.dumps(data))},
            "source_data": data,
            "tags": ["proj-intel", collector.lower()],
        }

    async def _batch_insert_context_items(self, items: List[Dict]):
        """Batch insert context items using asyncpg COPY."""
        if not items:
            return

        async with self.pg_pool.acquire() as conn:
            # Prepare records for COPY
            records = []
            for item in items:
                records.append(
                    (
                        item["source_type"],
                        item["source_id"],
                        item["entity_type"],
                        item["timestamp"],
                        item.get("title"),
                        item.get("content"),
                        item.get("content_hash"),
                        item.get("file_path"),
                        json.dumps(item.get("metrics", {})),
                        json.dumps(item.get("source_data", {})),
                        item.get("tags", []),
                    )
                )

            # Use COPY for high-performance batch insert
            await conn.copy_records_to_table(
                "context_items",
                records=records,
                columns=[
                    "source_type",
                    "source_id",
                    "entity_type",
                    "timestamp",
                    "title",
                    "content",
                    "content_hash",
                    "file_path",
                    "metrics",
                    "source_data",
                    "tags",
                ],
            )

            self.stats["elements_inserted"] += len(items)
            print(f"   Batch inserted {len(items)} context items")

    def validate_ingestion(self) -> Dict[str, Any]:
        """Validate the ingestion by running test queries."""
        print("🔍 Validating ingestion...")

        validation_results = {}

        with self.pg_conn.cursor() as cursor:
            # Count elements by type
            cursor.execute(
                """
                SELECT element_type, COUNT(*) as count
                FROM code_elements
                GROUP BY element_type
                ORDER BY count DESC
            """
            )

            validation_results["elements_by_type"] = dict(cursor.fetchall())

            # Count elements by language
            cursor.execute(
                """
                SELECT language, COUNT(*) as count
                FROM code_elements
                WHERE language != ''
                GROUP BY language
                ORDER BY count DESC
                LIMIT 10
            """
            )

            validation_results["elements_by_language"] = dict(cursor.fetchall())

            # Test JSONB queries
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM code_elements
                WHERE proj_intel_data ? 'functions'
            """
            )

            validation_results["files_with_functions"] = cursor.fetchone()[0]

            # Context items validation
            cursor.execute(
                """
                SELECT source_type, entity_type, COUNT(*) as count
                FROM context_items
                WHERE source_type = 'code'
                GROUP BY source_type, entity_type
                ORDER BY count DESC
            """
            )

            validation_results["context_items"] = [
                {"source_type": row[0], "entity_type": row[1], "count": row[2]}
                for row in cursor.fetchall()
            ]

        print("✅ Validation complete:")
        for key, value in validation_results.items():
            print(f"   {key}: {value}")

        return validation_results

    def _detect_language_from_path(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()

        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".sh": "bash",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".md": "markdown",
            ".txt": "text",
        }

        return language_map.get(ext, "unknown")

    def close(self):
        """Close connections."""
        if self.pg_conn:
            self.pg_conn.close()

    async def close_async(self):
        """Close async connections."""
        if self.pg_pool:
            await self.pg_pool.close()


async def main():
    """Main ingestion workflow."""
    print("🚀 Starting .proj-intel to PostgreSQL ingestion")

    ingester = ProjectIntelIngester()

    try:
        # Phase 1: Ingest file elements
        stats = ingester.ingest_file_elements()

        # Phase 2: Batch ingest to context_items
        await ingester.batch_ingest_context_items()

        # Phase 3: Validate ingestion
        validation = ingester.validate_ingestion()

        print(f"\n🎉 Ingestion complete!")
        print(f"   📊 Final stats: {stats}")

    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        import traceback

        traceback.print_exc()

    finally:
        ingester.close()
        await ingester.close_async()


if __name__ == "__main__":
    asyncio.run(main())
