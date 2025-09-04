#!/usr/bin/env python3
"""
Phase 1 Agent Team Launch Script
Implementing Real-Time Agent Orchestration Management Layer
Based on corrected priorities from critical gap analysis
"""
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from src.generic_orchestrator import AgentTask, GenericOrchestrator


class Phase1TeamManager:
    """Management layer for Phase 1 implementation team"""

    def __init__(self):
        self.orchestrator = GenericOrchestrator(
            output_dir=Path("./phase1_output"), max_parallel=4, use_optimizations=True
        )
        self.start_time = time.time()

        # Pre-defined UUIDs for predictable monitoring
        self.agent_uuids = {
            "monitor_specialist": "team-phase1-001-monitor-1725408000",
            "quality_specialist": "team-phase1-002-quality-1725408000",
            "integration_specialist": "team-phase1-003-integration-1725408000",
            "interface_specialist": "team-phase1-004-interface-1725408000",
        }

    def create_phase1_tasks(self):
        """Define the 4 specialist agent tasks based on critical gap analysis"""

        critical_context = """
        CRITICAL CONTEXT FROM GAP ANALYSIS:

        The unified context agent needs these capabilities IMMEDIATELY:
        1. Real-Time Agent Status API - Foundation for all monitoring
        2. Quality Gate Management - Complex dependency validation
        3. Enhanced Orchestrator Integration - Monitoring-enabled execution
        4. Management Interface - Unified API for management agents

        Current critical gaps:
        - Orchestrator can launch agents but NO way to monitor progress in real-time
        - No integration between chat_search.py and orchestrator
        - No quality gate validation system for complex dependencies
        - No structured agent status information for management consumption

        TARGET ARCHITECTURE:
        Management Agent → AgentTeamManager → Enhanced Orchestrator → Monitored Agent Teams
                     ↓
        Real-time status via chat_search integration + UUID-based log monitoring
        """

        tasks = [
            AgentTask(
                task_id="monitor_specialist",
                task_type="critical_infrastructure",
                prompt=f"""
                BUILD REAL-TIME AGENT STATUS API (HIGHEST PRIORITY - FOUNDATIONAL)

                You are the Real-Time Monitor Specialist. Your task is CRITICAL - nothing else works without this foundation.

                CRITICAL GAP TO SOLVE:
                "The orchestrator can launch agents but has NO way to monitor their progress in real-time."

                DELIVERABLES REQUIRED:

                1. AgentStatusMonitor Class (apps/agent-orchestrator/src/agent_monitor.py):
                   ```python
                   class AgentStatusMonitor:
                       async def get_agent_status(self, agent_uuid: str) -> AgentStatus
                       async def get_all_agent_statuses(self, team_id: str) -> Dict[str, AgentStatus]
                       async def monitor_agent_logs(self, agent_uuid: str) -> AsyncGenerator[LogEntry]
                   ```

                2. AgentStatus Data Structure:
                   - Current status: running/completed/failed/stuck
                   - Progress indicators from log analysis
                   - Context usage estimation
                   - Error count and recent errors
                   - Last activity timestamp
                   - Deliverables completed/missing

                3. Chat_Search Integration (apps/agent-orchestrator/src/log_parser.py):
                   ```python
                   class AgentLogParser:
                       async def parse_agent_progress(self, uuid: str) -> ProgressStatus
                       async def detect_agent_errors(self, uuid: str) -> List[ErrorInfo]
                       async def check_context_usage(self, uuid: str) -> float
                       async def get_agent_deliverables(self, uuid: str) -> List[str]
                   ```

                4. UUID-Based Log Monitoring:
                   - Direct integration with ~/.claude/projects/{{cwd}}/{{uuid}}.jsonl
                   - Real-time parsing of agent activity
                   - Progress detection from tool calls and outputs
                   - Stuck agent detection (no activity >10 minutes)

                INTEGRATION REQUIREMENTS:
                - Use existing chat_search.py as foundation
                - Build structured wrapper for orchestrator consumption
                - Enable monitoring by agent UUID, not manual log searching
                - Real-time updates every 15 seconds maximum

                SUCCESS CRITERIA:
                - Management agent can query any running agent's current status
                - Real-time progress updates every 15 seconds
                - Automatic detection of stuck/completed agents
                - Integration with chat_search.py works reliably

                CRITICAL: This is the foundation that enables everything else. Focus on reliability and accuracy over advanced features.

                UUID: {self.agent_uuids["monitor_specialist"]}
                """,
                dependencies=[],
            ),
            AgentTask(
                task_id="quality_specialist",
                task_type="critical_infrastructure",
                prompt=f"""
                BUILD QUALITY GATE & DEPENDENCY MANAGEMENT SYSTEM (HIGHEST PRIORITY - PARALLEL)

                You are the Quality Gate Specialist. Your task enables complex project orchestration with validation.

                CRITICAL GAP TO SOLVE:
                "Basic dependency tracking exists but no quality gate validation system for complex projects."

                The unified context system has complex dependencies:
                Database Setup → Migration → Population → Testing → Validation
                Without quality gates, agents advance with incomplete/invalid work.

                DELIVERABLES REQUIRED:

                1. QualityGateManager Class (apps/agent-orchestrator/src/quality_gates.py):
                   ```python
                   class QualityGateManager:
                       async def validate_deliverable(self, agent_id: str, deliverable: Any) -> ValidationResult
                       async def check_quality_gates(self, gate_name: str) -> GateStatus
                       async def block_until_dependencies_ready(self, task_id: str) -> None
                       async def release_dependent_tasks(self, completed_task_id: str) -> None
                   ```

                2. Dependency Validation System:
                   - Validate deliverables before releasing dependent tasks
                   - Quality gate definitions (database_ready, migration_complete, etc.)
                   - Automatic blocking/release of dependent agents
                   - Deliverable integrity checking

                3. Phase-Based Execution Support:
                   - Define phases with quality gates
                   - Automatic phase transitions when gates pass
                   - Rollback capability if validation fails
                   - Dependency graph visualization data

                4. Integration with Orchestrator:
                   - Hook into existing GenericOrchestrator
                   - Add quality gate validation to task execution
                   - Enable complex dependency chains
                   - Non-breaking integration with existing code

                EXAMPLES OF QUALITY GATES NEEDED:
                - database_ready: SELECT * FROM pg_extension WHERE extname = 'vector'
                - migration_complete: SELECT COUNT(*) FROM context_items WHERE source_type = 'chat' > 633
                - api_responding: WebSocket connection test to ws://localhost:8080/ide-bridge succeeds

                SUCCESS CRITERIA:
                - Complex projects can define dependency chains with validation
                - Agents automatically wait for validated dependencies
                - Quality gates prevent advancement with incomplete work
                - Integration maintains orchestrator backward compatibility

                UUID: {self.agent_uuids["quality_specialist"]}
                """,
                dependencies=[],  # Parallel with monitor_specialist
            ),
            AgentTask(
                task_id="integration_specialist",
                task_type="critical_infrastructure",
                prompt=f"""
                BUILD ENHANCED ORCHESTRATOR WITH MONITORING INTEGRATION (HIGH PRIORITY)

                You are the Orchestrator Integration Specialist. Your task integrates monitoring capabilities into existing orchestrator.

                CRITICAL REQUIREMENT:
                Modify existing GenericOrchestrator to support monitoring WITHOUT breaking existing functionality.

                DELIVERABLES REQUIRED:

                1. Enhanced GenericOrchestrator (modify apps/agent-orchestrator/src/generic_orchestrator.py):
                   - Add monitoring integration hooks
                   - Support pre-defined UUID assignment to agents
                   - Background execution with status tracking
                   - Integration with AgentStatusMonitor and QualityGateManager

                2. UUID Management System:
                   - Accept pre-defined UUIDs in task definitions
                   - Pass UUIDs to spawned agents for predictable log files
                   - Track agent lifecycle with UUID mapping
                   - Enable direct log file monitoring

                3. Background Execution Manager:
                   - Launch agent teams without blocking management agent
                   - Return team_id for monitoring and management
                   - Track background job status and completion
                   - Handle agent failures and cleanup

                4. Monitoring Integration Points:
                   - Hook real-time status monitoring into execution loop
                   - Integrate quality gate validation into task flow
                   - Enable management agent queries during execution
                   - Provide structured status updates

                INTEGRATION REQUIREMENTS:
                - MUST maintain backward compatibility with existing orchestrator usage
                - MUST work with monitor_specialist's AgentStatusMonitor
                - MUST work with quality_specialist's QualityGateManager
                - MUST enable interface_specialist to build unified management API

                DEPENDENCIES:
                - Wait for monitor_specialist to complete AgentStatusMonitor
                - Wait for quality_specialist to complete QualityGateManager
                - Coordinate integration approach with both specialists

                SUCCESS CRITERIA:
                - Existing orchestrator code continues to work unchanged
                - New monitoring capabilities available via enhanced interface
                - Background agent execution with predictable UUIDs
                - Seamless integration with monitoring and quality systems

                UUID: {self.agent_uuids["integration_specialist"]}
                """,
                dependencies=["monitor_specialist", "quality_specialist"],
            ),
            AgentTask(
                task_id="interface_specialist",
                task_type="critical_infrastructure",
                prompt=f"""
                BUILD AGENTTEAMMANAGER - PRIMARY MANAGEMENT INTERFACE (HIGH PRIORITY)

                You are the Management Interface Specialist. Your task creates the unified interface that management agents will use.

                OBJECTIVE:
                Create AgentTeamManager as the single interface that enables any management agent to launch and monitor agent teams.

                DELIVERABLES REQUIRED:

                1. AgentTeamManager Class (apps/agent-orchestrator/src/agent_team_manager.py):
                   ```python
                   class AgentTeamManager:
                       def launch_monitored_team(self, task_definitions: List[Dict]) -> str
                       def get_team_status(self, team_id: str) -> TeamStatus
                       def monitor_continuously(self, team_id: str, interval: int = 15) -> Iterator[TeamStatus]
                       def get_final_results(self, team_id: str) -> TeamResults
                   ```

                2. Unified Status API:
                   - TeamStatus aggregating all agent statuses
                   - Real-time progress tracking across entire team
                   - Blocked/completed agent identification
                   - Overall progress percentage and ETA

                3. Management Agent Usage Pattern:
                   ```python
                   manager = AgentTeamManager()
                   team_id = manager.launch_monitored_team(tasks)

                   for status in manager.monitor_continuously(team_id):
                       handle_team_status(status)
                   ```

                4. Integration with All Specialist Components:
                   - Use enhanced orchestrator for agent execution
                   - Use AgentStatusMonitor for real-time status
                   - Use QualityGateManager for dependency validation
                   - Provide unified, simplified interface hiding complexity

                INTEGRATION REQUIREMENTS:
                - MUST integrate monitor_specialist's AgentStatusMonitor
                - MUST integrate quality_specialist's QualityGateManager
                - MUST use integration_specialist's Enhanced Orchestrator
                - MUST provide agent-consumable APIs (not human interfaces)

                DEPENDENCIES:
                - Wait for all other specialists to complete core components
                - Coordinate integration testing with all components
                - Validate end-to-end workflow functionality

                SUCCESS CRITERIA:
                - Management agents can launch and monitor teams with single interface
                - Real-time visibility into entire team status
                - Structured APIs for programmatic decision making
                - Integration of all Phase 1 capabilities working together

                UUID: {self.agent_uuids["interface_specialist"]}
                """,
                dependencies=[
                    "monitor_specialist",
                    "quality_specialist",
                    "integration_specialist",
                ],
            ),
        ]

        return tasks

    async def launch_phase1_team(self):
        """Launch the Phase 1 implementation team with monitoring setup"""

        print("🚀 LAUNCHING PHASE 1 AGENT ORCHESTRATION TEAM")
        print("=" * 60)
        print("OBJECTIVE: Build Real-Time Agent Management Layer")
        print(
            "ADDRESSING: Critical gaps identified in unified context agent requirements"
        )
        print()

        # Create specialist tasks
        tasks = self.create_phase1_tasks()

        print("👥 AGENT TEAM COMPOSITION:")
        for task in tasks:
            uuid = self.agent_uuids[task.task_id]
            deps = ", ".join(task.dependencies) if task.dependencies else "None"
            print(f"   • {task.task_id}: {uuid}")
            print(f"     Dependencies: {deps}")
            print()

        print("📊 MONITORING SETUP:")
        print(f"   • Team Start Time: {datetime.now().isoformat()}")
        print(f"   • Log Monitoring: Every 15 seconds")
        print(f"   • UUID-Based Tracking: Enabled")
        print(f"   • Output Directory: ./phase1_output/")
        print()

        # Launch team execution
        print("🎯 LAUNCHING AGENTS...")
        try:
            # Execute the orchestrated tasks
            results = await self.orchestrator.execute_batch(tasks)
            return results
        except Exception as e:
            print(f"❌ TEAM LAUNCH FAILED: {e}")
            raise

    def get_monitoring_info(self):
        """Return monitoring information for real-time tracking"""
        return {
            "agent_uuids": self.agent_uuids,
            "log_paths": {
                agent: f"~/.claude/projects/-home-opsvi-master-root-apps-agent-orchestrator/{uuid}.jsonl"
                for agent, uuid in self.agent_uuids.items()
            },
            "monitoring_commands": {
                "check_all_status": f"python apps/chat-search/chat_search.py --limit 5 --date-from {datetime.now().strftime('%Y-%m-%d')} 'progress|completed|error'",
                "monitor_specific": "python apps/chat-search/chat_search.py --file-filter {uuid} --type assistant --limit 3 .",
                "tail_logs": "tail -f ~/.claude/projects/-home-opsvi-master-root-apps-agent-orchestrator/{uuid}.jsonl",
            },
        }


