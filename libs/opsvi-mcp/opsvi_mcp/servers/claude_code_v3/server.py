"""Claude Code V3 MCP Server - Fixed to use real Claude Code"""

import os
import json
import subprocess
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from fastmcp import FastMCP
from .config import config
from .task_decomposer import TaskDecomposer
from .timeout_manager import TimeoutManager
from .agents import ModeDetector

# Initialize server
server = FastMCP("Claude Code V3 - Enhanced")

# Initialize components
task_decomposer = TaskDecomposer(config)
timeout_manager = TimeoutManager(config)
mode_detector = ModeDetector(config)


async def execute_claude_code(
    task: str, mode: str = "CODE", timeout: int = 600, output_format: str = "json"
) -> Dict[str, Any]:
    """Execute Claude Code CLI with intelligent MCP management"""

    # Analyze task for MCP requirements
    from ..claude_code_v2.mcp_manager import MCPRequirementAnalyzer, MCPConfigManager
    import uuid

    required_servers = MCPRequirementAnalyzer.analyze_task(task)

    # Build command based on mode
    cmd = ["claude", "--dangerously-skip-permissions"]

    # Add MCP configuration if needed
    mcp_config_path = None
    if required_servers:
        instance_id = f"v3-{mode.lower()}-{uuid.uuid4().hex[:8]}"
        mcp_config_path = MCPConfigManager.create_instance_config(
            instance_id=instance_id, custom_servers=list(required_servers)
        )
        cmd.extend(["--mcp-config", mcp_config_path])
        cmd.append("--strict-mcp-config")

    # Add output format
    if output_format:
        cmd.extend(["--output-format", output_format])

    # Add mode-specific flags if needed
    # V3 modes can be handled through task modification
    mode_prefix = ""
    if mode == "TESTING":
        mode_prefix = "Write comprehensive tests for: "
    elif mode == "DOCUMENTATION":
        mode_prefix = "Write detailed documentation for: "
    elif mode == "REVIEW":
        mode_prefix = "Review and provide feedback on: "
    elif mode == "DEBUG":
        mode_prefix = "Debug and fix issues in: "
    elif mode == "FULL_CYCLE":
        mode_prefix = "Create production-ready code with tests and documentation for: "

    modified_task = mode_prefix + task if mode_prefix else task

    try:
        # Execute Claude Code
        import time

        start_time = time.time()

        # Prepare environment for Claude Code
        env = os.environ.copy()

        # Ensure CLAUDE_CODE_TOKEN is set
        claude_token = os.environ.get("CLAUDE_CODE_TOKEN", "")
        if claude_token:
            env["CLAUDE_CODE_TOKEN"] = claude_token

        # CRITICAL: Remove ANTHROPIC_API_KEY to force user auth
        # This is essential since ANTHROPIC_API_KEY is set by default in the environment
        if "ANTHROPIC_API_KEY" in env:
            del env["ANTHROPIC_API_KEY"]
        # Also explicitly set to empty as double safety
        env["ANTHROPIC_API_KEY"] = ""

        # Remove any other ANTHROPIC_* variables
        for key in list(env.keys()):
            if (
                key.startswith("ANTHROPIC_") and key != "ANTHROPIC_API_KEY"
            ):  # We already handled API_KEY
                del env[key]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # Wait for MCP servers if needed (async version)
        if required_servers:
            # Simple timing-based wait for MCP initialization
            # With minimal servers, should be ready in 1-3 seconds
            expected_wait = len(required_servers) * 1.5
            await asyncio.sleep(min(expected_wait, 5))  # Cap at 5 seconds

        # Send task and get result
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=modified_task.encode()), timeout=timeout
        )

        mcp_init_time = time.time() - start_time if required_servers else 0

        if process.returncode == 0:
            # Parse output
            try:
                result = json.loads(stdout.decode())
                return {
                    "success": True,
                    "mode": mode,
                    "output": result,
                    "session_id": result.get("session_id"),
                    "cost": result.get("total_cost_usd", 0),
                    "status": "completed",
                    "mcp_servers_used": list(required_servers)
                    if required_servers
                    else [],
                    "mcp_init_time_seconds": mcp_init_time,
                }
            except json.JSONDecodeError:
                # Non-JSON output
                return {
                    "success": True,
                    "mode": mode,
                    "output": stdout.decode(),
                    "status": "completed",
                    "mcp_servers_used": list(required_servers)
                    if required_servers
                    else [],
                    "mcp_init_time_seconds": mcp_init_time,
                }
        else:
            return {
                "success": False,
                "mode": mode,
                "error": stderr.decode()
                or f"Process exited with code {process.returncode}",
                "status": "failed",
            }

    except asyncio.TimeoutError:
        return {
            "success": False,
            "mode": mode,
            "error": f"Task timed out after {timeout} seconds",
            "status": "timeout",
        }
    except Exception as e:
        return {"success": False, "mode": mode, "error": str(e), "status": "error"}


