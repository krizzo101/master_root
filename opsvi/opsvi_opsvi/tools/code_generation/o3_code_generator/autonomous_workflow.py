"""
Autonomous Workflow Script

This script implements the complete autonomous workflow:
1. Analyze files using integrated_o3_analyzer.py
2. Generate enhancement requests from analysis
3. Process enhancement requests using self_improvement/run_self_improvement.py
4. Execute Phase 2 scripts (API docs, Docker, Security, Requirements)
5. Validate and apply improvements

This creates the full cycle: analyze → generate enhancement request → generate improved code → execute Phase 2 scripts → validate → apply
"""

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    from src.tools.code_generation.o3_code_generator.api_doc_generator import (
        ApiDocGenerator,
    )
    from src.tools.code_generation.o3_code_generator.docker_orchestrator import (
        DockerOrchestrator,
    )
    from src.tools.code_generation.o3_code_generator.requirements_analyzer import (
        RequirementsProcessor,
    )
    from src.tools.code_generation.o3_code_generator.schemas.api_doc_generator_input_schema import (
        ApiDocGeneratorInput,
    )
    from src.tools.code_generation.o3_code_generator.schemas.docker_orchestrator_input_schema import (
        DockerOrchestratorInput,
    )
    from src.tools.code_generation.o3_code_generator.schemas.requirements_analyzer_input_schema import (
        RequirementsAnalyzerInput,
    )
    from src.tools.code_generation.o3_code_generator.schemas.security_scanner_input_schema import (
        SecurityScannerInput,
    )
    from src.tools.code_generation.o3_code_generator.security_scanner import (
        SecurityScanner,
    )

    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False
else:
    pass
finally:
    pass
