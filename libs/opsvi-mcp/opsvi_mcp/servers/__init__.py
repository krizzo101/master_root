"""
MCP Server implementations for OPSVI

Available servers:
- claude_code: Original Claude Code MCP server
- claude_code_v2: Enhanced Claude Code with fire-and-forget pattern
- claude_code_v3: Next-gen with multi-agent support
- openai_codex: OpenAI GPT-4/Codex integration
- cursor_agent: Cursor IDE agent integration
- context_bridge: Context bridging between agents
"""

# Use lazy imports to avoid initialization issues
__all__ = [
    "claude_code",
    "claude_code_v2",
    "claude_code_v3",
    "openai_codex",
    "cursor_agent",
    "context_bridge",
]


def __getattr__(name):
    """Lazy import servers only when accessed"""
    if name == "claude_code":
        from . import claude_code

        return claude_code
    elif name == "claude_code_v2":
        from . import claude_code_v2

        return claude_code_v2
    elif name == "claude_code_v3":
        from . import claude_code_v3

        return claude_code_v3
    elif name == "openai_codex":
        from . import openai_codex

        return openai_codex
    elif name == "cursor_agent":
        from . import cursor_agent

        return cursor_agent
    elif name == "context_bridge":
        from . import context_bridge

        return context_bridge
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
