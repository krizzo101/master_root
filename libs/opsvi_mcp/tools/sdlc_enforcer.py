#!/usr/bin/env python3
"""
SDLC Enforcer MCP Tool - Ensures agents follow proper SDLC process
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib

class SDLCPhase(Enum):
    """SDLC Phases in strict order"""
    DISCOVERY = "discovery"
    DESIGN = "design"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    PRODUCTION = "production"

@dataclass
class PhaseRequirements:
    """Requirements for each phase"""
    phase: SDLCPhase
    required_deliverables: List[str]
    quality_gates: Dict[str, Any]
    minimum_duration_percent: float
    maximum_skip_penalty: float = 1.0  # Multiplier for rework if skipped

@dataclass
class ProjectState:
    """Current state of a project in SDLC"""
    project_id: str
    project_name: str
    description: str
    current_phase: SDLCPhase
    completed_phases: List[SDLCPhase]
    phase_artifacts: Dict[str, List[str]]
    quality_scores: Dict[str, float]
    started_at: str
    last_updated: str
    knowledge_queries: List[str]
    risks_identified: List[Dict[str, str]]
    rollback_points: List[Dict[str, str]]
    
class SDLCEnforcer:
    """Main SDLC Enforcement System"""
    
    PHASE_REQUIREMENTS = {
        SDLCPhase.DISCOVERY: PhaseRequirements(
            phase=SDLCPhase.DISCOVERY,
            required_deliverables=[
                "requirements.md",
                "risk_matrix.json",
                "dependency_map.json",
                "stakeholder_list.md",
                "success_criteria.md"
            ],
            quality_gates={
                "knowledge_queried": True,
                "requirements_complete": True,
                "risks_assessed": True,
                "dependencies_mapped": True,
                "stakeholders_identified": True
            },
            minimum_duration_percent=0.10
        ),
        SDLCPhase.DESIGN: PhaseRequirements(
            phase=SDLCPhase.DESIGN,
            required_deliverables=[
                "architecture_design.md",
                "component_diagram.json",
                "api_specification.yaml",
                "database_schema.sql",
                "security_review.md"
            ],
            quality_gates={
                "architecture_reviewed": True,
                "interfaces_defined": True,
                "security_assessed": True,
                "scalability_planned": True,
                "integration_mapped": True
            },
            minimum_duration_percent=0.15
        ),
        SDLCPhase.PLANNING: PhaseRequirements(
            phase=SDLCPhase.PLANNING,
            required_deliverables=[
                "implementation_plan.md",
                "sprint_plan.json",
                "test_strategy.md",
                "ci_cd_pipeline.yaml",
                "rollback_procedures.md"
            ],
            quality_gates={
                "tasks_broken_down": True,
                "timeline_realistic": True,
                "resources_allocated": True,
                "test_plan_complete": True,
                "rollback_defined": True
            },
            minimum_duration_percent=0.05
        ),
        SDLCPhase.DEVELOPMENT: PhaseRequirements(
            phase=SDLCPhase.DEVELOPMENT,
            required_deliverables=[
                "source_code",
                "unit_tests",
                "integration_tests",
                "documentation",
                "code_review_log.json"
            ],
            quality_gates={
                "code_coverage": 0.80,
                "tests_passing": True,
                "security_scan_passed": True,
                "code_reviewed": True,
                "documentation_complete": True
            },
            minimum_duration_percent=0.35
        ),
        SDLCPhase.TESTING: PhaseRequirements(
            phase=SDLCPhase.TESTING,
            required_deliverables=[
                "test_results.json",
                "performance_report.md",
                "security_audit.md",
                "uat_signoff.md",
                "bug_report.json"
            ],
            quality_gates={
                "unit_tests_passed": True,
                "integration_tests_passed": True,
                "performance_acceptable": True,
                "security_validated": True,
                "uat_completed": True
            },
            minimum_duration_percent=0.15
        ),
        SDLCPhase.DEPLOYMENT: PhaseRequirements(
            phase=SDLCPhase.DEPLOYMENT,
            required_deliverables=[
                "deployment_guide.md",
                "runbook.md",
                "monitoring_config.yaml",
                "alerts_config.yaml",
                "rollback_tested.json"
            ],
            quality_gates={
                "deployment_automated": True,
                "monitoring_configured": True,
                "alerts_setup": True,
                "rollback_tested": True,
                "documentation_complete": True
            },
            minimum_duration_percent=0.05
        ),
        SDLCPhase.PRODUCTION: PhaseRequirements(
            phase=SDLCPhase.PRODUCTION,
            required_deliverables=[
                "deployment_log.json",
                "health_check_results.json",
                "performance_metrics.json",
                "incident_log.json",
                "lessons_learned.md"
            ],
            quality_gates={
                "deployment_successful": True,
                "health_checks_passing": True,
                "sla_met": True,
                "monitoring_active": True,
                "knowledge_updated": True
            },
            minimum_duration_percent=0.0  # Ongoing
        )
    }
    
    def __init__(self, workspace_dir: str = "/home/opsvi/master_root"):
        self.workspace = Path(workspace_dir)
        self.state_file = self.workspace / ".proj-intel" / "sdlc_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.projects: Dict[str, ProjectState] = self._load_state()
        
    def _load_state(self) -> Dict[str, ProjectState]:
        """Load existing project states"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                return {
                    pid: ProjectState(**pdata) 
                    for pid, pdata in data.items()
                }
        return {}
    
    def _save_state(self):
        """Persist project states"""
        data = {
            pid: asdict(pstate)
            for pid, pstate in self.projects.items()
        }
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def start_project(
        self, 
        project_name: str, 
        description: str,
        force_sdlc: bool = True
    ) -> Dict[str, Any]:
        """Initialize a new project with SDLC enforcement"""
        
        # Generate unique project ID
        project_id = hashlib.md5(
            f"{project_name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        # Create project state
        project = ProjectState(
            project_id=project_id,
            project_name=project_name,
            description=description,
            current_phase=SDLCPhase.DISCOVERY,
            completed_phases=[],
            phase_artifacts={},
            quality_scores={},
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            knowledge_queries=[],
            risks_identified=[],
            rollback_points=[]
        )
        
        self.projects[project_id] = project
        self._save_state()
        
        # Create project structure
        project_dir = self.workspace / "projects" / project_id
        for phase in SDLCPhase:
            (project_dir / phase.value).mkdir(parents=True, exist_ok=True)
        
        # Generate initial checklist
        checklist = self._generate_phase_checklist(
            project_id, 
            SDLCPhase.DISCOVERY
        )
        
        return {
            "status": "success",
            "project_id": project_id,
            "message": f"Project '{project_name}' initialized in DISCOVERY phase",
            "current_phase": "DISCOVERY",
            "next_steps": checklist,
            "enforcement_mode": "STRICT" if force_sdlc else "ADVISORY"
        }
    
    def _generate_phase_checklist(
        self, 
        project_id: str, 
        phase: SDLCPhase
    ) -> List[Dict[str, Any]]:
        """Generate checklist for current phase"""
        
        requirements = self.PHASE_REQUIREMENTS[phase]
        checklist = []
        
        # Add required deliverables
        for deliverable in requirements.required_deliverables:
            checklist.append({
                "type": "deliverable",
                "name": deliverable,
                "required": True,
                "completed": False,
                "path": f"projects/{project_id}/{phase.value}/{deliverable}"
            })
        
        # Add quality gates
        for gate, requirement in requirements.quality_gates.items():
            checklist.append({
                "type": "quality_gate",
                "name": gate,
                "required": True,
                "requirement": requirement,
                "completed": False,
                "validation_method": self._get_validation_method(gate)
            })
        
        return checklist
    
    def _get_validation_method(self, gate: str) -> str:
        """Return validation method for a quality gate"""
        validation_methods = {
            "knowledge_queried": "check_knowledge_system_queries",
            "requirements_complete": "validate_requirements_document",
            "code_coverage": "run_coverage_analysis",
            "tests_passing": "execute_test_suite",
            "security_scan_passed": "run_security_scanner",
            "deployment_successful": "verify_deployment_status"
        }
        return validation_methods.get(gate, "manual_review")
    
    def validate_phase(
        self, 
        project_id: str,
        override: bool = False
    ) -> Dict[str, Any]:
        """Validate current phase before proceeding"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        current_phase = project.current_phase
        requirements = self.PHASE_REQUIREMENTS[current_phase]
        
        # Check deliverables
        deliverables_check = self._check_deliverables(
            project_id, 
            current_phase, 
            requirements.required_deliverables
        )
        
        # Check quality gates
        quality_check = self._check_quality_gates(
            project_id,
            current_phase,
            requirements.quality_gates
        )
        
        # Calculate phase score
        total_checks = len(deliverables_check) + len(quality_check)
        passed_checks = sum(
            1 for check in deliverables_check + quality_check 
            if check['passed']
        )
        phase_score = passed_checks / total_checks if total_checks > 0 else 0
        
        # Store quality score
        project.quality_scores[current_phase.value] = phase_score
        
        # Determine if phase can be completed
        can_proceed = phase_score >= 0.95 or override
        
        validation_result = {
            "status": "success" if can_proceed else "failed",
            "project_id": project_id,
            "current_phase": current_phase.value,
            "phase_score": phase_score,
            "can_proceed": can_proceed,
            "deliverables": deliverables_check,
            "quality_gates": quality_check,
            "issues": [
                check for check in deliverables_check + quality_check 
                if not check['passed']
            ]
        }
        
        if can_proceed:
            validation_result["message"] = f"Phase {current_phase.value} validated successfully"
        else:
            validation_result["message"] = f"Phase {current_phase.value} validation failed. Fix issues before proceeding."
            validation_result["override_warning"] = "Use override=True to force proceed (NOT RECOMMENDED)"
        
        self._save_state()
        return validation_result
    
    def _check_deliverables(
        self, 
        project_id: str,
        phase: SDLCPhase,
        required_deliverables: List[str]
    ) -> List[Dict[str, Any]]:
        """Check if required deliverables exist"""
        
        project_dir = self.workspace / "projects" / project_id / phase.value
        results = []
        
        for deliverable in required_deliverables:
            path = project_dir / deliverable
            exists = path.exists() or path.with_suffix('').exists()
            
            results.append({
                "type": "deliverable",
                "name": deliverable,
                "passed": exists,
                "path": str(path),
                "message": "Found" if exists else f"Missing: {deliverable}"
            })
        
        return results
    
    def _check_quality_gates(
        self,
        project_id: str,
        phase: SDLCPhase,
        quality_gates: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check quality gates for the phase"""
        
        results = []
        project = self.projects[project_id]
        
        for gate, requirement in quality_gates.items():
            # Simulate gate checking (in real implementation, would call actual validators)
            passed = self._evaluate_gate(project, gate, requirement)
            
            results.append({
                "type": "quality_gate",
                "name": gate,
                "requirement": requirement,
                "passed": passed,
                "message": "Passed" if passed else f"Failed: {gate} not meeting requirement"
            })
        
        return results
    
    def _evaluate_gate(
        self,
        project: ProjectState,
        gate: str,
        requirement: Any
    ) -> bool:
        """Evaluate a specific quality gate"""
        
        # Special handling for knowledge system check
        if gate == "knowledge_queried":
            return len(project.knowledge_queries) > 0
        
        # For boolean requirements, default to False (must be explicitly set)
        if isinstance(requirement, bool):
            return False  # In real implementation, would check actual state
        
        # For numeric requirements (like code coverage)
        if isinstance(requirement, (int, float)):
            return False  # In real implementation, would check actual metrics
        
        return False
    
    def proceed_to_next_phase(
        self,
        project_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """Move to next phase if current is validated"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        # Validate current phase first
        if not force:
            validation = self.validate_phase(project_id)
            if not validation["can_proceed"]:
                return {
                    "status": "error",
                    "message": "Current phase not validated. Fix issues or use force=True",
                    "validation_result": validation
                }
        
        # Find next phase
        phases = list(SDLCPhase)
        current_index = phases.index(project.current_phase)
        
        if current_index >= len(phases) - 1:
            return {
                "status": "info",
                "message": "Already in final phase (PRODUCTION)"
            }
        
        # Move to next phase
        project.completed_phases.append(project.current_phase)
        project.current_phase = phases[current_index + 1]
        project.last_updated = datetime.now().isoformat()
        
        # Create rollback point
        project.rollback_points.append({
            "phase": phases[current_index].value,
            "timestamp": datetime.now().isoformat(),
            "artifacts": project.phase_artifacts.get(phases[current_index].value, [])
        })
        
        # Generate new checklist
        new_checklist = self._generate_phase_checklist(
            project_id,
            project.current_phase
        )
        
        self._save_state()
        
        return {
            "status": "success",
            "message": f"Proceeded to {project.current_phase.value} phase",
            "project_id": project_id,
            "previous_phase": phases[current_index].value,
            "current_phase": project.current_phase.value,
            "next_steps": new_checklist,
            "completed_phases": [p.value for p in project.completed_phases]
        }
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get current status of a project"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        # Calculate overall progress
        total_phases = len(SDLCPhase)
        completed = len(project.completed_phases)
        progress = (completed / total_phases) * 100
        
        # Get current phase requirements
        current_requirements = self.PHASE_REQUIREMENTS[project.current_phase]
        
        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project.project_name,
            "description": project.description,
            "current_phase": project.current_phase.value,
            "completed_phases": [p.value for p in project.completed_phases],
            "overall_progress": f"{progress:.1f}%",
            "quality_scores": project.quality_scores,
            "started_at": project.started_at,
            "last_updated": project.last_updated,
            "current_requirements": {
                "deliverables": current_requirements.required_deliverables,
                "quality_gates": current_requirements.quality_gates
            },
            "rollback_points": len(project.rollback_points),
            "knowledge_queries": len(project.knowledge_queries),
            "risks_identified": len(project.risks_identified)
        }
    
    def record_knowledge_query(
        self,
        project_id: str,
        query: str,
        results: List[str]
    ) -> Dict[str, Any]:
        """Record that knowledge system was queried"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        project.knowledge_queries.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results_count": len(results),
            "results_summary": results[:3]  # Store first 3 results
        })
        
        self._save_state()
        
        return {
            "status": "success",
            "message": "Knowledge query recorded",
            "total_queries": len(project.knowledge_queries)
        }
    
    def add_risk(
        self,
        project_id: str,
        risk_description: str,
        impact: str,
        mitigation: str
    ) -> Dict[str, Any]:
        """Add identified risk to project"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        project.risks_identified.append({
            "timestamp": datetime.now().isoformat(),
            "description": risk_description,
            "impact": impact,
            "mitigation": mitigation,
            "status": "identified"
        })
        
        self._save_state()
        
        return {
            "status": "success",
            "message": "Risk recorded",
            "total_risks": len(project.risks_identified)
        }
    
    def rollback_phase(self, project_id: str) -> Dict[str, Any]:
        """Rollback to previous phase"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        if not project.completed_phases:
            return {
                "status": "error",
                "message": "No completed phases to rollback to"
            }
        
        # Rollback to last completed phase
        previous_phase = project.completed_phases.pop()
        current_phase = project.current_phase
        project.current_phase = previous_phase
        project.last_updated = datetime.now().isoformat()
        
        self._save_state()
        
        return {
            "status": "success",
            "message": f"Rolled back from {current_phase.value} to {previous_phase.value}",
            "current_phase": previous_phase.value,
            "rolled_back_from": current_phase.value
        }
    
    def generate_report(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive SDLC compliance report"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        # Calculate metrics
        total_phases = len(SDLCPhase)
        completed = len(project.completed_phases)
        
        # Quality score average
        avg_quality = (
            sum(project.quality_scores.values()) / len(project.quality_scores)
            if project.quality_scores else 0
        )
        
        # Time analysis
        started = datetime.fromisoformat(project.started_at)
        now = datetime.now()
        duration = (now - started).days
        
        report = {
            "project_id": project_id,
            "project_name": project.project_name,
            "executive_summary": {
                "status": project.current_phase.value,
                "progress": f"{(completed/total_phases)*100:.1f}%",
                "quality_score": f"{avg_quality:.2f}",
                "duration_days": duration,
                "compliance": "COMPLIANT" if avg_quality > 0.8 else "AT RISK"
            },
            "phase_details": {
                "completed": [p.value for p in project.completed_phases],
                "current": project.current_phase.value,
                "quality_scores": project.quality_scores
            },
            "risk_summary": {
                "total_identified": len(project.risks_identified),
                "risks": project.risks_identified[:5]  # Top 5 risks
            },
            "knowledge_integration": {
                "queries_made": len(project.knowledge_queries),
                "last_query": (
                    project.knowledge_queries[-1] 
                    if project.knowledge_queries else None
                )
            },
            "recommendations": self._generate_recommendations(project),
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendations(self, project: ProjectState) -> List[str]:
        """Generate recommendations based on project state"""
        
        recommendations = []
        
        # Check knowledge queries
        if len(project.knowledge_queries) < 3:
            recommendations.append(
                "Increase knowledge system queries to leverage existing patterns"
            )
        
        # Check quality scores
        low_quality_phases = [
            phase for phase, score in project.quality_scores.items()
            if score < 0.8
        ]
        if low_quality_phases:
            recommendations.append(
                f"Improve quality in phases: {', '.join(low_quality_phases)}"
            )
        
        # Check risks
        if len(project.risks_identified) < 5:
            recommendations.append(
                "Conduct more thorough risk assessment"
            )
        
        # Check phase progression
        if project.current_phase == SDLCPhase.DEVELOPMENT and \
           SDLCPhase.DESIGN not in project.completed_phases:
            recommendations.append(
                "WARNING: Design phase was skipped - high risk of rework"
            )
        
        return recommendations


# MCP Tool Interface
def sdlc_enforcer_tool(action: str, **kwargs) -> Dict[str, Any]:
    """MCP Tool interface for SDLC Enforcer"""
    
    enforcer = SDLCEnforcer()
    
    actions = {
        "start_project": enforcer.start_project,
        "validate_phase": enforcer.validate_phase,
        "proceed_to_next_phase": enforcer.proceed_to_next_phase,
        "get_project_status": enforcer.get_project_status,
        "record_knowledge_query": enforcer.record_knowledge_query,
        "add_risk": enforcer.add_risk,
        "rollback_phase": enforcer.rollback_phase,
        "generate_report": enforcer.generate_report
    }
    
    if action not in actions:
        return {
            "status": "error",
            "message": f"Unknown action: {action}",
            "available_actions": list(actions.keys())
        }
    
    try:
        return actions[action](**kwargs)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing {action}: {str(e)}"
        }


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: sdlc_enforcer.py <action> [args...]")
        print("Actions: start_project, validate_phase, proceed_to_next_phase, get_project_status")
        sys.exit(1)
    
    action = sys.argv[1]
    
    # Parse additional arguments
    kwargs = {}
    for i in range(2, len(sys.argv), 2):
        if i + 1 < len(sys.argv):
            kwargs[sys.argv[i]] = sys.argv[i + 1]
    
    result = sdlc_enforcer_tool(action, **kwargs)
    print(json.dumps(result, indent=2))