async def main():
    """Main execution function"""
    manager = Phase1TeamManager()

    # Display monitoring setup before launch
    monitoring_info = manager.get_monitoring_info()

    print("🔍 REAL-TIME MONITORING SETUP:")
    print("=" * 60)
    print("AGENT UUIDs FOR DIRECT LOG MONITORING:")
    for agent, uuid in monitoring_info["agent_uuids"].items():
        print(f"   {agent}: {uuid}")
    print()

    print("MONITORING COMMANDS:")
    print(
        f"   • Check All: {monitoring_info['monitoring_commands']['check_all_status']}"
    )
    print(
        f"   • Specific Agent: {monitoring_info['monitoring_commands']['monitor_specific']}"
    )
    print(f"   • Tail Logs: {monitoring_info['monitoring_commands']['tail_logs']}")
    print()

    # Launch the team
    print("▶️  INITIATING PHASE 1 TEAM EXECUTION...")
    print("⏱️  Expected Duration: 5-7 days total")
    print("🎯 Success Criteria: Real-time agent management layer operational")
    print()

    start_time = time.time()
    results = await manager.launch_phase1_team()
    duration = time.time() - start_time

    print()
    print("✅ PHASE 1 TEAM EXECUTION COMPLETE")
    print("=" * 60)
    print(f"Duration: {duration/60:.1f} minutes")
    print(f"Results: {len(results)} agents completed")
    print()
    print("🎯 PHASE 1 DELIVERABLES READY FOR VALIDATION:")
    print("   • Real-Time Agent Status API")
    print("   • Quality Gate & Dependency Management")
    print("   • Enhanced Orchestrator Integration")
    print("   • AgentTeamManager Interface")
    print()
    print("📋 NEXT: Validation testing with complex dependency project")


if __name__ == "__main__":
    asyncio.run(main())
