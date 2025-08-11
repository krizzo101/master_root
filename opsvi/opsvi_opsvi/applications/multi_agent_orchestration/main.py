#!/usr/bin/env python3
"""
Multi-Agent Orchestration System - Main Entry Point

This module provides the main entry point for the multi-agent orchestration
system, supporting both demo mode and production usage patterns.
"""

import argparse
import asyncio
import logging
from pathlib import Path
import sys
from typing import Optional

from .agents.research_agent import ResearchAgent
from .agents.task_agent import TaskAgent
from .communication.message_broker import MessageBroker

# Import application components
from .examples.demo_application import DemoApplication
from .examples.workflow_examples import create_workflow_by_type, get_available_workflows
from .orchestrator.workflow_orchestrator import ExecutionPattern, WorkflowOrchestrator


def setup_logging(
    level: str = "INFO", log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path

    Returns:
        Configured logger
    """
    logger = logging.getLogger("src.applications.multi_agent_orchestration")
    logger.setLevel(getattr(logging, level.upper()))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


async def run_demo(
    interactive: bool = False, work_dir: str = "./demo_workspace"
) -> None:
    """
    Run the demonstration application.

    Args:
        interactive: Whether to run in interactive mode
        work_dir: Working directory for demo files
    """
    print("Multi-Agent Orchestration System - Demo Mode")
    print("=" * 50)

    demo = DemoApplication(work_dir)

    try:
        await demo.initialize_agents()
        await demo.create_sample_data()

        if interactive:
            await demo.interactive_demo()
        else:
            results = await demo.run_all_demos()

            # Display summary
            summary = results["summary"]
            print("\nDemo Results:")
            print(f"  Workflows executed: {summary['total_workflows']}")
            print(f"  Success rate: {summary['success_rate']:.1f}%")
            print(f"  Total execution time: {summary['total_execution_time']:.2f}s")

            if summary["failed_workflows_list"]:
                print(
                    f"  Failed workflows: {', '.join(summary['failed_workflows_list'])}"
                )

    except Exception as e:
        print(f"Demo failed: {e}")
        logging.error(f"Demo failed: {e}")
    finally:
        await demo.cleanup()


async def run_single_workflow(
    workflow_type: str,
    work_dir: str = "./workspace",
    agents_config: Optional[dict] = None,
) -> None:
    """
    Run a single workflow.

    Args:
        workflow_type: Type of workflow to run
        work_dir: Working directory
        agents_config: Optional agent configuration
    """
    logger = logging.getLogger("single_workflow")

    # Create workspace
    workspace = Path(work_dir)
    workspace.mkdir(exist_ok=True)

    # Initialize components
    message_broker = MessageBroker()
    orchestrator = WorkflowOrchestrator(message_broker, logger)

    try:
        # Create and register agents
        research_agent = ResearchAgent("research_agent", logger=logger)
        task_agent = TaskAgent("task_agent", work_directory=work_dir, logger=logger)

        await orchestrator.register_agent(research_agent)
        await orchestrator.register_agent(task_agent)

        # Create workflow
        workflow_config = create_workflow_by_type(workflow_type)

        workflow_id = orchestrator.create_workflow(
            name=workflow_config["name"],
            steps=workflow_config["steps"],
            execution_pattern=workflow_config["execution_pattern"],
            max_retries=workflow_config.get("max_retries", 2),
            timeout=workflow_config.get("timeout"),
        )

        print(f"Executing {workflow_type} workflow...")

        # Execute workflow
        results = await orchestrator.execute_workflow(workflow_id)

        # Display results
        print("\nWorkflow Results:")
        print(f"  Status: {results['status']}")
        print(f"  Execution time: {results.get('execution_time', 0):.2f}s")
        print(f"  Steps: {len(results['steps'])}")

        completed_steps = [
            s for s in results["steps"].values() if s.get("status") == "completed"
        ]
        failed_steps = [
            s for s in results["steps"].values() if s.get("status") == "failed"
        ]

        print(f"  Completed: {len(completed_steps)}")
        print(f"  Failed: {len(failed_steps)}")

        if failed_steps:
            print("\nFailed Steps:")
            for step in failed_steps:
                print(
                    f"    {step.get('step_id')}: {step.get('error', 'Unknown error')}"
                )

    except Exception as e:
        print(f"Workflow execution failed: {e}")
        logger.error(f"Workflow execution failed: {e}")
    finally:
        await orchestrator.shutdown()


async def run_custom_workflow(config_file: str, work_dir: str = "./workspace") -> None:
    """
    Run a custom workflow from configuration file.

    Args:
        config_file: Path to workflow configuration file
        work_dir: Working directory
    """
    import json

    import yaml

    logger = logging.getLogger("custom_workflow")

    # Load configuration
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    if config_path.suffix.lower() in [".yaml", ".yml"]:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        with open(config_path) as f:
            config = json.load(f)

    # Create workspace
    workspace = Path(work_dir)
    workspace.mkdir(exist_ok=True)

    # Initialize components
    message_broker = MessageBroker()
    orchestrator = WorkflowOrchestrator(message_broker, logger)

    try:
        # Create and register agents based on config
        agents_config = config.get("agents", {})

        for agent_id, agent_config in agents_config.items():
            agent_type = agent_config.get("type", "task")

            if agent_type == "research":
                agent = ResearchAgent(agent_id, logger=logger)
            elif agent_type == "task":
                agent = TaskAgent(agent_id, work_directory=work_dir, logger=logger)
            else:
                logger.warning(f"Unknown agent type: {agent_type}, using TaskAgent")
                agent = TaskAgent(agent_id, work_directory=work_dir, logger=logger)

            await orchestrator.register_agent(agent)

        # Create workflow from config
        workflow_config = config.get("workflow", {})

        workflow_id = orchestrator.create_workflow(
            name=workflow_config.get("name", "Custom Workflow"),
            steps=workflow_config.get("steps", []),
            execution_pattern=ExecutionPattern(
                workflow_config.get("execution_pattern", "sequential")
            ),
            max_retries=workflow_config.get("max_retries", 2),
            timeout=workflow_config.get("timeout"),
        )

        print(
            f"Executing custom workflow: {workflow_config.get('name', 'Custom Workflow')}"
        )

        # Execute workflow
        results = await orchestrator.execute_workflow(workflow_id)

        # Display results
        print("\nWorkflow Results:")
        print(f"  Status: {results['status']}")
        print(f"  Execution time: {results.get('execution_time', 0):.2f}s")
        print(f"  Steps: {len(results['steps'])}")

        # Save results if specified
        output_file = config.get("output_file")
        if output_file:
            output_path = workspace / output_file
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"  Results saved to: {output_path}")

    except Exception as e:
        print(f"Custom workflow execution failed: {e}")
        logger.error(f"Custom workflow execution failed: {e}")
    finally:
        await orchestrator.shutdown()


def list_workflows() -> None:
    """List available workflow types."""
    workflows = get_available_workflows()

    print("Available Workflow Types:")
    print("=" * 30)

    from .examples.workflow_examples import get_workflow_description

    for workflow_type in workflows:
        description = get_workflow_description(workflow_type)
        print(f"  {workflow_type}: {description}")


def create_sample_config(output_file: str = "sample_workflow.yaml") -> None:
    """Create a sample workflow configuration file."""
    import yaml

    sample_config = {
        "agents": {
            "research_agent": {"type": "research", "name": "Sample Research Agent"},
            "task_agent": {"type": "task", "name": "Sample Task Agent"},
        },
        "workflow": {
            "name": "Sample Custom Workflow",
            "execution_pattern": "sequential",
            "max_retries": 2,
            "timeout": 300,
            "steps": [
                {
                    "step_id": "research_step",
                    "agent_id": "research_agent",
                    "task_type": "web_research",
                    "task_data": {
                        "query": "machine learning trends 2024",
                        "max_results": 5,
                    },
                    "dependencies": [],
                    "timeout": 120,
                },
                {
                    "step_id": "process_step",
                    "agent_id": "task_agent",
                    "task_type": "data_processing",
                    "task_data": {"operation": "summarize"},
                    "dependencies": ["research_step"],
                    "timeout": 60,
                },
            ],
        },
        "output_file": "workflow_results.json",
    }

    with open(output_file, "w") as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)

    print(f"Sample configuration created: {output_file}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s demo                              # Run demo mode
  %(prog)s demo --interactive                # Run interactive demo
  %(prog)s workflow data_analysis            # Run specific workflow
  %(prog)s custom workflow.yaml             # Run custom workflow
  %(prog)s list                              # List available workflows
  %(prog)s sample-config                     # Create sample configuration
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demonstration")
    demo_parser.add_argument(
        "--interactive", action="store_true", help="Run interactive demo"
    )
    demo_parser.add_argument(
        "--work-dir", default="./demo_workspace", help="Working directory"
    )

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run specific workflow")
    workflow_parser.add_argument("type", help="Workflow type")
    workflow_parser.add_argument(
        "--work-dir", default="./workspace", help="Working directory"
    )

    # Custom workflow command
    custom_parser = subparsers.add_parser("custom", help="Run custom workflow")
    custom_parser.add_argument("config", help="Configuration file path")
    custom_parser.add_argument(
        "--work-dir", default="./workspace", help="Working directory"
    )

    # List command
    subparsers.add_parser("list", help="List available workflows")

    # Sample config command
    sample_parser = subparsers.add_parser(
        "sample-config", help="Create sample configuration"
    )
    sample_parser.add_argument(
        "--output", default="sample_workflow.yaml", help="Output file"
    )

    # Global options
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    parser.add_argument("--log-file", help="Log file path")

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_level, args.log_file)

    # Handle commands
    if args.command == "demo":
        asyncio.run(run_demo(args.interactive, args.work_dir))

    elif args.command == "workflow":
        available_workflows = get_available_workflows()
        if args.type not in available_workflows:
            print(f"Error: Unknown workflow type '{args.type}'")
            print(f"Available types: {', '.join(available_workflows)}")
            sys.exit(1)

        asyncio.run(run_single_workflow(args.type, args.work_dir))

    elif args.command == "custom":
        asyncio.run(run_custom_workflow(args.config, args.work_dir))

    elif args.command == "list":
        list_workflows()

    elif args.command == "sample-config":
        create_sample_config(args.output)

    else:
        # No command specified, show help
        parser.print_help()


if __name__ == "__main__":
    main()
