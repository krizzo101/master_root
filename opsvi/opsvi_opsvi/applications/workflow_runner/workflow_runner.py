import argparse
import logging

from .config import Config
from .prompt_parser import PromptParser


def main():
    parser = argparse.ArgumentParser(description="Agentic Workflow Runner")
    parser.add_argument("--config", type=str, help="Path to config YAML")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["generate", "execute"],
        required=True,
        help="Mode: generate or execute",
    )
    parser.add_argument("--prompt", type=str, help="Path to prompt/manifest file")
    args = parser.parse_args()

    config = Config(args.config)
    logging.info(f"Started workflow_runner in {args.mode} mode.")

    # Integrate prompt parsing and execution plan
    if args.prompt:
        parser = PromptParser(args.prompt)
        parser.parse()
        plan = parser.build_execution_plan()
        plan.pretty_print()
        logging.info(f"Execution plan built with {len(plan.plan)} steps.")
        # Execute each step in the plan
        for i, step in enumerate(plan.plan):
            logging.info(
                f"[EXECUTE] Step {i+1}: {step.name} (depends on: {step.dependencies})"
            )
            print(f"Executing: {step.name} (depends on: {step.dependencies})")
            # Simulate execution (replace with real logic as needed)
    else:
        logging.warning("No prompt file provided. Skipping prompt parsing.")

    if args.mode == "generate":
        logging.info("Workflow generation mode selected.")
        # TODO: Implement workflow generation logic
    elif args.mode == "execute":
        logging.info("Workflow execution mode selected.")
        # TODO: Implement workflow execution logic
    else:
        logging.error("Invalid mode.")


if __name__ == "__main__":
    main()
