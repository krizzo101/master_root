#!/usr/bin/env python3
"""
Entity Extraction Pipeline for Chat Taxonomy
Implements comprehensive entity extraction from chat messages to enable semantic search
"""

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import asyncpg


@dataclass
class ExtractedEntity:
    """Represents a single extracted entity"""

    entity_type: str
    entity_value: str
    start_position: int
    end_position: int
    confidence: float = 1.0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EntityExtractor:
    """Core entity extraction engine"""

    def __init__(self):
        self.extractors = {
            "url": self._extract_urls,
            "file_path": self._extract_file_paths,
            "command": self._extract_commands,
            "email": self._extract_emails,
            "code_block": self._extract_code_blocks,
            "issue_reference": self._extract_issue_references,
            "user_mention": self._extract_user_mentions,
            "tech_keyword": self._extract_tech_keywords,
            "timestamp": self._extract_timestamps,
        }

        # Tech keywords - extensible list
        self.tech_keywords = {
            "python",
            "javascript",
            "typescript",
            "java",
            "cpp",
            "rust",
            "go",
            "docker",
            "kubernetes",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "aws",
            "azure",
            "gcp",
            "github",
            "gitlab",
            "jenkins",
            "nginx",
            "react",
            "vue",
            "angular",
            "node",
            "npm",
            "pip",
            "conda",
            "linux",
            "ubuntu",
            "debian",
            "centos",
            "macos",
            "windows",
            "api",
            "rest",
            "graphql",
            "websocket",
            "json",
            "xml",
            "yaml",
            "git",
            "svn",
            "mercurial",
            "bash",
            "zsh",
            "powershell",
            "claude",
            "openai",
            "anthropic",
            "gpt",
            "llm",
            "ai",
            "ml",
        }

    def extract_all(self, text: str) -> List[ExtractedEntity]:
        """Extract all entity types from text"""
        entities = []

        for entity_type, extractor in self.extractors.items():
            try:
                extracted = extractor(text)
                entities.extend(extracted)
            except Exception as e:
                print(f"Warning: Error extracting {entity_type}: {e}")

        # Sort by position for consistency
        entities.sort(key=lambda e: e.start_position)
        return entities

    def _extract_urls(self, text: str) -> List[ExtractedEntity]:
        """Extract HTTP/HTTPS URLs"""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        entities = []

        for match in re.finditer(pattern, text, re.IGNORECASE):
            url = match.group()
            entities.append(
                ExtractedEntity(
                    entity_type="url",
                    entity_value=url,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=0.95,
                    metadata={"domain": self._extract_domain(url)},
                )
            )

        return entities

    def _extract_file_paths(self, text: str) -> List[ExtractedEntity]:
        """Extract Unix/Windows file paths"""
        patterns = [
            r'(?:^|[\s"\'`])((?:/[^/\s"\'`<>|*?]+)+/?)',  # Unix absolute paths
            r'(?:^|[\s"\'`])((?:\./[^/\s"\'`<>|*?]+)+/?)',  # Unix relative paths
            r'(?:^|[\s"\'`])((?:[A-Za-z]:\\[^\\/:*?"<>|\s]+(?:\\[^\\/:*?"<>|\s]+)*\\?))',  # Windows paths
            r'(?:^|[\s"\'`])((?:[^/\\:\s"\'`<>|*?]+/[^/\s"\'`<>|*?]+)+/?)',  # General paths
        ]

        entities = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                path = match.group(1)
                # Filter common false positives
                if self._is_valid_path(path):
                    entities.append(
                        ExtractedEntity(
                            entity_type="file_path",
                            entity_value=path,
                            start_position=match.start(1),
                            end_position=match.end(1),
                            confidence=0.85,
                            metadata={
                                "path_type": "absolute"
                                if path.startswith("/")
                                or (len(path) > 1 and path[1] == ":")
                                else "relative",
                                "extension": Path(path).suffix
                                if Path(path).suffix
                                else None,
                            },
                        )
                    )

        return entities

    def _extract_commands(self, text: str) -> List[ExtractedEntity]:
        """Extract shell commands and tool calls"""
        patterns = [
            r"(?:^|[\n])\s*\$\s*([^\n]+)",  # $ prefixed commands
            r"(?:^|[\n])\s*>\s*([^\n]+)",  # > prefixed commands
            r"(?:^|[\s])((?:npm|pip|git|docker|kubectl|python|node|java|cargo|go)\s+[^\n]+)",  # Common tools
            r"`([^`]+)`",  # Backticked commands
        ]

        entities = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                command = match.group(1).strip()
                if len(command) > 2:  # Filter very short matches
                    entities.append(
                        ExtractedEntity(
                            entity_type="command",
                            entity_value=command,
                            start_position=match.start(1),
                            end_position=match.end(1),
                            confidence=0.80,
                            metadata={
                                "tool": command.split()[0] if command.split() else None
                            },
                        )
                    )

        return entities

    def _extract_emails(self, text: str) -> List[ExtractedEntity]:
        """Extract email addresses"""
        pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        entities = []

        for match in re.finditer(pattern, text):
            email = match.group()
            entities.append(
                ExtractedEntity(
                    entity_type="email",
                    entity_value=email,
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=0.95,
                    metadata={"domain": email.split("@")[1] if "@" in email else None},
                )
            )

        return entities

    def _extract_code_blocks(self, text: str) -> List[ExtractedEntity]:
        """Extract code blocks (fenced and inline)"""
        entities = []

        # Fenced code blocks
        fenced_pattern = r"```(\w+)?\n(.*?)\n```"
        for match in re.finditer(fenced_pattern, text, re.DOTALL):
            language = match.group(1) or "unknown"
            code = match.group(2)
            entities.append(
                ExtractedEntity(
                    entity_type="code_block",
                    entity_value=code,
                    start_position=match.start(2),
                    end_position=match.end(2),
                    confidence=0.95,
                    metadata={"language": language, "block_type": "fenced"},
                )
            )

        # Inline code
        inline_pattern = r"`([^`\n]+)`"
        for match in re.finditer(inline_pattern, text):
            code = match.group(1)
            if len(code) > 1 and not code.isdigit():  # Filter numbers
                entities.append(
                    ExtractedEntity(
                        entity_type="code_block",
                        entity_value=code,
                        start_position=match.start(1),
                        end_position=match.end(1),
                        confidence=0.75,
                        metadata={"language": "unknown", "block_type": "inline"},
                    )
                )

        return entities

    def _extract_issue_references(self, text: str) -> List[ExtractedEntity]:
        """Extract issue references like #123, PROJ-456"""
        patterns = [
            r"#(\d+)",  # GitHub-style #123
            r"\b([A-Z]+)-(\d+)\b",  # JIRA-style PROJ-123
        ]

        entities = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                issue_ref = match.group()
                entities.append(
                    ExtractedEntity(
                        entity_type="issue_reference",
                        entity_value=issue_ref,
                        start_position=match.start(),
                        end_position=match.end(),
                        confidence=0.90,
                        metadata={
                            "reference_type": "github"
                            if issue_ref.startswith("#")
                            else "jira"
                        },
                    )
                )

        return entities

    def _extract_user_mentions(self, text: str) -> List[ExtractedEntity]:
        """Extract user mentions like @username"""
        pattern = r"@([A-Za-z0-9_.-]+)"
        entities = []

        for match in re.finditer(pattern, text):
            username = match.group(1)
            entities.append(
                ExtractedEntity(
                    entity_type="user_mention",
                    entity_value=f"@{username}",
                    start_position=match.start(),
                    end_position=match.end(),
                    confidence=0.85,
                    metadata={"username": username},
                )
            )

        return entities

    def _extract_tech_keywords(self, text: str) -> List[ExtractedEntity]:
        """Extract technology keywords"""
        entities = []
        words = re.findall(r"\b\w+\b", text.lower())

        for word in set(words):
            if word in self.tech_keywords:
                # Find all positions of this keyword
                for match in re.finditer(
                    r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE
                ):
                    entities.append(
                        ExtractedEntity(
                            entity_type="tech_keyword",
                            entity_value=word,
                            start_position=match.start(),
                            end_position=match.end(),
                            confidence=0.70,
                            metadata={"category": self._categorize_tech_keyword(word)},
                        )
                    )

        return entities

    def _extract_timestamps(self, text: str) -> List[ExtractedEntity]:
        """Extract timestamp patterns"""
        patterns = [
            r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\b",  # ISO 8601
            r"\b\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\b",  # YYYY-MM-DD HH:MM:SS
            r"\b\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}\b",  # MM/DD/YYYY HH:MM:SS
        ]

        entities = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                timestamp = match.group()
                entities.append(
                    ExtractedEntity(
                        entity_type="timestamp",
                        entity_value=timestamp,
                        start_position=match.start(),
                        end_position=match.end(),
                        confidence=0.90,
                        metadata={"format": self._detect_timestamp_format(timestamp)},
                    )
                )

        return entities

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse

            return urlparse(url).netloc
        except:
            return url.split("/")[2] if "://" in url else url

    def _is_valid_path(self, path: str) -> bool:
        """Check if path looks valid (filter false positives)"""
        # Skip very short paths
        if len(path) < 3:
            return False

        # Skip paths that are likely not file paths
        false_positives = ["http", "https", "ftp", "www", "com", "org", "net"]
        if any(fp in path.lower() for fp in false_positives):
            return False

        return True

    def _categorize_tech_keyword(self, keyword: str) -> str:
        """Categorize technology keywords"""
        categories = {
            "language": {
                "python",
                "javascript",
                "typescript",
                "java",
                "cpp",
                "rust",
                "go",
            },
            "database": {"postgresql", "mysql", "mongodb", "redis"},
            "cloud": {"aws", "azure", "gcp"},
            "framework": {"react", "vue", "angular"},
            "tool": {"docker", "git", "npm", "pip", "jenkins"},
            "ai": {"claude", "openai", "gpt", "llm", "ai", "ml"},
        }

        for category, keywords in categories.items():
            if keyword in keywords:
                return category
        return "general"

    def _detect_timestamp_format(self, timestamp: str) -> str:
        """Detect timestamp format"""
        if "T" in timestamp and (
            "Z" in timestamp or "+" in timestamp or timestamp.count(":") == 3
        ):
            return "iso8601"
        elif "/" in timestamp:
            return "us_format"
        else:
            return "standard"


