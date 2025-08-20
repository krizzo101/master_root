#!/usr/bin/env python3
"""Project Mapper CLI using shared interfaces

This module provides the main CLI entry point for the Project Mapper tool.
"""

import sys

sys.path.insert(0, "/home/opsvi/master_root/libs")

from pathlib import Path
from typing import Optional

import click

# Use shared interfaces
from opsvi_interfaces.cli import BaseCLI
from opsvi_interfaces.config import ConfigManager

SHARED_LIBS = True

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console

from proj_mapper.analysis.report import make_report, print_report_text

# Import CLI command groups
from proj_mapper.cli.commands import relationship_group
from proj_mapper.cli.config_handler import ConfigManager
from proj_mapper.cli.interactive import run_interactive_mode
from proj_mapper.cli.progress import LogHandler, ProgressReporter
from proj_mapper.core.project_manager import ProjectManager
from proj_mapper.output.config import GeneratorConfig, MapFormatType
from proj_mapper.output.storage import StorageManager
from proj_mapper.utils.json_encoder import EnumEncoder
from proj_mapper.version import __version__

# Configure logging
logger = logging.getLogger(__name__)
console = Console()


# Create a pass context class to share common objects
class Context:
    """Context object for sharing state between commands."""

    def __init__(self):
        """Initialize the context."""
        self.verbose = False
        self.quiet = False
        self.debug = False
        self.config_file = None
        self.config = None
        self.console = Console()
        self.progress = None
        self.config_manager = None


