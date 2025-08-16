#!/usr/bin/env python3
"""
Neo4j-based Knowledge Learning System for Autonomous AI Agent

This system provides persistent knowledge storage and retrieval using Neo4j,
with embedding support for semantic search and graph traversal for relationships.
"""

import json
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """Represents a knowledge entry in the system"""
    knowledge_id: str
    knowledge_type: str  # CODE_PATTERN, ERROR_SOLUTION, WORKFLOW, USER_PREFERENCE, CONTEXT_PATTERN, TOOL_USAGE
    content: str
    context: Dict[str, Any]
    confidence_score: float
    usage_count: int
    success_rate: float
    created_at: str
    updated_at: str
    tags: List[str]
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None


class Neo4jKnowledgeLearningSystem:
    """
    Main class for knowledge learning using Neo4j as the backend.
    Provides methods to store, retrieve, and learn from knowledge.
    """
    
    def __init__(self):
        """Initialize the knowledge learning system"""
        self.knowledge_cache = {}
        self.session_context = {}
        
    async def store_knowledge(self, 
                             knowledge_type: str,
                             content: str,
                             context: Dict[str, Any],
                             tags: List[str] = None,
                             embedding: List[float] = None) -> str:
        """
        Store new knowledge in Neo4j
        
        Args:
            knowledge_type: Type of knowledge (CODE_PATTERN, ERROR_SOLUTION, etc.)
            content: The actual knowledge content
            context: Contextual information about the knowledge
            tags: Optional tags for categorization
            embedding: Optional pre-computed embedding vector
            
        Returns:
            knowledge_id: Unique identifier for the stored knowledge
        """
        knowledge_id = self._generate_knowledge_id(knowledge_type, content)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Prepare knowledge entry
        entry = KnowledgeEntry(
            knowledge_id=knowledge_id,
            knowledge_type=knowledge_type,
            content=content,
            context=context,
            confidence_score=0.8,  # Initial confidence
            usage_count=0,
            success_rate=0.0,
            created_at=timestamp,
            updated_at=timestamp,
            tags=tags or [],
            embedding=embedding,
            metadata={}
        )
        
        # Store in cache
        self.knowledge_cache[knowledge_id] = entry
        
        logger.info(f"Stored knowledge: {knowledge_id} of type {knowledge_type}")
        return knowledge_id
    
    async def retrieve_knowledge(self,
                                query: str,
                                knowledge_type: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None,
                                max_results: int = 5) -> List[KnowledgeEntry]:
        """
        Retrieve relevant knowledge based on query and context
        
        Args:
            query: Search query
            knowledge_type: Optional filter by knowledge type
            context: Optional contextual filters
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant knowledge entries
        """
        results = []
        
        # Simple retrieval from cache for now
        for entry in self.knowledge_cache.values():
            if knowledge_type and entry.knowledge_type != knowledge_type:
                continue
            
            # Simple text matching (would use embeddings in production)
            if query.lower() in entry.content.lower():
                results.append(entry)
                
            if len(results) >= max_results:
                break
        
        logger.info(f"Retrieved {len(results)} knowledge entries for query: {query}")
        return results
    
    async def learn_from_success(self,
                                knowledge_id: str,
                                success_metrics: Dict[str, float]):
        """
        Update knowledge based on successful application
        
        Args:
            knowledge_id: ID of the knowledge that was applied
            success_metrics: Metrics indicating success level
        """
        if knowledge_id in self.knowledge_cache:
            entry = self.knowledge_cache[knowledge_id]
            entry.usage_count += 1
            
            # Update success rate using exponential moving average
            alpha = 0.1
            new_success = sum(success_metrics.values()) / len(success_metrics)
            entry.success_rate = (1 - alpha) * entry.success_rate + alpha * new_success
            
            # Increase confidence if consistently successful
            if entry.success_rate > 0.8 and entry.usage_count > 5:
                entry.confidence_score = min(1.0, entry.confidence_score + 0.05)
            
            entry.updated_at = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Updated knowledge {knowledge_id}: success_rate={entry.success_rate:.2f}, confidence={entry.confidence_score:.2f}")
    
    async def learn_from_failure(self,
                                knowledge_id: str,
                                failure_reason: str):
        """
        Update knowledge based on failed application
        
        Args:
            knowledge_id: ID of the knowledge that failed
            failure_reason: Reason for failure
        """
        if knowledge_id in self.knowledge_cache:
            entry = self.knowledge_cache[knowledge_id]
            entry.usage_count += 1
            
            # Decrease success rate
            alpha = 0.1
            entry.success_rate = (1 - alpha) * entry.success_rate
            
            # Decrease confidence if consistently failing
            if entry.success_rate < 0.3:
                entry.confidence_score = max(0.1, entry.confidence_score - 0.1)
            
            # Add failure to metadata
            if 'failures' not in entry.metadata:
                entry.metadata['failures'] = []
            entry.metadata['failures'].append({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'reason': failure_reason
            })
            
            entry.updated_at = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Recorded failure for knowledge {knowledge_id}: confidence={entry.confidence_score:.2f}")
    
    async def discover_patterns(self) -> List[Dict[str, Any]]:
        """
        Analyze stored knowledge to discover patterns
        
        Returns:
            List of discovered patterns
        """
        patterns = []
        
        # Group by knowledge type
        type_groups = {}
        for entry in self.knowledge_cache.values():
            if entry.knowledge_type not in type_groups:
                type_groups[entry.knowledge_type] = []
            type_groups[entry.knowledge_type].append(entry)
        
        # Find high-performing patterns
        for k_type, entries in type_groups.items():
            successful_entries = [e for e in entries if e.success_rate > 0.7 and e.usage_count > 3]
            if successful_entries:
                patterns.append({
                    'pattern_type': 'HIGH_PERFORMANCE',
                    'knowledge_type': k_type,
                    'count': len(successful_entries),
                    'avg_success_rate': sum(e.success_rate for e in successful_entries) / len(successful_entries),
                    'example_ids': [e.knowledge_id for e in successful_entries[:3]]
                })
        
        logger.info(f"Discovered {len(patterns)} patterns")
        return patterns
    
    async def get_learning_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the learning system's current state
        
        Returns:
            Summary statistics and insights
        """
        total_knowledge = len(self.knowledge_cache)
        
        if total_knowledge == 0:
            return {
                'total_knowledge': 0,
                'message': 'No knowledge stored yet'
            }
        
        type_distribution = {}
        total_usage = 0
        total_success_rate = 0
        high_confidence_count = 0
        
        for entry in self.knowledge_cache.values():
            # Type distribution
            if entry.knowledge_type not in type_distribution:
                type_distribution[entry.knowledge_type] = 0
            type_distribution[entry.knowledge_type] += 1
            
            # Usage and success metrics
            total_usage += entry.usage_count
            total_success_rate += entry.success_rate
            
            # High confidence entries
            if entry.confidence_score > 0.8:
                high_confidence_count += 1
        
        avg_success_rate = total_success_rate / total_knowledge
        
        return {
            'total_knowledge': total_knowledge,
            'type_distribution': type_distribution,
            'total_usage': total_usage,
            'average_success_rate': avg_success_rate,
            'high_confidence_entries': high_confidence_count,
            'recommendation': self._get_learning_recommendation(avg_success_rate, total_usage, total_knowledge)
        }
    
    def _generate_knowledge_id(self, knowledge_type: str, content: str) -> str:
        """Generate unique ID for knowledge entry"""
        data = f"{knowledge_type}:{content[:100]}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_learning_recommendation(self, avg_success_rate: float, total_usage: int, total_knowledge: int) -> str:
        """Generate recommendation based on current metrics"""
        if total_knowledge < 10:
            return "Build more knowledge - system needs more data points"
        elif avg_success_rate < 0.5:
            return "Focus on improving knowledge quality - many entries have low success rates"
        elif total_usage / total_knowledge < 2:
            return "Increase knowledge application - many entries haven't been tested enough"
        else:
            return "System performing well - continue current learning patterns"


# Neo4j query functions using MCP tools
async def store_knowledge_in_neo4j(knowledge_entry: KnowledgeEntry) -> bool:
    """
    Store knowledge entry in Neo4j using MCP tools
    
    This would be called via mcp__db__write_neo4j_cypher in actual usage
    """
    query = """
    CREATE (k:Knowledge {
        knowledge_id: $knowledge_id,
        knowledge_type: $knowledge_type,
        content: $content,
        context: $context,
        confidence_score: $confidence_score,
        usage_count: $usage_count,
        success_rate: $success_rate,
        created_at: $created_at,
        updated_at: $updated_at,
        tags: $tags
    })
    RETURN k.knowledge_id as id
    """
    
    params = {
        'knowledge_id': knowledge_entry.knowledge_id,
        'knowledge_type': knowledge_entry.knowledge_type,
        'content': knowledge_entry.content,
        'context': json.dumps(knowledge_entry.context),
        'confidence_score': knowledge_entry.confidence_score,
        'usage_count': knowledge_entry.usage_count,
        'success_rate': knowledge_entry.success_rate,
        'created_at': knowledge_entry.created_at,
        'updated_at': knowledge_entry.updated_at,
        'tags': knowledge_entry.tags
    }
    
    # In actual usage, this would be:
    # result = await mcp__db__write_neo4j_cypher(query=query, params=params)
    logger.info(f"Would store in Neo4j: {knowledge_entry.knowledge_id}")
    return True


async def query_knowledge_from_neo4j(query_text: str, knowledge_type: Optional[str] = None) -> List[Dict]:
    """
    Query knowledge from Neo4j using MCP tools
    
    This would be called via mcp__db__read_neo4j_cypher in actual usage
    """
    if knowledge_type:
        cypher_query = """
        MATCH (k:Knowledge)
        WHERE k.knowledge_type = $knowledge_type 
        AND (k.content CONTAINS $query OR any(tag IN k.tags WHERE tag CONTAINS $query))
        RETURN k
        ORDER BY k.confidence_score DESC, k.usage_count DESC
        LIMIT 10
        """
        params = {'knowledge_type': knowledge_type, 'query': query_text}
    else:
        cypher_query = """
        MATCH (k:Knowledge)
        WHERE k.content CONTAINS $query OR any(tag IN k.tags WHERE tag CONTAINS $query)
        RETURN k
        ORDER BY k.confidence_score DESC, k.usage_count DESC
        LIMIT 10
        """
        params = {'query': query_text}
    
    # In actual usage, this would be:
    # result = await mcp__db__read_neo4j_cypher(query=cypher_query, params=params)
    logger.info(f"Would query Neo4j for: {query_text}")
    return []


async def create_knowledge_relationship(source_id: str, target_id: str, relationship_type: str) -> bool:
    """
    Create relationship between knowledge entries in Neo4j
    
    Relationship types: SIMILAR_TO, DERIVED_FROM, REQUIRES, CONTRADICTS, ENHANCES
    """
    query = """
    MATCH (source:Knowledge {knowledge_id: $source_id})
    MATCH (target:Knowledge {knowledge_id: $target_id})
    CREATE (source)-[r:""" + relationship_type + """ {
        created_at: $created_at,
        strength: $strength
    }]->(target)
    RETURN r
    """
    
    params = {
        'source_id': source_id,
        'target_id': target_id,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'strength': 1.0
    }
    
    # In actual usage, this would be:
    # result = await mcp__db__write_neo4j_cypher(query=query, params=params)
    logger.info(f"Would create relationship: {source_id} -{relationship_type}-> {target_id}")
    return True


# Example usage and self-learning demonstration
async def demonstrate_learning():
    """Demonstrate the knowledge learning system"""
    
    # Initialize system
    system = Neo4jKnowledgeLearningSystem()
    
    # Example 1: Store error solution knowledge
    error_knowledge_id = await system.store_knowledge(
        knowledge_type="ERROR_SOLUTION",
        content="Fix ImportError by installing missing package with pip install",
        context={
            "error_type": "ImportError",
            "language": "Python",
            "solution_type": "package_installation"
        },
        tags=["python", "import", "error", "pip"]
    )
    
    # Example 2: Store code pattern knowledge
    code_pattern_id = await system.store_knowledge(
        knowledge_type="CODE_PATTERN",
        content="Use async/await for handling asynchronous operations in Python",
        context={
            "language": "Python",
            "pattern_type": "concurrency",
            "use_case": "io_bound_operations"
        },
        tags=["python", "async", "concurrency", "pattern"]
    )
    
    # Example 3: Store workflow knowledge
    workflow_id = await system.store_knowledge(
        knowledge_type="WORKFLOW",
        content="Git workflow: 1) Create branch, 2) Make changes, 3) Commit, 4) Push, 5) Create PR",
        context={
            "tool": "git",
            "workflow_type": "feature_development",
            "steps": 5
        },
        tags=["git", "workflow", "development", "version_control"]
    )
    
    # Simulate retrieval
    print("\n=== Retrieving Knowledge ===")
    error_results = await system.retrieve_knowledge("ImportError", knowledge_type="ERROR_SOLUTION")
    print(f"Found {len(error_results)} error solutions")
    
    # Simulate learning from success
    print("\n=== Learning from Success ===")
    await system.learn_from_success(
        error_knowledge_id,
        {"resolved": 1.0, "time_saved": 0.8}
    )
    
    # Simulate learning from failure
    print("\n=== Learning from Failure ===")
    await system.learn_from_failure(
        code_pattern_id,
        "Pattern didn't work with Python 2.7"
    )
    
    # Discover patterns
    print("\n=== Discovering Patterns ===")
    patterns = await system.discover_patterns()
    for pattern in patterns:
        print(f"Pattern: {pattern}")
    
    # Get learning summary
    print("\n=== Learning Summary ===")
    summary = await system.get_learning_summary()
    print(json.dumps(summary, indent=2))
    
    # Demonstrate Neo4j operations (simulated)
    print("\n=== Neo4j Operations (Simulated) ===")
    await store_knowledge_in_neo4j(system.knowledge_cache[error_knowledge_id])
    await query_knowledge_from_neo4j("ImportError")
    await create_knowledge_relationship(error_knowledge_id, code_pattern_id, "RELATED_TO")


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_learning())