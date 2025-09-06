#!/usr/bin/env python3
"""
Run Continuous Improvement Agent Session
Launch agents to enhance our tools and capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from continuous_improvement_framework import create_improvement_session
from src.generic_orchestrator import GenericOrchestrator

async def run_improvement_session(
    num_agents: int = 5,
    max_parallel: int = 3,
    output_dir: str = None
):
    """Run a continuous improvement session with multiple agents"""
    
    print("🚀 STARTING CONTINUOUS IMPROVEMENT SESSION")
    print(f"Agents: {num_agents} | Max Parallel: {max_parallel}")
    print("=" * 60)
    
    # Create improvement session
    session_info = create_improvement_session(num_agents, output_dir)
    
    print(f"✅ Generated {len(session_info['tasks'])} improvement tasks")
    print(f"📁 Output: {session_info['session_info']['output_dir']}")
    print(f"📊 Total sessions: {session_info['stats']['total_sessions']}")
    print(f"🎯 Focus areas: {session_info['stats']['categories_worked']}")
    print()
    
    # Setup orchestrator
    orchestrator_output = Path(session_info['session_info']['output_dir']) / "orchestrator_output"
    orchestrator = GenericOrchestrator(
        output_dir=orchestrator_output,
        max_parallel=max_parallel
    )
    
    # Convert improvement tasks to orchestrator format
    orchestrator_tasks = []
    for task in session_info['tasks']:
        orchestrator_task = {
            "task_id": task['task_id'],
            "task_type": task['task_type'],
            "prompt": task['prompt'],
            "context": task['context']
        }
        orchestrator_tasks.append(orchestrator_task)
    
    print("🎯 IMPROVEMENT CATEGORIES THIS SESSION:")
    for i, task in enumerate(session_info['tasks'], 1):
        print(f"  {i}. {task['context']['improvement_focus']} ({task['category']})")
    print()
    
    # Define result processor for improvement tasks
    async def process_improvement_results(tasks, results):
        """Process results from improvement agents"""
        print("\n" + "="*60)
        print("📈 IMPROVEMENT SESSION RESULTS")
        print("="*60)
        
        improvements_made = []
        knowledge_stored = []
        
        for task, result in zip(tasks, results):
            print(f"\n🔧 {task['context']['improvement_focus']}:")
            print(f"   Status: {'✅ Success' if result.get('success') else '❌ Failed'}")
            
            if result.get('success'):
                # Extract improvements from result
                if 'improvements' in result:
                    improvements_made.extend(result['improvements'])
                
                # Track knowledge stored
                if 'knowledge_stored' in result:
                    knowledge_stored.extend(result['knowledge_stored'])
                    
                print(f"   📝 Output: {result.get('summary', 'No summary available')}")
            else:
                print(f"   ⚠️  Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n📊 SESSION SUMMARY:")
        print(f"   ✅ Successful improvements: {len([r for r in results if r.get('success')])}")
        print(f"   📚 Knowledge entries stored: {len(knowledge_stored)}")
        print(f"   🔧 Total enhancements made: {len(improvements_made)}")
        
        if improvements_made:
            print(f"\n🎉 KEY IMPROVEMENTS:")
            for imp in improvements_made[:5]:  # Show top 5
                print(f"   • {imp}")
        
        return {
            'improvements': improvements_made,
            'knowledge_stored': knowledge_stored,
            'success_count': len([r for r in results if r.get('success')])
        }
    
    # Run the orchestrator
    print("🚀 LAUNCHING IMPROVEMENT AGENTS...")
    print(f"📋 Debug logs: {orchestrator.log_file}")
    print()
    
    # Convert tasks to AgentTask objects
    from src.generic_orchestrator import AgentTask
    agent_tasks = []
    for task_data in orchestrator_tasks:
        agent_task = AgentTask(
            task_id=task_data['task_id'],
            task_type=task_data['task_type'],
            prompt=task_data['prompt'],
            context=task_data['context']
        )
        agent_tasks.append(agent_task)
    
    # Create task generator
    def task_generator():
        return agent_tasks
    
    try:
        results = await orchestrator.run(
            task_generator=task_generator,
            result_processor=process_improvement_results
        )
        
        print("\n" + "="*60) 
        print("🎉 CONTINUOUS IMPROVEMENT SESSION COMPLETE!")
        print("="*60)
        print(f"📁 Results saved to: {orchestrator_output}")
        print(f"📋 Debug logs: {orchestrator.log_file}")
        print(f"📈 Check improvement_sessions/ for session history")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Session failed: {e}")
        print(f"📋 Check debug logs: {orchestrator.log_file}")
        raise

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run continuous improvement agent session")
    parser.add_argument("--agents", type=int, default=5, help="Number of agents")
    parser.add_argument("--parallel", type=int, default=3, help="Max parallel agents")
    parser.add_argument("--output", type=str, help="Output directory")
    
    args = parser.parse_args()
    
    # Run the improvement session
    asyncio.run(run_improvement_session(
        num_agents=args.agents,
        max_parallel=args.parallel,
        output_dir=args.output
    ))

if __name__ == "__main__":
    main()