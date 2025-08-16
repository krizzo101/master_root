#!/usr/bin/env python3
"""
SDLC Hooks Integration - Shows how the enforcer intercepts MCP tool calls
"""

import json
from typing import Dict, Any, Callable
from functools import wraps
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sdlc_enforcer_strict import SDLCEnforcerStrict, SDLCViolationError

class SDLCMCPIntegration:
    """
    Integration layer between MCP tools and SDLC Enforcer
    This would be injected into the MCP runtime
    """
    
    def __init__(self):
        self.enforcer = SDLCEnforcerStrict()
        self.original_tools = {}
        self.intercept_enabled = True
    
    def wrap_mcp_tool(self, tool_name: str, original_tool: Callable) -> Callable:
        """
        Wrap an MCP tool with SDLC enforcement
        """
        
        @wraps(original_tool)
        def wrapped_tool(*args, **kwargs):
            # Get current enforcement status
            status = self.enforcer.get_enforcement_status()
            
            if not status["enforcement_active"]:
                # No active SDLC project, proceed normally
                return original_tool(*args, **kwargs)
            
            current_phase = status["current_phase"]
            allowed_ops = status.get("allowed_operations", [])
            
            # Check tool-specific restrictions
            restrictions = self._get_tool_restrictions(tool_name, current_phase)
            
            if restrictions["blocked"]:
                raise SDLCViolationError(
                    f"Tool '{tool_name}' is BLOCKED in {current_phase} phase.\n"
                    f"Reason: {restrictions['reason']}\n"
                    f"Required: Complete {restrictions['required_phase']} phase first."
                )
            
            if restrictions["warning"]:
                print(f"⚠️  SDLC Warning: {restrictions['warning']}")
            
            # Log the operation for audit
            self._log_operation(tool_name, current_phase, args, kwargs)
            
            # Special handling for specific tools
            if tool_name == "Write" and current_phase in ["discovery", "design"]:
                # Check if it's a documentation file
                file_path = kwargs.get("file_path", args[0] if args else "")
                if not file_path.endswith(('.md', '.txt', '.json', '.yaml', '.yml')):
                    raise SDLCViolationError(
                        f"Cannot write code files in {current_phase} phase.\n"
                        f"Only documentation files allowed.\n"
                        f"Complete Design phase to unlock code writing."
                    )
            
            elif tool_name == "Edit" and current_phase in ["discovery"]:
                # No editing code in discovery
                file_path = kwargs.get("file_path", args[0] if args else "")
                if file_path.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs')):
                    raise SDLCViolationError(
                        f"Cannot edit code files in Discovery phase.\n"
                        f"Focus on requirements gathering first."
                    )
            
            elif tool_name == "Bash":
                command = kwargs.get("command", args[0] if args else "")
                self._check_bash_command(command, current_phase)
            
            elif tool_name == "TodoWrite":
                # Inject SDLC phase into todos
                todos = kwargs.get("todos", [])
                for todo in todos:
                    if "content" in todo and "[SDLC:" not in todo["content"]:
                        todo["content"] = f"[SDLC:{current_phase}] {todo['content']}"
            
            # Proceed with the tool call
            try:
                result = original_tool(*args, **kwargs)
                
                # Post-process based on tool
                if tool_name == "knowledge_query" and current_phase == "discovery":
                    # Mark that knowledge was queried
                    project_id = status.get("project_id")
                    if project_id:
                        self._mark_knowledge_queried(project_id)
                
                return result
                
            except Exception as e:
                # Log failures for learning
                self._log_failure(tool_name, current_phase, str(e))
                raise
        
        return wrapped_tool
    
    def _get_tool_restrictions(self, tool_name: str, phase: str) -> Dict[str, Any]:
        """
        Define tool restrictions per phase
        """
        
        # Tools completely blocked in certain phases
        blocked_tools = {
            "discovery": {
                "blocked": ["NotebookEdit", "MultiEdit"],  # No code editing
                "warning": ["Write", "Edit"]  # Warn but allow for docs
            },
            "design": {
                "blocked": ["NotebookEdit"],  # No notebook editing yet
                "warning": ["Write", "Edit", "Bash"]  # Warn about premature coding
            },
            "planning": {
                "blocked": [],
                "warning": ["Write", "Edit"]  # Starting to allow more
            }
        }
        
        phase_restrictions = blocked_tools.get(phase, {"blocked": [], "warning": []})
        
        # Check if tool is blocked
        if tool_name in phase_restrictions["blocked"]:
            return {
                "blocked": True,
                "reason": f"{tool_name} not allowed in {phase} phase",
                "required_phase": self._get_required_phase(tool_name),
                "warning": None
            }
        
        # Check if we should warn
        warning = None
        if tool_name in phase_restrictions["warning"]:
            warning = f"Using {tool_name} in {phase} phase - ensure it's for documentation only"
        
        return {
            "blocked": False,
            "reason": None,
            "required_phase": None,
            "warning": warning
        }
    
    def _get_required_phase(self, tool_name: str) -> str:
        """Get the minimum phase required for a tool"""
        
        tool_requirements = {
            "NotebookEdit": "development",
            "MultiEdit": "development",
            "pytest": "testing",
            "docker": "deployment",
            "kubectl": "deployment"
        }
        
        return tool_requirements.get(tool_name, "development")
    
    def _check_bash_command(self, command: str, phase: str):
        """Check if bash command is allowed in current phase"""
        
        # Commands that indicate premature activity
        phase_commands = {
            "discovery": {
                "blocked": ["python", "node", "npm run", "cargo", "go run"],
                "allowed": ["grep", "find", "ls", "cat", "echo", "mkdir"]
            },
            "design": {
                "blocked": ["pytest", "npm test", "cargo test", "docker build"],
                "allowed": ["python", "node", "echo", "cat"]
            },
            "planning": {
                "blocked": ["docker push", "kubectl apply", "helm install"],
                "allowed": ["python", "npm", "pip"]
            }
        }
        
        restrictions = phase_commands.get(phase, {"blocked": [], "allowed": []})
        
        # Check for blocked commands
        for blocked in restrictions["blocked"]:
            if blocked in command.lower():
                # Check if it's actually blocked or just a warning case
                if "install" in command.lower() or "help" in command.lower():
                    print(f"⚠️  Note: Running '{blocked}' in {phase} phase")
                else:
                    raise SDLCViolationError(
                        f"Command '{blocked}' not allowed in {phase} phase.\n"
                        f"This indicates implementation before design.\n"
                        f"Complete {phase} phase requirements first."
                    )
    
    def _mark_knowledge_queried(self, project_id: str):
        """Mark that knowledge system was queried"""
        state_file = Path("/home/opsvi/master_root/.proj-intel/sdlc_state.json")
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            if "active_project" in state:
                state["active_project"]["knowledge_queried"] = True
                
                with open(state_file, 'w') as f:
                    json.dump(state, f, indent=2)
    
    def _log_operation(self, tool: str, phase: str, args: tuple, kwargs: dict):
        """Log operations for audit and learning"""
        log_file = Path("/home/opsvi/master_root/.proj-intel/sdlc_operations.log")
        
        log_entry = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "tool": tool,
            "phase": phase,
            "args_sample": str(args)[:100] if args else None,
            "kwargs_keys": list(kwargs.keys()) if kwargs else []
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _log_failure(self, tool: str, phase: str, error: str):
        """Log failures for pattern learning"""
        log_file = Path("/home/opsvi/master_root/.proj-intel/sdlc_failures.log")
        
        log_entry = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "tool": tool,
            "phase": phase,
            "error": error[:500]  # Truncate long errors
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")


