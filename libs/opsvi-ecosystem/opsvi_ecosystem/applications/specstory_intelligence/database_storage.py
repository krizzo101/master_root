"""
Database Storage for Atomic SpecStory Components
Handles storing parsed atomic components and relationships in ArangoDB
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .atomic_parser import (
    AtomicComponent,
    AtomicRelationship,
    ComponentType,
    RelationshipType,
)


class SpecStoryDatabaseStorage:
    """Handles storage and retrieval of atomic SpecStory components"""

    def __init__(self, collection_prefix: str = "specstory"):
        self.collection_prefix = collection_prefix
        self.collections = {
            # Primary collections (per specification)
            "components": f"{collection_prefix}_components",
            "relationships": f"{collection_prefix}_relationships",
            "sessions": f"{collection_prefix}_sessions",
            # Specialized collections (per specification)
            "code_blocks": f"{collection_prefix}_code_blocks",
            "tool_interactions": f"{collection_prefix}_tool_interactions",
            "temporal_sequence": f"{collection_prefix}_temporal_sequence",
            "text_content": f"{collection_prefix}_text_content",
            "tokens": f"{collection_prefix}_tokens",
            "characters": f"{collection_prefix}_characters",
            # Legacy collections (maintain compatibility)
            "files": f"{collection_prefix}_files",
            "metadata": f"{collection_prefix}_metadata",
        }

        self.logger = logging.getLogger(__name__)
        self.setup_logging()

    def setup_logging(self):
        """Configure structured logging"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        )

    async def initialize_database(self) -> bool:
        """Initialize database collections and indexes"""
        try:
            # Create collections
            await self._ensure_collections_exist()

            # Create indexes for performance
            await self._create_indexes()

            # Create views for complex queries
            await self._create_views()

            self.logger.info("✅ Database initialization complete")
            return True

        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")
            return False

    async def _ensure_collections_exist(self):
        """Ensure all required collections exist"""
        try:
            from src.shared.database.core.cognitive_database import (
                mcp_cognitive_tools_arango_manage,
            )
        except ImportError:
            # Mock for testing when database tools not available
            async def mcp_cognitive_tools_arango_manage(*args, **kwargs):
                return {"success": False, "error": "Database tools not available"}

        # Create document collections (primary + specialized + legacy)
        document_collections = [
            "components",
            "sessions",
            "code_blocks",
            "tool_interactions",
            "temporal_sequence",
            "text_content",
            "tokens",
            "characters",
            "files",
            "metadata",
        ]

        for collection_name in document_collections:
            full_name = self.collections[collection_name]
            result = await mcp_cognitive_tools_arango_manage(
                action="create_collection", name=full_name, collection_type="document"
            )
            if result.get("success"):
                self.logger.info(f"📁 Created collection: {full_name}")

        # Create edge collection for relationships
        result = await mcp_cognitive_tools_arango_manage(
            action="create_collection",
            name=self.collections["relationships"],
            collection_type="edge",
        )
        if result.get("success"):
            self.logger.info(
                f"🔗 Created edge collection: {self.collections['relationships']}"
            )

    async def _create_indexes(self):
        """Create performance indexes"""
        # Component indexes
        component_indexes = [
            {"fields": ["component_type"], "type": "hash"},
            {"fields": ["metadata.session_id"], "type": "hash"},
            {"fields": ["positioning.turn_sequence"], "type": "skiplist"},
            {"fields": ["positioning.component_sequence"], "type": "skiplist"},
            {"fields": ["content.raw_content"], "type": "fulltext"},
            {"fields": ["metadata.processing_timestamp"], "type": "skiplist"},
            {
                "fields": ["positioning.file_path", "positioning.line_start"],
                "type": "skiplist",
            },
        ]

        for index in component_indexes:
            self.logger.info(f"🔍 Creating index on {index['fields']} for components")

        # Relationship indexes
        relationship_indexes = [
            {"fields": ["relationship_type"], "type": "hash"},
            {"fields": ["temporal_data.temporal_order"], "type": "skiplist"},
            {"fields": ["semantic_data.relevance_score"], "type": "skiplist"},
            {"fields": ["semantic_data.confidence"], "type": "skiplist"},
        ]

        for index in relationship_indexes:
            self.logger.info(f"🔍 Creating index on {index['fields']} for relationships")

    async def _create_views(self):
        """Create materialized views for complex queries"""
        # Session overview view
        session_view = {
            "name": f"{self.collection_prefix}_session_view",
            "type": "arangosearch",
            "properties": {
                "links": {
                    self.collections["components"]: {
                        "analyzers": ["text_en"],
                        "fields": {
                            "content.raw_content": {},
                            "metadata.session_title": {},
                            "component_type": {},
                        },
                    }
                }
            },
        }

        self.logger.info("📊 Creating session overview view")

    async def store_parsed_file(
        self,
        file_path: str,
        components: list[AtomicComponent],
        relationships: list[AtomicRelationship],
        metadata: dict = None,
    ) -> dict:
        """Store complete parsed file with all components and relationships"""
        try:
            start_time = datetime.utcnow()

            # Store file metadata
            file_record = await self._store_file_metadata(
                file_path, components, relationships, metadata
            )

            # Store components in batches
            component_results = await self._store_components_batch(
                components, file_path
            )

            # Store relationships in batches
            relationship_results = await self._store_relationships_batch(relationships)

            # Store specialized collections
            specialized_results = await self._store_specialized_collections(
                components, relationships
            )

            # Update session aggregates
            session_id = components[0].session_id if components else ""
            session_update = await self._update_session_aggregates(
                session_id, components
            )

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "file_path": file_path,
                "file_record_id": file_record.get("_key"),
                "components_stored": len(component_results.get("stored", [])),
                "relationships_stored": len(relationship_results.get("stored", [])),
                "session_id": session_id,
                "processing_time_seconds": processing_time,
                "storage_timestamp": end_time.isoformat(),
            }

            self.logger.info(
                f"✅ Stored file {file_path}: {result['components_stored']} components, {result['relationships_stored']} relationships in {processing_time:.2f}s"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Failed to store parsed file {file_path}: {e}")
            return {"success": False, "error": str(e)}

    async def _store_file_metadata(
        self,
        file_path: str,
        components: list[AtomicComponent],
        relationships: list[AtomicRelationship],
        metadata: dict = None,
    ) -> dict:
        """Store file-level metadata"""
        try:
            from src.shared.database.core.cognitive_database import (
                mcp_cognitive_tools_arango_modify,
            )
        except ImportError:
            # Mock for testing when database tools not available
            async def mcp_cognitive_tools_arango_modify(*args, **kwargs):
                return {
                    "success": False,
                    "document": {},
                    "error": "Database tools not available",
                }

        file_info = Path(file_path)
        session_id = components[0].session_id if components else ""

        file_record = {
            "file_path": file_path,
            "file_name": file_info.name,
            "file_size": file_info.stat().st_size if file_info.exists() else 0,
            "session_id": session_id,
            "component_count": len(components),
            "relationship_count": len(relationships),
            "component_types": list(set(c.component_type.value for c in components)),
            "relationship_types": list(
                set(r.relationship_type.value for r in relationships)
            ),
            "processing_metadata": metadata or {},
            "parsed_timestamp": datetime.utcnow().isoformat(),
            "analysis": {
                "total_characters": sum(len(c.raw_content) for c in components),
                "total_words": sum(len(c.raw_content.split()) for c in components),
                "complexity_score": (
                    sum(c.analysis.get("complexity_score", 0) for c in components)
                    / len(components)
                    if components
                    else 0
                ),
                "turn_count": len(
                    [
                        c
                        for c in components
                        if c.component_type == ComponentType.CONVERSATION_TURN
                    ]
                ),
            },
        }

        result = await mcp_cognitive_tools_arango_modify(
            operation="insert",
            collection=self.collections["files"],
            document=file_record,
        )

        return result.get("document", {})

    async def _store_components_batch(
        self, components: list[AtomicComponent], file_path: str
    ) -> dict:
        """Store components in optimized batches"""
        from src.shared.database.core.cognitive_database import (
            mcp_cognitive_tools_arango_modify,
        )

        stored_components = []
        batch_size = 100

        for i in range(0, len(components), batch_size):
            batch = components[i : i + batch_size]

            # Convert to ArangoDB documents
            documents = []
            for component in batch:
                doc = component.to_arango_document()
                doc["positioning"]["file_path"] = file_path
                documents.append(doc)

            # Batch insert
            for doc in documents:
                result = await mcp_cognitive_tools_arango_modify(
                    operation="insert",
                    collection=self.collections["components"],
                    document=doc,
                )
                if result.get("success"):
                    stored_components.append(result.get("document", {}))

            self.logger.info(
                f"📦 Stored batch {i//batch_size + 1}: {len(batch)} components"
            )

        return {"stored": stored_components}

    async def _store_relationships_batch(
        self, relationships: list[AtomicRelationship]
    ) -> dict:
        """Store relationships in optimized batches"""
        from src.shared.database.core.cognitive_database import (
            mcp_cognitive_tools_arango_modify,
        )

        stored_relationships = []
        batch_size = 200

        for i in range(0, len(relationships), batch_size):
            batch = relationships[i : i + batch_size]

            # Convert to ArangoDB edges
            edges = [rel.to_arango_edge() for rel in batch]

            # Batch insert
            for edge in edges:
                result = await mcp_cognitive_tools_arango_modify(
                    operation="insert",
                    collection=self.collections["relationships"],
                    document=edge,
                )
                if result.get("success"):
                    stored_relationships.append(result.get("document", {}))

            self.logger.info(
                f"🔗 Stored batch {i//batch_size + 1}: {len(batch)} relationships"
            )

        return {"stored": stored_relationships}

    async def _store_specialized_collections(
        self, components: list[AtomicComponent], relationships: list[AtomicRelationship]
    ) -> dict:
        """Store components in specialized collections for optimized queries"""
        try:
            results = {
                "code_blocks": [],
                "tool_interactions": [],
                "temporal_sequence": [],
                "text_content": [],
                "tokens": [],
                "characters": [],
            }

            # Categorize components by type for specialized storage
            for component in components:
                # Store code blocks with enhanced analysis
                if component.component_type == ComponentType.CODE_BLOCK:
                    code_doc = self._create_code_block_document(component)
                    results["code_blocks"].append(code_doc)

                # Store tool interactions (calls + results + parameters)
                elif component.component_type in [
                    ComponentType.TOOL_CALL,
                    ComponentType.TOOL_RESULT,
                    ComponentType.TOOL_PARAMETER,
                ]:
                    tool_doc = self._create_tool_interaction_document(component)
                    results["tool_interactions"].append(tool_doc)

                # Store text content for NLP processing
                elif component.component_type == ComponentType.TEXT_CONTENT:
                    text_doc = self._create_text_content_document(component)
                    results["text_content"].append(text_doc)

                # Store tokens for linguistic analysis
                elif component.component_type == ComponentType.TOKEN:
                    token_doc = self._create_token_document(component)
                    results["tokens"].append(token_doc)

                # Store characters for character-level analysis
                elif component.component_type == ComponentType.CHARACTER:
                    char_doc = self._create_character_document(component)
                    results["characters"].append(char_doc)

            # Create temporal sequence from relationships
            temporal_docs = self._create_temporal_sequence_documents(relationships)
            results["temporal_sequence"] = temporal_docs

            # Store each specialized collection
            storage_results = {}
            for collection_type, documents in results.items():
                if documents:
                    storage_results[
                        collection_type
                    ] = await self._batch_store_documents(
                        self.collections[collection_type], documents
                    )

            total_stored = sum(len(docs) for docs in results.values())
            self.logger.info(
                f"📊 Stored {total_stored} documents across specialized collections"
            )

            return {
                "success": True,
                "results": storage_results,
                "total_stored": total_stored,
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to store specialized collections: {e}")
            return {"success": False, "error": str(e)}

    def _create_code_block_document(self, component: AtomicComponent) -> dict:
        """Create optimized code block document"""
        base_doc = component.to_arango_document()

        # Enhanced code analysis
        language = component.processed_content.get("language", "")
        content = component.processed_content.get("content", "")

        base_doc.update(
            {
                "code_analysis": {
                    "language": language,
                    "lines_of_code": content.count("\n") + 1,
                    "complexity_indicators": self._analyze_code_complexity(
                        content, language
                    ),
                    "syntax_elements": self._extract_syntax_elements(content, language),
                    "imports_exports": self._extract_imports_exports(content, language),
                },
                "searchable_content": content.lower(),  # For faster text search
                "language_category": self._categorize_language(language),
            }
        )

        return base_doc

    def _create_tool_interaction_document(self, component: AtomicComponent) -> dict:
        """Create optimized tool interaction document"""
        base_doc = component.to_arango_document()

        # Enhanced tool analysis
        if component.component_type == ComponentType.TOOL_CALL:
            tool_name = component.processed_content.get("tool_name", "")
            base_doc.update(
                {
                    "tool_analysis": {
                        "tool_category": self._categorize_tool(tool_name),
                        "complexity_score": component.analysis.get(
                            "complexity_score", 0
                        ),
                        "parameter_count": len(
                            component.processed_content.get("parameters", [])
                        ),
                        "estimated_execution_time": component.analysis.get(
                            "estimated_execution_time", 0
                        ),
                    }
                }
            )
        elif component.component_type == ComponentType.TOOL_RESULT:
            base_doc.update(
                {
                    "result_analysis": {
                        "success_indicator": component.processed_content.get(
                            "success_indicator", True
                        ),
                        "output_type": component.analysis.get("output_type", "unknown"),
                        "content_size": component.analysis.get("content_size", 0),
                        "contains_data": component.analysis.get("contains_data", False),
                    }
                }
            )

        return base_doc

    def _create_text_content_document(self, component: AtomicComponent) -> dict:
        """Create optimized text content document for NLP"""
        base_doc = component.to_arango_document()

        content = component.raw_content
        base_doc.update(
            {
                "nlp_analysis": {
                    "word_count": len(content.split()),
                    "sentence_count": len([s for s in content.split(".") if s.strip()]),
                    "readability_score": self._calculate_readability(content),
                    "sentiment_indicators": self._extract_sentiment_indicators(content),
                    "topic_keywords": self._extract_topic_keywords(content),
                },
                "searchable_text": content.lower(),
                "language_detection": "en",  # Default, could be enhanced with detection
            }
        )

        return base_doc

    def _create_token_document(self, component: AtomicComponent) -> dict:
        """Create optimized token document for linguistic analysis"""
        base_doc = component.to_arango_document()

        token_content = component.processed_content.get("token_content", "")
        base_doc.update(
            {
                "linguistic_analysis": {
                    "token_type": component.processed_content.get(
                        "token_type", "unknown"
                    ),
                    "word_index": component.processed_content.get("word_index"),
                    "is_programming_keyword": component.analysis.get(
                        "is_programming_keyword", False
                    ),
                    "semantic_category": component.analysis.get(
                        "semantic_category", "unknown"
                    ),
                    "frequency_weight": 1.0,  # Could be calculated across corpus
                },
                "normalized_token": token_content.lower(),
                "token_length": len(token_content),
            }
        )

        return base_doc

    def _create_character_document(self, component: AtomicComponent) -> dict:
        """Create optimized character document for character-level analysis"""
        base_doc = component.to_arango_document()

        char = component.processed_content.get("character", "")
        base_doc.update(
            {
                "character_analysis": {
                    "character_code": component.processed_content.get(
                        "character_code", 0
                    ),
                    "character_category": component.processed_content.get(
                        "character_category", "unknown"
                    ),
                    "is_printable": char.isprintable(),
                    "is_ascii": ord(char) < 128,
                    "unicode_category": self._get_unicode_category(char),
                },
                "position_analysis": {
                    "character_index_in_token": component.processed_content.get(
                        "character_index_in_token", 0
                    ),
                    "character_index_in_component": component.processed_content.get(
                        "character_index_in_component", 0
                    ),
                },
            }
        )

        return base_doc

    def _create_temporal_sequence_documents(
        self, relationships: list[AtomicRelationship]
    ) -> list[dict]:
        """Create temporal sequence documents for time-series analysis"""
        temporal_docs = []

        # Filter temporal relationships
        temporal_relationships = [
            rel
            for rel in relationships
            if rel.relationship_type
            in [
                RelationshipType.FOLLOWS,
                RelationshipType.PRECEDES,
                RelationshipType.SIMULTANEOUS,
            ]
        ]

        for rel in temporal_relationships:
            doc = rel.to_arango_edge()
            doc.update(
                {
                    "sequence_analysis": {
                        "temporal_order": rel.temporal_order,
                        "sequence_distance": rel.sequence_distance,
                        "time_distance": rel.time_distance,
                        "relationship_strength": rel.relationship_strength,
                    },
                    "temporal_category": rel.relationship_type.value,
                }
            )
            temporal_docs.append(doc)

        return temporal_docs

    async def _batch_store_documents(
        self, collection_name: str, documents: list[dict]
    ) -> dict:
        """Store documents in batches to specified collection"""
        try:
            from src.shared.database.core.cognitive_database import (
                mcp_cognitive_tools_arango_modify,
            )
        except ImportError:
            return {"success": False, "error": "Database tools not available"}

        stored_docs = []
        errors = []

        # Store in batches of 100
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            for doc in batch:
                try:
                    result = await mcp_cognitive_tools_arango_modify(
                        operation="insert", collection=collection_name, document=doc
                    )
                    if result.get("success"):
                        stored_docs.append(doc["_key"])
                    else:
                        errors.append(
                            f"Failed to store {doc.get('_key', 'unknown')}: {result.get('error', 'unknown error')}"
                        )
                except Exception as e:
                    errors.append(f"Exception storing document: {e}")

        return {"success": len(errors) == 0, "stored": stored_docs, "errors": errors}

    # Helper methods for enhanced analysis
    def _analyze_code_complexity(self, content: str, language: str) -> dict:
        """Analyze code complexity indicators"""
        return {
            "cyclomatic_complexity": content.count("if")
            + content.count("for")
            + content.count("while"),
            "nesting_depth": (
                max(line.count("    ") for line in content.split("\n"))
                if content
                else 0
            ),
            "function_count": (
                content.count("def ")
                if language == "python"
                else content.count("function")
            ),
            "comment_ratio": len(
                [line for line in content.split("\n") if line.strip().startswith("#")]
            )
            / max(len(content.split("\n")), 1),
        }

    def _extract_syntax_elements(self, content: str, language: str) -> list[str]:
        """Extract syntax elements from code"""
        elements = []
        if language == "python":
            elements.extend(
                [
                    "def",
                    "class",
                    "import",
                    "from",
                    "if",
                    "for",
                    "while",
                    "try",
                    "except",
                ]
            )
        elif language in ["javascript", "typescript"]:
            elements.extend(
                [
                    "function",
                    "const",
                    "let",
                    "var",
                    "if",
                    "for",
                    "while",
                    "try",
                    "catch",
                ]
            )

        return [elem for elem in elements if elem in content]

    def _extract_imports_exports(self, content: str, language: str) -> list[str]:
        """Extract import/export statements"""
        imports = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if (
                language == "python"
                and (line.startswith("import ") or line.startswith("from "))
                or language in ["javascript", "typescript"]
                and (line.startswith("import ") or line.startswith("export "))
            ):
                imports.append(line)

        return imports

    def _categorize_language(self, language: str) -> str:
        """Categorize programming language"""
        categories = {
            "python": "interpreted",
            "javascript": "interpreted",
            "typescript": "compiled_to_js",
            "java": "compiled",
            "cpp": "compiled",
            "c": "compiled",
            "go": "compiled",
            "rust": "compiled",
        }
        return categories.get(language.lower(), "unknown")

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by function"""
        if "file" in tool_name.lower() or "read" in tool_name.lower():
            return "file_operations"
        elif "search" in tool_name.lower() or "grep" in tool_name.lower():
            return "search_operations"
        elif "run" in tool_name.lower() or "command" in tool_name.lower():
            return "execution_operations"
        elif "edit" in tool_name.lower() or "write" in tool_name.lower():
            return "modification_operations"
        else:
            return "other"

    def _calculate_readability(self, content: str) -> float:
        """Calculate simple readability score"""
        words = content.split()
        if not words:
            return 0.0

        sentences = [s for s in content.split(".") if s.strip()]
        avg_words_per_sentence = len(words) / max(len(sentences), 1)
        avg_chars_per_word = sum(len(word) for word in words) / len(words)

        # Simple readability metric (lower is more readable)
        return min(avg_words_per_sentence / 20.0 + avg_chars_per_word / 10.0, 1.0)

    def _extract_sentiment_indicators(self, content: str) -> dict:
        """Extract basic sentiment indicators"""
        positive_words = ["good", "great", "excellent", "success", "working", "correct"]
        negative_words = ["error", "failed", "wrong", "issue", "problem", "broken"]

        content_lower = content.lower()

        return {
            "positive_indicators": sum(
                1 for word in positive_words if word in content_lower
            ),
            "negative_indicators": sum(
                1 for word in negative_words if word in content_lower
            ),
            "overall_sentiment": "neutral",  # Could be enhanced with ML
        }

    def _extract_topic_keywords(self, content: str) -> list[str]:
        """Extract topic keywords (simple implementation)"""
        # Remove common words and extract meaningful terms
        common_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "a",
            "an",
        }
        words = [word.lower().strip(".,!?;:") for word in content.split()]
        keywords = [
            word for word in words if len(word) > 3 and word not in common_words
        ]

        # Return top 10 most frequent
        from collections import Counter

        return [word for word, count in Counter(keywords).most_common(10)]

    def _get_unicode_category(self, char: str) -> str:
        """Get Unicode category for character"""
        import unicodedata

        try:
            return unicodedata.category(char)
        except:
            return "Unknown"

    async def _update_session_aggregates(
        self, session_id: str, components: list[AtomicComponent]
    ) -> dict:
        """Update session-level aggregated data"""
        from src.shared.database.core.cognitive_database import (
            mcp_cognitive_tools_arango_modify,
        )

        if not session_id:
            return {"success": False, "error": "No session ID"}

        # Calculate session statistics
        session_stats = {
            "session_id": session_id,
            "component_count": len(components),
            "turn_count": len(
                [
                    c
                    for c in components
                    if c.component_type == ComponentType.CONVERSATION_TURN
                ]
            ),
            "tool_call_count": len(
                [c for c in components if c.component_type == ComponentType.TOOL_CALL]
            ),
            "code_block_count": len(
                [c for c in components if c.component_type == ComponentType.CODE_BLOCK]
            ),
            "thinking_block_count": len(
                [
                    c
                    for c in components
                    if c.component_type == ComponentType.THINKING_BLOCK
                ]
            ),
            "total_words": sum(len(c.raw_content.split()) for c in components),
            "total_characters": sum(len(c.raw_content) for c in components),
            "session_title": components[0].session_title if components else "",
            "session_timestamp": (
                components[0].session_timestamp.isoformat()
                if components and components[0].session_timestamp
                else None
            ),
            "last_updated": datetime.utcnow().isoformat(),
            "analysis": {
                "complexity_score": (
                    sum(c.analysis.get("complexity_score", 0) for c in components)
                    / len(components)
                    if components
                    else 0
                ),
                "languages_used": list(
                    set(
                        c.processed_content.get("language", "")
                        for c in components
                        if c.component_type == ComponentType.CODE_BLOCK
                        and c.processed_content.get("language")
                    )
                ),
                "tools_used": list(
                    set(
                        c.processed_content.get("tool_name", "")
                        for c in components
                        if c.component_type == ComponentType.TOOL_CALL
                        and c.processed_content.get("tool_name")
                    )
                ),
            },
        }

        # Upsert session record
        result = await mcp_cognitive_tools_arango_modify(
            operation="upsert",
            collection=self.collections["sessions"],
            document=session_stats,
            match_fields=["session_id"],
        )

        return result

    async def query_components(
        self,
        component_type: ComponentType | None = None,
        session_id: str | None = None,
        file_path: str | None = None,
        content_search: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query components with flexible filters"""
        from src.shared.database.core.cognitive_database import (
            mcp_cognitive_tools_arango_search,
        )

        # Build query based on parameters
        if content_search:
            result = await mcp_cognitive_tools_arango_search(
                search_type="content",
                collection=self.collections["components"],
                content=content_search,
                limit=limit,
            )
        elif component_type:
            result = await mcp_cognitive_tools_arango_search(
                search_type="type",
                collection=self.collections["components"],
                document_type=component_type.value,
                limit=limit,
            )
        else:
            result = await mcp_cognitive_tools_arango_search(
                search_type="recent",
                collection=self.collections["components"],
                hours=24,
                limit=limit,
            )

        return result.get("documents", [])

    async def query_relationships(
        self,
        relationship_type: RelationshipType | None = None,
        source_component_id: str | None = None,
        min_confidence: float = 0.0,
        limit: int = 100,
    ) -> list[dict]:
        """Query relationships with filters"""
        from src.shared.database.core.cognitive_database import (
            mcp_cognitive_tools_arango_search,
        )

        # Query by relationship type
        if relationship_type:
            result = await mcp_cognitive_tools_arango_search(
                search_type="type",
                collection=self.collections["relationships"],
                document_type=relationship_type.value,
                limit=limit,
            )
        else:
            result = await mcp_cognitive_tools_arango_search(
                search_type="recent",
                collection=self.collections["relationships"],
                hours=24,
                limit=limit,
            )

        # Filter by confidence if specified
        documents = result.get("documents", [])
        if min_confidence > 0.0:
            documents = [
                doc
                for doc in documents
                if doc.get("semantic_data", {}).get("confidence", 0) >= min_confidence
            ]

        return documents

    async def get_session_overview(self, session_id: str) -> dict:
        """Get comprehensive session overview"""
        from src.shared.database.core.cognitive_database import (
            mcp_cognitive_tools_arango_search,
        )

        # Get session metadata
        session_result = await mcp_cognitive_tools_arango_search(
            search_type="id",
            collection=self.collections["sessions"],
            document_id=session_id,
        )

        session_data = session_result.get("documents", [{}])[0]

        # Get session components
        components_result = await mcp_cognitive_tools_arango_search(
            search_type="content",
            collection=self.collections["components"],
            content=session_id,
            fields=["metadata.session_id"],
            limit=1000,
        )

        components = components_result.get("documents", [])

        return {
            "session_metadata": session_data,
            "component_count": len(components),
            "component_breakdown": self._analyze_component_breakdown(components),
            "timeline": self._build_session_timeline(components),
            "insights": self._generate_session_insights(components),
        }

    def _analyze_component_breakdown(self, components: list[dict]) -> dict:
        """Analyze breakdown of component types"""
        breakdown = {}
        for component in components:
            comp_type = component.get("component_type", "unknown")
            breakdown[comp_type] = breakdown.get(comp_type, 0) + 1
        return breakdown

    def _build_session_timeline(self, components: list[dict]) -> list[dict]:
        """Build chronological timeline of session"""
        # Sort by component sequence
        sorted_components = sorted(
            components,
            key=lambda x: x.get("positioning", {}).get("component_sequence", 0),
        )

        timeline = []
        for i, component in enumerate(
            sorted_components[:20]
        ):  # Limit to first 20 for overview
            timeline.append(
                {
                    "sequence": i + 1,
                    "type": component.get("component_type"),
                    "content_preview": component.get("content", {}).get(
                        "raw_content", ""
                    )[:100]
                    + "...",
                    "timestamp": component.get("metadata", {}).get(
                        "processing_timestamp"
                    ),
                }
            )

        return timeline

    def _generate_session_insights(self, components: list[dict]) -> dict:
        """Generate analytical insights about session"""
        total_words = sum(
            len(comp.get("content", {}).get("raw_content", "").split())
            for comp in components
        )

        tool_calls = [
            comp for comp in components if comp.get("component_type") == "tool_call"
        ]

        return {
            "conversation_length": f"{total_words:,} words",
            "primary_activities": self._identify_primary_activities(components),
            "tool_usage_pattern": self._analyze_tool_usage(tool_calls),
            "complexity_assessment": self._assess_session_complexity(components),
        }

    def _identify_primary_activities(self, components: list[dict]) -> list[str]:
        """Identify primary activities in session"""
        activities = []

        if any(comp.get("component_type") == "code_block" for comp in components):
            activities.append("coding")

        if any(comp.get("component_type") == "tool_call" for comp in components):
            activities.append("tool_usage")

        if any(comp.get("component_type") == "thinking_block" for comp in components):
            activities.append("problem_solving")

        return activities

    def _analyze_tool_usage(self, tool_calls: list[dict]) -> dict:
        """Analyze patterns in tool usage"""
        tools_used = {}
        for call in tool_calls:
            tool_name = (
                call.get("content", {})
                .get("processed_content", {})
                .get("tool_name", "unknown")
            )
            tools_used[tool_name] = tools_used.get(tool_name, 0) + 1

        return {
            "total_calls": len(tool_calls),
            "unique_tools": len(tools_used),
            "most_used": (
                max(tools_used.items(), key=lambda x: x[1]) if tools_used else None
            ),
            "tool_distribution": tools_used,
        }

    def _assess_session_complexity(self, components: list[dict]) -> str:
        """Assess overall session complexity"""
        component_count = len(components)

        if component_count > 200:
            return "high"
        elif component_count > 50:
            return "medium"
        else:
            return "low"


# Usage example for testing
async def main():
    """Test database storage"""
    storage = SpecStoryDatabaseStorage()

    # Initialize database
    success = await storage.initialize_database()
    if success:
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")


if __name__ == "__main__":
    asyncio.run(main())