from src.tools.code_generation.o3_code_generator.auto_rules_generation.ast_patcher import (
    ASTPatcher,
)
from src.tools.code_generation.o3_code_generator.intelligent_o3_analyzer import (
    IntelligentFileAnalyzer,
)
from src.tools.code_generation.o3_code_generator.o3_code_generator import (
    O3CodeGenerator,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
if not PHASE2_AVAILABLE:
    logger.warning("Phase 2 scripts not available - some functionality will be limited")
else:
    pass


def run_analysis_phase(
    target_path: str, filter_impact: str | None = None, min_confidence: float = 0.0
) -> dict[str, list[dict[str, Any]]]:
    """
    Phase 1: Analyze files and generate improvement suggestions.
    Pre-process with ASTPatcher for all files (with backup).
    """
    logger.info(f"🔍 PHASE 1: Starting analysis of {target_path}")
    try:
        code_generator = O3CodeGenerator()
    except Exception as e:
        logger.error(f"Failed to initialize O3CodeGenerator: {e}")
        return {}
    else:
        pass
    finally:
        pass
    py_files = []
    if Path(target_path).is_file() and target_path.endswith(".py"):
        py_files = [Path(target_path)]
    else:
        for p in Path(target_path).rglob("*.py"):
            py_files.append(p)
        else:
            pass
    for py_file in py_files:
        backup_path = py_file.with_suffix(py_file.suffix + ".bak")
        shutil.copy2(py_file, backup_path)
        logger.info(f"Backup created: {backup_path}")
        try:
            ASTPatcher.patch_file(py_file)
            logger.info(f"Patched file: {py_file}")
        except Exception as e:
            logger.error(f"AST patching failed for {py_file}: {e}")
            shutil.copy2(backup_path, py_file)
            logger.info(f"Restored from backup: {py_file}")
        else:
            pass
        finally:
            pass
    else:
        pass
    analyzer = IntelligentFileAnalyzer(mode="analysis")
    improvement_summary = {}
    for py_file in py_files:
        try:
            result = analyzer.analyze_file(str(py_file))
            improvements = result.get("improvements", [])
            if improvements:
                improvement_summary[str(py_file)] = improvements
                logger.info(f"Found {len(improvements)} improvements for {py_file}")
            else:
                pass
        except Exception as e:
            logger.error(f"Analysis failed for {py_file}: {e}")
        else:
            pass
        finally:
            pass
    else:
        pass
    logger.info(
        f"✅ PHASE 1 COMPLETE: Analyzed {len(py_files)} files, found improvements in {len(improvement_summary)} files"
    )
    return improvement_summary


def generate_enhancement_requests(
    improvement_summary: dict[str, list[dict[str, Any]]],
) -> list[str]:
    """
    Phase 2: Convert analysis results to enhancement request JSON files.

    Args:
        improvement_summary: Analysis results from Phase 1

    Returns:
        List of generated enhancement request file paths
    """
    logger.info("📝 PHASE 2: Generating enhancement requests")
    self_improvement_dir = Path("self_improvement")
    self_improvement_dir.mkdir(exist_ok=True)
    generated_files = []
    for file_path, suggestions in improvement_summary.items():
        if not suggestions:
            continue
        else:
            pass
        try:
            with open(file_path, encoding="utf-8") as f:
                file_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read file content for {file_path}: {e}")
            continue
        else:
            pass
        finally:
            pass
        enhancement_request = {
            "prompt": f"""Fix the following {Path(file_path).name} file to comply with ALL project and universal rules.

REQUIREMENTS TO IMPLEMENT:
"""
            + "\n".join([f"- {s.get('message', '')}" for s in suggestions])
            + f"""

The generated code MUST pass all alignment checks. Every rule violation must be fixed.

File content:
```python
{file_content}
```""",
            "file_name": Path(file_path).name,
            "file_path": "generated_files",
            "language": "python",
            "file_content": file_content,
            "context_files": [
                "src/tools/code_generation/o3_code_generator/docs/project_rules.md",
                "src/tools/code_generation/o3_code_generator/docs/universal_rules.md",
            ],
            "requirements": [s.get("message", "") for s in suggestions],
        }
        base_name = Path(file_path).stem
        request_filename = f"{base_name}_enhancement_request.json"
        request_path = self_improvement_dir / request_filename
        with open(request_path, "w", encoding="utf-8") as f:
            json.dump(enhancement_request, f, indent=2)
        generated_files.append(str(request_path))
        logger.info(f"Generated enhancement request: {request_path}")
    else:
        pass
    logger.info(
        f"✅ PHASE 2 COMPLETE: Generated {len(generated_files)} enhancement requests"
    )
    return generated_files


def run_self_improvement_phase(enhancement_requests: list[str]) -> bool:
    """
    Phase 3: Process enhancement requests using the self-improvement orchestrator.

    Args:
        enhancement_requests: List of enhancement request file paths

    Returns:
        True if all requests were processed successfully
    """
    logger.info("🔄 PHASE 3: Processing enhancement requests")
    success_count = 0
    for request_file in enhancement_requests:
        logger.info(f"Processing enhancement request: {request_file}")
        try:
            from src.tools.code_generation.o3_code_generator.config.self_improvement.run_self_improvement import (
                SelfImprovementOrchestrator,
            )

            with open(request_file, encoding="utf-8") as f:
                enhancement_config = json.load(f)
            orchestrator = SelfImprovementOrchestrator()
            result = orchestrator.run_improvement_config(enhancement_config)
            if result.get("success", False):
                logger.info(f"✅ Successfully processed {request_file}")
                success_count += 1
            else:
                logger.error(
                    f"❌ Failed to process {request_file}: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            logger.error(f"❌ Error processing {request_file}: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback

            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        else:
            pass
        finally:
            pass
    else:
        pass
    logger.info(
        f"✅ PHASE 3 COMPLETE: Processed {success_count}/{len(enhancement_requests)} enhancement requests"
    )
    return success_count == len(enhancement_requests)


def run_phase2_scripts(target_path: str) -> bool:
    """
    Phase 4: Execute Phase 2 scripts for comprehensive project analysis and generation.

    Args:
        target_path: Path to the target project

    Returns:
        True if all Phase 2 scripts executed successfully
    """
    if not PHASE2_AVAILABLE:
        logger.warning("⚠️ Phase 2 scripts not available, skipping Phase 4")
        return True
    else:
        pass
    logger.info("🔧 PHASE 4: Executing Phase 2 scripts")
    # Use the O3 Code Generator project directory for all Phase 4 scripts
    o3_project_path = str(
        Path(__file__).parent
    )  # src/tools/code_generation/o3_code_generator/
    success_count = 0
    total_scripts = 4
    try:
        logger.info("📖 Generating API documentation...")
        api_generator = ApiDocGenerator()
        api_input = ApiDocGeneratorInput(
            project_path=o3_project_path,
            output_format="markdown",
            include_examples=True,
            include_schemas=True,
            generate_openapi=True,
            include_error_handling=True,
        )
        api_result = api_generator.generate_api_docs(api_input)
        if api_result:
            logger.info("✅ API documentation generated successfully")
            success_count += 1
        else:
            logger.error("❌ API documentation generation failed")
    except Exception as e:
        logger.error(f"❌ API documentation generation error: {e}")
    else:
        pass
    finally:
        pass
    try:
        logger.info("🐳 Generating Docker configuration...")
        docker_orchestrator = DockerOrchestrator()
        docker_input = DockerOrchestratorInput(
            project_name="O3CodeGenerator",
            project_path=o3_project_path,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        docker_result = docker_orchestrator.generate_docker_configuration(docker_input)
        if docker_result:
            logger.info("✅ Docker configuration generated successfully")
            success_count += 1
        else:
            logger.error("❌ Docker configuration generation failed")
    except Exception as e:
        logger.error(f"❌ Docker configuration generation error: {e}")
    else:
        pass
    finally:
        pass
    try:
        logger.info("🔒 Running security scan...")
        security_scanner = SecurityScanner()
        security_input = SecurityScannerInput(
            project_name="O3CodeGenerator",
            project_path=o3_project_path,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        security_result = security_scanner.scan_security(security_input)
        if security_result:
            logger.info("✅ Security scan completed successfully")
            success_count += 1
        else:
            logger.error("❌ Security scan failed")
    except Exception as e:
        logger.error(f"❌ Security scan error: {e}")
    else:
        pass
    finally:
        pass
    try:
        logger.info("📋 Analyzing requirements...")
        requirements_processor = RequirementsProcessor()
        requirements_input = RequirementsAnalyzerInput(
            project_name="O3CodeGenerator",
            project_path=o3_project_path,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        requirements_result = requirements_processor.analyze_requirements(
            requirements_input
        )
        if requirements_result:
            logger.info("✅ Requirements analysis completed successfully")
            success_count += 1
        else:
            logger.error("❌ Requirements analysis failed")
    except Exception as e:
        logger.error(f"❌ Requirements analysis error: {e}")
    else:
        pass
    finally:
        pass
    logger.info(
        f"✅ PHASE 4 COMPLETE: Executed {success_count}/{total_scripts} Phase 2 scripts successfully"
    )
    return success_count == total_scripts


def main() -> None:
    """
    Main function to execute the complete autonomous workflow.
    """
    parser = argparse.ArgumentParser(description="Autonomous Code Improvement Workflow")
    parser.add_argument(
        "path", type=str, help="Path to the file or directory to analyze and improve"
    )
    parser.add_argument(
        "--filter-impact",
        type=str,
        choices=["critical", "important", "nice-to-have"],
        help="Filter suggestions by the specified impact level",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Minimum confidence level to include a suggestion (0.0 - 1.0)",
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Run analysis only without triggering full workflow",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation phase (for testing)",
    )
    args = parser.parse_args()
    try:
        logger.info("🚀 Starting Autonomous Workflow")
        logger.info(f"Target: {args.path}")
        logger.info(f"Filter Impact: {args.filter_impact}")
        logger.info(f"Min Confidence: {args.min_confidence}")
        improvement_summary = run_analysis_phase(
            args.path, args.filter_impact, args.min_confidence
        )
        if args.analysis_only:
            logger.info("📋 Analysis-only mode: Stopping after Phase 1")
            return
        else:
            pass
        if not improvement_summary:
            logger.warning("⚠️ No improvements found. Workflow complete.")
            return
        else:
            pass
        enhancement_requests = generate_enhancement_requests(improvement_summary)
        if not enhancement_requests:
            logger.warning("⚠️ No enhancement requests generated. Workflow complete.")
            return
        else:
            pass
        success = run_self_improvement_phase(enhancement_requests)
        if not success:
            logger.error("❌ Phase 3 failed, stopping workflow")
            sys.exit(1)
        else:
            pass
        phase2_success = run_phase2_scripts(args.path)
        if phase2_success:
            logger.info("🎉 AUTONOMOUS WORKFLOW COMPLETE: All phases successful!")
        else:
            logger.error("❌ AUTONOMOUS WORKFLOW FAILED: Phase 4 had errors")
            sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Workflow failed with error: {e}")
        sys.exit(1)
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
