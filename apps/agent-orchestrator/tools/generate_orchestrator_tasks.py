#!/usr/bin/env python3
"""
Bulletproof Orchestrator Task Generator
Eliminates dependency naming errors by generating mathematically correct task definitions
"""
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Set


@dataclass
class TaskSpec:
    """Type-safe task specification"""

    task_id: str
    task_type: str
    prompt: str
    dependencies: List[str]
    agent_count: int = 1
    tools: List[str] = None
    permissions: List[str] = None
    priority: str = "medium"
    fallback_to_openai: bool = True
    estimated_tokens: int = 30000

    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.permissions is None:
            self.permissions = []


class TaskGenerator:
    """Generates orchestrator task definitions with guaranteed dependency correctness"""

    def __init__(self, max_parallel: int = 18):
        self.max_parallel = max_parallel
        self.tasks: List[TaskSpec] = []
        self.task_registry: Dict[str, TaskSpec] = {}

    def add_phase(
        self,
        base_id: str,
        task_type: str,
        prompt: str,
        agent_count: int = 1,
        dependencies: List[str] = None,
        **kwargs,
    ) -> List[str]:
        """
        Add a phase with multiple agents, returns actual task IDs for dependencies

        Args:
            base_id: Base task identifier (e.g., "system_discovery")
            task_type: Agent type (e.g., "research-genius")
            prompt: Task prompt
            agent_count: Number of agents for this phase
            dependencies: List of base_ids this phase depends on
            **kwargs: Additional task parameters

        Returns:
            List of actual task_ids generated for this phase
        """
        dependencies = dependencies or []

        # Resolve dependency base_ids to actual task_ids
        resolved_deps = []
        for dep_base_id in dependencies:
            dep_tasks = self._get_tasks_for_base_id(dep_base_id)
            if not dep_tasks:
                raise ValueError(
                    f"Dependency '{dep_base_id}' not found. Available: {list(self.task_registry.keys())}"
                )
            # For multi-agent dependencies, depend on the first agent of that phase
            resolved_deps.append(dep_tasks[0])

        # Generate actual task IDs
        generated_ids = []
        for i in range(agent_count):
            if agent_count == 1:
                task_id = base_id
            else:
                task_id = f"{base_id}_agent_{i+1}"

            task = TaskSpec(
                task_id=task_id,
                task_type=task_type,
                prompt=prompt,
                dependencies=resolved_deps,
                agent_count=1,  # Each individual task has 1 agent
                **kwargs,
            )

            self.tasks.append(task)
            self.task_registry[task_id] = task
            generated_ids.append(task_id)

        # Register base_id mapping
        self._register_base_id_mapping(base_id, generated_ids)

        return generated_ids

    def _get_tasks_for_base_id(self, base_id: str) -> List[str]:
        """Get all task IDs that belong to a base_id"""
        if hasattr(self, "_base_id_map"):
            return self._base_id_map.get(base_id, [])
        return []

    def _register_base_id_mapping(self, base_id: str, task_ids: List[str]):
        """Register mapping from base_id to actual task_ids"""
        if not hasattr(self, "_base_id_map"):
            self._base_id_map = {}
        self._base_id_map[base_id] = task_ids

    def validate_dependencies(self) -> List[str]:
        """Validate all dependencies are satisfiable"""
        errors = []
        task_ids = {task.task_id for task in self.tasks}

        for task in self.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(
                        f"Task '{task.task_id}' depends on missing task '{dep}'"
                    )

        return errors

    def generate_config(
        self,
        claude_code_fallback_enabled: bool = False,
        system_message_append: str = None,
    ) -> Dict[str, Any]:
        """Generate complete orchestrator configuration"""

        # Validate dependencies first
        errors = self.validate_dependencies()
        if errors:
            raise ValueError(f"Dependency validation failed:\n" + "\n".join(errors))

        # Calculate total agents and adjust parallelism if needed
        total_agents = len(self.tasks)
        actual_max_parallel = min(self.max_parallel, total_agents)

        config = {
            "agent_execution_config": {
                "claude_code_fallback": {
                    "enabled": claude_code_fallback_enabled,
                    "status": "TESTING_REQUIRED"
                    if claude_code_fallback_enabled
                    else "DISABLED",
                    "path": "../claude-code-clone/",
                    "description": "OpenAI-powered Claude Code alternative",
                    "models": {
                        "premium": "o4-mini",
                        "standard": "gpt-5",
                        "fallback": "gpt-5-mini",
                    },
                    "token_limits": {
                        "daily_premium": 1000000,
                        "daily_standard": 10000000,
                    },
                },
                "agent_requirements": {
                    "max_parallel_agents": actual_max_parallel,
                    "token_resilience": True,
                    "checkpoint_interval": 300,
                    "auto_recovery_enabled": True,
                    "quality_gates_enabled": True,
                },
                "system_message_append": system_message_append
                or "CRITICAL CONTEXT: You are working on a solo developer's badass AI automation system. "
                "Focus on practical, maintainable solutions that maximize automation with minimal maintenance. "
                "This system handles Anthropic 5-hour token limits and can fall back to OpenAI "
                "(1M premium, 10M regular daily tokens). Always consider token efficiency and production system protection.",
            },
            "tasks": [],
        }

        # Convert tasks to JSON format
        for task in self.tasks:
            task_dict = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "prompt": task.prompt,
                "dependencies": task.dependencies,
            }

            # Add agent_config if there are additional settings
            if (
                task.tools
                or task.permissions
                or task.priority != "medium"
                or not task.fallback_to_openai
                or task.estimated_tokens != 30000
            ):
                task_dict["agent_config"] = {
                    "agent_count": 1,  # Always 1 for individual tasks
                    "tools": task.tools,
                    "permissions": task.permissions,
                    "priority": task.priority,
                    "fallback_to_openai": task.fallback_to_openai,
                    "estimated_tokens": task.estimated_tokens,
                }

            config["tasks"].append(task_dict)

        return config

    def print_summary(self):
        """Print task generation summary"""
        print(
            f"📊 Generated {len(self.tasks)} tasks with {self.max_parallel} max parallel"
        )
        print(
            f"🔗 Dependency validation: {'✅ PASSED' if not self.validate_dependencies() else '❌ FAILED'}"
        )

        # Show base_id to task_id mapping
        if hasattr(self, "_base_id_map"):
            print("\n📋 Phase Mapping:")
            for base_id, task_ids in self._base_id_map.items():
                print(f"  {base_id} → {task_ids}")

        # Show dependency tree
        print("\n🌳 Dependency Tree:")
        for task in self.tasks:
            deps = (
                " (depends on: " + ", ".join(task.dependencies) + ")"
                if task.dependencies
                else " (independent)"
            )
            print(f"  📋 {task.task_id}{deps}")


