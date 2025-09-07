#!/usr/bin/env python3
"""CLI Tool"""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional

app = typer.Typer()
console = Console()

@app.command()
def hello(name: str = "World"):
    """Say hello"""
    console.print(f"Hello, {name}!", style="bold green")

@app.command()
def list_items(limit: int = 10):
    """List items in a table"""
    table = Table(title="Items")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="green")
    
    for i in range(limit):
        table.add_row(str(i), f"Item {i}", "Active")
    
    console.print(table)

@app.command()
def process(
    input_file: str = typer.Argument(..., help="Input file path"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Process a file"""
    if verbose:
        console.print(f"Processing {input_file}...", style="yellow")
    
    # Process logic here
    
    if output:
        console.print(f"Results saved to {output}", style="green")
    else:
        console.print("Processing complete!", style="bold green")

if __name__ == "__main__":
    app()
