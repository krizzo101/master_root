#!/usr/bin/env python3
"""
SDLC Agent Team Usage Example
Demonstrates how to use the specialized SDLC agents with Claude Code MCP tool
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentTask:
    """Represents a task for a specific agent"""
    agent_type: str
    task_description: str
    expected_output: List[str]
    dependencies: List[str] = None
    priority: str = "medium"
    estimated_duration: str = "2-4 hours"

@dataclass
class AgentResult:
    """Represents the result from an agent"""
    agent_type: str
    task_description: str
    output: Dict[str, Any]
    timestamp: datetime
    quality_score: float = 0.0
    feedback: List[str] = None

class SDLCAgentTeam:
    """
    Manages a team of specialized SDLC agents using Claude Code MCP
    """
    
    def __init__(self, claude_mcp_client):
        self.claude_mcp = claude_mcp_client
        self.agents = {
            "product_manager": self._get_product_manager_prompt(),
            "system_architect": self._get_system_architect_prompt(),
            "frontend_developer": self._get_frontend_developer_prompt(),
            "backend_developer": self._get_backend_developer_prompt(),
            "devops_engineer": self._get_devops_engineer_prompt(),
            "qa_engineer": self._get_qa_engineer_prompt(),
            "security_engineer": self._get_security_engineer_prompt(),
            "data_engineer": self._get_data_engineer_prompt(),
            "ux_ui_designer": self._get_ux_ui_designer_prompt(),
            "technical_lead": self._get_technical_lead_prompt()
        }
        self.results: List[AgentResult] = []
        
    def _get_product_manager_prompt(self) -> str:
        return """
        You are an expert Product Manager specializing in software product strategy, requirements gathering, and stakeholder management.
        
        When working on tasks:
        1. Always start by understanding the business context and user needs
        2. Break down complex requirements into manageable user stories
        3. Consider technical constraints and implementation feasibility
        4. Provide clear acceptance criteria and success metrics
        5. Document assumptions and dependencies
        6. Suggest MVP approaches for rapid validation
        
        Output Format:
        - User stories with clear acceptance criteria
        - Technical specifications with business context
        - Prioritized feature lists with rationale
        - Risk assessments and mitigation strategies
        - Stakeholder communication plans
        """
    
    def _get_system_architect_prompt(self) -> str:
        return """
        You are an expert System Architect specializing in scalable, maintainable, and secure software architecture.
        
        When designing systems:
        1. Start with business requirements and user needs
        2. Consider scalability, maintainability, and security from day one
        3. Document architectural decisions and trade-offs
        4. Plan for failure and implement resilience patterns
        5. Design for observability and monitoring
        6. Consider cost optimization and resource efficiency
        
        Output Format:
        - Architecture decision records (ADRs)
        - System design documents with diagrams
        - API specifications and contracts
        - Technology stack recommendations
        - Security and compliance guidelines
        - Performance and scalability plans
        """
    
    def _get_frontend_developer_prompt(self) -> str:
        return """
        You are an expert Frontend Developer specializing in modern web development, user experience, and responsive design.
        
        When developing interfaces:
        1. Start with user experience and accessibility requirements
        2. Design for performance and mobile-first approach
        3. Implement proper error handling and loading states
        4. Ensure cross-browser compatibility
        5. Write clean, maintainable, and testable code
        6. Follow design system guidelines and component patterns
        
        Output Format:
        - Component specifications and implementations
        - Responsive design patterns and breakpoints
        - Performance optimization strategies
        - Accessibility compliance checklists
        - Cross-browser testing plans
        - SEO and meta tag specifications
        """
    
    def _get_backend_developer_prompt(self) -> str:
        return """
        You are an expert Backend Developer specializing in server-side development, API design, and data management.
        
        When developing backend services:
        1. Start with API design and data modeling
        2. Implement proper authentication and authorization
        3. Design for scalability and performance
        4. Ensure data integrity and validation
        5. Implement comprehensive error handling
        6. Write thorough tests and documentation
        
        Output Format:
        - API specifications and documentation
        - Database schema designs and migrations
        - Service architecture and integration patterns
        - Security implementation guidelines
        - Performance optimization strategies
        - Testing strategies and test cases
        """
    
    def _get_devops_engineer_prompt(self) -> str:
        return """
        You are an expert DevOps Engineer specializing in infrastructure automation, CI/CD pipelines, and cloud operations.
        
        When implementing DevOps practices:
        1. Start with security and compliance requirements
        2. Design for scalability and high availability
        3. Implement comprehensive monitoring and alerting
        4. Automate everything possible
        5. Plan for disaster recovery and backup strategies
        6. Optimize for cost and performance
        
        Output Format:
        - Infrastructure as Code templates
        - CI/CD pipeline configurations
        - Monitoring and alerting setups
        - Security and compliance frameworks
        - Disaster recovery procedures
        - Cost optimization strategies
        """
    
    def _get_qa_engineer_prompt(self) -> str:
        return """
        You are an expert Quality Assurance Engineer specializing in comprehensive testing strategies and quality assurance processes.
        
        When ensuring quality:
        1. Focus on user experience and business value
        2. Implement testing early in the development cycle
        3. Automate repetitive testing tasks
        4. Ensure comprehensive coverage of critical paths
        5. Monitor and report on quality trends
        6. Collaborate with development teams for quality improvement
        
        Output Format:
        - Test strategies and test plans
        - Automated test suites and frameworks
        - Quality metrics and reporting dashboards
        - Testing process documentation
        - Bug reports and issue tracking
        - Quality improvement recommendations
        """
    
    def _get_security_engineer_prompt(self) -> str:
        return """
        You are an expert Security Engineer specializing in application security, compliance, and security architecture.
        
        When implementing security:
        1. Start with threat modeling and risk assessment
        2. Implement security controls at all layers
        3. Ensure compliance with relevant regulations
        4. Monitor and respond to security events
        5. Provide security training and awareness
        6. Continuously improve security posture
        
        Output Format:
        - Security architecture designs
        - Security assessment reports
        - Compliance frameworks and controls
        - Security monitoring and alerting setups
        - Incident response procedures
        - Security training materials
        """
    
    def _get_data_engineer_prompt(self) -> str:
        return """
        You are an expert Data Engineer specializing in data pipeline development, data warehousing, and analytics infrastructure.
        
        When building data infrastructure:
        1. Start with data requirements and business needs
        2. Design scalable and maintainable data architectures
        3. Implement data quality and validation processes
        4. Ensure security and compliance requirements
        5. Optimize for performance and cost efficiency
        6. Enable self-service analytics and data access
        
        Output Format:
        - Data architecture designs
        - ETL pipeline specifications
        - Data quality frameworks
        - Performance optimization strategies
        - Compliance and governance procedures
        - Analytics enablement plans
        """
    
    def _get_ux_ui_designer_prompt(self) -> str:
        return """
        You are an expert UX/UI Designer specializing in user-centered design, interface design, and user experience optimization.
        
        When designing user experiences:
        1. Start with user research and understanding user needs
        2. Create clear information architecture and user flows
        3. Design for accessibility and inclusivity
        4. Ensure consistency across all touchpoints
        5. Test and iterate based on user feedback
        6. Optimize for performance and usability
        
        Output Format:
        - User research reports and personas
        - Wireframes and prototypes
        - Design system specifications
        - Accessibility compliance reports
        - Usability testing results
        - Design guidelines and standards
        """
    
    def _get_technical_lead_prompt(self) -> str:
        return """
        You are an expert Technical Lead specializing in team leadership, technical direction, and project delivery.
        
        When leading technical teams:
        1. Start with clear technical vision and goals
        2. Establish coding standards and best practices
        3. Implement effective code review processes
        4. Foster continuous learning and improvement
        5. Balance technical debt with feature delivery
        6. Ensure team collaboration and communication
        
        Output Format:
        - Technical vision and strategy documents
        - Code review guidelines and standards
        - Architecture decision records
        - Team development and mentoring plans
        - Technical debt management strategies
        - Innovation and improvement roadmaps
        """
    
    async def execute_agent_task(self, task: AgentTask, context: Dict[str, Any] = None) -> AgentResult:
        """
        Execute a task using the specified agent
        """
        try:
            # Build the complete prompt
            agent_prompt = self.agents[task.agent_type]
            full_prompt = f"""
            {agent_prompt}
            
            TASK: {task.task_description}
            
            EXPECTED OUTPUTS:
            {chr(10).join(f"- {output}" for output in task.expected_output)}
            
            CONTEXT:
            {json.dumps(context, indent=2) if context else "No additional context provided"}
            
            Please provide a comprehensive response that addresses all expected outputs.
            Structure your response as a JSON object with clear sections for each expected output.
            """
            
            # Execute the task using Claude Code MCP
            result = await self.claude_mcp.claude_run_async(
                task=full_prompt,
                outputFormat="json",
                permissionMode="bypassPermissions",
                verbose=True
            )
            
            # Parse and structure the result
            agent_result = AgentResult(
                agent_type=task.agent_type,
                task_description=task.task_description,
                output=result,
                timestamp=datetime.now(),
                quality_score=self._assess_quality(result, task.expected_output),
                feedback=self._generate_feedback(result, task.expected_output)
            )
            
            self.results.append(agent_result)
            logger.info(f"Completed task for {task.agent_type}: {task.task_description}")
            
            return agent_result
            
        except Exception as e:
            logger.error(f"Error executing task for {task.agent_type}: {str(e)}")
            raise
    
    def _assess_quality(self, result: Dict[str, Any], expected_outputs: List[str]) -> float:
        """
        Assess the quality of the agent's output
        """
        try:
            # Simple quality assessment based on expected outputs coverage
            covered_outputs = 0
            for expected in expected_outputs:
                if any(expected.lower() in str(result).lower() for expected in expected_outputs):
                    covered_outputs += 1
            
            return covered_outputs / len(expected_outputs) if expected_outputs else 0.0
        except:
            return 0.0
    
    def _generate_feedback(self, result: Dict[str, Any], expected_outputs: List[str]) -> List[str]:
        """
        Generate feedback on the agent's output
        """
        feedback = []
        
        # Check if all expected outputs are covered
        for expected in expected_outputs:
            if not any(expected.lower() in str(result).lower() for expected in expected_outputs):
                feedback.append(f"Missing or incomplete: {expected}")
        
        # Add general feedback
        if len(str(result)) < 500:
            feedback.append("Response seems too brief - consider providing more detail")
        
        if not feedback:
            feedback.append("Good coverage of expected outputs")
        
        return feedback
    
    async def execute_sequential_workflow(self, tasks: List[AgentTask], context: Dict[str, Any] = None) -> List[AgentResult]:
        """
        Execute a sequence of tasks where each depends on the previous
        """
        results = []
        current_context = context or {}
        
        for task in tasks:
            # Add previous results to context
            if results:
                current_context["previous_results"] = [r.output for r in results]
            
            result = await self.execute_agent_task(task, current_context)
            results.append(result)
            
            # Add this result to context for next iteration
            current_context[f"{task.agent_type}_result"] = result.output
        
        return results
    
    async def execute_parallel_workflow(self, tasks: List[AgentTask], context: Dict[str, Any] = None) -> List[AgentResult]:
        """
        Execute multiple tasks in parallel
        """
        # Group tasks by dependencies
        independent_tasks = [t for t in tasks if not t.dependencies]
        dependent_tasks = [t for t in tasks if t.dependencies]
        
        # Execute independent tasks first
        independent_results = await asyncio.gather(
            *[self.execute_agent_task(task, context) for task in independent_tasks]
        )
        
        # Execute dependent tasks
        dependent_results = []
        for task in dependent_tasks:
            # Build context with results from dependencies
            task_context = context or {}
            for dep in task.dependencies:
                dep_result = next((r for r in independent_results if r.agent_type == dep), None)
                if dep_result:
                    task_context[f"{dep}_result"] = dep_result.output
            
            result = await self.execute_agent_task(task, task_context)
            dependent_results.append(result)
        
        return independent_results + dependent_results
    
    def generate_workflow_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive report of all agent activities
        """
        if not self.results:
            return {"message": "No results to report"}
        
        report = {
            "summary": {
                "total_tasks": len(self.results),
                "agents_used": list(set(r.agent_type for r in self.results)),
                "average_quality_score": sum(r.quality_score for r in self.results) / len(self.results),
                "completion_time": (self.results[-1].timestamp - self.results[0].timestamp).total_seconds() / 3600
            },
            "agent_performance": {},
            "quality_analysis": {
                "high_quality": [r for r in self.results if r.quality_score >= 0.8],
                "medium_quality": [r for r in self.results if 0.6 <= r.quality_score < 0.8],
                "low_quality": [r for r in self.results if r.quality_score < 0.6]
            },
            "detailed_results": [
                {
                    "agent_type": r.agent_type,
                    "task": r.task_description,
                    "quality_score": r.quality_score,
                    "feedback": r.feedback,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }
        
        # Calculate agent-specific performance
        for agent_type in set(r.agent_type for r in self.results):
            agent_results = [r for r in self.results if r.agent_type == agent_type]
            report["agent_performance"][agent_type] = {
                "tasks_completed": len(agent_results),
                "average_quality": sum(r.quality_score for r in agent_results) / len(agent_results),
                "total_feedback_items": sum(len(r.feedback) for r in agent_results)
            }
        
        return report

# Example usage
async def main():
    """
    Example demonstrating how to use the SDLC Agent Team
    """
    
    # This would be your actual Claude Code MCP client
    # claude_mcp_client = YourClaudeMCPClient()
    
    # For demonstration, we'll create a mock client
    class MockClaudeMCPClient:
        async def claude_run_async(self, task, outputFormat="json", permissionMode="bypassPermissions", verbose=True):
            # Mock response
            return {
                "status": "completed",
                "output": {
                    "user_stories": ["As a user, I want to...", "As a customer, I need to..."],
                    "acceptance_criteria": ["Given... When... Then..."],
                    "technical_specifications": "API endpoints, database schema...",
                    "risk_assessment": "Low risk implementation...",
                    "success_metrics": ["Reduced cart abandonment by 20%"]
                }
            }
    
    claude_mcp_client = MockClaudeMCPClient()
    
    # Initialize the SDLC Agent Team
    agent_team = SDLCAgentTeam(claude_mcp_client)
    
    # Define a sample project: E-commerce Checkout Optimization
    project_context = {
        "project_name": "E-commerce Checkout Optimization",
        "business_goal": "Reduce cart abandonment by 20%",
        "current_metrics": {
            "cart_abandonment_rate": "68%",
            "average_checkout_time": "4.5 minutes",
            "mobile_conversion_rate": "1.2%"
        },
        "constraints": [
            "Must maintain existing payment gateway integration",
            "Should work on mobile devices",
            "Must comply with PCI DSS standards"
        ]
    }
    
    # Define tasks for the workflow
    tasks = [
        AgentTask(
            agent_type="product_manager",
            task_description="Analyze the current checkout process and design an optimized user flow that reduces cart abandonment by 20%",
            expected_output=[
                "User journey maps with pain points",
                "A/B testing hypotheses",
                "Success metrics and KPIs",
                "Technical requirements for implementation"
            ]
        ),
        AgentTask(
            agent_type="system_architect",
            task_description="Design the technical architecture for the optimized checkout system",
            expected_output=[
                "System architecture diagrams",
                "API specifications",
                "Database schema updates",
                "Integration patterns"
            ],
            dependencies=["product_manager"]
        ),
        AgentTask(
            agent_type="frontend_developer",
            task_description="Implement the checkout interface using React",
            expected_output=[
                "React components and hooks",
                "Responsive CSS implementations",
                "API integration code",
                "Unit tests and accessibility tests"
            ],
            dependencies=["system_architect"]
        ),
        AgentTask(
            agent_type="backend_developer",
            task_description="Implement the checkout API endpoints and payment processing",
            expected_output=[
                "RESTful API implementations",
                "Payment gateway integrations",
                "Database migrations",
                "Service layer implementations"
            ],
            dependencies=["system_architect"]
        ),
        AgentTask(
            agent_type="qa_engineer",
            task_description="Create comprehensive test coverage for the checkout feature",
            expected_output=[
                "Test automation scripts",
                "Manual testing scenarios",
                "Performance test suites",
                "Quality metrics dashboard"
            ],
            dependencies=["frontend_developer", "backend_developer"]
        )
    ]
    
    # Execute the workflow
    print("🚀 Starting SDLC Agent Team Workflow...")
    print(f"📋 Project: {project_context['project_name']}")
    print(f"🎯 Goal: {project_context['business_goal']}")
    print()
    
    # Execute tasks sequentially (since they have dependencies)
    results = await agent_team.execute_sequential_workflow(tasks, project_context)
    
    # Generate and display the report
    report = agent_team.generate_workflow_report()
    
    print("📊 Workflow Report:")
    print(f"   Total Tasks: {report['summary']['total_tasks']}")
    print(f"   Agents Used: {', '.join(report['summary']['agents_used'])}")
    print(f"   Average Quality Score: {report['summary']['average_quality_score']:.2f}")
    print(f"   Completion Time: {report['summary']['completion_time']:.2f} hours")
    print()
    
    print("🏆 Agent Performance:")
    for agent, perf in report['agent_performance'].items():
        print(f"   {agent}: {perf['tasks_completed']} tasks, {perf['average_quality']:.2f} avg quality")
    
    print()
    print("✅ Workflow completed successfully!")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
