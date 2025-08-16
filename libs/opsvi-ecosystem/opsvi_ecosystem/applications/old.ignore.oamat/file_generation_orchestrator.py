"""
OAMAT File Generation Orchestrator
Advanced parallel file generation with dependency management and context consolidation
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger("OAMAT.FileOrchestrator")


@dataclass
class FileSpec:
    """Specification for a file to be generated"""

    name: str
    path: str
    content_type: str  # "code", "documentation", "config", "data"
    dependencies: list[str] = field(default_factory=list)  # Other files this depends on
    estimated_complexity: int = 5  # 1-10 scale
    parallel_safe: bool = True
    template_type: str | None = None
    context_requirements: list[str] = field(
        default_factory=list
    )  # What context this file needs

    # Generation metadata
    agent_role: str = "coder"
    tools_needed: list[str] = field(default_factory=lambda: ["write_file"])
    success_criteria: list[str] = field(default_factory=list)


@dataclass
class FileGenerationResult:
    """Result of generating a single file"""

    file_spec: FileSpec
    success: bool
    content: str | None = None
    file_path: str | None = None
    generation_time: float | None = None
    error: str | None = None
    context_used: dict[str, Any] = field(default_factory=dict)
    generated_artifacts: list[str] = field(default_factory=list)


@dataclass
class FileGenerationBatch:
    """A batch of files that can be generated in parallel"""

    level: int
    files: list[FileSpec]
    dependencies_met: set[str] = field(default_factory=set)


class FileDependencyAnalyzer:
    """Analyzes file dependencies to create optimal parallel execution plan"""

    def __init__(self):
        self.logger = logging.getLogger("OAMAT.FileDependency")

        # Common dependency patterns
        self.dependency_patterns = {
            "code": {
                "models.py": [],  # Usually no dependencies
                "schema.sql": [],  # Database schema
                "migrations/": [
                    "models.py",
                    "schema.sql",
                ],  # Depends on models and schema
                "routes/": ["models.py"],  # API routes depend on models
                "controllers/": [
                    "models.py",
                    "routes/",
                ],  # Controllers depend on models and routes
                "services/": ["models.py"],  # Services depend on models
                "utils/": [],  # Utilities usually independent
                "config/": [],  # Configuration usually independent
                "tests/": [
                    "models.py",
                    "routes/",
                    "controllers/",
                    "services/",
                ],  # Tests depend on everything
                "app.py": [
                    "models.py",
                    "routes/",
                    "controllers/",
                    "config/",
                ],  # Main app depends on core components
            },
            "documentation": {
                "README.md": [],  # Usually independent
                "API.md": ["routes/", "controllers/"],  # API docs depend on API code
                "architecture.md": [
                    "models.py",
                    "services/",
                ],  # Architecture docs depend on core structure
                "deployment.md": [
                    "config/",
                    "app.py",
                ],  # Deployment docs depend on config and main app
            },
        }

    def analyze_dependencies(self, files: list[FileSpec]) -> list[FileGenerationBatch]:
        """Analyze file dependencies and create execution batches"""
        self.logger.info(f"Analyzing dependencies for {len(files)} files")

        # Build dependency graph
        dependency_graph = {}
        file_map = {f.name: f for f in files}

        for file_spec in files:
            # Start with explicit dependencies
            deps = set(file_spec.dependencies)

            # Add pattern-based dependencies
            pattern_deps = self._get_pattern_dependencies(file_spec)
            deps.update(pattern_deps)

            # Filter to only include files that are actually being generated
            deps = {
                dep
                for dep in deps
                if dep in file_map or any(dep in f.name or dep in f.path for f in files)
            }

            dependency_graph[file_spec.name] = deps

        # Create execution levels using topological sort
        batches = self._create_execution_batches(files, dependency_graph)

        self.logger.info(f"Created {len(batches)} execution batches")
        for i, batch in enumerate(batches):
            self.logger.debug(
                f"Batch {i}: {[f.name for f in batch.files]} (level {batch.level})"
            )

        return batches

    def _get_pattern_dependencies(self, file_spec: FileSpec) -> set[str]:
        """Get dependencies based on common patterns"""
        deps = set()

        content_type = file_spec.content_type
        if content_type not in self.dependency_patterns:
            return deps

        patterns = self.dependency_patterns[content_type]

        # Check if this file matches any known patterns
        for pattern, pattern_deps in patterns.items():
            if pattern in file_spec.name or pattern in file_spec.path:
                deps.update(pattern_deps)
                break

        # Special logic for certain file types
        if file_spec.name.endswith(".py"):
            # Python files might import from models, utils
            if "test" not in file_spec.name.lower():
                if any("model" in f for f in file_spec.context_requirements):
                    deps.add("models.py")

        return deps

    def _create_execution_batches(
        self, files: list[FileSpec], dependency_graph: dict[str, set[str]]
    ) -> list[FileGenerationBatch]:
        """Create execution batches using topological sort"""
        batches = []
        file_map = {f.name: f for f in files}
        completed = set()
        level = 0

        while len(completed) < len(files):
            # Find files ready for execution (all dependencies completed)
            ready_files = []

            for file_spec in files:
                if file_spec.name in completed:
                    continue

                file_deps = dependency_graph.get(file_spec.name, set())
                # Check if all dependencies are completed or don't exist in our file set
                deps_met = all(
                    dep in completed or dep not in file_map for dep in file_deps
                )

                if deps_met:
                    ready_files.append(file_spec)

            if not ready_files:
                # Circular dependency or other issue - add remaining files
                remaining = [f for f in files if f.name not in completed]
                if remaining:
                    self.logger.warning(
                        f"Potential circular dependency, adding {len(remaining)} remaining files to final batch"
                    )
                    ready_files = remaining

            if ready_files:
                batch = FileGenerationBatch(
                    level=level, files=ready_files, dependencies_met=completed.copy()
                )
                batches.append(batch)

                # Mark these files as completed for next iteration
                for file_spec in ready_files:
                    completed.add(file_spec.name)

                level += 1

        return batches


class ContextConsolidator:
    """Manages context flow and consolidation across multiple levels"""

    def __init__(self):
        self.logger = logging.getLogger("OAMAT.ContextConsolidator")

    def prepare_file_context(
        self,
        file_spec: FileSpec,
        subtask_context: dict[str, Any],
        completed_files: dict[str, FileGenerationResult],
    ) -> dict[str, Any]:
        """Prepare context for a specific file generation"""

        file_context = {
            # Inherit all subtask context
            **subtask_context,
            # File-specific information
            "current_file": {
                "name": file_spec.name,
                "path": file_spec.path,
                "type": file_spec.content_type,
                "dependencies": file_spec.dependencies,
                "requirements": file_spec.context_requirements,
            },
            # Results from completed files that this file depends on
            "dependency_files": {},
            # File generation metadata
            "generation_metadata": {
                "agent_role": file_spec.agent_role,
                "tools_available": file_spec.tools_needed,
                "success_criteria": file_spec.success_criteria,
            },
        }

        # Add content from dependency files
        for dep_name in file_spec.dependencies:
            if dep_name in completed_files and completed_files[dep_name].success:
                dep_result = completed_files[dep_name]
                file_context["dependency_files"][dep_name] = {
                    "content": dep_result.content,
                    "path": dep_result.file_path,
                    "artifacts": dep_result.generated_artifacts,
                }

        self.logger.debug(
            f"Prepared context for {file_spec.name} with {len(file_context['dependency_files'])} dependency files"
        )
        return file_context

    def consolidate_file_results(
        self, results: list[FileGenerationResult], subtask_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Consolidate file generation results back into subtask context"""

        consolidated = {
            # Preserve original subtask context
            **subtask_context,
            # Add file generation summary
            "file_generation_summary": {
                "total_files": len(results),
                "successful_files": len([r for r in results if r.success]),
                "failed_files": len([r for r in results if not r.success]),
                "generation_time": sum(r.generation_time or 0 for r in results),
                "total_artifacts": sum(len(r.generated_artifacts) for r in results),
            },
            # Detailed file results
            "generated_files": {},
            "file_artifacts": [],
            "file_errors": [],
        }

        # Add detailed results for each file
        for result in results:
            file_info = {
                "success": result.success,
                "content_preview": result.content[:200] + "..."
                if result.content and len(result.content) > 200
                else result.content,
                "full_path": result.file_path,
                "generation_time": result.generation_time,
                "context_used": result.context_used,
                "artifacts": result.generated_artifacts,
            }

            consolidated["generated_files"][result.file_spec.name] = file_info
            consolidated["file_artifacts"].extend(result.generated_artifacts)

            if not result.success and result.error:
                consolidated["file_errors"].append(
                    {"file": result.file_spec.name, "error": result.error}
                )

        self.logger.info(
            f"Consolidated {len(results)} file results into subtask context"
        )
        return consolidated