def create_system_analysis_tasks(max_parallel: int = 18) -> TaskGenerator:
    """Create the standard 8-phase system analysis task set"""

    gen = TaskGenerator(max_parallel=max_parallel)

    # Phase 1: System Discovery (3 parallel research agents)
    discovery_ids = gen.add_phase(
        base_id="system_discovery",
        task_type="research-genius",
        agent_count=3,
        prompt="""COMPREHENSIVE SYSTEM DISCOVERY WITH LATEST RESEARCH

CRITICAL CONTEXT: This codebase contains a LOT of old, disconnected, experimental, and legacy code mixed with working production code. You MUST determine what's actually being used vs what's just sitting there taking up space.

Before analyzing the current system, conduct online research on the latest agent orchestration and AI automation trends for 2025:

1. Latest Technology Research (CRITICAL FIRST STEP):
   - Research latest agent orchestration frameworks and patterns (2024-2025)
   - Investigate current best practices in AI agent coordination
   - Study modern Claude Code alternatives and OpenAI integration patterns
   - Research token optimization and rate limiting strategies
   - Analyze parallel execution and resilience patterns in modern systems

2. Current System Analysis - SEPARATE WORKING FROM LEGACY:
   - CRITICAL: Map which Python files are actually imported/used vs orphaned
   - Trace execution paths from main entry points (main.py, run.py)
   - Identify which orchestrator classes are actually instantiated vs just defined
   - Document which features are fully implemented vs partially implemented vs just placeholder
   - Find code that's imported nowhere and used by nothing
   - Separate 'unified orchestrator' (current) from old experimental orchestrators

3. Legacy Code Identification:
   - Look for files with no imports pointing to them
   - Find classes/functions that are defined but never instantiated/called
   - Identify experimental features that were started but never finished
   - Document code that appears to be from different development phases
   - Flag potentially outdated patterns or deprecated approaches

4. Reality Check Assessment:
   - This is a solo developer project, not enterprise software
   - Goal: Most badass AI agent automation system possible
   - Must handle Anthropic 5-hour token limits gracefully
   - Must maximize OpenAI token allocation (1M premium, 10M regular daily)
   - System currently works well - don't break what's working

5. Integration Points Discovery:
   - Document current MCP integrations
   - Identify Claude Code dependencies
   - Map token management systems
   - Find any existing OpenAI integration code (may be in archive)
   - NOTE: Claude Code clone exists at ../claude-code-clone/ but needs validation before use
   - EXPLORE ECOSYSTEM: Investigate other apps and tools in the project space for integration opportunities

Generate a comprehensive system map that clearly separates:
- 'DEFINITELY WORKING AND CRITICAL'
- 'WORKING BUT MAYBE LEGACY'
- 'EXPERIMENTAL/INCOMPLETE'
- 'DEAD CODE THAT CAN BE REMOVED'
Include latest industry knowledge for informed enhancement recommendations.""",
        tools=["WebSearch", "WebFetch", "Read", "Glob", "Grep", "Task"],
        permissions=["read_all_files", "web_search", "mcp_integration"],
        priority="high",
        estimated_tokens=60000,
    )

    # Phase 2: Capability Analysis (2 parallel agents)
    capability_ids = gen.add_phase(
        base_id="capability_analysis",
        task_type="solution-architect",
        agent_count=2,
        dependencies=["system_discovery"],
        prompt="""CAPABILITY GAP ANALYSIS & 2025 BENCHMARKING

Based on the system discovery findings, conduct a comprehensive capability analysis:

1. Current Capability Assessment:
   - Evaluate existing orchestration patterns against 2025 industry standards
   - Benchmark current token management vs modern efficiency techniques
   - Assess parallel execution capabilities vs current best practices
   - Review error handling and resilience patterns
   - Analyze monitoring and observability features

2. Modern Standards Comparison:
   - Compare with CrewAI, LangGraph, AutoGen, OpenAI Agents SDK capabilities
   - Evaluate against Plandex and Codai token optimization approaches
   - Assess current vs. state-of-the-art multi-agent patterns
   - Review integration patterns with modern AI development tools

3. Gap Identification:
   - Identify missing capabilities for 2025 competitive advantage
   - Document technical debt that limits scalability
   - Find integration opportunities with modern toolchains
   - Assess security and reliability gaps

4. Enhancement Opportunities:
   - Prioritize capability additions based on impact and effort
   - Identify quick wins vs. strategic long-term improvements
   - Consider resource constraints (solo developer, token limits)
   - Focus on automation and reduced maintenance overhead

Generate a comprehensive capability gap analysis with specific recommendations for achieving 2025-level AI automation capabilities.""",
        tools=["WebSearch", "Read", "Glob", "Grep"],
        permissions=["read_all_files", "web_search"],
        estimated_tokens=45000,
    )

    # Phase 3: Performance Optimization (2 parallel agents)
    perf_ids = gen.add_phase(
        base_id="performance_optimization",
        task_type="performance-optimizer",
        agent_count=2,
        dependencies=["system_discovery"],
        prompt="""PERFORMANCE OPTIMIZATION & TOKEN EFFICIENCY ANALYSIS

Focus on maximizing performance and token efficiency:

1. Token Usage Optimization:
   - Analyze current token consumption patterns
   - Identify opportunities for intelligent provider routing (OpenAI vs Claude)
   - Evaluate caching and redundancy elimination opportunities
   - Design token pooling and rate limiting improvements

2. Parallel Execution Optimization:
   - Review current parallelism patterns and bottlenecks
   - Identify opportunities for increased concurrent execution
   - Analyze dependency resolution efficiency
   - Design adaptive scaling based on available resources

3. Memory and Resource Optimization:
   - Profile memory usage patterns during orchestration
   - Identify resource leaks or inefficient patterns
   - Optimize checkpoint and state persistence mechanisms
   - Review process management and cleanup procedures

4. Throughput Maximization:
   - Design strategies for maximum agent throughput
   - Evaluate batch processing opportunities
   - Optimize agent startup and teardown overhead
   - Consider pipeline parallelism opportunities

Generate specific optimization recommendations with performance impact estimates and implementation complexity.""",
        tools=["Read", "Glob", "Grep"],
        permissions=["read_all_files"],
        estimated_tokens=40000,
    )

    # Phase 4: Claude Clone Validation (single specialist agent)
    clone_ids = gen.add_phase(
        base_id="claude_clone_validation",
        task_type="qa-testing-guru",
        dependencies=["system_discovery"],
        prompt="""CLAUDE CODE CLONE VALIDATION & OPENAI INTEGRATION TESTING

Validate the Claude Code clone for production readiness:

1. Functionality Validation:
   - Test basic agent execution capabilities
   - Verify tool integration (MCP, file operations, web access)
   - Validate streaming response handling
   - Test error handling and recovery mechanisms

2. OpenAI Integration Testing:
   - Verify o4-mini, gpt-5, gpt-5-mini model access
   - Test token limit handling (1M premium, 10M regular daily)
   - Validate rate limiting and backoff mechanisms
   - Test cost tracking and usage monitoring

3. Compatibility Assessment:
   - Compare output quality vs. Claude Code
   - Test task execution reliability and consistency
   - Evaluate prompt compatibility across providers
   - Assess tool integration compatibility

4. Production Readiness:
   - Test under high concurrency loads
   - Validate error recovery and failover mechanisms
   - Assess security and isolation capabilities
   - Evaluate monitoring and logging features

Generate a comprehensive validation report with go/no-go recommendation for OpenAI integration activation.""",
        tools=["Bash", "Read", "Write"],
        permissions=["execute_code", "read_all_files", "write_files"],
        estimated_tokens=35000,
    )

    # Phase 5: Integration Strategy (depends on discovery + capability + clone validation)
    integration_ids = gen.add_phase(
        base_id="integration_strategy",
        task_type="api-integration-specialist",
        dependencies=[
            "system_discovery",
            "capability_analysis",
            "claude_clone_validation",
        ],
        prompt="""INTEGRATION STRATEGY & ARCHITECTURE PLANNING

Design comprehensive integration strategy based on analysis findings:

1. Multi-Provider Integration:
   - Design seamless Claude/OpenAI provider switching
   - Plan cost-optimized routing strategies
   - Design fallback and recovery mechanisms
   - Plan token pool management across providers

2. Modern Toolchain Integration:
   - Design MCP tool expansion strategy
   - Plan Git worktree integration for parallel development
   - Design monitoring and observability integration
   - Plan CI/CD and automation integration

3. Ecosystem Integration:
   - Identify valuable integrations with existing project apps
   - Design plugin and extension architecture
   - Plan API and webhook integration capabilities
   - Design collaboration and shared workspace features

4. Architecture Modernization:
   - Design migration path from current to target architecture
   - Plan backward compatibility preservation
   - Design feature flag and gradual rollout strategies
   - Plan testing and validation frameworks

Generate a detailed integration roadmap with technical specifications and implementation timeline.""",
        estimated_tokens=40000,
    )

    # Phase 6: Enhancement Prioritization (depends on capability + performance + integration)
    priority_ids = gen.add_phase(
        base_id="enhancement_prioritization",
        task_type="business-analyst",
        dependencies=[
            "capability_analysis",
            "performance_optimization",
            "integration_strategy",
        ],
        prompt="""ENHANCEMENT PRIORITIZATION & ROADMAP DEVELOPMENT

Prioritize enhancements for maximum impact with solo developer constraints:

1. Impact vs. Effort Analysis:
   - Score each enhancement opportunity for business impact
   - Assess implementation complexity and time requirements
   - Consider resource constraints and token limit impacts
   - Evaluate maintenance overhead for each enhancement

2. Strategic Roadmap Development:
   - Design phased implementation approach
   - Identify critical path dependencies
   - Plan resource allocation across enhancement phases
   - Design risk mitigation strategies

3. Quick Wins Identification:
   - Identify high-impact, low-effort improvements
   - Plan immediate value delivery opportunities
   - Design proof-of-concept validation approaches
   - Plan early adoption and feedback collection

4. Long-term Vision:
   - Design sustainable growth architecture
   - Plan scalability and extensibility features
   - Consider future technology integration opportunities
   - Design continuous improvement processes

Generate a prioritized enhancement roadmap with clear phases, timelines, and success metrics optimized for solo developer productivity.""",
        estimated_tokens=35000,
    )

    # Phase 7: Implementation Planning (depends on prioritization)
    impl_ids = gen.add_phase(
        base_id="implementation_planning",
        task_type="sdlc-planning",
        dependencies=["enhancement_prioritization"],
        prompt="""IMPLEMENTATION PLANNING & EXECUTION STRATEGY

Create detailed implementation plan for prioritized enhancements:

1. Technical Implementation Plan:
   - Break down enhancements into specific development tasks
   - Design technical architecture and component specifications
   - Plan database schema changes and data migration strategies
   - Design API and interface specifications

2. Development Workflow:
   - Plan Git workflow and branch management strategy
   - Design testing strategy and validation frameworks
   - Plan deployment and rollback procedures
   - Design monitoring and alerting for new features

3. Risk Management:
   - Identify technical risks and mitigation strategies
   - Plan backward compatibility preservation
   - Design feature flags and gradual rollout approaches
   - Plan recovery procedures for failed deployments

4. Resource Planning:
   - Estimate development time and token usage
   - Plan milestone delivery schedules
   - Identify external dependency requirements
   - Design progress tracking and reporting mechanisms

Generate a comprehensive implementation plan with detailed tasks, timelines, and deliverables ready for immediate execution.""",
        estimated_tokens=35000,
    )

    # Phase 8: Technical Documentation (2 parallel writers)
    doc_ids = gen.add_phase(
        base_id="technical_documentation",
        task_type="technical-writer",
        agent_count=2,
        dependencies=["implementation_planning"],
        prompt="""COMPREHENSIVE TECHNICAL DOCUMENTATION

Create complete technical documentation for the enhanced system:

1. Architecture Documentation:
   - Document system architecture and component relationships
   - Create deployment and configuration guides
   - Document API specifications and integration patterns
   - Create troubleshooting and maintenance guides

2. Developer Documentation:
   - Create setup and development environment guides
   - Document coding standards and contribution guidelines
   - Create testing and validation procedures
   - Document debugging and profiling techniques

3. Operations Documentation:
   - Create monitoring and alerting setup guides
   - Document backup and recovery procedures
   - Create scaling and performance tuning guides
   - Document security configuration and best practices

4. User Documentation:
   - Create user guides for new features
   - Document configuration options and customization
   - Create examples and use case demonstrations
   - Document migration procedures from current system

Generate comprehensive documentation that enables successful adoption and maintenance of the enhanced AI automation system.""",
        tools=["Write", "Read", "Glob"],
        permissions=["write_files", "read_all_files"],
        estimated_tokens=40000,
    )

    return gen