@server.tool()
async def claude_run_v3(
    task: str, mode: str = None, auto_detect: bool = True, quality_level: str = "normal"
) -> dict:
    """Enhanced Claude Code V3 with real execution"""

    # Detect mode
    execution_mode = mode_detector.detect_mode(task, explicit_mode=mode)
    mode_config = mode_detector.get_mode_config(execution_mode)

    # Calculate timeout
    complexity_str = task_decomposer.estimate_complexity(task)
    # Convert complexity string to numeric value for comparison
    complexity_map = {"simple": 1, "moderate": 2, "complex": 3, "very_complex": 4}
    complexity_num = complexity_map.get(complexity_str, 2)

    file_count = task_decomposer.estimate_file_count(task)
    timeout_ms = timeout_manager.calculate_timeout(
        task, "unknown", complexity_str, 0, file_count
    )
    timeout_seconds = timeout_ms // 1000

    # Decompose task if needed
    subtasks = []
    if config.decomposition.enable_decomposition and complexity_num > 2:
        subtasks = task_decomposer.decompose(task)

    # Execute main task or subtasks
    if subtasks and len(subtasks) > 1:
        # Execute subtasks sequentially (could be parallelized)
        results = []
        total_cost = 0

        for i, subtask in enumerate(subtasks):
            # SubTask is an object with attributes, not a dict
            task_desc = (
                subtask.description if hasattr(subtask, "description") else str(subtask)
            )
            print(f"Executing subtask {i+1}/{len(subtasks)}: {task_desc[:50]}...")

            result = await execute_claude_code(
                task_desc,
                mode=execution_mode.name,
                timeout=timeout_seconds
                // len(subtasks),  # Divide timeout among subtasks
                output_format="json",
            )

            results.append(result)
            if result.get("cost"):
                total_cost += result["cost"]

            # Stop on failure if critical
            is_critical = subtask.critical if hasattr(subtask, "critical") else False
            if not result.get("success") and is_critical:
                break

        # Aggregate results
        all_success = all(r.get("success") for r in results)
        return {
            "task": task,
            "mode": execution_mode.name,
            "subtasks_executed": len(results),
            "subtasks_total": len(subtasks),
            "results": results,
            "total_cost": total_cost,
            "success": all_success,
            "status": "completed" if all_success else "partial",
            "quality_level": quality_level,
            "complexity": complexity_str,
        }
    else:
        # Execute single task
        result = await execute_claude_code(
            task,
            mode=execution_mode.name,
            timeout=timeout_seconds,
            output_format="json",
        )

        # Add V3 metadata
        result.update(
            {
                "task": task,
                "mode": execution_mode.name,
                "quality_level": quality_level,
                "complexity": complexity_str,
                "timeout_used": timeout_seconds,
                "config": {
                    "quality_threshold": mode_config.quality_threshold,
                    "review_iterations": mode_config.review_iterations,
                    "enable_critic": mode_config.enable_critic,
                    "enable_tester": mode_config.enable_tester,
                    "enable_documenter": mode_config.enable_documenter,
                },
            }
        )

        return result


@server.tool()
async def get_v3_status() -> dict:
    """Get Claude Code V3 server status"""
    return {
        "version": "3.0.0",
        "multi_agent": True,
        "max_recursion_depth": config.recursion.max_depth,
        "modes_available": [
            "CODE",
            "ANALYSIS",
            "REVIEW",
            "TESTING",
            "DOCUMENTATION",
            "FULL_CYCLE",
            "QUALITY",
            "RAPID",
        ],
        "agents": ["critic", "tester", "documenter", "security"],
        "features": {
            "task_decomposition": config.decomposition.enable_decomposition,
            "adaptive_timeout": config.timeout.enable_adaptive,
            "checkpointing": config.recursion.enable_checkpointing,
            "priority_queue": config.recursion.enable_priority_queue,
            "recovery": config.recovery.enable_recovery,
        },
        "execution": "REAL",  # Now using real Claude Code!
        "stubbed": False,
    }


# Export
__all__ = ["server"]
