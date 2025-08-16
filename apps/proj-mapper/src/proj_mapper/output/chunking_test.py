"""Simple test for chunking functionality.

This script tests the basic functionality of the chunking system.
"""

import logging
import json
import sys
from typing import Dict, Any

from proj_mapper.output.chunking import ChunkingEngine
from proj_mapper.output.chunking.strategies import HierarchicalChunkingStrategy
from proj_mapper.output.config import GeneratorConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_map() -> Dict[str, Any]:
    """Create a test map with various elements.
    
    Returns:
        A dictionary representing a test map
    """
    return {
        "project": "Test Project",
        "version": "1.0.0",
        "code_elements": [
            {
                "id": "code1",
                "name": "TestClass",
                "type": "class",
                "location": {
                    "file_path": "test/file1.py",
                    "line_start": 10,
                    "line_end": 20
                },
                "content": "class TestClass:\n    def __init__(self):\n        pass"
            },
            {
                "id": "code2",
                "name": "test_function",
                "type": "function",
                "location": {
                    "file_path": "test/file2.py",
                    "line_start": 5,
                    "line_end": 15
                },
                "content": "def test_function():\n    return True"
            }
        ],
        "documentation_elements": [
            {
                "id": "doc1",
                "name": "README",
                "type": "markdown",
                "location": {
                    "file_path": "test/README.md",
                    "line_start": 1,
                    "line_end": 100
                },
                "content": "# Test Project\n\nThis is a test project."
            }
        ],
        "relationships": [
            {
                "source_id": "code1",
                "source_type": "code",
                "target_id": "code2",
                "target_type": "code",
                "relationship_type": "calls",
                "confidence": 0.9
            },
            {
                "source_id": "doc1",
                "source_type": "documentation",
                "target_id": "code1",
                "target_type": "code",
                "relationship_type": "documents",
                "confidence": 0.8
            }
        ]
    }


def main():
    """Run a simple test of the chunking functionality."""
    # Create a test map
    test_map = create_test_map()
    logger.info("Created test map with %d code elements, %d doc elements, and %d relationships",
               len(test_map["code_elements"]), len(test_map["documentation_elements"]), 
               len(test_map["relationships"]))
    
    # Create a config
    config = GeneratorConfig(enable_chunking=True)
    
    # Create a chunking engine
    engine = ChunkingEngine(strategy=HierarchicalChunkingStrategy(target_chunk_size=100))
    
    # Chunk the map
    try:
        chunks = engine.chunk_map(test_map, config)
        logger.info("Successfully chunked map into %d chunks", len(chunks))
        
        # Print some information about the chunks
        for chunk_id, chunk_data in chunks.items():
            if chunk_id == "master":
                logger.info("Master chunk has %d sub-chunks", chunk_data.get("chunk_count", 0))
            else:
                if "elements" in chunk_data:
                    logger.info("Chunk %s contains %d elements", chunk_id, len(chunk_data["elements"]))
                if "relationships" in chunk_data:
                    logger.info("Chunk %s contains %d relationships", chunk_id, len(chunk_data["relationships"]))
        
        # Print the chunks in JSON format for inspection
        print(json.dumps(chunks, indent=2))
        
        return True
    except Exception as e:
        logger.error("Error chunking map: %s", str(e))
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 