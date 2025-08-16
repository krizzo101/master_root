"""
CrewAI Agent Coordination Example for ASEA Next-Generation Orchestration Platform
Standards Compliance: Rule 951 (CrewAI Technical Guidelines)

This example demonstrates a production-ready CrewAI implementation following
all established standards for role-based agent coordination.
"""

import asyncio
import json
import structlog
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew, Process
from crewai.memory import ShortTermMemory, LongTermMemory
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# Configure structured logging (Rule 921)
logger = structlog.get_logger()


class AgentRole(str, Enum):
    """Predefined agent roles for the coordination system."""

    COORDINATOR = "coordinator"
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    VALIDATOR = "validator"
    REPORTER = "reporter"


class TaskPriority(str, Enum):
    """Task priority levels for agent coordination."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MessageType(str, Enum):
    """Message types for agent communication."""

    TASK_ASSIGNMENT = "task_assignment"
    PROGRESS_UPDATE = "progress_update"
    RESULT_SUBMISSION = "result_submission"
    ERROR_REPORT = "error_report"
    COORDINATION_REQUEST = "coordination_request"


@dataclass
class MessageEnvelope:
    """
    JSON message envelope for agent communication (Rule 951).

    Provides structured communication format with proper metadata
    and error handling capabilities.
    """

    message_id: str
    message_type: MessageType
    sender_agent: str
    recipient_agent: Optional[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    retry_count: int = 0
    max_retries: int = 2  # Rule 951: Max 2 retries

    def to_json(self) -> str:
        """Convert message to JSON format."""
        return json.dumps(
            {
                "message_id": self.message_id,
                "message_type": self.message_type.value,
                "sender_agent": self.sender_agent,
                "recipient_agent": self.recipient_agent,
                "timestamp": self.timestamp.isoformat(),
                "correlation_id": self.correlation_id,
                "payload": self.payload,
                "priority": self.priority.value,
                "retry_count": self.retry_count,
                "max_retries": self.max_retries,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "MessageEnvelope":
        """Create message from JSON string."""
        data = json.loads(json_str)
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["message_type"]),
            sender_agent=data["sender_agent"],
            recipient_agent=data.get("recipient_agent"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id", ""),
            payload=data.get("payload", {}),
            priority=TaskPriority(data.get("priority", "normal")),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 2),
        )


class CoordinationTools:
    """Tools available to all agents in the coordination system."""

    @staticmethod
    @tool
    def send_message(message_envelope: str) -> Dict[str, Any]:
        """Send structured message between agents."""
        try:
            envelope = MessageEnvelope.from_json(message_envelope)

            logger.info(
                "agent.message.sent",
                message_id=envelope.message_id,
                sender=envelope.sender_agent,
                recipient=envelope.recipient_agent,
                message_type=envelope.message_type.value,
                correlation_id=envelope.correlation_id,
            )

            # Simulate message delivery
            return {
                "status": "delivered",
                "message_id": envelope.message_id,
                "delivery_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("agent.message.send_failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    @staticmethod
    @tool
    def analyze_data(data_source: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze data using specified analysis type."""
        try:
            # Simulate data analysis
            results = {
                "data_source": data_source,
                "analysis_type": analysis_type,
                "findings": [
                    "Data quality is 95% complete",
                    "Identified 3 key patterns",
                    "Recommended 2 optimization strategies",
                ],
                "metrics": {
                    "processing_time": 2.5,
                    "accuracy_score": 0.94,
                    "confidence_level": 0.89,
                },
                "recommendations": [
                    "Implement data cleaning pipeline",
                    "Add real-time monitoring",
                ],
            }

            logger.info(
                "agent.analysis.completed",
                data_source=data_source,
                analysis_type=analysis_type,
                findings_count=len(results["findings"]),
            )

            return results

        except Exception as e:
            logger.error("agent.analysis.failed", data_source=data_source, error=str(e))
            raise

    @staticmethod
    @tool
    def research_topic(topic: str, depth: str = "standard") -> Dict[str, Any]:
        """Research a specific topic with configurable depth."""
        try:
            # Simulate research process
            research_results = {
                "topic": topic,
                "depth": depth,
                "sources": [
                    "Academic papers: 15 relevant studies",
                    "Industry reports: 8 recent publications",
                    "Expert interviews: 3 domain experts",
                ],
                "key_insights": [
                    f"Latest trends in {topic}",
                    f"Best practices for {topic} implementation",
                    f"Common challenges in {topic} adoption",
                ],
                "confidence_score": 0.87,
                "research_duration": "45 minutes",
            }

            logger.info(
                "agent.research.completed",
                topic=topic,
                depth=depth,
                sources_count=len(research_results["sources"]),
            )

            return research_results

        except Exception as e:
            logger.error("agent.research.failed", topic=topic, error=str(e))
            raise

    @staticmethod
    @tool
    def validate_results(results_data: str) -> Dict[str, Any]:
        """Validate analysis or research results."""
        try:
            data = json.loads(results_data)

            # Validation logic
            validation_checks = {
                "data_completeness": len(data.get("findings", [])) > 0,
                "metric_validity": "metrics" in data,
                "recommendation_quality": len(data.get("recommendations", [])) > 0,
                "confidence_threshold": data.get("confidence_score", 0) > 0.7,
            }

            validation_passed = all(validation_checks.values())

            validation_result = {
                "validation_status": "passed" if validation_passed else "failed",
                "checks_performed": validation_checks,
                "overall_score": sum(validation_checks.values())
                / len(validation_checks),
                "validated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                "agent.validation.completed",
                validation_status=validation_result["validation_status"],
                overall_score=validation_result["overall_score"],
            )

            return validation_result

        except Exception as e:
            logger.error("agent.validation.failed", error=str(e))
            raise


