"""
Claude Command Factory - Comprehensive command builder based on headless guide
Implements all optimizations and patterns from claude_headless_complete_guide.md
"""

import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentProfile(Enum):
    """Agent profiles from the headless guide"""

    SPEED_DEMON = "speed_demon"  # 3-5s, simple tasks
    PRODUCTION = "production"  # 5-20s, balanced
    QUALITY_CHAMPION = "quality_champion"  # 20-100s, thorough
    BULK_PROCESSOR = "bulk_processor"  # Optimized for many tasks
    CI_CD = "ci_cd"  # For pipeline integration


class TaskComplexity(Enum):
    """Task complexity levels"""

    SIMPLE = "simple"  # Quick queries, calculations
    NORMAL = "normal"  # Standard development tasks
    COMPLEX = "complex"  # Architecture, design, multi-step
    BULK = "bulk"  # Many similar operations


class PermissionMode(Enum):
    """Permission modes for different safety levels"""

    DANGEROUS_SKIP = "dangerously-skip-permissions"  # Fastest, least safe
    ACCEPT_EDITS = "acceptEdits"  # Production safe, auto-accept
    BYPASS = "bypassPermissions"  # Skip all permissions
    DEFAULT = None  # Use default (will prompt)


@dataclass
class CommandConfig:
    """Configuration for building Claude commands"""

    # Core settings
    model: str = "sonnet"  # Default to fastest
    profile: AgentProfile = AgentProfile.PRODUCTION
    complexity: TaskComplexity = TaskComplexity.NORMAL

    # Performance optimizations
    use_minimal_mcp: bool = True  # 80% faster
    permission_mode: PermissionMode = PermissionMode.ACCEPT_EDITS
    output_format: str = "json"  # Structured output

    # Session tracking
    session_id: Optional[str] = None  # Auto-generate if not provided

    # Tool restrictions
    allowed_tools: List[str] = field(
        default_factory=lambda: ["Write", "Read", "Edit", "Bash", "TodoWrite"]
    )

    # Workspace
    workspace_dirs: List[Path] = field(default_factory=list)

    # Agent specialization
    system_prompt: Optional[str] = None
    agent_role: Optional[str] = None

    # Advanced options
    verbose: bool = False
    debug: bool = False  # Enable Claude debug mode (-d flag)
    capture_debug_output: bool = False  # Capture debug output for app logs
    timeout: Optional[int] = None  # In seconds
    max_retries: int = 0
    continuation_prompt: bool = False  # For retry scenarios

    # Resource paths
    mcp_config_path: Optional[Path] = None


