#!/usr/bin/env python3
"""
Enhanced Knowledge Tools with Auto-Embedding
Automatically generates embeddings when storing knowledge.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List

# Import embedding service
try:
    from embedding_service import get_embedding_service
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: Embedding service not available. Install sentence-transformers for auto-embedding.")


class KnowledgeStoreTool:
    """
    Enhanced knowledge storage with automatic embedding generation
    """
    
    @staticmethod
    def execute(
        knowledge_type: str,
        content: str,
        context: Dict[str, Any] = None,
        tags: List[str] = None,
        confidence_score: float = 0.8,
        knowledge_id: str = None,
        auto_embed: bool = True  # New parameter to control embedding
    ) -> Dict[str, Any]:
        """
        Store knowledge with automatic embedding generation
        
        Args:
            knowledge_type: ERROR_SOLUTION, CODE_PATTERN, WORKFLOW, etc.
            content: The knowledge content
            context: Any context dict (will be JSON serialized)
            tags: List of tags
            confidence_score: Initial confidence (0-1)
            knowledge_id: Optional ID (will generate if not provided)
            auto_embed: Whether to automatically generate embedding
            
        Returns:
            Cypher query and params ready for mcp__db__write_neo4j_cypher
        """
        
        # Generate ID if not provided
        if not knowledge_id:
            id_source = f"{knowledge_type}:{content[:100]}:{datetime.now(timezone.utc).isoformat()}"
            knowledge_id = hashlib.sha256(id_source.encode()).hexdigest()[:16]
        
        # JSON serialize complex objects
        context_json = json.dumps(context) if context else "{}"
        
        # Ensure tags is a list
        if tags is None:
            tags = []
        elif isinstance(tags, str):
            tags = [tags]
        
        # Generate embedding if requested and available
        embedding = None
        embedding_model = None
        if auto_embed and EMBEDDINGS_AVAILABLE:
            try:
                service = get_embedding_service()
                
                # Prepare knowledge text for embedding
                knowledge_dict = {
                    "knowledge_type": knowledge_type,
                    "content": content,
                    "context": context,
                    "tags": tags
                }
                prepared_text = service.prepare_knowledge_text(knowledge_dict)
                
                # Generate embedding
                embedding = service.generate_embedding(prepared_text)
                embedding_model = service.model_name
                
                print(f"✨ Auto-generated embedding with {len(embedding)} dimensions")
                
            except Exception as e:
                print(f"⚠️ Could not generate embedding: {e}")
                embedding = None
        
        # Build query based on whether we have an embedding
        if embedding:
            query = """
            MERGE (k:Knowledge {knowledge_id: $knowledge_id})
            ON CREATE SET
                k.knowledge_type = $knowledge_type,
                k.content = $content,
                k.context = $context,
                k.tags = $tags,
                k.confidence_score = $confidence_score,
                k.usage_count = 0,
                k.success_rate = 0.0,
                k.created_at = datetime(),
                k.updated_at = datetime(),
                k.embedding = $embedding,
                k.embedding_model = $embedding_model,
                k.embedding_generated_at = datetime()
            ON MATCH SET
                k.updated_at = datetime(),
                k.content = $content,
                k.context = $context,
                k.tags = $tags,
                k.embedding = $embedding,
                k.embedding_model = $embedding_model,
                k.embedding_generated_at = datetime()
            RETURN k.knowledge_id as id
            """
            
            params = {
                "knowledge_id": knowledge_id,
                "knowledge_type": knowledge_type,
                "content": content,
                "context": context_json,
                "tags": tags,
                "confidence_score": confidence_score,
                "embedding": embedding,
                "embedding_model": embedding_model
            }
        else:
            # Original query without embedding
            query = """
            MERGE (k:Knowledge {knowledge_id: $knowledge_id})
            ON CREATE SET
                k.knowledge_type = $knowledge_type,
                k.content = $content,
                k.context = $context,
                k.tags = $tags,
                k.confidence_score = $confidence_score,
                k.usage_count = 0,
                k.success_rate = 0.0,
                k.created_at = datetime(),
                k.updated_at = datetime()
            ON MATCH SET
                k.updated_at = datetime(),
                k.content = $content,
                k.context = $context,
                k.tags = $tags
            RETURN k.knowledge_id as id
            """
            
            params = {
                "knowledge_id": knowledge_id,
                "knowledge_type": knowledge_type,
                "content": content,
                "context": context_json,
                "tags": tags,
                "confidence_score": confidence_score
            }
        
        return {
            "query": query,
            "params": params,
            "knowledge_id": knowledge_id,
            "embedding_generated": embedding is not None,
            "instruction": "Execute via mcp__db__write_neo4j_cypher"
        }


if __name__ == "__main__":
    # Test auto-embedding
    print("Testing Auto-Embedding Knowledge Storage")
    print("-" * 50)
    
    result = KnowledgeStoreTool.execute(
        knowledge_type="TEST_AUTO_EMBED",
        content="Testing automatic embedding generation on knowledge storage",
        context={"test": True, "timestamp": datetime.now(timezone.utc).isoformat()},
        tags=["test", "auto-embed", "validation"],
        confidence_score=1.0,
        auto_embed=True
    )
    
    print(f"Knowledge ID: {result['knowledge_id']}")
    print(f"Embedding generated: {result['embedding_generated']}")
    
    if result['embedding_generated']:
        print(f"Embedding dimensions: {len(result['params']['embedding'])}")
        print(f"Model used: {result['params']['embedding_model']}")
    
    print("\n✅ Auto-embedding implementation ready!")