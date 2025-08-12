"""
Simplified Database Storage for Auto-Loader
Uses consolidated ArangoDB interface directly for atomic components
"""

from datetime import datetime
import logging
from pathlib import Path

# Import the atomic parser types
import sys
from typing import Dict, List

sys.path.append(str(Path(__file__).parent.parent))
from specstory_intelligence.atomic_parser import AtomicComponent, AtomicRelationship


class SimplifiedSpecStoryStorage:
    """Simplified storage using consolidated ArangoDB interface"""

    def __init__(self, db_client, collection_prefix: str = "specstory"):
        self.db_client = db_client
        self.collection_prefix = collection_prefix
        self.collections = {
            "components": f"{collection_prefix}_components",
            "relationships": f"{collection_prefix}_relationships",
            "sessions": f"{collection_prefix}_sessions",
            "intelligence": f"{collection_prefix}_intelligence",
        }

        self.logger = logging.getLogger(__name__)

    async def initialize_database(self) -> bool:
        """Initialize database collections"""
        try:
            # Create collections if they don't exist
            for collection_name in self.collections.values():
                result = self.db_client.manage(
                    "create_collection", name=collection_name
                )
                if result.get("success"):
                    self.logger.info(f"✅ Collection ready: {collection_name}")

            self.logger.info("✅ Database initialization complete")
            return True

        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            return False

    async def store_parsed_file(
        self,
        file_path: str,
        components: List[AtomicComponent],
        relationships: List[AtomicRelationship],
        metadata: Dict = None,
        intelligence=None,
        intelligence_summary: Dict = None,
    ) -> Dict:
        """Store parsed file components and relationships"""
        try:
            start_time = datetime.utcnow()

            # Extract session info
            session_id = (
                components[0].session_id
                if components
                else f"session_{start_time.timestamp()}"
            )

            # Store components
            stored_components = 0
            for component in components:
                component_doc = component.to_arango_document()
                component_doc["file_path"] = file_path

                result = self.db_client.modify(
                    "insert", self.collections["components"], document=component_doc
                )

                if result.get("success"):
                    stored_components += 1
                else:
                    self.logger.warning(
                        f"Failed to store component: {result.get('error')}"
                    )

            # Store relationships
            stored_relationships = 0
            for relationship in relationships:
                rel_doc = relationship.to_arango_edge()

                result = self.db_client.modify(
                    "insert", self.collections["relationships"], document=rel_doc
                )

                if result.get("success"):
                    stored_relationships += 1
                else:
                    self.logger.warning(
                        f"Failed to store relationship: {result.get('error')}"
                    )

            # Store intelligence analysis if provided
            intelligence_stored = False
            if intelligence and intelligence_summary:
                intelligence_doc = {
                    "_key": f"intel_{session_id}",
                    "session_id": session_id,
                    "file_path": file_path,
                    "conversation_id": intelligence.conversation_id,
                    "participants": intelligence.participants,
                    "concept_evolution": {
                        concept: {
                            "first_mention": evolution.first_mention,
                            "last_mention": evolution.last_mention,
                            "mentions": evolution.mentions,
                            "evolution_stages": evolution.evolution_stages,
                        }
                        for concept, evolution in intelligence.concept_evolution.items()
                    },
                    "insight_patterns": [
                        {
                            "pattern_type": pattern.pattern_type,
                            "trigger_components": pattern.trigger_components,
                            "insight_content": pattern.insight_content,
                            "confidence": pattern.confidence,
                            "context": pattern.context,
                        }
                        for pattern in intelligence.insight_patterns
                    ],
                    "recursive_loops": intelligence.recursive_loops,
                    "meta_cognitive_moments": intelligence.meta_cognitive_moments,
                    "strategic_decisions": intelligence.strategic_decisions,
                    "knowledge_building_sequences": intelligence.knowledge_building_sequences,
                    "compound_learning_indicators": intelligence.compound_learning_indicators,
                    "philosophical_explorations": intelligence.philosophical_explorations,
                    "intelligence_summary": intelligence_summary,
                    "analysis_timestamp": start_time.isoformat(),
                }

                intel_result = self.db_client.modify(
                    "upsert",
                    self.collections["intelligence"],
                    document=intelligence_doc,
                    match_fields=["session_id"],
                )

                intelligence_stored = intel_result.get("success", False)

            # Store session summary
            session_doc = {
                "_key": session_id,
                "session_id": session_id,
                "file_path": file_path,
                "component_count": len(components),
                "relationship_count": len(relationships),
                "component_types": list(
                    set(c.component_type.value for c in components)
                ),
                "processing_timestamp": start_time.isoformat(),
                "metadata": metadata or {},
                "has_intelligence": intelligence_stored,
            }

            session_result = self.db_client.modify(
                "upsert",
                self.collections["sessions"],
                document=session_doc,
                match_fields=["session_id"],
            )

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "session_id": session_id,
                "file_path": file_path,
                "components_stored": stored_components,
                "relationships_stored": stored_relationships,
                "processing_time_seconds": processing_time,
                "storage_timestamp": end_time.isoformat(),
            }

            self.logger.info(
                f"✅ Stored {file_path}: {stored_components} components, {stored_relationships} relationships"
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to store parsed file {file_path}: {e}")
            return {"success": False, "error": str(e)}