class EntityExtractionPipeline:
    """Main pipeline for processing chat messages and extracting entities"""

    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.extractor = EntityExtractor()

    async def process_message(self, context_item_id: str, content: str) -> int:
        """Process a single message and extract entities"""
        if not content or not content.strip():
            return 0

        # Extract entities
        entities = self.extractor.extract_all(content)

        if not entities:
            return 0

        # Store entities in database
        async with self.db_pool.acquire() as conn:
            stored_count = 0
            for entity in entities:
                try:
                    await conn.execute(
                        """
                        INSERT INTO extracted_entities (
                            id, context_item_id, entity_type, entity_value,
                            start_position, end_position, confidence, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (context_item_id, entity_type, entity_value, start_position)
                        DO NOTHING
                        """,
                        str(uuid.uuid4()),
                        context_item_id,
                        entity.entity_type,
                        entity.entity_value,
                        entity.start_position,
                        entity.end_position,
                        entity.confidence,
                        json.dumps(entity.metadata),
                    )
                    stored_count += 1
                except Exception as e:
                    print(f"Warning: Failed to store entity {entity.entity_type}: {e}")

        return stored_count

    async def create_entities_table(self):
        """Create the extracted_entities table if it doesn't exist"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS extracted_entities (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    context_item_id UUID REFERENCES context_items(id) ON DELETE CASCADE,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_value TEXT NOT NULL,
                    start_position INTEGER,
                    end_position INTEGER,
                    confidence FLOAT DEFAULT 1.0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(context_item_id, entity_type, entity_value, start_position)
                );

                CREATE INDEX IF NOT EXISTS idx_extracted_entities_type
                ON extracted_entities(entity_type);

                CREATE INDEX IF NOT EXISTS idx_extracted_entities_value
                ON extracted_entities(entity_value);

                CREATE INDEX IF NOT EXISTS idx_extracted_entities_context
                ON extracted_entities(context_item_id);
            """
            )

    async def process_existing_messages(self, limit: Optional[int] = None):
        """Process existing messages that haven't been analyzed yet"""
        async with self.db_pool.acquire() as conn:
            # Find messages without entity extraction
            query = """
                SELECT ci.id, ci.content
                FROM context_items ci
                LEFT JOIN extracted_entities ee ON ci.id = ee.context_item_id
                WHERE ci.content IS NOT NULL
                AND ci.content != ''
                AND ee.id IS NULL
                GROUP BY ci.id, ci.content
            """

            if limit:
                query += f" LIMIT {limit}"

            rows = await conn.fetch(query)

            print(f"🔍 Found {len(rows)} messages to process")

            processed = 0
            total_entities = 0

            for row in rows:
                entity_count = await self.process_message(
                    str(row["id"]), row["content"]
                )
                if entity_count > 0:
                    processed += 1
                    total_entities += entity_count

                if processed % 100 == 0:
                    print(
                        f"   Processed {processed} messages, extracted {total_entities} entities"
                    )

            print(
                f"✅ Entity extraction complete: {processed} messages, {total_entities} entities"
            )
            return total_entities


