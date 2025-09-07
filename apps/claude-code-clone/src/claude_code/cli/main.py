"""Main CLI application for Claude Code Clone."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..config import ClaudeCodeConfig
from ..core.executor import ClaudeCodeExecutor
from ..core.analyzer import CodeAnalyzer
from ..core.streaming import StreamingHandler

app = typer.Typer(
    name="claude-code",
    help="Claude Code Clone - Multi-Provider AI Coding Assistant",
    add_completion=False,
)
console = Console()


@app.command()
def analyze(
    file_path: str = typer.Argument(..., help="File to analyze"),
    analysis_type: str = typer.Option(
        "general", help="Type of analysis (general, security, performance, style, bugs)"
    ),
    context: Optional[str] = typer.Option(None, help="Additional context for analysis"),
    provider: str = typer.Option(
        "openai", help="LLM provider (openai, anthropic, perplexity)"
    ),
    model: str = typer.Option("gpt-5-mini", help="Model to use"),
    api_key: Optional[str] = typer.Option(None, help="API key for the provider"),
    working_directory: str = typer.Option(".", help="Working directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Analyze a file using AI."""
    asyncio.run(
        _analyze_file(
            file_path,
            analysis_type,
            context,
            provider,
            model,
            api_key,
            working_directory,
            verbose,
        )
    )


