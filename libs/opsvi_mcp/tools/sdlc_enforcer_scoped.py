#!/usr/bin/env python3
"""
Scoped SDLC Enforcer - Only enforces SDLC within project boundaries
Supports multiple concurrent projects without interfering with normal operations
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
import re

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
class ProjectScope:
    """Defines the scope/boundaries of SDLC enforcement"""
    project_id: str
    project_name: str
    root_path: str  # e.g., /home/opsvi/master_root/projects/context_intelligence
    subdirs: List[str]  # Subdirectories under control
    enforcement_level: str  # "strict", "advisory", "off"
    allowed_external_paths: List[str]  # Paths outside project that can be accessed
    phase_overrides: Dict[str, List[str]]  # Phase-specific path allowances

@dataclass
class SDLCProject:
    """Represents an SDLC-controlled project"""
    project_id: str
    project_name: str
    description: str
    scope: ProjectScope
    current_phase: SDLCPhase
    completed_phases: List[SDLCPhase]
    created_at: str
    last_updated: str
    is_active: bool  # Can be paused/resumed
    metadata: Dict[str, Any]

class ScopedSDLCEnforcer:
    """
    Scoped SDLC Enforcer that only controls specific project paths
    Allows multiple concurrent projects and normal operations outside project scope
    """
    
    def __init__(self, workspace_dir: str = "/home/opsvi/master_root"):
        self.workspace = Path(workspace_dir)
        self.state_file = self.workspace / ".proj-intel" / "sdlc_scoped_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load all projects
        self.projects: Dict[str, SDLCProject] = self._load_projects()
        
        # Track which paths are under SDLC control
        self.controlled_paths: Dict[str, str] = {}  # path -> project_id mapping
        self._rebuild_path_index()
    
    def _load_projects(self) -> Dict[str, SDLCProject]:
        """Load all SDLC projects from state file"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                projects = {}
                for pid, pdata in data.items():
                    # Reconstruct scope
                    scope_data = pdata.pop('scope')
                    scope = ProjectScope(**scope_data)
                    
                    # Reconstruct phases
                    pdata['current_phase'] = SDLCPhase(pdata['current_phase'])
                    pdata['completed_phases'] = [
                        SDLCPhase(p) for p in pdata['completed_phases']
                    ]
                    
                    projects[pid] = SDLCProject(scope=scope, **pdata)
                return projects
        return {}
    
    def _save_projects(self):
        """Save all projects to state file"""
        data = {}
        for pid, project in self.projects.items():
            pdict = asdict(project)
            # Convert enums to strings for JSON
            pdict['current_phase'] = project.current_phase.value
            pdict['completed_phases'] = [p.value for p in project.completed_phases]
            data[pid] = pdict
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _rebuild_path_index(self):
        """Rebuild the index of controlled paths"""
        self.controlled_paths.clear()
        
        for project_id, project in self.projects.items():
            if not project.is_active:
                continue
                
            # Add root path
            self.controlled_paths[project.scope.root_path] = project_id
            
            # Add subdirectories
            root = Path(project.scope.root_path)
            for subdir in project.scope.subdirs:
                path = str(root / subdir)
                self.controlled_paths[path] = project_id
    
    def create_project(
        self,
        project_name: str,
        description: str,
        root_path: Optional[str] = None,
        enforcement_level: str = "strict",
        auto_activate: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new SDLC-controlled project with defined scope
        """
        
        # Generate project ID
        project_id = hashlib.md5(
            f"{project_name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        # Determine root path
        if root_path:
            # Custom path provided
            project_root = Path(root_path)
        else:
            # Default to projects directory with sanitized name
            safe_name = re.sub(r'[^a-z0-9_-]', '_', project_name.lower())
            project_root = self.workspace / "projects" / safe_name
        
        # Create project structure
        project_root.mkdir(parents=True, exist_ok=True)
        
        # Define scope
        scope = ProjectScope(
            project_id=project_id,
            project_name=project_name,
            root_path=str(project_root),
            subdirs=[
                "discovery",
                "design", 
                "planning",
                "development",
                "testing",
                "deployment",
                "production",
                "docs",
                "src",
                "tests",
                "configs"
            ],
            enforcement_level=enforcement_level,
            allowed_external_paths=[
                str(self.workspace / "docs"),  # Can read/write to main docs
                str(self.workspace / ".proj-intel"),  # Can access project intelligence
                "/tmp"  # Temporary files
            ],
            phase_overrides={
                "discovery": ["docs", "discovery"],  # Only these subdirs in discovery
                "design": ["docs", "discovery", "design"],
                "planning": ["docs", "discovery", "design", "planning"],
                # Development and later phases have access to all subdirs
            }
        )
        
        # Create project
        project = SDLCProject(
            project_id=project_id,
            project_name=project_name,
            description=description,
            scope=scope,
            current_phase=SDLCPhase.DISCOVERY,
            completed_phases=[],
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            is_active=auto_activate,
            metadata={
                "creator": os.environ.get("USER", "unknown"),
                "enforcement_enabled": True,
                "validation_results": {},
                "knowledge_queries": []
            }
        )
        
        # Add to projects
        self.projects[project_id] = project
        self._save_projects()
        
        # Rebuild path index if active
        if auto_activate:
            self._rebuild_path_index()
        
        # Create phase directories
        for subdir in scope.subdirs:
            (project_root / subdir).mkdir(exist_ok=True)
        
        # Create initial requirements template
        reqs_file = project_root / "discovery" / "requirements.md"
        if not reqs_file.exists():
            reqs_file.write_text(f"""# {project_name} Requirements

## Project Scope
**Project ID**: {project_id}
**Root Path**: {project_root}
**Enforcement Level**: {enforcement_level}

## SDLC Phase: DISCOVERY

### Functional Requirements
- [ ] TODO: Define core functionality
- [ ] TODO: List user stories
- [ ] TODO: Specify acceptance criteria

### Non-Functional Requirements
- [ ] TODO: Performance requirements
- [ ] TODO: Security requirements
- [ ] TODO: Scalability requirements

### Dependencies
- [ ] TODO: External dependencies
- [ ] TODO: Internal dependencies

### Success Criteria
- [ ] TODO: Measurable success metrics

---
**Note**: This project is under SDLC enforcement. Code files cannot be created until Design phase is complete.
""")
        
        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project_name,
            "root_path": str(project_root),
            "current_phase": "discovery",
            "is_active": auto_activate,
            "enforcement_level": enforcement_level,
            "controlled_paths": [
                str(project_root / subdir) for subdir in scope.subdirs
            ],
            "message": (
                f"Project '{project_name}' created with scoped SDLC enforcement.\n"
                f"Enforcement is LIMITED to: {project_root}\n"
                f"Normal operations continue outside this path."
            )
        }
    
    def check_path_enforcement(
        self,
        file_path: str,
        operation: str = "write"
    ) -> Dict[str, Any]:
        """
        Check if a path is under SDLC enforcement and if operation is allowed
        
        Returns:
            - enforced: bool - Whether path is under SDLC control
            - allowed: bool - Whether operation is allowed
            - project_id: str - Which project controls this path (if any)
            - reason: str - Explanation
        """
        
        # Normalize path
        abs_path = str(Path(file_path).resolve())
        
        # Check if path is under any project's control
        project_id = None
        project = None
        
        # Find which project controls this path
        for controlled_path, pid in self.controlled_paths.items():
            if abs_path.startswith(controlled_path):
                project_id = pid
                project = self.projects.get(pid)
                break
        
        # Not under SDLC control - always allowed
        if not project_id or not project:
            return {
                "enforced": False,
                "allowed": True,
                "project_id": None,
                "reason": "Path not under SDLC control",
                "message": "Normal operation - proceed"
            }
        
        # Path is under SDLC control - check if active
        if not project.is_active:
            return {
                "enforced": False,
                "allowed": True,
                "project_id": project_id,
                "reason": "Project SDLC enforcement is paused",
                "message": "Project exists but enforcement is disabled"
            }
        
        # Check enforcement level
        if project.scope.enforcement_level == "off":
            return {
                "enforced": False,
                "allowed": True,
                "project_id": project_id,
                "reason": "Project enforcement level is 'off'",
                "message": "Tracking only, no restrictions"
            }
        
        # Check if path is in allowed external paths
        for allowed_path in project.scope.allowed_external_paths:
            if abs_path.startswith(allowed_path):
                return {
                    "enforced": True,
                    "allowed": True,
                    "project_id": project_id,
                    "reason": "Path is in allowed external paths",
                    "message": f"External path access permitted for {project.project_name}"
                }
        
        # Now check phase-specific restrictions
        current_phase = project.current_phase
        
        # Determine which subdirectory this is
        relative_path = Path(abs_path).relative_to(project.scope.root_path)
        target_subdir = relative_path.parts[0] if relative_path.parts else ""
        
        # Check phase overrides
        phase_overrides = project.scope.phase_overrides.get(current_phase.value, [])
        
        if phase_overrides:
            # Phase has specific directory restrictions
            if target_subdir not in phase_overrides:
                # Check if it's a code file
                if abs_path.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c')):
                    return {
                        "enforced": True,
                        "allowed": False,
                        "project_id": project_id,
                        "reason": f"Code files not allowed in {current_phase.value} phase",
                        "message": (
                            f"Project '{project.project_name}' is in {current_phase.value} phase.\n"
                            f"Cannot write code to {target_subdir}/.\n"
                            f"Allowed directories: {', '.join(phase_overrides)}"
                        ),
                        "current_phase": current_phase.value,
                        "allowed_dirs": phase_overrides
                    }
        
        # Check operation type restrictions
        if operation in ["write", "create", "edit"]:
            # Writing restrictions based on phase
            if current_phase in [SDLCPhase.DISCOVERY, SDLCPhase.DESIGN]:
                # Check file type
                if abs_path.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c')):
                    advisory = project.scope.enforcement_level == "advisory"
                    
                    return {
                        "enforced": True,
                        "allowed": advisory,  # Advisory mode allows with warning
                        "project_id": project_id,
                        "reason": f"Code files restricted in {current_phase.value} phase",
                        "message": (
                            f"{'⚠️ WARNING' if advisory else '❌ BLOCKED'}: "
                            f"Project '{project.project_name}' is in {current_phase.value} phase.\n"
                            f"Code files should not be created until Development phase."
                        ),
                        "current_phase": current_phase.value,
                        "severity": "warning" if advisory else "error"
                    }
        
        # Default: allow the operation
        return {
            "enforced": True,
            "allowed": True,
            "project_id": project_id,
            "reason": "Operation allowed in current phase",
            "message": f"Proceeding with {operation} in {current_phase.value} phase",
            "current_phase": current_phase.value
        }
    
    def list_projects(self, active_only: bool = False) -> Dict[str, Any]:
        """List all SDLC projects and their status"""
        
        projects_list = []
        
        for project_id, project in self.projects.items():
            if active_only and not project.is_active:
                continue
            
            projects_list.append({
                "project_id": project_id,
                "project_name": project.project_name,
                "root_path": project.scope.root_path,
                "current_phase": project.current_phase.value,
                "is_active": project.is_active,
                "enforcement_level": project.scope.enforcement_level,
                "completed_phases": [p.value for p in project.completed_phases],
                "created_at": project.created_at,
                "controlled_paths_count": len(project.scope.subdirs)
            })
        
        # Show which paths are currently controlled
        controlled_summary = {}
        for path, pid in self.controlled_paths.items():
            if pid not in controlled_summary:
                controlled_summary[pid] = []
            controlled_summary[pid].append(path)
        
        return {
            "status": "success",
            "total_projects": len(self.projects),
            "active_projects": sum(1 for p in self.projects.values() if p.is_active),
            "projects": projects_list,
            "controlled_paths": controlled_summary,
            "message": (
                f"{len(projects_list)} projects found. "
                f"{sum(1 for p in projects_list if p['is_active'])} active."
            )
        }
    
    def toggle_project(self, project_id: str, activate: Optional[bool] = None) -> Dict[str, Any]:
        """
        Activate/deactivate SDLC enforcement for a project
        This allows temporarily disabling enforcement without losing state
        """
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        # Toggle or set explicitly
        if activate is None:
            project.is_active = not project.is_active
        else:
            project.is_active = activate
        
        self._save_projects()
        self._rebuild_path_index()
        
        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project.project_name,
            "is_active": project.is_active,
            "enforcement_level": project.scope.enforcement_level,
            "message": (
                f"Project '{project.project_name}' SDLC enforcement is now "
                f"{'ACTIVE' if project.is_active else 'PAUSED'}.\n"
                f"Controlled paths: {project.scope.root_path}"
            )
        }
    
    def validate_phase(self, project_id: str) -> Dict[str, Any]:
        """Validate current phase requirements"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        current_phase = project.current_phase
        project_root = Path(project.scope.root_path)
        
        validation_results = []
        all_passed = True
        
        # Phase-specific validation
        if current_phase == SDLCPhase.DISCOVERY:
            # Check requirements
            reqs_file = project_root / "discovery" / "requirements.md"
            if reqs_file.exists():
                content = reqs_file.read_text()
                has_todos = "TODO:" in content
                validation_results.append({
                    "check": "Requirements Complete",
                    "passed": not has_todos,
                    "message": "Requirements have TODOs" if has_todos else "Requirements complete"
                })
                all_passed = all_passed and not has_todos
            else:
                validation_results.append({
                    "check": "Requirements Document",
                    "passed": False,
                    "message": "Requirements document not found"
                })
                all_passed = False
            
            # Check knowledge queries
            has_knowledge = len(project.metadata.get("knowledge_queries", [])) > 0
            validation_results.append({
                "check": "Knowledge System Queried",
                "passed": has_knowledge,
                "message": "Knowledge queried" if has_knowledge else "No knowledge queries recorded"
            })
            all_passed = all_passed and has_knowledge
        
        elif current_phase == SDLCPhase.DESIGN:
            # Check architecture document
            arch_file = project_root / "design" / "architecture_design.md"
            validation_results.append({
                "check": "Architecture Design",
                "passed": arch_file.exists(),
                "message": "Found" if arch_file.exists() else "Missing architecture design"
            })
            all_passed = all_passed and arch_file.exists()
        
        # Store validation results
        project.metadata["validation_results"][current_phase.value] = {
            "timestamp": datetime.now().isoformat(),
            "passed": all_passed,
            "checks": validation_results
        }
        self._save_projects()
        
        return {
            "status": "success" if all_passed else "failed",
            "project_id": project_id,
            "project_name": project.project_name,
            "current_phase": current_phase.value,
            "validation_passed": all_passed,
            "results": validation_results,
            "can_proceed": all_passed,
            "message": (
                f"Phase {current_phase.value} validation "
                f"{'PASSED ✅' if all_passed else 'FAILED ❌'}"
            )
        }
    
    def proceed_to_next_phase(
        self,
        project_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """Move project to next SDLC phase"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        # Validate current phase
        if not force:
            validation = self.validate_phase(project_id)
            if not validation["validation_passed"]:
                return {
                    "status": "error",
                    "message": "Current phase validation failed",
                    "validation": validation,
                    "hint": "Fix validation issues or use force=True to override"
                }
        
        # Get next phase
        phases = list(SDLCPhase)
        current_index = phases.index(project.current_phase)
        
        if current_index >= len(phases) - 1:
            return {
                "status": "info",
                "message": "Already in final phase (PRODUCTION)"
            }
        
        # Move to next phase
        next_phase = phases[current_index + 1]
        project.completed_phases.append(project.current_phase)
        project.current_phase = next_phase
        project.last_updated = datetime.now().isoformat()
        
        # Update phase overrides if entering development
        if next_phase == SDLCPhase.DEVELOPMENT:
            # Remove directory restrictions for development
            project.scope.phase_overrides[next_phase.value] = []
        
        self._save_projects()
        
        return {
            "status": "success",
            "project_id": project_id,
            "project_name": project.project_name,
            "previous_phase": phases[current_index].value,
            "current_phase": next_phase.value,
            "message": (
                f"Project '{project.project_name}' advanced to {next_phase.value} phase.\n"
                f"{'🔓 Code writing now ENABLED!' if next_phase == SDLCPhase.DEVELOPMENT else ''}"
            ),
            "unlocked_capabilities": self._get_phase_capabilities(next_phase)
        }
    
    def _get_phase_capabilities(self, phase: SDLCPhase) -> List[str]:
        """Get capabilities unlocked in a phase"""
        
        capabilities = {
            SDLCPhase.DISCOVERY: ["Read files", "Search code", "Query knowledge", "Write documentation"],
            SDLCPhase.DESIGN: ["Create diagrams", "Write specifications", "Design APIs"],
            SDLCPhase.PLANNING: ["Create plans", "Define tests", "Setup CI/CD configs"],
            SDLCPhase.DEVELOPMENT: ["Write code", "Create tests", "Refactor", "All file operations"],
            SDLCPhase.TESTING: ["Run tests", "Performance testing", "Security scanning"],
            SDLCPhase.DEPLOYMENT: ["Build containers", "Deploy", "Configure monitoring"],
            SDLCPhase.PRODUCTION: ["All operations", "Monitoring", "Maintenance"]
        }
        
        return capabilities.get(phase, [])
    
    def record_knowledge_query(
        self,
        project_id: str,
        query: str,
        results_count: int = 0
    ) -> Dict[str, Any]:
        """Record that knowledge system was queried for a project"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        if "knowledge_queries" not in project.metadata:
            project.metadata["knowledge_queries"] = []
        
        project.metadata["knowledge_queries"].append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results_count": results_count,
            "phase": project.current_phase.value
        })
        
        self._save_projects()
        
        return {
            "status": "success",
            "message": "Knowledge query recorded",
            "total_queries": len(project.metadata["knowledge_queries"])
        }
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get detailed status of a project"""
        
        if project_id not in self.projects:
            return {
                "status": "error",
                "message": f"Project {project_id} not found"
            }
        
        project = self.projects[project_id]
        
        # Calculate progress
        total_phases = len(SDLCPhase)
        completed = len(project.completed_phases)
        progress = (completed / total_phases) * 100
        
        return {
            "status": "success",
            "project": {
                "id": project_id,
                "name": project.project_name,
                "description": project.description,
                "root_path": project.scope.root_path,
                "is_active": project.is_active,
                "enforcement_level": project.scope.enforcement_level
            },
            "sdlc": {
                "current_phase": project.current_phase.value,
                "completed_phases": [p.value for p in project.completed_phases],
                "progress_percent": progress
            },
            "scope": {
                "controlled_directories": project.scope.subdirs,
                "allowed_external_paths": project.scope.allowed_external_paths,
                "phase_restrictions": project.scope.phase_overrides.get(
                    project.current_phase.value, []
                )
            },
            "metrics": {
                "knowledge_queries": len(project.metadata.get("knowledge_queries", [])),
                "validation_attempts": len(project.metadata.get("validation_results", {})),
                "days_active": (
                    datetime.now() - datetime.fromisoformat(project.created_at)
                ).days
            },
            "message": (
                f"Project '{project.project_name}' is {progress:.0f}% complete.\n"
                f"Currently in {project.current_phase.value} phase.\n"
                f"Enforcement: {'ACTIVE' if project.is_active else 'PAUSED'}"
            )
        }


# MCP Tool Interface
def scoped_sdlc_tool(action: str, **kwargs) -> Dict[str, Any]:
    """MCP Tool interface for Scoped SDLC Enforcer"""
    
    enforcer = ScopedSDLCEnforcer()
    
    actions = {
        "create_project": enforcer.create_project,
        "check_path": enforcer.check_path_enforcement,
        "list_projects": enforcer.list_projects,
        "toggle_project": enforcer.toggle_project,
        "validate_phase": enforcer.validate_phase,
        "proceed_phase": enforcer.proceed_to_next_phase,
        "record_knowledge": enforcer.record_knowledge_query,
        "project_status": enforcer.get_project_status
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
        print("Scoped SDLC Enforcer - Project-specific enforcement")
        print("=" * 50)
        print("Usage: sdlc_enforcer_scoped.py <action> [args...]")
        print("\nActions:")
        print("  create_project <name> - Create new SDLC project")
        print("  list_projects - List all projects")
        print("  check_path <path> - Check if path is under SDLC")
        print("  toggle_project <id> - Toggle enforcement on/off")
        print("  validate_phase <id> - Validate current phase")
        print("  proceed_phase <id> - Move to next phase")
        print("  project_status <id> - Get project status")
        sys.exit(1)
    
    action = sys.argv[1]
    
    # Parse arguments
    kwargs = {}
    for i in range(2, len(sys.argv), 2):
        if i + 1 < len(sys.argv):
            key = sys.argv[i].lstrip('-')
            value = sys.argv[i + 1]
            # Try to parse as JSON for complex values
            try:
                kwargs[key] = json.loads(value)
            except:
                kwargs[key] = value
    
    result = scoped_sdlc_tool(action, **kwargs)
    print(json.dumps(result, indent=2))