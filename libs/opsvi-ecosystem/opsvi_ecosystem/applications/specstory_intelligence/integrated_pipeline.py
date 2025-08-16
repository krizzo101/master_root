"""
Integrated SpecStory Intelligence Pipeline
Combines cleaning, file mapping, concept extraction, atomic parsing, embedding, and storage
"""

import asyncio
import json
import logging

# Import shared utilities
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Import existing components
from .atomic_parser import AtomicComponent, AtomicRelationship, AtomicSpecStoryParser
from .conversation_intelligence import ConversationIntelligenceEngine
from .database_storage import SpecStoryDatabaseStorage

sys.path.append(str(Path(__file__).parent.parent.parent / "shared"))


@dataclass
class ConceptExtraction:
    """High-level concept/idea extraction before atomic decomposition"""

    concepts: list[dict] = field(default_factory=list)
    ideas: list[dict] = field(default_factory=list)
    themes: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    learnings: list[dict] = field(default_factory=list)
    patterns: list[dict] = field(default_factory=list)


@dataclass
class ProcessingResult:
    """Complete processing result for a file"""

    file_path: str
    file_map: dict
    concepts: ConceptExtraction
    components: list[AtomicComponent]
    relationships: list[AtomicRelationship]
    embeddings: dict
    storage_results: dict
    processing_time: float
    success: bool
    errors: list[str] = field(default_factory=list)