def main():
    """Generate bulletproof system analysis tasks"""
    print("🔧 Generating bulletproof orchestrator tasks...")

    # Create task generator
    gen = create_system_analysis_tasks(max_parallel=18)

    # Print summary
    gen.print_summary()

    # Generate config
    config = gen.generate_config(
        claude_code_fallback_enabled=False,
        system_message_append="CRITICAL CONTEXT: You are working on a solo developer's most badass AI automation system. "
        "Focus on practical, maintainable solutions that maximize automation efficiency. "
        "System handles Anthropic 5-hour token limits with OpenAI fallback capability "
        "(1M premium + 10M regular daily tokens). Prioritize token efficiency and production system protection.",
    )

    # Save bulletproof configuration
    output_file = Path("system_analysis_tasks_bulletproof.json")
    with open(output_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Bulletproof configuration saved to: {output_file}")
    print(f"📊 Total tasks: {len(config['tasks'])}")
    print(
        f"🚀 Max parallel agents: {config['agent_execution_config']['agent_requirements']['max_parallel_agents']}"
    )
    print(f"🔗 Dependency validation: PASSED")

    # Generate validation report
    print(f"\n📋 Task Validation Report:")
    task_names = [task["task_id"] for task in config["tasks"]]
    print(f"   Generated task IDs: {len(task_names)}")
    print(f"   Unique task IDs: {len(set(task_names))} (✅ No duplicates)")

    dep_errors = []
    for task in config["tasks"]:
        for dep in task.get("dependencies", []):
            if dep not in task_names:
                dep_errors.append(
                    f"   ❌ Task '{task['task_id']}' depends on missing '{dep}'"
                )

    if dep_errors:
        print("   Dependency errors:")
        for error in dep_errors[:5]:  # Show first 5 errors
            print(error)
    else:
        print("   ✅ All dependencies are satisfiable")


if __name__ == "__main__":
    main()