async def main():
    """Test the entity extraction pipeline"""
    # Test text with various entity types
    test_text = """
    Check out this URL: https://github.com/anthropics/claude-code

    Run this command: `docker run -p 8080:80 nginx`

    File path: /home/opsvi/master_root/apps/project-context/entity_extraction.py

    Contact: developer@example.com

    Fixed issue #123 and PROJ-456

    Thanks @john.doe for the Python code review!

    ```python
    def hello_world():
        print("Hello, World!")
    ```

    Timestamp: 2025-09-05T03:30:00Z
    """

    extractor = EntityExtractor()
    entities = extractor.extract_all(test_text)

    print(f"Extracted {len(entities)} entities:")
    for entity in entities:
        print(
            f"  {entity.entity_type}: '{entity.entity_value}' "
            f"({entity.start_position}-{entity.end_position}, conf={entity.confidence:.2f})"
        )
        if entity.metadata:
            print(f"    metadata: {entity.metadata}")

    # Test database integration
    db_pool = await asyncpg.create_pool(
        "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
        min_size=2,
        max_size=5,
    )

    try:
        pipeline = EntityExtractionPipeline(db_pool)
        await pipeline.create_entities_table()
        print("\n✅ Entity extraction table created")

        # Process a sample of existing messages
        await pipeline.process_existing_messages(limit=10)

    finally:
        await db_pool.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
