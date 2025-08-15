"""
AI Agent Integration for Knowledge Learning System

Provides seamless integration with AI agents for knowledge retrieval and learning.
"""

import asyncio
import json
import logging
import uuid
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Types of agent events"""
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    TOOL_INVOCATION = "tool_invocation"
    ERROR_OCCURRED = "error_occurred"
    SOLUTION_APPLIED = "solution_applied"
    USER_FEEDBACK = "user_feedback"
    CONTEXT_UPDATE = "context_update"


@dataclass
class AgentContext:
    """Current agent context"""
    session_id: str
    user_id: Optional[str]
    conversation_id: str
    current_task: Optional[str]
    language: Optional[str]
    framework: Optional[str]
    tools_available: List[str]
    metadata: Dict[str, Any]


class KnowledgeIntegration:
    """
    Main integration layer for AI agents to use the knowledge system
    """
    
    def __init__(
        self,
        knowledge_store,
        retriever,
        learner,
        embedding_service
    ):
        """
        Initialize integration layer
        
        Args:
            knowledge_store: Neo4j knowledge store
            retriever: Hybrid retrieval system
            learner: Self-learning loop
            embedding_service: Embedding service
        """
        self.store = knowledge_store
        self.retriever = retriever
        self.learner = learner
        self.embedder = embedding_service
        
        # Context management
        self.active_contexts = {}
        self.knowledge_buffer = {}
        
        # Event handlers
        self.event_handlers = {}
        
        # Metrics
        self.metrics = {
            'queries_processed': 0,
            'knowledge_applied': 0,
            'errors_resolved': 0,
            'patterns_learned': 0
        }
    
    async def initialize_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        initial_context: Optional[Dict] = None
    ) -> AgentContext:
        """
        Initialize a new agent session
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            initial_context: Initial context data
            
        Returns:
            Initialized agent context
        """
        context = AgentContext(
            session_id=session_id,
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            current_task=None,
            language=initial_context.get('language') if initial_context else None,
            framework=initial_context.get('framework') if initial_context else None,
            tools_available=initial_context.get('tools', []) if initial_context else [],
            metadata=initial_context or {}
        )
        
        self.active_contexts[session_id] = context
        
        # Preload relevant knowledge
        if user_id:
            await self._preload_user_knowledge(user_id, context)
        
        # Notify learner of session start
        await self.learner.capture_event(LearningEvent(
            event_type='session_start',
            timestamp=datetime.now(),
            context=asdict(context),
            data={'session_id': session_id},
            session_id=session_id
        ))
        
        return context
    
    async def query_knowledge(
        self,
        session_id: str,
        query: str,
        max_results: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Query knowledge base for relevant information
        
        Args:
            session_id: Session identifier
            query: Query text
            max_results: Maximum number of results
            filters: Optional filters
            
        Returns:
            List of relevant knowledge entries (token-optimized)
        """
        # Get current context
        context = self.active_contexts.get(session_id)
        if not context:
            logging.warning(f"Unknown session: {session_id}")
            context_dict = {}
        else:
            context_dict = asdict(context)
        
        # Retrieve knowledge
        results = await self.retriever.retrieve(
            query=query,
            context=context_dict,
            k=max_results,
            filters=filters
        )
        
        # Format for minimal token usage
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result.knowledge_id,
                'summary': result.summary[:200],  # Truncate summary
                'confidence': round(result.confidence_score, 2),
                'relevance': round(result.relevance_score, 2),
                'type': result.metadata.get('type', 'general')
            })
        
        # Track metrics
        self.metrics['queries_processed'] += 1
        
        # Capture query event for learning
        await self.learner.capture_event(LearningEvent(
            event_type='action',
            timestamp=datetime.now(),
            context=context_dict,
            data={
                'action': 'query_knowledge',
                'query': query,
                'results_returned': len(formatted_results)
            },
            session_id=session_id
        ))
        
        return formatted_results
    
    async def apply_knowledge(
        self,
        session_id: str,
        knowledge_id: str
    ) -> Dict:
        """
        Apply specific knowledge and track usage
        
        Args:
            session_id: Session identifier
            knowledge_id: Knowledge entry ID
            
        Returns:
            Full knowledge content for application
        """
        # Retrieve full knowledge
        knowledge = await self.store.get_knowledge(knowledge_id)
        
        if not knowledge:
            return {'error': 'Knowledge not found'}
        
        # Track application
        self.metrics['knowledge_applied'] += 1
        
        # Capture application event
        context = self.active_contexts.get(session_id)
        await self.learner.capture_event(LearningEvent(
            event_type='action',
            timestamp=datetime.now(),
            context=asdict(context) if context else {},
            data={
                'action': 'apply_knowledge',
                'knowledge_id': knowledge_id,
                'knowledge_type': knowledge.get('type')
            },
            session_id=session_id
        ))
        
        # Return actionable content
        return {
            'id': knowledge_id,
            'content': knowledge.get('content', ''),
            'type': knowledge.get('type', 'general'),
            'metadata': {
                'confidence': knowledge.get('confidence_score', 0.5),
                'success_rate': knowledge.get('success_rate', 0.0),
                'last_updated': knowledge.get('updated_at')
            }
        }
    
    async def report_tool_usage(
        self,
        session_id: str,
        tool_name: str,
        parameters: Dict,
        result: Any,
        success: bool,
        execution_time_ms: Optional[int] = None
    ):
        """
        Report tool usage for learning
        
        Args:
            session_id: Session identifier
            tool_name: Name of tool used
            parameters: Tool parameters
            result: Tool execution result
            success: Whether execution was successful
            execution_time_ms: Execution time in milliseconds
        """
        context = self.active_contexts.get(session_id)
        
        # Capture tool usage event
        await self.learner.capture_event(LearningEvent(
            event_type='action',
            timestamp=datetime.now(),
            context=asdict(context) if context else {},
            data={
                'action': 'tool_usage',
                'tool': tool_name,
                'parameters': parameters,
                'success': success,
                'execution_time_ms': execution_time_ms
            },
            outcome='success' if success else 'failure',
            session_id=session_id
        ))
        
        # Check for tool usage patterns
        if success:
            await self._check_tool_pattern(tool_name, parameters, context)
    
    async def report_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Report an error and get potential resolution
        
        Args:
            session_id: Session identifier
            error_type: Type of error
            error_message: Error message
            stack_trace: Optional stack trace
            context_data: Additional context
            
        Returns:
            Potential resolution if found
        """
        context = self.active_contexts.get(session_id)
        
        # Capture error event
        await self.learner.capture_event(LearningEvent(
            event_type='error',
            timestamp=datetime.now(),
            context=asdict(context) if context else {},
            data={
                'type': error_type,
                'message': error_message,
                'stack_trace': stack_trace,
                'context': context_data
            },
            session_id=session_id
        ))
        
        # Search for known resolution
        error_query = f"Error: {error_type} - {error_message}"
        resolutions = await self.retriever.retrieve(
            query=error_query,
            context={'error_type': error_type},
            k=1
        )
        
        if resolutions:
            resolution = resolutions[0]
            self.metrics['errors_resolved'] += 1
            
            # Apply and return resolution
            full_resolution = await self.apply_knowledge(session_id, resolution.knowledge_id)
            return full_resolution
        
        return None
    
    async def report_solution(
        self,
        session_id: str,
        problem_description: str,
        solution_steps: List[Dict],
        success: bool
    ):
        """
        Report a solution attempt for learning
        
        Args:
            session_id: Session identifier
            problem_description: Description of problem
            solution_steps: Steps taken to solve
            success: Whether solution worked
        """
        context = self.active_contexts.get(session_id)
        
        # Capture solution event
        await self.learner.capture_event(LearningEvent(
            event_type='success' if success else 'failure',
            timestamp=datetime.now(),
            context=asdict(context) if context else {},
            data={
                'problem': problem_description,
                'solution_steps': solution_steps,
                'success': success
            },
            session_id=session_id
        ))
        
        # If successful, consider creating new knowledge
        if success:
            await self._create_solution_knowledge(
                problem_description,
                solution_steps,
                context
            )
    
    async def update_context(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ):
        """
        Update session context
        
        Args:
            session_id: Session identifier
            updates: Context updates
        """
        if session_id not in self.active_contexts:
            logging.warning(f"Unknown session: {session_id}")
            return
        
        context = self.active_contexts[session_id]
        
        # Update context fields
        for key, value in updates.items():
            if hasattr(context, key):
                setattr(context, key, value)
            else:
                context.metadata[key] = value
        
        # Capture context update event
        await self.learner.capture_event(LearningEvent(
            event_type='action',
            timestamp=datetime.now(),
            context=asdict(context),
            data={
                'action': 'context_update',
                'updates': updates
            },
            session_id=session_id
        ))
    
    async def end_session(
        self,
        session_id: str,
        success_metrics: Optional[Dict] = None
    ) -> Dict:
        """
        End an agent session and trigger learning
        
        Args:
            session_id: Session identifier
            success_metrics: Optional success metrics
            
        Returns:
            Session analysis results
        """
        if session_id not in self.active_contexts:
            return {'error': 'Unknown session'}
        
        context = self.active_contexts[session_id]
        
        # Capture session end event
        await self.learner.capture_event(LearningEvent(
            event_type='session_end',
            timestamp=datetime.now(),
            context=asdict(context),
            data={
                'metrics': success_metrics or {}
            },
            session_id=session_id
        ))
        
        # Analyze session for learning
        analysis = await self.learner.analyze_session(session_id)
        
        # Clean up
        del self.active_contexts[session_id]
        if session_id in self.knowledge_buffer:
            del self.knowledge_buffer[session_id]
        
        return analysis
    
    async def _preload_user_knowledge(
        self,
        user_id: str,
        context: AgentContext
    ):
        """
        Preload user-specific knowledge
        
        Args:
            user_id: User identifier
            context: Agent context
        """
        # Query user preferences
        query = """
        MATCH (up:UserPreference)
        WHERE up.user_id = $user_id
        RETURN up
        ORDER BY up.priority DESC
        LIMIT 10
        """
        
        preferences = await self.store.neo4j.read(query, {'user_id': user_id})
        
        # Store in buffer for quick access
        if context.session_id not in self.knowledge_buffer:
            self.knowledge_buffer[context.session_id] = {}
        
        self.knowledge_buffer[context.session_id]['preferences'] = preferences
    
    async def _check_tool_pattern(
        self,
        tool_name: str,
        parameters: Dict,
        context: Optional[AgentContext]
    ):
        """
        Check for tool usage patterns
        
        Args:
            tool_name: Tool name
            parameters: Tool parameters
            context: Agent context
        """
        # Look for similar tool usage patterns
        query = """
        MATCH (tu:ToolUsage)
        WHERE tu.tool_name = $tool_name
        AND tu.success_rate > 0.8
        RETURN tu
        ORDER BY tu.access_count DESC
        LIMIT 5
        """
        
        patterns = await self.store.neo4j.read(query, {'tool_name': tool_name})
        
        # Check if current usage matches successful patterns
        for pattern in patterns:
            if self._matches_pattern(parameters, pattern.get('parameters', {})):
                # Boost confidence in this pattern
                await self.store.update_knowledge_metrics(
                    knowledge_id=pattern['id'],
                    success=True,
                    confidence_delta=0.05
                )
    
    async def _create_solution_knowledge(
        self,
        problem: str,
        steps: List[Dict],
        context: Optional[AgentContext]
    ):
        """
        Create new knowledge from successful solution
        
        Args:
            problem: Problem description
            steps: Solution steps
            context: Agent context
        """
        # Format solution content
        content = f"Problem: {problem}\n\nSolution Steps:\n"
        for i, step in enumerate(steps, 1):
            content += f"{i}. {step.get('description', 'Step')}\n"
            if 'code' in step:
                content += f"   Code: {step['code']}\n"
        
        # Generate embedding
        embedding = await self.embedder.generate_embedding(content)
        
        # Create knowledge entry
        knowledge_id = str(uuid.uuid4())
        
        query = """
        CREATE (k:Knowledge:Solution {
            id: $id,
            type: 'Solution',
            content: $content,
            summary: $summary,
            embedding: $embedding,
            created_at: datetime(),
            updated_at: datetime(),
            confidence_score: 0.7,
            success_rate: 1.0,
            access_count: 0
        })
        RETURN k.id as id
        """
        
        await self.store.neo4j.write(query, {
            'id': knowledge_id,
            'content': content,
            'summary': f"Solution for: {problem[:100]}",
            'embedding': embedding
        })
        
        self.metrics['patterns_learned'] += 1
    
    def _matches_pattern(self, params1: Dict, params2: Dict) -> bool:
        """
        Check if two parameter sets match
        
        Args:
            params1: First parameter set
            params2: Second parameter set
            
        Returns:
            True if parameters match
        """
        # Simple matching - can be enhanced
        key_overlap = set(params1.keys()) & set(params2.keys())
        
        if not key_overlap:
            return False
        
        matches = 0
        for key in key_overlap:
            if params1[key] == params2[key]:
                matches += 1
        
        return matches / len(key_overlap) > 0.7
    
    def get_metrics(self) -> Dict:
        """Get integration metrics"""
        return self.metrics.copy()


class MCPKnowledgeTool:
    """
    MCP-compatible tool for knowledge system access
    """
    
    def __init__(self, integration: KnowledgeIntegration):
        """
        Initialize MCP tool
        
        Args:
            integration: Knowledge integration instance
        """
        self.integration = integration
        self.default_session_id = str(uuid.uuid4())
    
    async def query(
        self,
        query: str,
        max_results: int = 5,
        knowledge_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Query knowledge base (MCP-compatible)
        
        Args:
            query: Query text
            max_results: Maximum results
            knowledge_type: Optional type filter
            
        Returns:
            List of knowledge summaries
        """
        filters = {'type': knowledge_type} if knowledge_type else None
        
        return await self.integration.query_knowledge(
            session_id=self.default_session_id,
            query=query,
            max_results=max_results,
            filters=filters
        )
    
    async def apply(self, knowledge_id: str) -> Dict:
        """
        Apply knowledge (MCP-compatible)
        
        Args:
            knowledge_id: Knowledge ID to apply
            
        Returns:
            Knowledge content
        """
        return await self.integration.apply_knowledge(
            session_id=self.default_session_id,
            knowledge_id=knowledge_id
        )
    
    async def report_error(
        self,
        error_type: str,
        error_message: str
    ) -> Optional[Dict]:
        """
        Report error and get resolution (MCP-compatible)
        
        Args:
            error_type: Error type
            error_message: Error message
            
        Returns:
            Resolution if found
        """
        return await self.integration.report_error(
            session_id=self.default_session_id,
            error_type=error_type,
            error_message=error_message
        )


# Import types from other modules
from .self_learning_loop import LearningEvent
from .neo4j_knowledge_store import Knowledge
from dataclasses import asdict