# Define the main command group
@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output")
@click.option("--debug", "-d", is_flag=True, help="Enable debug output")
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--log-dir", type=click.Path(), default="./log", help="Directory for log files"
)
@click.version_option(version=__version__, prog_name="Project Mapper")
@click.pass_context
def cli(ctx, verbose, quiet, debug, config_file, log_dir):
    """Project Mapper - Map and analyze project structure."""
    # Create the context object
    ctx.obj = Context()
    ctx.obj.verbose = verbose
    ctx.obj.quiet = quiet
    ctx.obj.debug = debug
    ctx.obj.config_file = config_file

    # Ensure log directory exists
    log_dir = Path(log_dir)
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    level = logging.DEBUG if debug else logging.INFO if verbose else logging.WARNING

    # Create file handler for all output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_log_file = log_dir / f"proj-mapper_{timestamp}.log"
    file_handler = logging.FileHandler(main_log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Create console handler with minimal output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING if quiet else logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # If debug mode is enabled, create separate debug log file
    if debug:
        debug_log_file = log_dir / f"proj_mapper_debug_{timestamp}.log"
        debug_handler = logging.FileHandler(debug_log_file, mode="w", encoding="utf-8")
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(file_formatter)
        root_logger.addHandler(debug_handler)
        logger.debug(f"Debug logging enabled. Debug log file: {debug_log_file}")

    logger.info(f"Log file: {main_log_file}")

    # Create progress reporter with minimal console output
    ctx.obj.progress = ProgressReporter(
        console=ctx.obj.console, quiet=quiet, verbose=verbose or debug
    )

    # Create config manager
    ctx.obj.config_manager = ConfigManager(config_file=config_file)

    # Log entry point
    logger.debug(
        f"Project Mapper CLI started with debug={debug}, verbose={verbose}, quiet={quiet}"
    )

    # Load configuration if possible
    try:
        if config_file:
            ctx.obj.config = ctx.obj.config_manager.load_config()
            logger.debug(f"Loaded configuration from {config_file}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        ctx.obj.config = None


# Register command groups
cli.add_command(relationship_group)


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--include", multiple=True, help="Glob patterns for files to include")
@click.option("--exclude", multiple=True, help="Glob patterns for files to exclude")
@click.option("--no-gitignore", is_flag=True, help="Disable .gitignore respect")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", "-d", is_flag=True, help="Enable debug output")
@click.option("--log-dir", type=click.Path(), help="Directory for log files")
@click.pass_context
def analyze(
    ctx, project_path, output, include, exclude, no_gitignore, verbose, debug, log_dir
):
    """Analyze a project and generate maps."""
    # Get context objects
    progress = ctx.obj.progress
    config_manager = ctx.obj.config_manager

    # Use log directory from context if not specified
    log_dir = Path(log_dir) if log_dir else Path("./log")
    log_dir.mkdir(exist_ok=True)

    # Create timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Configure logging for analysis
    logger_name = "proj_mapper.analyze"
    analyze_logger = logging.getLogger(logger_name)

    # Create analysis-specific log file
    analysis_log = log_dir / f"analysis_{timestamp}.log"
    file_handler = logging.FileHandler(analysis_log, mode="w", encoding="utf-8")
    file_handler.setLevel(
        logging.DEBUG if debug else logging.INFO if verbose else logging.WARNING
    )

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    # Remove any existing handlers
    for handler in analyze_logger.handlers[:]:
        analyze_logger.removeHandler(handler)

    # Add file handler
    analyze_logger.addHandler(file_handler)
    analyze_logger.setLevel(logging.DEBUG)

    # Create configuration
    config = {
        "include_patterns": list(include) if include else None,
        "exclude_patterns": list(exclude) if exclude else None,
        "respect_gitignore": not no_gitignore,  # Disable if --no-gitignore flag is set
        "format_type": "json",  # Default format
        "include_code": True,
        "include_documentation": True,
        "include_metadata": True,
        "enable_chunking": True,
        "max_tokens": 2048,
        "ai_optimize": True,
    }

    # Load base configuration
    base_config = ctx.obj.config or {}
    config.update(base_config)  # Base config overrides defaults

    # Create Configuration object
    from proj_mapper.core.config import Configuration

    config_obj = Configuration(**config)

    # Determine output path
    if not output:
        output_dir = os.path.join(project_path, ".maps")
        os.makedirs(output_dir, exist_ok=True)
        output = os.path.join(output_dir, "project_map.json")

    analyze_logger.info(f"Starting analysis of project: {project_path}")
    analyze_logger.info(f"Output will be saved to: {output}")
    analyze_logger.info(f"Analysis log file: {analysis_log}")

    if debug:
        analyze_logger.debug("Debug mode enabled")
        analyze_logger.debug(f"Configuration: {config}")

    try:
        # Create project manager with configuration
        manager = ProjectManager(config=config_obj)

        # Run analysis
        project_map = manager.analyze_project(project_path)

        # Save output
        storage = StorageManager()
        storage.store_map(project_map, project_path, config_obj)

        analyze_logger.info("Analysis completed successfully")
        return 0

    except Exception as e:
        analyze_logger.error(f"Error during analysis: {str(e)}")
        if debug:
            analyze_logger.exception("Detailed error information:")
        return 1


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--full", is_flag=True, help="Perform a full update")
@click.pass_context
def update(ctx, project_path, full):
    """Update project maps."""
    # Get context objects
    progress = ctx.obj.progress

    logger.info(f"Updating maps for project: {project_path}")
    logger.info(f"Update type: {'Full' if full else 'Incremental'}")

    try:
        # Start progress
        progress.start_progress(total=100, description="Updating project maps")

        # Get project manager from context
        config_obj = (
            ctx.obj.config_manager.load_config() if ctx.obj.config_file else None
        )
        manager = ProjectManager(config=config_obj)

        # Run update
        manager.update_project(project_path, full=full)

        progress.update_progress(advance=100)
        progress.stop_progress()
        progress.log("Project maps updated successfully")

    except Exception as e:
        progress.stop_progress()
        logger.error(f"Error updating project maps: {e}")
        raise click.ClickException(f"Error updating project maps: {e}")


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.pass_context
def info(ctx, project_path):
    """Get information about a project."""
    # Get context objects
    console = ctx.obj.console

    # Get the project name from the path
    project_name = Path(project_path).name

    # Use the StorageManager to find maps
    storage = StorageManager()

    # Try to get the latest map
    latest_map_path = storage.get_latest_map(project_path)

    if not latest_map_path:
        logger.error(f"No maps found for project: {project_path}")
        raise click.ClickException(
            f"No maps found for project: {project_path}.\n"
            f"Run 'analyze' command first."
        )

    # Load the map file
    try:
        with open(latest_map_path, "r") as f:
            project_map = json.load(f)
    except Exception as e:
        logger.error(f"Error loading project map: {e}")
        raise click.ClickException(f"Error loading project map: {e}")

    # Display project information
    from rich.table import Table

    # Basic info
    table = Table(title="Project Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Project Name", project_map.get("project_name", "Unknown"))
    table.add_row("Schema Version", project_map.get("schema_version", "Unknown"))
    table.add_row("Timestamp", project_map.get("timestamp", "Unknown"))

    # Statistics
    files_count = len(project_map.get("files", []))
    modules_count = len(project_map.get("modules", []))
    relationships_count = len(project_map.get("relationships", []))

    table.add_row("Files Count", str(files_count))
    table.add_row("Modules Count", str(modules_count))
    table.add_row("Relationships Count", str(relationships_count))

    console.print(table)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode."""
    return run_interactive_mode()


@cli.command()
@click.option(
    "--port", "-p", type=int, default=5000, help="Port to run the web server on"
)
@click.option("--host", "-h", default="127.0.0.1", help="Host to run the web server on")
@click.option("--debug", is_flag=True, help="Run in debug mode")
@click.pass_context
def web(ctx, port, host, debug):
    """Start the web interface."""
    logger.info(f"Starting web interface on {host}:{port}")

    try:
        # Check if Flask is installed
        try:
            from proj_mapper.web.app import app
        except ImportError:
            raise click.ClickException(
                "Flask is required for the web interface. "
                "Install it with: pip install flask"
            )

        # Start the Flask app
        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        logger.error(f"Error starting web interface: {e}")
        raise click.ClickException(f"Error starting web interface: {e}")


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "list_config", is_flag=True, help="List all configuration")
@click.option("--save", type=click.Path(), help="Save configuration to file")
@click.pass_context
def config(ctx, key, value, list_config, save):
    """View or modify configuration."""
    # Get context objects
    console = ctx.obj.console
    config_manager = ctx.obj.config_manager

    # Load current configuration
    current_config = ctx.obj.config or config_manager._get_default_config()

    if list_config or (not key and not save):
        # Display current configuration
        from rich.table import Table

        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value")

        def add_config_rows(config, prefix=""):
            for k, v in config.items():
                if isinstance(v, dict):
                    add_config_rows(v, f"{prefix}{k}.")
                else:
                    table.add_row(f"{prefix}{k}", str(v))

        add_config_rows(current_config)
        console.print(table)

    elif key and value is None:
        # Get specific configuration value
        keys = key.split(".")
        config = current_config

        try:
            for k in keys:
                config = config[k]

            console.print(f"{key} = {config}")
        except (KeyError, TypeError):
            logger.error(f"Configuration key not found: {key}")
            raise click.ClickException(f"Configuration key not found: {key}")

    elif key and value is not None:
        # Set configuration value
        keys = key.split(".")
        config = current_config

        # Parse value
        if value.lower() in ["true", "yes"]:
            value = True
        elif value.lower() in ["false", "no"]:
            value = False
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
            value = float(value)

        # Set the value
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

        # Update context config
        ctx.obj.config = current_config

        console.print(f"Set {key} = {value}")

    if save:
        # Save configuration to file
        try:
            config_manager.save_config(save, current_config)
            console.print(f"Configuration saved to: {save}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise click.ClickException(f"Error saving configuration: {e}")


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file for the visualization"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["dot", "html"], case_sensitive=False),
    default="dot",
    show_default=True,
    help="Output format for the visualization",
)
@click.pass_context
def visualize(ctx, project_path, output, format):
    """Generate a visualization of a project map."""
    console = ctx.obj.console
    storage = StorageManager()

    try:
        latest_map_path = storage.get_latest_map(project_path)
        if not latest_map_path:
            console.print(
                f"[bold red]Error:[/] No project map found for '{project_path}'."
            )
            console.print("Please run the 'analyze' command first.")
            return

        project_map = storage.load_map(project_path)
        if not project_map:
            console.print(
                f"[bold red]Error:[/] Could not load project map from '{latest_map_path}'."
            )
            return

        from proj_mapper.output.visualization.base import (
            VisualizationConfig,
            VisualizationFormat,
        )
        from proj_mapper.output.visualization.generator import VisualizationGenerator

        generator = VisualizationGenerator()

        # Resolve output path and extension
        fmt_enum = (
            VisualizationFormat.DOT
            if format.lower() == "dot"
            else VisualizationFormat.HTML
        )

        if not output:
            default_name = (
                "visualization.dot"
                if fmt_enum == VisualizationFormat.DOT
                else "visualization.html"
            )
            output = Path(project_path) / ".maps" / default_name
        else:
            output = Path(output)

        # Ensure extension matches format if no suffix provided
        if output.suffix == "":
            output = output.with_suffix(
                ".dot" if fmt_enum == VisualizationFormat.DOT else ".html"
            )
        else:
            # If suffix doesn't match desired format, adjust it
            desired_suffix = ".dot" if fmt_enum == VisualizationFormat.DOT else ".html"
            if output.suffix.lower() != desired_suffix:
                output = output.with_suffix(desired_suffix)

        output.parent.mkdir(parents=True, exist_ok=True)

        # Generate visualization with selected format
        generator = VisualizationGenerator(
            config=VisualizationConfig(output_format=fmt_enum)
        )
        generated_path = generator.generate(project_map, output)

        # Verify file existence before claiming success
        if not generated_path or not Path(generated_path).exists():
            raise click.ClickException(
                f"Visualization generation reported success but no file found at: {output}"
            )

        console.print(
            f"[bold green]Success:[/] Visualization saved to [cyan]{Path(generated_path).resolve()}[/cyan]"
        )

    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        raise click.ClickException(f"Error generating visualization: {e}")


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--json", "json_out", is_flag=True, help="Output JSON instead of text")
@click.option(
    "--top", type=int, default=15, show_default=True, help="Top N hubs/components"
)
@click.pass_context
def report(ctx, project_path, json_out, top):
    """Compute actionable metrics (hubs, orphans, cycles, package coupling)."""
    storage = StorageManager()
    try:
        # Load map
        project_map = storage.load_map(project_path)
        data = project_map.to_dict()
        rep = make_report(data, top_n=top)
        if json_out:
            import json as _json

            click.echo(_json.dumps(rep, indent=2))
        else:
            print_report_text(rep)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise click.ClickException(f"Error generating report: {e}")


if __name__ == "__main__":
    cli()