@app.command()
def generate(
    file_path: str = typer.Argument(..., help="File to generate"),
    prompt: str = typer.Argument(..., help="Prompt for code generation"),
    language: Optional[str] = typer.Option(None, help="Programming language"),
    context: Optional[str] = typer.Option(None, help="Additional context"),
    provider: str = typer.Option(
        "openai", help="LLM provider (openai, anthropic, perplexity)"
    ),
    model: str = typer.Option("gpt-5-mini", help="Model to use"),
    api_key: Optional[str] = typer.Option(None, help="API key for the provider"),
    working_directory: str = typer.Option(".", help="Working directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Generate code using AI."""
    asyncio.run(
        _generate_file(
            file_path,
            prompt,
            language,
            context,
            provider,
            model,
            api_key,
            working_directory,
            verbose,
        )
    )


@app.command()
def refactor(
    file_path: str = typer.Argument(..., help="File to refactor"),
    refactor_type: str = typer.Option(
        "improve", help="Type of refactoring (improve, optimize, modernize, simplify)"
    ),
    context: Optional[str] = typer.Option(None, help="Additional context"),
    provider: str = typer.Option(
        "openai", help="LLM provider (openai, anthropic, perplexity)"
    ),
    model: str = typer.Option("gpt-5-mini", help="Model to use"),
    api_key: Optional[str] = typer.Option(None, help="API key for the provider"),
    working_directory: str = typer.Option(".", help="Working directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Refactor code using AI."""
    asyncio.run(
        _refactor_file(
            file_path,
            refactor_type,
            context,
            provider,
            model,
            api_key,
            working_directory,
            verbose,
        )
    )


@app.command()
def project(
    project_path: str = typer.Argument(..., help="Project directory to analyze"),
    analysis_types: Optional[List[str]] = typer.Option(
        None, help="Types of analysis to run"
    ),
    provider: str = typer.Option(
        "openai", help="LLM provider (openai, anthropic, perplexity)"
    ),
    model: str = typer.Option("gpt-5-mini", help="Model to use"),
    api_key: Optional[str] = typer.Option(None, help="API key for the provider"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Analyze an entire project."""
    asyncio.run(
        _analyze_project(
            project_path, analysis_types, provider, model, api_key, verbose
        )
    )


@app.command()
def interactive(
    provider: str = typer.Option(
        "openai", help="LLM provider (openai, anthropic, perplexity)"
    ),
    model: str = typer.Option("gpt-5-mini", help="Model to use"),
    api_key: Optional[str] = typer.Option(None, help="API key for the provider"),
    working_directory: str = typer.Option(".", help="Working directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Start interactive mode."""
    asyncio.run(_interactive_mode(provider, model, api_key, working_directory, verbose))


async def _analyze_file(
    file_path: str,
    analysis_type: str,
    context: Optional[str],
    provider: str,
    model: str,
    api_key: Optional[str],
    working_directory: str,
    verbose: bool,
):
    """Analyze a file."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    config = ClaudeCodeConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        working_directory=working_directory,
    )

    executor = ClaudeCodeExecutor(config)

    try:
        console.print(f"[bold blue]Analyzing {file_path}...[/bold blue]")

        result = await executor.analyze_file(file_path, analysis_type, context)

        console.print(
            Panel(result, title=f"Analysis Results - {file_path}", border_style="green")
        )

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    finally:
        await executor.close()


async def _generate_file(
    file_path: str,
    prompt: str,
    language: Optional[str],
    context: Optional[str],
    provider: str,
    model: str,
    api_key: Optional[str],
    working_directory: str,
    verbose: bool,
):
    """Generate a file."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    config = ClaudeCodeConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        working_directory=working_directory,
    )

    executor = ClaudeCodeExecutor(config)

    try:
        console.print(f"[bold blue]Generating {file_path}...[/bold blue]")

        result = await executor.generate_file(file_path, prompt, language, context)

        console.print(
            Panel(result, title=f"Generated Code - {file_path}", border_style="green")
        )

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    finally:
        await executor.close()


async def _refactor_file(
    file_path: str,
    refactor_type: str,
    context: Optional[str],
    provider: str,
    model: str,
    api_key: Optional[str],
    working_directory: str,
    verbose: bool,
):
    """Refactor a file."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    config = ClaudeCodeConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        working_directory=working_directory,
    )

    executor = ClaudeCodeExecutor(config)

    try:
        console.print(f"[bold blue]Refactoring {file_path}...[/bold blue]")

        result = await executor.refactor_file(file_path, refactor_type, context)

        console.print(
            Panel(result, title=f"Refactored Code - {file_path}", border_style="green")
        )

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    finally:
        await executor.close()


async def _analyze_project(
    project_path: str,
    analysis_types: Optional[List[str]],
    provider: str,
    model: str,
    api_key: Optional[str],
    verbose: bool,
):
    """Analyze a project."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    config = ClaudeCodeConfig(
        provider=provider, model=model, api_key=api_key, working_directory=project_path
    )

    analyzer = CodeAnalyzer(config)

    try:
        console.print(f"[bold blue]Analyzing project: {project_path}[/bold blue]")

        if analysis_types is None:
            analysis_types = ["structure", "complexity", "duplicates", "issues"]

        for analysis_type in analysis_types:
            console.print(f"[yellow]Running {analysis_type} analysis...[/yellow]")

            if analysis_type == "structure":
                result = analyzer.analyze_project_structure()
                console.print(
                    Panel(
                        f"Total files: {result['total_files']}\n"
                        f"File types: {result['file_types']}\n"
                        f"Total functions: {result['complexity_summary']['total_functions']}\n"
                        f"Total classes: {result['complexity_summary']['total_classes']}\n"
                        f"Total complexity: {result['complexity_summary']['total_complexity']}",
                        title="Project Structure Analysis",
                        border_style="green",
                    )
                )

            elif analysis_type == "duplicates":
                result = analyzer.find_duplicate_code(["*.py", "*.js", "*.ts"])
                if result:
                    console.print(
                        Panel(
                            f"Found {len(result)} potential duplicate code blocks",
                            title="Duplicate Code Analysis",
                            border_style="yellow",
                        )
                    )
                else:
                    console.print("[green]No duplicate code found[/green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")


async def _interactive_mode(
    provider: str,
    model: str,
    api_key: Optional[str],
    working_directory: str,
    verbose: bool,
):
    """Start interactive mode."""
    if verbose:
        logging.basicConfig(level=logging.INFO)

    config = ClaudeCodeConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        working_directory=working_directory,
    )

    executor = ClaudeCodeExecutor(config)

    try:
        console.print(
            Panel(
                "Welcome to Claude Code Clone Interactive Mode!\n"
                "Type your prompts and I'll help you with coding tasks.\n"
                "Type 'exit' to quit.",
                title="Claude Code Clone",
                border_style="blue",
            )
        )

        while True:
            try:
                prompt = typer.prompt("\n[bold blue]claude-code[/bold blue]")

                if prompt.lower() in ["exit", "quit", "q"]:
                    break

                console.print("[yellow]Processing...[/yellow]")

                result = await executor.execute_prompt(prompt)

                console.print(Panel(result, title="Response", border_style="green"))

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[bold red]Error: {e}[/bold red]")

    finally:
        await executor.close()
        console.print("[bold blue]Goodbye![/bold blue]")


if __name__ == "__main__":
    app()
