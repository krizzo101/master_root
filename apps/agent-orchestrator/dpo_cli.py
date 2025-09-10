#!/usr/bin/env python3
"""
DPO Command-Line Interface

Provides a comprehensive CLI for the Development Process Orchestrator system.

Commands:
    dpo build       - Process a development request
    dpo status      - Check workflow status
    dpo results     - Get workflow results
    dpo list        - List all workflows
    dpo cancel      - Cancel a running workflow
    dpo configure   - Manage DPO configuration
    dpo templates   - Manage workflow templates
    dpo metrics     - View system metrics
    dpo server      - Start the DPO API server

Author: Agent Orchestrator Team
Date: September 2025
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from src.dpo_main_controller import (
    DevelopmentProcessOrchestrator,
    DPOConfiguration,
    RequestType,
)

# Initialize Rich console
console = Console()


class DPOCommandLine:
    """Command-line interface for DPO system"""

    def __init__(self):
        """Initialize CLI"""
        self.config_path = Path.home() / ".dpo" / "config.json"
        self.config = self._load_config()
        self.dpo = None

    def _load_config(self) -> DPOConfiguration:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            return DPOConfiguration.from_file(str(self.config_path))
        else:
            # Create default config
            config = DPOConfiguration()
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config.save(str(self.config_path))
            return config

    async def build(self, args):
        """Process a development request"""
        console.print(
            "[bold cyan]Development Process Orchestrator - Build Mode[/bold cyan]\n"
        )

        # Get request from args or prompt
        if args.request:
            request = args.request
        else:
            request = console.input("[bold]Enter your development request:[/bold] ")

        # Parse additional parameters
        project_type = args.type
        complexity = args.complexity

        # Load context from file if provided
        context = {}
        if args.context_file:
            context_path = Path(args.context_file)
            if context_path.exists():
                with open(context_path, "r") as f:
                    if context_path.suffix == ".json":
                        context = json.load(f)
                    elif context_path.suffix in [".yml", ".yaml"]:
                        context = yaml.safe_load(f)

        # Add inline context
        if args.framework:
            context["framework"] = args.framework
        if args.database:
            context["database"] = args.database
        if args.features:
            context["features"] = args.features.split(",")

        # Enhancement preferences
        enhancement_prefs = {}
        if args.prioritize_quality:
            enhancement_prefs["prioritize_quality"] = True
        if args.prioritize_innovation:
            enhancement_prefs["prioritize_innovation"] = True
        if args.prioritize_performance:
            enhancement_prefs["prioritize_performance"] = True

        # Initialize DPO
        self.dpo = DevelopmentProcessOrchestrator(self.config)

        # Process request with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing development request...", total=None)

            result = await self.dpo.process_development_request(
                request=request,
                project_type=project_type,
                complexity=complexity,
                context=context,
                enhancement_prefs=enhancement_prefs,
            )

            progress.update(task, completed=True)

        # Display results
        if result["success"]:
            console.print(
                "\n[bold green]✓ Development workflow initiated successfully![/bold green]"
            )

            # Create result panel
            result_text = f"""
