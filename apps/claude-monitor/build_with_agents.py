#!/usr/bin/env python3
"""
Build Claude System Monitor using multi-agent orchestration
Uses agent-orchestrator to parallelize development across 15 agents
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add agent-orchestrator to path
sys.path.append("/home/opsvi/master_root/apps/agent-orchestrator")
from src.generic_orchestrator import AgentTask, GenericOrchestrator


class MonitoringSystemBuilder:
    """Orchestrate building the Claude monitoring system"""

    def __init__(self):
        self.output_dir = Path("/tmp/claude_monitor_build")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.orchestrator = GenericOrchestrator(
            output_dir=self.output_dir,
            max_parallel=15,  # Use all available tokens
            use_optimizations=True,
        )

        self.monitor_dir = Path("/home/opsvi/master_root/apps/claude-monitor")
        self.monitor_dir.mkdir(parents=True, exist_ok=True)

    async def build_phase_1_core(self):
        """Phase 1: Build core monitoring components (3 agents in parallel)"""
        print("\n" + "=" * 60)
        print("PHASE 1: Building Core Components")
        print("=" * 60)

        tasks = [
            AgentTask(
                task_id="backend_service",
                task_type="development",
                prompt="""Create a comprehensive monitoring backend service:

REQUIREMENTS:
1. FastAPI application with WebSocket support
2. Query SQLite database at /home/opsvi/master_root/chat_logs.db
3. Monitor system resources using psutil
4. Track Docker containers with Claude processes
5. Provide REST endpoints and WebSocket for real-time updates

DATABASE QUERIES:
- Token usage from nodes table (raw_json field)
- Session information from sessions table
- Tool usage from tool_calls table

ENDPOINTS:
- GET /api/dashboard - Current dashboard data
- GET /api/tokens - Token usage statistics
- GET /api/docker - Docker container status
- GET /api/system - System resource metrics
- WS /ws - WebSocket for real-time updates

Save as: /home/opsvi/master_root/apps/claude-monitor/backend/monitoring_service.py

Include proper error handling, logging, and async operations.""",
                dependencies=[],
            ),
            AgentTask(
                task_id="console_ui",
                task_type="development",
                prompt="""Create a beautiful Rich-based terminal UI for monitoring:

REQUIREMENTS:
1. Multiple view modes:
   - master: Everything combined
   - docker: Docker containers focus
   - agents: Agent orchestrator focus
   - tokens: Token usage focus
   - system: System resources focus
   - costs: Cost analysis focus

2. Keyboard navigation:
   - Tab: Switch between views
   - Arrow keys: Navigate
   - Q: Quit
   - R: Refresh
   - H: Help
   - 1-9: Quick view switch

3. Real-time updates via WebSocket connection to backend

4. Visual elements:
   - Progress bars for agent tasks
   - Sparklines for metrics
   - Tables for data
   - Color-coded status indicators

5. Overlay system for additional data layers

Save as: /home/opsvi/master_root/apps/claude-monitor/console/terminal_ui.py

Use Rich library features: Layout, Table, Progress, Live, etc.""",
                dependencies=[],
            ),
            AgentTask(
                task_id="docker_monitor",
                task_type="development",
                prompt="""Create Docker monitoring for Claude processes:

REQUIREMENTS:
1. Use docker-py library to interact with Docker
2. Find all containers with Claude activity:
   - Check environment variables for CLAUDE tokens
   - Monitor processes for 'claude' command
   - Check container labels
   - Scan recent logs for Claude mentions

3. Track per container:
   - Resource usage (CPU, Memory, Network)
   - Running Claude processes
   - Token consumption
   - Log streaming

4. Aggregate metrics across all containers

Save as: /home/opsvi/master_root/apps/claude-monitor/monitors/docker_monitor.py

Include error handling for Docker daemon connection issues.""",
                dependencies=[],
            ),
        ]

        results = await self.orchestrator.execute_batch(tasks)
        print(f"✅ Phase 1 Complete: {len(results)} components built")
        return results

    async def build_phase_2_integration(self):
        """Phase 2: Integration and data collection (3 agents)"""
        print("\n" + "=" * 60)
        print("PHASE 2: Integration Components")
        print("=" * 60)

        tasks = [
            AgentTask(
                task_id="data_collector",
                task_type="development",
                prompt="""Create a data collection service that aggregates from all sources:

REQUIREMENTS:
1. Collect from multiple sources:
   - SQLite database queries
   - System resources (psutil)
   - Docker containers
   - Process monitoring
   - Log files

