import argparse
import sys

from asea_factory.orchestrator import PipelineOrchestrator
import yaml


def main():
    parser = argparse.ArgumentParser(description="SDLC Automation Factory CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Create project
    create_parser = subparsers.add_parser("create", help="Create a new project")
    create_parser.add_argument(
        "project_name", type=str, help="Project name or description"
    )

    # Design phase
    design_parser = subparsers.add_parser("design", help="Run interactive design phase")
    design_parser.add_argument(
        "--interactive", action="store_true", help="Interactive mode"
    )

    # Develop phase
    develop_parser = subparsers.add_parser(
        "develop", help="Run autonomous development phase"
    )
    develop_parser.add_argument("--from-design", type=str, help="Design artifact file")

    # Run full pipeline
    run_parser = subparsers.add_parser("run", help="Run full SDLC pipeline")
    run_parser.add_argument(
        "--autonomous", action="store_true", help="Fully autonomous mode"
    )

    # Status
    status_parser = subparsers.add_parser("status", help="Show live status")
    status_parser.add_argument(
        "--live", action="store_true", help="Live status updates"
    )

    # Agents
    agents_parser = subparsers.add_parser("agents", help="Monitor agents")
    agents_parser.add_argument(
        "--monitor", action="store_true", help="Monitor agent activity"
    )

    # Quality
    quality_parser = subparsers.add_parser("quality", help="Show quality dashboard")
    quality_parser.add_argument(
        "--dashboard", action="store_true", help="Show dashboard"
    )

    # Resources
    resources_parser = subparsers.add_parser("resources", help="Show resource usage")
    resources_parser.add_argument(
        "--monitor", action="store_true", help="Monitor resources"
    )

    args = parser.parse_args()

    orchestrator = PipelineOrchestrator()

    # If running in autonomous mode, check for requirements_input.yaml and inform user
    if args.command == "run" and args.autonomous:
        import os

        if os.path.exists("requirements_input.yaml"):
            print(
                "[SDLC Factory] Autonomous mode: requirements_input.yaml found and will be used for requirements input."
            )
        else:
            print(
                "[SDLC Factory] Autonomous mode: No requirements_input.yaml found. Interactive input will be required unless you provide this file."
            )

    if args.command == "create":
        print(f"[SDLC Factory] Project created: {args.project_name}")
        os.makedirs(args.project_name, exist_ok=True)
        # Optionally, initialize project metadata/config here
    elif args.command == "design":
        print("[SDLC Factory] Running design phase...")
        if args.interactive:
            requirements = orchestrator.requirements_agent.run()
        else:
            # Autonomous: load requirements from file or config
            if os.path.exists("requirements_input.yaml"):
                with open("requirements_input.yaml", "r") as f:
                    req_input = yaml.safe_load(f)
                requirements = orchestrator.requirements_agent.run(
                    requirements_input=req_input
                )
            else:
                print(
                    "[ERROR] requirements_input.yaml not found for autonomous design phase."
                )
                sys.exit(1)
        research = orchestrator.research_agent.run(
            [r.description for r in requirements.requirements if r.type == "functional"]
        )
        architecture = orchestrator.architecture_agent.run(
            [r.id for r in requirements.requirements], [f.id for f in research]
        )
        design_review = orchestrator.design_review_agent.run(architecture.id)
        # Save design artifacts
        with open("design_artifacts.yaml", "w") as f:
            yaml.safe_dump(
                {
                    "requirements": requirements.dict(),
                    "research": [r.dict() for r in research],
                    "architecture": architecture.dict(),
                    "design_review": design_review.dict(),
                },
                f,
            )
        print(
            "[SDLC Factory] Design phase complete. Artifacts saved to design_artifacts.yaml"
        )
    elif args.command == "develop":
        print(f"[SDLC Factory] Running autonomous development from {args.from_design}")
        if not args.from_design or not os.path.exists(args.from_design):
            print("[ERROR] Design artifact file required for development phase.")
            sys.exit(1)
        with open(args.from_design, "r") as f:
            design = yaml.safe_load(f)
        architecture = design["architecture"]
        frontend = orchestrator.frontend_agent.run(architecture, architecture["id"])
        backend = orchestrator.backend_agent.run(architecture, architecture["id"])
        database = orchestrator.database_agent.run(architecture, architecture["id"])
        integration = orchestrator.integration_agent.run([frontend, backend, database])
        critic = orchestrator.critic_agent.run(integration.id, integration.code)
        tests = orchestrator.testing_agent.run(
            integration.id, [r["id"] for r in architecture["requirements"]]
        )
        docs = orchestrator.documentation_agent.run(
            [frontend.id, backend.id, database.id, integration.id],
            [r["id"] for r in architecture["requirements"]],
        )
        # Save dev artifacts
        with open("dev_artifacts.yaml", "w") as f:
            yaml.safe_dump(
                {
                    "frontend": frontend.dict(),
                    "backend": backend.dict(),
                    "database": database.dict(),
                    "integration": integration.dict(),
                    "critic": critic.dict(),
                    "tests": tests.dict(),
                    "docs": docs.dict(),
                },
                f,
            )
        print(
            "[SDLC Factory] Development phase complete. Artifacts saved to dev_artifacts.yaml"
        )
    elif args.command == "run":
        print("[SDLC Factory] Running full SDLC pipeline in autonomous mode...")
        results = orchestrator.run_pipeline()
        # Convert Pydantic models to dictionaries for YAML serialization
        serializable_results = {}
        for key, value in results.items():
            if hasattr(value, "model_dump"):
                serializable_results[key] = value.model_dump()
            elif hasattr(value, "dict"):
                serializable_results[key] = value.dict()
            elif isinstance(value, list):
                serializable_results[key] = [
                    (
                        item.model_dump()
                        if hasattr(item, "model_dump")
                        else item.dict()
                        if hasattr(item, "dict")
                        else item
                    )
                    for item in value
                ]
            else:
                serializable_results[key] = value
        with open("full_pipeline_artifacts.yaml", "w") as f:
            yaml.safe_dump(serializable_results, f)
        print(
            "[SDLC Factory] Full pipeline complete. Artifacts saved to full_pipeline_artifacts.yaml"
        )
    elif args.command == "status":
        print("[SDLC Factory] Showing live status...")
        # TODO: Show agent and workflow status
    elif args.command == "agents":
        print("[SDLC Factory] Monitoring agents...")
        # TODO: Show agent activity
    elif args.command == "quality":
        print("[SDLC Factory] Showing quality dashboard...")
        # TODO: Show quality metrics
    elif args.command == "resources":
        print("[SDLC Factory] Monitoring resource usage...")
        # TODO: Show resource usage
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
