"""
Dynamic Agent Selector - Intelligently selects optimal agents for each task
Uses LLM to determine which specialized agents are needed
"""

import json
import asyncio
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Available specialized agents from MCP servers"""
    
    # Core Development Agents
    REQUIREMENTS_ANALYST = "requirements-analyst"
    SOLUTION_ARCHITECT = "solution-architect" 
    DEVELOPMENT_SPECIALIST = "development-specialist"
    CODE_ANALYZER = "code-analyzer"
    REFACTORING_MASTER = "refactoring-master"
    
    # Quality Assurance Agents
    REVIEWER_CRITIC = "reviewer-critic"
    QA_TESTING_GURU = "qa-testing-guru"
    
    # Specialized Agents
    TECHNICAL_WRITER = "technical-writer"
    RESEARCH_GENIUS = "research-genius"
    CEO_TEAM_MANAGER = "ceo-team-manager"
    BUSINESS_ANALYST = "business-analyst"
    PROMPT_GENERATOR = "prompt-generator"
    
    # Infrastructure Agents
    EXCELLENCE_OPTIMIZER = "excellence-optimizer"
    TEST_REMEDIATION_SPECIALIST = "test-remediation-specialist"
    
    # External Intelligence
    CLAUDE_CODE = "claude-code"
    GEMINI_AGENT = "gemini-agent"
    THINKING_AGENT = "thinking"


@dataclass
class AgentCapability:
    """Defines what an agent can do"""
    agent_type: AgentType
    strengths: List[str]
    best_for: List[str]
    limitations: List[str]
    cost: float  # Relative cost (0-1)
    speed: float  # Relative speed (0-1)
    quality: float  # Output quality (0-1)


class DynamicAgentSelector:
    """
    Intelligently selects the optimal agents for a given task
    Uses LLM to make decisions, not hardcoded rules
    """
    
    def __init__(self):
        self.agent_registry = self._initialize_agent_registry()
        self.selection_history = []
        self.performance_metrics = {}
        
    async def select_optimal_agents(self, understanding: 'Understanding') -> List[AgentType]:
        """
        Select the optimal set of agents based on deep understanding
        """
        # Build selection prompt
        selection_prompt = self._build_selection_prompt(understanding)
        
        # Get LLM recommendation
        llm_recommendation = await self._get_llm_recommendation(selection_prompt)
        
        # Validate and optimize selection
        selected_agents = self._validate_selection(llm_recommendation)
        
        # Apply learned optimizations
        selected_agents = self._apply_performance_optimizations(selected_agents, understanding)
        
        # Record selection for learning
        self._record_selection(understanding, selected_agents)
        
        return selected_agents
    
    def _build_selection_prompt(self, understanding: 'Understanding') -> str:
        """Build prompt for LLM agent selection"""
        return f"""
        Select the optimal agents for this software development task:
        
        PROJECT UNDERSTANDING:
        - Core Purpose: {understanding.core_purpose}
        - Complexity: {understanding.complexity_level}
        - Users: {', '.join(understanding.target_users)}
        - Technical Requirements: {', '.join(understanding.technical_requirements[:5])}
        - Key Challenges: {', '.join(understanding.key_challenges[:5])}
        - Architecture Patterns: {', '.join(understanding.architectural_patterns)}
        
        AVAILABLE AGENTS:
        {self._format_agent_capabilities()}
        
        SELECTION CRITERIA:
        1. Coverage - Selected agents must cover all requirements
        2. Efficiency - Minimize redundancy, maximize parallel execution
        3. Quality - Choose agents with highest quality for critical tasks
        4. Cost - Balance quality with resource usage
        5. Speed - Optimize for fastest delivery
        
        CONSIDER:
        - Which agents are ESSENTIAL for this project?
        - Which agents would ADD VALUE beyond basics?
        - Which agents can work in PARALLEL?
        - What's the optimal SEQUENCE of agent execution?
        
        Return a JSON object with:
        {{
            "essential_agents": ["agent1", "agent2", ...],
            "value_add_agents": ["agent3", "agent4", ...],
            "parallel_groups": [
                ["agent1", "agent2"],  // Can run together
                ["agent3", "agent4"]   // Can run together
            ],
            "sequence": ["group1", "group2", ...],
            "reasoning": "Explanation of selection"
        }}
        """
    
    def _format_agent_capabilities(self) -> str:
        """Format agent capabilities for prompt"""
        capabilities = []
        for agent_type, capability in self.agent_registry.items():
            capabilities.append(f"""
        {agent_type.value}:
        - Strengths: {', '.join(capability.strengths)}
        - Best for: {', '.join(capability.best_for)}
        - Quality: {capability.quality:.1f}/1.0
        - Speed: {capability.speed:.1f}/1.0
            """)
        return '\n'.join(capabilities)
    
    async def _get_llm_recommendation(self, prompt: str) -> Dict:
        """Get agent selection recommendation from LLM"""
        # TODO: Implement actual LLM API call
        # This would call Claude/GPT-4/Gemini
        
        # Mock response for now
        return {
            "essential_agents": [
                "requirements-analyst",
                "solution-architect",
                "development-specialist",
                "qa-testing-guru"
            ],
            "value_add_agents": [
                "reviewer-critic",
                "technical-writer",
                "excellence-optimizer"
            ],
            "parallel_groups": [
                ["requirements-analyst", "research-genius"],
                ["solution-architect", "business-analyst"],
                ["development-specialist", "code-analyzer"],
                ["qa-testing-guru", "reviewer-critic"]
            ],
            "sequence": ["group1", "group2", "group3", "group4"],
            "reasoning": "Selected based on project complexity and requirements"
        }
    
    def _validate_selection(self, recommendation: Dict) -> List[AgentType]:
        """Validate and clean up LLM recommendation"""
        selected = []
        
        # Combine essential and value-add agents
        all_agents = recommendation.get("essential_agents", []) + \
                    recommendation.get("value_add_agents", [])
        
        # Convert to AgentType enums
        for agent_name in all_agents:
            try:
                agent_type = self._find_agent_type(agent_name)
                if agent_type and agent_type not in selected:
                    selected.append(agent_type)
            except ValueError:
                logger.warning(f"Unknown agent type: {agent_name}")
        
        # Ensure minimum viable set
        if not selected:
            selected = self._get_default_agents()
        
        return selected
    
    def _find_agent_type(self, agent_name: str) -> Optional[AgentType]:
        """Find AgentType by name"""
        agent_name = agent_name.lower().replace('_', '-')
        for agent_type in AgentType:
            if agent_type.value == agent_name:
                return agent_type
        return None
    
    def _apply_performance_optimizations(self, 
                                        agents: List[AgentType], 
                                        understanding: 'Understanding') -> List[AgentType]:
        """Apply learned performance optimizations"""
        
        # Check historical performance for similar projects
        similar_selections = self._find_similar_selections(understanding)
        
        for past_selection in similar_selections:
            if past_selection.get("success_rate", 0) > 0.9:
                # Add successful agents not already selected
                for agent in past_selection.get("agents", []):
                    agent_type = self._find_agent_type(agent)
                    if agent_type and agent_type not in agents:
                        agents.append(agent_type)
                        logger.info(f"Adding {agent_type.value} based on past success")
        
        # Remove underperforming agents
        for agent in agents[:]:
            performance = self.performance_metrics.get(agent, {})
            if performance.get("failure_rate", 0) > 0.3:
                logger.info(f"Removing {agent.value} due to poor performance")
                agents.remove(agent)
        
        return agents
    
    def _find_similar_selections(self, understanding: 'Understanding') -> List[Dict]:
        """Find similar past selections"""
        similar = []
        
        for selection in self.selection_history:
            similarity = self._calculate_similarity(
                understanding, 
                selection.get("understanding", {})
            )
            if similarity > 0.7:
                similar.append(selection)
        
        return sorted(similar, 
                     key=lambda x: x.get("success_rate", 0), 
                     reverse=True)[:3]
    
    def _calculate_similarity(self, u1: 'Understanding', u2: Dict) -> float:
        """Calculate similarity between two understandings"""
        # Simple similarity based on complexity and patterns
        score = 0.0
        
        if u1.complexity_level == u2.get("complexity_level"):
            score += 0.3
        
        patterns1 = set(u1.architectural_patterns)
        patterns2 = set(u2.get("architectural_patterns", []))
        if patterns1 and patterns2:
            overlap = len(patterns1.intersection(patterns2))
            score += 0.7 * (overlap / max(len(patterns1), len(patterns2)))
        
        return score
    
    def _record_selection(self, understanding: 'Understanding', agents: List[AgentType]):
        """Record selection for future learning"""
        self.selection_history.append({
            "understanding": {
                "complexity_level": understanding.complexity_level,
                "architectural_patterns": understanding.architectural_patterns,
                "key_challenges": understanding.key_challenges
            },
            "agents": [agent.value for agent in agents],
            "timestamp": datetime.now().isoformat()
        })
    
    def _get_default_agents(self) -> List[AgentType]:
        """Get default minimum viable agent set"""
        return [
            AgentType.REQUIREMENTS_ANALYST,
            AgentType.DEVELOPMENT_SPECIALIST,
            AgentType.QA_TESTING_GURU
        ]
    
    def _initialize_agent_registry(self) -> Dict[AgentType, AgentCapability]:
        """Initialize agent capability registry"""
        return {
            AgentType.REQUIREMENTS_ANALYST: AgentCapability(
                agent_type=AgentType.REQUIREMENTS_ANALYST,
                strengths=["requirement extraction", "stakeholder analysis", "gap analysis"],
                best_for=["complex requirements", "ambiguous requests", "enterprise projects"],
                limitations=["implementation details"],
                cost=0.3,
                speed=0.8,
                quality=0.9
            ),
            AgentType.SOLUTION_ARCHITECT: AgentCapability(
                agent_type=AgentType.SOLUTION_ARCHITECT,
                strengths=["system design", "architecture patterns", "scalability"],
                best_for=["complex systems", "microservices", "distributed systems"],
                limitations=["detailed coding"],
                cost=0.4,
                speed=0.7,
                quality=0.95
            ),
            AgentType.DEVELOPMENT_SPECIALIST: AgentCapability(
                agent_type=AgentType.DEVELOPMENT_SPECIALIST,
                strengths=["code implementation", "best practices", "optimization"],
                best_for=["core development", "algorithm implementation", "performance"],
                limitations=["high-level design"],
                cost=0.5,
                speed=0.6,
                quality=0.9
            ),
            AgentType.QA_TESTING_GURU: AgentCapability(
                agent_type=AgentType.QA_TESTING_GURU,
                strengths=["test strategy", "test automation", "quality assurance"],
                best_for=["comprehensive testing", "test coverage", "bug prevention"],
                limitations=["implementation"],
                cost=0.4,
                speed=0.7,
                quality=0.92
            ),
            AgentType.REVIEWER_CRITIC: AgentCapability(
                agent_type=AgentType.REVIEWER_CRITIC,
                strengths=["code review", "quality assessment", "improvement suggestions"],
                best_for=["code quality", "best practices", "refactoring"],
                limitations=["initial development"],
                cost=0.3,
                speed=0.8,
                quality=0.88
            ),
            AgentType.EXCELLENCE_OPTIMIZER: AgentCapability(
                agent_type=AgentType.EXCELLENCE_OPTIMIZER,
                strengths=["optimization", "performance", "innovation"],
                best_for=["performance critical", "innovation", "cutting-edge"],
                limitations=["basic tasks"],
                cost=0.6,
                speed=0.5,
                quality=0.98
            ),
            AgentType.TECHNICAL_WRITER: AgentCapability(
                agent_type=AgentType.TECHNICAL_WRITER,
                strengths=["documentation", "clarity", "user guides"],
                best_for=["documentation", "API docs", "tutorials"],
                limitations=["code implementation"],
                cost=0.3,
                speed=0.8,
                quality=0.85
            ),
            AgentType.RESEARCH_GENIUS: AgentCapability(
                agent_type=AgentType.RESEARCH_GENIUS,
                strengths=["research", "analysis", "insights"],
                best_for=["technology research", "best practices", "trends"],
                limitations=["implementation"],
                cost=0.4,
                speed=0.6,
                quality=0.9
            )
        }
    
    async def create_execution_plan(self, 
                                   agents: List[AgentType], 
                                   understanding: 'Understanding') -> List[List[AgentType]]:
        """
        Create optimal execution plan with parallel groups
        """
        execution_prompt = f"""
        Create an execution plan for these agents: {[a.value for a in agents]}
        
        Project complexity: {understanding.complexity_level}
        Key challenges: {understanding.key_challenges}
        
        Determine:
        1. Which agents can run in parallel (no dependencies)?
        2. What's the optimal execution order?
        3. How to maximize parallelization?
        
        Return parallel execution groups in order.
        """
        
        plan = await self._call_llm(execution_prompt)
        
        # Convert to AgentType groups
        execution_groups = []
        for group in plan.get("groups", []):
            agent_group = []
            for agent_name in group:
                agent_type = self._find_agent_type(agent_name)
                if agent_type:
                    agent_group.append(agent_type)
            if agent_group:
                execution_groups.append(agent_group)
        
        return execution_groups if execution_groups else [[agent] for agent in agents]
    
    async def _call_llm(self, prompt: str) -> Dict:
        """Call LLM for execution planning"""
        # TODO: Implement actual LLM call
        return {
            "groups": [
                ["requirements-analyst", "research-genius"],
                ["solution-architect"],
                ["development-specialist", "code-analyzer"],
                ["qa-testing-guru", "reviewer-critic"],
                ["technical-writer"]
            ]
        }


from datetime import datetime