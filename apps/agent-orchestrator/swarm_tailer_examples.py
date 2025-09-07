#!/usr/bin/env python3
"""
Example usage patterns for the Enhanced Multi-Agent Log Tailer

This script demonstrates different ways to use the swarm log tailer
with various agent orchestrator workflows.
"""

import asyncio
import subprocess
import time
from pathlib import Path
import signal
import sys

class SwarmTailerExamples:
    """Example usage patterns for the swarm log tailer"""
    
    def __init__(self):
        self.tailer_path = Path(__file__).parent / "swarm_log_tailer.py"
        self.orchestrator_dir = Path(__file__).parent
        
    def example_1_basic_monitoring(self):
        """Example 1: Basic monitoring of agent-orchestrator logs"""
        print("🔍 Example 1: Basic Agent Orchestrator Monitoring")
        print("=" * 50)
        print()
        print("Command:")
        print(f"  {self.tailer_path}")
        print()
        print("This monitors the default *agent-orchestrator* pattern")
        print("Perfect for watching orchestrated multi-agent workflows")
        
    def example_2_custom_pattern(self):
        """Example 2: Custom pattern monitoring"""  
        print("🎯 Example 2: Custom Pattern Monitoring")
        print("=" * 50)
        print()
        print("Commands:")
        print(f"  {self.tailer_path} --pattern '*multi-agent*'")
        print(f"  {self.tailer_path} --pattern '*research*'")
        print(f"  {self.tailer_path} --pattern '*build*'")
        print()
        print("Use specific patterns to focus on particular types of work")
        
    def example_3_debug_session(self):
        """Example 3: Full debug monitoring"""
        print("🐛 Example 3: Full Debug Session")
        print("=" * 50) 
        print()
        print("Command:")
        print(f"  {self.tailer_path} --pattern '*' --include-historical | tee debug_session.log")
        print()
        print("Captures ALL agent activity including historical logs")
        print("Saves to file for later analysis")
        print("⚠️  Warning: Can be very busy with many agents!")
        
    def example_4_focused_project(self):
        """Example 4: Project-specific monitoring"""
        print("📁 Example 4: Project-Specific Monitoring")
        print("=" * 50)
        print()
        print("Command:")
        print(f"  {self.tailer_path} --pattern '*my-important-project*'")
        print()
        print("Filters to show only agents working on specific project")
        print("Useful for focused development work")
        
    async def example_5_live_demo(self):
        """Example 5: Live demonstration with orchestrator"""
        print("🎬 Example 5: Live Demo with Agent Orchestrator")  
        print("=" * 50)
        print()
        
        # Check if we can find a test orchestrator script
        test_script = self.orchestrator_dir / "test_basic_orchestrator.py"
        if test_script.exists():
            print("Found test orchestrator script!")
            print("This will:")
            print("1. Start the swarm log tailer in background")
            print("2. Run a test orchestrator workflow")  
            print("3. Show real-time agent swarm activity")
            print()
            
            response = input("Run live demo? (y/N): ").lower()
            if response == 'y':
                await self.run_live_demo(test_script)
        else:
            print("No test orchestrator script found.")
            print("Create a test workflow and run alongside:")
            print()
            print("Terminal 1:")
            print(f"  {self.tailer_path}")
            print()
            print("Terminal 2:")  
            print("  python3 your_orchestrator_workflow.py")
            
    async def run_live_demo(self, test_script: Path):
        """Run the actual live demo"""
        print("\n🚀 Starting live demo...")
        
        # Start log tailer in background
        print("Starting swarm log tailer...")
        tailer_proc = subprocess.Popen([
            "python3", str(self.tailer_path), "--pattern", "*test*"
        ])
        
        # Give tailer time to start
        await asyncio.sleep(2)
        
        try:
            print("Starting test orchestrator workflow...")
            
            # Start orchestrator test
            orch_proc = subprocess.Popen([
                "python3", str(test_script)
            ])
            
            print("🎭 Watch the terminal for swarm activity!")
            print("Press Ctrl+C to stop the demo")
            
            # Wait for orchestrator to complete or user interrupt
            while orch_proc.poll() is None:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
            
        finally:
            # Clean up processes
            print("Cleaning up...")
            try:
                tailer_proc.terminate()
                tailer_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tailer_proc.kill()
                
            try:
                if orch_proc.poll() is None:
                    orch_proc.terminate() 
                    orch_proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, UnboundLocalError):
                pass
                
        print("✅ Demo completed!")
        
    def example_6_integration_patterns(self):
        """Example 6: Integration with other tools"""
        print("🔗 Example 6: Integration Patterns")
        print("=" * 50)
        print()
        
        print("A. With existing chat monitor:")
        print("Terminal 1: ./swarm_log_tailer.py")
        print("Terminal 2: python3 /path/to/chat-monitor/monitor.py")
        print()
        
        print("B. With output analysis:")
        print(f"{self.tailer_path} | grep 'ERROR\\|FAILED\\|⚠️'")
        print()
        
        print("C. With log file capture:")
        print(f"{self.tailer_path} | tee agent_activity_$(date +%Y%m%d_%H%M%S).log")
        print()
        
        print("D. Focus on specific agents:")
        print(f"{self.tailer_path} | grep '\\[a1b2c3d4\\]'  # Filter to specific agent")
        
    def show_usage_tips(self):
        """Show practical usage tips"""
        print("💡 Usage Tips")
        print("=" * 50)
        print()
        
        print("🎯 Performance:")
        print("- Start with specific patterns, not '*'")
        print("- Use Ctrl+C for clean shutdown")
        print("- Monitor CPU usage with 100+ agents")
        print()
        
        print("🐝 Swarm Detection:")
        print("- Agents in same project = potential swarm")
        print("- Created within 5-minute window = active swarm")
        print("- Each swarm gets unique emoji icon")
        print()
        
        print("🎨 Visual Indicators:")
        print("- 👤 = User message")
        print("- 🤖 = Assistant response") 
        print("- ⚡ = Tool result")
        print("- 🔧 = Tool use")
        print("- Colors = Individual agent identity")
        print()
        
        print("🔍 Troubleshooting:")
        print("- No agents found? Check ~/.claude/projects exists")
        print("- Garbled colors? Ensure terminal supports ANSI")
        print("- Permission errors? Check file access")

