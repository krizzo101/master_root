#!/usr/bin/env python3
"""
Decision Tree Generator from Knowledge Graph
Converts knowledge patterns into executable decision trees for agent orchestration.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(Enum):
    """Types of nodes in the decision tree."""

    ROOT = "root"
    DECISION = "decision"
    ACTION = "action"
    PARALLEL = "parallel"
    CHECKPOINT = "checkpoint"
    VALIDATION = "validation"
    ERROR_HANDLER = "error_handler"
    TERMINAL = "terminal"


@dataclass
class DecisionNode:
    """Node in the agent decision tree."""

    node_id: str
    node_type: NodeType
    content: str
    knowledge_id: Optional[str] = None
    confidence: float = 1.0
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    children: List["DecisionNode"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionTreeGenerator:
    """Generates decision trees from knowledge graph patterns."""

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.node_counter = 0

    def generate_sdlc_decision_tree(
        self, project_type: str = "general"
    ) -> DecisionNode:
        """Generate complete SDLC decision tree from knowledge base."""

        # Create root node
        root = self._create_node(
            NodeType.ROOT,
            "SDLC Orchestration Decision Tree",
            metadata={"project_type": project_type},
        )

        # Add phase selection
        phase_decision = self._create_node(
            NodeType.DECISION, "Select SDLC Phase", conditions={"current_phase": "?"}
        )
        root.children.append(phase_decision)

        # Generate phase-specific subtrees
        phases = ["discovery", "design", "development", "testing", "deployment"]
        for phase in phases:
            phase_tree = self._generate_phase_tree(phase)
            phase_decision.children.append(phase_tree)

        return root

    def _generate_phase_tree(self, phase: str) -> DecisionNode:
        """Generate decision tree for a specific SDLC phase."""

        # Query knowledge for this phase
        phase_knowledge = self._query_phase_knowledge(phase)

        if not phase_knowledge:
            # Fallback if no specific knowledge
            return self._create_default_phase_tree(phase)

        # Create phase root
        phase_node = self._create_node(
            NodeType.DECISION,
            f"{phase.capitalize()} Phase",
            knowledge_id=phase_knowledge[0].get("id"),
            conditions={"phase": phase},
        )

        # Add resource check
        resource_check = self._create_node(
            NodeType.DECISION,
            "Check Resources",
            conditions={"available_agents": "?", "time_remaining": "?"},
        )
        phase_node.children.append(resource_check)

        # Add parallel execution branch
        if self._supports_parallel(phase_knowledge[0]):
            parallel_branch = self._create_parallel_branch(phase, phase_knowledge[0])
            resource_check.children.append(parallel_branch)

        # Add sequential fallback
        sequential_branch = self._create_sequential_branch(phase, phase_knowledge[0])
        resource_check.children.append(sequential_branch)

        # Add validation
        validation = self._create_validation_node(phase)
        phase_node.children.append(validation)

        return phase_node

    def _create_parallel_branch(self, phase: str, knowledge: Dict) -> DecisionNode:
        """Create parallel execution branch."""
        parallel_node = self._create_node(
            NodeType.PARALLEL,
            f"Parallel {phase} Execution",
            knowledge_id=knowledge.get("id"),
            metadata={"max_parallel": 5},
        )

        # Extract agents from knowledge
        agents = self._extract_agents(knowledge)

        for agent in agents[:5]:  # Max 5 parallel
            agent_node = self._create_node(
                NodeType.ACTION,
                f"Deploy {agent}",
                actions=[
                    f"Create worktree for {agent}",
                    f"Spawn {agent} with 10min timeout",
                    "Monitor progress",
                ],
            )

            # Add checkpoint
            checkpoint = self._create_node(
                NodeType.CHECKPOINT,
                f"Checkpoint {agent}",
                actions=["Save state to checkpoint.json"],
                metadata={"interval": "3 minutes"},
            )
            agent_node.children.append(checkpoint)

            parallel_node.children.append(agent_node)

        return parallel_node

    def _create_sequential_branch(self, phase: str, knowledge: Dict) -> DecisionNode:
        """Create sequential execution branch (fallback)."""
        sequential_node = self._create_node(
            NodeType.DECISION,
            f"Sequential {phase} Execution",
            conditions={"parallel_failed": True},
        )

        agents = self._extract_agents(knowledge)

        current = sequential_node
        for agent in agents:
            agent_node = self._create_node(
                NodeType.ACTION,
                f"Execute {agent}",
                actions=[f"Run {agent} with extended timeout"],
            )
            current.children.append(agent_node)
            current = agent_node

        return sequential_node

    def _create_validation_node(self, phase: str) -> DecisionNode:
        """Create validation node for phase completion."""
        validation = self._create_node(
            NodeType.VALIDATION,
            f"Validate {phase} Outputs",
            actions=[
                "Check required artifacts exist",
                "Validate output quality",
                "Run phase-specific tests",
            ],
        )

        # Success path
        success = self._create_node(
            NodeType.ACTION,
            "Mark Phase Complete",
            actions=["Update state", "Trigger next phase"],
            metadata={"status": "success"},
        )
        validation.children.append(success)

        # Failure path
        failure = self._create_node(
            NodeType.ERROR_HANDLER,
            "Handle Validation Failure",
            actions=[
                "Identify failed validations",
                "Create correction tasks",
                "Retry with corrections",
            ],
        )
        validation.children.append(failure)

        return validation

    def generate_error_recovery_tree(self, error_type: str) -> DecisionNode:
        """Generate error recovery decision tree."""

        # Query for error solutions
        solutions = self._query_error_solutions(error_type)

        root = self._create_node(
            NodeType.ERROR_HANDLER,
            f"Error Recovery: {error_type}",
            conditions={"error_type": error_type},
        )

        # Add error classification
        classify = self._create_node(
            NodeType.DECISION, "Classify Error Severity", conditions={"severity": "?"}
        )
        root.children.append(classify)

        # Critical errors - immediate compensation
        critical = self._create_node(
            NodeType.ACTION,
            "Execute Compensation Workflow",
            conditions={"severity": "critical"},
            actions=["Stop all agents", "Rollback changes", "Alert human operator"],
        )
        classify.children.append(critical)

        # Recoverable errors - retry with checkpoint
        recoverable = self._create_node(
            NodeType.DECISION,
            "Attempt Recovery",
            conditions={"severity": "recoverable"},
        )
        classify.children.append(recoverable)

        # Add checkpoint recovery
        if solutions and any(
            "checkpoint" in s.get("description", "").lower() for s in solutions
        ):
            checkpoint_recovery = self._create_node(
                NodeType.ACTION,
                "Resume from Checkpoint",
                knowledge_id=solutions[0].get("id"),
                actions=[
                    "Read last checkpoint",
                    "Restore state",
                    "Continue from last position",
                ],
            )
            recoverable.children.append(checkpoint_recovery)

        # Add retry logic
        retry = self._create_node(
            NodeType.ACTION,
            "Retry with Backoff",
            actions=["Wait exponentially", "Retry operation", "Monitor for success"],
            metadata={"max_retries": 3},
        )
        recoverable.children.append(retry)

        return root

    def generate_resource_optimization_tree(self) -> DecisionNode:
        """Generate decision tree for resource optimization."""

        root = self._create_node(
            NodeType.DECISION,
            "Resource Optimization",
            conditions={"resource_pressure": "?"},
        )

        # High resource usage
        high_usage = self._create_node(
            NodeType.DECISION,
            "High Resource Usage",
            conditions={"cpu_usage": ">80%", "memory_usage": ">75%"},
        )
        root.children.append(high_usage)

        # Throttle agents
        throttle = self._create_node(
            NodeType.ACTION,
            "Throttle Agent Execution",
            actions=[
                "Reduce parallel agents to 3",
                "Increase checkpoint frequency",
                "Switch to lighter models",
            ],
        )
        high_usage.children.append(throttle)

        # Queue tasks
        queue = self._create_node(
            NodeType.ACTION,
            "Queue Excess Tasks",
            actions=[
                "Move tasks to queue",
                "Process sequentially",
                "Monitor queue depth",
            ],
        )
        high_usage.children.append(queue)

        # Normal usage - optimize
        normal_usage = self._create_node(
            NodeType.DECISION,
            "Normal Resource Usage",
            conditions={"cpu_usage": "<60%", "memory_usage": "<60%"},
        )
        root.children.append(normal_usage)

        # Scale up
        scale_up = self._create_node(
            NodeType.ACTION,
            "Scale Up Execution",
            actions=[
                "Increase parallel agents to 5",
                "Use more powerful models",
                "Reduce checkpoint frequency",
            ],
        )
        normal_usage.children.append(scale_up)

        return root

    def _query_phase_knowledge(self, phase: str) -> List[Dict]:
        """Query knowledge base for phase-specific patterns."""
        query = """
        MATCH (k:Knowledge)
        WHERE k.knowledge_id CONTAINS $phase
           OR k.content CONTAINS $phase
           OR k.tags CONTAINS $phase
        RETURN k.knowledge_id as id,
               k.content as content,
               k.context as context,
               k.confidence_score as confidence
        ORDER BY k.confidence_score DESC
        LIMIT 3
        """

        with self.driver.session() as session:
            result = session.run(query, phase=phase)
            return [self._parse_knowledge(record.data()) for record in result]

    def _query_error_solutions(self, error_type: str) -> List[Dict]:
        """Query for error recovery solutions."""
        query = """
        MATCH (k:Knowledge)
        WHERE k.knowledge_type = 'ERROR_SOLUTION'
          AND (k.content CONTAINS $error_type OR
               k.description CONTAINS $error_type)
        RETURN k.knowledge_id as id,
               k.content as content,
               k.description as description,
               k.context as context
        LIMIT 5
        """

        with self.driver.session() as session:
            result = session.run(query, error_type=error_type)
            return [self._parse_knowledge(record.data()) for record in result]

    def _parse_knowledge(self, knowledge: Dict) -> Dict:
        """Parse knowledge entry, handling JSON context."""
        if "context" in knowledge and isinstance(knowledge["context"], str):
            try:
                knowledge["context"] = json.loads(knowledge["context"])
            except (json.JSONDecodeError, TypeError):
                knowledge["context"] = {}
        return knowledge

    def _supports_parallel(self, knowledge: Dict) -> bool:
        """Check if knowledge pattern supports parallel execution."""
        context = knowledge.get("context", {})
        return (
            context.get("parallel_capable", False)
            or context.get("parallel_agents")
            or "parallel" in knowledge.get("content", "").lower()
        )

    def _extract_agents(self, knowledge: Dict) -> List[str]:
        """Extract agent names from knowledge context."""
        context = knowledge.get("context", {})

        # Check various locations for agent definitions
        if "agents" in context:
            return context["agents"]

        if "agent_types" in context:
            return context["agent_types"]

        # Fallback to generic agents
        return ["analyzer", "builder", "validator", "reporter"]

    def _create_node(
        self,
        node_type: NodeType,
        content: str,
        knowledge_id: Optional[str] = None,
        confidence: float = 1.0,
        conditions: Dict = None,
        actions: List[str] = None,
        metadata: Dict = None,
    ) -> DecisionNode:
        """Create a new decision tree node."""
        self.node_counter += 1
        return DecisionNode(
            node_id=f"node_{self.node_counter}",
            node_type=node_type,
            content=content,
            knowledge_id=knowledge_id,
            confidence=confidence,
            conditions=conditions or {},
            actions=actions or [],
            metadata=metadata or {},
        )

    def _create_default_phase_tree(self, phase: str) -> DecisionNode:
        """Create default phase tree when no specific knowledge exists."""
        return self._create_node(
            NodeType.ACTION,
            f"Execute Default {phase.capitalize()}",
            actions=[
                f"Run standard {phase} workflow",
                "Monitor progress",
                "Validate outputs",
            ],
            confidence=0.7,
        )

    def export_tree_as_mermaid(self, root: DecisionNode) -> str:
        """Export decision tree as Mermaid diagram."""
        lines = ["graph TD"]
        self._add_mermaid_nodes(root, lines)
        return "\n".join(lines)

    def _add_mermaid_nodes(
        self, node: DecisionNode, lines: List[str], parent_id: str = None
    ):
        """Recursively add nodes to Mermaid diagram."""
        # Node shape based on type
        shapes = {
            NodeType.ROOT: ("(", ")"),
            NodeType.DECISION: ("{", "}"),
            NodeType.ACTION: ("[", "]"),
            NodeType.PARALLEL: ("[[", "]]"),
            NodeType.CHECKPOINT: ("[(", ")]"),
            NodeType.VALIDATION: ("[", "]"),
            NodeType.ERROR_HANDLER: ("{{", "}}"),
            NodeType.TERMINAL: ("((", "))"),
        }

        start, end = shapes.get(node.node_type, ("[", "]"))
        lines.append(f"    {node.node_id}{start}{node.content}{end}")

        if parent_id:
            lines.append(f"    {parent_id} --> {node.node_id}")

        for child in node.children:
            self._add_mermaid_nodes(child, lines, node.node_id)


# Example usage
if __name__ == "__main__":
    print("Decision Tree Generator Example")
    print("=" * 50)

    # Example tree structure
    generator = DecisionTreeGenerator(None)  # Would pass neo4j driver

    # Create simple example tree
    root = generator._create_node(NodeType.ROOT, "Agent Orchestration")

    phase = generator._create_node(NodeType.DECISION, "Select Phase")
    root.children.append(phase)

    discovery = generator._create_node(NodeType.PARALLEL, "Discovery Phase")
    phase.children.append(discovery)

    for agent in ["Requirements", "Research", "Analysis"]:
        agent_node = generator._create_node(NodeType.ACTION, f"{agent} Agent")
        discovery.children.append(agent_node)

    # Export as Mermaid
    mermaid = generator.export_tree_as_mermaid(root)
    print("\nMermaid Diagram:")
    print(mermaid)