class ClaudeCommandFactory:
    """
    Factory for building optimized Claude commands based on the headless guide.
    Implements all performance optimizations and patterns.
    """

    # Performance benchmarks from guide
    PERFORMANCE_PROFILES = {
        AgentProfile.SPEED_DEMON: {
            "model": "sonnet",
            "time": "3-5s",
            "use_minimal_mcp": True,
            "permission_mode": PermissionMode.DANGEROUS_SKIP,
        },
        AgentProfile.PRODUCTION: {
            "model": "opus",
            "time": "5-20s",
            "use_minimal_mcp": True,
            "permission_mode": PermissionMode.ACCEPT_EDITS,
        },
        AgentProfile.QUALITY_CHAMPION: {
            "model": "opus",
            "time": "20-100s",
            "use_minimal_mcp": False,  # May need full MCP
            "permission_mode": PermissionMode.ACCEPT_EDITS,
        },
        AgentProfile.BULK_PROCESSOR: {
            "model": "sonnet",
            "time": "3-5s each",
            "use_minimal_mcp": True,
            "permission_mode": PermissionMode.DANGEROUS_SKIP,
        },
        AgentProfile.CI_CD: {
            "model": "sonnet",
            "time": "10-20s",
            "use_minimal_mcp": True,
            "permission_mode": PermissionMode.ACCEPT_EDITS,
        },
    }

    # Role-specific system prompts
    ROLE_PROMPTS = {
        "architect": "You are a system architect. Design scalable, maintainable solutions. Consider performance, security, and future growth.",
        "developer": "You are an expert developer. Write clean, efficient, production-ready code with proper error handling.",
        "tester": "You are a QA specialist. Write comprehensive tests covering edge cases, error conditions, and performance.",
        "reviewer": "You are a senior code reviewer. Provide detailed, constructive feedback. Check for bugs, performance, and best practices.",
        "debugger": "You are a debugging expert. Systematically identify and fix issues. Include detailed logging and error messages.",
        "documenter": "You are a documentation specialist. Write clear, comprehensive docs with examples and usage patterns.",
        "security": "You are a security expert. Identify vulnerabilities, implement secure practices, and validate inputs.",
        "performance": "You are a performance optimizer. Focus on speed, memory usage, and scalability. Profile and benchmark.",
        "refactor": "You are a refactoring specialist. Improve code structure, reduce complexity, and enhance maintainability.",
        "researcher": "You are a research specialist. Find and analyze relevant information thoroughly. Cite sources.",
        "frontend": "You are a frontend specialist. Create responsive, accessible, performant user interfaces.",
        "backend": "You are a backend specialist. Design efficient APIs, handle data processing, ensure reliability.",
        "database": "You are a database expert. Design schemas, optimize queries, ensure data integrity.",
        "devops": "You are a DevOps specialist. Create deployment configs, CI/CD pipelines, and monitoring.",
        "analyst": "You are a business analyst. Understand requirements, identify gaps, propose solutions.",
    }

    # Complexity-based system prompt additions
    COMPLEXITY_PROMPTS = {
        TaskComplexity.SIMPLE: "Be concise. Provide direct answers.",
        TaskComplexity.NORMAL: "Be thorough but focused. Include error handling.",
        TaskComplexity.COMPLEX: "Be comprehensive. Consider edge cases, provide alternatives, include detailed documentation.",
        TaskComplexity.BULK: "Process efficiently. Maintain consistency across operations.",
    }

    def __init__(self, base_mcp_config_path: Optional[Path] = None):
        """
        Initialize the command factory.

        Args:
            base_mcp_config_path: Path to minimal MCP config (creates if not exists)
        """
        if base_mcp_config_path:
            self.mcp_config_path = base_mcp_config_path
        else:
            # Default to project config
            self.mcp_config_path = (
                Path(__file__).parent.parent.parent / "config" / "claude_minimal.json"
            )

        # Ensure minimal MCP config exists
        self._ensure_minimal_mcp_config()

    def _ensure_minimal_mcp_config(self):
        """Ensure the minimal MCP config file exists"""
        if not self.mcp_config_path.exists():
            self.mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
            self.mcp_config_path.write_text('{"mcpServers": {}}')

    def build_command(
        self, prompt: str, config: Optional[CommandConfig] = None, **kwargs
    ) -> List[str]:
        """
        Build an optimized Claude command based on configuration.

        Args:
            prompt: The task prompt
            config: Command configuration (uses defaults if not provided)
            **kwargs: Override specific config values

        Returns:
            List of command arguments
        """
        # Use provided config or create default
        if config is None:
            config = CommandConfig()

        # Apply any kwargs overrides
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # Auto-detect profile based on complexity if not set
        if config.profile == AgentProfile.PRODUCTION and config.complexity:
            config = self._auto_select_profile(config)

        # Build base command
        cmd = ["claude"]

        # Debug mode (NOTE: reduces performance by ~30% according to guide)
        if config.debug:
            cmd.append("-d")  # Debug flag must come before -p

        cmd.append("-p")  # Always use print/headless mode

        # Add prompt (from file or direct)
        if len(prompt) > 1000 or "\n" in prompt:
            # Use file for long/multiline prompts
            cmd.append(f"@-")  # Will pipe via stdin
        else:
            cmd.extend(["--", prompt])

        # Apply profile optimizations
        profile_settings = self.PERFORMANCE_PROFILES.get(config.profile, {})

        # Model selection (critical for performance)
        model = profile_settings.get("model", config.model)
        cmd.extend(["--model", model])

        # MCP optimization (80% speed improvement)
        if config.use_minimal_mcp:
            cmd.append("--strict-mcp-config")
            if config.mcp_config_path or self.mcp_config_path:
                mcp_path = config.mcp_config_path or self.mcp_config_path
                cmd.extend(["--mcp-config", str(mcp_path)])

        # Permission mode (5-15s savings)
        permission_mode = profile_settings.get("permission_mode", config.permission_mode)
        if permission_mode and permission_mode != PermissionMode.DEFAULT:
            if permission_mode == PermissionMode.DANGEROUS_SKIP:
                cmd.append("--dangerously-skip-permissions")
            else:
                cmd.extend(["--permission-mode", permission_mode.value])

        # Output format
        if config.output_format:
            cmd.extend(["--output-format", config.output_format])
            # Special case for stream-json
            if config.output_format == "stream-json" and config.verbose:
                cmd.append("--verbose")

        # Session tracking (critical for debugging)
        session_id = config.session_id or str(uuid.uuid4())
        cmd.extend(["--session-id", session_id])

        # Tool restrictions (security and focus)
        if config.allowed_tools:
            tools_str = ",".join(config.allowed_tools)
            cmd.extend(["--allowed-tools", tools_str])

        # Workspace directories
        for workspace_dir in config.workspace_dirs:
            cmd.extend(["--add-dir", str(workspace_dir)])

        # System prompt construction
        system_prompt = self._build_system_prompt(config)
        if system_prompt:
            cmd.extend(["--append-system-prompt", system_prompt])

        # Advanced options
        if config.verbose and config.output_format != "stream-json":
            cmd.append("--verbose")

        if config.timeout:
            # Note: Claude CLI doesn't have direct timeout, would need wrapper
            pass

        return cmd

    def _auto_select_profile(self, config: CommandConfig) -> CommandConfig:
        """Auto-select optimal profile based on task complexity"""
        complexity_profile_map = {
            TaskComplexity.SIMPLE: AgentProfile.SPEED_DEMON,
            TaskComplexity.NORMAL: AgentProfile.PRODUCTION,
            TaskComplexity.COMPLEX: AgentProfile.QUALITY_CHAMPION,
            TaskComplexity.BULK: AgentProfile.BULK_PROCESSOR,
        }

        if config.complexity in complexity_profile_map:
            config.profile = complexity_profile_map[config.complexity]

        return config

    def _build_system_prompt(self, config: CommandConfig) -> Optional[str]:
        """Build comprehensive system prompt based on role and complexity"""
        prompts = []

        # Add role-specific prompt
        if config.agent_role and config.agent_role in self.ROLE_PROMPTS:
            prompts.append(self.ROLE_PROMPTS[config.agent_role])

        # Add complexity-based instructions
        if config.complexity in self.COMPLEXITY_PROMPTS:
            prompts.append(self.COMPLEXITY_PROMPTS[config.complexity])

        # Add custom system prompt
        if config.system_prompt:
            prompts.append(config.system_prompt)

        # Add continuation prompt for retries
        if config.continuation_prompt:
            prompts.append("Continue from where you left off. Complete any unfinished tasks.")

        return " ".join(prompts) if prompts else None

    def build_parallel_commands(
        self, tasks: List[Dict[str, Any]], base_config: Optional[CommandConfig] = None
    ) -> List[List[str]]:
        """
        Build commands for parallel execution of multiple tasks.

        Args:
            tasks: List of task dictionaries with 'prompt' and optional config overrides
            base_config: Base configuration for all tasks

        Returns:
            List of command lists ready for parallel execution
        """
        commands = []
        base_config = base_config or CommandConfig(profile=AgentProfile.BULK_PROCESSOR)

        for task in tasks:
            # Extract prompt
            prompt = task.get("prompt", task.get("description", ""))

            # Create task-specific config
            task_config = CommandConfig(
                model=base_config.model,
                profile=base_config.profile,
                complexity=task.get("complexity", base_config.complexity),
                use_minimal_mcp=base_config.use_minimal_mcp,
                permission_mode=base_config.permission_mode,
                output_format=base_config.output_format,
                session_id=str(uuid.uuid4()),  # Always generate valid UUID
                allowed_tools=task.get("allowed_tools", base_config.allowed_tools),
                workspace_dirs=task.get("workspace_dirs", base_config.workspace_dirs),
                system_prompt=task.get("system_prompt", base_config.system_prompt),
                agent_role=task.get("role", task.get("agent_type", base_config.agent_role)),
            )

            # Build command
            cmd = self.build_command(prompt, task_config)
            commands.append(cmd)

        return commands

    def get_performance_estimate(self, config: CommandConfig) -> str:
        """Get estimated execution time based on configuration"""
        profile_times = {
            AgentProfile.SPEED_DEMON: "3-5 seconds",
            AgentProfile.PRODUCTION: "5-20 seconds",
            AgentProfile.QUALITY_CHAMPION: "20-100 seconds",
            AgentProfile.BULK_PROCESSOR: "3-5 seconds per task",
            AgentProfile.CI_CD: "10-20 seconds",
        }
        return profile_times.get(config.profile, "10-30 seconds")

    def create_retry_command(self, original_cmd: List[str], session_id: str) -> List[str]:
        """Create a retry command that continues from previous attempt"""
        retry_cmd = original_cmd.copy()

        # Update session ID to maintain continuity
        for i, arg in enumerate(retry_cmd):
            if arg == "--session-id" and i + 1 < len(retry_cmd):
                retry_cmd[i + 1] = session_id
                break

        # Add continuation prompt
        for i, arg in enumerate(retry_cmd):
            if arg == "--append-system-prompt" and i + 1 < len(retry_cmd):
                retry_cmd[
                    i + 1
                ] += " Continue from where you left off. Complete any unfinished tasks."
                break
        else:
            retry_cmd.extend(
                [
                    "--append-system-prompt",
                    "Continue from where you left off. Complete any unfinished tasks.",
                ]
            )

        return retry_cmd

    @staticmethod
    def create_monitoring_command(session_id: str) -> str:
        """Create command to monitor a running session"""
        return f"tail -f ~/.claude/projects/*/{session_id}.jsonl | jq '.type'"

    @staticmethod
    def create_analysis_commands(session_id: str) -> Dict[str, str]:
        """Create commands for post-execution analysis"""
        return {
            "view_full": f"cat ~/.claude/projects/*/{session_id}.jsonl | jq '.'",
            "extract_errors": f"cat ~/.claude/projects/*/{session_id}.jsonl | jq 'select(.error != null)'",
            "get_responses": f"cat ~/.claude/projects/*/{session_id}.jsonl | jq -r '.message.content[0].text // empty'",
        }


