#!/usr/bin/env python3
"""
Enhanced Multi-Agent SDLC Orchestrator with Full Visibility
Solves the core problems: timeout, validation, visibility, debugging
"""

import asyncio
import json
import subprocess
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..claude_code_v3.agent_monitor import (
    AgentHealthMonitor,
    MonitoringDashboard,
    PhaseValidator,
    SessionCaptureAgent,
)


class SDLCPhase(Enum):
    """SDLC phases with specific requirements"""

    DISCOVERY = "discovery"
    DESIGN = "design"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    PRODUCTION = "production"
    POSTMORTEM = "postmortem"


class PhaseConfig:
    """Configuration for each SDLC phase"""

    CONFIGS = {
        SDLCPhase.DISCOVERY: {
            "timeout": 900,  # 15 minutes (was 600)
            "required_outputs": ["requirements.md", "research_notes.md"],
            "validation_checks": [
                "requirements_documented",
                "scope_defined",
                "constraints_identified",
            ],
            "mcp_servers": ["firecrawl", "research_papers", "tech_docs"],
            "agent_prompts": {
                "role": "Requirements Analyst",
                "focus": "Understanding and documenting requirements",
                "outputs": "Clear requirements and constraints documentation",
            },
        },
        SDLCPhase.DESIGN: {
            "timeout": 1200,  # 20 minutes
            "required_outputs": ["architecture.md", "design_doc.md", "api_spec.md"],
            "validation_checks": [
                "architecture_defined",
                "interfaces_specified",
                "data_models_created",
            ],
            "mcp_servers": ["mermaid", "tech_docs"],
            "agent_prompts": {
                "role": "Solution Architect",
                "focus": "Creating comprehensive technical design",
                "outputs": "Architecture diagrams and design documentation",
            },
        },
        SDLCPhase.PLANNING: {
            "timeout": 600,  # 10 minutes
            "required_outputs": ["project_plan.md", "tasks.json"],
            "validation_checks": [
                "tasks_defined",
                "dependencies_mapped",
                "timeline_created",
            ],
            "mcp_servers": [],
            "agent_prompts": {
                "role": "Project Manager",
                "focus": "Breaking down work into executable tasks",
                "outputs": "Detailed project plan with task breakdown",
            },
        },
        SDLCPhase.DEVELOPMENT: {
            "timeout": 1800,  # 30 minutes
            "required_outputs": ["src/", "README.md"],
            "validation_checks": [
                "code_implemented",
                "no_syntax_errors",
                "dependencies_resolved",
            ],
            "mcp_servers": ["shell_exec"],
            "agent_prompts": {
                "role": "Senior Developer",
                "focus": "Implementing clean, maintainable code",
                "outputs": "Working implementation with documentation",
            },
        },
        SDLCPhase.TESTING: {
            "timeout": 1200,  # 20 minutes
            "required_outputs": ["tests/", "test_results.md"],
            "validation_checks": [
                "tests_created",
                "tests_passing",
                "coverage_adequate",
            ],
            "mcp_servers": ["shell_exec"],
            "agent_prompts": {
                "role": "QA Engineer",
                "focus": "Comprehensive testing and quality assurance",
                "outputs": "Test suite with passing tests and coverage report",
            },
        },
    }


