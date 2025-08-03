"""OPSVI Project Intelligence CLI."""

import click
from opsvi_core import get_logger, setup_logging
from rich.console import Console
from rich.table import Table

console = Console()
logger = get_logger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--log-level", default="INFO", help="Logging level")
def main(debug: bool, log_level: str) -> None:
    """OPSVI Project Intelligence CLI."""
    setup_logging(level=log_level)
    if debug:
        logger.info("Debug mode enabled")


@main.command()
@click.argument("project_path", type=click.Path(exists=True))
def analyze(project_path: str) -> None:
    """Analyze a project for intelligence gathering."""
    console.print(f"[bold blue]Analyzing project: {project_path}[/bold blue]")

    # TODO: Implement project analysis
    table = Table(title="Project Analysis Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Files", "0")
    table.add_row("Lines of Code", "0")
    table.add_row("Dependencies", "0")

    console.print(table)
    logger.info("Project analysis completed", project_path=project_path)


@main.command()
@click.option("--collection", default="global__demo", help="Qdrant collection name")
def init_rag(collection: str) -> None:
    """Initialize RAG system with demo collection."""
    console.print(
        f"[bold green]Initializing RAG system with collection: {collection}[/bold green]"
    )

    try:
        from opsvi_rag import QdrantClient

        client = QdrantClient()
        client.create_collection(collection)

        console.print(
            f"[green]✓ Collection '{collection}' created successfully[/green]"
        )
        logger.info("RAG system initialized", collection=collection)

    except Exception as e:
        console.print(f"[red]✗ Failed to initialize RAG system: {e}[/red]")
        logger.error("Failed to initialize RAG system", error=str(e))
        raise click.Abort() from e


if __name__ == "__main__":
    main()
