"""
Multi-Agent Orchestration and Automation CLI Tool
Entry point and CLI command definitions.
"""
import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)
import logging
from loguru import logger
from multiagent_cli.config import AppConfig, get_config, load_dotenv_config
from multiagent_cli.input_parser import parse_and_validate_input
from multiagent_cli.orchestrator import OrchestrationEngine
from multiagent_cli.logs import configure_logging, get_log_file_path
from multiagent_cli.response_aggregator import aggregate_responses

app = typer.Typer(
    add_completion=True,
    help="""
Multi-Agent Orchestration and Automation CLI Tool

Example:
    python -m multiagent_cli.main run --input-file workloads/sample_input.json
""",
)

console = Console()


def cli_exception_handler(exc_type, exc, tb):
    logger.opt(exception=exc).error(f"Fatal error: {exc}")
    console.print(f"[bold red]Error: {exc}[/bold red]")
    sys.exit(1)


sys.excepthook = cli_exception_handler


@app.command()
def run(
    input_file: Path = typer.Option(
        ...,
        "--input-file",
        "-i",
        exists=True,
        readable=True,
        help="Path to workflows JSON input file.",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging."
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress most output, only show errors."
    ),
    log_file: Path = typer.Option(
        get_log_file_path(), "--log-file", help="Write logs to a file."
    ),
    config_file: Path = typer.Option(
        None,
        "--config",
        "-c",
        exists=False,
        help="Optional path to configuration file (.env or YAML).",
    ),
    output_file: Path = typer.Option(
        None,
        "--output-file",
        "-o",
        exists=False,
        help="Path to write aggregated JSON results.",
    ),
):
    """Run workloads described in the input JSON, orchestrated by multiple agents."""
    # Load config and environment
    load_dotenv_config(config_file)
    config = get_config()

    configure_logging(log_file, verbose, quiet)
    logger.info(f"Loading input file: {input_file}")
    input_data = parse_and_validate_input(input_file)
    if not input_data:
        logger.error("Input data invalid or loading failed.")
        sys.exit(100)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            "[green]Executing multi-agent orchestration...", total=100
        )

        try:
            orchestrator = OrchestrationEngine(input_data, config, logger)
            agent_outputs = orchestrator.run(progress, progress_task=task)
        except Exception as exc:
            logger.opt(exception=exc).error("Workflow execution failed.")
            console.print(f"[bold red]Workflow execution failed: {exc}[/bold red]")
            sys.exit(110)
        progress.update(task, advance=100 - progress.tasks[0].completed)

    # Aggregate and persist results
    results = aggregate_responses(agent_outputs)
    if output_file:
        try:
            import json

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            console.print(
                f"[bold green]Aggregated results written to: {output_file}[/bold green]"
            )
        except Exception as exc:
            logger.opt(exception=exc).error(
                f"Failed to write results to file: {output_file}"
            )
            console.print(f"[yellow]Could not write results file: {exc}[/yellow]")
    else:
        import rich

        console.print("[bold cyan]Aggregated agent results:[/bold cyan]")
        from rich.syntax import Syntax
        import json

        syntax = Syntax(
            json.dumps(results, indent=2), "json", theme="monokai", line_numbers=True
        )
        rich.print(syntax)

    logger.success("Multi-agent orchestration completed successfully.")
    sys.exit(0)


@app.command()
def validate(
    input_file: Path = typer.Option(
        ...,
        "--input-file",
        "-i",
        exists=True,
        readable=True,
        help="Path to workflows JSON input file.",
    ),
    config_file: Path = typer.Option(
        None,
        "--config",
        "-c",
        exists=False,
        help="Optional path to configuration file (.env or YAML).",
    ),
):
    """Validate the input JSON against the schema without execution."""
    # Load config for input versions, etc.
    load_dotenv_config(config_file)
    cfg = get_config()

    logger.info(f"Validating input file: {input_file}")
    try:
        _ = parse_and_validate_input(input_file)
    except Exception as exc:
        logger.opt(exception=exc).error("Validation failed.")
        console.print(f"[bold red]Validation failed: {exc}[/bold red]")
        sys.exit(1)
    else:
        console.print(
            f"[bold green]Input file '{input_file.name}' is valid.[/bold green]"
        )
        sys.exit(0)


@app.command()
def show_schema():
    """Show the expected workload JSON schema."""
    from multiagent_cli.input_parser import WORKLOAD_JSON_SCHEMA
    import json

    print(json.dumps(WORKLOAD_JSON_SCHEMA, indent=2))


if __name__ == "__main__":
    app()
