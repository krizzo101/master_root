#!/usr/bin/env python3
"""
Console Interface - Beautiful User-Friendly Output

Provides clear, formatted console output for users while preserving
detailed debug logging for developers. Focuses on user experience
with pretty-printing, progress tracking, and clear status indicators.
"""

import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree


class ConsoleInterface:
    """
    Beautiful console interface for user-friendly OAMAT-SD output

    Separates user experience from technical logging:
    - Console: Clear, formatted, user-friendly
    - Debug Logs: Technical, detailed, comprehensive
    """

    def __init__(self):
        self.console = Console()
        self.current_step = 0
        self.total_steps = 5
        self.start_time = datetime.now()

    def show_header(self, title: str = "OAMAT Smart Decomposition"):
        """Display beautiful header"""
        self.console.print()
        self.console.print(
            Panel.fit(
                f"[bold blue]{title}[/bold blue]\n"
                f"[dim]🤖 Intelligent Multi-Agent Workflow Orchestration[/dim]",
                border_style="blue",
            )
        )
        self.console.print()

    def show_request_analysis(self, request: str, analysis: dict[str, Any]):
        """Display request analysis in beautiful format"""
        self._show_step("Request Analysis")

        # Show original request
        self.console.print(
            Panel(
                f"[white]{request}[/white]",
                title="📝 Original Request",
                border_style="green",
            )
        )

        # Show analysis results
        table = Table(title="🔍 Analysis Results", show_header=False)
        table.add_column("Aspect", style="cyan", width=20)
        table.add_column("Result", style="white")

        table.add_row("🏷️ Type", analysis.get("request_type", "Unknown"))
        table.add_row("🔧 Complexity", analysis.get("complexity_level", "Unknown"))
        table.add_row("🎯 Technologies", ", ".join(analysis.get("technologies", [])))
        table.add_row("📊 Confidence", f"{analysis.get('confidence', 0):.1f}%")

        self.console.print(table)
        self.console.print()

    def show_workflow_specification(self, workflow_spec: dict[str, Any]):
        """Display workflow specification with pretty formatting"""
        self._show_step("Workflow Generation")

        # Show workflow overview
        agents = workflow_spec.get("agent_specifications", [])
        self.console.print(
            Panel(
                f"[green]✅ Generated workflow with {len(agents)} specialized agents[/green]",
                title="🧠 O3 Reasoning Complete",
            )
        )

        # Show agent specifications
        if agents:
            table = Table(title="🤖 Generated Agent Specifications")
            table.add_column("Agent", style="cyan", width=20)
            table.add_column("Role", style="yellow", width=25)
            table.add_column("Tools", style="green", width=15)
            table.add_column("Deliverables", style="white")

            for agent in agents:
                agent_id = agent.get("agent_id", "Unknown")
                role = agent.get("role", "Unknown")
                tools = len(agent.get("required_tools", []))
                deliverables = len(agent.get("required_deliverables", []))

                table.add_row(agent_id, role, f"{tools} tools", f"{deliverables} files")

            self.console.print(table)

        self.console.print()

    def show_subdivision_detection(self, subdivision_metadata: Any):
        """Display subdivision workflow detection"""
        self.console.print(
            Panel(
                f"[yellow]🔄 SUBDIVISION WORKFLOW DETECTED[/yellow]\n\n"
                f"[white]Reasoning:[/white] {subdivision_metadata.subdivision_reasoning}\n"
                f"[white]Sub-agents:[/white] {subdivision_metadata.estimated_sub_agents}\n"
                f"[white]Complexity:[/white] {subdivision_metadata.complexity_score}/10",
                title="🎯 Advanced Workflow",
                border_style="yellow",
            )
        )
        self.console.print()

    def show_agent_creation(self, agents: dict[str, Any], subdivision: bool = False):
        """Display agent creation results"""
        workflow_type = "Subdivision" if subdivision else "Standard"
        self._show_step(f"{workflow_type} Agent Creation")

        self.console.print(
            Panel(
                f"[green]✅ Created {len(agents)} specialized agents[/green]",
                title=f"🏭 {workflow_type} Agents Ready",
            )
        )

        # Show agent details in a tree structure
        tree = Tree("🤖 Agent Hierarchy")

        for agent_id, agent_data in agents.items():
            role = agent_data.get("role", "Unknown Role")
            agent_node = tree.add(f"[cyan]{agent_id}[/cyan] - [yellow]{role}[/yellow]")

            # Add specialization info
            if "specialization" in agent_data:
                agent_node.add(f"[green]🎯 {agent_data['specialization']}[/green]")

            # Add timestamp
            if "created_timestamp" in agent_data:
                agent_node.add(f"[dim]⏰ {agent_data['created_timestamp']}[/dim]")

        self.console.print(tree)
        self.console.print()

    def show_execution_start(self, agent_count: int):
        """Display execution start with agent count"""
        self._show_step("Parallel Execution")

        self.console.print(
            Panel(
                f"[blue]⚡ Running {agent_count} agents concurrently using LangGraph Send API[/blue]\n"
                f"[dim]🚀 3-5x performance improvement over sequential execution[/dim]",
                title="🔄 Agent Orchestration",
                border_style="blue",
            )
        )
        self.console.print()

    def show_agent_progress(self, agent_id: str, status: str, details: str = ""):
        """Display individual agent progress"""
        status_icon = (
            "✅" if status == "completed" else "🔄" if status == "running" else "❌"
        )
        status_color = (
            "green"
            if status == "completed"
            else "blue"
            if status == "running"
            else "red"
        )

        message = f"[{status_color}]{status_icon} {agent_id}: {status.title()}[/{status_color}]"
        if details:
            message += f" - [dim]{details}[/dim]"

        self.console.print(f"  {message}")

    def show_synthesis_start(self):
        """Display solution synthesis start"""
        self._show_step("Solution Synthesis")

        self.console.print(
            Panel(
                "[purple]🔄 O3-mini intelligently combining all agent outputs[/purple]\n"
                "[dim]• Resolving conflicts between agents\n"
                "• Filling gaps in coverage\n"
                "• Creating coherent final solution[/dim]",
                title="🧠 Intelligent Integration",
                border_style="purple",
            )
        )
        self.console.print()

    def show_file_generation(self, files_queued: list[str], files_created: list[str]):
        """Display file generation results"""
        self._show_step("File Generation")

        # Show files queued vs created
        table = Table(title="📁 File Generation Results")
        table.add_column("Status", style="cyan", width=12)
        table.add_column("Count", style="yellow", width=8)
        table.add_column("Details", style="white")

        table.add_row(
            "📋 Queued",
            str(len(files_queued)),
            f"{len(files_queued)} files identified for creation",
        )
        table.add_row(
            "✅ Created",
            str(len(files_created)),
            f"{len(files_created)} files successfully written",
        )

        success_rate = (
            (len(files_created) / len(files_queued) * 100) if files_queued else 0
        )
        table.add_row(
            "📊 Success", f"{success_rate:.1f}%", "File generation success rate"
        )

        self.console.print(table)

        # Show created files
        if files_created:
            self.console.print("\n[green]📄 Generated Files:[/green]")
            for file_path in files_created:
                self.console.print(f"  ✅ [cyan]{file_path}[/cyan]")

        self.console.print()

    def show_final_results(
        self, project_path: str, execution_time: float, success: bool
    ):
        """Display final results summary"""
        status_color = "green" if success else "red"
        status_icon = "✅" if success else "❌"
        status_text = "SUCCESS" if success else "FAILED"

        # Results panel
        results_content = (
            f"[{status_color}]{status_icon} {status_text}[/{status_color}]\n\n"
        )
        results_content += (
            f"[white]📁 Project Location:[/white] [cyan]{project_path}[/cyan]\n"
        )
        results_content += (
            f"[white]⏱️ Total Time:[/white] [yellow]{execution_time:.1f}s[/yellow]\n"
        )
        results_content += (
            "[white]🔄 Workflow:[/white] [blue]5-Stage Pipeline Complete[/blue]"
        )

        self.console.print(
            Panel(results_content, title="🎯 Final Results", border_style=status_color)
        )

        # Next steps
        if success:
            self.console.print("\n[green]🚀 Next Steps:[/green]")
            self.console.print(
                f"  📂 Review generated files in: [cyan]{project_path}[/cyan]"
            )
            self.console.print(
                f"  📋 Check logs for details: [cyan]{project_path}/logs/[/cyan]"
            )
            self.console.print("  🔧 Test and customize the generated solution")

        self.console.print()

    def show_error(self, error_message: str, stage: str = "Unknown"):
        """Display error in a clear format"""
        self.console.print(
            Panel(
                f"[red]❌ Error in {stage}:[/red]\n\n" f"[white]{error_message}[/white]",
                title="🚨 Execution Failed",
                border_style="red",
            )
        )
        self.console.print()

    def show_pretty_json(self, data: dict[str, Any], title: str = "Data"):
        """Display JSON data with pretty formatting"""
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)

        self.console.print(Panel(syntax, title=f"📊 {title}", border_style="blue"))
        self.console.print()

    def show_prompt_preview(self, prompt: str, title: str = "Generated Prompt"):
        """Display prompt with proper formatting"""
        # Truncate very long prompts for console display
        if len(prompt) > 1000:
            preview = prompt[:1000] + "\n\n[... truncated for display ...]"
        else:
            preview = prompt

        self.console.print(
            Panel(
                f"[white]{preview}[/white]", title=f"📝 {title}", border_style="yellow"
            )
        )
        self.console.print()

    def _show_step(self, step_name: str):
        """Display step header with progress"""
        self.current_step += 1

        self.console.print(
            f"\n[bold blue]━━━ Step {self.current_step}/{self.total_steps}: {step_name} ━━━[/bold blue]"
        )

        # Calculate elapsed time
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self.console.print(f"[dim]⏱️ Elapsed: {elapsed:.1f}s[/dim]\n")

    def clear(self):
        """Clear the console"""
        self.console.clear()

    def print(self, message: str):
        """Simple print method for basic messages"""
        self.console.print(message)
