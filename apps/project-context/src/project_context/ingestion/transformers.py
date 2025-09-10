"""Data transformation utilities for ingestion pipeline."""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog

from ..models.common import ContextItem

logger = structlog.get_logger(__name__)


class DataTransformer:
    """Common data transformation utilities.

    Provides standardized transformation functions that can be used
    by adapters to convert raw data into ContextItems.
    """

    def __init__(self):
        """Initialize transformer."""
        self.logger = logger.bind(component="data_transformer")

    async def transform_item(self, item: ContextItem) -> ContextItem:
        """Apply standard transformations to a ContextItem.

        Args:
            item: ContextItem to transform

        Returns:
            Transformed ContextItem
        """
        # Generate content hash if not present
        if not item.content_hash and item.content:
            item.content_hash = self.generate_content_hash(item.content)

        # Generate search vector for full-text search
        if item.content or item.title:
            search_text = " ".join(filter(None, [item.title, item.content]))
            # This would integrate with PostgreSQL tsvector generation
            # For now, just store the text
            item.search_text = search_text

        # Sanitize content
        if item.content:
            item.content = self.sanitize_content(item.content)

        if item.title:
            item.title = self.sanitize_title(item.title)

        # Normalize tags
        if item.tags:
            item.tags = self.normalize_tags(item.tags)

        # Set ingestion timestamp
        if not item.ingested_at:
            item.ingested_at = datetime.utcnow()

        return item

    def generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication.

        Args:
            content: Content to hash

        Returns:
            SHA-256 hash as hexadecimal string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def sanitize_content(self, content: str, max_length: int = 100000) -> str:
        """Sanitize and truncate content.

        Args:
            content: Content to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized content
        """
        if not content:
            return ""

        # Remove null bytes and other problematic characters
        sanitized = content.replace("\x00", "").strip()

        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "... [truncated]"

        return sanitized

    def sanitize_title(self, title: str, max_length: int = 500) -> str:
        """Sanitize and truncate title.

        Args:
            title: Title to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized title
        """
        if not title:
            return ""

        # Remove newlines and extra whitespace
        sanitized = re.sub(r"\s+", " ", title.replace("\n", " ").strip())

        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip() + "..."

        return sanitized

    def normalize_tags(self, tags: List[str]) -> List[str]:
        """Normalize and deduplicate tags.

        Args:
            tags: List of tags to normalize

        Returns:
            Normalized and deduplicated tags
        """
        if not tags:
            return []

        normalized = []
        seen = set()

        for tag in tags:
            if not isinstance(tag, str):
                continue

            # Normalize tag
            normalized_tag = tag.lower().strip().replace(" ", "_")

            # Remove invalid characters
            normalized_tag = re.sub(r"[^a-z0-9_-]", "", normalized_tag)

            if normalized_tag and normalized_tag not in seen:
                normalized.append(normalized_tag)
                seen.add(normalized_tag)

        return sorted(normalized)

    def extract_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw data.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Extracted metadata
        """
        metadata = {}

        # Common metadata fields
        metadata_fields = [
            "author",
            "creator",
            "user_id",
            "user_name",
            "created_by",
            "modified_by",
            "version",
            "revision",
            "branch",
            "commit_hash",
            "pull_request",
            "issue_number",
            "file_size",
            "line_count",
            "language",
            "encoding",
            "mime_type",
            "file_type",
            "extension",
        ]

        for field in metadata_fields:
            if field in raw_data:
                metadata[field] = raw_data[field]

        return metadata

    def infer_entity_type(
        self,
        source_type: str,
        content: str = "",
        file_path: str = "",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Infer entity type based on available information.

        Args:
            source_type: Source type (chat, code, git, etc.)
            content: Content of the item
            file_path: File path if applicable
            metadata: Additional metadata

        Returns:
            Inferred entity type
        """
        metadata = metadata or {}

        if source_type == "chat":
            return "message"

        elif source_type == "git":
            if "commit" in content.lower() or metadata.get("commit_hash"):
                return "commit"
            elif "branch" in content.lower():
                return "branch"
            elif "tag" in content.lower():
                return "tag"
            else:
                return "git_event"

        elif source_type == "code":
            if file_path:
                extension = file_path.split(".")[-1].lower() if "." in file_path else ""

                # Language-specific inference
                language_map = {
                    "py": "python_file",
                    "js": "javascript_file",
                    "ts": "typescript_file",
                    "java": "java_file",
                    "cpp": "cpp_file",
                    "c": "c_file",
                    "h": "header_file",
                    "sql": "sql_file",
                    "json": "json_file",
                    "yaml": "yaml_file",
                    "yml": "yaml_file",
                    "xml": "xml_file",
                    "html": "html_file",
                    "css": "css_file",
                    "md": "markdown_file",
                    "txt": "text_file",
                }

                if extension in language_map:
                    return language_map[extension]

            # Content-based inference
            if "class " in content or "def " in content:
                return "code_definition"
            elif "import " in content or "from " in content:
                return "code_import"
            else:
                return "code_snippet"

        elif source_type == "error":
            if "exception" in content.lower():
                return "exception"
            elif "warning" in content.lower():
                return "warning"
            elif "error" in content.lower():
                return "error"
            else:
                return "diagnostic"

        elif source_type == "monitor":
            if metadata.get("metric_type"):
                return "metric"
            elif "performance" in content.lower():
                return "performance_data"
            else:
                return "monitoring_event"

        else:
            return "unknown"

    def extract_location_context(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract location context from raw data.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Location context information
        """
        location = {}

        # File-based location
        if "file_path" in raw_data:
            location["file_path"] = raw_data["file_path"]
        elif "filename" in raw_data:
            location["file_path"] = raw_data["filename"]
        elif "path" in raw_data:
            location["file_path"] = raw_data["path"]

        # Line-based location
        if "line_number" in raw_data:
            location["line_start"] = raw_data["line_number"]
        elif "start_line" in raw_data:
            location["line_start"] = raw_data["start_line"]

        if "end_line" in raw_data:
            location["line_end"] = raw_data["end_line"]
        elif "line_count" in raw_data and location.get("line_start"):
            location["line_end"] = location["line_start"] + raw_data["line_count"] - 1

        # Function/class context
        if "function_name" in raw_data:
            location["function_name"] = raw_data["function_name"]
        elif "function" in raw_data:
            location["function_name"] = raw_data["function"]

        if "class_name" in raw_data:
            location["class_name"] = raw_data["class_name"]
        elif "class" in raw_data:
            location["class_name"] = raw_data["class"]

        # Project context
        if "project_id" in raw_data:
            location["project_id"] = raw_data["project_id"]
        elif "repository" in raw_data:
            location["project_id"] = raw_data["repository"]
        elif "repo" in raw_data:
            location["project_id"] = raw_data["repo"]

        return location

    def extract_actor_information(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actor information from raw data.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Actor information
        """
        actor = {}

        # Actor ID
        if "user_id" in raw_data:
            actor["actor_id"] = raw_data["user_id"]
        elif "author_id" in raw_data:
            actor["actor_id"] = raw_data["author_id"]
        elif "username" in raw_data:
            actor["actor_id"] = raw_data["username"]
        elif "user" in raw_data:
            actor["actor_id"] = raw_data["user"]

        # Actor type inference
        if "bot" in str(actor.get("actor_id", "")).lower():
            actor["actor_type"] = "ai"
        elif "system" in str(actor.get("actor_id", "")).lower():
            actor["actor_type"] = "system"
        else:
            actor["actor_type"] = "human"

        # Session context
        if "session_id" in raw_data:
            actor["session_id"] = raw_data["session_id"]
        elif "conversation_id" in raw_data:
            actor["session_id"] = raw_data["conversation_id"]

        return actor

    def extract_temporal_context(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract temporal context from raw data.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Temporal context information
        """
        temporal = {}

        # Main timestamp
        timestamp_fields = [
            "timestamp",
            "created_at",
            "created_time",
            "date",
            "modified_at",
            "updated_at",
            "last_modified",
        ]

        for field in timestamp_fields:
            if field in raw_data:
                timestamp_value = raw_data[field]

                # Convert to datetime if needed
                if isinstance(timestamp_value, str):
                    try:
                        temporal["timestamp"] = datetime.fromisoformat(
                            timestamp_value.replace("Z", "+00:00")
                        )
                        break
                    except ValueError:
                        continue
                elif isinstance(timestamp_value, (int, float)):
                    try:
                        temporal["timestamp"] = datetime.fromtimestamp(timestamp_value)
                        break
                    except ValueError:
                        continue
                elif isinstance(timestamp_value, datetime):
                    temporal["timestamp"] = timestamp_value
                    break

        # End timestamp for duration events
        end_fields = ["end_time", "completed_at", "finished_at"]
        for field in end_fields:
            if field in raw_data:
                try:
                    end_value = raw_data[field]
                    if isinstance(end_value, str):
                        temporal["timestamp_end"] = datetime.fromisoformat(
                            end_value.replace("Z", "+00:00")
                        )
                    elif isinstance(end_value, datetime):
                        temporal["timestamp_end"] = end_value
                    break
                except ValueError:
                    continue

        return temporal

    async def validate_item(self, item: ContextItem) -> bool:
        """Validate a transformed ContextItem.

        Args:
            item: ContextItem to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Required fields
            if not item.source_type or not item.source_id:
                return False

            # Must have either content or title
            if not item.content and not item.title:
                return False

            # Timestamp validation
            if not item.timestamp:
                return False

            # Content hash validation
            if item.content and not item.content_hash:
                return False

            # Validate UUIDs if present
            if hasattr(item, "id") and item.id:
                try:
                    uuid4(str(item.id))
                except ValueError:
                    return False

            return True

        except Exception as e:
            self.logger.error("Validation error", error=str(e))
            return False

    def create_base_context_item(
        self, source_type: str, source_id: str, raw_data: Dict[str, Any]
    ) -> ContextItem:
        """Create a base ContextItem from raw data.

        Args:
            source_type: Type of data source
            source_id: Unique ID from source system
            raw_data: Raw data dictionary

        Returns:
            Base ContextItem with common fields populated
        """
        # Extract various contexts
        location = self.extract_location_context(raw_data)
        actor = self.extract_actor_information(raw_data)
        temporal = self.extract_temporal_context(raw_data)
        metadata = self.extract_metadata(raw_data)

        # Create base item
        item = ContextItem(
            source_type=source_type,
            source_id=source_id,
            **location,
            **actor,
            **temporal,
            source_data=raw_data,
            metrics=metadata,
        )

        # Set default timestamp if not present
        if not item.timestamp:
            item.timestamp = datetime.utcnow()

        # Infer entity type
        item.entity_type = self.infer_entity_type(
            source_type=source_type,
            content=raw_data.get("content", ""),
            file_path=item.file_path or "",
            metadata=metadata,
        )

        return item
