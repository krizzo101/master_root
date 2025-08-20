"""
CLI Interface Base Classes
Provides base classes and decorators for building CLI applications
"""

import asyncio
import sys
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

import click


@dataclass
class Command:
    """Represents a CLI command"""

    name: str
    function: Callable
    help: str
    options: List[Any] = None
    arguments: List[Any] = None
    is_group: bool = False
    parent: Optional[str] = None

    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.arguments is None:
            self.arguments = []


class BaseCLI:
    """Base class for CLI applications"""

    def __init__(self, name: str = None, version: str = "0.1.0", help: str = None):
        """Initialize CLI application"""
        self.name = name or "cli"
        self.version = version
        self.help = help or f"{self.name} CLI application"
        self.commands: Dict[str, Command] = {}
        self.groups: Dict[str, click.Group] = {}
        self.context = {}
        self._cli_group = None
        self._setup_cli()

    def _setup_cli(self):
        """Setup the main CLI group"""

        @click.group(name=self.name, help=self.help)
        @click.version_option(version=self.version)
        @click.pass_context
        def cli(ctx):
            """Main CLI entry point"""
            ctx.ensure_object(dict)
            ctx.obj["cli"] = self
            ctx.obj.update(self.context)

        self._cli_group = cli

    def add_command(self, command: Command):
        """Add a command to the CLI"""
        self.commands[command.name] = command

        if command.is_group:
            # Create a group
            group = click.Group(name=command.name, help=command.help)
            self.groups[command.name] = group
            self._cli_group.add_command(group)
        else:
            # Add regular command
            if command.parent and command.parent in self.groups:
                self.groups[command.parent].add_command(command.function)
            else:
                self._cli_group.add_command(command.function)

    def command(self, name: str = None, **kwargs):
        """Decorator to register a command"""

        def decorator(func: Callable) -> Callable:
            cmd_name = name or func.__name__

            # Wrap with click command
            click_cmd = click.command(name=cmd_name, **kwargs)(func)

            # Create Command object
            cmd = Command(
                name=cmd_name,
                function=click_cmd,
                help=kwargs.get("help", func.__doc__ or ""),
                parent=kwargs.get("parent", None),
            )

            # Register the command
            self.add_command(cmd)

            return func

        return decorator

    def group(self, name: str = None, **kwargs):
        """Decorator to register a command group"""

        def decorator(func: Callable) -> Callable:
            grp_name = name or func.__name__

            # Create Command object for group
            cmd = Command(
                name=grp_name,
                function=func,
                help=kwargs.get("help", func.__doc__ or ""),
                is_group=True,
            )

            # Register the group
            self.add_command(cmd)

            return func

        return decorator

    def run(self, args: List[str] = None):
        """Run the CLI application"""
        try:
            if args:
                self._cli_group(args, standalone_mode=False)
            else:
                self._cli_group(standalone_mode=True)
        except click.ClickException as e:
            e.show()
            sys.exit(e.exit_code)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    def get_context(self) -> Dict[str, Any]:
        """Get CLI context"""
        return self.context

    def set_context(self, key: str, value: Any):
        """Set context value"""
        self.context[key] = value


def async_command(name: str = None, **kwargs):
    """Decorator for async CLI commands"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))

        # Wrap with click command
        cmd = click.command(name=name, **kwargs)(wrapper)

        # Store metadata
        cmd._cli_command = Command(
            name=name or func.__name__,
            function=func,
            help=kwargs.get("help", func.__doc__ or ""),
        )

        return cmd

    return decorator


class CLIApplication:
    """Full-featured CLI application with automatic command discovery"""

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        help: str = None,
        auto_discover: bool = True,
    ):
        """Initialize CLI application

        Args:
            name: Application name
            version: Application version
            help: Help text
            auto_discover: Automatically discover commands from methods
        """
        self.cli = BaseCLI(name=name, version=version, help=help)
        self.auto_discover = auto_discover

        if auto_discover:
            self._discover_commands()

    def _discover_commands(self):
        """Automatically discover command methods"""
        for attr_name in dir(self):
            if attr_name.startswith("cmd_"):
                method = getattr(self, attr_name)
                if callable(method):
                    # Extract command name
                    cmd_name = attr_name[4:].replace("_", "-")

                    # Register as command
                    self.cli.command(name=cmd_name)(method)

    def run(self, args: List[str] = None):
        """Run the CLI application"""
        return self.cli.run(args)

    def add_command(self, func: Callable, name: str = None, **kwargs):
        """Manually add a command"""
        return self.cli.command(name=name, **kwargs)(func)

    def add_group(self, name: str, help: str = None) -> click.Group:
        """Add a command group"""

        @self.cli.group(name=name, help=help)
        def group():
            pass

        return self.cli.groups[name]


class CLIGroup:
    """Group of CLI commands with enhanced functionality"""

    def __init__(self, name: str, help: str = None, parent: BaseCLI = None):
        """Initialize command group"""
        self.name = name
        self.help = help
        self.parent = parent
        self.commands: List[Command] = []
        self._click_group = None
        self._setup_group()

    def _setup_group(self):
        """Setup the click group"""

        @click.group(name=self.name, help=self.help)
        @click.pass_context
        def group(ctx):
            ctx.ensure_object(dict)
            ctx.obj["group"] = self

        self._click_group = group

    def command(self, name: str = None, **kwargs):
        """Decorator to add command to group"""

        def decorator(func: Callable) -> Callable:
            cmd_name = name or func.__name__

            # Wrap with click command
            click_cmd = click.command(name=cmd_name, **kwargs)(func)

            # Add to group
            self._click_group.add_command(click_cmd)

            # Store in commands list
            cmd = Command(
                name=cmd_name,
                function=click_cmd,
                help=kwargs.get("help", func.__doc__ or ""),
                parent=self.name,
            )
            self.commands.append(cmd)

            return func

        return decorator

    def add_command(self, command: Command):
        """Add command to group"""
        self.commands.append(command)
        if hasattr(command.function, "__click_params__"):
            self._click_group.add_command(command.function)

    def get_click_group(self) -> click.Group:
        """Get the click Group object"""
        return self._click_group


def create_cli(
    name: str, version: str = "0.1.0", commands: List[Dict[str, Any]] = None
) -> BaseCLI:
    """Factory function to create a CLI application

    Args:
        name: Application name
        version: Application version
        commands: List of command specifications

    Returns:
        Configured BaseCLI instance
    """
    cli = BaseCLI(name=name, version=version)

    if commands:
        for cmd_spec in commands:
            # Create command from specification
            @cli.command(name=cmd_spec["name"], help=cmd_spec.get("help", ""))
            @click.pass_context
            def cmd(ctx, **kwargs):
                # Execute command handler
                handler = cmd_spec.get("handler")
                if handler:
                    return handler(ctx, **kwargs)

    return cli
