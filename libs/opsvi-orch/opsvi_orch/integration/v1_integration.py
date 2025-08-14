"""
V1 Integration Module
---------------------
Integrates orchestration library with Claude Code V1 server.

This shows how to add parallel batch spawning to the existing V1 server
without breaking compatibility.
"""

from typing import List, Optional, Dict, Any, Callable
import json
import logging

from ..managers.job_manager import JobManager, JobConfig
from ..executors.claude_executor import ClaudeJobExecutor, ClaudeBatchExecutor

logger = logging.getLogger(__name__)


class V1OrchestrationIntegration:
    """
    Integration layer for V1 Claude Code server.
    Adds parallel batch spawning capabilities.
    """
    
    def __init__(
        self,
        existing_job_manager: Any = None,  # V1's JobManager
        claude_token: Optional[str] = None
    ):
        """
        Initialize integration.
        
        Args:
            existing_job_manager: V1's existing JobManager instance
            claude_token: CLAUDE_CODE_TOKEN
        """
        self.v1_job_manager = existing_job_manager
        
        # Create orchestration components
        self.job_manager = JobManager(
            config=JobConfig(
                max_concurrent=10,
                enable_recursion=True,
                enable_checkpointing=True
            )
        )
        
        self.claude_executor = ClaudeJobExecutor(
            claude_token=claude_token
        )
        
        self.batch_executor = ClaudeBatchExecutor(
            job_executor=self.claude_executor,
            max_concurrent=10
        )
    
    def create_mcp_tools(self) -> Dict[str, Callable]:
        """
        Create MCP tool functions for V1 server.
        
        These can be added to V1's server.py alongside existing tools.
        
        Returns:
            Dict of tool_name -> tool_function
        """
        
        async def claude_run_batch_async(
            tasks: List[str],
            parentJobId: Optional[str] = None,
            cwd: Optional[str] = None,
            outputFormat: str = "json",
            permissionMode: str = "bypassPermissions",
            verbose: bool = False
        ) -> str:
            """
            MCP Tool: Spawn multiple Claude instances in parallel.
            
            This is the KEY TOOL that enables parallel spawning.
            Each Claude instance can use this to spawn multiple children.
            
            Args:
                tasks: List of task descriptions to execute in parallel
                parentJobId: Parent job ID for recursive tracking
                cwd: Working directory
                outputFormat: Output format (json or text)
                permissionMode: Permission mode
                verbose: Enable verbose output
                
            Returns:
                JSON string with job IDs and batch info
            """
            try:
                # Use orchestration manager for batch execution
                batch_result = await self.job_manager.execute_batch_async(
                    tasks=tasks,
                    parent_job_id=parentJobId,
                    cwd=cwd
                )
                
                # If V1 job manager exists, register jobs
                if self.v1_job_manager and hasattr(self.v1_job_manager, 'active_jobs'):
                    for job_id in batch_result.job_ids:
                        self.v1_job_manager.active_jobs[job_id] = {
                            "batch_id": batch_result.batch_id,
                            "parent_job_id": parentJobId,
                            "status": "running"
                        }
                
                return json.dumps({
                    "jobIds": batch_result.job_ids,
                    "batchId": batch_result.batch_id,
                    "count": batch_result.total_jobs,
                    "status": batch_result.status,
                    "message": f"Spawned {batch_result.total_jobs} jobs in parallel"
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Batch spawn failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "status": "failed"
                }, indent=2)
        
        async def claude_collect_batch(
            batchId: Optional[str] = None,
            jobIds: Optional[List[str]] = None,
            wait: bool = True,
            timeout: int = 300
        ) -> str:
            """
            MCP Tool: Collect results from batch execution.
            
            Args:
                batchId: Batch ID to collect
                jobIds: Specific job IDs to collect
                wait: Wait for all jobs to complete
                timeout: Timeout in seconds
                
            Returns:
                JSON string with collected results
            """
            try:
                if batchId:
                    results = await self.job_manager.collect_batch_results(
                        batch_id=batchId,
                        wait=wait,
                        timeout_ms=timeout * 1000
                    )
                elif jobIds:
                    # Create ad-hoc batch for specific jobs
                    results = {
                        "jobIds": jobIds,
                        "results": {},
                        "errors": {}
                    }
                    
                    for job_id in jobIds:
                        # Check V1 job manager
                        if self.v1_job_manager:
                            job_result = self.v1_job_manager.get_job_result(job_id)
                            if job_result:
                                results["results"][job_id] = job_result
                            else:
                                results["errors"][job_id] = "Job not found or still running"
                else:
                    return json.dumps({
                        "error": "Must provide either batchId or jobIds"
                    }, indent=2)
                
                return json.dumps(results, indent=2)
                
            except Exception as e:
                logger.error(f"Batch collection failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "status": "failed"
                }, indent=2)
        
        async def claude_spawn_recursive(
            task: str,
            maxDepth: int = 3,
            childrenPerLevel: int = 3,
            parentJobId: Optional[str] = None
        ) -> str:
            """
            MCP Tool: Spawn a recursive tree of Claude instances.
            
            Each level spawns multiple children in parallel.
            
            Args:
                task: Root task description
                maxDepth: Maximum recursion depth
                childrenPerLevel: Number of children per parent
                parentJobId: Parent job ID
                
            Returns:
                JSON string with tree structure
            """
            try:
                # This would use RecursiveClaudeExecutor
                from ..executors.recursive_executor import RecursiveClaudeExecutor, RecursionConfig
                
                config = RecursionConfig(
                    max_depth=maxDepth,
                    max_children_per_parent=childrenPerLevel
                )
                
                executor = RecursiveClaudeExecutor(config=config)
                
                result = await executor.execute_claude_recursive(
                    task=task,
                    parent_job_id=parentJobId
                )
                
                return json.dumps({
                    "jobId": result.job_id,
                    "success": result.success,
                    "depth": result.depth,
                    "childrenSpawned": result.children_spawned,
                    "totalDescendants": result.total_descendants,
                    "treeStructure": result.tree_structure
                }, indent=2)
                
            except Exception as e:
                logger.error(f"Recursive spawn failed: {e}")
                return json.dumps({
                    "error": str(e),
                    "status": "failed"
                }, indent=2)
        
        return {
            "claude_run_batch_async": claude_run_batch_async,
            "claude_collect_batch": claude_collect_batch,
            "claude_spawn_recursive": claude_spawn_recursive
        }
    
    def integrate_with_v1_server(self, mcp_server: Any):
        """
        Add orchestration tools to existing V1 MCP server.
        
        Args:
            mcp_server: The V1 MCP server instance
        """
        tools = self.create_mcp_tools()
        
        for name, func in tools.items():
            # Add tool to MCP server
            # This assumes V1 uses FastMCP or similar
            if hasattr(mcp_server, 'tool'):
                mcp_server.tool()(func)
                logger.info(f"Added orchestration tool: {name}")
            else:
                logger.warning(f"Could not add tool {name} - incompatible server")


def enhance_v1_with_orchestration(
    v1_server_module: Any,
    claude_token: Optional[str] = None
) -> None:
    """
    Enhance an existing V1 server with orchestration capabilities.
    
    This function can be called from V1's server.py to add
    parallel batch spawning capabilities.
    
    Args:
        v1_server_module: The V1 server module
        claude_token: CLAUDE_CODE_TOKEN
    
    Example usage in V1 server.py:
    
    ```python
    # In libs/opsvi-mcp/opsvi_mcp/servers/claude_code/server.py
    
    # After existing imports
    from opsvi_orch.integration.v1_integration import enhance_v1_with_orchestration
    
    # After existing tool definitions
    enhance_v1_with_orchestration(mcp, os.environ.get("CLAUDE_CODE_TOKEN"))
    ```
    """
    integration = V1OrchestrationIntegration(
        existing_job_manager=getattr(v1_server_module, 'job_manager', None),
        claude_token=claude_token
    )
    
    integration.integrate_with_v1_server(v1_server_module)
    
    logger.info("V1 server enhanced with orchestration capabilities")