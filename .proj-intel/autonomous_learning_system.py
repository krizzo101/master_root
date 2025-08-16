#!/usr/bin/env python3
"""
Autonomous Learning Knowledge System

Implements hybrid knowledge storage combining:
1. Neo4j Knowledge Graph - Relationships between concepts, patterns, solutions
2. ChromaDB RAG - Semantic search over learned experiences
3. Error Pattern Cache - Fast lookup for known issues
4. Learning History - Temporal learning progression

This system enables autonomous agents to:
- Store and retrieve learned knowledge
- Build conceptual relationships
- Apply learned patterns to new situations
- Self-improve through accumulated experience
"""

import json
import hashlib
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None


@dataclass
class LearningEvent:
    """Single learning event to be stored"""
    event_id: str
    timestamp: str
    event_type: str  # "error_resolution", "pattern_discovery", "optimization", "feedback"
    context: Dict[str, Any]
    input_data: str
    output_data: str
    success_metrics: Dict[str, float]
    tags: List[str]
    relationships: List[Dict[str, str]]  # [{"type": "causes", "target": "event_id"}]


@dataclass
class KnowledgePattern:
    """Discovered knowledge pattern"""
    pattern_id: str
    pattern_type: str  # "error_solution", "optimization_strategy", "workflow_improvement"
    confidence: float
    description: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    success_rate: float
    usage_count: int
    last_used: str


