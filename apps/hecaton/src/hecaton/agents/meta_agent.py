"""
Meta-Agent implementation for intelligent coordination and delegation.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Agent capability types"""

    RESEARCH = "research"
    CODING = "coding"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"


@dataclass
class AgentProfile:
    """Profile of an agent's capabilities and performance"""

    agent_id: str
    capabilities: List[AgentCapability]
    performance_score: float  # 0.0 to 1.0
    current_load: float  # 0.0 to 1.0
    success_rate: float  # 0.0 to 1.0
    avg_response_time: float  # seconds
    specializations: Dict[str, float]  # capability -> proficiency


@dataclass
class DelegationDecision:
    """Decision about task delegation"""

    agent_id: str
    confidence: float
    reasoning: str
    alternative_agents: List[str]
    delegation_metadata: Dict[str, Any]


class MetaAgent:
    """Meta-agent for intelligent task delegation and coordination"""

    def __init__(self):
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.delegation_history: List[Dict[str, Any]] = []
        self.performance_matrix = np.zeros((0, 0))
        self.task_queue: List[Dict[str, Any]] = []

    def register_agent(self, profile: AgentProfile):
        """Register an agent with its capabilities"""
        self.agent_profiles[profile.agent_id] = profile
        logger.info(
            f"Registered agent: {profile.agent_id} with capabilities: {profile.capabilities}"
        )

    async def decide_delegation(
        self, task: Dict[str, Any], available_agents: Optional[List[str]] = None
    ) -> DelegationDecision:
        """Decide which agent should handle a task"""

        # Get available agents
        if available_agents is None:
            available_agents = list(self.agent_profiles.keys())

        # Analyze task requirements
        required_capabilities = self._analyze_task_requirements(task)

        # Score each agent
        agent_scores = {}
        for agent_id in available_agents:
            if agent_id not in self.agent_profiles:
                continue

            profile = self.agent_profiles[agent_id]
            score = self._score_agent_for_task(profile, task, required_capabilities)
            agent_scores[agent_id] = score

        # Select best agent
        if not agent_scores:
            raise ValueError("No suitable agents available for task")

        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        alternative_agents = sorted(
            [a for a in agent_scores if a != best_agent[0]],
            key=lambda a: agent_scores[a],
            reverse=True,
        )[:3]

        decision = DelegationDecision(
            agent_id=best_agent[0],
            confidence=best_agent[1],
            reasoning=self._generate_reasoning(best_agent[0], task, required_capabilities),
            alternative_agents=alternative_agents,
            delegation_metadata={
                "task_type": task.get("type"),
                "required_capabilities": [c.value for c in required_capabilities],
                "agent_scores": agent_scores,
            },
        )

        # Record delegation
        self._record_delegation(decision, task)

        return decision

    async def coordinate_multi_agent_task(
        self, complex_task: Dict[str, Any]
    ) -> List[DelegationDecision]:
        """Coordinate multiple agents for a complex task"""

        # Decompose task
        subtasks = self._decompose_task(complex_task)

        # Identify dependencies
        dependency_graph = self._build_dependency_graph(subtasks)

        # Plan execution order
        execution_plan = self._plan_execution(subtasks, dependency_graph)

        # Delegate subtasks
        delegations = []
        for subtask_group in execution_plan:
            group_delegations = []

            for subtask in subtask_group:
                decision = await self.decide_delegation(subtask)
                group_delegations.append(decision)

            delegations.extend(group_delegations)

        return delegations

    def update_agent_performance(self, agent_id: str, task_result: Dict[str, Any]):
        """Update agent performance based on task results"""

        if agent_id not in self.agent_profiles:
            return

        profile = self.agent_profiles[agent_id]

        # Update performance metrics
        success = task_result.get("success", False)
        response_time = task_result.get("response_time", 0)

        # Update success rate (exponential moving average)
        alpha = 0.1  # Learning rate
        profile.success_rate = (1 - alpha) * profile.success_rate + alpha * (1 if success else 0)

        # Update average response time
        profile.avg_response_time = (1 - alpha) * profile.avg_response_time + alpha * response_time

        # Update performance score
        profile.performance_score = self._calculate_performance_score(profile)

        logger.info(
            f"Updated performance for agent {agent_id}: score={profile.performance_score:.2f}"
        )

    def get_agent_recommendations(
        self, capability: AgentCapability, top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """Get top agents for a specific capability"""

        recommendations = []

        for agent_id, profile in self.agent_profiles.items():
            if capability in profile.capabilities:
                score = profile.performance_score * profile.specializations.get(
                    capability.value, 0.5
                )
                recommendations.append((agent_id, score))

        # Sort and return top-k
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:top_k]

    def _analyze_task_requirements(self, task: Dict[str, Any]) -> List[AgentCapability]:
        """Analyze task to determine required capabilities"""

        required = []
        task_type = task.get("type", "").lower()
        task_description = task.get("description", "").lower()

        # Map task types to capabilities
        capability_keywords = {
            AgentCapability.RESEARCH: ["research", "analyze", "investigate", "explore"],
            AgentCapability.CODING: ["code", "implement", "develop", "program"],
            AgentCapability.TESTING: ["test", "verify", "validate", "check"],
            AgentCapability.DOCUMENTATION: ["document", "write", "explain", "describe"],
            AgentCapability.REVIEW: ["review", "evaluate", "assess", "critique"],
            AgentCapability.DEPLOYMENT: ["deploy", "release", "publish", "distribute"],
            AgentCapability.SECURITY: ["secure", "protect", "audit", "vulnerability"],
            AgentCapability.PERFORMANCE: ["optimize", "performance", "speed", "efficiency"],
            AgentCapability.ARCHITECTURE: ["design", "architect", "structure", "pattern"],
        }

        for capability, keywords in capability_keywords.items():
            if any(keyword in task_type or keyword in task_description for keyword in keywords):
                required.append(capability)

        # Default to coding if no specific capability identified
        if not required:
            required.append(AgentCapability.CODING)

        return required

    def _score_agent_for_task(
        self,
        profile: AgentProfile,
        task: Dict[str, Any],
        required_capabilities: List[AgentCapability],
    ) -> float:
        """Score an agent's suitability for a task"""

        score = 0.0

        # Capability match (40% weight)
        capability_match = sum(1 for cap in required_capabilities if cap in profile.capabilities)
        capability_score = capability_match / max(len(required_capabilities), 1)
        score += 0.4 * capability_score

        # Performance score (30% weight)
        score += 0.3 * profile.performance_score

        # Success rate (20% weight)
        score += 0.2 * profile.success_rate

        # Load balancing (10% weight) - prefer less loaded agents
        load_score = 1.0 - profile.current_load
        score += 0.1 * load_score

        # Specialization bonus
        for capability in required_capabilities:
            if capability.value in profile.specializations:
                score += 0.1 * profile.specializations[capability.value]

        return min(score, 1.0)

    def _generate_reasoning(
        self, agent_id: str, task: Dict[str, Any], required_capabilities: List[AgentCapability]
    ) -> str:
        """Generate reasoning for delegation decision"""

        profile = self.agent_profiles[agent_id]

        reasoning_parts = []
        reasoning_parts.append(f"Selected {agent_id} for task '{task.get('type', 'unknown')}'")

        # Capability match
        matched_caps = [cap for cap in required_capabilities if cap in profile.capabilities]
        if matched_caps:
            reasoning_parts.append(
                f"Agent has required capabilities: {', '.join(c.value for c in matched_caps)}"
            )

        # Performance
        reasoning_parts.append(f"Performance score: {profile.performance_score:.2f}")
        reasoning_parts.append(f"Success rate: {profile.success_rate:.2%}")

        # Load
        if profile.current_load < 0.5:
            reasoning_parts.append(f"Agent has low current load: {profile.current_load:.2%}")

        return ". ".join(reasoning_parts)

    def _record_delegation(self, decision: DelegationDecision, task: Dict[str, Any]):
        """Record delegation decision for learning"""

        self.delegation_history.append(
            {
                "timestamp": asyncio.get_event_loop().time(),
                "task": task,
                "decision": decision,
                "agent_id": decision.agent_id,
            }
        )

        # Keep only recent history
        if len(self.delegation_history) > 1000:
            self.delegation_history = self.delegation_history[-1000:]

    def _decompose_task(self, complex_task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose complex task into subtasks"""

        # Simple decomposition based on task structure
        subtasks = []

        if "subtasks" in complex_task:
            return complex_task["subtasks"]

        # Generate subtasks based on task type
        task_type = complex_task.get("type", "")

        if task_type == "full_implementation":
            subtasks = [
                {"type": "research", "description": "Research requirements"},
                {"type": "design", "description": "Design architecture"},
                {"type": "coding", "description": "Implement solution"},
                {"type": "testing", "description": "Test implementation"},
                {"type": "documentation", "description": "Document code"},
            ]
        else:
            # Single task
            subtasks = [complex_task]

        return subtasks

    def _build_dependency_graph(self, subtasks: List[Dict[str, Any]]) -> Dict[int, List[int]]:
        """Build dependency graph for subtasks"""

        # Simple linear dependencies for now
        dependencies = {}

        for i in range(len(subtasks)):
            if i > 0:
                dependencies[i] = [i - 1]  # Each task depends on previous
            else:
                dependencies[i] = []

        return dependencies

    def _plan_execution(
        self, subtasks: List[Dict[str, Any]], dependency_graph: Dict[int, List[int]]
    ) -> List[List[Dict[str, Any]]]:
        """Plan execution order respecting dependencies"""

        # Topological sort
        execution_plan = []
        completed = set()

        while len(completed) < len(subtasks):
            current_batch = []

            for i, subtask in enumerate(subtasks):
                if i not in completed:
                    # Check if dependencies are satisfied
                    deps = dependency_graph.get(i, [])
                    if all(dep in completed for dep in deps):
                        current_batch.append(subtask)
                        completed.add(i)

            if current_batch:
                execution_plan.append(current_batch)
            else:
                # Circular dependency or error
                break

        return execution_plan

    def _calculate_performance_score(self, profile: AgentProfile) -> float:
        """Calculate overall performance score for agent"""

        # Weighted combination of metrics
        score = 0.0
        score += 0.5 * profile.success_rate  # 50% weight on success
        score += 0.3 * (1.0 - min(profile.avg_response_time / 60, 1.0))  # 30% on speed
        score += 0.2 * (1.0 - profile.current_load)  # 20% on availability

        return min(max(score, 0.0), 1.0)