class ASEAAgentCreator:
    """
    Factory for creating role-based agents following Rule 951 patterns.

    Implements:
    - Role-based patterns with clear definitions
    - Memory enabled for all agents
    - Structured communication capabilities
    """

    def __init__(self):
        # Initialize LLM with appropriate model (Rule 953)
        self.llm = ChatOpenAI(
            model="gpt-4", temperature=0.1, max_retries=2, timeout=30.0
        )

        # Shared tools for all agents
        self.tools = CoordinationTools()
        self.shared_tools = [
            self.tools.send_message,
            self.tools.analyze_data,
            self.tools.research_topic,
            self.tools.validate_results,
        ]

    def create_coordinator_agent(self) -> Agent:
        """Create coordinator agent for multi-agent orchestration."""
        return Agent(
            role="Project Coordinator",
            goal="Orchestrate multi-agent workflows and ensure task completion",
            backstory="""You are an experienced project coordinator specializing in 
            multi-agent workflow orchestration. Your expertise lies in task assignment, 
            progress monitoring, and ensuring all agents work together effectively to 
            achieve project objectives. You excel at communication, priority management, 
            and conflict resolution.""",
            verbose=True,
            memory=True,  # Rule 951: Memory enabled
            tools=self.shared_tools,
            llm=self.llm,
            max_iter=3,  # Limit iterations for reliability
            max_retry=2,  # Rule 951: Max 2 retries
            system_template="""You are a coordinator agent. Always communicate using 
            JSON message envelopes and maintain awareness of all agent activities. 
            Prioritize tasks based on business impact and coordinate resources 
            efficiently.""",
        )

    def create_analyst_agent(self) -> Agent:
        """Create data analyst agent."""
        return Agent(
            role="Data Analyst",
            goal="Analyze data, identify patterns, and provide actionable insights",
            backstory="""You are a skilled data analyst with expertise in statistical 
            analysis, pattern recognition, and data visualization. You excel at 
            transforming raw data into meaningful insights and recommendations. Your 
            analytical approach is methodical, detail-oriented, and results-focused.""",
            verbose=True,
            memory=True,  # Rule 951: Memory enabled
            tools=self.shared_tools,
            llm=self.llm,
            max_iter=3,
            max_retry=2,  # Rule 951: Max 2 retries
            system_template="""You are a data analyst agent. Focus on thorough 
            analysis, accurate metrics calculation, and clear communication of findings. 
            Always validate your results and provide confidence scores.""",
        )

    def create_researcher_agent(self) -> Agent:
        """Create research specialist agent."""
        return Agent(
            role="Research Specialist",
            goal="Conduct comprehensive research and gather relevant information",
            backstory="""You are a dedicated research specialist with extensive 
            experience in information gathering, source validation, and knowledge 
            synthesis. You have access to diverse information sources and excel at 
            finding relevant, up-to-date, and credible information on any topic.""",
            verbose=True,
            memory=True,  # Rule 951: Memory enabled
            tools=self.shared_tools,
            llm=self.llm,
            max_iter=3,
            max_retry=2,  # Rule 951: Max 2 retries
            system_template="""You are a research specialist agent. Conduct thorough 
            research, cite credible sources, and provide comprehensive insights. 
            Always assess the reliability and recency of your information sources.""",
        )

    def create_validator_agent(self) -> Agent:
        """Create validation specialist agent."""
        return Agent(
            role="Quality Validator",
            goal="Validate results, ensure quality standards, and verify accuracy",
            backstory="""You are a meticulous quality validator with expertise in 
            result verification, accuracy assessment, and quality assurance. You have 
            a keen eye for detail and extensive experience in validating complex 
            analytical and research outputs.""",
            verbose=True,
            memory=True,  # Rule 951: Memory enabled
            tools=self.shared_tools,
            llm=self.llm,
            max_iter=3,
            max_retry=2,  # Rule 951: Max 2 retries
            system_template="""You are a quality validator agent. Apply rigorous 
            validation criteria, check for consistency and accuracy, and provide 
            detailed feedback on quality improvements.""",
        )

    def create_reporter_agent(self) -> Agent:
        """Create report generation agent."""
        return Agent(
            role="Report Generator",
            goal="Synthesize information and create comprehensive reports",
            backstory="""You are an expert report writer with skills in information 
            synthesis, clear communication, and professional documentation. You excel 
            at transforming complex analytical and research findings into clear, 
            actionable reports for stakeholders.""",
            verbose=True,
            memory=True,  # Rule 951: Memory enabled
            tools=self.shared_tools,
            llm=self.llm,
            max_iter=3,
            max_retry=2,  # Rule 951: Max 2 retries
            system_template="""You are a report generator agent. Create clear, 
            well-structured reports that synthesize all findings and provide 
            actionable recommendations. Ensure executive summaries and detailed 
            technical sections are balanced.""",
        )


