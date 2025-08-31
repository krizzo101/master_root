#!/usr/bin/env python3
"""
Specialized Headless Claude Agents with Maximum Customization
Optimized for performance and specific use cases
"""

import asyncio
import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentModel(Enum):
    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


class PermissionMode(Enum):
    ACCEPT = "acceptEdits"
    BYPASS = "bypassPermissions"
    DANGEROUS = "dangerously-skip-permissions"
    DEFAULT = "default"


@dataclass
class AgentConfig:
    """Configuration for headless Claude agent"""

    model: AgentModel = AgentModel.SONNET
    max_tokens: int = 4000
    temperature: float = 0.3
    permission_mode: PermissionMode = PermissionMode.ACCEPT
    allowed_tools: List[str] = None
    system_prompt_append: str = ""
    strict_mcp: bool = True
    output_format: str = "json"
    session_id: str = None
    add_dirs: List[str] = None
    verbose: bool = False

    def __post_init__(self):
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())
        if self.allowed_tools is None:
            self.allowed_tools = []
        if self.add_dirs is None:
            self.add_dirs = []


class HeadlessAgent:
    """Base class for headless Claude agents"""

    MINIMAL_MCP_CONFIG = '{"mcpServers": {}}'
    MINIMAL_MCP_PATH = Path.home() / ".claude_minimal.json"

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self._setup_minimal_mcp()

    def _setup_minimal_mcp(self):
        """Create minimal MCP config for speed"""
        self.MINIMAL_MCP_PATH.write_text(self.MINIMAL_MCP_CONFIG)

    def build_command(self, prompt: str) -> List[str]:
        """Build claude command with all optimizations"""
        cmd = ["claude", "-p"]

        # Model
        cmd.extend(["--model", self.config.model.value])

        # Performance optimizations
        if self.config.strict_mcp:
            cmd.extend(
                ["--strict-mcp-config", "--mcp-config", str(self.MINIMAL_MCP_PATH)]
            )

        # Permissions
        if self.config.permission_mode == PermissionMode.DANGEROUS:
            cmd.append("--dangerously-skip-permissions")
        else:
            cmd.extend(["--permission-mode", self.config.permission_mode.value])

        # Output
        cmd.extend(["--output-format", self.config.output_format])

        # Session
        cmd.extend(["--session-id", self.config.session_id])

        # Limits
        cmd.extend(["--max-tokens", str(self.config.max_tokens)])
        cmd.extend(["--temperature", str(self.config.temperature)])

        # Tools
        if self.config.allowed_tools:
            cmd.extend(["--allowed-tools", ",".join(self.config.allowed_tools)])

        # Directories
        for dir_path in self.config.add_dirs:
            cmd.extend(["--add-dir", dir_path])

        # System prompt
        if self.config.system_prompt_append:
            cmd.extend(["--append-system-prompt", self.config.system_prompt_append])

        # Verbose
        if self.config.verbose:
            cmd.append("--verbose")

        # Add prompt
        cmd.append("--")
        cmd.append(prompt)

        return cmd

    def run(self, prompt: str, timeout: int = 300) -> Dict[str, Any]:
        """Execute agent and return result"""
        cmd = self.build_command(prompt)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

            if self.config.output_format == "json":
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"output": result.stdout, "error": result.stderr}
            else:
                return {"output": result.stdout, "error": result.stderr}

        except subprocess.TimeoutExpired:
            return {"error": "Timeout exceeded", "timeout": timeout}
        except Exception as e:
            return {"error": str(e)}

    async def run_async(self, prompt: str) -> Dict[str, Any]:
        """Async execution for parallel operations"""
        cmd = self.build_command(prompt)

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if self.config.output_format == "json":
            try:
                return json.loads(stdout.decode())
            except:
                return {"output": stdout.decode(), "error": stderr.decode()}
        else:
            return {"output": stdout.decode(), "error": stderr.decode()}


# ============================================
# SPECIALIZED AGENT CLASSES
# ============================================


class SpeedAgent(HeadlessAgent):
    """Ultra-fast agent for simple tasks"""

    def __init__(self):
        config = AgentConfig(
            model=AgentModel.SONNET,
            max_tokens=2000,
            temperature=0.1,
            permission_mode=PermissionMode.DANGEROUS,
            system_prompt_append="Be extremely concise. Output only essential information.",
        )
        super().__init__(config)


