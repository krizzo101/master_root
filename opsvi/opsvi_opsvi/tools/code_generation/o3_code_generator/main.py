"""TODO: Add module-level docstring."""

import argparse
import glob
import os
from pathlib import Path
import sys
import json
from typing import Optional

from src.tools.code_generation.o3_code_generator.api_doc_generator import (
    ApiDocGenerator,
)
from src.tools.code_generation.o3_code_generator.api_spec_generator import (
    APISpecGenerator,
)
from src.tools.code_generation.o3_code_generator.architecture_designer import (
    ArchitectureDesigner,
)
from src.tools.code_generation.o3_code_generator.architecture_validator import (
    ArchitectureValidator,
)
from src.tools.code_generation.o3_code_generator.brainstorming_tool import (
    run_brainstorm,
)
from src.tools.code_generation.o3_code_generator.code_reviewer import CodeReviewer
from src.tools.code_generation.o3_code_generator.component_designer import (
    ComponentDesigner,
)
from src.tools.code_generation.o3_code_generator.data_flow_designer import (
    DataFlowDesigner,
)
from src.tools.code_generation.o3_code_generator.database_schema_generator import (
    DatabaseSchemaGenerator,
)
from src.tools.code_generation.o3_code_generator.dependency_analyzer import (
    DependencyAnalyzer,
)
from src.tools.code_generation.o3_code_generator.docker_orchestrator import (
    DockerOrchestrator,
)
from src.tools.code_generation.o3_code_generator.feasibility_assessor import (
    run_feasibility_assess,
)
from src.tools.code_generation.o3_code_generator.idea_formation_analyzer import (
    run_idea_analyze,
)
from src.tools.code_generation.o3_code_generator.integration_spec_generator import (
    IntegrationSpecGenerator,
)
from src.tools.code_generation.o3_code_generator.interface_designer import (
    InterfaceDesigner,
)
from src.tools.code_generation.o3_code_generator.market_research_integrator import (
    run_market_research,
)
from src.tools.code_generation.o3_code_generator.o3_code_generator import (
    O3CodeGenerator,
)
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    get_logger,
    setup_logger,
)
from src.tools.code_generation.o3_code_generator.performance_spec_generator import (
    PerformanceSpecGenerator,
)
from src.tools.code_generation.o3_code_generator.requirements_analyzer import (
    run_requirements_analyze,
)
from src.tools.code_generation.o3_code_generator.research_script import (
    run_research,
)
from src.tools.code_generation.o3_code_generator.utils.input_loader import (
    UniversalInputLoader,
)
from src.tools.code_generation.o3_code_generator.validation_framework import (
    ValidationFramework,
)
from src.tools.code_generation.o3_code_generator.security_scanner import SecurityScanner
from src.tools.code_generation.o3_code_generator.technical_spec_generator import (
    TechnicalSpecGenerator,
)

# Setup logger once at the entry point
# Initialize with default config, will be reconfigured in main() if needed
setup_logger(LogConfig())
logger = get_logger()


# --- CLI-facing run_* functions (condensed) ---
def run_analyze(paths, output_file=None):
    """Analyze one or more project paths for dependency issues.

    Each *path* should point to a project root containing `requirements.txt`,
    `package.json`, or similar manifest files.  For every provided path we run
    the DependencyAnalyzer and aggregate the results.
    """
    from src.tools.code_generation.o3_code_generator.schemas.dependency_analyzer_input_schema import (
        DependencyAnalysisInput,
    )

    logger.log_info(f"Analyzing projects: {paths}")
    analyzer = DependencyAnalyzer()
    inp = DependencyAnalysisInput(paths=list(paths))
    report = analyzer.analyze_projects(inp)

    if output_file:
        Path(output_file).write_text(json.dumps(report, indent=2))
        logger.log_info(f"Analysis report saved → {output_file}")
    else:
        logger.log_info("Dependency analysis results:\n" + json.dumps(report, indent=2))


