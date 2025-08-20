"""
CLI Interface Base Classes
Provides base classes and decorators for building CLI applications
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

import click


@dataclass
class Command:
    """Represents a CLI command"""

    name: str
    function: Callable
    help: str
    options: List[Any] = None

    def __post_init__(self):
        if self.options is None:
            self.options = []


class BaseCLI:
    """Base class for CLI applications"""

    def __init__(self, name: str = None, version: str = "0.1.0"):
        """Initialize CLI application"""
        self.name = name or "cli"
        self.version = version
        self.commands: Dict[str, Command] = {}
        self.context = {}

    def add_command(self, command: Command):
        """Add a command to the CLI"""
        self.commands[command.name] = command

    def run(self, args: List[str] = None):
        """Run the CLI application"""
        # In real implementation, this would parse args and execute commands
        # For now, we'll use click's built-in functionality
        pass

    def get_context(self) -> Dict[str, Any]:
        """Get CLI context"""
        return self.context

    def set_context(self, key: str, value: Any):
        """Set context value"""
        self.context[key] = value


def command(name: str = None, **kwargs):
    """Decorator for CLI commands"""

    def decorator(func: Callable) -> Callable:
        # Wrap with click command
        cmd = click.command(name=name, **kwargs)(func)

        # Store metadata
        cmd._cli_command = Command(
            name=name or func.__name__,
            function=func,
            help=kwargs.get("help", func.__doc__ or ""),
        )

        return cmd

    return decorator


class CLIGroup:
    """Group of CLI commands"""

    def __init__(self, name: str, help: str = None):
        """Initialize command group"""
        self.name = name
        self.help = help
        self.commands: List[Command] = []

    def add_command(self, command: Command):
        """Add command to group"""
        self.commands.append(command)

    def get_click_group(self) -> click.Group:
        """Convert to click Group"""
        group = click.Group(name=self.name, help=self.help)

        for cmd in self.commands:
            if hasattr(cmd.function, "__click_params__"):
                group.add_command(cmd.function)

        return group