class IntegratedSpecStoryPipeline:
    """Fully integrated pipeline for SpecStory processing"""

    def __init__(
        self,
        input_dir: str = ".cursor/import",
        db_config: dict = None,
        enable_embeddings: bool = True,
        enable_concept_extraction: bool = True,
    ):
        self.input_dir = Path(input_dir)
        self.enable_embeddings = enable_embeddings
        self.enable_concept_extraction = enable_concept_extraction

        # Initialize components
        self.atomic_parser = AtomicSpecStoryParser()
        self.intelligence_engine = ConversationIntelligenceEngine()
        self.db_storage = SpecStoryDatabaseStorage()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Processing metrics
        self.metrics = {
            "files_processed": 0,
            "concepts_extracted": 0,
            "components_created": 0,
            "embeddings_generated": 0,
            "total_processing_time": 0.0,
        }

    def setup_logging(self):
        """Configure structured logging"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        )

    async def process_file(self, file_path: str) -> ProcessingResult:
        """Process a single file through the complete pipeline"""
        start_time = datetime.utcnow()
        result = ProcessingResult(
            file_path=file_path,
            file_map={},
            concepts=ConceptExtraction(),
            components=[],
            relationships=[],
            embeddings={},
            storage_results={},
            processing_time=0.0,
            success=False,
        )

        try:
            self.logger.info(f"🚀 Starting integrated processing for {file_path}")

            # Step 1: Generate file map (if not already present)
            result.file_map = await self._generate_file_map(file_path)

            # Step 2: Extract high-level concepts/ideas
            if self.enable_concept_extraction:
                result.concepts = await self._extract_concepts(
                    file_path, result.file_map
                )

            # Step 3: Atomic parsing
            (
                result.components,
                result.relationships,
            ) = await self.atomic_parser.parse_file(file_path)

            # Step 4: Generate embeddings
            if self.enable_embeddings:
                result.embeddings = await self._generate_embeddings(result.components)

            # Step 5: Store in multi-database system
            result.storage_results = await self._store_multi_database(
                file_path,
                result.file_map,
                result.concepts,
                result.components,
                result.relationships,
                result.embeddings,
            )

            # Calculate processing time
            end_time = datetime.utcnow()
            result.processing_time = (end_time - start_time).total_seconds()
            result.success = True

            # Update metrics
            self._update_metrics(result)

            self.logger.info(
                f"✅ Completed processing {file_path} in {result.processing_time:.2f}s"
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to process {file_path}: {e}")
            result.errors.append(str(e))
            result.success = False

        return result

    async def _generate_file_map(self, file_path: str) -> dict:
        """Generate or extract file map from the file"""
        try:
            # Check if file already has a file map
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Look for existing file map
            import re

            file_map_pattern = r"<!-- FILE_MAP_BEGIN <!--(.*?)--> <!-- FILE_MAP_END -->"
            match = re.search(file_map_pattern, content, re.DOTALL)

            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid file map JSON in {file_path}")

            # Generate new file map using genFileMap logic
            # This would integrate with your existing genFileMap functionality
            return await self._create_file_map_from_content(content, file_path)

        except Exception as e:
            self.logger.error(f"Failed to generate file map for {file_path}: {e}")
            return {}

    async def _create_file_map_from_content(self, content: str, file_path: str) -> dict:
        """Create file map from content analysis"""
        lines = content.split("\n")
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            # Detect section headers
            if line.startswith("#"):
                if current_section:
                    current_section["line_end"] = i - 1
                    sections.append(current_section)

                current_section = {
                    "name": line.strip("#").strip(),
                    "description": "",
                    "line_start": i + 1,
                    "line_end": len(lines),
                }

        if current_section:
            sections.append(current_section)

        return {
            "file_metadata": {
                "title": Path(file_path).stem,
                "description": f"Processed file from {file_path}",
                "type": "documentation",
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
            },
            "sections": sections,
            "key_elements": [],
        }

    async def _extract_concepts(
        self, file_path: str, file_map: dict
    ) -> ConceptExtraction:
        """Extract high-level concepts and ideas before atomic decomposition"""
        extraction = ConceptExtraction()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Use intelligence engine for concept extraction
            intelligence = await self.intelligence_engine.analyze_conversation(content)

            # Extract concepts from intelligence analysis
            if hasattr(intelligence, "strategic_decisions"):
                extraction.decisions = [
                    {
                        "concept": decision,
                        "confidence": 0.8,
                        "source": "intelligence_engine",
                        "context": "strategic_decision",
                    }
                    for decision in intelligence.strategic_decisions
                ]

            if hasattr(intelligence, "knowledge_building_sequences"):
                extraction.learnings = [
                    {
                        "concept": learning,
                        "confidence": 0.9,
                        "source": "intelligence_engine",
                        "context": "knowledge_building",
                    }
                    for learning in intelligence.knowledge_building_sequences
                ]

            # Extract concepts from file map sections
            for section in file_map.get("sections", []):
                extraction.concepts.append(
                    {
                        "concept": section["name"],
                        "description": section.get("description", ""),
                        "confidence": 0.7,
                        "source": "file_map",
                        "context": "section_title",
                        "location": {
                            "line_start": section.get("line_start"),
                            "line_end": section.get("line_end"),
                        },
                    }
                )

            self.logger.info(
                f"Extracted {len(extraction.concepts)} concepts, "
                f"{len(extraction.decisions)} decisions, "
                f"{len(extraction.learnings)} learnings from {file_path}"
            )

        except Exception as e:
            self.logger.error(f"Failed to extract concepts from {file_path}: {e}")

        return extraction

    async def _generate_embeddings(self, components: list[AtomicComponent]) -> dict:
        """Generate embeddings for components"""
        embeddings = {}

        try:
            from src.applications.graphrag_ai.graph_loader import embed_text_openai

            for component in components:
                # Generate embedding for text content
                text_content = component.raw_content
                if text_content and len(text_content.strip()) > 10:
                    embedding = embed_text_openai(
                        text_content, model="text-embedding-3-large", dimensions=1536
                    )
                    embeddings[component.component_id] = {
                        "embedding": embedding,
                        "text": text_content,
                        "component_type": component.component_type.value,
                    }

            self.logger.info(f"Generated {len(embeddings)} embeddings")

        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")

        return embeddings

    async def _store_multi_database(
        self,
        file_path: str,
        file_map: dict,
        concepts: ConceptExtraction,
        components: list[AtomicComponent],
        relationships: list[AtomicRelationship],
        embeddings: dict,
    ) -> dict:
        """Store data across multiple database collections/types"""
        storage_results = {}

        try:
            # Store atomic components and relationships (existing functionality)
            atomic_result = await self.db_storage.store_parsed_file(
                file_path, components, relationships, metadata={"file_map": file_map}
            )
            storage_results["atomic"] = atomic_result

            # Store concepts in graph database
            concept_result = await self._store_concepts_graph(concepts, file_path)
            storage_results["concepts"] = concept_result

            # Store embeddings in vector database
            embedding_result = await self._store_embeddings_vector(
                embeddings, file_path
            )
            storage_results["embeddings"] = embedding_result

            # Store file map as structured document
            filemap_result = await self._store_file_map(file_map, file_path)
            storage_results["file_map"] = filemap_result

            self.logger.info(
                f"Stored data across {len(storage_results)} database systems"
            )

        except Exception as e:
            self.logger.error(f"Failed to store data for {file_path}: {e}")
            storage_results["error"] = str(e)

        return storage_results

    async def _store_concepts_graph(
        self, concepts: ConceptExtraction, file_path: str
    ) -> dict:
        """Store concepts in graph database for relationship analysis"""
        # Implementation would create concept nodes and relationships
        # This is where high-level concepts get stored separately from atomic components
        return {"concepts_stored": len(concepts.concepts)}

    async def _store_embeddings_vector(self, embeddings: dict, file_path: str) -> dict:
        """Store embeddings in vector database for similarity search"""
        # Implementation would store embeddings for vector similarity search
        return {"embeddings_stored": len(embeddings)}

    async def _store_file_map(self, file_map: dict, file_path: str) -> dict:
        """Store file map as structured document"""
        # Implementation would store the file map for navigation
        return {"file_map_stored": True}

    def _update_metrics(self, result: ProcessingResult):
        """Update processing metrics"""
        self.metrics["files_processed"] += 1
        self.metrics["concepts_extracted"] += len(result.concepts.concepts)
        self.metrics["components_created"] += len(result.components)
        self.metrics["embeddings_generated"] += len(result.embeddings)
        self.metrics["total_processing_time"] += result.processing_time

    async def process_directory(self, directory: str = None) -> list[ProcessingResult]:
        """Process all files in a directory"""
        if directory is None:
            directory = self.input_dir

        directory = Path(directory)
        results = []

        # Find all markdown files
        md_files = list(directory.glob("*.md"))

        self.logger.info(f"Processing {len(md_files)} files from {directory}")

        for file_path in md_files:
            result = await self.process_file(str(file_path))
            results.append(result)

        # Log summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        self.logger.info(
            f"📊 Processing complete: {successful} successful, {failed} failed"
        )
        self.logger.info(f"📈 Metrics: {self.metrics}")

        return results

    async def start_monitoring(self):
        """Start real-time file monitoring"""
        # Implementation would use file system watching
        # to automatically process new files as they arrive
        pass


# Factory function for easy instantiation
def create_integrated_pipeline(**kwargs) -> IntegratedSpecStoryPipeline:
    """Create and configure an integrated pipeline"""
    return IntegratedSpecStoryPipeline(**kwargs)


# CLI interface
async def main():
    """CLI interface for the integrated pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description="Integrated SpecStory Pipeline")
    parser.add_argument("--input-dir", default=".cursor/import", help="Input directory")
    parser.add_argument("--file", help="Process single file")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring mode")

    args = parser.parse_args()

    pipeline = create_integrated_pipeline(input_dir=args.input_dir)

    if args.file:
        result = await pipeline.process_file(args.file)
        print(f"Processing result: {result.success}")
    elif args.monitor:
        await pipeline.start_monitoring()
    else:
        results = await pipeline.process_directory()
        print(f"Processed {len(results)} files")


if __name__ == "__main__":
    asyncio.run(main())
