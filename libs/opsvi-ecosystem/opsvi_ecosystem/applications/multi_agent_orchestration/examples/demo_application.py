"""
Demo Application for Multi-Agent Orchestration

This module provides a comprehensive demonstration of the multi-agent
orchestration system, showcasing various workflow patterns and agent
collaboration scenarios.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..agents.research_agent import ResearchAgent
from ..agents.task_agent import TaskAgent
from ..communication.message_broker import MessageBroker

# Import orchestration components
from ..orchestrator.workflow_orchestrator import WorkflowOrchestrator
from .workflow_examples import (
    create_conditional_workflow,
    create_data_analysis_workflow,
    create_parallel_processing_workflow,
    create_research_pipeline,
    get_available_workflows,
    get_workflow_description,
)


class DemoApplication:
    """
    Comprehensive demo application for multi-agent orchestration.

    This application demonstrates:
    - Multi-agent workflow execution
    - Different orchestration patterns
    - Agent collaboration and communication
    - Real-time monitoring and metrics
    - Error handling and recovery
    """

    def __init__(self, work_directory: str = "./demo_workspace"):
        """
        Initialize the demo application.

        Args:
            work_directory: Working directory for demo files
        """
        self.work_directory = Path(work_directory)
        self.work_directory.mkdir(exist_ok=True)

        # Setup logging
        self.logger = self._setup_logging()

        # Initialize components
        self.message_broker = MessageBroker()
        self.orchestrator = WorkflowOrchestrator(
            message_broker=self.message_broker, logger=self.logger
        )

        # Agent instances
        self.research_agent: ResearchAgent | None = None
        self.task_agent: TaskAgent | None = None

        # Demo state
        self.demo_results: dict[str, Any] = {}
        self.execution_history: list[dict[str, Any]] = []

        self.logger.info("Demo application initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("demo_application")
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # File handler
        log_file = self.work_directory / "demo.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    async def initialize_agents(self) -> None:
        """Initialize and register agents."""
        self.logger.info("Initializing agents...")

        # Create agents
        self.research_agent = ResearchAgent(
            agent_id="research_agent", name="Demo Research Agent", logger=self.logger
        )

        self.task_agent = TaskAgent(
            agent_id="task_agent",
            name="Demo Task Agent",
            work_directory=str(self.work_directory),
            logger=self.logger,
        )

        # Register with orchestrator
        await self.orchestrator.register_agent(self.research_agent)
        await self.orchestrator.register_agent(self.task_agent)

        self.logger.info("Agents initialized and registered")

    async def create_sample_data(self) -> None:
        """Create sample data files for demonstrations."""
        self.logger.info("Creating sample data files...")

        # Sample CSV data
        sample_data = [
            {"id": 1, "name": "Item A", "category": "Electronics", "value": 100.0},
            {"id": 2, "name": "Item B", "category": "Books", "value": 25.0},
            {"id": 3, "name": "Item C", "category": "Electronics", "value": 150.0},
            {"id": 4, "name": "Item D", "category": "Clothing", "value": 75.0},
            {"id": 5, "name": "Item E", "category": "Books", "value": 30.0},
            {"id": 6, "name": "Item F", "category": "Electronics", "value": 200.0},
            {"id": 7, "name": "Item G", "category": "Clothing", "value": 45.0},
            {"id": 8, "name": "Item H", "category": "Books", "value": 15.0},
        ]

        # Write sample CSV
        import csv

        csv_file = self.work_directory / "sample_data.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sample_data[0].keys())
            writer.writeheader()
            writer.writerows(sample_data)

        # Sample JSON data
        json_data = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "description": "Sample dataset for demo",
            },
            "data": sample_data,
        }

        json_file = self.work_directory / "sample_data.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2)

        # Raw data for pipeline demo
        raw_data = sample_data + [
            {"id": 9, "name": "Item I", "category": "Electronics", "value": 300.0},
            {"id": 10, "name": "Item J", "category": "Books", "value": 20.0},
            # Add some duplicate and null data for cleaning demo
            {
                "id": 1,
                "name": "Item A",
                "category": "Electronics",
                "value": 100.0,
            },  # Duplicate
            {
                "id": 11,
                "name": "Item K",
                "category": None,
                "value": 50.0,
            },  # Null category
            {
                "id": 12,
                "name": None,
                "category": "Clothing",
                "value": 60.0,
            },  # Null name
        ]

        raw_csv_file = self.work_directory / "raw_data.csv"
        with open(raw_csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "category", "value"])
            writer.writeheader()
            writer.writerows(raw_data)

        self.logger.info("Sample data files created")

    async def run_workflow_demo(self, workflow_type: str) -> dict[str, Any]:
        """
        Run a specific workflow demonstration.

        Args:
            workflow_type: Type of workflow to run

        Returns:
            Workflow execution results
        """
        self.logger.info(f"Running {workflow_type} workflow demo...")

        try:
            # Create workflow configuration
            if workflow_type == "data_analysis":
                workflow_config = create_data_analysis_workflow()
            elif workflow_type == "research_pipeline":
                workflow_config = create_research_pipeline()
            elif workflow_type == "parallel_processing":
                workflow_config = create_parallel_processing_workflow()
            elif workflow_type == "conditional":
                workflow_config = create_conditional_workflow()
            else:
                raise ValueError(f"Unsupported workflow type: {workflow_type}")

            # Create and execute workflow
            workflow_id = self.orchestrator.create_workflow(
                name=workflow_config["name"],
                steps=workflow_config["steps"],
                execution_pattern=workflow_config["execution_pattern"],
                max_retries=workflow_config.get("max_retries", 2),
                timeout=workflow_config.get("timeout"),
            )

            # Execute workflow
            start_time = datetime.now()
            results = await self.orchestrator.execute_workflow(workflow_id)
            execution_time = (datetime.now() - start_time).total_seconds()

            # Store results
            demo_result = {
                "workflow_type": workflow_type,
                "workflow_id": workflow_id,
                "execution_time": execution_time,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }

            self.demo_results[workflow_type] = demo_result
            self.execution_history.append(demo_result)

            self.logger.info(
                f"Completed {workflow_type} workflow demo in {execution_time:.2f}s"
            )
            return demo_result

        except Exception as e:
            self.logger.error(f"Failed to run {workflow_type} workflow demo: {e}")
            return {
                "workflow_type": workflow_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_all_demos(self) -> dict[str, Any]:
        """
        Run all available workflow demonstrations.

        Returns:
            Complete demo results
        """
        self.logger.info("Starting comprehensive demo suite...")

        # Available workflows (excluding research_pipeline for now due to web dependencies)
        workflows = ["data_analysis", "parallel_processing", "conditional"]

        demo_results = {}

        for workflow_type in workflows:
            try:
                result = await self.run_workflow_demo(workflow_type)
                demo_results[workflow_type] = result

                # Brief pause between demos
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Demo failed for {workflow_type}: {e}")
                demo_results[workflow_type] = {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

        # Generate summary report
        summary = self._generate_demo_summary(demo_results)

        self.logger.info("Comprehensive demo suite completed")
        return {
            "summary": summary,
            "individual_results": demo_results,
            "orchestrator_metrics": self.orchestrator.get_metrics(),
            "execution_history": self.orchestrator.get_execution_history(),
        }

    def _generate_demo_summary(self, results: dict[str, Any]) -> dict[str, Any]:
        """Generate a summary of demo results."""
        successful = [k for k, v in results.items() if "error" not in v]
        failed = [k for k, v in results.items() if "error" in v]

        total_execution_time = sum(
            r.get("execution_time", 0)
            for r in results.values()
            if "execution_time" in r
        )

        return {
            "total_workflows": len(results),
            "successful_workflows": len(successful),
            "failed_workflows": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
            "total_execution_time": total_execution_time,
            "average_execution_time": (
                total_execution_time / len(successful) if successful else 0
            ),
            "successful_workflows_list": successful,
            "failed_workflows_list": failed,
        }

    async def interactive_demo(self) -> None:
        """Run an interactive demo session."""
        print("\n" + "=" * 60)
        print("Multi-Agent Orchestration System - Interactive Demo")
        print("=" * 60)

        while True:
            print("\nAvailable options:")
            print("1. Run single workflow demo")
            print("2. Run all workflow demos")
            print("3. Show orchestrator metrics")
            print("4. Show execution history")
            print("5. Show agent capabilities")
            print("6. Exit")

            try:
                choice = input("\nEnter your choice (1-6): ").strip()

                if choice == "1":
                    await self._interactive_single_demo()
                elif choice == "2":
                    await self._interactive_all_demos()
                elif choice == "3":
                    self._show_metrics()
                elif choice == "4":
                    self._show_execution_history()
                elif choice == "5":
                    self._show_agent_capabilities()
                elif choice == "6":
                    print("Exiting demo...")
                    break
                else:
                    print("Invalid choice. Please try again.")

            except KeyboardInterrupt:
                print("\nExiting demo...")
                break
            except Exception as e:
                print(f"Error: {e}")

    async def _interactive_single_demo(self) -> None:
        """Interactive single workflow demo."""
        workflows = get_available_workflows()

        print("\nAvailable workflows:")
        for i, workflow in enumerate(workflows, 1):
            description = get_workflow_description(workflow)
            print(f"{i}. {workflow}: {description}")

        try:
            choice = int(input("\nSelect workflow (number): ")) - 1
            if 0 <= choice < len(workflows):
                workflow_type = workflows[choice]
                print(f"\nRunning {workflow_type} demo...")
                result = await self.run_workflow_demo(workflow_type)
                self._display_workflow_result(result)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")

    async def _interactive_all_demos(self) -> None:
        """Interactive all demos."""
        print("\nRunning all workflow demos...")
        results = await self.run_all_demos()

        print("\n" + "=" * 50)
        print("COMPREHENSIVE DEMO RESULTS")
        print("=" * 50)

        summary = results["summary"]
        print(f"Total Workflows: {summary['total_workflows']}")
        print(f"Successful: {summary['successful_workflows']}")
        print(f"Failed: {summary['failed_workflows']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        print(f"Average Execution Time: {summary['average_execution_time']:.2f}s")

        if summary["successful_workflows_list"]:
            print(
                f"\nSuccessful Workflows: {', '.join(summary['successful_workflows_list'])}"
            )
        if summary["failed_workflows_list"]:
            print(f"Failed Workflows: {', '.join(summary['failed_workflows_list'])}")

    def _show_metrics(self) -> None:
        """Show orchestrator metrics."""
        metrics = self.orchestrator.get_metrics()

        print("\n" + "=" * 40)
        print("ORCHESTRATOR METRICS")
        print("=" * 40)

        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")

    def _show_execution_history(self) -> None:
        """Show execution history."""
        history = self.orchestrator.get_execution_history()

        print("\n" + "=" * 50)
        print("EXECUTION HISTORY")
        print("=" * 50)

        if not history:
            print("No workflows executed yet.")
            return

        for i, record in enumerate(history, 1):
            print(f"\n{i}. {record['name']} ({record['workflow_id'][:8]}...)")
            print(f"   Status: {record['status']}")
            print(f"   Execution Time: {record['execution_time']:.2f}s")
            print(f"   Steps Completed: {record['steps_completed']}")
            print(f"   Steps Failed: {record['steps_failed']}")
            if record["errors"]:
                print(f"   Errors: {', '.join(record['errors'])}")

    def _show_agent_capabilities(self) -> None:
        """Show agent capabilities."""
        print("\n" + "=" * 40)
        print("AGENT CAPABILITIES")
        print("=" * 40)

        if self.research_agent:
            print("\nResearch Agent:")
            capabilities = self.research_agent.get_capabilities()
            for key, value in capabilities.items():
                print(f"  {key}: {value}")

        if self.task_agent:
            print("\nTask Agent:")
            capabilities = self.task_agent.get_capabilities()
            for key, value in capabilities.items():
                print(f"  {key}: {value}")

    def _display_workflow_result(self, result: dict[str, Any]) -> None:
        """Display workflow execution result."""
        print("\n" + "=" * 50)
        print("WORKFLOW EXECUTION RESULT")
        print("=" * 50)

        if "error" in result:
            print(f"Error: {result['error']}")
            return

        workflow_results = result.get("results", {})
        print(f"Workflow: {workflow_results.get('name', 'Unknown')}")
        print(f"Status: {workflow_results.get('status', 'Unknown')}")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
        print(f"Steps: {len(workflow_results.get('steps', {}))}")

        # Show step details
        steps = workflow_results.get("steps", {})
        completed_steps = [s for s in steps.values() if s.get("status") == "completed"]
        failed_steps = [s for s in steps.values() if s.get("status") == "failed"]

        print(f"Completed Steps: {len(completed_steps)}")
        print(f"Failed Steps: {len(failed_steps)}")

        if failed_steps:
            print("\nFailed Steps:")
            for step in failed_steps:
                print(
                    f"  - {step.get('step_id', 'Unknown')}: {step.get('error', 'Unknown error')}"
                )

    async def save_demo_results(self) -> None:
        """Save demo results to file."""
        results_file = self.work_directory / "demo_results.json"

        demo_data = {
            "timestamp": datetime.now().isoformat(),
            "demo_results": self.demo_results,
            "execution_history": self.execution_history,
            "orchestrator_metrics": self.orchestrator.get_metrics(),
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(demo_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Demo results saved to {results_file}")

    async def cleanup(self) -> None:
        """Cleanup resources."""
        self.logger.info("Cleaning up demo application...")

        # Save results
        await self.save_demo_results()

        # Shutdown orchestrator
        await self.orchestrator.shutdown()

        self.logger.info("Demo application cleanup complete")


async def main() -> None:
    """Main demo application entry point."""
    demo = DemoApplication()

    try:
        # Initialize
        await demo.initialize_agents()
        await demo.create_sample_data()

        # Check if running interactively
        if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
            await demo.interactive_demo()
        else:
            # Run automated demo
            print("Running automated multi-agent orchestration demo...")
            results = await demo.run_all_demos()

            print("\n" + "=" * 60)
            print("DEMO COMPLETED SUCCESSFULLY")
            print("=" * 60)

            summary = results["summary"]
            print(f"Workflows executed: {summary['total_workflows']}")
            print(f"Success rate: {summary['success_rate']:.1f}%")
            print(f"Total execution time: {summary['total_execution_time']:.2f}s")

    except Exception as e:
        print(f"Demo failed: {e}")
        demo.logger.error(f"Demo failed: {e}")
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
