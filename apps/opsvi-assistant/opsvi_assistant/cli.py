"""CLI interface for OPSVI Assistant."""

import sys
import asyncio
from pathlib import Path
from typing import Optional

import click

# Import from opsvi libraries
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "libs"))

from opsvi_interfaces.cli import BaseCLI
from opsvi_llm.providers import AnthropicProvider, AnthropicConfig

from .core import Assistant
from .commands import ask, code, analyze, chat


def create_cli() -> BaseCLI:
    """Create the CLI application."""
    cli = BaseCLI(
        name="opsvi-assistant",
        version="1.0.0",
        help="AI-powered assistant using OPSVI libraries"
    )
    
    # Initialize assistant
    assistant = Assistant()
    cli.set_context("assistant", assistant)
    
    @cli.command()
    @click.argument("question")
    @click.option("--model", default=None, help="Model to use")
    @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
    def ask(question: str, model: Optional[str], verbose: bool):
        """Ask the AI a question."""
        ctx = click.get_current_context()
        assistant = ctx.obj["assistant"]
        
        if verbose:
            click.echo(f"Using model: {model or assistant.default_model}")
        
        response = assistant.ask(question, model=model)
        click.echo(response)
    
    @cli.command()
    @click.argument("description")
    @click.option("--language", "-l", default="python", help="Programming language")
    @click.option("--save", "-s", help="Save to file")
    def code(description: str, language: str, save: Optional[str]):
        """Generate code from description."""
        ctx = click.get_current_context()
        assistant = ctx.obj["assistant"]
        
        click.echo(f"Generating {language} code...")
        code = assistant.generate_code(description, language)
        
        if save:
            Path(save).write_text(code)
            click.echo(f"Code saved to {save}")
        else:
            click.echo(code)
    
    @cli.command()
    @click.argument("file_path", type=click.Path(exists=True))
    @click.option("--check", is_flag=True, help="Check for issues")
    @click.option("--improve", is_flag=True, help="Suggest improvements")
    def analyze(file_path: str, check: bool, improve: bool):
        """Analyze code file."""
        ctx = click.get_current_context()
        assistant = ctx.obj["assistant"]
        
        code = Path(file_path).read_text()
        
        if check:
            issues = assistant.check_code(code, file_path)
            if issues:
                click.echo("Issues found:")
                for issue in issues:
                    click.echo(f"  - {issue}")
            else:
                click.echo("No issues found!")
        
        if improve:
            suggestions = assistant.improve_code(code, file_path)
            click.echo("Suggestions:")
            click.echo(suggestions)
    
    @cli.command()
    @click.option("--multiline", "-m", is_flag=True, help="Multiline mode")
    def chat(multiline: bool):
        """Start interactive chat session."""
        ctx = click.get_current_context()
        assistant = ctx.obj["assistant"]
        
        click.echo("Starting chat session. Type 'exit' to quit.")
        click.echo("=" * 50)
        
        while True:
            try:
                if multiline:
                    click.echo("Enter message (Ctrl+D to send):")
                    lines = []
                    while True:
                        try:
                            line = input()
                            lines.append(line)
                        except EOFError:
                            break
                    message = "\n".join(lines)
                else:
                    message = click.prompt("You", type=str)
                
                if message.lower() in ["exit", "quit", "bye"]:
                    click.echo("Goodbye!")
                    break
                
                response = assistant.chat(message)
                click.echo(f"Assistant: {response}")
                click.echo("-" * 50)
                
            except KeyboardInterrupt:
                click.echo("\nGoodbye!")
                break
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
    
    @cli.command()
    def status():
        """Show assistant status."""
        ctx = click.get_current_context()
        assistant = ctx.obj["assistant"]
        
        status = assistant.get_status()
        click.echo("Assistant Status:")
        click.echo(f"  Provider: {status['provider']}")
        click.echo(f"  Model: {status['model']}")
        click.echo(f"  Messages: {status['message_count']}")
        click.echo(f"  Tokens used: {status['total_tokens']}")
    
    @cli.command()
    @click.option("--provider", type=click.Choice(["anthropic", "openai"]))
    @click.option("--model", help="Model name")
    @click.option("--temperature", type=float, help="Temperature (0-1)")
    def config(provider: Optional[str], model: Optional[str], temperature: Optional[float]):
        """Configure assistant settings."""
        ctx = click.get_current_context()
        assistant = ctx.obj["assistant"]
        
        if provider:
            assistant.set_provider(provider)
            click.echo(f"Provider set to: {provider}")
        
        if model:
            assistant.set_model(model)
            click.echo(f"Model set to: {model}")
        
        if temperature is not None:
            assistant.set_temperature(temperature)
            click.echo(f"Temperature set to: {temperature}")
        
        if not any([provider, model, temperature]):
            config = assistant.get_config()
            click.echo("Current configuration:")
            for key, value in config.items():
                click.echo(f"  {key}: {value}")
    
    return cli


def main():
    """Main entry point."""
    cli = create_cli()
    cli.run()


if __name__ == "__main__":
    main()