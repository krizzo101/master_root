"""
Debug Monitor for Claude Agent Sessions
Provides real-time monitoring and analysis of Claude agent executions
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ClaudeSessionMonitor:
    """
    Monitors Claude agent sessions for debugging and analysis.
    Reads from ~/.claude/projects/ session logs.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the session monitor.

        Args:
            logger: Optional logger for output
        """
        self.logger = logger or logging.getLogger(__name__)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

    def get_session_log_path(self, session_id: str) -> Optional[Path]:
        """
        Find the session log file for a given session ID.

        Args:
            session_id: The Claude session ID

        Returns:
            Path to the session log file if found
        """
        base_path = Path.home() / ".claude" / "projects"
        if not base_path.exists():
            return None

        # Search for session file
        for project_dir in base_path.iterdir():
            if project_dir.is_dir():
                session_file = project_dir / f"{session_id}.jsonl"
                if session_file.exists():
                    return session_file

        return None

    async def monitor_session(self, session_id: str, callback=None):
        """
        Monitor a Claude session in real-time.

        Args:
            session_id: The session ID to monitor
            callback: Optional callback for each log entry
        """
        log_path = self.get_session_log_path(session_id)
        if not log_path:
            self.logger.warning(f"Session log not found for {session_id}")
            return

        self.logger.info(f"Monitoring session {session_id} at {log_path}")

        # Track session data
        self.sessions[session_id] = {
            "start_time": datetime.now(),
            "log_path": log_path,
            "events": [],
            "tool_calls": [],
            "errors": [],
        }

        # Read existing content
        with open(log_path, "r") as f:
            for line in f:
                await self._process_log_entry(session_id, line, callback)

        # Monitor for new content
        last_position = log_path.stat().st_size

        while session_id in self.monitoring_tasks:
            try:
                current_size = log_path.stat().st_size
                if current_size > last_position:
                    with open(log_path, "r") as f:
                        f.seek(last_position)
                        for line in f:
                            await self._process_log_entry(session_id, line, callback)
                    last_position = current_size

                await asyncio.sleep(0.5)  # Check every 500ms

            except Exception as e:
                self.logger.error(f"Error monitoring session {session_id}: {e}")
                break

    async def _process_log_entry(self, session_id: str, line: str, callback=None):
        """Process a single log entry"""
        try:
            entry = json.loads(line.strip())

            # Store in session data
            self.sessions[session_id]["events"].append(entry)

            # Extract key information
            entry_type = entry.get("type", "unknown")

            # Track tool calls
            if entry_type == "tool_call":
                tool_info = {
                    "tool": entry.get("tool", "unknown"),
                    "timestamp": entry.get("timestamp"),
                    "parameters": entry.get("parameters", {}),
                }
                self.sessions[session_id]["tool_calls"].append(tool_info)
                self.logger.debug(f"[{session_id}] Tool call: {tool_info['tool']}")

            # Track errors
            if entry.get("error"):
                error_info = {
                    "error": entry.get("error"),
                    "timestamp": entry.get("timestamp"),
                    "context": entry.get("context"),
                }
                self.sessions[session_id]["errors"].append(error_info)
                self.logger.warning(f"[{session_id}] Error: {error_info['error']}")

            # Track messages
            if entry_type == "message" and entry.get("content"):
                content = entry["content"]
                if isinstance(content, list) and content:
                    text = content[0].get("text", "")[:100]  # First 100 chars
                    self.logger.debug(f"[{session_id}] Message: {text}...")

            # Call custom callback
            if callback:
                await callback(session_id, entry)

        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse log entry: {line[:100]}")
        except Exception as e:
            self.logger.error(f"Error processing log entry: {e}")

    async def start_monitoring(self, session_id: str):
        """Start monitoring a session asynchronously"""
        if session_id not in self.monitoring_tasks:
            task = asyncio.create_task(self.monitor_session(session_id))
            self.monitoring_tasks[session_id] = task
            self.logger.info(f"Started monitoring session {session_id}")

    def stop_monitoring(self, session_id: str):
        """Stop monitoring a session"""
        if session_id in self.monitoring_tasks:
            self.monitoring_tasks[session_id].cancel()
            del self.monitoring_tasks[session_id]
            self.logger.info(f"Stopped monitoring session {session_id}")

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a monitored session"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}

        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "start_time": session["start_time"].isoformat(),
            "duration": (datetime.now() - session["start_time"]).total_seconds(),
            "total_events": len(session["events"]),
            "tool_calls": len(session["tool_calls"]),
            "errors": len(session["errors"]),
            "tools_used": list(set(t["tool"] for t in session["tool_calls"])),
            "error_summary": [e["error"][:100] for e in session["errors"][:5]],  # First 5 errors
        }

    def get_all_summaries(self) -> List[Dict[str, Any]]:
        """Get summaries of all monitored sessions"""
        return [self.get_session_summary(sid) for sid in self.sessions]


class DebugLogCapture:
    """
    Captures debug output from Claude agents for application logging.
    Integrates with the application's logging infrastructure.
    """

    def __init__(self, app_logger: logging.Logger, log_level: int = logging.DEBUG):
        """
        Initialize debug log capture.

        Args:
            app_logger: Application logger to write to
            log_level: Logging level for captured output
        """
        self.app_logger = app_logger
        self.log_level = log_level
        self.capture_buffer: Dict[str, List[str]] = {}

    def capture_output(self, agent_id: str, output_type: str, content: str):
        """
        Capture output from a Claude agent.

        Args:
            agent_id: Identifier for the agent
            output_type: Type of output (stdout, stderr, debug)
            content: The content to capture
        """
        # Initialize buffer if needed
        if agent_id not in self.capture_buffer:
            self.capture_buffer[agent_id] = []

        # Store in buffer
        self.capture_buffer[agent_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "type": output_type,
                "content": content,
            }
        )

        # Log to application logger
        if output_type == "stderr" or "error" in content.lower():
            self.app_logger.error(f"[Agent {agent_id}] {content}")
        elif output_type == "debug":
            self.app_logger.debug(f"[Agent {agent_id}] {content}")
        else:
            self.app_logger.log(self.log_level, f"[Agent {agent_id}] {content}")

    def get_agent_log(self, agent_id: str) -> List[Dict[str, str]]:
        """Get captured log for a specific agent"""
        return self.capture_buffer.get(agent_id, [])

    def clear_agent_log(self, agent_id: str):
        """Clear captured log for a specific agent"""
        if agent_id in self.capture_buffer:
            del self.capture_buffer[agent_id]

    def save_to_file(self, agent_id: str, filepath: Path):
        """Save captured log to a file"""
        if agent_id not in self.capture_buffer:
            return

        with open(filepath, "w") as f:
            for entry in self.capture_buffer[agent_id]:
                f.write(f"[{entry['timestamp']}] [{entry['type']}] {entry['content']}\n")


# Performance diagnostics from the headless guide
async def run_performance_diagnosis(logger: Optional[logging.Logger] = None):
    """
    Run performance diagnosis for Claude CLI optimization.
    Based on the troubleshooting section of the headless guide.
    """
    logger = logger or logging.getLogger(__name__)

    logger.info("Running Claude CLI Performance Diagnosis")
    logger.info("=" * 50)

    results = []

    # Test 1: Baseline (no optimization)
    start = datetime.now()
    proc = await asyncio.create_subprocess_exec(
        "claude",
        "-p",
        "What is 2+2?",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    baseline_time = (datetime.now() - start).total_seconds()
    results.append(("Baseline (no optimization)", baseline_time))
    logger.info(f"1. Default (no optimization): {baseline_time:.2f}s")

    # Test 2: MCP optimization
    mcp_config = Path.home() / ".claude_minimal.json"
    if not mcp_config.exists():
        mcp_config.write_text('{"mcpServers": {}}')

    start = datetime.now()
    proc = await asyncio.create_subprocess_exec(
        "claude",
        "-p",
        "--strict-mcp-config",
        "--mcp-config",
        str(mcp_config),
        "What is 2+2?",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    mcp_time = (datetime.now() - start).total_seconds()
    results.append(("With MCP optimization", mcp_time))
    logger.info(f"2. With MCP optimization: {mcp_time:.2f}s")

    # Test 3: Full optimization
    start = datetime.now()
    proc = await asyncio.create_subprocess_exec(
        "claude",
        "-p",
        "--model",
        "sonnet",
        "--strict-mcp-config",
        "--mcp-config",
        str(mcp_config),
        "--dangerously-skip-permissions",
        "What is 2+2?",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    full_time = (datetime.now() - start).total_seconds()
    results.append(("Full optimization", full_time))
    logger.info(f"3. Full optimization: {full_time:.2f}s")

    # Diagnosis
    logger.info("")
    logger.info("Diagnosis:")
    if baseline_time > 10:
        logger.warning("MCP servers are the issue - use --strict-mcp-config")
    if mcp_time > 5:
        logger.warning("Permission prompts are the issue - use --permission-mode acceptEdits")
    if full_time > 3:
        logger.warning("Network or API issues detected")

    if full_time <= 5:
        logger.info("✅ Performance is optimized!")

    return results


if __name__ == "__main__":
    # Example usage
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("debug_monitor")

    # Run performance diagnosis
    asyncio.run(run_performance_diagnosis(logger))

    # Example session monitoring
    async def monitor_example():
        monitor = ClaudeSessionMonitor(logger)

        # Start monitoring a session
        session_id = "test-session-123"
        await monitor.start_monitoring(session_id)

        # Wait a bit
        await asyncio.sleep(5)

        # Get summary
        summary = monitor.get_session_summary(session_id)
        print("Session Summary:", json.dumps(summary, indent=2))

        # Stop monitoring
        monitor.stop_monitoring(session_id)

    # Uncomment to run monitor example
    # asyncio.run(monitor_example())
