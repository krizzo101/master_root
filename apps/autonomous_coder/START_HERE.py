#!/usr/bin/env python3
"""
Start the Autonomous Coder - One command to bootstrap everything
"""

import subprocess
import sys

def start_autonomous_coder():
    """
    Single command to start the research-driven autonomous coder
    """
    
    print("🚀 Starting Research-Driven Autonomous Coder")
    print("=" * 50)
    
    # The complete instruction for Claude
    BOOTSTRAP_COMMAND = """
    Build a research-driven autonomous coding system RIGHT HERE in this directory.
    
    Step 1: Research Current Technologies
    - Search for "Python async await best practices 2024 2025"
    - Search for "Python testing frameworks 2024 pytest alternatives"
    - Search for "Python package management 2024 poetry vs pip"
    
    Step 2: Create the System
    Based on your research, create:
    
    autonomous_coder.py with this structure:
    ```python
    import asyncio
    import subprocess
    from typing import Dict, Any
    
    class AutonomousCoder:
        def __init__(self):
            self.iteration = 0
            self.max_iterations = 50
            
        async def research(self, topic: str) -> Dict[str, Any]:
            # Research current information
            pass
            
        async def build(self, goal: str):
            # Main autonomous loop
            # 1. Research needed technologies
            # 2. Create plan based on research
            # 3. Implement with current best practices
            # 4. Test and validate
            # 5. Fix errors and continue
            pass
    ```
    
    Step 3: Implement Key Features
    - Research before choosing any technology
    - Use only verified current versions
    - Test everything automatically
    - Fix errors and continue until success
    
    Step 4: Test It
    Make it build a simple web app to prove it works.
    
    Start implementing now. Make it work, make it good.
    """
    
    # Execute via Claude
    try:
        result = subprocess.run(
            ["claude", "--dangerously-skip-permissions", "-p", BOOTSTRAP_COMMAND],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print("✅ Bootstrap command executed!")
        print("\nOutput:")
        print(result.stdout)
        
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏱️ Command is taking time... Claude is building your system.")
        print("Check this directory for the files being created.")
    except FileNotFoundError:
        print("❌ Claude CLI not found. Make sure 'claude' command is available.")
        print("\nAlternative: Copy the instruction above and run manually:")
        print("claude --dangerously-skip-permissions -p '<paste instruction>'")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    start_autonomous_coder()