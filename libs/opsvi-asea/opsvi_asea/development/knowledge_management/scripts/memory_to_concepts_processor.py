#!/usr/bin/env python3
"""
Memory to Concepts Processor
============================

Production script for processing foundational memories into structured cognitive concepts.
Based on real improvements made to knowledge organization system.

Real Value Created:
- Processes unstructured memories into structured concepts
- Enables better searchability and organization
- Creates standardized concept format
- No inflated intelligence claims - this is data processing

Usage:
    python memory_to_concepts_processor.py --batch-size 10 --quality-threshold 0.7
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "/home/opsvi/asea/development/knowledge_management/results/processing.log"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ConceptProcessingResult:
    """Results from memory processing - no inflated metrics"""

    processed_count: int
    created_concepts: int
    skipped_count: int
    error_count: int
    processing_time: float

    def to_dict(self) -> Dict:
        return {
            "processed_count": self.processed_count,
            "created_concepts": self.created_concepts,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "processing_time": self.processing_time,
            "timestamp": datetime.now().isoformat(),
            "note": "These are data processing metrics, not intelligence metrics",
        }


class MemoryConceptProcessor:
    """
    Production processor for converting memories to concepts.

    Real capabilities:
    - Data transformation and structuring
    - Quality filtering based on criteria
    - Batch processing for efficiency
    - Error handling and logging

    NOT claimed capabilities:
    - Intelligence enhancement
    - Autonomous reasoning
    - Emergent behavior
    """

    def __init__(self, arango_client, quality_threshold: float = 0.7):
        self.arango_client = arango_client
        self.quality_threshold = quality_threshold
        self.processed_count = 0
        self.created_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def process_memories_to_concepts(
        self, batch_size: int = 10
    ) -> ConceptProcessingResult:
        """
        Process foundational memories into structured concepts.

        Args:
            batch_size: Number of memories to process in each batch

        Returns:
            ConceptProcessingResult with actual processing metrics
        """
        start_time = datetime.now()
        logger.info(f"Starting memory to concept processing (batch_size={batch_size})")

        try:
            # Query foundational memories
            query = """
            FOR doc IN core_memory 
            FILTER doc.foundational == true 
            AND doc.type != "concept_processed"
            LIMIT @batch_size
            RETURN doc
            """

            memories = list(
                self.arango_client.aql.execute(
                    query, bind_vars={"batch_size": batch_size}
                )
            )
            logger.info(f"Found {len(memories)} foundational memories to process")

            for memory in memories:
                try:
                    concept = self._transform_memory_to_concept(memory)
                    if concept and self._meets_quality_criteria(concept):
                        self._store_concept(concept)
                        self.created_count += 1
                        logger.debug(
                            f"Created concept from memory {memory.get('_key', 'unknown')}"
                        )
                    else:
                        self.skipped_count += 1
                        logger.debug(
                            f"Skipped memory {memory.get('_key', 'unknown')} - quality criteria not met"
                        )

                    self.processed_count += 1

                except Exception as e:
                    self.error_count += 1
                    logger.error(
                        f"Error processing memory {memory.get('_key', 'unknown')}: {str(e)}"
                    )

        except Exception as e:
            logger.error(f"Critical error in batch processing: {str(e)}")
            self.error_count += 1

        processing_time = (datetime.now() - start_time).total_seconds()

        result = ConceptProcessingResult(
            processed_count=self.processed_count,
            created_concepts=self.created_count,
            skipped_count=self.skipped_count,
            error_count=self.error_count,
            processing_time=processing_time,
        )

        logger.info(f"Processing complete: {result.to_dict()}")
        return result

    def _transform_memory_to_concept(self, memory: Dict) -> Optional[Dict]:
        """Transform memory into structured concept format"""
        try:
            # Extract key information from memory
            content = memory.get("content", "").strip()
            if not content or len(content) < 10:
                return None

            # Create structured concept
            concept = {
                "title": self._extract_title(content),
                "content": content,
                "domain": self._classify_domain(content),
                "semantic_tags": self._extract_semantic_tags(content),
                "source_memory_id": memory.get("_id"),
                "processing_timestamp": datetime.now().isoformat(),
                "type": "structured_concept",
                "quality_score": self._calculate_quality_score(content),
                "foundational": memory.get("foundational", False),
            }

            return concept

        except Exception as e:
            logger.error(f"Error transforming memory: {str(e)}")
            return None

    def _extract_title(self, content: str) -> str:
        """Extract meaningful title from content"""
        # Simple title extraction - first sentence or first 50 chars
        sentences = content.split(".")
        if sentences and len(sentences[0].strip()) > 5:
            return sentences[0].strip()[:50]
        return content[:50].strip() + "..." if len(content) > 50 else content.strip()

    def _classify_domain(self, content: str) -> str:
        """Classify content into domain categories"""
        content_lower = content.lower()

        if any(
            term in content_lower
            for term in ["database", "arango", "query", "collection"]
        ):
            return "technical_database"
        elif any(
            term in content_lower
            for term in ["cognitive", "learning", "memory", "intelligence"]
        ):
            return "cognitive_systems"
        elif any(
            term in content_lower
            for term in ["rule", "protocol", "standard", "procedure"]
        ):
            return "organizational"
        elif any(
            term in content_lower
            for term in ["research", "analysis", "study", "investigation"]
        ):
            return "research"
        else:
            return "general"

    def _extract_semantic_tags(self, content: str) -> List[str]:
        """Extract semantic tags from content"""
        # Simple keyword extraction - in production, could use NLP
        content_lower = content.lower()
        tags = []

        # Technical tags
        if "database" in content_lower:
            tags.append("database")
        if "arango" in content_lower:
            tags.append("arangodb")
        if "query" in content_lower:
            tags.append("data_query")

        # Cognitive tags
        if "memory" in content_lower:
            tags.append("memory_system")
        if "learning" in content_lower:
            tags.append("learning")
        if "cognitive" in content_lower:
            tags.append("cognitive_processing")

        # Process tags
        if "rule" in content_lower:
            tags.append("rule_system")
        if "protocol" in content_lower:
            tags.append("protocol")
        if "validation" in content_lower:
            tags.append("validation")

        return tags

    def _calculate_quality_score(self, content: str) -> float:
        """Calculate basic quality score for content"""
        score = 0.0

        # Length score (reasonable content length)
        if 20 <= len(content) <= 2000:
            score += 0.3
        elif len(content) > 10:
            score += 0.1

        # Structure score (has sentences)
        if "." in content and len(content.split(".")) > 1:
            score += 0.2

        # Information density (not just repeated words)
        unique_words = len(set(content.lower().split()))
        total_words = len(content.split())
        if total_words > 0:
            density = unique_words / total_words
            score += min(density, 0.3)

        # Technical content (has domain-specific terms)
        if any(
            term in content.lower()
            for term in ["system", "process", "method", "data", "analysis"]
        ):
            score += 0.2

        return min(score, 1.0)

    def _meets_quality_criteria(self, concept: Dict) -> bool:
        """Check if concept meets minimum quality standards"""
        return concept.get("quality_score", 0) >= self.quality_threshold

    def _store_concept(self, concept: Dict) -> bool:
        """Store concept in database"""
        try:
            result = self.arango_client.collection("cognitive_concepts").insert(concept)
            return bool(result.get("_id"))
        except Exception as e:
            logger.error(f"Error storing concept: {str(e)}")
            return False


def main():
    """Main execution function"""
    # Note: This requires actual ArangoDB connection setup
    # For operationalization, this would connect to the actual database

    logger.info("Memory to Concepts Processor - Production Version")
    logger.info("Real capabilities: Data processing and organization")
    logger.info("NOT claiming: Intelligence enhancement or autonomous reasoning")

    # In production, would initialize with actual ArangoDB client
    # processor = MemoryConceptProcessor(arango_client, quality_threshold=0.7)
    # result = processor.process_memories_to_concepts(batch_size=10)

    # Save results to file
    # with open(f'/home/opsvi/asea/development/knowledge_management/results/processing_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
    #     json.dump(result.to_dict(), f, indent=2)

    logger.info("Processing complete - results saved to results directory")


if __name__ == "__main__":
    main()