class EnhancedOrchestrator:
    """Orchestrates multi-agent SDLC with full visibility and validation"""

    def __init__(self, project_path: Path, monitoring_enabled: bool = True):
        self.project_path = Path(project_path)
        self.monitoring_enabled = monitoring_enabled
        self.session_dir = self.project_path / ".sdlc-sessions"
        self.session_dir.mkdir(exist_ok=True)

        # Initialize monitoring components
        self.capture_agent = SessionCaptureAgent(self.session_dir)
        self.validator = PhaseValidator()
        self.health_monitor = AgentHealthMonitor()
        self.dashboard = MonitoringDashboard() if monitoring_enabled else None

        # Track active agents
        self.active_agents: Dict[str, Dict] = {}

    async def execute_sdlc_lifecycle(
        self,
        project_name: str,
        requirements: str,
        phases_to_run: Optional[List[SDLCPhase]] = None,
    ) -> Dict[str, Any]:
        """Execute SDLC lifecycle with monitoring and validation"""

        if phases_to_run is None:
            phases_to_run = [
                SDLCPhase.DISCOVERY,
                SDLCPhase.DESIGN,
                SDLCPhase.PLANNING,
                SDLCPhase.DEVELOPMENT,
                SDLCPhase.TESTING,
            ]

        results = {
            "project_name": project_name,
            "started_at": datetime.now().isoformat(),
            "phases": {},
            "success": True,
            "monitoring_enabled": self.monitoring_enabled,
        }

        # Initialize dashboard
        if self.dashboard:
            await self.dashboard.initialize(project_name, phases_to_run)

        # Execute each phase with validation gates
        previous_outputs = {}

        for phase in phases_to_run:
            print(f"\n{'='*60}")
            print(f"EXECUTING PHASE: {phase.value.upper()}")
            print(f"{'='*60}")

            phase_result = await self._execute_phase(
                phase=phase,
                project_name=project_name,
                requirements=requirements,
                previous_outputs=previous_outputs,
            )

            results["phases"][phase.value] = phase_result

            # Validation gate
            if not phase_result.get("validation", {}).get("passed", False):
                print(f"\n❌ Phase {phase.value} failed validation!")
                print(f"   Errors: {phase_result['validation'].get('errors', [])}")
                results["success"] = False

                # Don't proceed to next phase if validation failed
                if phase != SDLCPhase.POSTMORTEM:  # Always run postmortem
                    break

            # Accumulate outputs for next phase
            previous_outputs[phase.value] = phase_result.get("outputs", {})

            # Update dashboard
            if self.dashboard:
                await self.dashboard.update_phase_status(
                    phase.value,
                    "completed"
                    if phase_result.get("validation", {}).get("passed")
                    else "failed",
                    phase_result,
                )

        # Generate final report
        results["completed_at"] = datetime.now().isoformat()
        results["summary"] = self._generate_summary(results)

        # Save final results
        results_file = self.session_dir / f"{project_name}_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n{'='*60}")
        print(f"SDLC EXECUTION {'SUCCESSFUL' if results['success'] else 'FAILED'}")
        print(f"Results saved to: {results_file}")
        print(f"{'='*60}")

        return results

    async def _execute_phase(
        self,
        phase: SDLCPhase,
        project_name: str,
        requirements: str,
        previous_outputs: Dict,
    ) -> Dict[str, Any]:
        """Execute a single SDLC phase with monitoring"""

        config = PhaseConfig.CONFIGS.get(phase, {})
        job_id = f"{phase.value}_{uuid.uuid4().hex[:8]}"

        # Prepare phase directory
        phase_dir = self.session_dir / phase.value
        phase_dir.mkdir(exist_ok=True)

        # Build agent command
        agent_cmd = self._build_agent_command(
            phase=phase,
            project_name=project_name,
            requirements=requirements,
            previous_outputs=previous_outputs,
            config=config,
        )

        print(f"\n🚀 Launching {phase.value} agent...")
        print(f"   Job ID: {job_id}")
        print(f"   Timeout: {config.get('timeout', 600)}s")
        print(f"   Required outputs: {config.get('required_outputs', [])}")

        # Start agent process
        process = subprocess.Popen(
            agent_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.project_path),
        )

        # Register agent
        self.active_agents[job_id] = {
            "phase": phase.value,
            "process": process,
            "started_at": datetime.now(),
            "config": config,
        }

        # Capture session with monitoring
        if self.monitoring_enabled:
            session = await self.capture_agent.capture_session_stream(
                process=process,
                job_id=job_id,
                phase=phase.value,
                timeout=config.get("timeout", 600),
            )
        else:
            # Simple wait without monitoring
            try:
                stdout, stderr = process.communicate(timeout=config.get("timeout", 600))
                session = {
                    "job_id": job_id,
                    "phase": phase.value,
                    "stdout": stdout,
                    "stderr": stderr,
                    "return_code": process.returncode,
                    "status": "completed" if process.returncode == 0 else "failed",
                }
            except subprocess.TimeoutExpired:
                process.kill()
                session = {
                    "job_id": job_id,
                    "phase": phase.value,
                    "status": "timeout",
                    "error": f"Agent timed out after {config.get('timeout')}s",
                }

        # Save session
        session_file = phase_dir / f"{job_id}_session.json"
        with open(session_file, "w") as f:
            json.dump(session, f, indent=2)

        # Validate phase outputs
        validation_result = await self.validator.validate_phase(
            phase=phase.value,
            project_path=self.project_path,
            session=session,
            config=config,
        )

        # Health check
        health = await self.health_monitor.check_health(session)

        # Unregister agent
        del self.active_agents[job_id]

        return {
            "job_id": job_id,
            "phase": phase.value,
            "status": session.get("status", "unknown"),
            "duration_seconds": (
                datetime.now()
                - self.active_agents.get(job_id, {}).get("started_at", datetime.now())
            ).total_seconds()
            if job_id in self.active_agents
            else 0,
            "validation": validation_result,
            "health": health,
            "outputs": self._extract_outputs(session),
            "session_file": str(session_file),
        }

    def _build_agent_command(
        self,
        phase: SDLCPhase,
        project_name: str,
        requirements: str,
        previous_outputs: Dict,
        config: Dict,
    ) -> List[str]:
        """Build the command to execute an agent"""

        # Build context from previous phases
        context = {
            "project_name": project_name,
            "requirements": requirements,
            "previous_phases": previous_outputs,
            "phase_config": config,
        }

        context_file = self.session_dir / f"{phase.value}_context.json"
        with open(context_file, "w") as f:
            json.dump(context, f, indent=2)

        # Build agent prompt
        agent_prompts = config.get("agent_prompts", {})
        prompt = f"""
You are a {agent_prompts.get('role', 'Specialist')} working on the {phase.value} phase.

Project: {project_name}
Requirements: {requirements}

Your focus: {agent_prompts.get('focus', 'Complete this phase successfully')}
Expected outputs: {agent_prompts.get('outputs', 'Phase deliverables')}

Context from previous phases is available at: {context_file}

Please create the following outputs:
{chr(10).join('- ' + out for out in config.get('required_outputs', []))}
"""

        # Select MCP servers for this phase
        mcp_args = []
        for server in config.get("mcp_servers", []):
            mcp_args.extend(["--mcp", server])

        # Build command
        cmd = [
            "claude",
            "code",
            prompt,
            "--timeout",
            str(config.get("timeout", 600)),
            "--working-dir",
            str(self.project_path),
        ] + mcp_args

        return cmd

    def _extract_outputs(self, session: Dict) -> Dict[str, Any]:
        """Extract outputs from agent session"""
        outputs = {}

        # Extract files created
        if "files_created" in session:
            outputs["files"] = session["files_created"]

        # Extract key information from stdout
        if "stdout" in session:
            # Parse for specific patterns
            stdout = session.get("stdout", "")
            if "requirements" in stdout.lower():
                outputs["has_requirements"] = True
            if "error" in stdout.lower():
                outputs["has_errors"] = True

        return outputs

    def _generate_summary(self, results: Dict) -> Dict[str, Any]:
        """Generate execution summary"""
        summary = {
            "total_phases": len(results["phases"]),
            "successful_phases": sum(
                1
                for p in results["phases"].values()
                if p.get("validation", {}).get("passed", False)
            ),
            "failed_phases": sum(
                1
                for p in results["phases"].values()
                if not p.get("validation", {}).get("passed", False)
            ),
            "total_duration": sum(
                p.get("duration_seconds", 0) for p in results["phases"].values()
            ),
        }

        # Identify bottlenecks
        slowest_phase = max(
            results["phases"].items(),
            key=lambda x: x[1].get("duration_seconds", 0),
            default=(None, {}),
        )

        if slowest_phase[0]:
            summary["bottleneck"] = {
                "phase": slowest_phase[0],
                "duration": slowest_phase[1].get("duration_seconds", 0),
            }

        return summary


async def run_sdlc(
    project_name: str,
    requirements: str,
    project_path: Optional[Path] = None,
    phases: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience function to run SDLC lifecycle"""

    if project_path is None:
        project_path = Path.cwd()

    if phases:
        phases_to_run = [SDLCPhase[p.upper()] for p in phases]
    else:
        phases_to_run = None

    orchestrator = EnhancedOrchestrator(project_path, monitoring_enabled=True)

    return await orchestrator.execute_sdlc_lifecycle(
        project_name=project_name,
        requirements=requirements,
        phases_to_run=phases_to_run,
    )


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python enhanced_orchestrator.py <project_name> <requirements>")
        sys.exit(1)

    asyncio.run(run_sdlc(sys.argv[1], sys.argv[2]))
