"""Chat data source adapter."""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Union

import numpy as np
import structlog

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer

logger = structlog.get_logger(__name__)


class ChatAdapter(BaseAdapter):
    """Adapter for ingesting chat/conversation data.

    Supports multiple chat formats:
    - JSONL files with conversation logs
    - JSON conversation exports
    - Real-time chat streams
    - Chat API integrations
    """

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get default configuration for chat adapter."""
        return AdapterConfig(
            adapter_id="chat",
            source_type="chat",
            batch_mode=BatchMode.STREAMING,
            batch_size=50,
            generate_embeddings=True,
            generate_summaries=False,
            extract_relationships=True,
            source_config={
                "input_format": "jsonl",  # jsonl, json, api, stream
                "file_patterns": ["*.jsonl", "*.json"],
                "watch_directories": [],
                "api_endpoint": None,
                "api_key": None,
                "message_filters": [],
                "include_system_messages": True,
                "include_metadata": True,
                "conversation_timeout_minutes": 60,
                "extract_entities": True,
                "entity_extraction_config": {
                    "enable_url_detection": True,
                    "enable_code_detection": True,
                    "enable_mention_detection": True,
                    "enable_issue_detection": True,
                    "enable_tech_keyword_detection": True,
                    "enable_email_detection": True,
                    "enable_file_path_detection": True,
                    "enable_command_detection": True,
                    "enable_timestamp_detection": True,
                    "enable_named_entity_recognition": True,
                    "max_entities_per_type": 50,
                },
                "embedding_config": {
                    "service": "sentence_transformers",  # openai, sentence_transformers, simple
                    "model": "all-MiniLM-L6-v2",
                    "api_key": None,  # Set this for OpenAI
                    "max_tokens": 8192,
                    "batch_size": 32,
                },
                "relationship_detection_config": {
                    "enable_entity_relationships": True,
                    "enable_content_similarity": True,
                    "enable_actor_relationships": True,
                    "similarity_threshold": 0.2,
                    "entity_overlap_threshold": 0.3,
                },
            },
        )

    def __init__(self, config: AdapterConfig):
        """Initialize chat adapter."""
        super().__init__(config)
        self.transformer = DataTransformer()
        self._processed_files: set = set()
        self._processed_message_hashes: set = set()  # For deduplication
        self._conversation_contexts: Dict[str, List[ContextItem]] = {}
        self._last_activity: Dict[str, datetime] = {}
        self._checkpoint_file = None  # For incremental processing

    async def initialize(self) -> None:
        """Initialize chat adapter resources."""
        self.logger.info("Initializing chat adapter")

        # Validate configuration
        self._validate_configuration()

        # Initialize file tracking
        self._processed_files = set()

        # Set up directory watching if configured
        watch_dirs = self.config.source_config.get("watch_directories", [])
        if watch_dirs:
            self.logger.info("Setting up directory watching", directories=watch_dirs)
            # Validate that watch directories exist
            for watch_dir in watch_dirs:
                if not Path(watch_dir).exists():
                    self.logger.warning(
                        "Watch directory does not exist", directory=watch_dir
                    )

        # Set up checkpoint file for incremental processing
        self._setup_checkpoint_file()

        # Load processed message hashes for deduplication
        await self._load_processed_hashes()

        self.logger.info("Chat adapter initialized")

    def _validate_configuration(self) -> None:
        """Validate adapter configuration for common issues."""
        input_format = self.config.source_config.get("input_format", "jsonl")
        if input_format not in ["jsonl", "json", "api", "stream"]:
            raise ValueError(
                f"Unsupported input format: {input_format}. "
                f"Supported formats: jsonl, json, api, stream"
            )

        # Validate entity extraction config if present
        entity_config = self.config.source_config.get("entity_extraction_config", {})
        if entity_config:
            max_entities = entity_config.get("max_entities_per_type", 50)
            if not isinstance(max_entities, int) or max_entities < 1:
                raise ValueError("max_entities_per_type must be a positive integer")

        # Validate embedding config if embeddings are enabled
        if self.config.generate_embeddings:
            embedding_config = self.config.source_config.get("embedding_config", {})
            service = embedding_config.get("service", "simple")
            if service not in ["openai", "sentence_transformers", "simple"]:
                raise ValueError(
                    f"Unsupported embedding service: {service}. "
                    f"Supported services: openai, sentence_transformers, simple"
                )

            if service == "openai" and not embedding_config.get("api_key"):
                self.logger.warning(
                    "OpenAI embedding service selected but no API key provided"
                )

        # Validate batch configuration
        if self.config.batch_size < 1:
            raise ValueError("batch_size must be at least 1")

        self.logger.debug("Configuration validation passed")

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch chat messages from configured sources."""
        input_format = self.config.source_config.get("input_format", "jsonl")

        if input_format == "jsonl":
            async for item in self._fetch_from_jsonl_files(since, until, limit):
                yield item
        elif input_format == "json":
            async for item in self._fetch_from_json_files(since, until, limit):
                yield item
        elif input_format == "api":
            async for item in self._fetch_from_api(since, until, limit):
                yield item
        elif input_format == "stream":
            async for item in self._fetch_from_stream(since, until, limit):
                yield item

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform raw chat message into ContextItem."""
        # Create base context item
        source_id = (
            raw_item.get("message_id")
            or raw_item.get("id")
            or str(raw_item.get("timestamp", ""))
        )

        item = self.transformer.create_base_context_item(
            source_type="chat", source_id=source_id, raw_data=raw_item
        )

        # Chat-specific fields
        item.title = self._extract_message_title(raw_item)
        item.content = raw_item.get("content") or raw_item.get("text") or ""

        # Extract entities from content (if enabled)
        if self.config.source_config.get("extract_entities", True):
            try:
                extracted_entities = await self._extract_entities_enhanced(item.content)
                if extracted_entities:
                    if not item.metrics:
                        item.metrics = {}
                    item.metrics["extracted_entities"] = extracted_entities
                    item.metrics["entities_extracted_count"] = sum(
                        len(entities) for entities in extracted_entities.values()
                    )
                    self.logger.debug(
                        "Extracted entities from message",
                        entity_types=list(extracted_entities.keys()),
                        total_count=item.metrics["entities_extracted_count"],
                    )
            except Exception as e:
                self.logger.warning(
                    "Entity extraction failed for message",
                    error=str(e),
                    message_id=item.source_id,
                )
                # Continue processing even if entity extraction fails
                if not item.metrics:
                    item.metrics = {}
                item.metrics["entity_extraction_error"] = str(e)

        # Generate embeddings for the message content
        if self.config.generate_embeddings and item.content:
            try:
                # Combine title and content for embedding
                embedding_text = f"{item.title or ''} {item.content}".strip()
                if embedding_text:
                    embedding = await self.generate_embedding(embedding_text)
                    if embedding:
                        item.embedding = embedding
                        if not item.metrics:
                            item.metrics = {}
                        item.metrics["embedding_dimensions"] = len(embedding)
                        item.metrics[
                            "embedding_service"
                        ] = self.config.source_config.get("embedding_config", {}).get(
                            "service", "simple"
                        )
                        self.logger.debug(
                            "Generated embedding for message",
                            dimensions=len(embedding),
                            message_id=item.source_id,
                        )
                    else:
                        self.logger.debug(
                            "No embedding generated for message",
                            message_id=item.source_id,
                        )
            except Exception as e:
                self.logger.warning(
                    "Embedding generation failed for message",
                    error=str(e),
                    message_id=item.source_id,
                )
                # Continue processing even if embedding generation fails
                if not item.metrics:
                    item.metrics = {}
                item.metrics["embedding_error"] = str(e)

        # Chat metadata
        item.actor_id = raw_item.get("user_id") or raw_item.get("author") or "unknown"
        item.actor_type = self._determine_actor_type(raw_item)
        item.session_id = raw_item.get("conversation_id") or raw_item.get("session_id")

        # Message-specific metadata
        message_metadata = {
            "message_type": raw_item.get("type", "message"),
            "thread_id": raw_item.get("thread_id"),
            "parent_message_id": raw_item.get("parent_id"),
            "reaction_count": raw_item.get("reactions", 0),
            "edited": raw_item.get("edited", False),
            "attachments": raw_item.get("attachments", []),
        }

        if item.metrics:
            item.metrics.update(message_metadata)
        else:
            item.metrics = message_metadata

        # Set entity type
        item.entity_type = "message"

        # Add conversation context tags
        if item.session_id:
            conversation_tags = self._get_conversation_tags(item.session_id)
            if item.tags:
                item.tags.extend(conversation_tags)
            else:
                item.tags = conversation_tags

        # Apply transformations
        item = await self.transformer.transform_item(item)

        # Check for deduplication
        if self.config.skip_duplicates and item.content_hash:
            if item.content_hash in self._processed_message_hashes:
                self.logger.debug(
                    "Skipping duplicate message", content_hash=item.content_hash
                )
                return None
            else:
                self._processed_message_hashes.add(item.content_hash)

        return item

    async def detect_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships with other chat messages."""
        relationships = []

        # Reply relationships
        parent_id = item.metrics.get("parent_message_id") if item.metrics else None
        if parent_id:
            # Find parent message in context
            for context_item in context_window:
                if context_item.source_id == parent_id:
                    relationships.append(("replies_to", context_item.id, 1.0))
                    break

        # Thread relationships
        thread_id = item.metrics.get("thread_id") if item.metrics else None
        if thread_id:
            for context_item in context_window:
                context_thread = (
                    context_item.metrics.get("thread_id")
                    if context_item.metrics
                    else None
                )
                if context_thread == thread_id and context_item.id != item.id:
                    relationships.append(("same_thread", context_item.id, 0.8))

        # Conversation relationships
        if item.session_id:
            for context_item in context_window:
                if (
                    context_item.session_id == item.session_id
                    and context_item.id != item.id
                ):
                    relationships.append(("same_conversation", context_item.id, 0.6))

        # Temporal relationships (consecutive messages)
        for context_item in context_window[:5]:  # Check recent messages
            time_diff = abs((item.timestamp - context_item.timestamp).total_seconds())
            if time_diff < 300:  # Within 5 minutes
                confidence = max(0.3, 1.0 - (time_diff / 300))
                relationships.append(
                    ("temporal_proximity", context_item.id, confidence)
                )

        # Entity-based relationships
        entity_relationships = await self._detect_entity_relationships(
            item, context_window
        )
        relationships.extend(entity_relationships)

        # Content similarity relationships
        similarity_relationships = await self._detect_content_similarities(
            item, context_window
        )
        relationships.extend(similarity_relationships)

        # Actor interaction relationships
        actor_relationships = self._detect_actor_relationships(item, context_window)
        relationships.extend(actor_relationships)

        return relationships

    async def cleanup(self) -> None:
        """Clean up chat adapter resources including ML models."""
        self.logger.info("Cleaning up chat adapter")

        # Clean up conversation contexts
        self._conversation_contexts.clear()
        self._last_activity.clear()
        self._processed_files.clear()

        # Save processed hashes for next run
        await self._save_processed_hashes()

        # Clean up ML models
        if hasattr(self, "_embedding_model"):
            del self._embedding_model
        if hasattr(self, "_nlp_model"):
            del self._nlp_model

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text content using OpenAI or local embedding service.

        Args:
            text: Text to embed

        Returns:
            Vector embedding or None if generation fails
        """
        if not text or not text.strip():
            return None

        try:
            # Try to use embedding service configured in source_config
            embedding_config = self.config.source_config.get("embedding_config", {})
            service_type = embedding_config.get("service", "openai")

            if service_type == "openai":
                return await self._generate_openai_embedding(text, embedding_config)
            elif service_type == "sentence_transformers":
                return await self._generate_local_embedding(text, embedding_config)
            else:
                # Fallback to simple hash-based embedding for testing
                return self._generate_simple_embedding(text)

        except Exception as e:
            self.logger.warning(
                "Failed to generate embedding", error=str(e), text_length=len(text)
            )
            return None

    async def _generate_openai_embedding(
        self, text: str, config: Dict[str, Any]
    ) -> Optional[List[float]]:
        """Generate embedding using OpenAI API."""
        try:
            import openai

            api_key = config.get("api_key") or config.get("openai_api_key")
            if not api_key:
                self.logger.warning("OpenAI API key not configured for embeddings")
                return None

            client = openai.AsyncOpenAI(api_key=api_key)
            model = config.get("model", "text-embedding-3-small")

            # Truncate text if too long (OpenAI has token limits)
            max_tokens = config.get("max_tokens", 8192)
            if len(text) > max_tokens * 4:  # Rough estimate: 4 chars per token
                text = text[: max_tokens * 4]

            response = await client.embeddings.create(input=text, model=model)

            return response.data[0].embedding

        except ImportError:
            self.logger.warning("OpenAI package not available for embeddings")
            return None
        except Exception as e:
            self.logger.error("OpenAI embedding generation failed", error=str(e))
            return None

    async def _generate_local_embedding(
        self, text: str, config: Dict[str, Any]
    ) -> Optional[List[float]]:
        """Generate embedding using local sentence-transformers."""
        try:
            from sentence_transformers import SentenceTransformer

            model_name = config.get("model", "all-MiniLM-L6-v2")

            # Use cached model if available
            if not hasattr(self, "_embedding_model"):
                self._embedding_model = SentenceTransformer(model_name)

            # Generate embedding
            embedding = self._embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()

        except ImportError:
            self.logger.warning("sentence-transformers package not available")
            return None
        except Exception as e:
            self.logger.error("Local embedding generation failed", error=str(e))
            return None

    def _generate_simple_embedding(
        self, text: str, dimensions: int = 384
    ) -> List[float]:
        """Generate a simple hash-based embedding for testing purposes."""
        # This is a fallback for development/testing
        import hashlib

        # Create multiple hash values to fill the dimension space
        embeddings = []
        for i in range(dimensions // 32 + 1):  # 32 floats per hash
            hash_input = f"{text}_{i}"
            hash_bytes = hashlib.sha256(hash_input.encode()).digest()

            # Convert bytes to floats
            for j in range(0, len(hash_bytes), 4):
                if len(embeddings) >= dimensions:
                    break
                # Convert 4 bytes to a float between -1 and 1
                value = int.from_bytes(hash_bytes[j : j + 4], "big") / (2**31)
                embeddings.append(max(-1.0, min(1.0, value - 1.0)))

        return embeddings[:dimensions]

    # Private methods

    async def _fetch_from_jsonl_files(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from JSONL chat files."""
        patterns = self.config.source_config.get("file_patterns", ["*.jsonl"])
        watch_dirs = self.config.source_config.get("watch_directories", ["."])

        count = 0
        for directory in watch_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for pattern in patterns:
                for file_path in dir_path.glob(pattern):
                    # Skip files that haven't been modified since last run
                    if self._should_skip_file_by_timestamp(file_path, since):
                        continue

                    if str(file_path) in self._processed_files:
                        continue

                    async for item in self._read_jsonl_file(file_path, since, until):
                        if limit and count >= limit:
                            return

                        yield item
                        count += 1

                    self._processed_files.add(str(file_path))

    async def _read_jsonl_file(
        self,
        file_path: Path,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Read messages from a JSONL file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        message = json.loads(line)

                        # Filter by timestamp if specified
                        if since or until:
                            msg_time = self._parse_timestamp(message)
                            if msg_time:
                                if since and msg_time < since:
                                    continue
                                if until and msg_time > until:
                                    continue

                        # Add file metadata
                        message["_source_file"] = str(file_path)
                        message["_source_line"] = line_num

                        yield message

                    except json.JSONDecodeError as e:
                        self.logger.warning(
                            "Invalid JSON in chat file",
                            file=str(file_path),
                            line=line_num,
                            error=str(e),
                        )

        except Exception as e:
            self.logger.error(
                "Error reading chat file", file=str(file_path), error=str(e)
            )

    async def _fetch_from_json_files(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from JSON conversation files."""
        # Implementation for JSON format conversations
        # This would handle full conversation exports
        patterns = self.config.source_config.get("file_patterns", ["*.json"])
        watch_dirs = self.config.source_config.get("watch_directories", ["."])

        count = 0
        for directory in watch_dirs:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for pattern in patterns:
                for file_path in dir_path.glob(pattern):
                    if str(file_path) in self._processed_files:
                        continue

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        # Handle different JSON structures
                        if isinstance(data, list):
                            messages = data
                        elif isinstance(data, dict):
                            messages = data.get("messages", [data])
                        else:
                            continue

                        for message in messages:
                            if limit and count >= limit:
                                return

                            # Filter by timestamp
                            if since or until:
                                msg_time = self._parse_timestamp(message)
                                if msg_time:
                                    if since and msg_time < since:
                                        continue
                                    if until and msg_time > until:
                                        continue

                            message["_source_file"] = str(file_path)
                            yield message
                            count += 1

                        self._processed_files.add(str(file_path))

                    except Exception as e:
                        self.logger.error(
                            "Error reading JSON chat file",
                            file=str(file_path),
                            error=str(e),
                        )

    async def _fetch_from_api(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from chat API."""
        # Implementation for API-based chat ingestion
        # This would integrate with Slack, Discord, Teams, etc.
        endpoint = self.config.source_config.get("api_endpoint")
        if not endpoint:
            return

        # API implementation would go here
        self.logger.info("API-based chat ingestion not yet implemented")
        return
        yield  # Make this a generator

    async def _fetch_from_stream(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from real-time chat stream."""
        # Implementation for streaming chat data
        # This would handle WebSocket connections, etc.
        self.logger.info("Streaming chat ingestion not yet implemented")
        return
        yield  # Make this a generator

    def _extract_message_title(self, message: Dict[str, Any]) -> str:
        """Extract a title from a chat message."""
        content = message.get("content") or message.get("text") or ""

        # Use first line as title, truncated
        first_line = content.split("\n")[0].strip()
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."

        return first_line or f"Message {message.get('id', 'unknown')}"

    def _determine_actor_type(self, message: Dict[str, Any]) -> str:
        """Determine if message is from human, AI, or system."""
        user_id = message.get("user_id") or message.get("author") or ""
        message_type = message.get("type", "")

        # Check for bot indicators
        if (
            "bot" in user_id.lower()
            or "ai" in user_id.lower()
            or message_type == "bot"
            or message.get("is_bot", False)
        ):
            return "ai"

        # Check for system indicators
        if (
            "system" in user_id.lower()
            or message_type == "system"
            or message.get("is_system", False)
        ):
            return "system"

        return "human"

    def _parse_timestamp(self, message: Dict[str, Any]) -> Optional[datetime]:
        """Parse timestamp from message."""
        timestamp_fields = ["timestamp", "created_at", "time", "date"]

        for field in timestamp_fields:
            if field in message:
                try:
                    value = message[field]
                    if isinstance(value, str):
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    elif isinstance(value, (int, float)):
                        return datetime.fromtimestamp(value)
                except (ValueError, TypeError):
                    continue

        return None

    def _get_conversation_tags(self, session_id: str) -> List[str]:
        """Get tags based on conversation context."""
        tags = ["conversation"]

        # Add session-based tags
        if session_id:
            tags.append(f"session_{session_id[:8]}")

        # Add activity-based tags
        if session_id in self._last_activity:
            last_activity = self._last_activity[session_id]
            time_since_activity = (datetime.utcnow() - last_activity).total_seconds()

            if time_since_activity < 300:  # 5 minutes
                tags.append("active_conversation")
            elif time_since_activity < 3600:  # 1 hour
                tags.append("recent_conversation")
            else:
                tags.append("historical_conversation")

        return tags

    async def _extract_entities_enhanced(self, content: str) -> Dict[str, List[str]]:
        """Enhanced entity extraction with configurable detection methods.

        Args:
            content: Message content to analyze

        Returns:
            Dictionary of entity types and their values
        """
        if not content:
            return {}

        entities = {}
        config = self.config.source_config.get("entity_extraction_config", {})

        # URL detection
        if config.get("enable_url_detection", True):
            urls = self._extract_urls(content)
            if urls:
                entities["urls"] = urls

        # Email detection
        if config.get("enable_email_detection", True):
            emails = self._extract_emails(content)
            if emails:
                entities["email_addresses"] = emails

        # File path detection
        if config.get("enable_file_path_detection", True):
            file_paths = self._extract_file_paths(content)
            if file_paths:
                entities["file_paths"] = file_paths

        # Code reference detection
        if config.get("enable_code_detection", True):
            code_refs = self._extract_code_references(content)
            if code_refs:
                entities["code_references"] = code_refs

        # Mention detection
        if config.get("enable_mention_detection", True):
            mentions = self._extract_mentions(content)
            if mentions:
                entities["mentions"] = mentions

        # Issue/ticket detection
        if config.get("enable_issue_detection", True):
            issues = self._extract_issues(content)
            if issues:
                entities["issues"] = issues

        # Command detection
        if config.get("enable_command_detection", True):
            commands = self._extract_commands(content)
            if commands:
                entities["commands"] = commands

        # Timestamp detection
        if config.get("enable_timestamp_detection", True):
            timestamps = self._extract_timestamps(content)
            if timestamps:
                entities["timestamps"] = timestamps

        # Technology keyword detection
        if config.get("enable_tech_keyword_detection", True):
            tech_keywords = self._extract_tech_keywords(content)
            if tech_keywords:
                entities["tech_keywords"] = tech_keywords

        # Named entity recognition (if enabled)
        if config.get("enable_named_entity_recognition", False):
            named_entities = await self._extract_named_entities(content)
            if named_entities:
                entities.update(named_entities)

        # Apply max limits
        max_per_type = config.get("max_entities_per_type", 50)
        for entity_type in entities:
            if len(entities[entity_type]) > max_per_type:
                entities[entity_type] = entities[entity_type][:max_per_type]

        return entities

    def _extract_urls(self, content: str) -> List[str]:
        """Extract URLs from content."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|github\.com/[^\s<>"{}|\\^`\[\]]+'
        return list(set(re.findall(url_pattern, content, re.IGNORECASE)))

    def _extract_emails(self, content: str) -> List[str]:
        """Extract email addresses from content."""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        return list(set(re.findall(email_pattern, content)))

    def _extract_file_paths(self, content: str) -> List[str]:
        """Extract file paths from content."""
        # Enhanced file path patterns
        patterns = [
            r'(?:[a-zA-Z]:)?[\\\/]?(?:[^\s\\/:*?"<>|]+[\\\/])*[^\s\\/:*?"<>|]+\.[a-zA-Z0-9]+',  # Full paths with extensions
            r'[./]+[^\s\\/:*?"<>|]+(?:[\\\/][^\s\\/:*?"<>|]+)*',  # Relative paths
            r"[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z0-9]+",  # Simple filename.ext
        ]

        file_paths = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            file_paths.extend(matches)

        # Filter out common false positives
        filtered_paths = []
        for path in file_paths:
            if not any(exclude in path.lower() for exclude in ["http", "www", "@"]):
                filtered_paths.append(path)

        return list(set(filtered_paths))

    def _extract_code_references(self, content: str) -> List[str]:
        """Extract code references from content."""
        patterns = [
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\(\)",  # function()
            r"\bclass\s+[A-Z][a-zA-Z0-9_]*\b",  # class ClassName
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*",  # object.method
            r"`[^`]+`",  # inline code
            r"```[\s\S]*?```",  # code blocks
        ]

        code_refs = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            code_refs.extend(matches)

        return list(set(code_refs))

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract user mentions from content."""
        mention_pattern = r"@[a-zA-Z0-9_-]+"
        return list(set(re.findall(mention_pattern, content)))

    def _extract_issues(self, content: str) -> List[str]:
        """Extract issue/ticket references from content."""
        patterns = [
            r"#\d+",  # #123
            r"\b[A-Z]+-\d+\b",  # PROJ-123
            r"\bissue\s+\d+\b",  # issue 123
            r"\bbug\s+\d+\b",  # bug 123
            r"\bticket\s+\d+\b",  # ticket 123
        ]

        issues = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            issues.extend(matches)

        return list(set(issues))

    def _extract_commands(self, content: str) -> List[str]:
        """Extract shell commands from content."""
        patterns = [
            r"`[^`]+`",  # `command`
            r"\$\s*[a-zA-Z][^\s]*(?:\s+[^\s]+)*",  # $ command args
            r"sudo\s+[a-zA-Z][^\n]*",  # sudo commands
            r"npm\s+[a-zA-Z][^\n]*",  # npm commands
            r"pip\s+[a-zA-Z][^\n]*",  # pip commands
            r"git\s+[a-zA-Z][^\n]*",  # git commands
        ]

        commands = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            commands.extend(matches)

        return list(set(commands))

    def _extract_timestamps(self, content: str) -> List[str]:
        """Extract timestamps and dates from content."""
        patterns = [
            r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",  # ISO format
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # MM/DD/YYYY
            r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\b",  # time
            r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
        ]

        timestamps = []
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            timestamps.extend(matches)

        return list(set(timestamps))

    def _extract_tech_keywords(self, content: str) -> List[str]:
        """Extract technology keywords from content."""
        tech_keywords = [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "rust",
            "go",
            "sql",
            "docker",
            "kubernetes",
            "k8s",
            "aws",
            "gcp",
            "azure",
            "terraform",
            "ansible",
            "react",
            "vue",
            "angular",
            "nodejs",
            "node",
            "express",
            "django",
            "flask",
            "postgres",
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "github",
            "gitlab",
            "jenkins",
            "circleci",
            "travis",
            "github actions",
            "api",
            "rest",
            "graphql",
            "jwt",
            "oauth",
            "ssl",
            "tls",
            "https",
            "microservices",
            "serverless",
            "lambda",
            "devops",
            "ci/cd",
            "mlops",
            "machine learning",
            "ml",
            "ai",
            "artificial intelligence",
            "neural network",
            "deep learning",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
            "numpy",
        ]

        found_keywords = []
        content_lower = content.lower()

        for keyword in tech_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", content_lower):
                found_keywords.append(keyword)

        return found_keywords

    async def _extract_named_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract named entities using NLP if available."""
        try:
            import spacy

            # Use cached model if available
            if not hasattr(self, "_nlp_model"):
                try:
                    self._nlp_model = spacy.load("en_core_web_sm")
                except OSError:
                    self.logger.warning(
                        "spaCy English model not found, skipping named entity recognition"
                    )
                    return {}

            doc = self._nlp_model(content)

            entities = {
                "persons": [],
                "organizations": [],
                "locations": [],
                "technologies": [],
                "dates": [],
                "money": [],
                "misc": [],
            }

            for ent in doc.ents:
                entity_text = ent.text.strip()
                if not entity_text:
                    continue

                if ent.label_ in ["PERSON"]:
                    entities["persons"].append(entity_text)
                elif ent.label_ in ["ORG"]:
                    entities["organizations"].append(entity_text)
                elif ent.label_ in ["GPE", "LOC"]:
                    entities["locations"].append(entity_text)
                elif ent.label_ in ["DATE", "TIME"]:
                    entities["dates"].append(entity_text)
                elif ent.label_ in ["MONEY"]:
                    entities["money"].append(entity_text)
                elif ent.label_ in [
                    "PRODUCT",
                    "EVENT",
                    "WORK_OF_ART",
                    "LAW",
                    "LANGUAGE",
                ]:
                    entities["technologies"].append(entity_text)
                else:
                    entities["misc"].append(entity_text)

            # Remove empty categories and deduplicate
            return {k: list(set(v)) for k, v in entities.items() if v}

        except ImportError:
            self.logger.debug("spaCy not available for named entity recognition")
            return {}
        except Exception as e:
            self.logger.warning("Named entity recognition failed", error=str(e))
            return {}

    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract structured entities from chat message content.

        Args:
            content: Message content to analyze

        Returns:
            Dictionary of entity types and their values
        """
        if not content:
            return {}

        entities = {
            "urls": [],
            "email_addresses": [],
            "file_paths": [],
            "code_references": [],
            "mentions": [],
            "issues": [],
            "commands": [],
            "timestamps": [],
            "tech_keywords": [],
        }

        # URLs (including GitHub, Slack, etc.)
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+|github\.com/[^\s<>"{}|\\^`\[\]]+'
        entities["urls"] = re.findall(url_pattern, content, re.IGNORECASE)

        # Email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        entities["email_addresses"] = re.findall(email_pattern, content)

        # File paths (Unix and Windows)
        file_path_pattern = r'(?:[a-zA-Z]:)?[/\\]?(?:[^\s/\\:*?"<>|]+[/\\])*[^\s/\\:*?"<>|]+\.[a-zA-Z0-9]+|[./]+[^\s/\\:*?"<>|]+(?:[/\\][^\s/\\:*?"<>|]+)*'
        entities["file_paths"] = re.findall(file_path_pattern, content)

        # Code references (function calls, classes, etc.)
        code_patterns = [
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\(\)",  # function()
            r"\bclass\s+[A-Z][a-zA-Z0-9_]*\b",  # class ClassName
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*",  # object.method
        ]
        for pattern in code_patterns:
            entities["code_references"].extend(re.findall(pattern, content))

        # User mentions (@username)
        mention_pattern = r"@[a-zA-Z0-9_-]+"
        entities["mentions"] = re.findall(mention_pattern, content)

        # Issue/ticket references
        issue_patterns = [
            r"#\d+",  # #123
            r"\b[A-Z]+-\d+\b",  # PROJ-123
            r"\bissue\s+\d+\b",  # issue 123
            r"\bbug\s+\d+\b",  # bug 123
        ]
        for pattern in issue_patterns:
            entities["issues"].extend(re.findall(pattern, content, re.IGNORECASE))

        # Shell commands
        command_pattern = r"`[^`]+`|\$\s*[a-zA-Z][^\s]*(?:\s+[^\s]+)*"
        entities["commands"] = re.findall(command_pattern, content)

        # Timestamps and dates
        timestamp_patterns = [
            r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",  # ISO format
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # MM/DD/YYYY
            r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\b",  # time
        ]
        for pattern in timestamp_patterns:
            entities["timestamps"].extend(re.findall(pattern, content, re.IGNORECASE))

        # Technology keywords
        tech_keywords = [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "rust",
            "go",
            "sql",
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
            "terraform",
            "ansible",
            "react",
            "vue",
            "angular",
            "nodejs",
            "express",
            "django",
            "flask",
            "postgres",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "github",
            "gitlab",
            "jenkins",
            "circleci",
            "travis",
        ]
        for keyword in tech_keywords:
            if re.search(rf"\b{keyword}\b", content, re.IGNORECASE):
                entities["tech_keywords"].append(keyword)

        # Remove empty categories and deduplicate
        return {k: list(set(v)) for k, v in entities.items() if v}

    async def _detect_entity_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships based on shared entities."""
        relationships = []

        if not item.metrics or "extracted_entities" not in item.metrics:
            return relationships

        item_entities = item.metrics["extracted_entities"]

        for context_item in context_window:
            if (
                context_item.id == item.id
                or not context_item.metrics
                or "extracted_entities" not in context_item.metrics
            ):
                continue

            context_entities = context_item.metrics["extracted_entities"]
            shared_score = 0.0
            shared_types = 0

            # Calculate shared entity score
            for entity_type in item_entities:
                if entity_type in context_entities:
                    item_set = set(item_entities[entity_type])
                    context_set = set(context_entities[entity_type])
                    intersection = item_set.intersection(context_set)

                    if intersection:
                        # Weight different entity types differently
                        weight = {
                            "urls": 0.9,
                            "file_paths": 0.8,
                            "code_references": 0.7,
                            "issues": 0.8,
                            "mentions": 0.6,
                            "tech_keywords": 0.3,
                        }.get(entity_type, 0.5)

                        overlap_ratio = len(intersection) / max(
                            len(item_set), len(context_set)
                        )
                        shared_score += weight * overlap_ratio
                        shared_types += 1

            # Create relationship if significant overlap
            if shared_score > 0.3:
                confidence = min(0.95, shared_score / max(1, shared_types))
                relationships.append(("shares_entities", context_item.id, confidence))

        return relationships

    async def _detect_content_similarities(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships based on content similarity."""
        relationships = []

        if not item.content or len(item.content.strip()) < 10:
            return relationships

        # Simple keyword-based similarity for now
        # In production, this could use embeddings or TF-IDF
        item_words = set(re.findall(r"\b\w+\b", item.content.lower()))
        if len(item_words) < 3:
            return relationships

        for context_item in context_window[:10]:  # Check recent messages
            if (
                context_item.id == item.id
                or not context_item.content
                or len(context_item.content.strip()) < 10
            ):
                continue

            context_words = set(re.findall(r"\b\w+\b", context_item.content.lower()))
            if len(context_words) < 3:
                continue

            # Calculate Jaccard similarity
            intersection = item_words.intersection(context_words)
            union = item_words.union(context_words)

            if len(union) > 0:
                similarity = len(intersection) / len(union)

                # Only create relationship if significant similarity
                if similarity > 0.2:
                    confidence = min(0.8, similarity * 2)  # Scale and cap confidence
                    relationships.append(
                        ("content_similarity", context_item.id, confidence)
                    )

        return relationships

    def _detect_actor_relationships(
        self, item: ContextItem, context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships based on actor interactions."""
        relationships = []

        if not item.actor_id:
            return relationships

        # Track actor interactions
        for context_item in context_window[:20]:  # Check more messages for patterns
            if context_item.id == item.id or not context_item.actor_id:
                continue

            # Same actor relationship
            if context_item.actor_id == item.actor_id:
                # Calculate recency boost
                time_diff = abs(
                    (item.timestamp - context_item.timestamp).total_seconds()
                )
                if time_diff < 3600:  # Within 1 hour
                    confidence = max(0.4, 1.0 - (time_diff / 3600))
                    relationships.append(("same_actor", context_item.id, confidence))

            # Actor interaction patterns (mentions, replies without explicit parent)
            elif item.content and context_item.actor_id.lower() in item.content.lower():
                relationships.append(("mentions_actor", context_item.id, 0.7))
            elif (
                context_item.content
                and item.actor_id.lower() in context_item.content.lower()
            ):
                relationships.append(("mentioned_by_actor", context_item.id, 0.7))

        return relationships

    # Incremental processing and deduplication methods

    def _setup_checkpoint_file(self) -> None:
        """Set up checkpoint file for tracking processing progress."""
        checkpoint_dir = self.config.source_config.get(
            "checkpoint_directory", "/tmp/chat_adapter_checkpoints"
        )
        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
        self._checkpoint_file = (
            Path(checkpoint_dir) / f"{self.config.adapter_id}_processed_hashes.json"
        )

    async def _load_processed_hashes(self) -> None:
        """Load previously processed message hashes for deduplication."""
        if not self._checkpoint_file or not self._checkpoint_file.exists():
            return

        try:
            with open(self._checkpoint_file, "r") as f:
                data = json.load(f)
                self._processed_message_hashes = set(data.get("processed_hashes", []))
                self.logger.info(
                    "Loaded processed hashes for deduplication",
                    count=len(self._processed_message_hashes),
                )
        except Exception as e:
            self.logger.warning("Failed to load processed hashes", error=str(e))
            self._processed_message_hashes = set()

    async def _save_processed_hashes(self) -> None:
        """Save processed message hashes for future runs."""
        if not self._checkpoint_file:
            return

        try:
            # Keep only the most recent hashes to prevent unlimited growth
            max_hashes = self.config.source_config.get("max_checkpoint_hashes", 10000)
            if len(self._processed_message_hashes) > max_hashes:
                # Convert to list, sort, and keep most recent
                hash_list = list(self._processed_message_hashes)
                hash_list.sort()  # This doesn't guarantee chronological order but limits size
                self._processed_message_hashes = set(hash_list[-max_hashes:])

            data = {
                "processed_hashes": list(self._processed_message_hashes),
                "last_updated": datetime.utcnow().isoformat(),
                "adapter_id": self.config.adapter_id,
            }

            with open(self._checkpoint_file, "w") as f:
                json.dump(data, f)

            self.logger.debug(
                "Saved processed hashes checkpoint",
                count=len(self._processed_message_hashes),
            )
        except Exception as e:
            self.logger.warning("Failed to save processed hashes", error=str(e))

    def _is_incremental_fetch_supported(self) -> bool:
        """Check if incremental fetching is supported for current configuration."""
        input_format = self.config.source_config.get("input_format", "jsonl")
        return input_format in [
            "jsonl",
            "json",
        ]  # File-based formats support incremental fetch

    def _should_skip_file_by_timestamp(
        self, file_path: Path, since: Optional[datetime]
    ) -> bool:
        """Check if file should be skipped based on modification time."""
        if not since:
            return False

        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            return file_mtime < since
        except Exception:
            return False  # Process file if we can't determine timestamp
