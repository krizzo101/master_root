"""
Neo4j Knowledge Store for Knowledge Learning System

This module provides the core knowledge storage and retrieval functionality
using Neo4j as the graph database backend.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class KnowledgeType(Enum):
    """Types of knowledge that can be stored"""
    CODE_PATTERN = "CodePattern"
    ERROR_RESOLUTION = "ErrorResolution"
    WORKFLOW = "Workflow"
    USER_PREFERENCE = "UserPreference"
    TOOL_USAGE = "ToolUsage"
    CONTEXT_PATTERN = "ContextPattern"
    GENERAL = "Knowledge"


@dataclass
class Knowledge:
    """Base knowledge entity"""
    id: str
    type: str
    content: str
    summary: str
    embedding: List[float]
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    success_rate: float = 0.0
    confidence_score: float = 0.5
    token_count: int = 0
    last_accessed: Optional[datetime] = None
    version: int = 1
    metadata: Dict[str, Any] = None


class Neo4jKnowledgeStore:
    """
    Main knowledge store interface for Neo4j
    """
    
    def __init__(self, neo4j_client):
        """
        Initialize knowledge store
        
        Args:
            neo4j_client: Neo4j client instance (MCP tool wrapper)
        """
        self.neo4j = neo4j_client
        self.initialized = False
        
    async def initialize_schema(self):
        """
        Create necessary indexes and constraints in Neo4j
        """
        indexes = [
            # Core indexes
            "CREATE INDEX knowledge_id IF NOT EXISTS FOR (n:Knowledge) ON (n.id)",
            "CREATE INDEX knowledge_type IF NOT EXISTS FOR (n:Knowledge) ON (n.type)",
            "CREATE INDEX knowledge_confidence IF NOT EXISTS FOR (n:Knowledge) ON (n.confidence_score)",
            "CREATE INDEX knowledge_created IF NOT EXISTS FOR (n:Knowledge) ON (n.created_at)",
            
            # Specialized indexes
            "CREATE INDEX code_pattern_language IF NOT EXISTS FOR (n:CodePattern) ON (n.language)",
            "CREATE INDEX error_signature IF NOT EXISTS FOR (n:ErrorResolution) ON (n.error_signature)",
            "CREATE INDEX workflow_name IF NOT EXISTS FOR (n:Workflow) ON (n.workflow_name)",
            "CREATE INDEX tool_name IF NOT EXISTS FOR (n:ToolUsage) ON (n.tool_name)",
            "CREATE INDEX context_type IF NOT EXISTS FOR (n:ContextPattern) ON (n.context_type)",
            "CREATE INDEX user_pref_user IF NOT EXISTS FOR (n:UserPreference) ON (n.user_id)",
            
            # Session tracking
            "CREATE INDEX session_id IF NOT EXISTS FOR (n:Session) ON (n.id)",
            "CREATE INDEX session_user IF NOT EXISTS FOR (n:Session) ON (n.user_id)",
            
            # Vector index for embeddings (if supported)
            "CREATE INDEX knowledge_embedding IF NOT EXISTS FOR (n:Knowledge) ON (n.embedding)"
        ]
        
        for index_query in indexes:
            try:
                await self.neo4j.write(index_query)
            except Exception as e:
                logging.warning(f"Index creation warning: {e}")
        
        self.initialized = True
        logging.info("Neo4j schema initialized")
    
    async def create_knowledge(self, knowledge: Knowledge) -> str:
        """
        Create new knowledge entry in Neo4j
        
        Args:
            knowledge: Knowledge object to store
            
        Returns:
            ID of created knowledge
        """
        query = """
        CREATE (k:Knowledge {
            id: $id,
            type: $type,
            content: $content,
            summary: $summary,
            embedding: $embedding,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at),
            access_count: $access_count,
            success_rate: $success_rate,
            confidence_score: $confidence_score,
            token_count: $token_count,
            version: $version
        })
        
        // Add type-specific label
        WITH k
        CALL apoc.create.addLabels(k, [$type]) YIELD node
        
        RETURN node.id as id
        """
        
        params = {
            'id': knowledge.id,
            'type': knowledge.type,
            'content': knowledge.content,
            'summary': knowledge.summary,
            'embedding': knowledge.embedding,
            'created_at': knowledge.created_at.isoformat(),
            'updated_at': knowledge.updated_at.isoformat(),
            'access_count': knowledge.access_count,
            'success_rate': knowledge.success_rate,
            'confidence_score': knowledge.confidence_score,
            'token_count': knowledge.token_count,
            'version': knowledge.version
        }
        
        result = await self.neo4j.write(query, params)
        return result[0]['id']
    
    async def batch_create_knowledge(self, knowledge_list: List[Knowledge]) -> List[str]:
        """
        Batch create multiple knowledge entries
        
        Args:
            knowledge_list: List of knowledge objects
            
        Returns:
            List of created IDs
        """
        query = """
        UNWIND $batch as item
        CREATE (k:Knowledge {
            id: item.id,
            type: item.type,
            content: item.content,
            summary: item.summary,
            embedding: item.embedding,
            created_at: datetime(item.created_at),
            updated_at: datetime(item.updated_at),
            access_count: item.access_count,
            success_rate: item.success_rate,
            confidence_score: item.confidence_score,
            token_count: item.token_count,
            version: item.version
        })
        
        // Add type-specific label
        WITH k, item
        CALL apoc.create.addLabels(k, [item.type]) YIELD node
        
        RETURN collect(node.id) as ids
        """
        
        batch = []
        for k in knowledge_list:
            batch.append({
                'id': k.id,
                'type': k.type,
                'content': k.content,
                'summary': k.summary,
                'embedding': k.embedding,
                'created_at': k.created_at.isoformat(),
                'updated_at': k.updated_at.isoformat(),
                'access_count': k.access_count,
                'success_rate': k.success_rate,
                'confidence_score': k.confidence_score,
                'token_count': k.token_count,
                'version': k.version
            })
        
        result = await self.neo4j.write(query, {'batch': batch})
        return result[0]['ids']
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict]:
        """
        Retrieve knowledge by ID
        
        Args:
            knowledge_id: Knowledge ID
            
        Returns:
            Knowledge data or None
        """
        query = """
        MATCH (k:Knowledge {id: $id})
        
        // Update access metrics
        SET k.access_count = k.access_count + 1,
            k.last_accessed = datetime()
        
        RETURN k
        """
        
        result = await self.neo4j.read(query, {'id': knowledge_id})
        
        if result:
            return self._node_to_dict(result[0]['k'])
        return None
    
    async def vector_search(
        self, 
        embedding: List[float], 
        k: int = 5,
        min_similarity: float = 0.7,
        knowledge_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar knowledge using vector similarity
        
        Args:
            embedding: Query embedding vector
            k: Number of results to return
            min_similarity: Minimum similarity threshold
            knowledge_type: Optional filter by knowledge type
            
        Returns:
            List of similar knowledge entries with similarity scores
        """
        # Build type filter if specified
        type_filter = f"AND k.type = '{knowledge_type}'" if knowledge_type else ""
        
        query = f"""
        MATCH (k:Knowledge)
        WHERE k.embedding IS NOT NULL {type_filter}
        
        // Calculate cosine similarity
        WITH k, gds.similarity.cosine(k.embedding, $embedding) AS similarity
        WHERE similarity >= $min_similarity
        
        RETURN k, similarity
        ORDER BY similarity DESC
        LIMIT $k
        """
        
        results = await self.neo4j.read(query, {
            'embedding': embedding,
            'min_similarity': min_similarity,
            'k': k
        })
        
        return [{
            'knowledge': self._node_to_dict(r['k']),
            'similarity': r['similarity']
        } for r in results]
    
    async def graph_search(
        self,
        context: Dict[str, Any],
        k: int = 5
    ) -> List[Dict]:
        """
        Context-aware graph traversal search
        
        Args:
            context: Context dictionary with triggers and conditions
            k: Number of results to return
            
        Returns:
            List of relevant knowledge entries
        """
        query = """
        // Find relevant context patterns
        MATCH (cp:ContextPattern)
        WHERE any(trigger IN cp.triggers WHERE trigger IN $context_keys)
        
        // Find activated knowledge
        MATCH (cp)-[:ACTIVATES]->(k:Knowledge)
        
        // Include related knowledge
        OPTIONAL MATCH (k)-[:SIMILAR_TO|REQUIRES|DERIVED_FROM*1..2]->(related:Knowledge)
        WHERE related.confidence_score > 0.5
        
        // Calculate relevance score
        WITH k, 
             collect(DISTINCT related) as related_items,
             count(DISTINCT cp) as context_matches
        
        RETURN k, 
               related_items, 
               context_matches,
               k.success_rate * context_matches as relevance_score
        ORDER BY relevance_score DESC, k.confidence_score DESC
        LIMIT $k
        """
        
        context_keys = list(context.keys())
        results = await self.neo4j.read(query, {
            'context_keys': context_keys,
            'k': k
        })
        
        return [{
            'knowledge': self._node_to_dict(r['k']),
            'related': [self._node_to_dict(rel) for rel in r['related_items']],
            'context_matches': r['context_matches'],
            'relevance_score': r['relevance_score']
        } for r in results]
    
    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
        properties: Optional[Dict] = None
    ):
        """
        Create relationship between knowledge nodes
        
        Args:
            from_id: Source knowledge ID
            to_id: Target knowledge ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
        """
        props_str = ""
        if properties:
            props_list = [f"{k}: ${k}" for k in properties.keys()]
            props_str = f" {{{', '.join(props_list)}}}"
        
        query = f"""
        MATCH (from:Knowledge {{id: $from_id}})
        MATCH (to:Knowledge {{id: $to_id}})
        CREATE (from)-[r:{relationship_type}{props_str}]->(to)
        RETURN r
        """
        
        params = {
            'from_id': from_id,
            'to_id': to_id
        }
        if properties:
            params.update(properties)
        
        await self.neo4j.write(query, params)
    
    async def update_knowledge_metrics(
        self,
        knowledge_id: str,
        success: bool,
        confidence_delta: float = 0.0
    ):
        """
        Update knowledge metrics based on usage
        
        Args:
            knowledge_id: Knowledge ID
            success: Whether the application was successful
            confidence_delta: Change in confidence score
        """
        query = """
        MATCH (k:Knowledge {id: $id})
        
        // Update success rate
        SET k.access_count = k.access_count + 1,
            k.success_count = COALESCE(k.success_count, 0) + CASE WHEN $success THEN 1 ELSE 0 END,
            k.success_rate = (COALESCE(k.success_count, 0) + CASE WHEN $success THEN 1 ELSE 0 END) * 1.0 / (k.access_count + 1),
            k.confidence_score = CASE 
                WHEN k.confidence_score + $confidence_delta > 1.0 THEN 1.0
                WHEN k.confidence_score + $confidence_delta < 0.0 THEN 0.0
                ELSE k.confidence_score + $confidence_delta
            END,
            k.last_accessed = datetime(),
            k.updated_at = datetime()
        
        RETURN k
        """
        
        await self.neo4j.write(query, {
            'id': knowledge_id,
            'success': success,
            'confidence_delta': confidence_delta
        })
    
    async def find_similar_knowledge(
        self,
        knowledge_id: str,
        similarity_threshold: float = 0.8
    ) -> List[Dict]:
        """
        Find knowledge similar to a given entry
        
        Args:
            knowledge_id: Source knowledge ID
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of similar knowledge entries
        """
        query = """
        MATCH (source:Knowledge {id: $id})
        MATCH (target:Knowledge)
        WHERE target.id <> source.id
        AND target.embedding IS NOT NULL
        AND source.embedding IS NOT NULL
        
        WITH source, target,
             gds.similarity.cosine(source.embedding, target.embedding) AS similarity
        WHERE similarity >= $threshold
        
        MERGE (source)-[r:SIMILAR_TO]->(target)
        SET r.similarity = similarity,
            r.updated_at = datetime()
        
        RETURN target, similarity
        ORDER BY similarity DESC
        """
        
        results = await self.neo4j.read(query, {
            'id': knowledge_id,
            'threshold': similarity_threshold
        })
        
        return [{
            'knowledge': self._node_to_dict(r['target']),
            'similarity': r['similarity']
        } for r in results]
    
    async def deprecate_old_knowledge(self, days_old: int = 90):
        """
        Deprecate knowledge that hasn't been accessed recently
        
        Args:
            days_old: Number of days since last access
        """
        query = """
        MATCH (k:Knowledge)
        WHERE k.last_accessed < datetime() - duration({days: $days})
        OR (k.last_accessed IS NULL AND k.created_at < datetime() - duration({days: $days}))
        
        SET k.deprecated = true,
            k.deprecation_date = datetime()
        
        RETURN count(k) as deprecated_count
        """
        
        result = await self.neo4j.write(query, {'days': days_old})
        return result[0]['deprecated_count']
    
    async def merge_duplicate_knowledge(self, similarity_threshold: float = 0.95):
        """
        Find and merge duplicate knowledge entries
        
        Args:
            similarity_threshold: Threshold for considering duplicates
            
        Returns:
            Number of merges performed
        """
        query = """
        MATCH (k1:Knowledge), (k2:Knowledge)
        WHERE k1.id < k2.id
        AND k1.embedding IS NOT NULL
        AND k2.embedding IS NOT NULL
        AND k1.type = k2.type
        AND gds.similarity.cosine(k1.embedding, k2.embedding) > $threshold
        
        // Merge properties (keep better metrics)
        SET k1.access_count = k1.access_count + k2.access_count,
            k1.success_rate = CASE 
                WHEN k1.access_count > k2.access_count THEN k1.success_rate
                ELSE k2.success_rate
            END,
            k1.confidence_score = CASE
                WHEN k1.confidence_score > k2.confidence_score THEN k1.confidence_score
                ELSE k2.confidence_score
            END,
            k1.content = CASE
                WHEN k1.success_rate > k2.success_rate THEN k1.content
                ELSE k2.content
            END
        
        // Transfer relationships
        WITH k1, k2
        MATCH (k2)-[r]->(n)
        WHERE NOT (k1)-[]-(n)
        CREATE (k1)-[r2:MERGED_FROM]->(n)
        SET r2 = properties(r)
        
        // Delete duplicate
        DETACH DELETE k2
        
        RETURN count(k2) as merged_count
        """
        
        result = await self.neo4j.write(query, {'threshold': similarity_threshold})
        return result[0]['merged_count']
    
    async def get_knowledge_stats(self) -> Dict:
        """
        Get statistics about the knowledge base
        
        Returns:
            Dictionary of statistics
        """
        query = """
        MATCH (k:Knowledge)
        WITH count(k) as total_knowledge,
             avg(k.confidence_score) as avg_confidence,
             avg(k.success_rate) as avg_success,
             sum(k.access_count) as total_accesses,
             count(DISTINCT k.type) as knowledge_types
        
        OPTIONAL MATCH (s:Session)
        WITH total_knowledge, avg_confidence, avg_success, total_accesses, knowledge_types,
             count(s) as total_sessions
        
        OPTIONAL MATCH (k:Knowledge)
        WHERE k.deprecated = true
        WITH total_knowledge, avg_confidence, avg_success, total_accesses, knowledge_types,
             total_sessions, count(k) as deprecated_count
        
        RETURN {
            total_knowledge: total_knowledge,
            knowledge_types: knowledge_types,
            avg_confidence: avg_confidence,
            avg_success_rate: avg_success,
            total_accesses: total_accesses,
            total_sessions: total_sessions,
            deprecated_count: deprecated_count,
            knowledge_per_session: CASE 
                WHEN total_sessions > 0 THEN total_knowledge * 1.0 / total_sessions
                ELSE 0
            END
        } as stats
        """
        
        result = await self.neo4j.read(query)
        return result[0]['stats'] if result else {}
    
    def _node_to_dict(self, node) -> Dict:
        """
        Convert Neo4j node to dictionary
        
        Args:
            node: Neo4j node object
            
        Returns:
            Dictionary representation
        """
        # Handle different node formats from Neo4j
        if hasattr(node, 'properties'):
            return dict(node.properties)
        elif isinstance(node, dict):
            return node
        else:
            return {'id': str(node)}


