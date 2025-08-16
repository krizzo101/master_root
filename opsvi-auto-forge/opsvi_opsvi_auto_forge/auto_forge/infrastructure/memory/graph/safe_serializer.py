"""Bulletproof Neo4j data serializer that eliminates Map{} errors."""

import json
import logging
from typing import Any, Dict, List, Union
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


class Neo4jSafeSerializer:
    """Bulletproof serializer that converts ANY data to Neo4j-safe format."""

    @staticmethod
    def serialize_value(value: Any) -> Union[str, int, float, bool, List, None]:
        """Convert ANY value to Neo4j-safe format."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [Neo4jSafeSerializer.serialize_value(v) for v in value]
        if isinstance(value, dict):
            # ALWAYS convert dicts to JSON strings - NO EXCEPTIONS
            return json.dumps(value, default=str)
        # For any other object, convert to string
        return str(value)

    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert entire data structure to Neo4j-safe format."""
        if not data:
            return {}

        safe_data = {}
        for key, value in data.items():
            # Special handling for metadata fields
            if key in [
                "metadata",
                "metadata_json",
                "inputs",
                "inputs_json",
                "outputs",
                "outputs_json",
                "metrics",
                "metrics_json",
                "policy_scores",
                "policy_scores_json",
                "quality_gates",
                "quality_gates_json",
            ]:
                # ALWAYS convert to JSON string
                if isinstance(value, dict):
                    safe_data[key] = json.dumps(value, default=str)
                elif isinstance(value, str):
                    # Validate it's valid JSON
                    try:
                        json.loads(value)
                        safe_data[key] = value
                    except json.JSONDecodeError:
                        safe_data[key] = "{}"
                else:
                    safe_data[key] = json.dumps(value, default=str) if value else "{}"
            else:
                # Regular fields
                safe_data[key] = Neo4jSafeSerializer.serialize_value(value)

        return safe_data

    @staticmethod
    def ensure_json_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all *_json fields exist and are JSON strings."""
        json_fields = [
            "metadata_json",
            "inputs_json",
            "outputs_json",
            "metrics_json",
            "policy_scores_json",
            "quality_gates_json",
        ]

        for field in json_fields:
            if field not in data:
                data[field] = "{}"
            elif isinstance(data[field], dict):
                data[field] = json.dumps(data[field], default=str)
            elif not isinstance(data[field], str):
                data[field] = (
                    json.dumps(data[field], default=str) if data[field] else "{}"
                )

        return data
