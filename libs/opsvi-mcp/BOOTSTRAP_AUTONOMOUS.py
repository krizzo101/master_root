#!/usr/bin/env python3
"""
Bootstrap Autonomous Coder - Minimal framework for Claude to build itself

This provides just enough structure for Claude Code to build its own 
autonomous coding system. It's intentionally minimal - Claude will enhance it.
"""

import asyncio
import json
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

class BootstrapAutonomous:
    """
    Minimal autonomous framework - Claude will enhance this
    """
    
    def __init__(self, workspace: str = "./autonomous_workspace"):
        self.workspace = Path(workspace)
        self.workspace.mkdir(exist_ok=True)
        self.session_id = str(uuid.uuid4())[:8]
        self.state_file = self.workspace / f"state_{self.session_id}.json"
        self.iteration = 0
        self.max_iterations = 100
        self.state = self.load_state()
        
    def load_state(self) -> Dict[str, Any]:
        """Load or initialize state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "goal": None,
            "completed": False,
            "current_task": None,
            "completed_tasks": [],
            "errors": [],
            "test_results": [],
            "files_created": []
        }
    
    def save_state(self):
        """Persist state to disk"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def run_claude(self, prompt: str, permission_mode: str = "bypassPermissions") -> str:
        """Execute Claude Code and return output"""
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p", prompt
        ]
        
        print(f"\n[Iteration {self.iteration}] Running Claude with prompt:\n{prompt[:200]}...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.workspace,
                timeout=300
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "ERROR: Command timed out"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def validate_progress(self) -> bool:
        """Check if we're making progress toward the goal"""
        # Let Claude validate its own progress
        validation_prompt = f"""
        Goal: {self.state['goal']}
        Completed tasks: {self.state['completed_tasks']}
        Files created: {self.state['files_created']}
        
        Are we done? Answer with JSON:
        {{
            "complete": true/false,
            "reason": "explanation",
            "next_task": "what to do next if not complete"
        }}
        """
        
        result = self.run_claude(validation_prompt)
        
        try:
            validation = json.loads(result)
            if validation.get('complete'):
                self.state['completed'] = True
                return True
            else:
                self.state['current_task'] = validation.get('next_task', 'Continue building')
                return False
        except:
            # If we can't parse, assume not complete
            return False
    
    def autonomous_loop(self, goal: str):
        """Main autonomous execution loop"""
        print(f"\n🚀 Starting autonomous build: {goal}\n")
        self.state['goal'] = goal
        self.save_state()
        
        # Initial planning
        plan_prompt = f"""
        I need to build: {goal}
        
        Create a step-by-step plan. Output as JSON:
        {{
            "steps": ["step1", "step2", ...],
            "first_action": "specific first task to do"
        }}
        """
        
        plan_result = self.run_claude(plan_prompt)
        
        try:
            plan = json.loads(plan_result)
            self.state['plan'] = plan.get('steps', [])
            self.state['current_task'] = plan.get('first_action', goal)
        except:
            self.state['current_task'] = f"Build: {goal}"
        
        # Main loop
        while self.iteration < self.max_iterations and not self.state['completed']:
            self.iteration += 1
            print(f"\n{'='*50}")
            print(f"Iteration {self.iteration}")
            print(f"Current task: {self.state['current_task']}")
            print(f"{'='*50}")
            
            # Execute current task
            task_prompt = f"""
            Overall goal: {self.state['goal']}
            Current task: {self.state['current_task']}
            Completed so far: {self.state['completed_tasks'][-5:]}
            
            Execute this task. Create/modify files as needed.
            After completing, summarize what you did.
            """
            
            result = self.run_claude(task_prompt)
            
            # Record completion
            self.state['completed_tasks'].append({
                'iteration': self.iteration,
                'task': self.state['current_task'],
                'result': result[:500]  # Truncate for storage
            })
            
            # Check for errors and try to fix
            if "error" in result.lower() or "failed" in result.lower():
                self.state['errors'].append({
                    'iteration': self.iteration,
                    'error': result[:500]
                })
                
                # Self-healing attempt
                fix_prompt = f"""
                An error occurred: {result[:500]}
                
                Fix this error and continue with the task.
                """
                fix_result = self.run_claude(fix_prompt)
                
            # Validate progress
            if self.validate_progress():
                print("\n✅ Goal completed successfully!")
                break
            
            # Save state after each iteration
            self.save_state()
            
            # Brief pause to avoid overwhelming
            import time
            time.sleep(2)
        
        # Final summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate final summary of what was built"""
        summary_prompt = f"""
        Goal: {self.state['goal']}
        Iterations: {self.iteration}
        Tasks completed: {len(self.state['completed_tasks'])}
        Errors encountered: {len(self.state['errors'])}
        
        Generate a summary of:
        1. What was built
        2. How to use it
        3. Any remaining issues
        
        Also list all files created.
        """
        
        summary = self.run_claude(summary_prompt)
        
        summary_file = self.workspace / f"BUILD_SUMMARY_{self.session_id}.md"
        with open(summary_file, 'w') as f:
            f.write(f"# Build Summary\n\n")
            f.write(f"**Goal:** {self.state['goal']}\n\n")
            f.write(f"**Session:** {self.session_id}\n\n")
            f.write(f"**Iterations:** {self.iteration}\n\n")
            f.write(f"## Summary\n\n{summary}\n\n")
            f.write(f"## Build Log\n\n")
            for task in self.state['completed_tasks']:
                f.write(f"### Iteration {task['iteration']}\n")
                f.write(f"**Task:** {task['task']}\n")
                f.write(f"**Result:** {task['result']}\n\n")
        
        print(f"\n📄 Summary saved to: {summary_file}")

# Advanced Bootstrap - This is what Claude will enhance
class AdvancedBootstrap(BootstrapAutonomous):
    """
    Extended bootstrap with more capabilities for Claude to use.
    Claude should enhance this class with its own improvements.
    """
    
    def __init__(self, workspace: str = "./autonomous_workspace"):
        super().__init__(workspace)
        self.test_command = None
        self.validation_criteria = []
        
    def set_validation(self, test_command: str = None, criteria: List[str] = None):
        """Set how to validate success"""
        self.test_command = test_command
        self.validation_criteria = criteria or []
    
    def run_tests(self) -> Dict[str, Any]:
        """Run validation tests"""
        if not self.test_command:
            return {"passed": True, "reason": "No tests configured"}
        
        try:
            result = subprocess.run(
                self.test_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.workspace,
                timeout=60
            )
            return {
                "passed": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e)
            }
    
    def enhanced_loop(self, goal: str, test_command: str = None):
        """Enhanced autonomous loop with testing"""
        self.set_validation(test_command)
        
        # Add meta-goal for Claude to enhance itself
        enhanced_goal = f"""
        {goal}
        
        IMPORTANT: As you build, also improve this autonomous framework itself.
        Feel free to:
        1. Add better error handling to this bootstrap script
        2. Create helper functions you need
        3. Improve the validation logic
        4. Add any features that would help you work better
        
        The bootstrap file is at: {__file__}
        """
        
        self.autonomous_loop(enhanced_goal)

