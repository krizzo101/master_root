#!/usr/bin/env python3
"""
Auto-Forge Factory - End-to-End Demonstration

This script demonstrates the complete autonomous software development pipeline
from requirements to production-ready code.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any

import httpx
import websockets
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from auto_forge_factory.models.schemas import (
    DevelopmentRequest,
    Language,
    Framework,
    CloudProvider,
)

console = Console()


class AutoForgeDemo:
    """End-to-end demonstration of the Auto-Forge Factory."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
        self.job_id = None
        self.websocket = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        if self.websocket:
            await self.websocket.close()

    async def check_factory_health(self) -> bool:
        """Check if the Auto-Forge Factory is healthy."""
        try:
            response = await self.client.get("/health")
            if response.status_code == 200:
                health_data = response.json()
                console.print(
                    f"✅ Factory Status: {health_data['status']}", style="green"
                )
                return True
            else:
                console.print(
                    f"❌ Factory Health Check Failed: {response.status_code}",
                    style="red",
                )
                return False
        except Exception as e:
            console.print(f"❌ Cannot connect to Auto-Forge Factory: {e}", style="red")
            return False

    async def get_factory_status(self) -> Dict[str, Any]:
        """Get the current factory status."""
        response = await self.client.get("/factory/status")
        return response.json()

    async def start_development_job(self, request: DevelopmentRequest) -> str:
        """Start a new development job."""
        console.print("\n🚀 Starting Development Job...", style="bold blue")

        # Display the request
        table = Table(title="Development Request")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Project Name", request.name)
        table.add_row("Description", request.description)
        table.add_row("Target Language", request.target_language.value)
        table.add_row("Target Framework", request.target_framework.value)
        table.add_row("Architecture", request.target_architecture)
        table.add_row("Priority", str(request.priority))
        table.add_row(
            "Requirements", "\n".join(f"• {req}" for req in request.requirements)
        )

        console.print(table)

        # Submit the job
        response = await self.client.post("/develop", json=request.model_dump())

        if response.status_code == 200:
            job_data = response.json()
            self.job_id = job_data["job_id"]
            console.print(f"✅ Job Started Successfully!", style="green")
            console.print(f"📋 Job ID: {self.job_id}", style="cyan")
            console.print(f"🔗 Progress URL: {job_data['progress_url']}", style="cyan")
            console.print(
                f"🔌 WebSocket URL: {job_data['websocket_url']}", style="cyan"
            )
            return self.job_id
        else:
            console.print(f"❌ Failed to start job: {response.text}", style="red")
            raise Exception("Failed to start development job")

    async def monitor_progress_websocket(self):
        """Monitor job progress via WebSocket."""
        if not self.job_id:
            return

        websocket_url = f"ws://localhost:8000/ws/{self.job_id}"

        try:
            async with websockets.connect(websocket_url) as websocket:
                self.websocket = websocket
                console.print(
                    f"🔌 Connected to WebSocket: {websocket_url}", style="cyan"
                )

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "Monitoring development progress...", total=None
                    )

                    while True:
                        try:
                            message = await websocket.recv()
                            data = json.loads(message)

                            if data["type"] == "progress":
                                progress_data = data["data"]
                                progress.update(
                                    task,
                                    description=f"Phase: {progress_data.get('current_phase', 'Unknown')} - {progress_data.get('overall_progress_percent', 0):.1f}%",
                                )

                                # Check if job is complete
                                if progress_data.get("status") in [
                                    "completed",
                                    "failed",
                                ]:
                                    break

                        except websockets.exceptions.ConnectionClosed:
                            console.print(
                                "🔌 WebSocket connection closed", style="yellow"
                            )
                            break
                        except Exception as e:
                            console.print(f"⚠️ WebSocket error: {e}", style="yellow")
                            break

        except Exception as e:
            console.print(f"❌ WebSocket connection failed: {e}", style="red")

    async def monitor_progress_polling(self):
        """Monitor job progress via polling."""
        if not self.job_id:
            return

        console.print("\n📊 Monitoring Development Progress...", style="bold blue")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Polling for progress updates...", total=None)

            while True:
                try:
                    response = await self.client.get(f"/status/{self.job_id}")

                    if response.status_code == 200:
                        status_data = response.json()

                        progress.update(
                            task,
                            description=f"Status: {status_data['status']} - Phase: {status_data.get('current_phase', 'Unknown')} - {status_data.get('overall_progress_percent', 0):.1f}%",
                        )

                        # Check if job is complete
                        if status_data["status"] in ["completed", "failed"]:
                            console.print(
                                f"\n🏁 Job {status_data['status'].upper()}!",
                                style=(
                                    "bold green"
                                    if status_data["status"] == "completed"
                                    else "bold red"
                                ),
                            )
                            break

                    await asyncio.sleep(2)  # Poll every 2 seconds

                except Exception as e:
                    console.print(f"⚠️ Polling error: {e}", style="yellow")
                    await asyncio.sleep(5)

    async def get_job_results(self) -> Dict[str, Any]:
        """Get the final job results and artifacts."""
        if not self.job_id:
            raise Exception("No job ID available")

        console.print("\n📦 Retrieving Job Results...", style="bold blue")

        response = await self.client.get(f"/artifacts/{self.job_id}")

        if response.status_code == 200:
            result_data = response.json()

            # Display results summary
            table = Table(title="Development Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Status", result_data["status"])
            table.add_row("Quality Score", f"{result_data['quality_score']:.2f}/1.0")
            table.add_row("Security Score", f"{result_data['security_score']:.2f}/1.0")
            table.add_row(
                "Performance Score", f"{result_data['performance_score']:.2f}/1.0"
            )
            table.add_row("Total Tokens Used", f"{result_data['total_tokens_used']:,}")
            table.add_row("Total Cost", f"${result_data['total_cost']:.4f}")
            table.add_row(
                "Execution Time", f"{result_data['execution_time_seconds']:.1f}s"
            )
            table.add_row("Total Artifacts", str(len(result_data["artifacts"])))

            console.print(table)

            # Display artifacts tree
            tree = Tree("📁 Generated Artifacts")
            for artifact in result_data["artifacts"]:
                artifact_node = tree.add(f"📄 {artifact['name']} ({artifact['type']})")
                if artifact.get("metadata"):
                    for key, value in artifact["metadata"].items():
                        artifact_node.add(f"  {key}: {value}")

            console.print(tree)

            # Display summary
            console.print(
                Panel(
                    result_data["summary"],
                    title="📋 Development Summary",
                    style="green",
                )
            )

            # Display deployment instructions
            if result_data.get("deployment_instructions"):
                console.print(
                    Panel(
                        result_data["deployment_instructions"],
                        title="🚀 Deployment Instructions",
                        style="blue",
                    )
                )

            return result_data
        else:
            console.print(f"❌ Failed to get job results: {response.text}", style="red")
            raise Exception("Failed to get job results")

    async def list_all_jobs(self):
        """List all jobs in the factory."""
        console.print("\n📋 Listing All Jobs...", style="bold blue")

        response = await self.client.get("/jobs")

        if response.status_code == 200:
            jobs_data = response.json()

            # Display active jobs
            if jobs_data["active_jobs"]:
                table = Table(title="Active Jobs")
                table.add_column("Job ID", style="cyan")
                table.add_column("Project Name", style="white")
                table.add_column("Status", style="green")
                table.add_column("Started At", style="yellow")
                table.add_column("Current Phase", style="blue")

                for job in jobs_data["active_jobs"]:
                    table.add_row(
                        job["job_id"][:8] + "...",
                        job["project_name"],
                        job["status"],
                        job["started_at"],
                        str(job["current_phase"]),
                    )

                console.print(table)

            # Display completed jobs
            if jobs_data["completed_jobs"]:
                table = Table(title="Completed Jobs")
                table.add_column("Job ID", style="cyan")
                table.add_column("Project Name", style="white")
                table.add_column("Status", style="green")
                table.add_column("Completed At", style="yellow")
                table.add_column("Quality Score", style="blue")
                table.add_column("Total Cost", style="red")

                for job in jobs_data["completed_jobs"][:5]:  # Show last 5
                    table.add_row(
                        job["job_id"][:8] + "...",
                        job["project_name"],
                        job["status"],
                        job["completed_at"] or "N/A",
                        f"{job.get('quality_score', 0):.2f}",
                        f"${job.get('total_cost', 0):.4f}",
                    )

                console.print(table)

            console.print(
                f"📊 Total Active: {jobs_data['total_active']}, Total Completed: {jobs_data['total_completed']}",
                style="cyan",
            )
        else:
            console.print(f"❌ Failed to list jobs: {response.text}", style="red")


