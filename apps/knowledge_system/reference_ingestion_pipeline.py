#!/usr/bin/env python3
"""
Reference Knowledge Ingestion Pipeline

Processes the /home/opsvi/.reference directory and ingests relevant knowledge
into the knowledge base with RAG indexing.
"""

import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add path for imports
sys.path.insert(0, "/home/opsvi/master_root")

from apps.knowledge_system.mcp_knowledge_tools import EnhancedKnowledgeStore

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeChunk:
    """Represents a chunk of knowledge to be ingested"""

    content: str
    source_file: str
    chunk_type: str
    tags: List[str]
    metadata: Dict[str, Any]


class ReferenceIngestionPipeline:
    """Pipeline for ingesting reference documentation into knowledge base"""

    def __init__(self, reference_dir: str = "/home/opsvi/.reference"):
        self.reference_dir = Path(reference_dir)
        self.store = EnhancedKnowledgeStore()
        self.processed_files = set()
        self.failed_files = []
        self.stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "chunks_stored": 0,
            "errors": 0,
        }
        self.state_file = Path("/tmp/ingestion_state.json")
        self.load_state()

    def load_state(self):
        """Load previous processing state if exists"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    self.processed_files = set(state.get("processed", []))
                    self.stats = state.get("stats", self.stats)
                    logger.info(
                        f"Resumed from previous state: {len(self.processed_files)} files already processed"
                    )
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def save_state(self):
        """Save current processing state"""
        try:
            state = {
                "processed": list(self.processed_files),
                "stats": self.stats,
                "timestamp": time.time(),
            }
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")

    def extract_chunks_from_file(self, file_path: Path) -> List[KnowledgeChunk]:
        """Extract knowledge chunks from a file"""
        chunks = []

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Skip empty or very small files
            if len(content) < 50:
                return chunks

            # Determine file type and extraction strategy
            if file_path.suffix == ".md":
                chunks.extend(self.extract_markdown_chunks(content, file_path))
            elif file_path.suffix == ".py":
                chunks.extend(self.extract_python_chunks(content, file_path))
            elif file_path.suffix == ".txt":
                chunks.extend(self.extract_text_chunks(content, file_path))
            elif file_path.name == "README.md":
                chunks.extend(self.extract_readme_chunks(content, file_path))

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.failed_files.append(str(file_path))

        return chunks

    def extract_markdown_chunks(
        self, content: str, file_path: Path
    ) -> List[KnowledgeChunk]:
        """Extract knowledge from markdown files"""
        chunks = []

        # Extract code blocks with language hints
        import re

        code_blocks = re.findall(r"```(\w+)?\n(.*?)```", content, re.DOTALL)
        for lang, code in code_blocks:
            if len(code.strip()) > 100:  # Skip tiny snippets
                chunk = KnowledgeChunk(
                    content=code.strip(),
                    source_file=str(file_path),
                    chunk_type="CODE_PATTERN",
                    tags=self.generate_tags(file_path, lang or "code"),
                    metadata={"language": lang or "unknown", "source": file_path.name},
                )
                chunks.append(chunk)

        # Extract headers and their content
        sections = re.split(r"^#{1,3}\s+", content, flags=re.MULTILINE)
        for section in sections[1:]:  # Skip before first header
            lines = section.split("\n")
            if lines and len("\n".join(lines)) > 200:
                title = lines[0].strip()
                body = "\n".join(lines[1:]).strip()
                if body:
                    chunk = KnowledgeChunk(
                        content=f"{title}: {body[:1000]}",  # Limit size
                        source_file=str(file_path),
                        chunk_type="DOCUMENTATION",
                        tags=self.generate_tags(file_path, title),
                        metadata={"section": title, "source": file_path.name},
                    )
                    chunks.append(chunk)

        return chunks

    def extract_python_chunks(
        self, content: str, file_path: Path
    ) -> List[KnowledgeChunk]:
        """Extract knowledge from Python files"""
        chunks = []

        # Extract class definitions
        import re

        classes = re.findall(r"class\s+(\w+).*?:\n((?:\s{4,}.*\n)*)", content)
        for class_name, class_body in classes:
            if len(class_body) > 100:
                chunk = KnowledgeChunk(
                    content=f"class {class_name}:\n{class_body[:1500]}",
                    source_file=str(file_path),
                    chunk_type="CODE_PATTERN",
                    tags=self.generate_tags(file_path, f"class-{class_name}"),
                    metadata={
                        "type": "class",
                        "name": class_name,
                        "source": file_path.name,
                    },
                )
                chunks.append(chunk)

        # Extract important functions (with docstrings)
        functions = re.findall(
            r'def\s+(\w+)\(.*?\).*?:\n\s*"""(.*?)"""', content, re.DOTALL
        )
        for func_name, docstring in functions:
            if len(docstring) > 50:
                chunk = KnowledgeChunk(
                    content=f"Function {func_name}: {docstring}",
                    source_file=str(file_path),
                    chunk_type="API_DOCUMENTATION",
                    tags=self.generate_tags(file_path, f"function-{func_name}"),
                    metadata={
                        "type": "function",
                        "name": func_name,
                        "source": file_path.name,
                    },
                )
                chunks.append(chunk)

        return chunks

    def extract_text_chunks(
        self, content: str, file_path: Path
    ) -> List[KnowledgeChunk]:
        """Extract knowledge from text files"""
        chunks = []

        # For API documentation files
        if "api" in file_path.name.lower() or "responses" in file_path.name.lower():
            # Split into manageable sections
            sections = content.split("\n\n")
            for i, section in enumerate(sections):
                if len(section) > 200 and len(section) < 3000:
                    chunk = KnowledgeChunk(
                        content=section,
                        source_file=str(file_path),
                        chunk_type="API_DOCUMENTATION",
                        tags=self.generate_tags(file_path, f"section-{i}"),
                        metadata={"section": i, "source": file_path.name},
                    )
                    chunks.append(chunk)

        # For structured output examples
        if "structured" in file_path.name.lower():
            # Extract JSON examples
            import re

            json_blocks = re.findall(r"\{[^{}]*\}", content)
            for block in json_blocks:
                if len(block) > 100:
                    chunk = KnowledgeChunk(
                        content=f"Structured output example: {block}",
                        source_file=str(file_path),
                        chunk_type="CODE_PATTERN",
                        tags=self.generate_tags(file_path, "json-structure"),
                        metadata={"type": "json", "source": file_path.name},
                    )
                    chunks.append(chunk)

        return chunks

    def extract_readme_chunks(
        self, content: str, file_path: Path
    ) -> List[KnowledgeChunk]:
        """Extract overview knowledge from README files"""
        chunks = []

        # Extract project description (usually at the beginning)
        lines = content.split("\n")
        description = []
        for line in lines[:50]:  # First 50 lines usually contain description
            if line.strip():
                description.append(line)
            if len("\n".join(description)) > 500:
                break

        if description:
            chunk = KnowledgeChunk(
                content="\n".join(description),
                source_file=str(file_path),
                chunk_type="PROJECT_OVERVIEW",
                tags=self.generate_tags(file_path, "readme"),
                metadata={"type": "overview", "source": file_path.parent.name},
            )
            chunks.append(chunk)

        return chunks

    def generate_tags(self, file_path: Path, extra: str = "") -> List[str]:
        """Generate tags based on file path and content"""
        tags = []

        # Add path components as tags
        parts = file_path.relative_to(self.reference_dir).parts
        tags.extend([p.replace("-", "_").replace(".", "_") for p in parts[:-1]])

        # Add file type
        if file_path.suffix:
            tags.append(file_path.suffix[1:])

        # Add extra context
        if extra:
            tags.append(extra.lower().replace(" ", "_")[:30])

        # Add special tags for known projects
        if "openai" in str(file_path).lower():
            tags.append("openai")
        if "gpt-5" in str(file_path).lower():
            tags.append("gpt5")
        if "cookbook" in str(file_path).lower():
            tags.append("cookbook")
        if "eval" in str(file_path).lower():
            tags.append("evaluation")

        return list(set(tags))[:10]  # Limit to 10 tags

    async def store_chunk(self, chunk: KnowledgeChunk) -> bool:
        """Store a knowledge chunk in the knowledge base"""
        try:
            # Prepare content
            content = chunk.content
            if chunk.metadata:
                content = (
                    f"{content}\n\nSource: {chunk.metadata.get('source', 'unknown')}"
                )

            # Store with RAG (Neo4j auth fixed, rate limiting disabled)
            result = await self.store.store(
                raw_input=content,
                hint_type=chunk.chunk_type,
                hint_tags=chunk.tags,
                direct_execute=True,  # Execute directly in Neo4j
            )

            if result.get("success"):
                self.stats["chunks_stored"] += 1
                return True
            else:
                logger.warning(f"Failed to store chunk: {result}")
                return False

        except Exception as e:
            logger.error(f"Error storing chunk: {e}")
            self.stats["errors"] += 1
            return False

    async def process_file(self, file_path: Path):
        """Process a single file"""
        # Skip if already processed
        if str(file_path) in self.processed_files:
            return

        logger.info(f"Processing: {file_path.relative_to(self.reference_dir)}")

        # Extract chunks
        chunks = self.extract_chunks_from_file(file_path)
        self.stats["chunks_created"] += len(chunks)

        # Store chunks
        for chunk in chunks:
            await self.store_chunk(chunk)
            await asyncio.sleep(0.1)  # Rate limiting

        # Mark as processed
        self.processed_files.add(str(file_path))
        self.stats["files_processed"] += 1

        # Save state periodically
        if self.stats["files_processed"] % 10 == 0:
            self.save_state()
            logger.info(f"Progress: {self.stats}")

    async def run(self, max_files: Optional[int] = None):
        """Run the ingestion pipeline"""
        logger.info(f"Starting ingestion pipeline for {self.reference_dir}")

        # Collect files to process
        file_patterns = ["**/*.md", "**/*.txt", "**/*.py"]
        files_to_process = []

        for pattern in file_patterns:
            for file_path in self.reference_dir.glob(pattern):
                if str(file_path) not in self.processed_files:
                    files_to_process.append(file_path)

        # Limit files if specified
        if max_files:
            files_to_process = files_to_process[:max_files]

        logger.info(f"Found {len(files_to_process)} files to process")

        # Process files
        for i, file_path in enumerate(files_to_process, 1):
            try:
                await self.process_file(file_path)

                # Progress report
                if i % 25 == 0:
                    pct = (i / len(files_to_process)) * 100
                    logger.info(f"Progress: {i}/{len(files_to_process)} ({pct:.1f}%)")

            except KeyboardInterrupt:
                logger.info("Interrupted by user - saving state...")
                self.save_state()
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

        # Final save
        self.save_state()

        # Report results
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"Chunks created: {self.stats['chunks_created']}")
        logger.info(f"Chunks stored: {self.stats['chunks_stored']}")
        logger.info(f"Errors: {self.stats['errors']}")
        if self.failed_files:
            logger.info(f"Failed files: {len(self.failed_files)}")
        logger.info("=" * 60)


async def main():
    """Main entry point"""
    pipeline = ReferenceIngestionPipeline()

    # Run full ingestion (set max_files to limit)
    await pipeline.run(max_files=50)  # Process 50 files for demonstration

    # For full 1500+ files, use:
    # await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
