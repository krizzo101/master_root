"""
Self-Learning Loop for Knowledge Learning System

Implements continuous learning from agent interactions and outcomes.
"""

import asyncio
import json
import logging
import uuid
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib


@dataclass
class LearningEvent:
    """Represents an event to learn from"""
    event_type: str  # 'action', 'error', 'success', 'failure'
    timestamp: datetime
    context: Dict[str, Any]
    data: Dict[str, Any]
    outcome: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class Pattern:
    """Represents a discovered pattern"""
    pattern_type: str
    pattern_id: str
    frequency: int
    success_rate: float
    components: List[Dict]
    conditions: Dict[str, Any]
    confidence: float


class SelfLearningLoop:
    """
    Main self-learning system that extracts patterns and knowledge from interactions
    """
    
    def __init__(
        self,
        knowledge_store,
        embedding_service,
        min_pattern_frequency: int = 3,
        min_confidence: float = 0.7
    ):
        """
        Initialize self-learning loop
        
        Args:
            knowledge_store: Neo4j knowledge store
            embedding_service: Embedding service
            min_pattern_frequency: Minimum occurrences to consider a pattern
            min_confidence: Minimum confidence to store knowledge
        """
        self.store = knowledge_store
        self.embedder = embedding_service
        self.min_pattern_frequency = min_pattern_frequency
        self.min_confidence = min_confidence
        
        # Event buffer for pattern detection
        self.event_buffer = []
        self.pattern_cache = {}
        self.session_data = {}
        
        # Learning metrics
        self.metrics = {
            'patterns_discovered': 0,
            'knowledge_created': 0,
            'knowledge_updated': 0,
            'sessions_analyzed': 0
        }
    
    async def capture_event(self, event: LearningEvent):
        """
        Capture an event for learning
        
        Args:
            event: Learning event to capture
        """
        # Add to buffer
        self.event_buffer.append(event)
        
        # Add to session data if session ID provided
        if event.session_id:
            if event.session_id not in self.session_data:
                self.session_data[event.session_id] = {
                    'events': [],
                    'start_time': event.timestamp,
                    'context': event.context
                }
            self.session_data[event.session_id]['events'].append(event)
        
        # Trigger pattern detection if buffer is large enough
        if len(self.event_buffer) >= 50:
            await self.process_event_buffer()
    
    async def process_event_buffer(self):
        """Process buffered events to extract patterns"""
        if not self.event_buffer:
            return
        
        # Group events by type
        events_by_type = defaultdict(list)
        for event in self.event_buffer:
            events_by_type[event.event_type].append(event)
        
        # Process each event type
        for event_type, events in events_by_type.items():
            if event_type == 'action':
                await self._process_action_patterns(events)
            elif event_type == 'error':
                await self._process_error_patterns(events)
            elif event_type in ['success', 'failure']:
                await self._process_outcome_patterns(events)
        
        # Clear processed events
        self.event_buffer = self.event_buffer[-10:]  # Keep last 10 for context
    
    async def _process_action_patterns(self, events: List[LearningEvent]):
        """
        Process action events to find workflow patterns
        
        Args:
            events: List of action events
        """
        # Find sequences of actions that occur together
        sequences = self._find_action_sequences(events)
        
        for sequence in sequences:
            if len(sequence) >= self.min_pattern_frequency:
                pattern = await self._create_workflow_pattern(sequence)
                if pattern and pattern.confidence >= self.min_confidence:
                    await self._store_pattern(pattern)
    
    async def _process_error_patterns(self, events: List[LearningEvent]):
        """
        Process error events to find resolution patterns
        
        Args:
            events: List of error events
        """
        # Group errors by signature
        errors_by_signature = defaultdict(list)
        
        for event in events:
            error_data = event.data
            signature = self._get_error_signature(error_data)
            errors_by_signature[signature].append(event)
        
        # Find successful resolutions
        for signature, error_events in errors_by_signature.items():
            resolutions = self._find_successful_resolutions(error_events)
            
            for resolution in resolutions:
                pattern = await self._create_error_resolution_pattern(
                    signature,
                    resolution
                )
                if pattern and pattern.confidence >= self.min_confidence:
                    await self._store_pattern(pattern)
    
    async def _process_outcome_patterns(self, events: List[LearningEvent]):
        """
        Process outcome events to update knowledge confidence
        
        Args:
            events: List of outcome events
        """
        # Track success/failure for knowledge items
        knowledge_outcomes = defaultdict(lambda: {'success': 0, 'failure': 0})
        
        for event in events:
            if 'knowledge_id' in event.data:
                kid = event.data['knowledge_id']
                if event.event_type == 'success':
                    knowledge_outcomes[kid]['success'] += 1
                else:
                    knowledge_outcomes[kid]['failure'] += 1
        
        # Update knowledge metrics
        for kid, outcomes in knowledge_outcomes.items():
            total = outcomes['success'] + outcomes['failure']
            success_rate = outcomes['success'] / total if total > 0 else 0
            
            # Update confidence based on outcomes
            confidence_delta = 0.1 if success_rate > 0.7 else -0.1
            
            await self.store.update_knowledge_metrics(
                knowledge_id=kid,
                success=success_rate > 0.5,
                confidence_delta=confidence_delta
            )
            
            self.metrics['knowledge_updated'] += 1
    
    def _find_action_sequences(
        self,
        events: List[LearningEvent],
        max_gap_seconds: int = 60
    ) -> List[List[LearningEvent]]:
        """
        Find sequences of related actions
        
        Args:
            events: List of action events
            max_gap_seconds: Maximum time gap between related actions
            
        Returns:
            List of action sequences
        """
        sequences = []
        current_sequence = []
        
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        for event in sorted_events:
            if not current_sequence:
                current_sequence.append(event)
            else:
                time_gap = (event.timestamp - current_sequence[-1].timestamp).seconds
                
                if time_gap <= max_gap_seconds:
                    current_sequence.append(event)
                else:
                    if len(current_sequence) >= 2:
                        sequences.append(current_sequence)
                    current_sequence = [event]
        
        if len(current_sequence) >= 2:
            sequences.append(current_sequence)
        
        return sequences
    
    def _get_error_signature(self, error_data: Dict) -> str:
        """
        Generate unique signature for an error
        
        Args:
            error_data: Error data dictionary
            
        Returns:
            Error signature string
        """
        error_type = error_data.get('type', 'Unknown')
        error_message = error_data.get('message', '')
        
        # Normalize error message
        normalized = error_message.lower()
        # Remove specific values (file paths, line numbers, etc.)
        import re
        normalized = re.sub(r'[/\\][\w\-\.\/\\]+', '<PATH>', normalized)
        normalized = re.sub(r'line \d+', 'line <NUM>', normalized)
        normalized = re.sub(r'\b\d+\b', '<NUM>', normalized)
        
        signature = f"{error_type}:{normalized[:100]}"
        return hashlib.md5(signature.encode()).hexdigest()
    
    def _find_successful_resolutions(
        self,
        error_events: List[LearningEvent]
    ) -> List[Dict]:
        """
        Find successful resolutions for errors
        
        Args:
            error_events: List of error events
            
        Returns:
            List of successful resolution patterns
        """
        resolutions = []
        
        for event in error_events:
            # Check if there's a success event after this error
            if event.session_id:
                session = self.session_data.get(event.session_id)
                if session:
                    # Find actions between error and success
                    error_index = session['events'].index(event)
                    
                    for i in range(error_index + 1, len(session['events'])):
                        if session['events'][i].event_type == 'success':
                            # Found successful resolution
                            resolution_steps = []
                            for j in range(error_index + 1, i):
                                if session['events'][j].event_type == 'action':
                                    resolution_steps.append(session['events'][j].data)
                            
                            if resolution_steps:
                                resolutions.append({
                                    'error': event.data,
                                    'steps': resolution_steps,
                                    'context': event.context
                                })
                            break
        
        return resolutions
    
    async def _create_workflow_pattern(
        self,
        sequence: List[LearningEvent]
    ) -> Optional[Pattern]:
        """
        Create workflow pattern from action sequence
        
        Args:
            sequence: Sequence of action events
            
        Returns:
            Pattern object or None
        """
        # Extract workflow steps
        steps = []
        for event in sequence:
            steps.append({
                'action': event.data.get('action'),
                'tool': event.data.get('tool'),
                'parameters': event.data.get('parameters', {})
            })
        
        # Calculate pattern metrics
        pattern_id = self._generate_pattern_id(steps)
        
        # Check if pattern already exists
        if pattern_id in self.pattern_cache:
            self.pattern_cache[pattern_id]['frequency'] += 1
            return None
        
        # Create new pattern
        pattern = Pattern(
            pattern_type='workflow',
            pattern_id=pattern_id,
            frequency=1,
            success_rate=0.8,  # Initial estimate
            components=steps,
            conditions={
                'min_steps': len(steps),
                'tools_required': list(set(s['tool'] for s in steps if s.get('tool')))
            },
            confidence=0.7
        )
        
        self.pattern_cache[pattern_id] = pattern
        return pattern
    
    async def _create_error_resolution_pattern(
        self,
        error_signature: str,
        resolution: Dict
    ) -> Optional[Pattern]:
        """
        Create error resolution pattern
        
        Args:
            error_signature: Error signature
            resolution: Resolution data
            
        Returns:
            Pattern object or None
        """
        pattern_id = f"error_resolution_{error_signature}"
        
        # Check if pattern exists
        if pattern_id in self.pattern_cache:
            # Update existing pattern
            existing = self.pattern_cache[pattern_id]
            existing.frequency += 1
            existing.confidence = min(1.0, existing.confidence + 0.05)
            return existing
        
        # Create new pattern
        pattern = Pattern(
            pattern_type='error_resolution',
            pattern_id=pattern_id,
            frequency=1,
            success_rate=1.0,  # It worked at least once
            components=resolution['steps'],
            conditions={
                'error_signature': error_signature,
                'error_type': resolution['error'].get('type'),
                'context': resolution['context']
            },
            confidence=0.6
        )
        
        self.pattern_cache[pattern_id] = pattern
        return pattern
    
    async def _store_pattern(self, pattern: Pattern):
        """
        Store pattern as knowledge in Neo4j
        
        Args:
            pattern: Pattern to store
        """
        # Generate content and summary
        if pattern.pattern_type == 'workflow':
            content = self._workflow_pattern_to_content(pattern)
            summary = f"Workflow pattern with {len(pattern.components)} steps"
        elif pattern.pattern_type == 'error_resolution':
            content = self._error_pattern_to_content(pattern)
            summary = f"Error resolution for {pattern.conditions.get('error_type', 'unknown error')}"
        else:
            content = json.dumps(asdict(pattern))
            summary = f"Pattern of type {pattern.pattern_type}"
        
        # Generate embedding
        embedding = await self.embedder.generate_embedding(content)
        
        # Create knowledge entry
        knowledge = Knowledge(
            id=str(uuid.uuid4()),
            type=pattern.pattern_type.title().replace('_', ''),
            content=content,
            summary=summary,
            embedding=embedding,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            confidence_score=pattern.confidence,
            success_rate=pattern.success_rate,
            metadata={
                'pattern_id': pattern.pattern_id,
                'frequency': pattern.frequency,
                'conditions': pattern.conditions
            }
        )
        
        # Store in Neo4j
        await self.store.create_knowledge(knowledge)
        
        self.metrics['patterns_discovered'] += 1
        self.metrics['knowledge_created'] += 1
        
        logging.info(f"Stored new pattern: {pattern.pattern_id}")
    
    def _workflow_pattern_to_content(self, pattern: Pattern) -> str:
        """Convert workflow pattern to content string"""
        steps_text = []
        for i, step in enumerate(pattern.components, 1):
            step_text = f"{i}. {step.get('action', 'Action')}"
            if step.get('tool'):
                step_text += f" using {step['tool']}"
            steps_text.append(step_text)
        
        content = f"""Workflow Pattern:
Steps:
{chr(10).join(steps_text)}

Frequency: {pattern.frequency}
Success Rate: {pattern.success_rate:.2%}
Required Tools: {', '.join(pattern.conditions.get('tools_required', []))}
"""
        return content
    
    def _error_pattern_to_content(self, pattern: Pattern) -> str:
        """Convert error resolution pattern to content string"""
        steps_text = []
        for i, step in enumerate(pattern.components, 1):
            step_text = f"{i}. {step.get('action', 'Action')}"
            if step.get('tool'):
                step_text += f" using {step['tool']}"
            steps_text.append(step_text)
        
        content = f"""Error Resolution Pattern:
Error Type: {pattern.conditions.get('error_type', 'Unknown')}
Error Signature: {pattern.conditions.get('error_signature', '')}

Resolution Steps:
{chr(10).join(steps_text)}

Success Rate: {pattern.success_rate:.2%}
Frequency: {pattern.frequency}
"""
        return content
    
    def _generate_pattern_id(self, components: List[Dict]) -> str:
        """Generate unique ID for a pattern"""
        # Create a normalized representation
        normalized = []
        for comp in components:
            normalized.append(f"{comp.get('action', '')}:{comp.get('tool', '')}")
        
        pattern_str = '|'.join(normalized)
        return hashlib.md5(pattern_str.encode()).hexdigest()
    
    async def analyze_session(self, session_id: str) -> Dict:
        """
        Analyze a completed session for learning
        
        Args:
            session_id: Session ID to analyze
            
        Returns:
            Analysis results
        """
        if session_id not in self.session_data:
            return {'error': 'Session not found'}
        
        session = self.session_data[session_id]
        events = session['events']
        
        # Calculate session metrics
        total_events = len(events)
        error_count = sum(1 for e in events if e.event_type == 'error')
        success_count = sum(1 for e in events if e.event_type == 'success')
        action_count = sum(1 for e in events if e.event_type == 'action')
        
        success_rate = success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0
        
        # Extract patterns from session
        action_sequences = self._find_action_sequences(
            [e for e in events if e.event_type == 'action']
        )
        
        # Store session in Neo4j
        await self._store_session(session_id, session, success_rate)
        
        self.metrics['sessions_analyzed'] += 1
        
        return {
            'session_id': session_id,
            'total_events': total_events,
            'error_count': error_count,
            'success_count': success_count,
            'action_count': action_count,
            'success_rate': success_rate,
            'patterns_found': len(action_sequences),
            'duration': (events[-1].timestamp - events[0].timestamp).seconds if events else 0
        }
    
    async def _store_session(
        self,
        session_id: str,
        session: Dict,
        success_rate: float
    ):
        """Store session data in Neo4j"""
        events = session['events']
        
        query = """
        CREATE (s:Session {
            id: $id,
            started_at: datetime($started_at),
            ended_at: datetime($ended_at),
            user_id: $user_id,
            context: $context,
            event_count: $event_count,
            success_rate: $success_rate
        })
        RETURN s.id as id
        """
        
        params = {
            'id': session_id,
            'started_at': events[0].timestamp.isoformat() if events else datetime.now().isoformat(),
            'ended_at': events[-1].timestamp.isoformat() if events else datetime.now().isoformat(),
            'user_id': session.get('context', {}).get('user_id', 'unknown'),
            'context': json.dumps(session.get('context', {})),
            'event_count': len(events),
            'success_rate': success_rate
        }
        
        await self.store.neo4j.write(query, params)
    
    async def identify_knowledge_gaps(self) -> List[Dict]:
        """
        Identify areas where knowledge is lacking
        
        Returns:
            List of identified knowledge gaps
        """
        gaps = []
        
        # Find frequent errors without resolutions
        unresolved_errors = []
        for event in self.event_buffer:
            if event.event_type == 'error' and event.outcome != 'resolved':
                error_sig = self._get_error_signature(event.data)
                if error_sig not in self.pattern_cache:
                    unresolved_errors.append({
                        'type': 'unresolved_error',
                        'signature': error_sig,
                        'frequency': 1,
                        'last_seen': event.timestamp
                    })
        
        # Find tools with low success rates
        query = """
        MATCH (tu:ToolUsage)
        WHERE tu.success_rate < 0.5
        RETURN tu.tool_name as tool, tu.success_rate as success_rate
        ORDER BY tu.access_count DESC
        LIMIT 10
        """
        
        low_success_tools = await self.store.neo4j.read(query)
        
        for tool in low_success_tools:
            gaps.append({
                'type': 'low_success_tool',
                'tool': tool['tool'],
                'success_rate': tool['success_rate']
            })
        
        # Find contexts with no associated knowledge
        query = """
        MATCH (cp:ContextPattern)
        WHERE NOT (cp)-[:ACTIVATES]->(:Knowledge)
        RETURN cp.context_type as context, cp.triggers as triggers
        """
        
        empty_contexts = await self.store.neo4j.read(query)
        
        for ctx in empty_contexts:
            gaps.append({
                'type': 'empty_context',
                'context': ctx['context'],
                'triggers': ctx['triggers']
            })
        
        return gaps
    
    def get_metrics(self) -> Dict:
        """Get learning metrics"""
        return self.metrics.copy()