async def create_sample_requests() -> list[DevelopmentRequest]:
    """Create sample development requests for demonstration."""

    requests = [
        DevelopmentRequest(
            name="Task Management API",
            description="A RESTful API for collaborative task management with real-time updates",
            requirements=[
                "User authentication and authorization with JWT tokens",
                "Project creation and management with team collaboration",
                "Task creation, assignment, and status tracking",
                "Real-time notifications for task updates",
                "File upload and attachment support",
                "Search and filtering capabilities",
                "Role-based access control",
                "API rate limiting and security",
            ],
            target_language=Language.PYTHON,
            target_framework=Framework.FASTAPI,
            target_architecture="microservices",
            cloud_provider=CloudProvider.AWS,
            priority=8,
        ),
        DevelopmentRequest(
            name="E-commerce Platform",
            description="A complete e-commerce platform with payment processing and inventory management",
            requirements=[
                "Product catalog with categories and search",
                "Shopping cart and checkout process",
                "Payment gateway integration (Stripe/PayPal)",
                "User account management and order history",
                "Inventory management and stock tracking",
                "Admin dashboard for product management",
                "Email notifications and order confirmations",
                "Responsive design for mobile and desktop",
            ],
            target_language=Language.JAVASCRIPT,
            target_framework=Framework.REACT,
            target_architecture="monolith",
            cloud_provider=CloudProvider.VERCEL,
            priority=9,
        ),
        DevelopmentRequest(
            name="Data Analytics Dashboard",
            description="A real-time data analytics dashboard with interactive visualizations",
            requirements=[
                "Real-time data ingestion from multiple sources",
                "Interactive charts and graphs (line, bar, pie charts)",
                "Data filtering and drill-down capabilities",
                "User authentication and role-based access",
                "Export functionality (PDF, CSV, Excel)",
                "Custom dashboard creation and sharing",
                "Alert system for data thresholds",
                "Performance optimization for large datasets",
            ],
            target_language=Language.PYTHON,
            target_framework=Framework.DJANGO,
            target_architecture="microservices",
            cloud_provider=CloudProvider.GCP,
            priority=7,
        ),
    ]

    return requests