2. Aggregate and calculate:
   - Total token usage across all sources
   - Cost calculations by model
   - Resource usage by project
   - Error rates and patterns

3. Cache results for performance

Save as: /home/opsvi/master_root/apps/claude-monitor/collectors/data_collector.py""",
                dependencies=["backend_service", "docker_monitor"],
            ),
            AgentTask(
                task_id="view_manager",
                task_type="development",
                prompt="""Create view management for the console UI:

REQUIREMENTS:
1. Define view layouts for each mode
2. Handle view switching and overlays
3. Manage data flow to UI components
4. Implement filtering and sorting

Save as: /home/opsvi/master_root/apps/claude-monitor/console/view_manager.py""",
                dependencies=["console_ui"],
            ),
            AgentTask(
                task_id="main_app",
                task_type="development",
                prompt="""Create the main application that ties everything together:

REQUIREMENTS:
1. Start backend service
2. Initialize console UI
3. Handle graceful shutdown
4. Provide CLI arguments for different modes
5. Include --web flag for future web UI

Save as: /home/opsvi/master_root/apps/claude-monitor/main.py

Create launch script:
Save as: /home/opsvi/master_root/apps/claude-monitor/monitor.sh""",
                dependencies=["backend_service", "console_ui", "data_collector"],
            ),
        ]

        results = await self.orchestrator.execute_batch(tasks)
        print(f"✅ Phase 2 Complete: {len(results)} integration components built")
        return results

    async def build_phase_3_testing(self):
        """Phase 3: Testing and documentation (2 agents)"""
        print("\n" + "=" * 60)
        print("PHASE 3: Testing & Documentation")
        print("=" * 60)

        tasks = [
            AgentTask(
                task_id="test_suite",
                task_type="development",
                prompt="""Create tests for the monitoring system:

1. Unit tests for each component
2. Integration tests for data flow
3. Mock Docker and database for testing
4. Performance tests

Save as: /home/opsvi/master_root/apps/claude-monitor/tests/test_monitor.py""",
                dependencies=["main_app"],
            ),
            AgentTask(
                task_id="documentation",
                task_type="documentation",
                prompt="""Create comprehensive documentation:

1. README.md with installation and usage
2. Architecture overview
3. API documentation
4. Configuration guide

Save as: /home/opsvi/master_root/apps/claude-monitor/README.md""",
                dependencies=["main_app"],
            ),
        ]

        results = await self.orchestrator.execute_batch(tasks)
        print(f"✅ Phase 3 Complete: Testing and documentation created")
        return results

    async def build(self):
        """Execute the full build process"""
        start_time = datetime.now()
        print(f"\n🚀 Starting Claude Monitor Build at {start_time}")
        print(f"Using {self.orchestrator.max_parallel} parallel agents")

        try:
            # Phase 1: Core components (parallel)
            phase1_results = await self.build_phase_1_core()

            # Phase 2: Integration (depends on Phase 1)
            phase2_results = await self.build_phase_2_integration()

            # Phase 3: Testing & Docs (depends on Phase 2)
            phase3_results = await self.build_phase_3_testing()

            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            print("\n" + "=" * 60)
            print("BUILD COMPLETE")
            print("=" * 60)
            print(f"Total Duration: {duration:.1f} seconds")
            print(
                f"Components Built: {len(phase1_results) + len(phase2_results) + len(phase3_results)}"
            )
            print(f"Output Directory: {self.monitor_dir}")

            # Save build report
            report = {
                "build_time": start_time.isoformat(),
                "duration_seconds": duration,
                "phases": {
                    "phase1": [r["task_id"] for r in phase1_results],
                    "phase2": [r["task_id"] for r in phase2_results],
                    "phase3": [r["task_id"] for r in phase3_results],
                },
                "output_dir": str(self.monitor_dir),
            }

            report_file = self.monitor_dir / "build_report.json"
            report_file.write_text(json.dumps(report, indent=2))
            print(f"\nBuild report saved to: {report_file}")

            return True

        except Exception as e:
            print(f"\n❌ Build failed: {e}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """Main entry point"""
    builder = MonitoringSystemBuilder()
    success = await builder.build()

    if success:
        print("\n✅ Claude Monitor system built successfully!")
        print("\nTo run the monitor:")
        print("  cd /home/opsvi/master_root/apps/claude-monitor")
        print("  ./monitor.sh")
    else:
        print("\n❌ Build failed. Check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