class CodeGeneratorAgent(HeadlessAgent):
    """Production code generation"""

    def __init__(self, language: str = "python"):
        config = AgentConfig(
            model=AgentModel.OPUS,
            max_tokens=8000,
            temperature=0.3,
            permission_mode=PermissionMode.ACCEPT,
            allowed_tools=["Write", "Read", "Edit", "MultiEdit"],
            system_prompt_append=f"""You are an expert {language} developer.
Generate production-ready code with:
- Comprehensive error handling
- Type hints and documentation
- Performance optimizations
- Security best practices
- No placeholder code
Output executable code only.""",
        )
        super().__init__(config)


class CodeReviewAgent(HeadlessAgent):
    """Security-focused code review"""

    def __init__(self):
        config = AgentConfig(
            model=AgentModel.OPUS,
            max_tokens=6000,
            temperature=0.2,
            permission_mode=PermissionMode.BYPASS,
            allowed_tools=["Read", "Grep", "Glob"],
            system_prompt_append="""You are a senior security-focused code reviewer.
Identify:
- Security vulnerabilities (OWASP Top 10)
- Performance issues (O(n²) or worse)
- Memory leaks and race conditions
- Missing error handling
- Code smells and anti-patterns
Rate issues: CRITICAL/HIGH/MEDIUM/LOW.
Provide specific fixes.""",
        )
        super().__init__(config)


class TestGeneratorAgent(HeadlessAgent):
    """Comprehensive test generation"""

    def __init__(self, framework: str = "pytest"):
        config = AgentConfig(
            model=AgentModel.SONNET,
            max_tokens=8000,
            temperature=0.4,
            permission_mode=PermissionMode.ACCEPT,
            allowed_tools=["Write", "Read", "Edit"],
            system_prompt_append=f"""Generate comprehensive {framework} tests:
- Unit tests for all functions
- Edge cases and boundaries
- Error scenarios
- Integration tests
- Performance tests
- Fixtures and mocks
- >90% coverage target
Use descriptive names. No placeholders.""",
        )
        super().__init__(config)


class RefactoringAgent(HeadlessAgent):
    """Code refactoring specialist"""

    def __init__(self, focus: str = "performance"):
        config = AgentConfig(
            model=AgentModel.OPUS,
            max_tokens=8000,
            temperature=0.2,
            permission_mode=PermissionMode.ACCEPT,
            allowed_tools=["Read", "Edit", "MultiEdit", "Write"],
            system_prompt_append=f"""Refactoring expert focusing on {focus}.
Priorities:
- Preserve ALL functionality
- Apply SOLID principles
- Reduce complexity
- Optimize algorithms
- Improve naming
- Add type hints
- Ensure backward compatibility
Make surgical changes only.""",
        )
        super().__init__(config)


class DebuggerAgent(HeadlessAgent):
    """Issue diagnosis and fixing"""

    def __init__(self):
        config = AgentConfig(
            model=AgentModel.OPUS,
            max_tokens=6000,
            temperature=0.1,
            permission_mode=PermissionMode.ACCEPT,
            allowed_tools=["Read", "Edit", "Bash", "Grep"],
            system_prompt_append="""Debugging expert.
Approach:
1. Analyze error and stack trace
2. Identify root cause
3. Implement minimal fix
4. Add defensive code
5. Verify fix doesn't break other code
Be surgical. Add error handling.""",
        )
        super().__init__(config)


class ArchitectAgent(HeadlessAgent):
    """System design and architecture"""

    def __init__(self):
        config = AgentConfig(
            model=AgentModel.OPUS,
            max_tokens=10000,
            temperature=0.6,
            permission_mode=PermissionMode.BYPASS,
            system_prompt_append="""Senior solutions architect.
Design considering:
- Scalability (10x growth)
- Reliability (99.9% uptime)
- Security (defense in depth)
- Performance (sub-second)
- Maintainability
- Cost optimization
- Technology rationale
- API design
- DevOps and monitoring
Output complete technical specification.""",
        )
        super().__init__(config)


class SecurityAuditor(HeadlessAgent):
    """Security vulnerability scanner"""

    def __init__(self):
        config = AgentConfig(
            model=AgentModel.OPUS,
            max_tokens=8000,
            temperature=0.1,
            permission_mode=PermissionMode.BYPASS,
            allowed_tools=["Read", "Grep", "Glob"],
            system_prompt_append="""Security auditor (CISSP level).
Check for:
- Input validation issues
- Injection vulnerabilities
- XSS/CSRF
- Auth flaws
- Data exposure
- Misconfigurations
- Insecure dependencies
- Crypto weaknesses
Rate: CRITICAL/HIGH/MEDIUM/LOW.
Include POC and remediation.""",
        )
        super().__init__(config)