# Convenience functions for common scenarios
def create_speed_demon_command(prompt: str, **kwargs) -> List[str]:
    """Create command optimized for maximum speed (3-5s)"""
    factory = ClaudeCommandFactory()
    config = CommandConfig(
        profile=AgentProfile.SPEED_DEMON, complexity=TaskComplexity.SIMPLE, **kwargs
    )
    return factory.build_command(prompt, config)


def create_production_command(prompt: str, workspace: Optional[Path] = None, **kwargs) -> List[str]:
    """Create balanced production command (5-20s)"""
    factory = ClaudeCommandFactory()
    config = CommandConfig(
        profile=AgentProfile.PRODUCTION,
        complexity=TaskComplexity.NORMAL,
        workspace_dirs=[workspace] if workspace else [],
        **kwargs,
    )
    return factory.build_command(prompt, config)


def create_quality_command(prompt: str, **kwargs) -> List[str]:
    """Create command for complex, high-quality output (20-100s)"""
    factory = ClaudeCommandFactory()
    config = CommandConfig(
        profile=AgentProfile.QUALITY_CHAMPION,
        complexity=TaskComplexity.COMPLEX,
        system_prompt="Be thorough. Include error handling, tests, and documentation.",
        **kwargs,
    )
    return factory.build_command(prompt, config)