# Example of how this would be integrated
def demonstrate_integration():
    """
    Demonstration of how the SDLC enforcer would work
    """
    
    print("=" * 60)
    print("SDLC ENFORCEMENT DEMONSTRATION")
    print("=" * 60)
    
    # Initialize the integration
    integration = SDLCMCPIntegration()
    enforcer = integration.enforcer
    
    # Simulate activating a project
    print("\n1. ACTIVATING SDLC ENFORCEMENT FOR NEW PROJECT")
    print("-" * 40)
    
    result = enforcer.activate_project("ctx_intel_001", "Context Intelligence System")
    print(f"✅ Project activated: {result['project_id']}")
    print(f"📍 Current phase: {result['current_phase']}")
    print(f"🔒 Locked paths: {result['locked_paths']}")
    print(f"⚠️  {result['warning']}")
    
    # Show what happens when trying to write code in discovery
    print("\n2. ATTEMPTING TO WRITE CODE IN DISCOVERY PHASE")
    print("-" * 40)
    
    def mock_write_tool(file_path: str, content: str):
        return f"Would write to {file_path}"
    
    # Wrap the tool
    wrapped_write = integration.wrap_mcp_tool("Write", mock_write_tool)
    
    # Try to write a Python file (should fail)
    try:
        wrapped_write(file_path="/home/opsvi/src/main.py", content="print('hello')")
    except SDLCViolationError as e:
        print(f"❌ BLOCKED: {e}")
    
    # Try to write a documentation file (should work with warning)
    print("\n3. WRITING DOCUMENTATION IN DISCOVERY PHASE")
    print("-" * 40)
    
    try:
        result = wrapped_write(
            file_path="/home/opsvi/docs/requirements.md", 
            content="# Requirements"
        )
        print(f"✅ Allowed: Documentation file created")
    except SDLCViolationError as e:
        print(f"❌ Blocked: {e}")
    
    # Show bash command filtering
    print("\n4. BASH COMMAND FILTERING")
    print("-" * 40)
    
    def mock_bash_tool(command: str):
        return f"Would run: {command}"
    
    wrapped_bash = integration.wrap_mcp_tool("Bash", mock_bash_tool)
    
    # Try to run tests in discovery (should fail)
    try:
        wrapped_bash(command="pytest tests/")
    except SDLCViolationError as e:
        print(f"❌ BLOCKED: {e}")
    
    # Try to search files (should work)
    try:
        result = wrapped_bash(command="grep -r 'TODO' .")
        print(f"✅ Allowed: Search command executed")
    except SDLCViolationError as e:
        print(f"❌ Blocked: {e}")
    
    # Show current status
    print("\n5. CURRENT ENFORCEMENT STATUS")
    print("-" * 40)
    
    status = enforcer.get_enforcement_status()
    print(f"📊 Status: {status['status']}")
    print(f"📍 Phase: {status['current_phase']}")
    print(f"🔒 Locked: {len(status['locked_paths'])} paths")
    print(f"✅ Allowed: {status['allowed_operations']}")
    
    print("\n" + "=" * 60)
    print("To proceed to next phase, requirements must be completed:")
    for req in status['phase_requirements']:
        print(f"  □ {req}")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_integration()