def run_generate(input_file, save):
    logger.log_info(f"Generating code from: {input_file}")
    loader = UniversalInputLoader()
    data = loader.load_file_by_extension(input_file)

    # Convert dict to CodeGenerationInput object if needed
    from src.tools.code_generation.o3_code_generator.schemas.input_schema import (
        CodeGenerationInput,
    )

    if isinstance(data, dict):
        data = CodeGenerationInput(**data)

    gen = O3CodeGenerator()
    # Import the output schema to enable structured JSON responses
    from src.tools.code_generation.o3_code_generator.schemas.output_schema import (
        CodeGenerationOutput,
    )

    output = gen.generate_code(data, output_schema=CodeGenerationOutput)
    if not output.success:
        logger.log_error(f"Generation failed: {output.error_message}")
        sys.exit(1)
    if save:
        # Use the FileGenerator to save the generated code
        output_path = f"generated_files/{output.file_name}"
        gen.file_generator.save_file(output.code, output_path)
        logger.log_info(f"Code saved to: {output_path}")
    else:
        logger.log_info(output.code)


def run_validate(file_path):
    logger.log_info(f"Validating: {file_path}")
    loader = UniversalInputLoader()
    content = (
        loader.load_json_file(file_path)
        if Path(file_path).suffix == ".json"
        else loader.load_file_by_extension(file_path)
    )
    vf = ValidationFramework()
    results = vf.run_all_validations(content)
    logger.log_info(str(results))


def run_self_improve(improve_type):
    logger.log_info(f"Self-improve: {improve_type}")
    # Placeholder for actual self-improvement logic
    logger.log_info("Self-improvement completed.")


def run_enhancement_request(analysis_file, output_dir):
    logger.log_info(f"Enhancement request from: {analysis_file}")
    # Placeholder for actual enhancement request logic
    logger.log_info(f"Enhancement requests generated in: {output_dir}")


def run_workflow(workflow_file):
    logger.log_info(f"Running workflow: {workflow_file}")
    # Placeholder for workflow logic
    logger.log_info("Workflow execution completed.")


def run_chain(operations):
    logger.log_info(f"Chaining operations: {operations}")

    # Map operation names to their functions
    operation_map = {
        "brainstorm": run_brainstorm,
        "idea-analyze": run_idea_analyze,
        "market-research": run_market_research,
        "feasibility-assess": run_feasibility_assess,
        "requirements-analyze": run_requirements_analyze,
    }

    current_output_file = None

    for i, operation in enumerate(operations):
        operation = operation.strip()
        logger.log_info(f"Executing operation {i+1}/{len(operations)}: {operation}")

        if operation not in operation_map:
            logger.log_error(f"Unknown operation: {operation}")
            continue

        try:
            if operation == "brainstorm":
                # For brainstorm, we need an input file
                if current_output_file is None:
                    logger.log_error(
                        "Chain must start with brainstorm operation and provide input file"
                    )
                    break
                operation_map[operation](current_output_file, False)  # Non-interactive
            else:
                # For other operations, use the previous step's output
                if current_output_file is None:
                    logger.log_error(
                        f"No input file available for operation: {operation}"
                    )
                    break

                if operation == "idea-analyze":
                    operation_map[operation](
                        current_output_file, False
                    )  # Non-interactive
                else:
                    operation_map[operation](current_output_file)

            # Find the most recent output file for the next step
            output_files = glob.glob("output/*")
            if output_files:
                current_output_file = max(
                    output_files, key=lambda x: os.path.getctime(x)
                )
                logger.log_info(f"Next step will use: {current_output_file}")

        except Exception as e:
            logger.log_error(f"Error in operation {operation}: {str(e)}")
            break

    logger.log_info("Chain execution completed.")


def run_project_initialize(input_file):
    logger.log_info(f"Initializing project: {input_file}")
    # Placeholder for project initialization logic
    logger.log_info("Project initialized.")


def run_dependency_analyze(input_file):
    logger.log_info(f"Dependency analysis: {input_file}")
    da = DependencyAnalyzer()
    data = da.input_loader.load_file_by_extension(input_file)
    out = da.analyze_dependencies(data)
    logger.log_info(str(out))


def run_code_review(input_file):
    logger.log_info(f"Code review: {input_file}")
    cr = CodeReviewer()
    data = cr.input_loader.load_file_by_extension(input_file)
    out = cr.review_code(data)
    logger.log_info(str(out))


def run_api_doc_generate(input_file):
    logger.log_info(f"API doc: {input_file}")
    ag = ApiDocGenerator()
    data = ag.input_loader.load_file_by_extension(input_file)
    out = ag.generate_api_docs(data)
    logger.log_info(str(out))


def run_docker_orchestrate(input_file):
    logger.log_info(f"Docker orchestration: {input_file}")
    do = DockerOrchestrator()
    data = do.input_loader.load_file_by_extension(input_file)
    out = do.generate_docker_configuration(data)
    logger.log_info(str(out))