def create_specialized_agent_command(prompt: str, role: str, **kwargs) -> List[str]:
    """Create command for a specialized agent role"""
    factory = ClaudeCommandFactory()
    config = CommandConfig(agent_role=role, complexity=TaskComplexity.NORMAL, **kwargs)
    return factory.build_command(prompt, config)


if __name__ == "__main__":
    # Example usage
    factory = ClaudeCommandFactory()

    # Example 1: Speed demon for simple task
    cmd1 = create_speed_demon_command("What is 2+2?")
    print("Speed Demon:", " ".join(cmd1))

    # Example 2: Production command with workspace
    cmd2 = create_production_command(
        "Create a REST API with user authentication", workspace=Path("/tmp/project")
    )
    print("Production:", " ".join(cmd2))

    # Example 3: Quality command for complex task
    cmd3 = create_quality_command("Design and implement a distributed caching system")
    print("Quality:", " ".join(cmd3))

    # Example 4: Specialized agent
    cmd4 = create_specialized_agent_command(
        "Review this code for security vulnerabilities", role="security"
    )
    print("Security Agent:", " ".join(cmd4))

    # Example 5: Parallel commands
    parallel_tasks = [
        {"prompt": "Design the architecture", "role": "architect"},
        {"prompt": "Write the implementation", "role": "developer"},
        {"prompt": "Create test suite", "role": "tester"},
    ]
    parallel_cmds = factory.build_parallel_commands(parallel_tasks)
    print(f"Parallel: {len(parallel_cmds)} commands ready")
