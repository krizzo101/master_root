#!/usr/bin/env python3
"""
Sequential Thinking MCP Client - Complex Problem Solving via MCP
"""

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

# MCP imports
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, TextContent
except ImportError:
    print("Error: MCP Python SDK not installed.")
    print("Install with: pip install 'mcp[cli]'")
    sys.exit(1)


class SequentialThinkingError(Exception):
    """Base exception for Sequential Thinking-related errors."""

    pass


@dataclass
class ThoughtStep:
    """Represents a single thought step in the reasoning process."""

    thought_number: int
    thought: str
    is_revision: bool = False
    revises_thought: int | None = None
    branch_from_thought: int | None = None
    branch_id: str | None = None


@dataclass
class ThinkingSession:
    """Represents a complete thinking session."""

    problem: str
    thoughts: list[ThoughtStep] = field(default_factory=list)
    total_thoughts: int = 0
    completed: bool = False
    final_answer: str = ""


class SequentialThinkingMCPClient:
    """Client for interacting with Sequential Thinking MCP server."""

    def __init__(self, mcp_config_path: str | None = None, debug: bool = False):
        """Initialize the Sequential Thinking MCP client."""
        self.mcp_config_path = mcp_config_path or ".cursor/mcp.json"
        self.debug = debug
        self.active_sessions: dict[str, ThinkingSession] = {}

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def _get_session(self):
        """Create and manage an MCP session with Sequential Thinking server."""
        config_path = Path(self.mcp_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")

        with open(config_path) as f:
            config = json.load(f)

        thinking_config = config.get("mcpServers", {}).get("sequential_thinking", {})
        if not thinking_config:
            raise ValueError(
                "sequential_thinking server not found in MCP configuration"
            )

        server_params = StdioServerParameters(
            command=thinking_config.get("command", "npx"),
            args=thinking_config.get("args", ["-y", "server-sequential-thinking"]),
            env={**os.environ, **thinking_config.get("env", {})},
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.logger.debug("Sequential Thinking MCP session initialized")
                    yield session
        except Exception as e:
            self.logger.error(f"Failed to establish MCP session: {e}")
            raise SequentialThinkingError(
                f"Failed to connect to Sequential Thinking MCP server: {e}"
            )

    async def think_step(
        self,
        thought: str,
        session_id: str = "default",
        thought_number: int = 1,
        total_thoughts: int = 5,
        next_thought_needed: bool = True,
    ) -> str:
        """Execute a single thinking step."""
        if not thought.strip():
            raise ValueError("Thought cannot be empty")

        arguments = {
            "thought": thought,
            "nextThoughtNeeded": next_thought_needed,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
        }

        self.logger.info(f"Executing thought step {thought_number}")

        async with self._get_session() as session:
            try:
                result = await session.call_tool("sequential_thinking", arguments)

                if result.content:
                    content = result.content[0]
                    if isinstance(content, TextContent):
                        return content.text

                return "Thinking step completed"

            except Exception as e:
                self.logger.error(f"Thinking step failed: {e}")
                raise SequentialThinkingError(f"Thinking step failed: {e}")

    async def solve_problem(
        self, problem: str, max_thoughts: int = 10
    ) -> ThinkingSession:
        """Solve a complex problem using sequential thinking."""
        if not problem.strip():
            raise ValueError("Problem cannot be empty")

        self.logger.info(f"Starting problem solving for: {problem}")

        session = ThinkingSession(problem=problem, total_thoughts=max_thoughts)
        thoughts = []

        # Initial analysis
        current_thought = f"Let me analyze this problem: {problem}"

        try:
            for i in range(1, max_thoughts + 1):
                result = await self.think_step(
                    thought=current_thought,
                    thought_number=i,
                    total_thoughts=max_thoughts,
                    next_thought_needed=i < max_thoughts,
                )

                step = ThoughtStep(thought_number=i, thought=current_thought)
                thoughts.append(step)

                # Generate next thought based on progress
                if i == 1:
                    current_thought = "Let me break this down into key components."
                elif i == 2:
                    current_thought = "Now let me analyze potential solutions."
                elif i == 3:
                    current_thought = "Let me evaluate the trade-offs."
                elif i == 4:
                    current_thought = "Based on my analysis, here's my recommendation."
                else:
                    current_thought = "Let me refine and finalize my solution."

            session.thoughts = thoughts
            session.completed = True
            session.final_answer = thoughts[-1].thought if thoughts else ""

            return session

        except Exception as e:
            self.logger.error(f"Problem solving failed: {e}")
            session.thoughts = thoughts
            return session

    def get_session_summary(self, session: ThinkingSession) -> str:
        """Get a summary of a thinking session."""
        summary = f"Problem: {session.problem}\n"
        summary += f"Status: {'Completed' if session.completed else 'In Progress'}\n"
        summary += f"Thoughts: {len(session.thoughts)}\n\n"

        for thought in session.thoughts:
            summary += f"Step {thought.thought_number}: {thought.thought[:100]}...\n"

        if session.final_answer:
            summary += f"\nFinal Answer: {session.final_answer}\n"

        return summary


# Command line interface
async def main():
    """Command line interface for Sequential Thinking MCP client."""
    import argparse

    parser = argparse.ArgumentParser(description="Sequential Thinking MCP Client")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Solve command
    solve_parser = subparsers.add_parser("solve", help="Solve a complex problem")
    solve_parser.add_argument("problem", help="Problem to solve")
    solve_parser.add_argument(
        "--max-thoughts", type=int, default=8, help="Maximum thoughts"
    )

    # Think command
    think_parser = subparsers.add_parser("think", help="Execute a single thinking step")
    think_parser.add_argument("thought", help="Thought content")
    think_parser.add_argument(
        "--thought-number", type=int, default=1, help="Thought number"
    )

    # Global options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", help="Path to mcp.json config file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        client = SequentialThinkingMCPClient(
            mcp_config_path=args.config, debug=args.debug
        )

        if args.command == "solve":
            print(f"🤔 Solving problem: {args.problem}")
            print("=" * 50)

            session = await client.solve_problem(args.problem, args.max_thoughts)

            for thought in session.thoughts:
                print(f"Step {thought.thought_number}: {thought.thought}")

            if session.completed:
                print(f"\n✅ Solution completed in {len(session.thoughts)} steps")

        elif args.command == "think":
            result = await client.think_step(
                args.thought, thought_number=args.thought_number
            )
            print(f"✅ Thought result: {result}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
