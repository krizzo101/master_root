"""
Standalone Pattern Engine Core - Extracted and Enhanced
Distributed pattern recognition and learning system
"""

import asyncio
import json
import pickle
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Make Redis optional for local mode
try:
    import redis.asyncio as redis
    from redis.asyncio.lock import Lock as RedisLock
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    RedisLock = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be recognized"""
    TASK_SEQUENCE = "task_sequence"
    ERROR_RECOVERY = "error_recovery"
    OPTIMIZATION = "optimization"
    TOOL_USAGE = "tool_usage"
    SUCCESS_PATH = "success_path"
    FAILURE_MODE = "failure_mode"
    USER_PREFERENCE = "user_preference"
    CONTEXT_SWITCH = "context_switch"
    DISTRIBUTED = "distributed"  # New: patterns from federated learning


@dataclass
class Pattern:
    """Enhanced pattern with distributed learning support"""
    id: str
    type: PatternType
    description: str
    trigger_conditions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    occurrences: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    source_node: str = "local"  # Track which node discovered this pattern
    global_occurrences: int = 0  # Track occurrences across all nodes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'type': self.type.value,
            'description': self.description,
            'trigger_conditions': self.trigger_conditions,
            'actions': self.actions,
            'confidence': self.confidence,
            'occurrences': self.occurrences,
            'success_rate': self.success_rate,
            'avg_execution_time': self.avg_execution_time,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'source_node': self.source_node,
            'global_occurrences': self.global_occurrences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        """Create pattern from dictionary"""
        return cls(
            id=data['id'],
            type=PatternType(data['type']),
            description=data['description'],
            trigger_conditions=data.get('trigger_conditions', []),
            actions=data.get('actions', []),
            confidence=data.get('confidence', 0.0),
            occurrences=data.get('occurrences', 0),
            success_rate=data.get('success_rate', 0.0),
            avg_execution_time=data.get('avg_execution_time', 0.0),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
            source_node=data.get('source_node', 'local'),
            global_occurrences=data.get('global_occurrences', 0)
        )
    
    def matches(self, context: Dict[str, Any]) -> float:
        """Calculate match score for given context"""
        score = 0.0
        
        for condition in self.trigger_conditions:
            if self._evaluate_condition(condition, context):
                score += 1.0
        
        if self.trigger_conditions:
            score = score / len(self.trigger_conditions)
        
        # Weight by confidence and success rate
        score *= self.confidence * self.success_rate
        
        return score
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition against context"""
        try:
            condition_lower = condition.lower()
            context_str = json.dumps(context).lower()
            return condition_lower in context_str
        except:
            return False