class OptimizationAgent(HeadlessAgent):
    """Performance optimization specialist"""

    def __init__(self, target: str = "latency"):
        config = AgentConfig(
            model=AgentModel.OPUS,
            max_tokens=8000,
            temperature=0.3,
            permission_mode=PermissionMode.ACCEPT,
            allowed_tools=["Read", "Edit", "MultiEdit", "Bash"],
            system_prompt_append=f"""Performance expert optimizing {target}.
Focus on:
- Profiling bottlenecks
- Algorithm improvements
- Data structure optimization
- Caching strategies
- Parallel processing
- I/O batching
- Query optimization
Include benchmarks.""",
        )
        super().__init__(config)


# ============================================
# AGENT ORCHESTRATION
# ============================================


class AgentTeam:
    """Coordinate multiple agents for complex tasks"""

    def __init__(self):
        self.agents = {
            "architect": ArchitectAgent(),
            "coder": CodeGeneratorAgent(),
            "reviewer": CodeReviewAgent(),
            "tester": TestGeneratorAgent(),
            "optimizer": OptimizationAgent(),
            "security": SecurityAuditor(),
        }

    async def run_parallel(self, tasks: Dict[str, str]) -> Dict[str, Any]:
        """Run multiple agents in parallel"""
        results = {}
        tasks_list = []

        for agent_name, prompt in tasks.items():
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                tasks_list.append(self._run_agent(agent_name, agent, prompt))

        completed = await asyncio.gather(*tasks_list)

        for agent_name, result in completed:
            results[agent_name] = result

        return results

    async def _run_agent(self, name: str, agent: HeadlessAgent, prompt: str):
        """Run single agent async"""
        result = await agent.run_async(prompt)
        return (name, result)

    def run_sequential(self, workflow: List[tuple]) -> List[Dict]:
        """Run agents in sequence with context passing"""
        results = []
        context = ""

        for agent_name, prompt_template in workflow:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                prompt = prompt_template.format(context=context)
                result = agent.run(prompt)
                results.append(result)

                # Extract output for next agent
                if "output" in result:
                    context = result["output"]

        return results


# ============================================
# UTILITY FUNCTIONS
# ============================================


def run_with_monitoring(agent: HeadlessAgent, prompt: str) -> Dict:
    """Run agent with performance monitoring"""
    import time

    start = time.time()
    result = agent.run(prompt)
    duration = time.time() - start

    result["execution_time"] = duration
    result["session_id"] = agent.config.session_id

    # Log to session manager
    log_path = (
        Path.home()
        / ".claude"
        / "headless_sessions"
        / f"{agent.config.session_id}.json"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "w") as f:
        json.dump(
            {
                "session_id": agent.config.session_id,
                "duration": duration,
                "model": agent.config.model.value,
                "prompt": prompt[:500],
                "result": result.get("output", "")[:500],
            },
            f,
            indent=2,
        )

    return result


def batch_process(agent: HeadlessAgent, prompts: List[str], max_parallel: int = 10):
    """Process multiple prompts with parallelization"""
    import concurrent.futures

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = [executor.submit(agent.run, prompt) for prompt in prompts]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return results


# ============================================
# CLI INTERFACE
# ============================================


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Specialized Headless Claude Agents")
    parser.add_argument(
        "agent",
        choices=[
            "speed",
            "code",
            "review",
            "test",
            "refactor",
            "debug",
            "architect",
            "security",
            "optimize",
        ],
    )
    parser.add_argument("prompt", help="Task for the agent")
    parser.add_argument("--language", default="python", help="Programming language")
    parser.add_argument("--framework", default="pytest", help="Test framework")
    parser.add_argument("--focus", default="performance", help="Refactoring focus")
    parser.add_argument("--target", default="latency", help="Optimization target")
    parser.add_argument("--timeout", type=int, default=300, help="Execution timeout")

    args = parser.parse_args()

    # Select agent
    agents = {
        "speed": SpeedAgent(),
        "code": CodeGeneratorAgent(args.language),
        "review": CodeReviewAgent(),
        "test": TestGeneratorAgent(args.framework),
        "refactor": RefactoringAgent(args.focus),
        "debug": DebuggerAgent(),
        "architect": ArchitectAgent(),
        "security": SecurityAuditor(),
        "optimize": OptimizationAgent(args.target),
    }

    agent = agents[args.agent]
    result = run_with_monitoring(agent, args.prompt)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
