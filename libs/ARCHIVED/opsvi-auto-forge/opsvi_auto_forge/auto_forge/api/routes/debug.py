"""Debug routes for testing."""

from fastapi import APIRouter
from opsvi_auto_forge.infrastructure.memory.graph.safe_serializer import (
    Neo4jSafeSerializer,
)

router = APIRouter()


@router.get("/debug/serializer")
async def test_serializer():
    """Test the bulletproof serializer."""
    test_data = {
        "metadata": {"test": True, "fix": "debug"},
        "inputs": {"data": "test"},
        "outputs": {"result": "success"},
    }

    safe_data = Neo4jSafeSerializer.serialize_data(test_data)
    safe_data = Neo4jSafeSerializer.ensure_json_fields(safe_data)

    return {
        "original": test_data,
        "serialized": safe_data,
        "metadata_type": str(type(safe_data.get("metadata_json"))),
        "metadata_value": safe_data.get("metadata_json"),
    }