class DistributedPatternEngine:
    """Enhanced Pattern Engine with distributed learning capabilities"""
    
    def __init__(self, node_id: str = None, redis_url: str = None, cache_dir: Optional[Path] = None):
        self.node_id = node_id or f"node_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        self.patterns: Dict[str, Pattern] = {}
        self.pattern_index: Dict[PatternType, Set[str]] = defaultdict(set)
        self.sequence_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 1000
        self.cache_dir = cache_dir or Path(f'/tmp/pattern_engine_{self.node_id}')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ML components
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.pattern_vectors = None
        self.pattern_ids = []
        
        # Statistics
        self.pattern_stats = defaultdict(lambda: {
            'triggers': 0,
            'successes': 0,
            'failures': 0,
            'total_time': 0.0
        })
        
        # Distributed components
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.federation_channel = "pattern_federation"
        self.discovery_channel = "pattern_discovery"
        
        self._lock = asyncio.Lock()
        self._federation_task = None
    
    async def initialize(self):
        """Initialize distributed components"""
        try:
            # Connect to Redis if available and URL provided
            if REDIS_AVAILABLE and self.redis_url and self.redis_url != "None":
                self.redis_client = await redis.from_url(self.redis_url)
                self.pubsub = self.redis_client.pubsub()
            
                # Subscribe to federation channels
                await self.pubsub.subscribe(self.federation_channel, self.discovery_channel)
                
                # Start federation listener
                self._federation_task = asyncio.create_task(self._federation_listener())
            
            # Load local patterns
            await self._load_patterns()
            
            # Sync with distributed patterns
            await self._sync_distributed_patterns()
            
            logger.info(f"Pattern Engine {self.node_id} initialized with {len(self.patterns)} patterns")
            
        except Exception as e:
            logger.error(f"Failed to initialize distributed components: {e}")
            # Fall back to local-only mode
            await self._load_patterns()
    
    async def _federation_listener(self):
        """Listen for pattern updates from other nodes"""
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self._handle_federation_message(message)
        except Exception as e:
            logger.error(f"Federation listener error: {e}")
    
    async def _handle_federation_message(self, message):
        """Handle incoming pattern federation messages"""
        try:
            data = json.loads(message['data'])
            
            if message['channel'].decode() == self.discovery_channel:
                # New pattern discovered by another node
                pattern = Pattern.from_dict(data['pattern'])
                await self._integrate_federated_pattern(pattern)
                
            elif message['channel'].decode() == self.federation_channel:
                # Pattern update from another node
                if data['type'] == 'update':
                    await self._update_federated_stats(data['pattern_id'], data['stats'])
                    
        except Exception as e:
            logger.error(f"Error handling federation message: {e}")
    
    async def _integrate_federated_pattern(self, pattern: Pattern):
        """Integrate a pattern discovered by another node"""
        async with self._lock:
            if pattern.id in self.patterns:
                # Merge with existing pattern
                existing = self.patterns[pattern.id]
                existing.global_occurrences += pattern.occurrences
                existing.confidence = max(existing.confidence, pattern.confidence)
                
                # Weighted average for success rate
                total_occurrences = existing.occurrences + pattern.occurrences
                if total_occurrences > 0:
                    existing.success_rate = (
                        (existing.success_rate * existing.occurrences + 
                         pattern.success_rate * pattern.occurrences) / 
                        total_occurrences
                    )
            else:
                # Add new federated pattern
                pattern.metadata['federated'] = True
                self.patterns[pattern.id] = pattern
                self.pattern_index[pattern.type].add(pattern.id)
                
                logger.info(f"Integrated federated pattern {pattern.id} from {pattern.source_node}")
    
    async def _sync_distributed_patterns(self):
        """Sync patterns with distributed storage"""
        if not self.redis_client:
            return
        
        try:
            # Get all patterns from Redis
            pattern_keys = await self.redis_client.keys("pattern:*")
            
            for key in pattern_keys:
                pattern_data = await self.redis_client.get(key)
                if pattern_data:
                    pattern = Pattern.from_dict(json.loads(pattern_data))
                    await self._integrate_federated_pattern(pattern)
            
            logger.info(f"Synced {len(pattern_keys)} patterns from distributed storage")
            
        except Exception as e:
            logger.error(f"Failed to sync distributed patterns: {e}")
    
    async def register_pattern(self, pattern: Pattern) -> bool:
        """Register a new pattern and broadcast to other nodes"""
        async with self._lock:
            try:
                # Set source node
                pattern.source_node = self.node_id
                
                # Register locally
                if pattern.id in self.patterns:
                    existing = self.patterns[pattern.id]
                    existing.occurrences += pattern.occurrences
                    existing.confidence = max(existing.confidence, pattern.confidence)
                    existing.last_used = datetime.now()
                else:
                    self.patterns[pattern.id] = pattern
                    self.pattern_index[pattern.type].add(pattern.id)
                    
                    # Update vector representation
                    await self._update_pattern_vectors()
                
                # Broadcast to other nodes if connected
                if self.redis_client:
                    # Store in Redis
                    await self.redis_client.set(
                        f"pattern:{pattern.id}",
                        json.dumps(pattern.to_dict()),
                        ex=86400 * 7  # Expire after 7 days
                    )
                    
                    # Publish discovery event
                    await self.redis_client.publish(
                        self.discovery_channel,
                        json.dumps({'pattern': pattern.to_dict()})
                    )
                
                self._save_patterns()
                logger.info(f"Registered pattern: {pattern.id} ({pattern.type.value})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to register pattern: {e}")
                return False
    
    async def observe_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Observe an interaction and return insights"""
        async with self._lock:
            # Add to sequence buffer
            self.sequence_buffer.append({
                'timestamp': datetime.now(),
                'interaction': interaction,
                'node_id': self.node_id
            })
            
            # Trim buffer if too large
            if len(self.sequence_buffer) > self.max_buffer_size:
                self.sequence_buffer = self.sequence_buffer[-self.max_buffer_size:]
            
            # Extract patterns
            new_patterns = await self._extract_patterns(interaction)
            
            # Find matching patterns
            matches = await self.find_matching_patterns(interaction)
            
            # Update statistics
            for pattern_id, score in matches:
                self.pattern_stats[pattern_id]['triggers'] += 1
                
                # Broadcast stats update if connected
                if self.redis_client:
                    await self.redis_client.publish(
                        self.federation_channel,
                        json.dumps({
                            'type': 'update',
                            'pattern_id': pattern_id,
                            'stats': self.pattern_stats[pattern_id],
                            'node_id': self.node_id
                        })
                    )
            
            return {
                'new_patterns': len(new_patterns),
                'matching_patterns': len(matches),
                'top_match': matches[0] if matches else None,
                'node_id': self.node_id
            }
    
    async def _extract_patterns(self, interaction: Dict[str, Any]) -> List[Pattern]:
        """Extract patterns from interaction"""
        new_patterns = []
        
        # Extract different pattern types
        if len(self.sequence_buffer) >= 3:
            seq_patterns = await self._extract_sequence_patterns()
            new_patterns.extend(seq_patterns)
        
        if interaction.get('error'):
            error_patterns = await self._extract_error_patterns(interaction)
            new_patterns.extend(error_patterns)
        
        if interaction.get('tool_used'):
            tool_patterns = await self._extract_tool_patterns(interaction)
            new_patterns.extend(tool_patterns)
        
        if interaction.get('execution_time'):
            opt_patterns = await self._extract_optimization_patterns(interaction)
            new_patterns.extend(opt_patterns)
        
        # Register all new patterns
        for pattern in new_patterns:
            await self.register_pattern(pattern)
        
        return new_patterns
    
    async def _extract_sequence_patterns(self) -> List[Pattern]:
        """Extract sequence patterns from buffer"""
        patterns = []
        recent = self.sequence_buffer[-10:]
        
        tasks = [item['interaction'].get('task', '') for item in recent if item['interaction'].get('task')]
        
        if len(tasks) >= 3:
            for i in range(len(tasks) - 2):
                sequence = tasks[i:i+3]
                sequence_key = ' -> '.join(sequence)
                
                count = self._count_sequence(sequence)
                
                if count >= 2:
                    pattern_id = f"seq_{hashlib.md5(sequence_key.encode()).hexdigest()[:8]}"
                    
                    if pattern_id not in self.patterns:
                        pattern = Pattern(
                            id=pattern_id,
                            type=PatternType.TASK_SEQUENCE,
                            description=f"Task sequence: {sequence_key}",
                            trigger_conditions=[sequence[0]],
                            actions=sequence[1:],
                            confidence=min(count / 10.0, 1.0),
                            occurrences=count,
                            source_node=self.node_id
                        )
                        patterns.append(pattern)
        
        return patterns
    
    async def _extract_error_patterns(self, interaction: Dict[str, Any]) -> List[Pattern]:
        """Extract error recovery patterns"""
        patterns = []
        
        error = interaction.get('error')
        recovery = interaction.get('recovery_action')
        
        if error and recovery:
            pattern_id = f"error_{hashlib.md5(str(error).encode()).hexdigest()[:8]}"
            
            if pattern_id not in self.patterns:
                pattern = Pattern(
                    id=pattern_id,
                    type=PatternType.ERROR_RECOVERY,
                    description=f"Recovery for: {str(error)[:100]}",
                    trigger_conditions=[str(error)],
                    actions=[recovery],
                    confidence=0.5,
                    occurrences=1,
                    source_node=self.node_id
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _extract_tool_patterns(self, interaction: Dict[str, Any]) -> List[Pattern]:
        """Extract tool usage patterns"""
        patterns = []
        
        task = interaction.get('task', '')
        tool = interaction.get('tool_used', '')
        success = interaction.get('success', False)
        
        if task and tool:
            pattern_id = f"tool_{hashlib.md5(f'{task}_{tool}'.encode()).hexdigest()[:8]}"
            
            if pattern_id not in self.patterns:
                pattern = Pattern(
                    id=pattern_id,
                    type=PatternType.TOOL_USAGE,
                    description=f"Use {tool} for {task[:50]}",
                    trigger_conditions=[task],
                    actions=[f"use_tool:{tool}"],
                    confidence=0.7,
                    occurrences=1,
                    success_rate=1.0 if success else 0.0,
                    source_node=self.node_id
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _extract_optimization_patterns(self, interaction: Dict[str, Any]) -> List[Pattern]:
        """Extract optimization patterns"""
        patterns = []
        
        task = interaction.get('task', '')
        execution_time = interaction.get('execution_time', 0)
        method = interaction.get('method', '')
        
        if task and execution_time and method:
            similar_tasks = [
                item for item in self.sequence_buffer
                if item['interaction'].get('task') == task
            ]
            
            if len(similar_tasks) >= 2:
                times = [
                    item['interaction'].get('execution_time', float('inf'))
                    for item in similar_tasks
                ]
                
                avg_time = np.mean([t for t in times if t != float('inf')])
                
                if execution_time < avg_time * 0.5:  # 50% faster
                    pattern_id = f"opt_{hashlib.md5(f'{task}_{method}'.encode()).hexdigest()[:8]}"
                    
                    if pattern_id not in self.patterns:
                        pattern = Pattern(
                            id=pattern_id,
                            type=PatternType.OPTIMIZATION,
                            description=f"Fast method for {task[:50]}: {method}",
                            trigger_conditions=[task],
                            actions=[f"method:{method}"],
                            confidence=0.8,
                            occurrences=1,
                            avg_execution_time=execution_time,
                            source_node=self.node_id
                        )
                        patterns.append(pattern)
        
        return patterns
    
    def _count_sequence(self, sequence: List[str]) -> int:
        """Count occurrences of a sequence in buffer"""
        count = 0
        buffer_tasks = [
            item['interaction'].get('task', '') 
            for item in self.sequence_buffer 
            if item['interaction'].get('task')
        ]
        
        for i in range(len(buffer_tasks) - len(sequence) + 1):
            if buffer_tasks[i:i+len(sequence)] == sequence:
                count += 1
        
        return count
    
    async def find_matching_patterns(self, context: Dict[str, Any], 
                                    threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Find patterns matching the given context"""
        matches = []
        
        # Convert context to text
        context_text = json.dumps(context)
        
        # Use vector similarity if available
        if self.pattern_vectors is not None:
            try:
                context_vector = self.vectorizer.transform([context_text])
                similarities = cosine_similarity(context_vector, self.pattern_vectors)[0]
                
                for i, similarity in enumerate(similarities):
                    if similarity > threshold:
                        pattern_id = self.pattern_ids[i]
                        pattern = self.patterns[pattern_id]
                        
                        # Calculate final score with federated boost
                        score = similarity * pattern.confidence * pattern.success_rate
                        
                        # Boost score for patterns with global confirmation
                        if pattern.global_occurrences > pattern.occurrences:
                            score *= 1.2
                        
                        if score > threshold:
                            matches.append((pattern_id, score))
            except:
                pass
        
        # Fallback to direct matching
        for pattern_id, pattern in self.patterns.items():
            score = pattern.matches(context)
            if score > threshold:
                matches.append((pattern_id, score))
        
        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:10]
    
    async def _update_pattern_vectors(self):
        """Update vector representations of patterns"""
        if not self.patterns:
            return
        
        try:
            pattern_texts = []
            self.pattern_ids = []
            
            for pattern_id, pattern in self.patterns.items():
                text = f"{pattern.description} {' '.join(pattern.trigger_conditions)} {' '.join(pattern.actions)}"
                pattern_texts.append(text)
                self.pattern_ids.append(pattern_id)
            
            self.pattern_vectors = self.vectorizer.fit_transform(pattern_texts)
            
        except Exception as e:
            logger.error(f"Failed to update pattern vectors: {e}")
    
    async def get_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get action recommendations based on patterns"""
        recommendations = []
        matches = await self.find_matching_patterns(context)
        
        for pattern_id, score in matches[:5]:
            pattern = self.patterns[pattern_id]
            
            recommendation = {
                'pattern_id': pattern_id,
                'type': pattern.type.value,
                'actions': pattern.actions,
                'confidence': score,
                'reasoning': pattern.description,
                'success_rate': pattern.success_rate,
                'avg_time': pattern.avg_execution_time,
                'source_node': pattern.source_node,
                'global_confirmations': pattern.global_occurrences
            }
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pattern engine statistics"""
        total_patterns = len(self.patterns)
        local_patterns = sum(1 for p in self.patterns.values() if p.source_node == self.node_id)
        federated_patterns = total_patterns - local_patterns
        
        by_type = {
            ptype.value: len(self.pattern_index[ptype])
            for ptype in PatternType
        }
        
        avg_confidence = np.mean([p.confidence for p in self.patterns.values()]) if self.patterns else 0
        avg_success_rate = np.mean([p.success_rate for p in self.patterns.values()]) if self.patterns else 0
        
        successful_patterns = sorted(
            self.patterns.values(),
            key=lambda p: p.success_rate * p.occurrences,
            reverse=True
        )[:5]
        
        return {
            'node_id': self.node_id,
            'total_patterns': total_patterns,
            'local_patterns': local_patterns,
            'federated_patterns': federated_patterns,
            'by_type': by_type,
            'avg_confidence': avg_confidence,
            'avg_success_rate': avg_success_rate,
            'buffer_size': len(self.sequence_buffer),
            'most_successful': [
                {
                    'id': p.id,
                    'type': p.type.value,
                    'description': p.description,
                    'success_rate': p.success_rate,
                    'occurrences': p.occurrences,
                    'source': p.source_node
                }
                for p in successful_patterns
            ]
        }
    
    async def shutdown(self):
        """Clean shutdown"""
        if self._federation_task:
            self._federation_task.cancel()
        
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        self._save_patterns()
        logger.info(f"Pattern Engine {self.node_id} shutdown complete")
    
    def _save_patterns(self):
        """Save patterns to local cache"""
        pattern_file = self.cache_dir / 'patterns.pkl'
        try:
            data = {
                'patterns': {pid: p.to_dict() for pid, p in self.patterns.items()},
                'stats': dict(self.pattern_stats)
            }
            with open(pattern_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    async def _load_patterns(self):
        """Load patterns from local cache"""
        pattern_file = self.cache_dir / 'patterns.pkl'
        if pattern_file.exists():
            try:
                with open(pattern_file, 'rb') as f:
                    data = pickle.load(f)
                    
                    for pid, pdata in data.get('patterns', {}).items():
                        pattern = Pattern.from_dict(pdata)
                        self.patterns[pid] = pattern
                        self.pattern_index[pattern.type].add(pid)
                    
                    self.pattern_stats = data.get('stats', defaultdict(lambda: {
                        'triggers': 0,
                        'successes': 0,
                        'failures': 0,
                        'total_time': 0.0
                    }))
                    
                logger.info(f"Loaded {len(self.patterns)} patterns from cache")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")