[bold]Workflow ID:[/bold] {result['workflow_id']}
[bold]Project Type:[/bold] {result['analysis']['project_type']}
[bold]Complexity:[/bold] {result['analysis']['complexity']}
[bold]Estimated Effort:[/bold] {result['analysis']['estimated_effort']}
[bold]Enhancements Applied:[/bold] {result['enhancements_count']}
[bold]Workflow Phases:[/bold] {result['phases_count']}
[bold]Processing Time:[/bold] {result['processing_time']:.2f}s
            """

            panel = Panel(
                result_text.strip(), title="Workflow Details", border_style="green"
            )
            console.print(panel)

            # Show key requirements
            if result["analysis"]["key_requirements"]:
                console.print("\n[bold]Key Requirements Identified:[/bold]")
                for req in result["analysis"]["key_requirements"][:5]:
                    console.print(f"  • {req}")

            # Show suggested technologies
            if result["analysis"]["suggested_technologies"]:
                console.print("\n[bold]Suggested Technologies:[/bold]")
                console.print(
                    "  " + ", ".join(result["analysis"]["suggested_technologies"])
                )

            # Show risk factors
            if result["analysis"]["risk_factors"]:
                console.print("\n[bold]Risk Factors:[/bold]")
                for risk in result["analysis"]["risk_factors"]:
                    console.print(f"  ⚠ {risk}")

            # Monitoring instructions
            console.print(
                f"\n[dim]Monitor progress with: dpo status {result['workflow_id']}[/dim]"
            )
            console.print(
                f"[dim]Get results with: dpo results {result['workflow_id']}[/dim]"
            )

            # Save workflow ID for convenience
            last_workflow_file = Path.home() / ".dpo" / "last_workflow"
            last_workflow_file.parent.mkdir(parents=True, exist_ok=True)
            last_workflow_file.write_text(result["workflow_id"])

        else:
            console.print(f"\n[bold red]✗ Failed to process request[/bold red]")
            console.print(f"Error: {result.get('error')}")
            if args.verbose:
                console.print(f"Traceback:\n{result.get('traceback')}")

        # Cleanup
        if self.dpo:
            await self.dpo.shutdown()

    async def status(self, args):
        """Check workflow status"""
        # Get workflow ID
        workflow_id = args.workflow_id
        if not workflow_id:
            # Try to get last workflow
            last_workflow_file = Path.home() / ".dpo" / "last_workflow"
            if last_workflow_file.exists():
                workflow_id = last_workflow_file.read_text().strip()
            else:
                console.print(
                    "[red]No workflow ID provided and no recent workflow found[/red]"
                )
                return

        # Initialize DPO
        self.dpo = DevelopmentProcessOrchestrator(self.config)

        # Get status
        status = await self.dpo.get_workflow_status(workflow_id)

        # Display status
        if status.get("status") == "not_found":
            console.print(f"[red]Workflow {workflow_id} not found[/red]")
        else:
            # Create status panel
            status_color = {
                "pending": "yellow",
                "initializing": "yellow",
                "running": "cyan",
                "completed": "green",
                "failed": "red",
                "cancelled": "orange",
            }.get(status["status"], "white")

            panel_content = f"""
[bold]Workflow ID:[/bold] {workflow_id}
[bold]Status:[/bold] [{status_color}]{status['status'].upper()}[/{status_color}]
            """

            # Add progress if available
            if status.get("progress"):
                progress = status["progress"]
                progress_pct = progress.get("progress_percentage", 0)
                completed = progress.get("completed_tasks", 0)
                total = progress.get("total_tasks", 0)

                panel_content += f"""
[bold]Progress:[/bold] {completed}/{total} tasks ({progress_pct:.1f}%)
[bold]Running Tasks:[/bold] {len(progress.get('running_tasks', []))}
[bold]Failed Tasks:[/bold] {progress.get('failed_tasks', 0)}
                """

                if progress.get("current_phase"):
                    panel_content += (
                        f"\n[bold]Current Phase:[/bold] {progress['current_phase']}"
                    )

                if progress.get("estimated_completion"):
                    panel_content += (
                        f"\n[bold]ETA:[/bold] {progress['estimated_completion']}"
                    )

            # Add metadata if available
            if status.get("metadata"):
                meta = status["metadata"]
                if meta.get("estimated_duration"):
                    panel_content += f"\n[bold]Estimated Duration:[/bold] {meta['estimated_duration']}"

            panel = Panel(
                panel_content.strip(),
                title=f"Workflow Status",
                border_style=status_color,
            )
            console.print(panel)

            # Show running tasks if verbose
            if args.verbose and status.get("progress", {}).get("running_tasks"):
                console.print("\n[bold]Currently Running Tasks:[/bold]")
                for task_id in status["progress"]["running_tasks"]:
                    console.print(f"  • {task_id}")

        # Cleanup
        if self.dpo:
            await self.dpo.shutdown()

    async def results(self, args):
        """Get workflow results"""
        # Get workflow ID
        workflow_id = args.workflow_id
        if not workflow_id:
            last_workflow_file = Path.home() / ".dpo" / "last_workflow"
            if last_workflow_file.exists():
                workflow_id = last_workflow_file.read_text().strip()
            else:
                console.print(
                    "[red]No workflow ID provided and no recent workflow found[/red]"
                )
                return

        # Initialize DPO
        self.dpo = DevelopmentProcessOrchestrator(self.config)

        # Get results
        results = await self.dpo.get_workflow_results(workflow_id)

        if "error" in results:
            console.print(f"[red]{results['error']}[/red]")
        else:
            # Display results summary
            console.print(
                f"\n[bold green]Workflow {workflow_id} Results[/bold green]\n"
            )

            # Metrics panel
            metrics = results.get("metrics", {})
            metrics_text = f"""