class AutonomousLearningSystem:
    """
    Central system for storing and retrieving learned knowledge
    
    Architecture:
    - Neo4j: Concept relationships, causal chains, pattern hierarchies
    - ChromaDB: Semantic search over experiences, context matching
    - JSON Cache: Fast lookup for frequent patterns
    - Memory Index: Recent learning events for quick access
    """
    
    def __init__(self, base_path: str = ".proj-intel"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # File-based storage paths
        self.error_patterns_file = self.base_path / "error_patterns.json"
        self.learning_history_file = self.base_path / "learning_history.jsonl"
        self.knowledge_patterns_file = self.base_path / "knowledge_patterns.json"
        self.learning_index_file = self.base_path / "learning_index.json"
        
        # In-memory caches
        self.recent_events: List[LearningEvent] = []
        self.pattern_cache: Dict[str, KnowledgePattern] = {}
        self.learning_index: Dict[str, Any] = {}
        
        # Initialize storage systems
        self._init_chroma_db()
        self._init_neo4j()
        self._load_existing_data()
    
    def _init_chroma_db(self):
        """Initialize ChromaDB for semantic search"""
        if chromadb is None:
            print("ChromaDB not available - install with: pip install chromadb")
            self.chroma_client = None
            self.learning_collection = None
            return
            
        chroma_path = self.base_path / "chroma_db"
        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collection for learned experiences
        self.learning_collection = self.chroma_client.get_or_create_collection(
            name="autonomous_learning",
            metadata={"description": "Autonomous agent learning experiences"}
        )
    
    def _init_neo4j(self):
        """Initialize Neo4j for knowledge graph"""
        # Use MCP Neo4j client if available
        self.neo4j_driver = None
        try:
            # Would connect to Neo4j via MCP in production
            # For now, prepare the schema queries
            self.neo4j_queries = {
                "create_learning_event": """
                CREATE (e:LearningEvent {
                    event_id: $event_id,
                    timestamp: $timestamp,
                    event_type: $event_type,
                    context: $context,
                    success_metrics: $success_metrics
                })
                """,
                "create_pattern": """
                CREATE (p:KnowledgePattern {
                    pattern_id: $pattern_id,
                    pattern_type: $pattern_type,
                    confidence: $confidence,
                    description: $description,
                    success_rate: $success_rate
                })
                """,
                "create_relationship": """
                MATCH (a), (b)
                WHERE a.event_id = $source_id AND b.event_id = $target_id
                CREATE (a)-[r:RELATES_TO {type: $relationship_type}]->(b)
                """
            }
        except Exception as e:
            print(f"Neo4j not available: {e}")
    
    def _load_existing_data(self):
        """Load existing learning data from files"""
        try:
            if self.learning_index_file.exists():
                with open(self.learning_index_file) as f:
                    self.learning_index = json.load(f)
            else:
                self.learning_index = {
                    "total_events": 0,
                    "event_types": {},
                    "success_rates": {},
                    "recent_patterns": [],
                    "learning_velocity": 0.0
                }
        except Exception as e:
            print(f"Error loading learning index: {e}")
            self.learning_index = {}
    
    def learn_from_event(self, 
                        event_type: str,
                        context: Dict[str, Any],
                        input_data: str,
                        output_data: str,
                        success_metrics: Dict[str, float],
                        tags: List[str] = None) -> str:
        """
        Learn from a single event and store in all systems
        
        Returns:
            str: event_id for the stored learning event
        """
        event_id = self._generate_event_id(event_type, input_data, output_data)
        timestamp = datetime.now(timezone.utc).isoformat()
        tags = tags or []
        
        learning_event = LearningEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            context=context,
            input_data=input_data,
            output_data=output_data,
            success_metrics=success_metrics,
            tags=tags,
            relationships=[]
        )
        
        # Store in all systems
        self._store_in_history(learning_event)
        self._store_in_chroma(learning_event)
        self._store_in_neo4j(learning_event)
        self._update_patterns(learning_event)
        self._update_index(learning_event)
        
        # Add to recent events cache
        self.recent_events.append(learning_event)
        if len(self.recent_events) > 100:  # Keep only recent 100
            self.recent_events = self.recent_events[-100:]
        
        return event_id
    
    def find_similar_experiences(self, 
                                query: str, 
                                context: Dict[str, Any] = None,
                                limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar past experiences using semantic search
        
        Args:
            query: Description of current situation
            context: Additional context to match
            limit: Max number of results
            
        Returns:
            List of similar experiences with metadata
        """
        if self.learning_collection is None:
            return self._fallback_text_search(query, limit)
        
        try:
            # Build query with context
            search_query = query
            if context:
                context_str = " ".join(f"{k}:{v}" for k, v in context.items() 
                                     if isinstance(v, (str, int, float)))
                search_query = f"{query} {context_str}"
            
            results = self.learning_collection.query(
                query_texts=[search_query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            similar_experiences = []
            for i in range(len(results["documents"][0])):
                experience = {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "source": "semantic_search"
                }
                similar_experiences.append(experience)
            
            return similar_experiences
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return self._fallback_text_search(query, limit)
    
    def get_applicable_patterns(self, 
                               context: Dict[str, Any],
                               min_confidence: float = 0.7) -> List[KnowledgePattern]:
        """
        Get knowledge patterns applicable to current context
        
        Args:
            context: Current situation context
            min_confidence: Minimum pattern confidence threshold
            
        Returns:
            List of applicable patterns sorted by relevance
        """
        applicable_patterns = []
        
        for pattern in self.pattern_cache.values():
            if pattern.confidence < min_confidence:
                continue
                
            # Check if pattern trigger conditions match context
            match_score = self._calculate_pattern_match(pattern, context)
            if match_score > 0.5:
                applicable_patterns.append((pattern, match_score))
        
        # Sort by match score and success rate
        applicable_patterns.sort(
            key=lambda x: (x[1], x[0].success_rate), 
            reverse=True
        )
        
        return [pattern for pattern, score in applicable_patterns]
    
    def record_pattern_usage(self, 
                           pattern_id: str, 
                           success: bool, 
                           context: Dict[str, Any]):
        """Record usage of a pattern and update its success rate"""
        if pattern_id in self.pattern_cache:
            pattern = self.pattern_cache[pattern_id]
            pattern.usage_count += 1
            pattern.last_used = datetime.now(timezone.utc).isoformat()
            
            # Update success rate using exponential moving average
            alpha = 0.1  # Learning rate
            if success:
                pattern.success_rate = (1 - alpha) * pattern.success_rate + alpha * 1.0
            else:
                pattern.success_rate = (1 - alpha) * pattern.success_rate + alpha * 0.0
            
            # Store updated pattern
            self._save_patterns()
    
    def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights about learning progress and patterns"""
        return {
            "total_events": self.learning_index.get("total_events", 0),
            "event_types": self.learning_index.get("event_types", {}),
            "recent_patterns": self.learning_index.get("recent_patterns", []),
            "learning_velocity": self.learning_index.get("learning_velocity", 0.0),
            "top_patterns": self._get_top_patterns(),
            "knowledge_growth": self._calculate_knowledge_growth(),
            "recommendation": self._get_learning_recommendation()
        }
    
    # Internal implementation methods
    
    def _generate_event_id(self, event_type: str, input_data: str, output_data: str) -> str:
        """Generate unique event ID"""
        content = f"{event_type}:{input_data}:{output_data}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _store_in_history(self, event: LearningEvent):
        """Store event in JSONL history file"""
        try:
            with open(self.learning_history_file, "a") as f:
                f.write(json.dumps(asdict(event)) + "\n")
        except Exception as e:
            print(f"Error storing in history: {e}")
    
    def _store_in_chroma(self, event: LearningEvent):
        """Store event in ChromaDB for semantic search"""
        if self.learning_collection is None:
            return
            
        try:
            # Create searchable document combining input, output, and context
            document = f"Event: {event.event_type}\nInput: {event.input_data}\nOutput: {event.output_data}"
            if event.context:
                context_str = json.dumps(event.context, indent=2)
                document += f"\nContext: {context_str}"
            
            metadata = {
                "event_id": event.event_id,
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "tags": ",".join(event.tags),
                "success_score": sum(event.success_metrics.values()) / len(event.success_metrics) if event.success_metrics else 0.0
            }
            
            self.learning_collection.add(
                documents=[document],
                metadatas=[metadata],
                ids=[event.event_id]
            )
            
        except Exception as e:
            print(f"Error storing in ChromaDB: {e}")
    
    def _store_in_neo4j(self, event: LearningEvent):
        """Store event in Neo4j knowledge graph"""
        # Would implement Neo4j storage via MCP
        # For now, prepare the data structure
        neo4j_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "event_type": event.event_type,
            "context": json.dumps(event.context),
            "success_metrics": json.dumps(event.success_metrics)
        }
        
        # In production, would execute via MCP Neo4j client
        # self.mcp_neo4j_client.execute_query(self.neo4j_queries["create_learning_event"], neo4j_data)
    
    def _update_patterns(self, event: LearningEvent):
        """Update or create knowledge patterns based on new event"""
        # Pattern discovery logic based on event type and success
        if event.event_type == "error_resolution" and event.success_metrics.get("resolved", False):
            self._create_error_solution_pattern(event)
        elif event.event_type == "optimization" and event.success_metrics.get("improvement", 0) > 0.1:
            self._create_optimization_pattern(event)
        elif event.event_type == "workflow_improvement":
            self._create_workflow_pattern(event)
    
    def _create_error_solution_pattern(self, event: LearningEvent):
        """Create pattern for error resolution"""
        pattern_id = f"error_solution_{hashlib.sha256(event.input_data.encode()).hexdigest()[:8]}"
        
        if pattern_id not in self.pattern_cache:
            pattern = KnowledgePattern(
                pattern_id=pattern_id,
                pattern_type="error_solution",
                confidence=0.8,
                description=f"Solution for {event.context.get('error_type', 'unknown error')}",
                trigger_conditions={"error_pattern": event.input_data[:200]},
                actions=[{"type": "apply_solution", "solution": event.output_data}],
                success_rate=1.0,
                usage_count=1,
                last_used=event.timestamp
            )
            self.pattern_cache[pattern_id] = pattern
        else:
            # Update existing pattern
            pattern = self.pattern_cache[pattern_id]
            pattern.usage_count += 1
            pattern.last_used = event.timestamp
        
        self._save_patterns()
    
    def _create_optimization_pattern(self, event: LearningEvent):
        """Create pattern for optimization strategies"""
        pattern_id = f"optimization_{hashlib.sha256(event.context.get('target', '').encode()).hexdigest()[:8]}"
        
        improvement = event.success_metrics.get("improvement", 0)
        confidence = min(0.9, 0.5 + improvement)  # Higher improvement = higher confidence
        
        pattern = KnowledgePattern(
            pattern_id=pattern_id,
            pattern_type="optimization_strategy",
            confidence=confidence,
            description=f"Optimization strategy for {event.context.get('target', 'unknown target')}",
            trigger_conditions={"optimization_target": event.context.get("target", "")},
            actions=[{"type": "apply_optimization", "strategy": event.output_data}],
            success_rate=confidence,
            usage_count=1,
            last_used=event.timestamp
        )
        
        self.pattern_cache[pattern_id] = pattern
        self._save_patterns()
    
    def _create_workflow_pattern(self, event: LearningEvent):
        """Create pattern for workflow improvements"""
        # Implementation for workflow pattern creation
        pass
    
    def _update_index(self, event: LearningEvent):
        """Update learning index with new event"""
        self.learning_index["total_events"] = self.learning_index.get("total_events", 0) + 1
        
        # Update event type counts
        event_types = self.learning_index.get("event_types", {})
        event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        self.learning_index["event_types"] = event_types
        
        # Update success rates by event type
        success_rates = self.learning_index.get("success_rates", {})
        if event.success_metrics:
            avg_success = sum(event.success_metrics.values()) / len(event.success_metrics)
            if event.event_type not in success_rates:
                success_rates[event.event_type] = avg_success
            else:
                # Exponential moving average
                alpha = 0.1
                success_rates[event.event_type] = (1 - alpha) * success_rates[event.event_type] + alpha * avg_success
        
        self.learning_index["success_rates"] = success_rates
        
        # Calculate learning velocity (events per hour in recent period)
        recent_events = [e for e in self.recent_events if len(self.recent_events) > 10]
        if len(recent_events) >= 2:
            time_span = (datetime.fromisoformat(recent_events[-1].timestamp.replace('Z', '+00:00')) - 
                        datetime.fromisoformat(recent_events[0].timestamp.replace('Z', '+00:00')))
            hours = time_span.total_seconds() / 3600
            if hours > 0:
                self.learning_index["learning_velocity"] = len(recent_events) / hours
        
        self._save_index()
    
    def _save_patterns(self):
        """Save patterns to file"""
        try:
            patterns_data = {
                "version": "1.0.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "patterns": [asdict(pattern) for pattern in self.pattern_cache.values()]
            }
            with open(self.knowledge_patterns_file, "w") as f:
                json.dump(patterns_data, f, indent=2)
        except Exception as e:
            print(f"Error saving patterns: {e}")
    
    def _save_index(self):
        """Save learning index to file"""
        try:
            with open(self.learning_index_file, "w") as f:
                json.dump(self.learning_index, f, indent=2)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def _fallback_text_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback text search when ChromaDB unavailable"""
        # Simple text matching against stored events
        matches = []
        try:
            if self.learning_history_file.exists():
                with open(self.learning_history_file) as f:
                    for line in f:
                        event_data = json.loads(line.strip())
                        if query.lower() in event_data.get("input_data", "").lower() or \
                           query.lower() in event_data.get("output_data", "").lower():
                            matches.append({
                                "content": f"{event_data.get('input_data', '')} -> {event_data.get('output_data', '')}",
                                "metadata": {
                                    "event_id": event_data.get("event_id"),
                                    "event_type": event_data.get("event_type"),
                                    "timestamp": event_data.get("timestamp")
                                },
                                "similarity": 0.5,  # Approximate
                                "source": "text_search"
                            })
                            if len(matches) >= limit:
                                break
        except Exception as e:
            print(f"Error in fallback search: {e}")
        
        return matches
    
    def _calculate_pattern_match(self, pattern: KnowledgePattern, context: Dict[str, Any]) -> float:
        """Calculate how well a pattern matches current context"""
        if not pattern.trigger_conditions:
            return 0.0
        
        matches = 0
        total_conditions = len(pattern.trigger_conditions)
        
        for key, expected_value in pattern.trigger_conditions.items():
            if key in context:
                actual_value = context[key]
                if isinstance(expected_value, str) and isinstance(actual_value, str):
                    if expected_value.lower() in actual_value.lower():
                        matches += 1
                elif expected_value == actual_value:
                    matches += 1
        
        return matches / total_conditions if total_conditions > 0 else 0.0
    
    def _get_top_patterns(self) -> List[Dict[str, Any]]:
        """Get top performing patterns"""
        patterns = list(self.pattern_cache.values())
        patterns.sort(key=lambda p: (p.success_rate, p.usage_count), reverse=True)
        
        return [
            {
                "pattern_id": p.pattern_id,
                "type": p.pattern_type,
                "success_rate": p.success_rate,
                "usage_count": p.usage_count,
                "description": p.description
            }
            for p in patterns[:10]
        ]
    
    def _calculate_knowledge_growth(self) -> Dict[str, Any]:
        """Calculate knowledge growth metrics"""
        total_events = self.learning_index.get("total_events", 0)
        total_patterns = len(self.pattern_cache)
        
        return {
            "total_events": total_events,
            "total_patterns": total_patterns,
            "events_per_pattern": total_events / max(1, total_patterns),
            "knowledge_density": total_patterns / max(1, total_events) * 100  # Patterns per 100 events
        }
    
    def _get_learning_recommendation(self) -> str:
        """Get recommendation for improving learning"""
        total_events = self.learning_index.get("total_events", 0)
        learning_velocity = self.learning_index.get("learning_velocity", 0.0)
        
        if total_events < 10:
            return "Start accumulating more learning events to build knowledge base"
        elif learning_velocity < 1.0:
            return "Increase learning frequency - aim for more diverse experiences"
        elif len(self.pattern_cache) < total_events / 20:
            return "Focus on pattern recognition - analyze successes for reusable strategies"
        else:
            return "Good learning progress - continue building knowledge graph relationships"


# Example usage and testing
if __name__ == "__main__":
    # Initialize the learning system
    learning_system = AutonomousLearningSystem()
    
    # Example: Learn from an error resolution
    event_id = learning_system.learn_from_event(
        event_type="error_resolution",
        context={"error_type": "ImportError", "module": "missing_package"},
        input_data="ModuleNotFoundError: No module named 'missing_package'",
        output_data="pip install missing_package",
        success_metrics={"resolved": True, "time_to_resolve": 30.0},
        tags=["python", "dependencies", "import_error"]
    )
    
    # Example: Find similar experiences
    similar = learning_system.find_similar_experiences(
        "ImportError with missing module",
        context={"language": "python"}
    )
    
    # Example: Get applicable patterns
    patterns = learning_system.get_applicable_patterns(
        context={"error_type": "ImportError", "language": "python"}
    )
    
    # Example: Get learning insights
    insights = learning_system.get_learning_insights()
    
    print(f"Stored learning event: {event_id}")
    print(f"Found {len(similar)} similar experiences")
    print(f"Found {len(patterns)} applicable patterns")
    print(f"Learning insights: {insights}")