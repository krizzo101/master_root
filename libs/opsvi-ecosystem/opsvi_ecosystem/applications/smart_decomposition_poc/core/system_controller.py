"""
Smart Decomposition Meta-Intelligence System - System Controller
Main orchestration system with parallel execution capabilities
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import time
from typing import Any, Dict, List, Optional

from .agent_factory import AgentFactory, SpecializedAgentFactory
from .config import SystemConfig, get_config
from .dependency_manager import DependencyManager
from .parallel_execution_engine import (
    ExecutionResult,
    ExecutionTask,
    ParallelExecutionEngine,
)
from .schemas import (
    CoordinationResponse,
    ImplementationResponse,
    PerformanceMetrics,
    RequirementsResponse,
    ValidationResponse,
)


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution"""

    success: bool
    generated_application: Dict[str, Any]
    requirements: Optional[RequirementsResponse]
    work_plan: Optional[CoordinationResponse]
    implementation: Optional[ImplementationResponse]
    validation: Optional[ValidationResponse]
    performance_metrics: PerformanceMetrics
    execution_time: float
    parallel_efficiency: float
    metadata: Dict[str, Any]


class SystemController:
    """
    Main system controller for the Smart Decomposition Meta-Intelligence System.
    Orchestrates autonomous application generation with parallel execution.
    """

    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or get_config()
        self.agent_factory = AgentFactory(self.config)
        self.specialized_factory = SpecializedAgentFactory(self.agent_factory)
        self.parallel_engine = ParallelExecutionEngine(self.config)
        self.dependency_manager = DependencyManager(self.config)
        self.workflow_history = []
        self.performance_tracker = PerformanceTracker()

    async def initialize(self):
        """Initialize all system components"""
        await self.parallel_engine.initialize()
        await self.dependency_manager.initialize()
        print("✅ System controller initialized with parallel execution")

    async def generate_application_from_prompt(
        self, user_prompt: str, execution_mode: str = "parallel"
    ) -> WorkflowResult:
        """
        Main entry point: Generate complete application from user prompt.

        Args:
            user_prompt: Natural language description of desired application
            execution_mode: "parallel" (default), "sequential", or "hybrid"

        Returns:
            WorkflowResult with complete application and performance metrics
        """
        start_time = time.time()
        workflow_id = f"workflow_{int(start_time)}"

        print(f"🚀 Starting Smart Decomposition workflow: {workflow_id}")
        print(f"📝 User prompt: {user_prompt}")
        print(f"⚡ Execution mode: {execution_mode}")

        try:
            if execution_mode == "parallel":
                return await self._execute_parallel_workflow(
                    user_prompt, workflow_id, start_time
                )
            else:
                return await self._execute_sequential_workflow(
                    user_prompt, workflow_id, start_time
                )

        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time

            print(f"\n❌ Workflow failed: {str(e)}")

            # Create error result
            error_result = WorkflowResult(
                success=False,
                generated_application={},
                requirements=None,
                work_plan=None,
                implementation=None,
                validation=None,
                performance_metrics=self._create_error_metrics(execution_time),
                execution_time=execution_time,
                parallel_efficiency=0.0,
                metadata={
                    "workflow_id": workflow_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )

            self.workflow_history.append(error_result)
            return error_result

    async def _execute_parallel_workflow(
        self, user_prompt: str, workflow_id: str, start_time: float
    ) -> WorkflowResult:
        """Execute workflow using parallel execution engine"""

        print("\n🔄 Creating parallel execution plan...")

        # Create execution tasks for parallel processing
        tasks = await self._create_parallel_execution_tasks(user_prompt)

        print(f"📋 Created {len(tasks)} execution tasks")
        for task in tasks:
            deps_str = f" (deps: {task.dependencies})" if task.dependencies else ""
            print(f"   • {task.task_id}: {task.agent_role}{deps_str}")

        # Execute using parallel engine
        execution_result = await self.parallel_engine.execute_workflow(tasks)

        end_time = time.time()
        execution_time = end_time - start_time

        if execution_result["success"]:
            # Extract results from parallel execution
            task_results = execution_result["task_results"]

            # Parse structured results
            requirements = self._extract_requirements_from_results(task_results)
            work_plan = self._extract_work_plan_from_results(task_results)
            implementation = self._extract_implementation_from_results(task_results)
            validation = self._extract_validation_from_results(task_results)

            # Package application
            application = self._package_application_from_results(task_results)

            result = WorkflowResult(
                success=True,
                generated_application=application,
                requirements=requirements,
                work_plan=work_plan,
                implementation=implementation,
                validation=validation,
                performance_metrics=execution_result["performance_metrics"],
                execution_time=execution_time,
                parallel_efficiency=execution_result["parallel_efficiency"],
                metadata={
                    "workflow_id": workflow_id,
                    "user_prompt": user_prompt,
                    "execution_mode": "parallel",
                    "wave_count": execution_result["wave_count"],
                    "task_count": len(tasks),
                    "completion_time": datetime.utcnow().isoformat(),
                    "agent_performance": self.agent_factory.get_agent_performance_metrics(),
                },
            )

            print("\n🎉 Parallel workflow completed successfully!")
            print(f"⚡ Parallel efficiency: {result.parallel_efficiency:.2f}x")
            print(
                f"📊 Executed {len(tasks)} tasks in {execution_result['wave_count']} waves"
            )
            print(f"⏱️ Total time: {execution_time:.2f}s")

        else:
            result = WorkflowResult(
                success=False,
                generated_application={},
                requirements=None,
                work_plan=None,
                implementation=None,
                validation=None,
                performance_metrics=execution_result["performance_metrics"],
                execution_time=execution_time,
                parallel_efficiency=execution_result.get("parallel_efficiency", 0.0),
                metadata={
                    "workflow_id": workflow_id,
                    "error": "Parallel execution failed",
                    "task_results": execution_result.get("task_results", {}),
                },
            )

        self.workflow_history.append(result)
        return result

    async def _execute_sequential_workflow(
        self, user_prompt: str, workflow_id: str, start_time: float
    ) -> WorkflowResult:
        """Execute workflow using sequential processing (legacy mode)"""

        print("\n📋 Phase 1: Requirements Analysis...")
        requirements = await self._expand_requirements(user_prompt)

        print("\n🗂️ Phase 2: Work Planning...")
        work_plan = await self._create_work_plan(requirements)

        print("\n💻 Phase 3: Implementation...")
        implementation = await self._implement_application(work_plan)

        print("\n✅ Phase 4: Validation...")
        validation = await self._validate_implementation(implementation, requirements)

        print("\n📦 Phase 5: Packaging...")
        application = self._package_application(implementation)

        end_time = time.time()
        execution_time = end_time - start_time

        # Create performance metrics for sequential execution
        performance_metrics = PerformanceMetrics(
            execution_time=execution_time,
            parallel_efficiency=1.0,  # Sequential = 1x efficiency
            task_count=4,  # 4 sequential phases
            success_rate=1.0,
            memory_usage=400.0,  # Estimated
            model_usage={},
        )

        result = WorkflowResult(
            success=True,
            generated_application=application,
            requirements=requirements,
            work_plan=work_plan,
            implementation=implementation,
            validation=validation,
            performance_metrics=performance_metrics,
            execution_time=execution_time,
            parallel_efficiency=1.0,
            metadata={
                "workflow_id": workflow_id,
                "user_prompt": user_prompt,
                "execution_mode": "sequential",
                "completion_time": datetime.utcnow().isoformat(),
            },
        )

        print(f"\n🎉 Sequential workflow completed in {execution_time:.2f}s")

        self.workflow_history.append(result)
        return result

    async def _create_parallel_execution_tasks(
        self, user_prompt: str
    ) -> List[ExecutionTask]:
        """Create execution tasks optimized for parallel processing"""

        # Create initial requirements analysis task
        requirements_task = ExecutionTask(
            task_id="requirements_analysis",
            agent_role="requirements_expander",
            input_data={
                "input": f"""
                Analyze the following user prompt and expand it into comprehensive technical requirements:

                User Prompt: "{user_prompt}"

                Provide detailed analysis including:
                1. Complete technical specifications
                2. System dependencies and integrations
                3. Complexity assessment
                4. Effort estimation
                5. Validation criteria
                6. Architecture considerations
                7. Risk factors
                """
            },
            dependencies=[],
            priority=10,
            estimated_duration=120,  # 2 minutes
        )

        # Work planning depends on requirements
        planning_task = ExecutionTask(
            task_id="work_planning",
            agent_role="manager",
            input_data={
                "input": "Create detailed work plan and task decomposition based on requirements analysis"
            },
            dependencies=["requirements_analysis"],
            priority=9,
            estimated_duration=90,  # 1.5 minutes
        )

        # Implementation can start after planning
        implementation_task = ExecutionTask(
            task_id="implementation",
            agent_role="developer",
            input_data={
                "input": "Implement complete application based on work plan and requirements"
            },
            dependencies=["work_planning"],
            priority=8,
            estimated_duration=300,  # 5 minutes
        )

        # Testing can run in parallel with some implementation work
        testing_task = ExecutionTask(
            task_id="testing",
            agent_role="tester",
            input_data={
                "input": "Create comprehensive test suite based on requirements and implementation"
            },
            dependencies=["requirements_analysis", "work_planning"],
            priority=7,
            estimated_duration=180,  # 3 minutes
        )

        # Documentation can run in parallel
        documentation_task = ExecutionTask(
            task_id="documentation",
            agent_role="coordinator",
            input_data={
                "input": "Create comprehensive documentation based on requirements and work plan"
            },
            dependencies=["requirements_analysis", "work_planning"],
            priority=6,
            estimated_duration=120,  # 2 minutes
        )

        # Final validation depends on implementation and testing
        validation_task = ExecutionTask(
            task_id="validation",
            agent_role="validator",
            input_data={
                "input": "Validate complete application against requirements and quality standards"
            },
            dependencies=["implementation", "testing"],
            priority=5,
            estimated_duration=90,  # 1.5 minutes
        )

        return [
            requirements_task,
            planning_task,
            implementation_task,
            testing_task,
            documentation_task,
            validation_task,
        ]

    def _extract_requirements_from_results(
        self, task_results: Dict[str, ExecutionResult]
    ) -> Optional[RequirementsResponse]:
        """Extract requirements response from task results"""
        if "requirements_analysis" in task_results:
            result = task_results["requirements_analysis"]
            if result.success and result.result:
                try:
                    return RequirementsResponse(**result.result)
                except Exception as e:
                    print(f"⚠️  Failed to parse requirements: {e}")
        return None

    def _extract_work_plan_from_results(
        self, task_results: Dict[str, ExecutionResult]
    ) -> Optional[CoordinationResponse]:
        """Extract work plan from task results"""
        if "work_planning" in task_results:
            result = task_results["work_planning"]
            if result.success and result.result:
                try:
                    return CoordinationResponse(**result.result)
                except Exception as e:
                    print(f"⚠️  Failed to parse work plan: {e}")
        return None

    def _extract_implementation_from_results(
        self, task_results: Dict[str, ExecutionResult]
    ) -> Optional[ImplementationResponse]:
        """Extract implementation from task results"""
        if "implementation" in task_results:
            result = task_results["implementation"]
            if result.success and result.result:
                try:
                    return ImplementationResponse(**result.result)
                except Exception as e:
                    print(f"⚠️  Failed to parse implementation: {e}")
        return None

    def _extract_validation_from_results(
        self, task_results: Dict[str, ExecutionResult]
    ) -> Optional[ValidationResponse]:
        """Extract validation from task results"""
        if "validation" in task_results:
            result = task_results["validation"]
            if result.success and result.result:
                try:
                    return ValidationResponse(**result.result)
                except Exception as e:
                    print(f"⚠️  Failed to parse validation: {e}")
        return None

    def _package_application_from_results(
        self, task_results: Dict[str, ExecutionResult]
    ) -> Dict[str, Any]:
        """Package complete application from all task results"""
        application = {
            "metadata": {
                "name": "Generated Application",
                "version": "1.0.0",
                "generated_at": datetime.utcnow().isoformat(),
                "generator": "Smart Decomposition Meta-Intelligence System (Parallel)",
            },
            "code_files": {},
            "documentation": "",
            "tests": "",
            "deployment": "",
            "setup_instructions": "",
            "dependencies": [],
            "notes": [],
        }

        # Extract implementation details
        if "implementation" in task_results:
            impl_result = task_results["implementation"].result
            if "code_files" in impl_result:
                application["code_files"] = impl_result["code_files"]
            if "documentation" in impl_result:
                application["documentation"] = impl_result["documentation"]
            if "deployment_config" in impl_result:
                application["deployment"] = impl_result["deployment_config"]
            if "setup_instructions" in impl_result:
                application["setup_instructions"] = impl_result["setup_instructions"]

        # Extract testing information
        if "testing" in task_results:
            test_result = task_results["testing"].result
            if "tests" in test_result:
                application["tests"] = test_result.get("tests", "")

        # Extract documentation
        if "documentation" in task_results:
            doc_result = task_results["documentation"].result
            if "content" in doc_result:
                application["documentation"] += "\n\n" + doc_result["content"]

        return application

    # Keep existing sequential methods for backward compatibility
    async def _expand_requirements(self, user_prompt: str) -> RequirementsResponse:
        """Legacy sequential requirements expansion"""
        requirements_agent = self.specialized_factory.create_requirements_expander()

        input_data = {"input": f"Analyze requirements for: {user_prompt}"}

        result = await requirements_agent.process_with_structured_response(input_data)

        if not result["success"]:
            raise ValueError(
                f"Requirements expansion failed: {result.get('error', 'Unknown error')}"
            )

        requirements_data = result["result"]
        return RequirementsResponse(**requirements_data)

    async def _create_work_plan(
        self, requirements: RequirementsResponse
    ) -> CoordinationResponse:
        """Legacy sequential work planning"""
        manager_agent = self.specialized_factory.create_manager_agent()

        input_data = {
            "input": f"Create work plan for: {requirements.expanded_requirements}"
        }

        result = await manager_agent.process_with_structured_response(input_data)

        if not result["success"]:
            raise ValueError(
                f"Work planning failed: {result.get('error', 'Unknown error')}"
            )

        work_plan_data = result["result"]
        return CoordinationResponse(**work_plan_data)

    async def _implement_application(
        self, work_plan: CoordinationResponse
    ) -> ImplementationResponse:
        """Legacy sequential implementation"""
        developer_agent = self.specialized_factory.create_developer_agent()

        input_data = {"input": "Implement application based on work plan"}

        result = await developer_agent.process_with_structured_response(input_data)

        if not result["success"]:
            raise ValueError(
                f"Implementation failed: {result.get('error', 'Unknown error')}"
            )

        implementation_data = result["result"]
        return ImplementationResponse(**implementation_data)

    async def _validate_implementation(
        self, implementation: ImplementationResponse, requirements: RequirementsResponse
    ) -> ValidationResponse:
        """Legacy sequential validation"""
        validator_spec = {
            "role": "validator",
            "capabilities": [
                "code_validation",
                "requirements_checking",
                "quality_assessment",
            ],
        }
        validator_agent = self.agent_factory.create_agent(validator_spec)

        input_data = {"input": "Validate implementation against requirements"}

        result = await validator_agent.process_with_structured_response(input_data)

        if not result["success"]:
            raise ValueError(
                f"Validation failed: {result.get('error', 'Unknown error')}"
            )

        validation_data = result["result"]
        return ValidationResponse(**validation_data)

    def _package_application(
        self, implementation: ImplementationResponse
    ) -> Dict[str, Any]:
        """Legacy sequential application packaging"""
        application = {
            "metadata": {
                "name": "Generated Application",
                "version": "1.0.0",
                "generated_at": datetime.utcnow().isoformat(),
                "generator": "Smart Decomposition Meta-Intelligence System (Sequential)",
            },
            "code_files": {},
            "documentation": implementation.documentation,
            "tests": implementation.tests,
            "deployment": implementation.deployment_config,
            "setup_instructions": implementation.setup_instructions,
            "dependencies": implementation.dependencies_installed,
            "notes": implementation.implementation_notes,
        }

        # Convert code files from Pydantic models to dict
        for code_file in implementation.code_files:
            application["code_files"][code_file.filename] = {
                "content": code_file.content,
                "language": code_file.language,
                "purpose": code_file.purpose,
            }

        return application

    def _create_error_metrics(self, execution_time: float) -> PerformanceMetrics:
        """Create error metrics for failed workflows"""
        return PerformanceMetrics(
            execution_time=execution_time,
            parallel_efficiency=0.0,
            task_count=0,
            success_rate=0.0,
            memory_usage=0.0,
            model_usage={},
        )

    def get_workflow_history(self) -> List[WorkflowResult]:
        """Get history of all workflow executions"""
        return self.workflow_history

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all workflows"""
        if not self.workflow_history:
            return {"message": "No workflows executed yet"}

        successful_workflows = [w for w in self.workflow_history if w.success]

        # Calculate parallel efficiency statistics
        parallel_workflows = [
            w for w in successful_workflows if w.parallel_efficiency > 1.0
        ]
        avg_parallel_efficiency = (
            sum(w.parallel_efficiency for w in parallel_workflows)
            / len(parallel_workflows)
            if parallel_workflows
            else 1.0
        )

        return {
            "total_workflows": len(self.workflow_history),
            "successful_workflows": len(successful_workflows),
            "success_rate": len(successful_workflows) / len(self.workflow_history),
            "average_execution_time": sum(
                w.execution_time for w in successful_workflows
            )
            / len(successful_workflows)
            if successful_workflows
            else 0,
            "average_parallel_efficiency": avg_parallel_efficiency,
            "parallel_workflows": len(parallel_workflows),
            "max_parallel_efficiency": max(
                w.parallel_efficiency for w in self.workflow_history
            )
            if self.workflow_history
            else 0,
            "agent_performance": self.agent_factory.get_agent_performance_metrics(),
            "efficiency_target_met": avg_parallel_efficiency >= 3.0,
        }

    async def close(self):
        """Clean up system resources"""
        await self.dependency_manager.close()


class PerformanceTracker:
    """Track system performance across workflow executions"""

    def __init__(self):
        self.execution_history = []

    def record_execution(self, result: WorkflowResult):
        """Record workflow execution for performance analysis"""
        self.execution_history.append(
            {
                "timestamp": datetime.utcnow(),
                "success": result.success,
                "execution_time": result.execution_time,
                "parallel_efficiency": result.parallel_efficiency,
                "task_count": result.performance_metrics.task_count,
            }
        )

        # Keep only last 50 executions
        if len(self.execution_history) > 50:
            self.execution_history.pop(0)


# Enhanced workflow runner with parallel capabilities
async def run_enhanced_demo(
    user_prompt: str = "Create a todo application with real-time updates",
    execution_mode: str = "parallel",
):
    """Run enhanced demonstration with parallel execution"""
    print("🌟 Smart Decomposition Meta-Intelligence System - Enhanced Demo")
    print("=" * 70)
    print(f"⚡ Execution Mode: {execution_mode}")

    controller = SystemController()
    await controller.initialize()

    try:
        result = await controller.generate_application_from_prompt(
            user_prompt, execution_mode
        )

        if result.success:
            print("\n✅ Enhanced demo completed successfully!")
            print(
                f"📁 Generated application with {len(result.generated_application.get('code_files', {}))} code files"
            )
            print(f"⏱️ Total execution time: {result.execution_time:.2f} seconds")
            print(f"⚡ Parallel efficiency: {result.parallel_efficiency:.2f}x")
            if result.parallel_efficiency >= 3.0:
                print("🎯 Parallel efficiency target achieved! (≥3x)")
            else:
                print(
                    f"📊 Parallel efficiency: {result.parallel_efficiency:.2f}x (target: ≥3x)"
                )

            # Performance summary
            summary = controller.get_performance_summary()
            print(f"📈 System performance: {summary}")

            return result
        else:
            print("\n❌ Enhanced demo failed!")
            return result

    except Exception as e:
        print(f"\n💥 Enhanced demo crashed: {str(e)}")
        raise
    finally:
        await controller.close()


if __name__ == "__main__":
    # Run enhanced demo if executed directly
    asyncio.run(run_enhanced_demo())