def main():
    """Main demonstration menu"""
    examples = SwarmTailerExamples()
    
    print("🐝 Enhanced Multi-Agent Log Tailer - Examples")
    print("=" * 60)
    print()
    
    menu_options = [
        ("Basic Monitoring", examples.example_1_basic_monitoring),
        ("Custom Patterns", examples.example_2_custom_pattern),
        ("Debug Session", examples.example_3_debug_session),
        ("Project-Specific", examples.example_4_focused_project),
        ("Live Demo", examples.example_5_live_demo),
        ("Integration Patterns", examples.example_6_integration_patterns),
        ("Usage Tips", examples.show_usage_tips),
    ]
    
    while True:
        print("Select an example:")
        for i, (name, _) in enumerate(menu_options, 1):
            print(f"  {i}. {name}")
        print("  0. Exit")
        print()
        
        try:
            choice = input("Enter choice (0-{}): ".format(len(menu_options)))
            choice = int(choice)
            
            if choice == 0:
                print("👋 Goodbye!")
                break
            elif 1 <= choice <= len(menu_options):
                print("\n" + "=" * 60)
                name, func = menu_options[choice - 1]
                
                if asyncio.iscoroutinefunction(func):
                    asyncio.run(func())
                else:
                    func()
                    
                print("\n" + "=" * 60)
                input("\nPress Enter to continue...")
                print("\n" * 2)
            else:
                print("❌ Invalid choice. Try again.\n")
                
        except (ValueError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()