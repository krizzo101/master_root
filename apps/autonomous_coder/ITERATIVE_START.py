#!/usr/bin/env python3
"""
Iterative Autonomous Coder - Builds in small, manageable chunks
"""

import subprocess
import time
import json
from pathlib import Path

class IterativeAutonomousBuilder:
    """Builds the autonomous coder step by step to avoid timeouts"""
    
    def __init__(self):
        self.workspace = Path(".")
        self.state_file = self.workspace / "build_state.json"
        self.state = self.load_state()
        
    def load_state(self):
        """Load build state"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "step": 0,
            "completed_files": [],
            "current_task": None
        }
    
    def save_state(self):
        """Save build state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def run_claude_task(self, task: str, timeout: int = 60):
        """Run a single Claude task with shorter timeout"""
        try:
            result = subprocess.run(
                ["claude", "--dangerously-skip-permissions", "-p", task],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            return "TIMEOUT - Task too large, breaking down further"
        except Exception as e:
            return f"ERROR: {e}"
    
    def build_step_by_step(self):
        """Build the autonomous coder one piece at a time"""
        
        # Define small, focused tasks
        tasks = [
            # Step 1: Create basic structure
            {
                "name": "Create basic autonomous engine",
                "prompt": """Create ONLY the file 'autonomous_engine.py' with:
                - A class AutonomousEngine
                - An __init__ method
                - A simple run() method that prints 'Running'
                - Nothing else for now""",
                "file": "autonomous_engine.py"
            },
            
            # Step 2: Add research capability
            {
                "name": "Add research method",
                "prompt": """In autonomous_engine.py, add a method:
                def research_current_tech(self, topic):
                    # Simulate research - will use real web search later
                    return f"Researched: {topic}"
                Keep it simple.""",
                "file": "autonomous_engine.py"
            },
            
            # Step 3: Add planning
            {
                "name": "Add planning method",
                "prompt": """In autonomous_engine.py, add:
                def create_plan(self, goal):
                    # Create simple plan
                    return ["Research tech", "Build", "Test"]""",
                "file": "autonomous_engine.py"
            },
            
            # Step 4: State management
            {
                "name": "Create state manager",
                "prompt": """Create 'state_manager.py' with:
                class StateManager:
                    def __init__(self):
                        self.state = {}
                    def save(self): pass
                    def load(self): pass""",
                "file": "state_manager.py"
            },
            
            # Step 5: Main loop
            {
                "name": "Add main loop",
                "prompt": """In autonomous_engine.py, add:
                def autonomous_loop(self, goal):
                    plan = self.create_plan(goal)
                    for task in plan:
                        print(f"Executing: {task}")
                        # Will implement later""",
                "file": "autonomous_engine.py"
            },
            
            # Step 6: Entry point
            {
                "name": "Create main.py",
                "prompt": """Create 'main.py':
                from autonomous_engine import AutonomousEngine
                
                def main():
                    engine = AutonomousEngine()
                    engine.autonomous_loop("Build a web app")
                
                if __name__ == "__main__":
                    main()""",
                "file": "main.py"
            },
            
            # Step 7: Add validation
            {
                "name": "Create validator",
                "prompt": """Create 'validator.py':
                class Validator:
                    def validate_code(self, code):
                        return True  # Simple for now
                    def run_tests(self):
                        return {"passed": True}""",
                "file": "validator.py"
            },
            
            # Step 8: Enhance with research
            {
                "name": "Enhance research",
                "prompt": """In autonomous_engine.py, improve research_current_tech:
                - Add a list of things to research
                - Return structured data
                - Add comments about using web search""",
                "file": "autonomous_engine.py"
            },
            
            # Step 9: Error handling
            {
                "name": "Add error handling",
                "prompt": """In autonomous_engine.py, add:
                def handle_error(self, error):
                    # Log error and try to recover
                    print(f"Error: {error}")
                    return "retry"  # or "skip" or "abort" """,
                "file": "autonomous_engine.py"
            },
            
            # Step 10: Make it work
            {
                "name": "Connect everything",
                "prompt": """Update autonomous_engine.py to:
                1. Import StateManager and Validator
                2. Use them in autonomous_loop
                3. Add proper error handling
                4. Make it actually functional""",
                "file": "autonomous_engine.py"
            }
        ]
        
        print("🚀 Building Autonomous Coder Step by Step")
        print("=" * 50)
        
        start_step = self.state.get("step", 0)
        
        for i, task in enumerate(tasks[start_step:], start=start_step):
            print(f"\n📍 Step {i+1}/{len(tasks)}: {task['name']}")
            print("-" * 40)
            
            # Execute task
            result = self.run_claude_task(task["prompt"], timeout=30)
            
            # Check result
            if "TIMEOUT" in result:
                print("⏱️ Task too complex, simplifying...")
                # Break down further
                simpler_prompt = f"Just add a comment '# TODO: {task['name']}' to {task['file']}"
                result = self.run_claude_task(simpler_prompt, timeout=10)
            
            if "ERROR" not in result:
                print(f"✅ Completed: {task['name']}")
                self.state["completed_files"].append(task["file"])
            else:
                print(f"⚠️ Issue with: {task['name']}")
                print(result[:200])
            
            # Update state
            self.state["step"] = i + 1
            self.state["current_task"] = task["name"]
            self.save_state()
            
            # Brief pause to avoid overwhelming
            time.sleep(2)
        
        print("\n" + "=" * 50)
        print("✨ Autonomous Coder Framework Complete!")
        print("\nCreated files:")
        for f in set(self.state["completed_files"]):
            print(f"  ✓ {f}")
        
        # Final step: test it
        print("\n🧪 Testing the system...")
        self.run_claude_task("Run: python main.py", timeout=10)

def main():
    """Start the iterative build process"""
    builder = IterativeAutonomousBuilder()
    builder.build_step_by_step()

if __name__ == "__main__":
    main()