class CodePatternStore(Neo4jKnowledgeStore):
    """
    Specialized store for code patterns
    """
    
    async def create_code_pattern(
        self,
        pattern_name: str,
        code: str,
        language: str,
        framework: Optional[str],
        pattern_type: str,
        embedding: List[float]
    ) -> str:
        """
        Create a code pattern entry
        
        Args:
            pattern_name: Name of the pattern
            code: Code content
            language: Programming language
            framework: Optional framework
            pattern_type: Type of pattern
            embedding: Pre-computed embedding
            
        Returns:
            ID of created pattern
        """
        pattern_id = str(uuid.uuid4())
        
        query = """
        CREATE (cp:CodePattern:Knowledge {
            id: $id,
            type: 'CodePattern',
            pattern_name: $pattern_name,
            content: $code,
            language: $language,
            framework: $framework,
            pattern_type: $pattern_type,
            embedding: $embedding,
            created_at: datetime(),
            updated_at: datetime(),
            access_count: 0,
            success_rate: 0.0,
            confidence_score: 0.5
        })
        RETURN cp.id as id
        """
        
        result = await self.neo4j.write(query, {
            'id': pattern_id,
            'pattern_name': pattern_name,
            'code': code,
            'language': language,
            'framework': framework,
            'pattern_type': pattern_type,
            'embedding': embedding
        })
        
        return result[0]['id']
    
    async def find_patterns_by_language(
        self,
        language: str,
        pattern_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Find code patterns by language
        
        Args:
            language: Programming language
            pattern_type: Optional pattern type filter
            
        Returns:
            List of matching patterns
        """
        type_filter = f"AND cp.pattern_type = '{pattern_type}'" if pattern_type else ""
        
        query = f"""
        MATCH (cp:CodePattern)
        WHERE cp.language = $language {type_filter}
        RETURN cp
        ORDER BY cp.success_rate DESC, cp.access_count DESC
        """
        
        results = await self.neo4j.read(query, {'language': language})
        return [self._node_to_dict(r['cp']) for r in results]


class ErrorResolutionStore(Neo4jKnowledgeStore):
    """
    Specialized store for error resolutions
    """
    
    async def create_error_resolution(
        self,
        error_signature: str,
        error_type: str,
        error_message: str,
        resolution: str,
        embedding: List[float]
    ) -> str:
        """
        Create an error resolution entry
        
        Args:
            error_signature: Unique error signature
            error_type: Type of error
            error_message: Error message
            resolution: Resolution steps
            embedding: Pre-computed embedding
            
        Returns:
            ID of created resolution
        """
        resolution_id = str(uuid.uuid4())
        
        query = """
        CREATE (er:ErrorResolution:Knowledge {
            id: $id,
            type: 'ErrorResolution',
            error_signature: $error_signature,
            error_type: $error_type,
            error_message: $error_message,
            content: $resolution,
            embedding: $embedding,
            created_at: datetime(),
            updated_at: datetime(),
            access_count: 0,
            success_rate: 0.0,
            confidence_score: 0.5
        })
        RETURN er.id as id
        """
        
        result = await self.neo4j.write(query, {
            'id': resolution_id,
            'error_signature': error_signature,
            'error_type': error_type,
            'error_message': error_message,
            'resolution': resolution,
            'embedding': embedding
        })
        
        return result[0]['id']
    
    async def find_resolution(self, error_signature: str) -> Optional[Dict]:
        """
        Find resolution for a specific error
        
        Args:
            error_signature: Error signature to search for
            
        Returns:
            Resolution if found, None otherwise
        """
        query = """
        MATCH (er:ErrorResolution)
        WHERE er.error_signature = $signature
        OR er.error_message CONTAINS $signature
        RETURN er
        ORDER BY er.success_rate DESC
        LIMIT 1
        """
        
        results = await self.neo4j.read(query, {'signature': error_signature})
        
        if results:
            return self._node_to_dict(results[0]['er'])
        return None