"""
Tetra CLI with proper async handling and STRICT model compliance.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from .ai.hybrid_controller import HybridController
from .ai.model_config import ModelConfig
from .ai.openai_adapter import OpenAIAdapter
from .core.config import TetraConfig, get_config
from .core.orchestrator import Orchestrator
from .utils.secure_init import (
    create_secure_orchestrator,
    get_token_pool_status,
    inject_tokens_from_environment,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), help="Config file path")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, config, debug):
    """Tetra - Hybrid Multi-Agent Orchestrator with STRICT 2025 compliance."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    if config:
        ctx.obj = TetraConfig.from_yaml(Path(config))
    else:
        ctx.obj = get_config()

    logger.info("Tetra CLI initialized with STRICT model compliance")


@cli.command()
@click.pass_obj
def validate(config: TetraConfig):
    """Validate configuration and models against STRICT 2025 standards."""
    click.echo("🔍 Validating Tetra configuration...")

    try:
        # Validate model configuration
        model_config = ModelConfig()
        click.echo("✅ Model configuration is COMPLIANT with 2025 standards")

        # Show approved models
        approved = model_config.get_all_approved_models()
        click.echo("\n📋 Approved Models:")
        for task_type, models in approved.items():
            click.echo(f"  {task_type}: {', '.join(models)}")

        # Validate hybrid controller
        controller = HybridController(config)
        validation = controller.validate_models()

        if validation["config_valid"]:
            click.echo("\n✅ Hybrid controller configuration VALID")
        else:
            click.echo("\n❌ Hybrid controller configuration INVALID")
            for error in validation["errors"]:
                click.echo(f"  - {error}")

        # Check token pool
        orchestrator = create_secure_orchestrator(config.to_dict())
        token_count = inject_tokens_from_environment(orchestrator.token_pool)
        status = get_token_pool_status(orchestrator.token_pool)

        click.echo(f"\n🔑 Token Pool Status:")
        click.echo(f"  Total tokens: {status['total_tokens']}")
        click.echo(f"  Pool size: {status['pool_size']}")

    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("task")
@click.option("--context", "-x", help="JSON context for the task")
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.pass_obj
def execute(config: TetraConfig, task: str, context: Optional[str], output: Optional[str]):
    """Execute a task using hybrid AI with STRICT compliance."""
    click.echo(f"🚀 Executing task with STRICT model compliance...")

    try:
        # Parse context if provided
        task_context = json.loads(context) if context else None

        # Create controller
        controller = HybridController(config)

        # Execute task with proper async handling
        async def run_task():
            return await controller.route_task(task, task_context)

        result = asyncio.run(run_task())

        # Display result
        if result["success"]:
            click.echo(f"✅ Task completed successfully")
            click.echo(f"Provider: {result['provider']}")
            click.echo(f"Model: {result['model']}")
            click.echo(f"\nResult:\n{result['result']}")

            # Save to file if requested
            if output:
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
                click.echo(f"\n💾 Result saved to {output}")
        else:
            click.echo(f"❌ Task failed: {result.get('error', 'Unknown error')}", err=True)

    except Exception as e:
        click.echo(f"❌ Execution failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("prompt")
@click.option("--model", "-m", help="Specific model to use (must be approved)")
@click.pass_obj
def analyze(config: TetraConfig, prompt: str, model: Optional[str]):
    """Analyze a prompt to determine task type and requirements."""
    click.echo("🔍 Analyzing prompt with STRICT compliance...")

    try:
        # Create adapter with STRICT validation
        adapter = OpenAIAdapter()

        # Use specific model if provided (with validation)
        if model:
            model_config = ModelConfig()
            if not model_config.is_model_approved(model):
                click.echo(f"❌ Model {model} is NOT approved by 2025 standards", err=True)
                sys.exit(1)

        # Run analysis with proper async handling
        async def run_analysis():
            return await adapter.analyze_task(prompt)

        analysis = asyncio.run(run_analysis())

        # Display analysis
        click.echo("\n📊 Task Analysis:")
        click.echo(f"  Type: {analysis.get('task_type', 'unknown')}")
        click.echo(f"  Complexity: {analysis.get('complexity', 'unknown')}")
        click.echo(f"  Requirements: {', '.join(analysis.get('requirements', []))}")
        click.echo(f"  Approach: {analysis.get('suggested_approach', 'No suggestion')}")

    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("tasks", nargs=-1, required=True)
@click.option("--parallel", "-p", default=3, help="Number of parallel tasks")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.pass_obj
def batch(config: TetraConfig, tasks, parallel: int, output: Optional[str]):
    """Execute multiple tasks in batch with STRICT compliance."""
    click.echo(f"🚀 Executing {len(tasks)} tasks (parallel: {parallel})...")

    try:
        # Update parallelism setting
        config.parallelism = parallel

        # Create controller
        controller = HybridController(config)

        # Execute batch with proper async handling
        async def run_batch():
            return await controller.batch_process(list(tasks))

        results = asyncio.run(run_batch())

        # Display results
        success_count = sum(1 for r in results if r.get("success"))
        click.echo(f"\n📊 Batch Results: {success_count}/{len(tasks)} successful")

        for i, result in enumerate(results):
            status = "✅" if result.get("success") else "❌"
            click.echo(f"\n{status} Task {i+1}: {result.get('task', 'Unknown')[:50]}...")
            if result.get("success"):
                click.echo(f"  Provider: {result.get('provider')}")
                click.echo(f"  Model: {result.get('model')}")
            else:
                click.echo(f"  Error: {result.get('error', 'Unknown error')}")

        # Save results if requested
        if output:
            with open(output, "w") as f:
                json.dump(results, f, indent=2)
            click.echo(f"\n💾 Results saved to {output}")

    except Exception as e:
        click.echo(f"❌ Batch execution failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_obj
def models(config: TetraConfig):
    """List all approved models for 2025 compliance."""
    click.echo("📋 2025 Approved Models (STRICT Compliance):")
    click.echo("=" * 50)

    model_config = ModelConfig()
    approved = model_config.get_all_approved_models()

    click.echo("\n✅ APPROVED MODELS:")
    for task_type, model_list in approved.items():
        click.echo(f"\n{task_type.upper()}:")
        for model in model_list:
            click.echo(f"  • {model}")

    click.echo("\n❌ FORBIDDEN PATTERNS:")
    for pattern in ModelConfig.FORBIDDEN_PATTERNS:
        click.echo(f"  • {pattern}*")

    click.echo("\n⚠️  NO EXCEPTIONS. NO FALLBACKS. NO WORKAROUNDS.")
    click.echo("Only use approved models from the list above.")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