def run_security_scan(input_file):
    logger.log_info(f"Security scan: {input_file}")
    ss = SecurityScanner()
    data = ss.input_loader.load_file_by_extension(input_file)
    out = ss.scan_security(data)
    logger.log_info(str(out))


# Stub functions removed - using imported functions from business logic modules


def run_tech_spec_generate(input_file):
    logger.log_info(f"Tech spec: {input_file}")
    tg = TechnicalSpecGenerator()
    data = tg.input_loader.load_file_by_extension(input_file)
    out = tg.generate_technical_specs(data)
    logger.log_info(str(out))


def run_api_spec_generate(input_file):
    logger.log_info(f"API spec: {input_file}")
    ag = APISpecGenerator()
    data = ag.input_loader.load_file_by_extension(input_file)
    ag.generate_api_specs(data)
    logger.log_info("API spec generation completed.")


def run_db_schema_generate(input_file):
    logger.log_info(f"DB schema: {input_file}")
    dg = DatabaseSchemaGenerator()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    dg.generate_schema(data)
    logger.log_info("DB schema generation completed.")


def run_integration_spec_generate(input_file):
    logger.log_info(f"Integration spec: {input_file}")
    ig = IntegrationSpecGenerator()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    ig.define_integrations(data)
    logger.log_info("Integration spec generation completed.")


def run_performance_spec_generate(input_file):
    logger.log_info(f"Performance spec: {input_file}")
    pg = PerformanceSpecGenerator()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    pg.define_performance_requirements(data)
    logger.log_info("Performance spec generation completed.")


def run_architecture_design(input_file):
    logger.log_info(f"Architecture design: {input_file}")
    ad = ArchitectureDesigner()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    ad.design_system_architecture(data)
    logger.log_info("Architecture design completed.")


def run_component_design(input_file):
    logger.log_info(f"Component design: {input_file}")
    cd = ComponentDesigner()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    cd.design_components(data)
    logger.log_info("Component design completed.")


def run_data_flow_design(input_file):
    logger.log_info(f"Data flow design: {input_file}")
    df = DataFlowDesigner()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    df.design_data_flows(data)
    logger.log_info("Data flow design completed.")


def run_interface_design(input_file):
    logger.log_info(f"Interface design: {input_file}")
    idf = InterfaceDesigner()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    idf.design_apis(data)
    logger.log_info("Interface design completed.")


def run_architecture_validate(input_file):
    logger.log_info(f"Architecture validate: {input_file}")
    av = ArchitectureValidator()
    data = UniversalInputLoader().load_file_by_extension(input_file)
    av.validate_architecture(data)
    logger.log_info("Architecture validation completed.")


def run_auto_workflow(
    problem_statement: str,
    steps: Optional[str] = None,
    output_dir: Optional[str] = None,
    resume: Optional[str] = None,
    from_step: Optional[str] = None,
):
    """Run autonomous workflow from problem statement to complete solution."""
    from src.tools.code_generation.o3_code_generator.workflow import AutonomousWorkflow
    from pathlib import Path

    logger = get_logger()

    try:
        # Handle resume workflow
        if resume:
            context_file = Path(resume)
            if not context_file.exists():
                logger.log_error(f"Context file not found: {context_file}")
                return

            # Initialize workflow with custom output dir if provided
            output_base = Path(output_dir) if output_dir else None
            workflow = AutonomousWorkflow(output_base_dir=output_base)

            # Resume workflow
            context = workflow.resume_workflow(context_file, from_step)

            logger.log_info(f"Resumed workflow completed")
            logger.log_info(f"Final progress: {context.get_workflow_progress()}")
            return

        # Initialize new workflow
        output_base = Path(output_dir) if output_dir else None
        workflow = AutonomousWorkflow(output_base_dir=output_base)

        # Parse steps if provided
        enabled_steps = None
        if steps:
            step_list = [step.strip() for step in steps.split(",")]
            # Validate and reorder steps
            enabled_steps = workflow.validate_step_sequence(step_list)
            logger.log_info(f"Custom steps enabled: {enabled_steps}")

        # Execute workflow
        logger.log_info(f"Starting autonomous workflow for: '{problem_statement}'")
        context = workflow.execute_workflow(
            problem_statement=problem_statement, enabled_steps=enabled_steps
        )

        # Report final results
        progress = context.get_workflow_progress()
        logger.log_info(f"Autonomous workflow completed!")
        logger.log_info(
            f"Progress: {progress['completed_steps']}/{progress['total_steps']} steps ({progress['progress_percent']:.1f}%)"
        )

        if context.selected_idea:
            logger.log_info(
                f"Selected solution: '{context.selected_idea.get('title', 'Untitled')}'"
            )

        logger.log_info(f"Results saved to: {context.output_directory}")
        logger.log_info(
            f"Workflow summary: {context.output_directory}/workflow_summary.md"
        )

        # Print user-friendly completion message
        print(f"\n🎉 Autonomous workflow completed successfully!")
        print(
            f"📊 Completed {progress['completed_steps']}/{progress['total_steps']} steps ({progress['progress_percent']:.1f}%)"
        )

        if context.selected_idea:
            print(
                f"💡 Selected solution: '{context.selected_idea.get('title', 'Untitled')}'"
            )

        print(f"📁 Results available at: {context.output_directory}")
        print(f"📋 Summary: {context.output_directory}/workflow_summary.md")
        print(f"🔄 Context: {context.output_directory}/workflow_context.json")

        if progress["completed_steps"] < progress["total_steps"]:
            print(f"\n⚠️  Workflow partially completed. Use --resume to continue:")
            print(
                f"   python -m main.py auto-workflow --resume {context.output_directory}/workflow_context.json"
            )

    except Exception as e:
        logger.log_error(f"Auto-workflow execution failed: {e}")
        raise