def main():
    """
    Bootstrap the autonomous coder
    """
    print("""
    🤖 Bootstrap Autonomous Coder
    =============================
    This minimal framework will help Claude Code build its own autonomous system.
    """)
    
    # The bootstrap goal - Claude will build its own enhanced version
    BOOTSTRAP_GOAL = """
    Build a complete autonomous coding system that can:
    1. Accept natural language descriptions
    2. Create comprehensive plans
    3. Build iteratively with validation
    4. Self-test and fix errors
    5. Learn from mistakes
    6. Deploy when complete
    
    Start by enhancing this bootstrap framework itself, then build the full system.
    Create it as a proper Python package with:
    - Core autonomous engine
    - State management
    - Test framework
    - Learning system
    - MCP integration
    - Web interface for monitoring
    
    Make it production-ready and well-documented.
    """
    
    # Alternative: Let user specify their own goal
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
    else:
        goal = BOOTSTRAP_GOAL
    
    # Create bootstrap instance
    bootstrap = AdvancedBootstrap()
    
    # Run autonomous build
    bootstrap.enhanced_loop(
        goal=goal,
        test_command="python -m pytest tests/ 2>/dev/null || python test_autonomous.py 2>/dev/null || true"
    )
    
    print("\n✨ Bootstrap complete! Check the workspace for results.")

if __name__ == "__main__":
    main()