"""
OAMAT Parallel Execution Module
Enables concurrent execution of multiple agents using asyncio
"""

import asyncio
import logging
from datetime import datetime


class ParallelAgentExecutor:
    """Executes multiple OAMAT agents in parallel"""

    def __init__(self, main_oamat_instance):
        self.oamat = main_oamat_instance
        self.logger = logging.getLogger("OAMAT.ParallelExecutor")

    async def execute_agents_parallel(
        self, parallel_candidates: list[dict], user_request: str, base_state: dict
    ) -> dict:
        """
        Execute multiple agents in parallel and combine their results

        Args:
            parallel_candidates: List of agent nodes that can run in parallel
            user_request: The original user request
            base_state: Base state to be passed to each agent

        Returns:
            Combined results from all parallel agents
        """
        print(f"🚀 PARALLEL: Starting execution of {len(parallel_candidates)} agents")
        start_time = datetime.now()

        # Create tasks for parallel execution
        tasks = []
        for candidate in parallel_candidates:
            task = self._create_agent_task(candidate, user_request, base_state.copy())
            tasks.append(task)

        # Execute all agents concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            combined_results = self._combine_parallel_results(
                results, parallel_candidates
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"🚀 PARALLEL: Completed in {execution_time:.2f} seconds")

            return combined_results

        except Exception as e:
            self.logger.error(f"Parallel execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _create_agent_task(self, candidate: dict, user_request: str, state: dict):
        """Create an async task for a single agent"""
        node_id = candidate["node_id"]
        agent_role = candidate["agent_role"]

        print(f"🤖 PARALLEL: Starting {agent_role} (node: {node_id})")

        try:
            # Prepare state for this specific agent
            agent_state = state.copy()
            agent_state.update(
                {
                    "current_node": node_id,
                    "current_role": agent_role,
                    "parallel_execution": True,
                    "agent_specific_context": candidate,
                }
            )

            # Execute the agent
            # Note: This runs in a thread pool since _run_agent_node is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.oamat._run_agent_node, agent_state, {}, node_id
            )

            print(f"✅ PARALLEL: Completed {agent_role}")
            return {
                "node_id": node_id,
                "agent_role": agent_role,
                "success": True,
                "result": result,
            }

        except Exception as e:
            print(f"❌ PARALLEL: Failed {agent_role}: {e}")
            return {
                "node_id": node_id,
                "agent_role": agent_role,
                "success": False,
                "error": str(e),
            }

    def _combine_parallel_results(self, results: list, candidates: list[dict]) -> dict:
        """Combine results from parallel agent execution"""
        combined = {
            "success": True,
            "parallel_execution": True,
            "agent_results": {},
            "completed_nodes": [],
            "failed_nodes": [],
            "errors": [],
        }

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                candidate = candidates[i]
                combined["failed_nodes"].append(candidate["node_id"])
                combined["errors"].append(f"{candidate['agent_role']}: {str(result)}")
                combined["success"] = False
            elif result.get("success", False):
                combined["agent_results"][result["agent_role"]] = result["result"]
                combined["completed_nodes"].append(result["node_id"])
            else:
                combined["failed_nodes"].append(result["node_id"])
                combined["errors"].append(
                    f"{result['agent_role']}: {result.get('error', 'Unknown error')}"
                )
                combined["success"] = False

        print(
            f"🔄 PARALLEL: Combined results - Success: {len(combined['completed_nodes'])}, Failed: {len(combined['failed_nodes'])}"
        )
        return combined


class AsyncAgentBridge:
    """Bridge to run synchronous agent methods in async context"""

    def __init__(self, oamat_instance):
        self.oamat = oamat_instance
        self.executor = None

    async def run_agent_async(self, state: dict, config: dict, node_id: str):
        """Run a single agent asynchronously"""
        if self.executor is None:
            # Create thread pool executor for CPU-bound agent work
            from concurrent.futures import ThreadPoolExecutor

            self.executor = ThreadPoolExecutor(max_workers=4)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self.executor, self.oamat._run_agent_node, state, config, node_id
            )
            return result
        except Exception as e:
            raise e
