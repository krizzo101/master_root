"""
Multi-Agent Collaboration Framework
Manages coordination between multiple specialized MCP agents with parallel execution
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Message passed between agents"""
    sender: str
    recipient: str  # Can be "broadcast" for all agents
    message_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


@dataclass
class AgentState:
    """Current state of an agent"""
    agent_id: str
    status: str  # idle, working, completed, failed
    current_task: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    output: Optional[Any] = None
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationResult:
    """Result from multi-agent collaboration"""
    success: bool
    artifacts: Dict[str, Any]
    agent_outputs: Dict[str, Any]
    execution_time: float
    parallel_efficiency: float
    errors: List[str]
    learnings: List[Dict]


class AgentCommunicationBus:
    """
    Manages inter-agent communication and shared state
    """
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.subscribers: Dict[str, List[callable]] = defaultdict(list)
        self.shared_state: Dict[str, Any] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
    
    async def publish(self, message: AgentMessage):
        """Publish message to the bus"""
        self.messages.append(message)
        
        # Notify subscribers
        if message.recipient == "broadcast":
            for subscriber_list in self.subscribers.values():
                for callback in subscriber_list:
                    await callback(message)
        elif message.recipient in self.subscribers:
            for callback in self.subscribers[message.recipient]:
                await callback(message)
    
    def subscribe(self, agent_id: str, callback: callable):
        """Subscribe an agent to messages"""
        self.subscribers[agent_id].append(callback)
    
    async def update_shared_state(self, key: str, value: Any, agent_id: str):
        """Update shared state with locking"""
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()
        
        async with self.locks[key]:
            self.shared_state[key] = {
                'value': value,
                'updated_by': agent_id,
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast state change
            await self.publish(AgentMessage(
                sender=agent_id,
                recipient="broadcast",
                message_type="state_update",
                content={'key': key, 'value': value}
            ))
    
    async def get_shared_state(self, key: str) -> Optional[Any]:
        """Get value from shared state"""
        if key in self.shared_state:
            return self.shared_state[key]['value']
        return None
    
    def get_messages_for(self, agent_id: str, since: Optional[datetime] = None) -> List[AgentMessage]:
        """Get messages for a specific agent"""
        messages = []
        for msg in self.messages:
            if msg.recipient in [agent_id, "broadcast"]:
                if since is None or msg.timestamp > since:
                    messages.append(msg)
        return messages


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState(agent_id=agent_id, status="idle")
        self.communication_bus: Optional[AgentCommunicationBus] = None
        self.context: Dict[str, Any] = {}
    
    def connect_to_bus(self, bus: AgentCommunicationBus):
        """Connect to communication bus"""
        self.communication_bus = bus
        bus.subscribe(self.agent_id, self.handle_message)
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming message"""
        if message.message_type == "task_assignment":
            await self.execute_task(message.content)
        elif message.message_type == "state_update":
            await self.handle_state_update(message.content)
        elif message.message_type == "request_info":
            await self.provide_info(message.sender, message.content)
    
    async def execute_task(self, task: Dict) -> Any:
        """Execute assigned task - to be overridden by specific agents"""
        raise NotImplementedError
    
    async def handle_state_update(self, update: Dict):
        """Handle shared state update"""
        # Update local context based on shared state
        if 'key' in update and 'value' in update:
            self.context[update['key']] = update['value']
    
    async def provide_info(self, requester: str, request: Dict):
        """Provide information to requesting agent"""
        info = self.gather_info(request)
        await self.communication_bus.publish(AgentMessage(
            sender=self.agent_id,
            recipient=requester,
            message_type="info_response",
            content=info
        ))
    
    def gather_info(self, request: Dict) -> Dict:
        """Gather requested information"""
        return {'agent_id': self.agent_id, 'state': asdict(self.state)}
    
    async def broadcast_completion(self, result: Any):
        """Broadcast task completion"""
        await self.communication_bus.publish(AgentMessage(
            sender=self.agent_id,
            recipient="broadcast",
            message_type="task_completed",
            content={'agent_id': self.agent_id, 'result': result}
        ))


class ConsultSuiteAgent(BaseAgent):
    """Wrapper for Consult Suite MCP agents"""
    
    def __init__(self, agent_id: str, specific_agent: str):
        super().__init__(agent_id, "consult_suite")
        self.specific_agent = specific_agent
    
    async def execute_task(self, task: Dict) -> Any:
        """Execute task using consult suite"""
        self.state.status = "working"
        self.state.current_task = task.get('description', 'Unknown task')
        
        try:
            # Call the actual MCP consult suite
            # In production:
            # from mcp__consult_suite_enhanced__consult_suite import consult_suite
            # result = await consult_suite(
            #     agent_type=self.specific_agent,
            #     prompt=task['prompt'],
            #     session_id=task.get('session_id', 'default')
            # )
            
            # For now, simulate
            result = {
                'status': 'success',
                'agent': self.specific_agent,
                'output': f"Completed: {task.get('description', 'task')}"
            }
            
            self.state.status = "completed"
            self.state.output = result
            await self.broadcast_completion(result)
            return result
            
        except Exception as e:
            self.state.status = "failed"
            self.state.errors.append(str(e))
            logger.error(f"Agent {self.agent_id} failed: {e}")
            return None


class ClaudeCodeAgent(BaseAgent):
    """Wrapper for Claude Code MCP"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "claude_code")
    
    async def execute_task(self, task: Dict) -> Any:
        """Execute task using Claude Code"""
        self.state.status = "working"
        
        try:
            # In production:
            # from mcp__claude_code__claude_run import claude_run
            # result = await claude_run(
            #     task=task['prompt'],
            #     outputFormat="json",
            #     permissionMode="bypassPermissions"
            # )
            
            # For now, simulate
            result = {
                'status': 'success',
                'code': '# Generated code would be here',
                'explanation': 'Code generation completed'
            }
            
            self.state.status = "completed"
            self.state.output = result
            await self.broadcast_completion(result)
            return result
            
        except Exception as e:
            self.state.status = "failed"
            self.state.errors.append(str(e))
            return None


class GeminiAgent(BaseAgent):
    """Wrapper for Gemini Agent MCP"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "gemini_agent")
    
    async def execute_task(self, task: Dict) -> Any:
        """Execute task using Gemini"""
        self.state.status = "working"
        
        try:
            # In production:
            # from mcp__gemini_agent__execute_gemini import execute_gemini
            # result = await execute_gemini(
            #     task=task['prompt'],
            #     mode=task.get('mode', 'react'),
            #     enable_web_search=True
            # )
            
            result = {
                'status': 'success',
                'analysis': 'Gemini analysis result'
            }
            
            self.state.status = "completed"
            self.state.output = result
            await self.broadcast_completion(result)
            return result
            
        except Exception as e:
            self.state.status = "failed"
            self.state.errors.append(str(e))
            return None


class ResearchAgent(BaseAgent):
    """Research agent using multiple MCP services"""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id, "research")
    
    async def execute_task(self, task: Dict) -> Any:
        """Execute research task"""
        self.state.status = "working"
        research_results = {}
        
        try:
            # Use multiple research sources in parallel
            research_tasks = []
            
            # Brave search
            if task.get('web_search', True):
                research_tasks.append(self.brave_search(task['query']))
            
            # Tech docs
            if task.get('tech_docs', True):
                research_tasks.append(self.search_tech_docs(task['query']))
            
            # Research papers
            if task.get('papers', False):
                research_tasks.append(self.search_papers(task['query']))
            
            # Execute all research in parallel
            results = await asyncio.gather(*research_tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if not isinstance(result, Exception):
                    research_results[f"source_{i}"] = result
            
            self.state.status = "completed"
            self.state.output = research_results
            await self.broadcast_completion(research_results)
            return research_results
            
        except Exception as e:
            self.state.status = "failed"
            self.state.errors.append(str(e))
            return None
    
    async def brave_search(self, query: str) -> Dict:
        """Search using Brave"""
        # In production: use mcp__mcp_web_search__brave_web_search
        return {'source': 'brave', 'results': []}
    
    async def search_tech_docs(self, query: str) -> Dict:
        """Search technical documentation"""
        # In production: use mcp__tech_docs__get-library-docs
        return {'source': 'tech_docs', 'results': []}
    
    async def search_papers(self, query: str) -> Dict:
        """Search research papers"""
        # In production: use mcp__research_papers__search_papers
        return {'source': 'papers', 'results': []}


class MultiAgentCollaborationFramework:
    """
    Main framework for orchestrating multi-agent collaboration
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.communication_bus = AgentCommunicationBus()
        self.execution_metrics = {
            'total_tasks': 0,
            'parallel_tasks': 0,
            'sequential_tasks': 0,
            'average_parallelism': 0
        }
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the framework"""
        self.agents[agent.agent_id] = agent
        agent.connect_to_bus(self.communication_bus)
    
    def create_standard_agents(self) -> List[BaseAgent]:
        """Create standard set of agents"""
        agents = [
            # Consult Suite Agents
            ConsultSuiteAgent("dev_specialist", "development_specialist"),
            ConsultSuiteAgent("code_analyzer", "code_analyzer"),
            ConsultSuiteAgent("solution_architect", "solution_architect"),
            ConsultSuiteAgent("qa_guru", "qa_testing_guru"),
            ConsultSuiteAgent("tech_writer", "technical_writer"),
            ConsultSuiteAgent("security_specialist", "security_specialist"),
            
            # Other MCP Agents
            ClaudeCodeAgent("claude_code"),
            GeminiAgent("gemini"),
            ResearchAgent("research")
        ]
        
        for agent in agents:
            self.register_agent(agent)
        
        return agents
    
    async def collaborate(self, tasks: List[Dict]) -> CollaborationResult:
        """
        Execute collaboration between agents
        """
        start_time = datetime.now()
        
        # Group tasks by dependencies
        task_groups = self.group_tasks_by_dependencies(tasks)
        
        # Execute task groups
        all_results = {}
        errors = []
        
        for group_index, group in enumerate(task_groups):
            logger.info(f"Executing task group {group_index + 1}/{len(task_groups)} with {len(group)} tasks")
            
            # Execute tasks in group in parallel
            group_results = await self.execute_task_group(group)
            
            # Collect results
            for task_id, result in group_results.items():
                all_results[task_id] = result
                if isinstance(result, Exception):
                    errors.append(str(result))
        
        # Calculate metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        parallel_efficiency = self.calculate_parallel_efficiency(task_groups)
        
        # Gather agent outputs
        agent_outputs = {}
        for agent_id, agent in self.agents.items():
            if agent.state.output:
                agent_outputs[agent_id] = agent.state.output
        
        # Extract learnings
        learnings = await self.extract_learnings(all_results, agent_outputs)
        
        return CollaborationResult(
            success=len(errors) == 0,
            artifacts=self.extract_artifacts(agent_outputs),
            agent_outputs=agent_outputs,
            execution_time=execution_time,
            parallel_efficiency=parallel_efficiency,
            errors=errors,
            learnings=learnings
        )
    
    def group_tasks_by_dependencies(self, tasks: List[Dict]) -> List[List[Dict]]:
        """Group tasks by their dependencies for parallel execution"""
        groups = []
        remaining_tasks = tasks.copy()
        completed_task_ids = set()
        
        while remaining_tasks:
            # Find tasks that can be executed (no pending dependencies)
            executable_tasks = []
            for task in remaining_tasks:
                task_deps = task.get('dependencies', [])
                if all(dep in completed_task_ids for dep in task_deps):
                    executable_tasks.append(task)
            
            if not executable_tasks:
                # Circular dependency or error
                logger.error("Circular dependency detected or no executable tasks")
                break
            
            # Add executable tasks to current group
            groups.append(executable_tasks)
            
            # Mark as completed and remove from remaining
            for task in executable_tasks:
                completed_task_ids.add(task['task_id'])
                remaining_tasks.remove(task)
        
        return groups
    
    async def execute_task_group(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Execute a group of tasks in parallel"""
        results = {}
        
        # Create coroutines for all tasks
        coroutines = []
        task_ids = []
        
        for task in tasks:
            agent_id = task['agent_id']
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                coroutines.append(agent.execute_task(task))
                task_ids.append(task['task_id'])
            else:
                logger.error(f"Agent {agent_id} not found for task {task['task_id']}")
                results[task['task_id']] = Exception(f"Agent {agent_id} not found")
        
        # Execute all coroutines in parallel
        if coroutines:
            task_results = await asyncio.gather(*coroutines, return_exceptions=True)
            for task_id, result in zip(task_ids, task_results):
                results[task_id] = result
        
        return results
    
    def calculate_parallel_efficiency(self, task_groups: List[List[Dict]]) -> float:
        """Calculate how efficiently tasks were parallelized"""
        if not task_groups:
            return 0.0
        
        total_tasks = sum(len(group) for group in task_groups)
        max_parallel = max(len(group) for group in task_groups)
        
        # Efficiency is ratio of average parallelism to maximum possible
        average_parallelism = total_tasks / len(task_groups)
        efficiency = average_parallelism / max_parallel if max_parallel > 0 else 0
        
        return min(efficiency, 1.0)
    
    def extract_artifacts(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract concrete artifacts from agent outputs"""
        artifacts = {
            'code': [],
            'documentation': [],
            'tests': [],
            'configs': [],
            'architecture': None
        }
        
        for agent_id, output in agent_outputs.items():
            if not output:
                continue
            
            # Categorize outputs by type
            if 'code' in agent_id or 'dev' in agent_id:
                artifacts['code'].append(output)
            elif 'doc' in agent_id or 'writer' in agent_id:
                artifacts['documentation'].append(output)
            elif 'test' in agent_id or 'qa' in agent_id:
                artifacts['tests'].append(output)
            elif 'architect' in agent_id:
                artifacts['architecture'] = output
        
        return artifacts
    
    async def extract_learnings(self, results: Dict, agent_outputs: Dict) -> List[Dict]:
        """Extract learnings from execution"""
        learnings = []
        
        # Learn from successful patterns
        successful_agents = [aid for aid, out in agent_outputs.items() if out]
        if successful_agents:
            learnings.append({
                'type': 'successful_collaboration',
                'agents': successful_agents,
                'pattern': 'multi_agent_success'
            })
        
        # Learn from failures
        for task_id, result in results.items():
            if isinstance(result, Exception):
                learnings.append({
                    'type': 'failure_pattern',
                    'task': task_id,
                    'error': str(result),
                    'pattern': 'task_failure'
                })
        
        # Learn from communication patterns
        message_patterns = self.analyze_communication_patterns()
        learnings.extend(message_patterns)
        
        return learnings
    
    def analyze_communication_patterns(self) -> List[Dict]:
        """Analyze inter-agent communication patterns"""
        patterns = []
        
        # Count message types
        message_counts = defaultdict(int)
        for msg in self.communication_bus.messages:
            message_counts[msg.message_type] += 1
        
        if message_counts:
            patterns.append({
                'type': 'communication_pattern',
                'message_distribution': dict(message_counts),
                'total_messages': len(self.communication_bus.messages)
            })
        
        return patterns
    
    async def get_agent_status(self) -> Dict[str, AgentState]:
        """Get current status of all agents"""
        return {agent_id: agent.state for agent_id, agent in self.agents.items()}
    
    async def broadcast_to_all(self, message_type: str, content: Any):
        """Broadcast message to all agents"""
        await self.communication_bus.publish(AgentMessage(
            sender="orchestrator",
            recipient="broadcast",
            message_type=message_type,
            content=content
        ))