class CrewAICoordinator:
    """
    Production-ready CrewAI coordination system implementing Rule 951 guidelines.

    Features:
    - Role-based agent patterns
    - JSON message envelope communication
    - Memory-enabled agents
    - Coordinator agent pattern
    - Error handling with max 2 retries
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self.agent_creator = ASEAAgentCreator()
        self.message_history: List[MessageEnvelope] = []

        # Create agents using role-based patterns
        self.agents = {
            AgentRole.COORDINATOR: self.agent_creator.create_coordinator_agent(),
            AgentRole.ANALYST: self.agent_creator.create_analyst_agent(),
            AgentRole.RESEARCHER: self.agent_creator.create_researcher_agent(),
            AgentRole.VALIDATOR: self.agent_creator.create_validator_agent(),
            AgentRole.REPORTER: self.agent_creator.create_reporter_agent(),
        }

        logger.info(
            "crewai.coordinator.initialized",
            debug_mode=debug,
            agents_count=len(self.agents),
        )

    def create_message_envelope(
        self,
        message_type: MessageType,
        sender_agent: str,
        payload: Dict[str, Any],
        recipient_agent: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        correlation_id: str = "",
    ) -> MessageEnvelope:
        """Create structured message envelope for agent communication."""

        message_id = (
            f"msg_{int(datetime.utcnow().timestamp())}_{len(self.message_history)}"
        )

        envelope = MessageEnvelope(
            message_id=message_id,
            message_type=message_type,
            sender_agent=sender_agent,
            recipient_agent=recipient_agent,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id
            or f"coord_{int(datetime.utcnow().timestamp())}",
        )

        self.message_history.append(envelope)
        return envelope

    async def execute_analysis_workflow(
        self,
        project_id: str,
        data_source: str,
        research_topic: str,
        correlation_id: str = "",
    ) -> Dict[str, Any]:
        """
        Execute a comprehensive analysis workflow with agent coordination.

        This workflow demonstrates the coordinator agent pattern with:
        1. Task assignment and coordination
        2. Parallel execution of analysis and research
        3. Result validation and quality assurance
        4. Final report generation
        """
        try:
            logger.info(
                "workflow.analysis.started",
                project_id=project_id,
                data_source=data_source,
                research_topic=research_topic,
                correlation_id=correlation_id,
            )

            # Create tasks with proper dependencies
            coordination_task = Task(
                description=f"""
                Coordinate a comprehensive analysis workflow for project {project_id}.
                
                Your responsibilities:
                1. Oversee the analysis of data source: {data_source}
                2. Monitor research on topic: {research_topic}
                3. Ensure quality validation of all results
                4. Coordinate final report generation
                
                Use JSON message envelopes for all agent communication.
                Send progress updates and coordinate task dependencies.
                Ensure all tasks complete successfully before proceeding to report generation.
                """,
                agent=self.agents[AgentRole.COORDINATOR],
                expected_output="Coordination summary with task status and agent communications",
            )

            analysis_task = Task(
                description=f"""
                Perform comprehensive data analysis on: {data_source}
                
                Requirements:
                1. Analyze data quality and completeness
                2. Identify key patterns and trends
                3. Calculate relevant metrics and statistics
                4. Provide actionable recommendations
                5. Include confidence scores for all findings
                
                Communicate results using structured JSON format.
                Coordinate with the validator for quality assurance.
                """,
                agent=self.agents[AgentRole.ANALYST],
                expected_output="Detailed analysis results with findings, metrics, and recommendations",
            )

            research_task = Task(
                description=f"""
                Conduct comprehensive research on: {research_topic}
                
                Requirements:
                1. Gather information from credible sources
                2. Identify latest trends and best practices
                3. Analyze industry insights and expert opinions
                4. Provide contextual background and implications
                5. Assess information reliability and recency
                
                Present findings in structured format with source citations.
                Coordinate with the validator for accuracy verification.
                """,
                agent=self.agents[AgentRole.RESEARCHER],
                expected_output="Research findings with sources, insights, and contextual analysis",
            )

            validation_task = Task(
                description="""
                Validate all analysis and research results for quality and accuracy.
                
                Requirements:
                1. Review analysis findings for statistical validity
                2. Verify research sources and citations
                3. Check consistency across all results
                4. Assess overall quality and reliability
                5. Provide improvement recommendations if needed
                
                Communicate validation results with detailed feedback.
                Ensure all results meet quality standards before final reporting.
                """,
                agent=self.agents[AgentRole.VALIDATOR],
                expected_output="Validation report with quality assessment and recommendations",
                dependencies=[analysis_task, research_task],
            )

            reporting_task = Task(
                description=f"""
                Generate comprehensive final report for project {project_id}.
                
                Requirements:
                1. Synthesize all analysis and research findings
                2. Create executive summary with key insights
                3. Include detailed technical sections
                4. Provide clear actionable recommendations
                5. Ensure professional formatting and clarity
                
                Structure the report for both technical and executive audiences.
                Include all validation feedback and quality assessments.
                """,
                agent=self.agents[AgentRole.REPORTER],
                expected_output="Final comprehensive report with executive summary and technical details",
                dependencies=[validation_task],
            )

            # Create crew with hierarchical process (coordinator pattern)
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=[
                    coordination_task,
                    analysis_task,
                    research_task,
                    validation_task,
                    reporting_task,
                ],
                process=Process.hierarchical,  # Coordinator agent pattern
                manager_llm=self.agent_creator.llm,
                verbose=self.debug,
                memory=True,  # Rule 951: Memory enabled
                embedder={
                    "provider": "openai",
                    "config": {"model": "text-embedding-ada-002"},
                },
            )

            # Execute workflow
            start_time = datetime.utcnow()
            result = crew.kickoff()
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Structure final output
            workflow_result = {
                "project_id": project_id,
                "execution_summary": {
                    "status": "completed",
                    "execution_time": execution_time,
                    "tasks_completed": len(crew.tasks),
                    "agents_involved": len(crew.agents),
                },
                "results": {
                    "coordination_summary": str(coordination_task.output)
                    if coordination_task.output
                    else "",
                    "analysis_findings": str(analysis_task.output)
                    if analysis_task.output
                    else "",
                    "research_insights": str(research_task.output)
                    if research_task.output
                    else "",
                    "validation_report": str(validation_task.output)
                    if validation_task.output
                    else "",
                    "final_report": str(reporting_task.output)
                    if reporting_task.output
                    else "",
                },
                "message_history": [
                    msg.to_json() for msg in self.message_history[-10:]
                ],  # Last 10 messages
                "correlation_id": correlation_id,
                "completed_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                "workflow.analysis.completed",
                project_id=project_id,
                execution_time=execution_time,
                correlation_id=correlation_id,
            )

            return workflow_result

        except Exception as e:
            logger.error(
                "workflow.analysis.failed",
                project_id=project_id,
                error=str(e),
                correlation_id=correlation_id,
            )

            return {
                "project_id": project_id,
                "execution_summary": {
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.utcnow().isoformat(),
                },
                "correlation_id": correlation_id,
            }

    async def execute_rapid_prototype_workflow(
        self, prototype_id: str, requirements: Dict[str, Any], correlation_id: str = ""
    ) -> Dict[str, Any]:
        """
        Demonstrate rapid prototyping capabilities of CrewAI.

        This workflow shows how CrewAI enables quick iteration and
        prototype development with minimal setup.
        """
        try:
            logger.info(
                "workflow.prototype.started",
                prototype_id=prototype_id,
                correlation_id=correlation_id,
            )

            # Simple prototype task with minimal agents
            prototype_task = Task(
                description=f"""
                Create a rapid prototype based on these requirements:
                {json.dumps(requirements, indent=2)}
                
                Focus on:
                1. Core functionality identification
                2. Technical approach recommendation
                3. Implementation timeline estimate
                4. Resource requirements assessment
                
                Provide a clear, actionable prototype plan.
                """,
                agent=self.agents[AgentRole.ANALYST],
                expected_output="Prototype plan with technical approach and timeline",
            )

            # Minimal crew for rapid execution
            prototype_crew = Crew(
                agents=[self.agents[AgentRole.ANALYST]],
                tasks=[prototype_task],
                process=Process.sequential,
                verbose=self.debug,
            )

            # Quick execution
            start_time = datetime.utcnow()
            result = prototype_crew.kickoff()
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            prototype_result = {
                "prototype_id": prototype_id,
                "execution_time": execution_time,
                "status": "completed",
                "prototype_plan": str(result),
                "correlation_id": correlation_id,
                "completed_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                "workflow.prototype.completed",
                prototype_id=prototype_id,
                execution_time=execution_time,
            )

            return prototype_result

        except Exception as e:
            logger.error(
                "workflow.prototype.failed", prototype_id=prototype_id, error=str(e)
            )
            raise


# Example usage and testing
async def example_crewai_coordination():
    """Example demonstrating CrewAI coordination capabilities."""

    # Initialize coordinator with debug mode
    coordinator = CrewAICoordinator(debug=True)

    # Example 1: Full analysis workflow
    print("=== Full Analysis Workflow ===")
    analysis_result = await coordinator.execute_analysis_workflow(
        project_id="analysis_project_001",
        data_source="customer_satisfaction_survey",
        research_topic="customer experience optimization",
        correlation_id="req_20241226_crewai_001",
    )

    print(f"Analysis Status: {analysis_result['execution_summary']['status']}")
    print(
        f"Execution Time: {analysis_result['execution_summary'].get('execution_time', 0):.2f} seconds"
    )
    print(
        f"Tasks Completed: {analysis_result['execution_summary'].get('tasks_completed', 0)}"
    )

    # Example 2: Rapid prototyping
    print("\n=== Rapid Prototyping Workflow ===")
    prototype_requirements = {
        "feature": "real-time dashboard",
        "technology": "React + WebSocket",
        "timeline": "2 weeks",
        "team_size": "3 developers",
    }

    prototype_result = await coordinator.execute_rapid_prototype_workflow(
        prototype_id="dashboard_prototype_001",
        requirements=prototype_requirements,
        correlation_id="req_20241226_prototype_001",
    )

    print(f"Prototype Status: {prototype_result['status']}")
    print(f"Execution Time: {prototype_result['execution_time']:.2f} seconds")

    return analysis_result, prototype_result


if __name__ == "__main__":
    # Run example CrewAI coordination
    asyncio.run(example_crewai_coordination())