[bold]Status:[/bold] {results['status']}
[bold]Duration:[/bold] {results.get('duration_seconds', 0):.2f} seconds
[bold]Total Tasks:[/bold] {metrics.get('total_tasks', 0)}
[bold]Completed:[/bold] {metrics.get('completed_tasks', 0)}
[bold]Failed:[/bold] {metrics.get('failed_tasks', 0)}
[bold]Success Rate:[/bold] {metrics.get('success_rate', 0):.1%}
[bold]Deliverables:[/bold] {metrics.get('deliverables_count', 0)} files
[bold]Knowledge Extracted:[/bold] {metrics.get('knowledge_extracted', 0)} items
            """

            panel = Panel(
                metrics_text.strip(), title="Execution Metrics", border_style="green"
            )
            console.print(panel)

            # Show deliverables
            if results.get("deliverables") and args.show_deliverables:
                console.print("\n[bold]Deliverables:[/bold]")
                for deliverable in results["deliverables"][:10]:
                    console.print(f"  📄 {deliverable}")
                if len(results["deliverables"]) > 10:
                    console.print(f"  ... and {len(results['deliverables']) - 10} more")

            # Show errors if any
            if results.get("errors"):
                console.print("\n[bold red]Errors:[/bold red]")
                for error in results["errors"][:5]:
                    console.print(f"  ✗ {error}")

            # Export option
            if args.export:
                export_path = Path(args.export)
                export_path.parent.mkdir(parents=True, exist_ok=True)
                with open(export_path, "w") as f:
                    json.dump(results, f, indent=2)
                console.print(f"\n[dim]Results exported to {export_path}[/dim]")

        # Cleanup
        if self.dpo:
            await self.dpo.shutdown()

    async def list_workflows(self, args):
        """List all workflows"""
        # Initialize DPO
        self.dpo = DevelopmentProcessOrchestrator(self.config)

        # Get workflows
        workflows = await self.dpo.list_workflows(status_filter=args.status)

        if not workflows:
            console.print("[dim]No workflows found[/dim]")
        else:
            # Create table
            table = Table(title=f"Workflows ({len(workflows)} total)")
            table.add_column("Workflow ID", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Project Type")
            table.add_column("Request", max_width=40)
            table.add_column("Started")

            for wf in workflows:
                status_color = {
                    "running": "cyan",
                    "completed": "green",
                    "failed": "red",
                    "cancelled": "yellow",
                }.get(wf["status"], "white")

                table.add_row(
                    wf["workflow_id"][:8] + "...",
                    f"[{status_color}]{wf['status']}[/{status_color}]",
                    wf["project_type"],
                    wf["request"],
                    wf["start_time"][:19] if wf.get("start_time") else "N/A",
                )

            console.print(table)

        # Cleanup
        if self.dpo:
            await self.dpo.shutdown()

    async def cancel(self, args):
        """Cancel a workflow"""
        workflow_id = args.workflow_id

        # Confirm cancellation
        if not args.force:
            confirm = console.input(
                f"[yellow]Cancel workflow {workflow_id}? (y/N):[/yellow] "
            )
            if confirm.lower() != "y":
                console.print("[dim]Cancelled[/dim]")
                return

        # Initialize DPO
        self.dpo = DevelopmentProcessOrchestrator(self.config)

        # Cancel workflow
        result = await self.dpo.cancel_workflow(workflow_id)

        if result["success"]:
            console.print(f"[green]✓ {result['message']}[/green]")
        else:
            console.print(f"[red]✗ {result['message']}[/red]")

        # Cleanup
        if self.dpo:
            await self.dpo.shutdown()

    async def configure(self, args):
        """Manage configuration"""
        if args.show:
            # Show current configuration
            config_dict = self.config.__dict__
            console.print("[bold]Current DPO Configuration:[/bold]\n")

            for key, value in config_dict.items():
                console.print(f"  [cyan]{key}:[/cyan] {value}")

        elif args.set:
            # Set configuration value
            key, value = args.set.split("=", 1)

            # Convert value to appropriate type
            if value.lower() in ["true", "false"]:
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)

            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.config.save(str(self.config_path))
                console.print(f"[green]✓ Set {key} = {value}[/green]")
            else:
                console.print(f"[red]Unknown configuration key: {key}[/red]")

        elif args.reset:
            # Reset to defaults
            self.config = DPOConfiguration()
            self.config.save(str(self.config_path))
            console.print("[green]✓ Configuration reset to defaults[/green]")

    async def templates(self, args):
        """Manage workflow templates"""
        console.print("[bold]Workflow Templates[/bold]\n")

        # List available templates
        templates = [
            ("web_app", "Full-stack web application"),
            ("api", "REST/GraphQL API service"),
            ("cli", "Command-line interface tool"),
            ("library", "Reusable library/package"),
            ("integration", "System integration"),
            ("mobile", "Mobile application"),
            ("desktop", "Desktop application"),
            ("data", "Data processing pipeline"),
        ]

        table = Table(title="Available Templates")
        table.add_column("Template", style="cyan")
        table.add_column("Description")
        table.add_column("Phases")

        for template_id, description in templates:
            # Estimate phases based on template
            phases = {
                "web_app": 8,
                "api": 7,
                "cli": 5,
                "library": 6,
                "integration": 6,
                "mobile": 9,
                "desktop": 8,
                "data": 7,
            }.get(template_id, 6)

            table.add_row(template_id, description, str(phases))

        console.print(table)

        if args.show and args.show in [t[0] for t in templates]:
            # Show template details
            console.print(f"\n[bold]Template: {args.show}[/bold]")
            console.print(
                "[dim]Detailed template information would be shown here[/dim]"
            )

    async def metrics(self, args):
        """View system metrics"""
        # Initialize DPO
        self.dpo = DevelopmentProcessOrchestrator(self.config)

        # Get metrics
        metrics = self.dpo.get_metrics()

        # Display metrics
        console.print("[bold]DPO System Metrics[/bold]\n")

        # Create metrics panel
        metrics_text = f"""