class FileGenerationOrchestrator:
    """Orchestrates parallel file generation within subtasks"""

    def __init__(self, oamat_instance):
        self.oamat = oamat_instance
        self.logger = logging.getLogger("OAMAT.FileOrchestrator")
        self.dependency_analyzer = FileDependencyAnalyzer()
        self.context_consolidator = ContextConsolidator()

    async def generate_files_parallel(
        self, file_specs: list[FileSpec], subtask_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate multiple files in parallel with dependency management"""

        if not file_specs:
            return {"success": True, "files": [], "message": "No files to generate"}

        self.logger.info(
            f"🔧 FILE-PARALLEL: Starting generation of {len(file_specs)} files"
        )

        # Analyze dependencies and create execution batches
        execution_batches = self.dependency_analyzer.analyze_dependencies(file_specs)

        all_results = []
        completed_files = {}

        # Execute each batch in sequence, but files within batch in parallel
        for batch in execution_batches:
            self.logger.info(
                f"🔧 FILE-PARALLEL: Executing batch {batch.level} with {len(batch.files)} files"
            )

            # Generate all files in this batch in parallel
            batch_results = await self._execute_file_batch_parallel(
                batch.files, subtask_context, completed_files
            )

            # Update completed files tracking
            for result in batch_results:
                completed_files[result.file_spec.name] = result
                all_results.append(result)

            # Log batch completion
            successful_in_batch = len([r for r in batch_results if r.success])
            self.logger.info(
                f"🔧 FILE-PARALLEL: Batch {batch.level} completed - {successful_in_batch}/{len(batch_results)} files successful"
            )

        # Consolidate all results
        consolidated_context = self.context_consolidator.consolidate_file_results(
            all_results, subtask_context
        )

        # Add orchestration summary
        consolidated_context["file_parallel_execution"] = {
            "total_batches": len(execution_batches),
            "total_files": len(file_specs),
            "successful_files": len([r for r in all_results if r.success]),
            "failed_files": len([r for r in all_results if not r.success]),
            "execution_strategy": "dependency-aware parallel batches",
        }

        success_rate = (
            len([r for r in all_results if r.success]) / len(all_results)
            if all_results
            else 0
        )
        self.logger.info(
            f"🔧 FILE-PARALLEL: Completed all batches - {success_rate:.1%} success rate"
        )

        return {
            "success": success_rate
            > 0.5,  # Consider successful if >50% of files generated
            "results": all_results,
            "consolidated_context": consolidated_context,
        }

    async def _execute_file_batch_parallel(
        self,
        files: list[FileSpec],
        subtask_context: dict[str, Any],
        completed_files: dict[str, FileGenerationResult],
    ) -> list[FileGenerationResult]:
        """Execute a batch of files in parallel"""

        if len(files) == 1:
            # Single file - no need for parallelization
            return [
                await self._generate_single_file(
                    files[0], subtask_context, completed_files
                )
            ]

        # Create tasks for parallel execution
        tasks = []
        for file_spec in files:
            task = self._create_file_generation_task(
                file_spec, subtask_context, completed_files
            )
            tasks.append(task)

        # Execute all files concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Convert exception to failed result
                    failed_result = FileGenerationResult(
                        file_spec=files[i],
                        success=False,
                        error=str(result),
                        generation_time=0.0,
                    )
                    processed_results.append(failed_result)
                    self.logger.error(
                        f"❌ FILE-PARALLEL: {files[i].name} failed: {result}"
                    )
                else:
                    processed_results.append(result)
                    status = "✅" if result.success else "❌"
                    self.logger.debug(
                        f"{status} FILE-PARALLEL: {result.file_spec.name}"
                    )

            return processed_results

        except Exception as e:
            self.logger.error(f"❌ FILE-PARALLEL: Batch execution failed: {e}")
            # Return failed results for all files
            return [
                FileGenerationResult(
                    file_spec=file_spec,
                    success=False,
                    error=f"Batch execution failed: {e}",
                    generation_time=0.0,
                )
                for file_spec in files
            ]

    async def _create_file_generation_task(
        self,
        file_spec: FileSpec,
        subtask_context: dict[str, Any],
        completed_files: dict[str, FileGenerationResult],
    ):
        """Create an async task for generating a single file"""
        return await self._generate_single_file(
            file_spec, subtask_context, completed_files
        )

    async def _generate_single_file(
        self,
        file_spec: FileSpec,
        subtask_context: dict[str, Any],
        completed_files: dict[str, FileGenerationResult],
    ) -> FileGenerationResult:
        """Generate a single file with proper context"""
        start_time = datetime.now()

        try:
            # Prepare file-specific context
            file_context = self.context_consolidator.prepare_file_context(
                file_spec, subtask_context, completed_files
            )

            # Create enhanced task description for file generation
            task_description = self._create_file_task_description(
                file_spec, file_context
            )

            # Create agent state for this file generation
            agent_state = subtask_context.copy()
            agent_state.update(
                {
                    "current_file_spec": file_spec,
                    "file_context": file_context,
                    "task_description": task_description,
                    "file_generation_mode": True,
                }
            )

            # Execute file generation using OAMAT agent
            result = await self._execute_file_generation_agent(agent_state, file_spec)

            generation_time = (datetime.now() - start_time).total_seconds()

            return FileGenerationResult(
                file_spec=file_spec,
                success=result.get("success", False),
                content=result.get("content"),
                file_path=result.get("file_path"),
                generation_time=generation_time,
                context_used=file_context,
                generated_artifacts=result.get("artifacts", []),
                error=result.get("error"),
            )

        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"File generation failed for {file_spec.name}: {e}")

            return FileGenerationResult(
                file_spec=file_spec,
                success=False,
                error=str(e),
                generation_time=generation_time,
            )

    def _create_file_task_description(
        self, file_spec: FileSpec, file_context: dict[str, Any]
    ) -> str:
        """Create a detailed task description for file generation"""

        # Get dependency information
        dep_info = ""
        if file_spec.dependencies and file_context.get("dependency_files"):
            dep_files = list(file_context["dependency_files"].keys())
            dep_info = f"\n\n**Dependencies**: This file depends on {', '.join(dep_files)}. Use their content as reference for consistency."

        # Get context requirements
        context_info = ""
        if file_spec.context_requirements:
            context_info = f"\n\n**Context Requirements**: This file requires understanding of: {', '.join(file_spec.context_requirements)}"

        # Success criteria
        criteria_info = ""
        if file_spec.success_criteria:
            criteria_info = (
                f"\n\n**Success Criteria**: {'. '.join(file_spec.success_criteria)}"
            )

        task_description = f"""
**FILE GENERATION TASK**

**File**: {file_spec.name}
**Path**: {file_spec.path}
**Type**: {file_spec.content_type}
**Agent Role**: {file_spec.agent_role}

**Task**: Generate the file '{file_spec.name}' at path '{file_spec.path}' as part of the current subtask.

{dep_info}{context_info}{criteria_info}

**CRITICAL REQUIREMENTS**:
- You MUST save the generated content using write_file("{file_spec.path}", content)
- The file should be of type {file_spec.content_type}
- Follow best practices for {file_spec.content_type} files
- Use the provided context and dependency information to ensure consistency
- Generate complete, functional content - no placeholders or TODO comments

**Available Tools**: {', '.join(file_spec.tools_needed)}

Please generate this file now and save it using write_file.
        """.strip()

        return task_description

    async def _execute_file_generation_agent(
        self, agent_state: dict[str, Any], file_spec: FileSpec
    ) -> dict[str, Any]:
        """Execute the agent to generate a specific file"""

        try:
            # Use asyncio to run the synchronous agent method
            loop = asyncio.get_event_loop()

            # Create a specialized agent for this file generation
            node_id = f"file_{file_spec.name.replace('.', '_').replace('/', '_')}"

            result = await loop.run_in_executor(
                None, self.oamat._run_agent_node, agent_state, {}, node_id
            )

            # Extract file generation results
            if result and "agent_outputs" in result:
                agent_output = result["agent_outputs"].get(node_id, {})

                return {
                    "success": True,
                    "content": "Generated by agent",  # Agent handles file writing directly
                    "file_path": file_spec.path,
                    "artifacts": [file_spec.path],
                    "agent_result": agent_output,
                }
            else:
                return {"success": False, "error": "No agent output received"}

        except Exception as e:
            return {"success": False, "error": f"Agent execution failed: {e}"}