async def main():
    """Main demonstration function."""
    console.print(
        Panel.fit("🚀 Auto-Forge Factory - End-to-End Demonstration", style="bold blue")
    )

    # Create sample requests
    sample_requests = await create_sample_requests()

    # Select a request for demonstration
    console.print("\n📋 Available Sample Projects:", style="bold")
    for i, request in enumerate(sample_requests, 1):
        console.print(f"{i}. {request.name} - {request.description}", style="cyan")

    # For demo purposes, use the first request
    selected_request = sample_requests[0]
    console.print(f"\n🎯 Selected Project: {selected_request.name}", style="bold green")

    async with AutoForgeDemo() as demo:
        # Check factory health
        if not await demo.check_factory_health():
            console.print(
                "❌ Factory is not healthy. Please ensure it's running.", style="red"
            )
            return

        # Get factory status
        factory_status = await demo.get_factory_status()
        console.print(
            f"🏭 Factory Status: {factory_status['active_jobs']} active jobs, {factory_status['completed_jobs']} completed",
            style="cyan",
        )

        # Start development job
        try:
            job_id = await demo.start_development_job(selected_request)

            # Monitor progress (choose one method)
            console.print("\n🔍 Choose monitoring method:", style="bold")
            console.print("1. WebSocket (real-time updates)", style="cyan")
            console.print("2. Polling (HTTP requests)", style="cyan")

            # For demo, use polling as it's more reliable
            await demo.monitor_progress_polling()

            # Get results
            results = await demo.get_job_results()

            # List all jobs
            await demo.list_all_jobs()

            console.print("\n🎉 Demonstration Complete!", style="bold green")
            console.print(
                "The Auto-Forge Factory has successfully demonstrated:", style="cyan"
            )
            console.print(
                "✅ Autonomous software development from requirements to production-ready code",
                style="green",
            )
            console.print(
                "✅ Multi-agent orchestration and coordination", style="green"
            )
            console.print("✅ Real-time progress monitoring and updates", style="green")
            console.print("✅ Quality assurance and security validation", style="green")
            console.print(
                "✅ Complete artifact generation and deployment instructions",
                style="green",
            )

        except Exception as e:
            console.print(f"❌ Demonstration failed: {e}", style="red")


if __name__ == "__main__":
    asyncio.run(main())
