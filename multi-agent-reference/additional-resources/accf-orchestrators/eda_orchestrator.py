"""
EDA Orchestrator
===============

Main orchestration class for the Enhanced Documentation Agent.
Coordinates template generation, diagram creation, and quality assurance.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List

from ..core.event_bus import NATSEventBus
from ..integrations import (
    CodeReviewAdapter,
    ProjectIntelligenceAdapter,
    ResearchAdapter,
)
from ..utils.async_tools import run_in_task_group
from .request_schema import DocumentationRequest, DocumentationResult

logger = logging.getLogger(__name__)


class EDAOrchestrator:
    """
    Main orchestrator for Enhanced Documentation Agent.

    Coordinates parallel execution of template generation, diagram creation,
    and quality assurance using async task groups and NATS event bus.
    """

    def __init__(
        self, nats_servers: str = "nats://localhost:4222", enable_nats: bool = True
    ):
        self.enable_nats = enable_nats
        self.event_bus = NATSEventBus(servers=nats_servers) if enable_nats else None
        self._initialized = False

        # Initialize adapters (will be connected during initialize())
        self.project_intelligence = None
        self.research = None
        self.code_review = None

    async def initialize(self) -> None:
        """Initialize the orchestrator and connect to services."""
        if self._initialized:
            return

        if self.enable_nats and self.event_bus:
            try:
                await self.event_bus.connect()

                # Initialize adapters with event bus
                self.project_intelligence = ProjectIntelligenceAdapter(self.event_bus)
                self.research = ResearchAdapter(self.event_bus)
                self.code_review = CodeReviewAdapter(self.event_bus)

                logger.info("EDA Orchestrator initialized with NATS and adapters")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to NATS: {e}. Running without event bus."
                )
                self.enable_nats = False
                self.event_bus = None

        self._initialized = True
        logger.info("EDA Orchestrator initialized")

    def _extract_dependencies(self, setup_content: str) -> List[str]:
        """Extract dependencies from setup.py content."""
        dependencies = []
        lines = setup_content.split("\n")
        in_install_requires = False

        for line in lines:
            line = line.strip()
            if "install_requires" in line and "=" in line:
                in_install_requires = True
                # Extract from the same line if possible
                if "[" in line and "]" in line:
                    deps_str = line[line.find("[") : line.find("]") + 1]
                    # Simple parsing - could be improved
                    deps = [
                        dep.strip().strip("\"'") for dep in deps_str[1:-1].split(",")
                    ]
                    dependencies.extend(deps)
            elif in_install_requires and line.startswith('"') or line.startswith("'"):
                dep = line.strip().strip("\",'")
                if dep:
                    dependencies.append(dep)
            elif in_install_requires and line == "]":
                in_install_requires = False

        return dependencies

    async def _save_documentation(
        self, result: DocumentationResult, save_path: str
    ) -> None:
        """Save documentation to file."""
        try:
            import os
            from pathlib import Path

            # Ensure directory exists
            save_dir = Path(save_path).parent
            save_dir.mkdir(parents=True, exist_ok=True)

            # Write content to file
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(result.content)

            # Write diagrams to separate files if they exist
            if result.diagrams:
                diagrams_dir = save_dir / "diagrams"
                diagrams_dir.mkdir(exist_ok=True)

                for i, diagram in enumerate(result.diagrams):
                    diagram_path = diagrams_dir / f"diagram_{i+1}.mmd"
                    with open(diagram_path, "w", encoding="utf-8") as f:
                        f.write(diagram)

            logger.info(f"Documentation saved to {save_path}")

        except Exception as e:
            logger.error(f"Failed to save documentation to {save_path}: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the orchestrator and disconnect from services."""
        if self.event_bus:
            await self.event_bus.disconnect()

        self._initialized = False
        logger.info("EDA Orchestrator shutdown complete")

    async def generate_documentation(
        self, request: DocumentationRequest
    ) -> DocumentationResult:
        """
        Generate documentation based on the request.

        Args:
            request: Documentation generation request

        Returns:
            Documentation result with content, diagrams, and metadata
        """
        if not self._initialized:
            await self.initialize()

        start_time = time.time()

        try:
            # Phase 1: Parallel intelligence gathering
            logger.info(f"Starting documentation generation for {request.doc_type}")

            intelligence_data = await self._gather_intelligence(request)

            # Phase 2: Content and diagram generation
            content_data = await self._generate_content(request, intelligence_data)

            # Phase 3: Quality assurance
            final_result = await self._quality_assurance(request, content_data)

            # Calculate generation time
            generation_time = int((time.time() - start_time) * 1000)
            final_result.generation_time_ms = generation_time

            # Phase 4: Save to file if requested
            if request.save_path:
                await self._save_documentation(final_result, request.save_path)

            logger.info(f"Documentation generation completed in {generation_time}ms")
            return final_result

        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return DocumentationResult(
                content=f"# Error\n\nDocumentation generation failed: {str(e)}",
                generation_time_ms=int((time.time() - start_time) * 1000),
                errors=[str(e)],
            )

    async def _gather_intelligence(
        self, request: DocumentationRequest
    ) -> Dict[str, Any]:
        """
        Gather intelligence from various sources in parallel.

        Args:
            request: Documentation request

        Returns:
            Combined intelligence data
        """
        logger.info("Gathering project intelligence")

        # Create coroutines for parallel execution
        intelligence_coros = [
            self._get_project_intelligence(request),
            self._get_research_context(request),
            self._get_code_analysis(request),
        ]

        try:
            # Use gather with return_exceptions=True for error isolation
            results = await asyncio.gather(*intelligence_coros, return_exceptions=True)

            # Handle exceptions and provide fallbacks
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"Intelligence gathering task {i} failed: {result}")
                    processed_results.append({})  # Fallback empty dict
                else:
                    processed_results.append(result)

            return {
                "project_intelligence": processed_results[0],
                "research_context": processed_results[1],
                "code_analysis": processed_results[2],
            }
        except Exception as e:
            logger.error(f"Intelligence gathering failed: {e}")
            return {
                "project_intelligence": {},
                "research_context": {},
                "code_analysis": {},
            }

    async def _generate_content(
        self, request: DocumentationRequest, intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate documentation content using enhanced template system.

        Args:
            request: Documentation request
            intelligence: Project intelligence data

        Returns:
            Generated content data
        """
        try:
            # Enhanced content generation with MCP integration
            from ..templates.template_manager import TemplateManager
            from ..utils.mcp_llm_client import MCPLLMClient

            template_manager = TemplateManager()

            # Initialize MCP LLM client for enhanced content generation
            llm_client = MCPLLMClient()

            # Prepare context with enhanced intelligence
            context = {
                "doc_type": request.doc_type,
                "detail_level": request.detail_level,
                "target_audience": request.target_audience,
                "project_name": intelligence.get("project_name", "ACCF Project"),
                "project_context": intelligence,
                "language": intelligence.get("language", "python"),
                "framework": intelligence.get("framework"),
                "include_diagrams": request.include_diagrams,
                "include_code_examples": request.include_code_examples,
            }

            # Generate template skeleton
            skeleton = template_manager.render_skeleton(request.doc_type, context)

            # Fill with LLM-enhanced content
            content = template_manager.fill_narrative_sections(
                skeleton, context, llm_client
            )

            # Generate diagrams if requested
            diagrams = []
            if request.include_diagrams:
                from ..diagrams.diagram_generator import DiagramGenerator

                diagram_gen = DiagramGenerator()
                diagrams = await diagram_gen.generate(
                    project_context=intelligence, style="auto", density="moderate"
                )

            return {
                "content": content,
                "diagrams": diagrams,
                "context": context,
                "template_used": f"{request.doc_type}.md.j2",
            }

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return {
                "content": f"Error generating content: {e}",
                "diagrams": [],
                "context": {},
                "template_used": "fallback",
            }

    async def _quality_assurance(
        self, request: DocumentationRequest, content_data: Dict[str, Any]
    ) -> DocumentationResult:
        """
        Perform quality assurance on generated content.

        Args:
            request: Documentation request
            content_data: Generated content and diagrams

        Returns:
            Final documentation result
        """
        logger.info("Performing quality assurance")

        # For now, implement basic QA
        # TODO: Implement 3-gate QA pipeline in Phase 5

        try:
            # Basic validation
            content = content_data.get("content", "")
            diagrams = content_data.get("diagrams", [])

            # Simple quality score based on content length and diagram presence
            quality_score = min(1.0, len(content) / 1000.0)  # Basic scoring
            if diagrams and request.include_diagrams:
                quality_score += 0.2

            quality_score = min(1.0, quality_score)

            return DocumentationResult(
                content=content,
                diagrams=diagrams,
                quality_score=quality_score,
                metadata={
                    "doc_type": request.doc_type,
                    "detail_level": request.detail_level,
                    "diagram_count": len(diagrams),
                },
            )

        except Exception as e:
            logger.error(f"Quality assurance failed: {e}")
            return DocumentationResult(
                content=content_data.get("content", ""),
                diagrams=content_data.get("diagrams", []),
                quality_score=0.0,
                errors=[f"QA failed: {str(e)}"],
            )

    # Intelligence gathering methods

    async def _get_project_intelligence(
        self, request: DocumentationRequest
    ) -> Dict[str, Any]:
        """Get project intelligence data."""
        try:
            import glob
            import os
            from pathlib import Path

            # Get repository path from attached files or default to current directory
            repo_path = "."
            if request.attach_files:
                # Use directory of first attached file as repository path
                repo_path = os.path.dirname(request.attach_files[0]) or "."

            # Analyze the actual project structure
            project_path = Path(repo_path).resolve()

            # Get Python files in the project
            python_files = []
            for pattern in [
                "**/*.py",
                "**/*.md",
                "**/*.txt",
                "**/*.json",
                "**/*.yaml",
                "**/*.yml",
            ]:
                python_files.extend(
                    glob.glob(str(project_path / pattern), recursive=True)
                )

            # Read key files for analysis
            project_structure = {}
            dependencies = []
            entry_points = []

            # Analyze setup.py or requirements.txt for dependencies
            if (project_path / "setup.py").exists():
                with open(project_path / "setup.py", "r") as f:
                    setup_content = f.read()
                    dependencies = self._extract_dependencies(setup_content)
            elif (project_path / "requirements.txt").exists():
                with open(project_path / "requirements.txt", "r") as f:
                    requirements_content = f.read()
                    dependencies = [
                        line.strip()
                        for line in requirements_content.split("\n")
                        if line.strip() and not line.startswith("#")
                    ]

            # Find entry points (main files, __main__.py, etc.)
            for file_path in python_files:
                if any(
                    name in file_path
                    for name in ["__main__.py", "main.py", "app.py", "cli.py"]
                ):
                    entry_points.append(file_path)

            # Analyze project structure
            for file_path in python_files[:20]:  # Limit to first 20 files
                rel_path = os.path.relpath(file_path, project_path)
                project_structure[rel_path] = {
                    "type": "file",
                    "size": os.path.getsize(file_path),
                    "extension": Path(file_path).suffix,
                }

            return {
                "success": True,
                "project_structure": project_structure,
                "dependencies": dependencies,
                "entry_points": entry_points,
                "statistics": {
                    "total_files": len(python_files),
                    "python_files": len([f for f in python_files if f.endswith(".py")]),
                    "project_size": sum(
                        os.path.getsize(f) for f in python_files if os.path.exists(f)
                    ),
                },
                "project_path": str(project_path),
            }

        except Exception as e:
            logger.warning(f"Project intelligence failed: {e}")
            # Fallback to mock data
            return {
                "success": False,
                "project_structure": {},
                "dependencies": [],
                "entry_points": [],
                "statistics": {},
            }

    async def _get_research_context(
        self, request: DocumentationRequest
    ) -> Dict[str, Any]:
        """Get research context from research agent."""
        if self.research:
            try:
                # Research documentation standards for the doc type
                standards_result = await self.research.get_documentation_standards(
                    doc_type=request.doc_type, audience=request.target_audience
                )

                # If we have project context, research relevant topics
                topic_result = {}
                if request.attach_files:
                    # Infer topic from doc type and attached files
                    topic = f"{request.doc_type} documentation best practices"
                    topic_result = await self.research.research_topic(
                        topic=topic,
                        depth=request.detail_level,
                        include_code_examples=request.include_code_examples,
                        max_results=5,
                    )

                return {
                    "success": True,
                    "standards": standards_result,
                    "topic_research": topic_result,
                    "best_practices": standards_result.get("standards", {}).get(
                        "best_practices", []
                    ),
                    "latest_standards": standards_result.get("standards", {}).get(
                        "guidelines", []
                    ),
                }

            except Exception as e:
                logger.warning(f"Research context failed: {e}")

        # Fallback to mock data
        await asyncio.sleep(0.1)  # Simulate async work
        return {"success": False, "best_practices": [], "latest_standards": []}

    async def _get_code_analysis(self, request: DocumentationRequest) -> Dict[str, Any]:
        """Get code analysis from code review agent."""
        if self.code_review:
            try:
                # Get repository path from attached files or default to current directory
                repo_path = "."
                if request.attach_files:
                    import os

                    repo_path = os.path.dirname(request.attach_files[0]) or "."

                # Perform code quality analysis
                quality_result = await self.code_review.analyze_code_quality(
                    repository_path=repo_path,
                    files=request.attach_files if request.attach_files else None,
                    include_suggestions=True,
                    severity_threshold="info",
                    max_findings_per_file=10,  # Limit for documentation purposes
                )

                # Get architecture insights if comprehensive detail level
                architecture_result = {}
                if request.detail_level in ["comprehensive", "exhaustive"]:
                    architecture_result = await self.code_review.review_architecture(
                        repository_path=repo_path,
                        include_patterns=True,
                        include_anti_patterns=True,
                    )

                return {
                    "success": True,
                    "quality_analysis": quality_result,
                    "architecture_analysis": architecture_result,
                    "code_quality": quality_result.get("quality_score", 0.0),
                    "complexity_score": quality_result.get("metrics", {}).get(
                        "complexity", 0.0
                    ),
                    "issues": quality_result.get("findings", []),
                }

            except Exception as e:
                logger.warning(f"Code analysis failed: {e}")

        # Fallback to mock data
        await asyncio.sleep(0.1)  # Simulate async work
        return {
            "success": False,
            "code_quality": 0.0,
            "complexity_score": 0.0,
            "issues": [],
        }

    # Content generation methods

    async def _generate_template_content(
        self, request: DocumentationRequest, intelligence: Dict[str, Any]
    ) -> str:
        """Generate template-based content."""
        # TODO: Implement template engine in Phase 2
        await asyncio.sleep(0.1)  # Simulate async work

        return f"""# {request.doc_type.title()} Documentation

## Overview
This is a {request.detail_level} level {request.doc_type} documentation.

## Project Structure
{intelligence.get('project_intelligence', {}).get('project_structure', 'Not available')}

## Dependencies
{', '.join(intelligence.get('project_intelligence', {}).get('dependencies', []))}

## Code Quality
Quality Score: {intelligence.get('code_analysis', {}).get('complexity_score', 'N/A')}

## Best Practices
{', '.join(intelligence.get('research_context', {}).get('best_practices', []))}

---
Generated by Enhanced Documentation Agent (EDA)
"""

    async def _generate_diagrams(
        self, request: DocumentationRequest, intelligence: Dict[str, Any]
    ) -> List[str]:
        """Generate Mermaid diagrams."""
        # TODO: Implement diagram generator in Phase 3
        await asyncio.sleep(0.1)  # Simulate async work

        if request.diagram_style == "auto" or request.diagram_style == "flow":
            return [
                """graph TD
    A[Start] --> B[Process]
    B --> C[End]
    C --> D[Output]"""
            ]

        return []

    async def _no_diagrams(self) -> List[str]:
        """Return empty diagrams list."""
        return []