[bold]Total Requests:[/bold] {metrics['total_requests']}
[bold]Successful Workflows:[/bold] {metrics['successful_workflows']}
[bold]Failed Workflows:[/bold] {metrics['failed_workflows']}
[bold]Average Duration:[/bold] {metrics['average_duration']:.2f} seconds
[bold]Total Agents Used:[/bold] {metrics['total_agents_used']}
[bold]Enhancements Applied:[/bold] {metrics['enhancements_applied']}
[bold]Context Injections:[/bold] {metrics['context_injections']}
[bold]Errors Recovered:[/bold] {metrics['errors_recovered']}
[bold]Knowledge Extracted:[/bold] {metrics['knowledge_extracted']}
        """

        success_rate = 0
        if metrics["total_requests"] > 0:
            success_rate = metrics["successful_workflows"] / metrics["total_requests"]

        panel = Panel(
            metrics_text.strip(),
            title=f"System Performance (Success Rate: {success_rate:.1%})",
            border_style="cyan",
        )
        console.print(panel)

        # Export option
        if args.export:
            export_path = Path(args.export)
            with open(export_path, "w") as f:
                json.dump(metrics, f, indent=2)
            console.print(f"\n[dim]Metrics exported to {export_path}[/dim]")

        # Cleanup
        if self.dpo:
            await self.dpo.shutdown()

    async def server(self, args):
        """Start the DPO API server"""
        console.print("[bold cyan]Starting DPO API Server[/bold cyan]\n")

        try:
            # Import FastAPI app
            from src.dpo_orchestrator_integration import api

            if api:
                import uvicorn

                console.print(
                    f"[green]✓ Server starting on http://{args.host}:{args.port}[/green]"
                )
                console.print("[dim]Press Ctrl+C to stop[/dim]\n")

                # Run server
                uvicorn.run(
                    api,
                    host=args.host,
                    port=args.port,
                    log_level="info" if not args.verbose else "debug",
                )
            else:
                console.print(
                    "[red]FastAPI not available - install with: pip install fastapi uvicorn[/red]"
                )
        except ImportError as e:
            console.print(f"[red]Failed to start server: {e}[/red]")
            console.print(
                "[dim]Install required packages: pip install fastapi uvicorn[/dim]"
            )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Development Process Orchestrator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Build command
    build_parser = subparsers.add_parser("build", help="Process a development request")
    build_parser.add_argument("request", nargs="?", help="Development request text")
    build_parser.add_argument(
        "-t", "--type", help="Project type (web_app, api, cli, etc.)"
    )
    build_parser.add_argument(
        "-c",
        "--complexity",
        choices=["simple", "moderate", "complex"],
        help="Complexity level",
    )
    build_parser.add_argument(
        "--context-file", help="JSON/YAML file with project context"
    )
    build_parser.add_argument("--framework", help="Framework to use")
    build_parser.add_argument("--database", help="Database to use")
    build_parser.add_argument("--features", help="Comma-separated list of features")
    build_parser.add_argument(
        "--prioritize-quality", action="store_true", help="Prioritize code quality"
    )
    build_parser.add_argument(
        "--prioritize-innovation",
        action="store_true",
        help="Prioritize innovative features",
    )
    build_parser.add_argument(
        "--prioritize-performance", action="store_true", help="Prioritize performance"
    )
    build_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Check workflow status")
    status_parser.add_argument("workflow_id", nargs="?", help="Workflow ID")
    status_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed status"
    )

    # Results command
    results_parser = subparsers.add_parser("results", help="Get workflow results")
    results_parser.add_argument("workflow_id", nargs="?", help="Workflow ID")
    results_parser.add_argument(
        "--show-deliverables", action="store_true", help="Show list of deliverables"
    )
    results_parser.add_argument("--export", help="Export results to file")

    # List command
    list_parser = subparsers.add_parser("list", help="List workflows")
    list_parser.add_argument("--status", help="Filter by status")

    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a workflow")
    cancel_parser.add_argument("workflow_id", help="Workflow ID to cancel")
    cancel_parser.add_argument(
        "-f", "--force", action="store_true", help="Skip confirmation"
    )

    # Configure command
    config_parser = subparsers.add_parser("configure", help="Manage configuration")
    config_parser.add_argument(
        "--show", action="store_true", help="Show current configuration"
    )
    config_parser.add_argument("--set", help="Set configuration value (key=value)")
    config_parser.add_argument("--reset", action="store_true", help="Reset to defaults")

    # Templates command
    templates_parser = subparsers.add_parser(
        "templates", help="Manage workflow templates"
    )
    templates_parser.add_argument("--show", help="Show template details")

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="View system metrics")
    metrics_parser.add_argument("--export", help="Export metrics to file")

    # Server command
    server_parser = subparsers.add_parser("server", help="Start API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=8000, help="Server port")
    server_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging"
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create CLI instance
    cli = DPOCommandLine()

    # Execute command
    try:
        if args.command == "build":
            asyncio.run(cli.build(args))
        elif args.command == "status":
            asyncio.run(cli.status(args))
        elif args.command == "results":
            asyncio.run(cli.results(args))
        elif args.command == "list":
            asyncio.run(cli.list_workflows(args))
        elif args.command == "cancel":
            asyncio.run(cli.cancel(args))
        elif args.command == "configure":
            asyncio.run(cli.configure(args))
        elif args.command == "templates":
            asyncio.run(cli.templates(args))
        elif args.command == "metrics":
            asyncio.run(cli.metrics(args))
        elif args.command == "server":
            asyncio.run(cli.server(args))
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            import traceback

            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
