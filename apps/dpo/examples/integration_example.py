#!/usr/bin/env python3
"""
Integration Example: Request Analyzer with Orchestrator
Demonstrates how to use the Request Analyzer to generate orchestrator workflows
"""

import json
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(
    0, str(Path(__file__).parent.parent.parent / "agent-orchestrator" / "src")
)

from generic_orchestrator import AgentTask, GenericOrchestrator
from request_analyzer import ComplexityLevel, ProjectType, RequestAnalyzer


class DPOIntegration:
    """Example integration of Request Analyzer with Orchestrator"""

    def __init__(self):
        self.analyzer = RequestAnalyzer()

    def create_orchestrator_tasks(self, analysis):
        """
        Convert RequestAnalysis to orchestrator AgentTask objects

        Args:
            analysis: RequestAnalysis object from analyzer

        Returns:
            List of AgentTask objects for orchestrator
        """
        tasks = []
        task_counter = 1

        # Phase 1: Requirements Analysis
        if "requirements" in analysis.phases:
            tasks.append(
                AgentTask(
                    task_id=f"task_{task_counter:03d}_requirements",
                    task_type="requirements-analyst",
                    prompt=self._generate_requirements_prompt(analysis),
                    context={
                        "project_type": analysis.project_type.value,
                        "tech_stack": analysis.tech_stack.to_dict(),
                        "requirements": analysis.requirements,
                    },
                    dependencies=[],
                )
            )
            task_counter += 1

        # Phase 2: Architecture Design
        if "architecture" in analysis.phases:
            tasks.append(
                AgentTask(
                    task_id=f"task_{task_counter:03d}_architecture",
                    task_type="solution-architect",
                    prompt=self._generate_architecture_prompt(analysis),
                    context={
                        "project_type": analysis.project_type.value,
                        "complexity": analysis.complexity.value,
                        "tech_stack": analysis.tech_stack.to_dict(),
                    },
                    dependencies=[tasks[0].task_id] if tasks else [],
                )
            )
            task_counter += 1

        # Phase 3: API Design (if applicable)
        if "api_design" in analysis.phases:
            tasks.append(
                AgentTask(
                    task_id=f"task_{task_counter:03d}_api_design",
                    task_type="api-design-specialist",
                    prompt=self._generate_api_design_prompt(analysis),
                    context={
                        "api_type": "REST",
                        "tech_stack": analysis.tech_stack.to_dict(),
                    },
                    dependencies=[
                        t.task_id for t in tasks if "architecture" in t.task_id
                    ],
                )
            )
            task_counter += 1

        # Phase 4: Implementation
        if "implementation" in analysis.phases:
            # Create multiple implementation tasks based on complexity
            impl_count = 2 if analysis.complexity == ComplexityLevel.SIMPLE else 3

            for i in range(impl_count):
                tasks.append(
                    AgentTask(
                        task_id=f"task_{task_counter:03d}_implementation_{i+1}",
                        task_type="development-specialist",
                        prompt=self._generate_implementation_prompt(
                            analysis, i + 1, impl_count
                        ),
                        context={
                            "tech_stack": analysis.tech_stack.to_dict(),
                            "component": f"component_{i+1}",
                        },
                        dependencies=[
                            t.task_id
                            for t in tasks
                            if "architecture" in t.task_id or "api_design" in t.task_id
                        ],
                    )
                )
                task_counter += 1

        # Phase 5: Testing
        if "testing" in analysis.phases:
            tasks.append(
                AgentTask(
                    task_id=f"task_{task_counter:03d}_testing",
                    task_type="qa-testing-guru",
                    prompt=self._generate_testing_prompt(analysis),
                    context={
                        "test_types": ["unit", "integration", "e2e"],
                        "tech_stack": analysis.tech_stack.to_dict(),
                    },
                    dependencies=[
                        t.task_id for t in tasks if "implementation" in t.task_id
                    ],
                )
            )
            task_counter += 1

        # Phase 6: Documentation
        if "documentation" in analysis.phases:
            tasks.append(
                AgentTask(
                    task_id=f"task_{task_counter:03d}_documentation",
                    task_type="technical-writer",
                    prompt=self._generate_documentation_prompt(analysis),
                    context={
                        "doc_types": ["user_guide", "api_docs", "developer_guide"],
                        "project_type": analysis.project_type.value,
                    },
                    dependencies=[
                        t.task_id for t in tasks if "implementation" in t.task_id
                    ],
                )
            )
            task_counter += 1

        # Phase 7: Deployment (if applicable)
        if "deployment" in analysis.phases:
            tasks.append(
                AgentTask(
                    task_id=f"task_{task_counter:03d}_deployment",
                    task_type="sdlc-deployment",
                    prompt=self._generate_deployment_prompt(analysis),
                    context={
                        "deployment_target": "production",
                        "tech_stack": analysis.tech_stack.to_dict(),
                    },
                    dependencies=[t.task_id for t in tasks if "testing" in t.task_id],
                )
            )
            task_counter += 1

        return tasks

    def _generate_requirements_prompt(self, analysis):
        """Generate prompt for requirements analysis agent"""
        return f"""Analyze and document comprehensive requirements for: {analysis.original_request}

Project Type: {analysis.project_type.value}
Tech Stack: {json.dumps(analysis.tech_stack.to_dict(), indent=2)}
Focus Areas: {', '.join(analysis.focus_areas)}

Deliverables:
1. Functional requirements specification
2. Non-functional requirements
3. User stories and acceptance criteria
4. Technical constraints and assumptions
5. Success metrics and KPIs

Context: {json.dumps(analysis.ecosystem_context, indent=2)}
"""

    def _generate_architecture_prompt(self, analysis):
        """Generate prompt for architecture design agent"""
        return f"""Design the system architecture for: {analysis.original_request}

Project Type: {analysis.project_type.value}
Complexity: {analysis.complexity.value}
Tech Stack: {json.dumps(analysis.tech_stack.to_dict(), indent=2)}

Deliverables:
1. High-level architecture diagram
2. Component breakdown and responsibilities
3. Data flow and storage design
4. Integration points and APIs
5. Security and performance considerations

Focus on: {', '.join(analysis.focus_areas)}
"""

    def _generate_api_design_prompt(self, analysis):
        """Generate prompt for API design agent"""
        return f"""Design the API specification for: {analysis.original_request}

Tech Stack: {json.dumps(analysis.tech_stack.to_dict(), indent=2)}
API Standards: RESTful, OpenAPI 3.0

Deliverables:
1. Complete API endpoint definitions
2. Request/response schemas
3. Authentication and authorization flow
4. Error handling standards
5. OpenAPI/Swagger documentation
"""

    def _generate_implementation_prompt(self, analysis, part, total):
        """Generate prompt for implementation agent"""
        return f"""Implement part {part} of {total} for: {analysis.original_request}

Tech Stack: {json.dumps(analysis.tech_stack.to_dict(), indent=2)}
Component: Part {part}/{total} of the implementation

Deliverables:
1. Working code implementation
2. Unit tests for your component
3. Integration with other components
4. Error handling and logging
5. Performance optimization

Focus on clean, maintainable code following best practices.
"""

    def _generate_testing_prompt(self, analysis):
        """Generate prompt for testing agent"""
        return f"""Create comprehensive test suite for: {analysis.original_request}

Tech Stack: {json.dumps(analysis.tech_stack.to_dict(), indent=2)}
Test Types: Unit, Integration, End-to-End

Deliverables:
1. Unit test suite with >80% coverage
2. Integration tests for all APIs
3. End-to-end test scenarios
4. Performance test benchmarks
5. Test documentation and CI/CD integration
"""

    def _generate_documentation_prompt(self, analysis):
        """Generate prompt for documentation agent"""
        return f"""Create complete documentation for: {analysis.original_request}

Project Type: {analysis.project_type.value}
Target Audience: Developers and End Users

Deliverables:
1. README with quick start guide
2. API documentation (if applicable)
3. User guide with examples
4. Developer documentation
5. Deployment and operations guide
"""

    def _generate_deployment_prompt(self, analysis):
        """Generate prompt for deployment agent"""
        return f"""Create deployment configuration for: {analysis.original_request}

Tech Stack: {json.dumps(analysis.tech_stack.to_dict(), indent=2)}
Deployment Target: Production Environment

Deliverables:
1. Dockerfile and docker-compose.yml (if applicable)
2. CI/CD pipeline configuration
3. Environment configuration and secrets management
4. Monitoring and logging setup
5. Deployment documentation and runbooks
"""

    def process_request(self, user_request):
        """
        Complete processing pipeline from request to orchestrator tasks

        Args:
            user_request: Natural language development request

        Returns:
            Dictionary with analysis and generated tasks
        """
        print(f"Processing request: {user_request}")
        print("-" * 50)

        # Step 1: Analyze the request
        print("Step 1: Analyzing request...")
        analysis = self.analyzer.analyze(user_request)

        # Display analysis results
        print(f"  Project Type: {analysis.project_type.value}")
        print(f"  Complexity: {analysis.complexity.value}")
        print(f"  Estimated Agents: {analysis.estimated_agents}")
        print(
            f"  Tech Stack: {', '.join(analysis.tech_stack.languages + analysis.tech_stack.frameworks)}"
        )
        print(f"  Phases: {', '.join(analysis.phases)}")
        print(f"  Confidence: {analysis.confidence_score:.2f}")

        # Step 2: Validate analysis
        print("\nStep 2: Validating analysis...")
        is_valid, issues = self.analyzer.validate_analysis(analysis)

        if not is_valid:
            print("  Validation failed:")
            for issue in issues:
                print(f"    - {issue}")
            return None

        print("  Analysis validated successfully")

        # Step 3: Generate orchestrator tasks
        print("\nStep 3: Generating orchestrator tasks...")
        tasks = self.create_orchestrator_tasks(analysis)
        print(f"  Generated {len(tasks)} tasks")

        # Display task summary
        print("\n  Task Summary:")
        for task in tasks:
            deps = (
                f" (depends on: {', '.join(task.dependencies)})"
                if task.dependencies
                else ""
            )
            print(f"    - {task.task_id}: {task.task_type}{deps}")

        # Step 4: Create workflow configuration
        print("\nStep 4: Creating workflow configuration...")
        workflow_config = {
            "workflow_name": f"dpo_workflow_{analysis.project_type.value}",
            "description": analysis.original_request,
            "max_parallel": min(5, analysis.estimated_agents // 3),
            "checkpoint_interval": 3,
            "analysis": analysis.to_dict(),
            "tasks": [task.to_dict() for task in tasks],
        }

        print(f"  Workflow: {workflow_config['workflow_name']}")
        print(f"  Max Parallel: {workflow_config['max_parallel']}")
        print(f"  Total Tasks: {len(workflow_config['tasks'])}")

        return workflow_config


def main():
    """Example usage of the DPO integration"""

    # Example requests to demonstrate different project types
    example_requests = [
        "Build a REST API for user management with JWT authentication",
        "Create a React dashboard with real-time data visualization",
        "Develop a full-stack e-commerce platform with payment processing",
        "Build a CLI tool for automated file organization",
        "Create a Python library for advanced data validation",
    ]

    integrator = DPOIntegration()

    print("=" * 70)
    print("DPO Request Analyzer - Orchestrator Integration Example")
    print("=" * 70)

    for i, request in enumerate(example_requests, 1):
        print(f"\nExample {i}:")
        print("=" * 70)

        workflow = integrator.process_request(request)

        if workflow:
            # Save workflow to file
            output_file = f"workflow_example_{i}.json"
            with open(output_file, "w") as f:
                json.dump(workflow, f, indent=2)
            print(f"\n  Workflow saved to: {output_file}")

        print()

    print("=" * 70)
    print("Integration examples complete!")
    print("\nTo execute a workflow with the orchestrator:")
    print("  1. Review the generated workflow JSON files")
    print("  2. Run: python -m generic_orchestrator workflow_example_1.json")


if __name__ == "__main__":
    main()
