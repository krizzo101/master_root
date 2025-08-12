"""
Simplified Database Storage for Auto-Loader
Uses consolidated ArangoDB interface directly for atomic components
"""

import hashlib
import json
import logging
import re

# Import the atomic parser types
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add parent directory to path for relative imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from atomic_parser import AtomicComponent, AtomicRelationship
except ImportError:
    # Fallback to absolute import
    from src.applications.specstory_intelligence.atomic_parser import (
        AtomicComponent,
        AtomicRelationship,
    )

from src.applications.graphrag_ai.graph_loader import embed_text_openai


def make_arango_key(value: str, fallback: str) -> str:
    """Sanitize value for use as ArangoDB _key. Fallback to hash if needed."""
    if not value or not isinstance(value, str):
        value = ""
    key = re.sub(r"[^a-zA-Z0-9_-]", "_", value)
    key = key.strip("_")
    if not key:
        # fallback: hash of fallback + timestamp
        key = hashlib.md5((fallback + str(time.time())).encode()).hexdigest()
    return key[:254]


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
        self.logger.setLevel(logging.WARNING)

    async def initialize_database(self) -> bool:
        """Initialize database collections"""
        try:
            # Create collections if they don't exist
            for collection_name in self.collections.values():
                if not self.db_client.collection_exists(collection_name):
                    result = self.db_client.create_collection(collection_name)
                    if result.get("success"):
                        self.logger.info(f"✅ Collection created: {collection_name}")
                else:
                    self.logger.info(f"✅ Collection exists: {collection_name}")

            self.logger.info("✅ Database initialization complete")
            return True

        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            return False

    async def store_parsed_file(
        self,
        file_path: str,
        components: list[AtomicComponent],
        relationships: list[AtomicRelationship],
        metadata: dict = None,
        intelligence=None,
        intelligence_summary: dict = None,
    ) -> dict:
        """Store parsed file components and relationships, embedding each component's text."""
        # Defensive: ensure components is always a list
        if not isinstance(components, list):
            self.logger.warning(
                f"[DEFENSIVE] 'components' was type {type(components)} for file {file_path}; wrapping in list."
            )
            components = [components]
        if not isinstance(relationships, list):
            self.logger.warning(
                f"[DEFENSIVE] 'relationships' was type {type(relationships)} for file {file_path}; wrapping in list."
            )
            relationships = [relationships]
        try:
            start_time = datetime.utcnow()
            session_id = (
                components[0].session_id
                if components
                else f"session_{start_time.timestamp()}"
            )
            session_key = make_arango_key(session_id, Path(file_path).stem)
            intelligence_key = f"intel_{session_key}"
            stored_components = 0
            for component in components:
                component_doc = component.to_arango_document()
                component_doc["file_path"] = file_path
                # Embed the component's text
                text_to_embed = getattr(component, "text", None) or getattr(
                    component, "content", None
                )
                if text_to_embed:
                    embedding = embed_text_openai(
                        text_to_embed, model="text-embedding-3-large", dimensions=1536
                    )
                    component_doc["embedding"] = embedding
                result = self.db_client.batch_insert(
                    self.collections["components"], [component_doc]
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
                self.logger.debug(
                    f"Inserting relationship edge: {json.dumps(rel_doc, default=str)}"
                )
                result = self.db_client.batch_insert(
                    self.collections["relationships"], [rel_doc]
                )
                self.logger.debug(f"Insert result: {result}")
                if result.get("success"):
                    stored_relationships += 1
                else:
                    self.logger.warning(
                        f"Failed to store relationship: {result.get('error')}, doc: {json.dumps(rel_doc, default=str)}"
                    )

            # Store intelligence analysis if provided
            intelligence_stored = False
            if intelligence and intelligence_summary:
                intelligence_doc = {
                    "_key": intelligence_key,
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

                # Use AQL for upsert operation
                upsert_query = """
                UPSERT { session_id: @session_id }
                INSERT @doc
                UPDATE @doc
                IN @@collection
                RETURN NEW
                """
                intel_result = self.db_client.execute_aql(
                    upsert_query,
                    {
                        "session_id": session_id,
                        "doc": intelligence_doc,
                        "@collection": self.collections["intelligence"],
                    },
                )

                intelligence_stored = intel_result.get("success", False)

            # Store session summary
            session_doc = {
                "_key": session_key,
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

            # Use AQL for session upsert
            session_upsert_query = """
            UPSERT { session_id: @session_id }
            INSERT @doc
            UPDATE @doc
            IN @@collection
            RETURN NEW
            """
            session_result = self.db_client.execute_aql(
                session_upsert_query,
                {
                    "session_id": session_id,
                    "doc": session_doc,
                    "@collection": self.collections["sessions"],
                },
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
