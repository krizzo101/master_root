"""
Experience Replay - Learn from past experiences and improve decision making
"""

import asyncio
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque, defaultdict
import random
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExperienceOutcome(Enum):
    """Outcome of an experience"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class Experience:
    """Represents a single experience"""
    id: str
    task: str
    context: Dict[str, Any]
    actions: List[Dict[str, Any]]
    outcome: ExperienceOutcome
    reward: float
    execution_time: float
    resources_used: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    lessons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['outcome'] = self.outcome.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def calculate_value(self) -> float:
        """Calculate the value of this experience for learning"""
        # Base value from reward
        value = self.reward
        
        # Adjust for outcome
        if self.outcome == ExperienceOutcome.SUCCESS:
            value *= 1.5
        elif self.outcome == ExperienceOutcome.FAILURE:
            value *= 0.5  # Failures are still valuable for learning
        elif self.outcome == ExperienceOutcome.ERROR:
            value *= 0.3
        
        # Adjust for execution time (prefer faster solutions)
        if self.execution_time > 0:
            time_factor = 1.0 / (1.0 + np.log1p(self.execution_time))
            value *= time_factor
        
        # Value lessons learned
        value += len(self.lessons) * 0.1
        
        return value


class ExperienceReplay:
    """Manages experience replay for learning"""
    
    def __init__(self, capacity: int = 10000, cache_dir: Optional[Path] = None):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.priority_buffer = []  # For prioritized replay
        self.cache_dir = cache_dir or Path.home() / '.autonomous_claude' / 'experiences'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Categorized experiences
        self.by_task: Dict[str, List[Experience]] = defaultdict(list)
        self.by_outcome: Dict[ExperienceOutcome, List[Experience]] = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_experiences': 0,
            'success_rate': 0.0,
            'avg_reward': 0.0,
            'avg_execution_time': 0.0
        }
        
        # Learning parameters
        self.batch_size = 32
        self.learning_rate = 0.01
        self.discount_factor = 0.95
        
        self._lock = asyncio.Lock()
        self._load_experiences()
    
    def _load_experiences(self):
        """Load experiences from cache"""
        experience_file = self.cache_dir / 'experiences.pkl'
        if experience_file.exists():
            try:
                with open(experience_file, 'rb') as f:
                    data = pickle.load(f)
                    experiences = data.get('experiences', [])
                    for exp in experiences[-self.capacity:]:
                        self.buffer.append(exp)
                        self._index_experience(exp)
                    self.stats = data.get('stats', self.stats)
                    logger.info(f"Loaded {len(self.buffer)} experiences from cache")
            except Exception as e:
                logger.error(f"Failed to load experiences: {e}")
    
    def _save_experiences(self):
        """Save experiences to cache"""
        experience_file = self.cache_dir / 'experiences.pkl'
        try:
            data = {
                'experiences': list(self.buffer),
                'stats': self.stats
            }
            with open(experience_file, 'wb') as f:
                pickle.dump(data, f)
            logger.debug("Experiences saved to cache")
        except Exception as e:
            logger.error(f"Failed to save experiences: {e}")
    
    def _index_experience(self, experience: Experience):
        """Index experience for quick retrieval"""
        self.by_task[experience.task].append(experience)
        self.by_outcome[experience.outcome].append(experience)
    
    async def add_experience(self, experience: Experience):
        """Add a new experience to the replay buffer"""
        async with self._lock:
            # Add to buffer
            self.buffer.append(experience)
            self._index_experience(experience)
            
            # Update priority buffer for important experiences
            if experience.outcome in [ExperienceOutcome.SUCCESS, ExperienceOutcome.ERROR]:
                priority = abs(experience.reward) + len(experience.lessons) * 0.5
                self.priority_buffer.append((priority, experience))
                # Keep priority buffer limited
                if len(self.priority_buffer) > self.capacity // 10:
                    self.priority_buffer.sort(key=lambda x: x[0], reverse=True)
                    self.priority_buffer = self.priority_buffer[:self.capacity // 10]
            
            # Update statistics
            self._update_stats(experience)
            
            # Save periodically
            if len(self.buffer) % 100 == 0:
                self._save_experiences()
            
            logger.info(f"Added experience: {experience.task} ({experience.outcome.value})")
    
    def _update_stats(self, experience: Experience):
        """Update running statistics"""
        total = self.stats['total_experiences']
        
        # Update counts
        self.stats['total_experiences'] += 1
        
        # Update success rate
        if experience.outcome == ExperienceOutcome.SUCCESS:
            self.stats['success_rate'] = (
                (self.stats['success_rate'] * total + 1) / (total + 1)
            )
        else:
            self.stats['success_rate'] = (
                (self.stats['success_rate'] * total) / (total + 1)
            )
        
        # Update average reward
        self.stats['avg_reward'] = (
            (self.stats['avg_reward'] * total + experience.reward) / (total + 1)
        )
        
        # Update average execution time
        self.stats['avg_execution_time'] = (
            (self.stats['avg_execution_time'] * total + experience.execution_time) / (total + 1)
        )
    
    async def sample_batch(self, batch_size: Optional[int] = None, 
                          prioritized: bool = True) -> List[Experience]:
        """Sample a batch of experiences for learning"""
        
        batch_size = batch_size or self.batch_size
        
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        if prioritized and self.priority_buffer:
            # Mix prioritized and random sampling
            priority_size = min(batch_size // 2, len(self.priority_buffer))
            random_size = batch_size - priority_size
            
            # Sample from priority buffer
            priority_experiences = random.sample(
                [exp for _, exp in self.priority_buffer],
                priority_size
            )
            
            # Sample randomly from main buffer
            random_experiences = random.sample(list(self.buffer), random_size)
            
            return priority_experiences + random_experiences
        else:
            # Pure random sampling
            return random.sample(list(self.buffer), batch_size)
    
    async def get_similar_experiences(self, task: str, context: Dict[str, Any], 
                                     limit: int = 5) -> List[Experience]:
        """Get similar past experiences"""
        
        # Get experiences for the same task
        task_experiences = self.by_task.get(task, [])
        
        if not task_experiences:
            # Try to find similar tasks
            similar_tasks = []
            task_lower = task.lower()
            for other_task in self.by_task.keys():
                if self._task_similarity(task_lower, other_task.lower()) > 0.5:
                    similar_tasks.extend(self.by_task[other_task])
            task_experiences = similar_tasks
        
        if not task_experiences:
            return []
        
        # Score experiences by context similarity
        scored = []
        for exp in task_experiences:
            score = self._context_similarity(context, exp.context)
            scored.append((exp, score))
        
        # Sort by similarity and return top matches
        scored.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, _ in scored[:limit]]
    
    def _task_similarity(self, task1: str, task2: str) -> float:
        """Calculate similarity between two tasks"""
        # Simple word overlap for now
        words1 = set(task1.split())
        words2 = set(task2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts"""
        # Compare keys
        keys1 = set(context1.keys())
        keys2 = set(context2.keys())
        
        if not keys1 or not keys2:
            return 0.0
        
        key_similarity = len(keys1 & keys2) / len(keys1 | keys2)
        
        # Compare values for common keys
        common_keys = keys1 & keys2
        if common_keys:
            value_matches = sum(
                1 for k in common_keys
                if str(context1[k]) == str(context2[k])
            )
            value_similarity = value_matches / len(common_keys)
        else:
            value_similarity = 0.0
        
        return (key_similarity + value_similarity) / 2
    
    async def learn_from_batch(self, batch: Optional[List[Experience]] = None) -> Dict[str, Any]:
        """Learn from a batch of experiences"""
        
        if batch is None:
            batch = await self.sample_batch()
        
        if not batch:
            return {'status': 'no_experiences'}
        
        # Extract lessons from experiences
        lessons_learned = []
        patterns_identified = []
        optimizations_found = []
        
        for exp in batch:
            # Learn from successes
            if exp.outcome == ExperienceOutcome.SUCCESS:
                lesson = {
                    'type': 'success_pattern',
                    'task': exp.task,
                    'actions': exp.actions,
                    'execution_time': exp.execution_time,
                    'resources': exp.resources_used
                }
                patterns_identified.append(lesson)
            
            # Learn from failures
            elif exp.outcome in [ExperienceOutcome.FAILURE, ExperienceOutcome.ERROR]:
                lesson = {
                    'type': 'failure_avoidance',
                    'task': exp.task,
                    'errors': exp.errors,
                    'context': exp.context
                }
                lessons_learned.append(lesson)
            
            # Look for optimization opportunities
            if exp.execution_time > 0:
                similar = await self.get_similar_experiences(exp.task, exp.context, limit=3)
                if similar:
                    avg_time = np.mean([e.execution_time for e in similar])
                    if exp.execution_time < avg_time * 0.7:
                        optimization = {
                            'task': exp.task,
                            'improvement': (avg_time - exp.execution_time) / avg_time,
                            'method': exp.actions
                        }
                        optimizations_found.append(optimization)
        
        # Calculate Q-values for reinforcement learning
        q_values = self._calculate_q_values(batch)
        
        return {
            'batch_size': len(batch),
            'lessons_learned': lessons_learned,
            'patterns_identified': patterns_identified,
            'optimizations_found': optimizations_found,
            'q_values': q_values,
            'learning_rate': self.learning_rate
        }
    
    def _calculate_q_values(self, experiences: List[Experience]) -> Dict[str, float]:
        """Calculate Q-values for experiences (simplified Q-learning)"""
        
        q_values = {}
        
        for exp in experiences:
            # State is represented by task + context hash
            state = f"{exp.task}_{hash(json.dumps(exp.context, sort_keys=True)) % 10000}"
            
            # Action is represented by the action sequence
            action = json.dumps(exp.actions, sort_keys=True)
            
            # Calculate Q-value
            immediate_reward = exp.reward
            
            # Estimate future rewards (simplified)
            future_reward = 0.0
            similar = [e for e in self.buffer if e.task == exp.task]
            if similar:
                future_reward = max(e.reward for e in similar) * self.discount_factor
            
            q_value = immediate_reward + future_reward
            
            key = f"{state}:{action[:50]}"  # Truncate action for key
            
            # Update with learning rate
            if key in q_values:
                q_values[key] = q_values[key] * (1 - self.learning_rate) + q_value * self.learning_rate
            else:
                q_values[key] = q_value
        
        return q_values
    
    async def get_best_action(self, task: str, context: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Get the best action sequence based on past experiences"""
        
        similar_experiences = await self.get_similar_experiences(task, context, limit=10)
        
        if not similar_experiences:
            return None
        
        # Find successful experiences
        successful = [
            exp for exp in similar_experiences
            if exp.outcome == ExperienceOutcome.SUCCESS
        ]
        
        if not successful:
            # No successful experiences, return None
            return None
        
        # Choose the best based on reward and execution time
        best = max(successful, key=lambda e: e.calculate_value())
        
        return best.actions
    
    async def analyze_failures(self, task: Optional[str] = None) -> Dict[str, Any]:
        """Analyze failure patterns"""
        
        if task:
            failures = [
                exp for exp in self.by_task.get(task, [])
                if exp.outcome in [ExperienceOutcome.FAILURE, ExperienceOutcome.ERROR]
            ]
        else:
            failures = self.by_outcome.get(ExperienceOutcome.FAILURE, []) + \
                      self.by_outcome.get(ExperienceOutcome.ERROR, [])
        
        if not failures:
            return {'message': 'No failures to analyze'}
        
        # Analyze error patterns
        error_counts = defaultdict(int)
        for exp in failures:
            for error in exp.errors:
                error_counts[error] += 1
        
        # Find common failure contexts
        context_patterns = defaultdict(list)
        for exp in failures:
            for key, value in exp.context.items():
                context_patterns[key].append(value)
        
        # Identify most problematic contexts
        problematic_contexts = {}
        for key, values in context_patterns.items():
            if len(values) > 1:
                # Find most common value
                value_counts = defaultdict(int)
                for v in values:
                    value_counts[str(v)] += 1
                most_common = max(value_counts.items(), key=lambda x: x[1])
                if most_common[1] > len(failures) * 0.3:  # Appears in >30% of failures
                    problematic_contexts[key] = most_common[0]
        
        return {
            'total_failures': len(failures),
            'common_errors': dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'problematic_contexts': problematic_contexts,
            'failure_rate': len(failures) / len(self.buffer) if self.buffer else 0
        }
    
    async def consolidate_experiences(self, min_similarity: float = 0.8):
        """Consolidate similar experiences to reduce redundancy"""
        async with self._lock:
            consolidated = []
            processed = set()
            
            for i, exp1 in enumerate(self.buffer):
                if i in processed:
                    continue
                
                similar_group = [exp1]
                processed.add(i)
                
                for j, exp2 in enumerate(self.buffer[i+1:], i+1):
                    if j in processed:
                        continue
                    
                    if (exp1.task == exp2.task and 
                        self._context_similarity(exp1.context, exp2.context) > min_similarity):
                        similar_group.append(exp2)
                        processed.add(j)
                
                if len(similar_group) > 1:
                    # Create consolidated experience
                    consolidated_exp = self._merge_experiences(similar_group)
                    consolidated.append(consolidated_exp)
                else:
                    consolidated.append(exp1)
            
            # Replace buffer with consolidated experiences
            self.buffer = deque(consolidated, maxlen=self.capacity)
            
            # Rebuild indices
            self.by_task.clear()
            self.by_outcome.clear()
            for exp in self.buffer:
                self._index_experience(exp)
            
            self._save_experiences()
            
            logger.info(f"Consolidated experiences: {len(self.buffer)} remaining")
    
    def _merge_experiences(self, experiences: List[Experience]) -> Experience:
        """Merge multiple similar experiences into one"""
        
        # Use the most recent experience as base
        base = max(experiences, key=lambda e: e.timestamp)
        
        # Aggregate metrics
        avg_reward = np.mean([e.reward for e in experiences])
        avg_time = np.mean([e.execution_time for e in experiences])
        
        # Combine lessons
        all_lessons = []
        for exp in experiences:
            all_lessons.extend(exp.lessons)
        unique_lessons = list(set(all_lessons))
        
        # Determine outcome (majority vote)
        outcome_counts = defaultdict(int)
        for exp in experiences:
            outcome_counts[exp.outcome] += 1
        majority_outcome = max(outcome_counts.items(), key=lambda x: x[1])[0]
        
        return Experience(
            id=f"merged_{base.id}",
            task=base.task,
            context=base.context,
            actions=base.actions,
            outcome=majority_outcome,
            reward=avg_reward,
            execution_time=avg_time,
            resources_used=base.resources_used,
            errors=base.errors,
            lessons=unique_lessons,
            timestamp=base.timestamp,
            metadata={**base.metadata, 'merged_count': len(experiences)}
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get replay buffer statistics"""
        
        outcome_distribution = {
            outcome.value: len(experiences)
            for outcome, experiences in self.by_outcome.items()
        }
        
        task_distribution = sorted(
            [(task, len(exps)) for task, exps in self.by_task.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'buffer_size': len(self.buffer),
            'capacity': self.capacity,
            'utilization': len(self.buffer) / self.capacity,
            'stats': self.stats,
            'outcome_distribution': outcome_distribution,
            'top_tasks': task_distribution,
            'priority_buffer_size': len(self.priority_buffer),
            'unique_tasks': len(self.by_task)
        }
    
    async def export_experiences(self, output_file: Path, 
                                outcome_filter: Optional[ExperienceOutcome] = None):
        """Export experiences to JSON"""
        
        if outcome_filter:
            experiences = self.by_outcome.get(outcome_filter, [])
        else:
            experiences = list(self.buffer)
        
        data = [exp.to_dict() for exp in experiences]
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(data)} experiences to {output_file}")
    
    async def clear_old_experiences(self, days: int = 30):
        """Clear experiences older than specified days"""
        async with self._lock:
            cutoff = datetime.now() - timedelta(days=days)
            
            new_buffer = deque(maxlen=self.capacity)
            for exp in self.buffer:
                if exp.timestamp > cutoff:
                    new_buffer.append(exp)
            
            removed = len(self.buffer) - len(new_buffer)
            self.buffer = new_buffer
            
            # Rebuild indices
            self.by_task.clear()
            self.by_outcome.clear()
            for exp in self.buffer:
                self._index_experience(exp)
            
            self._save_experiences()
            
            logger.info(f"Removed {removed} old experiences")
            return removed