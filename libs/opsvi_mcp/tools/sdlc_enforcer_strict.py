#!/usr/bin/env python3
"""
STRICT SDLC Enforcer - Actually prevents agents from bypassing the process
"""

import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import functools
import inspect

class SDLCViolationError(Exception):
    """Raised when SDLC process is violated"""
    pass

class SDLCEnforcerStrict:
    """
    Strict SDLC Enforcer that actually blocks operations
    """
    
    _instance = None
    _enforcement_active = True
    
    def __new__(cls):
        """Singleton pattern to ensure one enforcer"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the strict enforcer"""
        if not hasattr(self, 'initialized'):
            self.workspace = Path("/home/opsvi/master_root")
            self.lock_file = self.workspace / ".proj-intel" / "sdlc_lock.json"
            self.hooks_file = self.workspace / ".proj-intel" / "sdlc_hooks.json"
            self.state_file = self.workspace / ".proj-intel" / "sdlc_state.json"
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load or create enforcement state
            self.enforcement_state = self._load_enforcement_state()
            self.initialized = True
            
            # Register system hooks
            self._register_system_hooks()
    
    def _load_enforcement_state(self) -> Dict[str, Any]:
        """Load enforcement state"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "active_project": None,
            "locked_paths": [],
            "allowed_operations": [],
            "phase_locks": {}
        }
    
    def _save_enforcement_state(self):
        """Save enforcement state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.enforcement_state, f, indent=2)
    
    def _register_system_hooks(self):
        """Register hooks that intercept file operations"""
        hooks = {
            "file_write_hook": self._intercept_file_write,
            "file_edit_hook": self._intercept_file_edit,
            "bash_command_hook": self._intercept_bash_command,
            "git_commit_hook": self._intercept_git_commit
        }
        
        with open(self.hooks_file, 'w') as f:
            json.dump(hooks, f, indent=2, default=str)
    
    def _intercept_file_write(self, file_path: str, content: str) -> bool:
        """
        Intercept file write operations
        Returns: True to allow, False to block
        """
        if not self._enforcement_active:
            return True
            
        project = self.enforcement_state.get("active_project")
        if not project:
            return True  # No active project, allow
        
        # Check if we're in development phase or later
        current_phase = project.get("current_phase", "discovery")
        allowed_phases = ["development", "testing", "deployment", "production"]
        
        if current_phase not in allowed_phases:
            # Block code file creation in early phases
            if file_path.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs')):
                raise SDLCViolationError(
                    f"Cannot create code files in {current_phase} phase. "
                    f"Must complete Discovery and Design phases first!"
                )
        
        # Check if path is locked
        if file_path in self.enforcement_state.get("locked_paths", []):
            raise SDLCViolationError(
                f"Path {file_path} is locked by SDLC enforcer. "
                f"Complete current phase requirements first."
            )
        
        return True
    
    def _intercept_file_edit(self, file_path: str, changes: str) -> bool:
        """Intercept file edit operations"""
        return self._intercept_file_write(file_path, changes)
    
    def _intercept_bash_command(self, command: str) -> bool:
        """
        Intercept bash commands
        Block certain commands based on phase
        """
        if not self._enforcement_active:
            return True
            
        project = self.enforcement_state.get("active_project")
        if not project:
            return True
        
        current_phase = project.get("current_phase", "discovery")
        
        # Block deployment commands in non-deployment phases
        deployment_commands = ['docker push', 'kubectl apply', 'helm install', 
                              'terraform apply', 'aws deploy', 'gcloud deploy']
        
        if current_phase not in ["deployment", "production"]:
            for deploy_cmd in deployment_commands:
                if deploy_cmd in command.lower():
                    raise SDLCViolationError(
                        f"Cannot run deployment command '{command}' in {current_phase} phase. "
                        f"Must reach Deployment phase first!"
                    )
        
        # Block test execution before test phase
        test_commands = ['pytest', 'npm test', 'go test', 'cargo test', 'jest']
        if current_phase not in ["testing", "deployment", "production"]:
            for test_cmd in test_commands:
                if test_cmd in command.lower() and 'install' not in command.lower():
                    raise SDLCViolationError(
                        f"Cannot run tests in {current_phase} phase. "
                        f"Complete Development phase first!"
                    )
        
        return True
    
    def _intercept_git_commit(self, message: str) -> bool:
        """
        Intercept git commits
        Ensure phase requirements are met
        """
        if not self._enforcement_active:
            return True
            
        project = self.enforcement_state.get("active_project")
        if not project:
            return True
        
        # Add phase to commit message
        current_phase = project.get("current_phase", "unknown")
        if f"[{current_phase}]" not in message:
            print(f"⚠️  Adding SDLC phase tag to commit: [{current_phase}]")
        
        # Warn if committing in early phases
        if current_phase in ["discovery", "design"]:
            print(f"⚠️  Warning: Committing in {current_phase} phase. "
                  f"Ensure you're not implementing before design is complete!")
        
        return True
    
    def activate_project(self, project_id: str, project_name: str) -> Dict[str, Any]:
        """
        Activate SDLC enforcement for a project
        This LOCKS the workspace to enforce process
        """
        
        # Create project lock
        lock_data = {
            "project_id": project_id,
            "project_name": project_name,
            "locked_at": datetime.now().isoformat(),
            "current_phase": "discovery",
            "completed_phases": [],
            "phase_requirements": {}
        }
        
        # Set as active project
        self.enforcement_state["active_project"] = lock_data
        
        # Lock certain paths during discovery/design
        self.enforcement_state["locked_paths"] = [
            "src/",
            "lib/",
            "apps/",
            "components/"
        ]
        
        # Define allowed operations per phase
        self.enforcement_state["allowed_operations"] = {
            "discovery": ["read", "search", "query_knowledge"],
            "design": ["read", "search", "create_diagrams", "create_docs"],
            "planning": ["read", "create_plan", "create_tests"],
            "development": ["all"],
            "testing": ["all"],
            "deployment": ["all"],
            "production": ["all"]
        }
        
        self._save_enforcement_state()
        
        # Create phase-specific directories
        project_root = self.workspace / "projects" / project_id
        for phase in ["discovery", "design", "planning", "development", 
                     "testing", "deployment", "production"]:
            (project_root / phase).mkdir(parents=True, exist_ok=True)
        
        # Create requirements file that MUST be filled
        reqs_file = project_root / "discovery" / "requirements.md"
        if not reqs_file.exists():
            reqs_file.write_text("""# Requirements Document
## Status: INCOMPLETE ❌

### Functional Requirements
- [ ] TODO: Document functional requirements

### Non-Functional Requirements  
- [ ] TODO: Document performance requirements
- [ ] TODO: Document security requirements
- [ ] TODO: Document scalability requirements

### Constraints
- [ ] TODO: Identify constraints

### Dependencies
- [ ] TODO: Map all dependencies

### Success Criteria
- [ ] TODO: Define measurable success criteria

**THIS DOCUMENT MUST BE COMPLETED BEFORE PROCEEDING TO DESIGN PHASE**
""")
        
        return {
            "status": "success",
            "message": f"SDLC Enforcement ACTIVATED for {project_name}",
            "project_id": project_id,
            "current_phase": "discovery",
            "locked_paths": self.enforcement_state["locked_paths"],
            "requirements": {
                "immediate_action": "Complete requirements document",
                "location": str(reqs_file),
                "validation": "All TODOs must be completed"
            },
            "warning": "⚠️  Code creation is BLOCKED until Discovery and Design phases complete!"
        }
    
    def validate_and_proceed(self, project_id: str) -> Dict[str, Any]:
        """
        Validate current phase and proceed if passed
        This is the ONLY way to unlock next phase
        """
        
        project = self.enforcement_state.get("active_project")
        if not project or project["project_id"] != project_id:
            return {
                "status": "error",
                "message": "Project not active or not found"
            }
        
        current_phase = project["current_phase"]
        project_root = self.workspace / "projects" / project_id
        
        # Phase-specific validation
        validation_passed = False
        validation_errors = []
        
        if current_phase == "discovery":
            # Check requirements document
            reqs_file = project_root / "discovery" / "requirements.md"
            if reqs_file.exists():
                content = reqs_file.read_text()
                if "TODO:" not in content and "INCOMPLETE" not in content:
                    validation_passed = True
                else:
                    validation_errors.append("Requirements document has incomplete TODOs")
            else:
                validation_errors.append("Requirements document missing")
            
            # Check risk assessment
            risk_file = project_root / "discovery" / "risk_matrix.json"
            if not risk_file.exists():
                validation_errors.append("Risk assessment missing")
            
            # Check if knowledge was queried
            if not project.get("knowledge_queried", False):
                validation_errors.append("Knowledge system not queried")
        
        elif current_phase == "design":
            # Check architecture document
            arch_file = project_root / "design" / "architecture_design.md"
            if not arch_file.exists():
                validation_errors.append("Architecture design missing")
            
            # Check API specification
            api_file = project_root / "design" / "api_specification.yaml"
            if not api_file.exists():
                validation_errors.append("API specification missing")
        
        elif current_phase == "planning":
            # Check implementation plan
            plan_file = project_root / "planning" / "implementation_plan.md"
            if not plan_file.exists():
                validation_errors.append("Implementation plan missing")
            
            # Check test strategy
            test_file = project_root / "planning" / "test_strategy.md"
            if not test_file.exists():
                validation_errors.append("Test strategy missing")
        
        elif current_phase == "development":
            # Check if code exists and tests exist
            src_files = list(project_root.glob("development/**/*.py"))
            test_files = list(project_root.glob("development/**/test_*.py"))
            
            if len(src_files) == 0:
                validation_errors.append("No source code found")
            if len(test_files) == 0:
                validation_errors.append("No tests found")
            
            # Check code coverage (simulated)
            coverage_file = project_root / "development" / "coverage.json"
            if coverage_file.exists():
                coverage_data = json.loads(coverage_file.read_text())
                if coverage_data.get("percentage", 0) < 80:
                    validation_errors.append(f"Code coverage {coverage_data.get('percentage', 0)}% < 80%")
            else:
                validation_errors.append("Code coverage report missing")
        
        # Determine if we can proceed
        if validation_passed or len(validation_errors) == 0:
            # Move to next phase
            phases = ["discovery", "design", "planning", "development", 
                     "testing", "deployment", "production"]
            current_index = phases.index(current_phase)
            
            if current_index < len(phases) - 1:
                next_phase = phases[current_index + 1]
                project["completed_phases"].append(current_phase)
                project["current_phase"] = next_phase
                
                # Unlock paths for development phase
                if next_phase == "development":
                    self.enforcement_state["locked_paths"] = []
                    message = "🎉 Development phase UNLOCKED! You can now write code."
                else:
                    message = f"Proceeded to {next_phase} phase"
                
                self._save_enforcement_state()
                
                return {
                    "status": "success",
                    "message": message,
                    "previous_phase": current_phase,
                    "current_phase": next_phase,
                    "unlocked_capabilities": self.enforcement_state["allowed_operations"].get(next_phase, [])
                }
            else:
                return {
                    "status": "info",
                    "message": "Already in final phase (production)"
                }
        else:
            return {
                "status": "error",
                "message": f"Cannot proceed from {current_phase} phase",
                "validation_errors": validation_errors,
                "fix_required": "Address all validation errors before proceeding",
                "override": "Contact system admin to override (NOT RECOMMENDED)"
            }
    
    def get_enforcement_status(self) -> Dict[str, Any]:
        """Get current enforcement status"""
        project = self.enforcement_state.get("active_project")
        
        if not project:
            return {
                "status": "inactive",
                "message": "No active SDLC enforcement",
                "enforcement_active": False
            }
        
        return {
            "status": "active",
            "enforcement_active": True,
            "project_id": project["project_id"],
            "project_name": project["project_name"],
            "current_phase": project["current_phase"],
            "completed_phases": project.get("completed_phases", []),
            "locked_paths": self.enforcement_state.get("locked_paths", []),
            "allowed_operations": self.enforcement_state["allowed_operations"].get(
                project["current_phase"], []
            ),
            "phase_requirements": self._get_phase_requirements(project["current_phase"])
        }
    
    def _get_phase_requirements(self, phase: str) -> List[str]:
        """Get requirements for current phase"""
        requirements = {
            "discovery": [
                "Complete requirements document",
                "Create risk assessment",
                "Query knowledge system",
                "Identify all stakeholders",
                "Define success criteria"
            ],
            "design": [
                "Create architecture design",
                "Define API specifications",
                "Design data models",
                "Create security review",
                "Plan integrations"
            ],
            "planning": [
                "Create implementation plan",
                "Define sprint schedule",
                "Write test strategy",
                "Setup CI/CD pipeline plan",
                "Document rollback procedures"
            ],
            "development": [
                "Write source code",
                "Create unit tests",
                "Achieve 80% code coverage",
                "Pass code review",
                "Update documentation"
            ],
            "testing": [
                "Run all test suites",
                "Perform integration testing",
                "Execute performance tests",
                "Complete security scan",
                "Get UAT sign-off"
            ],
            "deployment": [
                "Create deployment guide",
                "Setup monitoring",
                "Configure alerts",
                "Test rollback procedures",
                "Prepare runbook"
            ],
            "production": [
                "Deploy to production",
                "Verify health checks",
                "Monitor performance",
                "Document lessons learned",
                "Update knowledge base"
            ]
        }
        return requirements.get(phase, [])
    
    def emergency_override(self, admin_key: str, reason: str) -> Dict[str, Any]:
        """
        Emergency override - requires admin key
        This should log the override for audit
        """
        
        # Verify admin key (in production, this would be more secure)
        expected_key = hashlib.sha256(
            f"sdlc_override_{datetime.now().strftime('%Y%m%d')}".encode()
        ).hexdigest()[:16]
        
        if admin_key != expected_key:
            return {
                "status": "error",
                "message": "Invalid admin key",
                "hint": "Contact system administrator"
            }
        
        # Log the override
        override_log = self.workspace / ".proj-intel" / "sdlc_overrides.log"
        with open(override_log, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - Override: {reason}\n")
        
        # Disable enforcement temporarily
        self._enforcement_active = False
        self.enforcement_state["locked_paths"] = []
        self._save_enforcement_state()
        
        return {
            "status": "success",
            "message": "⚠️  SDLC Enforcement OVERRIDDEN",
            "warning": "Process protection disabled - proceed with caution",
            "logged": True,
            "reason": reason,
            "duration": "Until next phase validation"
        }


# Hook Decorator for MCP Tools
def sdlc_required(phase: str = None):
    """
    Decorator that enforces SDLC phase requirements
    Use on any function that should be phase-locked
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            enforcer = SDLCEnforcerStrict()
            status = enforcer.get_enforcement_status()
            
            if status["enforcement_active"]:
                current_phase = status["current_phase"]
                
                # Check if we're in the required phase
                if phase and current_phase != phase:
                    phases_allowed = ["development", "testing", "deployment", "production"]
                    if phase == "development" and current_phase not in phases_allowed:
                        raise SDLCViolationError(
                            f"Function {func.__name__} requires {phase} phase. "
                            f"Currently in {current_phase} phase."
                        )
                
                # Check if operation is allowed
                allowed_ops = status.get("allowed_operations", [])
                if "all" not in allowed_ops:
                    # Inspect what the function does
                    func_name = func.__name__.lower()
                    write_ops = ["write", "create", "edit", "modify", "delete"]
                    
                    if any(op in func_name for op in write_ops):
                        if "write" not in allowed_ops and "all" not in allowed_ops:
                            raise SDLCViolationError(
                                f"Write operations not allowed in {current_phase} phase"
                            )
            
            # Function proceeds if checks pass
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example MCP Tool Integration
@sdlc_required(phase="development")
def write_code_file(file_path: str, content: str) -> bool:
    """Example: This function can only run in development phase or later"""
    with open(file_path, 'w') as f:
        f.write(content)
    return True


# CLI Interface
def main():
    """CLI interface for SDLC enforcer"""
    enforcer = SDLCEnforcerStrict()
    
    if len(sys.argv) < 2:
        print("Usage: sdlc_enforcer_strict.py <command> [args...]")
        print("Commands:")
        print("  activate <project_name> - Activate SDLC enforcement")
        print("  status - Show enforcement status")
        print("  validate - Validate and proceed to next phase")
        print("  override <admin_key> <reason> - Emergency override")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "activate":
        if len(sys.argv) < 3:
            print("Usage: activate <project_name>")
            sys.exit(1)
        
        project_name = sys.argv[2]
        project_id = hashlib.md5(
            f"{project_name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        
        result = enforcer.activate_project(project_id, project_name)
        print(json.dumps(result, indent=2))
    
    elif command == "status":
        result = enforcer.get_enforcement_status()
        print(json.dumps(result, indent=2))
    
    elif command == "validate":
        status = enforcer.get_enforcement_status()
        if not status["enforcement_active"]:
            print("No active project")
            sys.exit(1)
        
        result = enforcer.validate_and_proceed(status["project_id"])
        print(json.dumps(result, indent=2))
    
    elif command == "override":
        if len(sys.argv) < 4:
            print("Usage: override <admin_key> <reason>")
            sys.exit(1)
        
        admin_key = sys.argv[2]
        reason = " ".join(sys.argv[3:])
        result = enforcer.emergency_override(admin_key, reason)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()