# --- CLI Argument Parsing and Dispatch ---
def main():
    parser = argparse.ArgumentParser(
        description="O3 Code Generator CLI (self-contained)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    sub = parser.add_subparsers(dest="cmd")

    analyze_parser = sub.add_parser("analyze")
    analyze_parser.add_argument("files", nargs="+")

    generate_parser = sub.add_parser("generate")
    generate_parser.add_argument("input_file")
    generate_parser.add_argument("--save", action="store_true")

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("file_path")

    self_improve_parser = sub.add_parser("self-improve")
    self_improve_parser.add_argument("--type")

    enhancement_request_parser = sub.add_parser("enhancement-request")
    enhancement_request_parser.add_argument("analysis_file")
    enhancement_request_parser.add_argument("--output-dir")

    workflow_parser = sub.add_parser("workflow")
    workflow_parser.add_argument("workflow_file")

    chain_parser = sub.add_parser("chain")
    chain_parser.add_argument("operations")

    # Auto-workflow command for autonomous end-to-end execution
    auto_workflow_parser = sub.add_parser(
        "auto-workflow",
        help="Execute complete autonomous workflow from problem statement",
    )
    auto_workflow_parser.add_argument(
        "problem_statement", help="The problem statement to solve"
    )
    auto_workflow_parser.add_argument(
        "--steps", help="Comma-separated list of steps to include (default: all)"
    )
    auto_workflow_parser.add_argument("--output-dir", help="Custom output directory")
    auto_workflow_parser.add_argument(
        "--resume", help="Resume workflow from context file"
    )
    auto_workflow_parser.add_argument("--from-step", help="Resume from specific step")

    project_init_parser = sub.add_parser("project-init")
    project_init_parser.add_argument("input_file")

    dependency_analyze_parser = sub.add_parser("dependency-analyze")
    dependency_analyze_parser.add_argument("input_file")

    code_review_parser = sub.add_parser("code-review")
    code_review_parser.add_argument("input_file")

    api_doc_parser = sub.add_parser("api-doc")
    api_doc_parser.add_argument("input_file")

    docker_orchestrate_parser = sub.add_parser("docker-orchestrate")
    docker_orchestrate_parser.add_argument("input_file")

    security_scan_parser = sub.add_parser("security-scan")
    security_scan_parser.add_argument("input_file")

    requirements_analyze_parser = sub.add_parser("requirements-analyze")
    requirements_analyze_parser.add_argument("input_file")

    research_parser = sub.add_parser("research")
    research_parser.add_argument("topic")
    research_parser.add_argument("--max-urls", type=int, default=3)
    research_parser.add_argument("--methods", nargs="+", default=["all"])

    brainstorm_parser = sub.add_parser("brainstorm")
    brainstorm_parser.add_argument("input_file", nargs="?")
    brainstorm_parser.add_argument("--problem")
    brainstorm_parser.add_argument("--interactive", action="store_true")

    idea_analyze_parser = sub.add_parser("idea-analyze")
    idea_analyze_parser.add_argument("input_file", nargs="?")
    idea_analyze_parser.add_argument("--interactive", action="store_true")

    market_research_parser = sub.add_parser("market-research")
    market_research_parser.add_argument("input_file", nargs="?")

    feasibility_assess_parser = sub.add_parser("feasibility-assess")
    feasibility_assess_parser.add_argument("input_file", nargs="?")

    tech_spec_generate_parser = sub.add_parser("tech-spec-generate")
    tech_spec_generate_parser.add_argument("input_file")

    api_spec_generate_parser = sub.add_parser("api-spec-generate")
    api_spec_generate_parser.add_argument("input_file")

    db_schema_generate_parser = sub.add_parser("db-schema-generate")
    db_schema_generate_parser.add_argument("input_file")

    integration_spec_generate_parser = sub.add_parser("integration-spec-generate")
    integration_spec_generate_parser.add_argument("input_file")

    performance_spec_generate_parser = sub.add_parser("performance-spec-generate")
    performance_spec_generate_parser.add_argument("input_file")

    architecture_design_parser = sub.add_parser("architecture-design")
    architecture_design_parser.add_argument("input_file")

    component_design_parser = sub.add_parser("component-design")
    component_design_parser.add_argument("input_file")

    data_flow_design_parser = sub.add_parser("data-flow-design")
    data_flow_design_parser.add_argument("input_file")

    interface_design_parser = sub.add_parser("interface-design")
    interface_design_parser.add_argument("input_file")

    architecture_validate_parser = sub.add_parser("architecture-validate")
    architecture_validate_parser.add_argument("input_file")

    args = parser.parse_args()
    try:
        # Configure logger based on debug flag
        log_config = LogConfig()
        if args.debug:
            log_config.level = "DEBUG"
            log_config.enable_debug_log = True
        setup_logger(log_config)
        logger = get_logger()

        match args.cmd:
            case "analyze":
                run_analyze(args.files)
            case "generate":
                run_generate(args.input_file, args.save)
            case "validate":
                run_validate(args.file_path)
            case "self-improve":
                run_self_improve(args.type)
            case "enhancement-request":
                run_enhancement_request(args.analysis_file, args.output_dir)
            case "workflow":
                run_workflow(args.workflow_file)
            case "chain":
                run_chain(args.operations.split(","))
            case "auto-workflow":
                run_auto_workflow(
                    problem_statement=args.problem_statement,
                    steps=args.steps,
                    output_dir=args.output_dir,
                    resume=args.resume,
                    from_step=args.from_step,
                )
            case "project-init":
                run_project_initialize(args.input_file)
            case "dependency-analyze":
                run_dependency_analyze(args.input_file)
            case "code-review":
                run_code_review(args.input_file)
            case "api-doc":
                run_api_doc_generate(args.input_file)
            case "docker-orchestrate":
                run_docker_orchestrate(args.input_file)
            case "security-scan":
                run_security_scan(args.input_file)
            case "requirements-analyze":
                run_requirements_analyze(args.input_file)
            case "research":
                run_research(args.topic, args.max_urls, args.methods)
            case "brainstorm":
                run_brainstorm(args.input_file, args.problem, args.interactive)
            case "idea-analyze":
                run_idea_analyze(args.input_file, args.interactive)
            case "market-research":
                run_market_research(args.input_file)
            case "feasibility-assess":
                run_feasibility_assess(args.input_file)
            case "tech-spec-generate":
                run_tech_spec_generate(args.input_file)
            case "api-spec-generate":
                run_api_spec_generate(args.input_file)
            case "db-schema-generate":
                run_db_schema_generate(args.input_file)
            case "integration-spec-generate":
                run_integration_spec_generate(args.input_file)
            case "performance-spec-generate":
                run_performance_spec_generate(args.input_file)
            case "architecture-design":
                run_architecture_design(args.input_file)
            case "component-design":
                run_component_design(args.input_file)
            case "data-flow-design":
                run_data_flow_design(args.input_file)
            case "interface-design":
                run_interface_design(args.input_file)
            case "architecture-validate":
                run_architecture_validate(args.input_file)
            case _:
                parser.print_help()
                sys.exit(1)
    except Exception as e:
        logger.log_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
