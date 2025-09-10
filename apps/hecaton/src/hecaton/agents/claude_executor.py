"""
Real Claude Code Executor using MCP Server
This is the ACTUAL implementation that spawns real Claude instances
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add libs to path for MCP access
sys.path.insert(0, "/home/opsvi/master_root/libs")

# Import the actual Claude Code MCP client
from opsvi_mcp.servers.claude_code import JobManager

@dataclass
class ClaudeAgent:
    """Represents a real Claude Code agent instance"""
    
    id: str
    task: str
    token: str
    worktree: Optional[Path] = None
    job_id: Optional[str] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


class RealClaudeExecutor:
    """
    Executes tasks using REAL Claude Code instances via MCP.
    This is not a simulation - it actually runs Claude Code.
    """
    
    def __init__(self, token_pool, worktree_manager):
        """Initialize with token pool and worktree manager"""
        self.token_pool = token_pool
        self.worktree_manager = worktree_manager
        self.job_manager = JobManager()
        self.active_agents: Dict[str, ClaudeAgent] = {}
        
    async def execute_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with a real Claude Code instance"""
        
        # Get resources
        token, token_idx = self.token_pool.acquire()
        worktree = self.worktree_manager.create(task["id"])
        
        # Create agent
        agent = ClaudeAgent(
            id=task["id"],
            task=task.get("prompt", task.get("description", "")),
            token=token,
            worktree=worktree
        )
        self.active_agents[agent.id] = agent
        
        try:
            # Prepare environment for Claude Code
            env = os.environ.copy()
            env["CLAUDE_CODE_TOKEN"] = token
            env["ANTHROPIC_API_KEY"] = ""  # Must be empty as instructed
            
            # Create the job using the actual MCP server
            job = self.job_manager.create_job(
                task=agent.task,
                cwd=str(worktree) if worktree else None,
                output_format="json",
                permission_mode="bypassPermissions",
                verbose=False
            )
            
            agent.job_id = job.id
            agent.status = "running"
            
            print(f"🤖 Agent {agent.id} started with job {job.id} using token {token_idx}")
            
            # Execute the job asynchronously
            await self.job_manager.execute_job_async(job)
            
            # Get the result
            result = self.job_manager.get_job_result(job.id)
            
            agent.status = "completed"
            agent.result = result
            
            print(f"✅ Agent {agent.id} completed successfully")
            
            return {
                "task_id": task["id"],
                "status": "completed",
                "agent_id": agent.id,
                "job_id": job.id,
                "result": result
            }
            
        except Exception as e:
            agent.status = "failed"
            print(f"❌ Agent {agent.id} failed: {e}")
            
            return {
                "task_id": task["id"],
                "status": "failed",
                "agent_id": agent.id,
                "error": str(e)
            }
            
        finally:
            # Cleanup worktree
            if worktree:
                self.worktree_manager.cleanup(task["id"])
                
    async def execute_parallel_tasks(
        self, 
        tasks: List[Dict[str, Any]], 
        max_parallel: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Execute multiple tasks in parallel with real Claude Code instances"""
        
        # Limit parallel execution to available tokens
        max_parallel = max_parallel or self.token_pool.get_token_count()
        
        print(f"\n🚀 Starting parallel execution of {len(tasks)} tasks with up to {max_parallel} agents")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def execute_with_semaphore(task):
            async with semaphore:
                return await self.execute_single_task(task)
        
        # Execute all tasks in parallel (limited by semaphore)
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": tasks[i]["id"],
                    "status": "failed",
                    "error": str(result)
                })
            else:
                processed_results.append(result)
                
        # Summary
        successful = sum(1 for r in processed_results if r.get("status") == "completed")
        failed = len(processed_results) - successful
        
        print(f"\n📊 Parallel execution complete: {successful}/{len(tasks)} successful, {failed} failed")
        
        return processed_results
        
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        agent = self.active_agents.get(agent_id)
        if not agent:
            return None
            
        return {
            "id": agent.id,
            "task": agent.task,
            "status": agent.status,
            "job_id": agent.job_id,
            "worktree": str(agent.worktree) if agent.worktree else None
        }
        
    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        return [self.get_agent_status(aid) for aid in self.active_agents.keys()]


class Phase2Orchestrator:
    """
    Phase 2 Orchestrator that uses REAL Claude Code instances
    with 5 parallel agents capability from Phase 1
    """
    
    def __init__(self, token_pool, worktree_manager):
        """Initialize with enhanced capabilities"""
        self.executor = RealClaudeExecutor(token_pool, worktree_manager)
        self.message_queue = asyncio.Queue()  # For inter-agent messaging
        self.agent_registry = {}  # For specialized agents
        
    async def run_phase_2_implementation(self):
        """
        Use 5 real Claude agents to implement Phase 2 features in parallel
        """
        
        # Define Phase 2 implementation tasks
        phase_2_tasks = [
            {
                "id": "agent-1-messaging",
                "prompt": """Create an inter-agent messaging system for HECATON in /home/opsvi/master_root/apps/hecaton/src/hecaton/messaging/

                Create message_broker.py with:
                - AsyncIO Queue-based message broker
                - Message routing between agents
                - Topic-based publish/subscribe
                - Message persistence and replay
                - Thread-safe operations
                
                Include comprehensive tests and documentation."""
            },
            {
                "id": "agent-2-registry",
                "prompt": """Create an agent registry system for HECATON in /home/opsvi/master_root/apps/hecaton/src/hecaton/agents/

                Create agent_registry.py with:
                - Agent registration and discovery
                - Agent capability tracking
                - Dynamic agent spawning
                - Health monitoring
                - Load balancing logic
                
                Include comprehensive tests and documentation."""
            },
            {
                "id": "agent-3-specialized",
                "prompt": """Create specialized agent types for HECATON in /home/opsvi/master_root/apps/hecaton/src/hecaton/agents/specialized/

                Create:
                - code_agent.py: For code generation/modification
                - research_agent.py: For documentation and research
                - test_agent.py: For test generation and execution
                - review_agent.py: For code review and quality checks
                
                Each with unique capabilities and interfaces."""
            },
            {
                "id": "agent-4-monitoring",
                "prompt": """Create performance monitoring for HECATON in /home/opsvi/master_root/apps/hecaton/src/hecaton/monitoring/

                Create performance_monitor.py with:
                - Real-time metrics collection
                - Agent performance tracking
                - Resource usage monitoring
                - Execution time analytics
                - Dashboard data generation
                
                Include visualization utilities and alerts."""
            },
            {
                "id": "agent-5-integration",
                "prompt": """Integrate all Phase 2 components in HECATON at /home/opsvi/master_root/apps/hecaton/

                Update src/hecaton/core/orchestrator.py to:
                - Use the new messaging system
                - Register agents with the registry
                - Instantiate specialized agents
                - Connect monitoring
                - Create examples/phase_2_demo.py showing all features
                
                Ensure everything works together seamlessly."""
            }
        ]
        
        print("\n" + "="*60)
        print("HECATON PHASE 2: REAL PARALLEL AGENT IMPLEMENTATION")
        print("="*60)
        print("\nUsing 5 REAL Claude Code instances to build Phase 2 features:")
        print("1. Inter-agent messaging system")
        print("2. Agent registry")
        print("3. Specialized agent types")
        print("4. Performance monitoring")
        print("5. System integration")
        print("\nThis is NOT a simulation - real Claude agents at work!")
        print("="*60 + "\n")
        
        # Execute with real parallel Claude instances
        results = await self.executor.execute_parallel_tasks(phase_2_tasks, max_parallel=5)
        
        # Process results
        for result in results:
            if result.get("status") == "completed":
                print(f"\n✅ {result['task_id']} completed successfully")
                if result.get("result"):
                    # Extract any important information from the result
                    print(f"   Result available with job ID: {result.get('job_id')}")
            else:
                print(f"\n❌ {result['task_id']} failed: {result.get('error')}")
                
        return results