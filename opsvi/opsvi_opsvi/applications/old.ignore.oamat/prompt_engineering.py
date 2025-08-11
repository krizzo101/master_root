"""
OAMAT Fractal Prompt Engineering System
Handles prompt inheritance, adaptation, and context-aware generation
across the fractal hierarchy levels.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from pydantic import BaseModel

from src.applications.oamat.context_abstraction import AbstractionLevel
from src.applications.oamat.models.workflow_models import AgentRole


class PromptPersonality(Enum):
    """Different prompt personalities for different hierarchy levels"""

    STRATEGIC_EXECUTIVE = "strategic_executive"  # Big picture, business-focused
    TACTICAL_MANAGER = "tactical_manager"  # Coordination and architecture
    OPERATIONAL_LEAD = "operational_lead"  # Implementation planning
    TECHNICAL_EXPERT = "technical_expert"  # Deep technical execution


@dataclass
class PromptContext:
    """Context information for prompt generation"""

    hierarchy_level: int
    abstraction_level: AbstractionLevel
    agent_role: AgentRole
    parent_context: str
    focused_request: str
    available_tools: List[str]
    complexity_score: int
    is_subdivision_candidate: bool
    execution_constraints: Dict[str, Any]


class FractalPromptTemplate(BaseModel):
    """Template for generating prompts at different fractal levels"""

    base_system_prompt: str
    role_specific_additions: Dict[AgentRole, str]
    level_specific_adaptations: Dict[AbstractionLevel, str]
    autonomy_instructions: str
    tool_usage_patterns: str
    subdivision_logic: str
    context_awareness_instructions: str


class FractalPromptEngineer:
    """
    Core prompt engineering system for OAMAT fractal architecture.
    Generates appropriate prompts for each level and role combination.
    """

    def __init__(self):
        self.prompt_templates = self._initialize_templates()
        self.personality_mappings = self._create_personality_mappings()

    def generate_fractal_prompt(
        self,
        context: PromptContext,
        user_request: str,
        parent_results: Optional[Dict] = None,
    ) -> ChatPromptTemplate:
        """
        Generate a complete prompt for an agent at a specific fractal level
        """

        # 1. Determine the appropriate prompt personality
        personality = self._determine_personality(context)

        # 2. Build the system prompt components
        system_components = self._build_system_components(context, personality)

        # 3. Create context-aware user message
        user_message = self._create_contextual_user_message(
            context, user_request, parent_results
        )

        # 4. Add tool usage instructions
        tool_instructions = self._generate_tool_instructions(context)

        # 5. Combine into final prompt
        return self._assemble_final_prompt(
            system_components, user_message, tool_instructions, context
        )

    def _determine_personality(self, context: PromptContext) -> PromptPersonality:
        """Determine appropriate prompt personality based on context"""

        if context.abstraction_level == AbstractionLevel.EXECUTIVE:
            return PromptPersonality.STRATEGIC_EXECUTIVE
        elif context.abstraction_level == AbstractionLevel.MANAGERIAL:
            return PromptPersonality.TACTICAL_MANAGER
        elif context.abstraction_level == AbstractionLevel.OPERATIONAL:
            return PromptPersonality.OPERATIONAL_LEAD
        else:  # TECHNICAL
            return PromptPersonality.TECHNICAL_EXPERT

    def _build_system_components(
        self, context: PromptContext, personality: PromptPersonality
    ) -> Dict[str, str]:
        """Build the system prompt components for the specific context"""

        components = {}

        # Base identity and personality
        components["identity"] = self._create_identity_prompt(context, personality)

        # Level-appropriate autonomy instructions
        components["autonomy"] = self._create_autonomy_instructions(context)

        # Context awareness and hierarchy positioning
        components["context_awareness"] = self._create_context_awareness(context)

        # Subdivision decision logic
        components["subdivision_logic"] = self._create_subdivision_logic(context)

        # Quality and standards enforcement
        components["quality_standards"] = self._create_quality_standards(context)

        return components

    def _create_identity_prompt(
        self, context: PromptContext, personality: PromptPersonality
    ) -> str:
        """Create identity and role definition based on personality"""

        role_name = context.agent_role.value.replace("_", " ").title()

        if personality == PromptPersonality.STRATEGIC_EXECUTIVE:
            return f"""
You are a Strategic {role_name} operating at the EXECUTIVE level of a sophisticated workflow orchestration system.

EXECUTIVE MINDSET:
- Think in terms of business outcomes and strategic impact
- Focus on high-level architecture and key decisions
- Coordinate multiple teams and major components
- Make decisions that affect the entire project scope
- Delegate detailed implementation to specialized teams

Your decisions shape the overall project direction and success.
"""

        elif personality == PromptPersonality.TACTICAL_MANAGER:
            return f"""
You are a Tactical {role_name} operating at the MANAGERIAL level of a workflow orchestration system.

MANAGERIAL MINDSET:
- Bridge between strategic vision and operational execution
- Make architectural and technology stack decisions
- Coordinate between different development streams
- Plan implementation approaches and resource allocation
- Ensure technical decisions align with business goals

You translate strategic requirements into executable plans.
"""

        elif personality == PromptPersonality.OPERATIONAL_LEAD:
            return f"""
You are an Operational {role_name} operating at the OPERATIONAL level of a workflow orchestration system.

OPERATIONAL MINDSET:
- Focus on detailed implementation planning and execution
- Make specific technical and design decisions
- Coordinate direct implementation activities
- Ensure quality, testing, and operational readiness
- Handle specific technical challenges and solutions

You turn plans into working implementations.
"""

        else:  # TECHNICAL_EXPERT
            return f"""
You are a Technical {role_name} operating at the TECHNICAL level of a workflow orchestration system.

TECHNICAL MINDSET:
- Execute specific technical tasks with deep expertise
- Write code, configure systems, implement solutions
- Handle detailed technical decisions and implementation
- Ensure technical quality and best practices
- Solve specific technical problems and challenges

You are the hands-on technical expert who builds the actual solutions.
"""

    def _create_autonomy_instructions(self, context: PromptContext) -> str:
        """Create level-appropriate autonomy instructions"""

        base_autonomy = """
AUTONOMOUS EXECUTION REQUIREMENTS:
1. **Complete Ownership**: You own this scope completely and must see it through to completion
2. **No External Dependencies**: Make all decisions within your scope autonomously
3. **Tool-First Approach**: Always use available tools rather than theoretical planning
4. **Evidence-Based Completion**: Provide concrete evidence that your work is complete
5. **Persistent Execution**: Continue until the objective is fully achieved
"""

        if context.is_subdivision_candidate:
            subdivision_autonomy = """
6. **Subdivision Authority**: You have full authority to subdivide complex work into focused sub-tasks
7. **Delegation Decisions**: Make autonomous decisions about when to delegate vs. execute directly
8. **Quality Orchestration**: Ensure all subdivided work meets your quality standards
"""
            return base_autonomy + subdivision_autonomy

        return (
            base_autonomy
            + """
6. **Direct Execution**: Execute this work directly using your technical expertise and available tools
"""
        )

    def _create_context_awareness(self, context: PromptContext) -> str:
        """Create context awareness instructions"""

        context_instruction = f"""
HIERARCHICAL CONTEXT AWARENESS:
- **Your Level**: {context.abstraction_level.name} (Level {context.hierarchy_level})
- **Your Scope**: {context.focused_request}
- **Parent Context**: {context.parent_context}
- **Complexity Score**: {context.complexity_score}/10

CONTEXT USAGE RULES:
1. Treat your focused request as a COMPLETE problem scope
2. Use parent context for alignment and constraints, not as your primary objective
3. Your success is measured by completing YOUR scope, not the entire parent project
4. Make decisions appropriate for your abstraction level
5. Escalate only critical issues that affect parent-level concerns
"""

        if context.hierarchy_level > 0:
            context_instruction += """

PARENT RELATIONSHIP:
- You are a specialized component of a larger system
- Your work will be integrated with other components at the parent level
- Focus on excellence in your domain rather than trying to solve everything
- Communicate results in terms appropriate for your parent's abstraction level
"""

        return context_instruction

    def _create_subdivision_logic(self, context: PromptContext) -> str:
        """Create subdivision decision logic"""

        if not context.is_subdivision_candidate:
            return """
EXECUTION APPROACH:
- Execute this work directly using your expertise and available tools
- Do not subdivide - you are responsible for hands-on implementation
"""

        return f"""
SUBDIVISION DECISION LOGIC:
Use this systematic approach to decide whether to subdivide:

1. **Complexity Assessment**:
   - Current complexity score: {context.complexity_score}/10
   - If score ≥ 7: Consider subdivision for specialized expertise
   - If score ≤ 6: Execute directly unless clear specialization benefits

2. **Specialization Benefits**:
   - Multiple distinct skill domains required (frontend + backend + mobile)
   - Parallel execution opportunities
   - Deep expertise in specific areas needed

3. **Subdivision Criteria**:
   ✅ SUBDIVIDE when:
   - Task requires 3+ distinct specialist roles
   - Components can work in parallel
   - Each component warrants dedicated focus

   ❌ DON'T SUBDIVIDE when:
   - You can handle it efficiently with your skillset
   - Coordination overhead exceeds specialization benefits
   - Task is primarily sequential in nature

4. **Subdivision Process**:
   - Break into focused, complete sub-problems
   - Each sub-problem should feel like a complete project to the sub-agent
   - Provide clear scope and success criteria for each subdivision
   - Maintain ownership of integration and final delivery
"""

    def _create_quality_standards(self, context: PromptContext) -> str:
        """Create quality standards appropriate for the level"""

        if context.abstraction_level == AbstractionLevel.EXECUTIVE:
            return """
EXECUTIVE QUALITY STANDARDS:
- Strategic alignment with business objectives
- Clear architectural decisions and rationale
- Risk identification and mitigation strategies
- Resource allocation and timeline realism
- Stakeholder communication and alignment
"""

        elif context.abstraction_level == AbstractionLevel.MANAGERIAL:
            return """
MANAGERIAL QUALITY STANDARDS:
- Technical architecture coherence and scalability
- Team coordination and resource optimization
- Implementation approach clarity and feasibility
- Integration planning and dependency management
- Quality assurance and testing strategy
"""

        elif context.abstraction_level == AbstractionLevel.OPERATIONAL:
            return """
OPERATIONAL QUALITY STANDARDS:
- Implementation completeness and correctness
- Code quality, documentation, and maintainability
- Testing coverage and operational readiness
- Performance and security considerations
- Deployment and monitoring capabilities
"""

        else:  # TECHNICAL
            return """
TECHNICAL QUALITY STANDARDS:
- Code excellence: clean, efficient, well-documented
- Best practices adherence and security implementation
- Comprehensive testing and error handling
- Performance optimization and resource efficiency
- Production readiness and operational excellence
"""

    def _create_contextual_user_message(
        self,
        context: PromptContext,
        user_request: str,
        parent_results: Optional[Dict] = None,
    ) -> str:
        """Create the user message with appropriate context"""

        message_parts = []

        # Primary objective
        message_parts.append(f"OBJECTIVE: {user_request}")

        # Context information
        if context.hierarchy_level > 0:
            message_parts.append(f"\nPARENT PROJECT CONTEXT: {context.parent_context}")

        # Previous results integration
        if parent_results:
            relevant_results = self._filter_results_for_level(parent_results, context)
            if relevant_results:
                message_parts.append(f"\nRELEVANT PRIOR RESULTS:\n{relevant_results}")

        # Execution constraints
        if context.execution_constraints:
            constraints_text = "\n".join(
                [
                    f"- {key}: {value}"
                    for key, value in context.execution_constraints.items()
                ]
            )
            message_parts.append(f"\nEXECUTION CONSTRAINTS:\n{constraints_text}")

        # Success criteria
        success_criteria = self._generate_success_criteria(context, user_request)
        message_parts.append(f"\nSUCCESS CRITERIA:\n{success_criteria}")

        return "\n".join(message_parts)

    def _generate_tool_instructions(self, context: PromptContext) -> str:
        """Generate tool usage instructions"""

        tool_categories = self._categorize_tools(context.available_tools)

        instructions = "TOOL USAGE STRATEGY:\n"

        if "research" in tool_categories:
            instructions += "- Use research tools early to understand requirements and best practices\n"

        if "code_generation" in tool_categories:
            instructions += "- Use code generation tools for implementation tasks\n"

        if "file_system" in tool_categories:
            instructions += (
                "- Use file system tools to organize and structure your work\n"
            )

        if "communication" in tool_categories:
            instructions += "- Use communication tools to coordinate with other agents when needed\n"

        instructions += "\nTOOL USAGE PRINCIPLES:\n"
        instructions += "1. Always prefer tool usage over theoretical planning\n"
        instructions += (
            "2. Use multiple tools in parallel when possible for efficiency\n"
        )
        instructions += "3. Validate results and gather evidence through tool usage\n"
        instructions += (
            "4. Document your tool usage for transparency and reproducibility\n"
        )

        return instructions

    def _assemble_final_prompt(
        self,
        system_components: Dict[str, str],
        user_message: str,
        tool_instructions: str,
        context: PromptContext,
    ) -> ChatPromptTemplate:
        """Assemble the final chat prompt template"""

        # Combine system components in logical order
        system_prompt = "\n\n".join(
            [
                system_components["identity"],
                system_components["autonomy"],
                system_components["context_awareness"],
                system_components["subdivision_logic"],
                system_components["quality_standards"],
                tool_instructions,
                "Now proceed with autonomous execution. Begin with a PLAN, then execute systematically.",
            ]
        )

        return ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_prompt),
                HumanMessagePromptTemplate.from_template(user_message),
            ]
        )

    def _filter_results_for_level(
        self, parent_results: Dict, context: PromptContext
    ) -> str:
        """Filter parent results appropriate for current level"""

        # This integrates with the context abstraction system
        if context.abstraction_level == AbstractionLevel.EXECUTIVE:
            # Only high-level strategic information
            return self._extract_strategic_info(parent_results)
        elif context.abstraction_level == AbstractionLevel.MANAGERIAL:
            # Tactical and architectural information
            return self._extract_tactical_info(parent_results)
        elif context.abstraction_level == AbstractionLevel.OPERATIONAL:
            # Implementation-focused information
            return self._extract_operational_info(parent_results)
        else:  # TECHNICAL
            # All relevant technical details
            return self._extract_technical_info(parent_results)

    def _generate_success_criteria(
        self, context: PromptContext, user_request: str
    ) -> str:
        """Generate specific success criteria for the request"""

        criteria = []

        if context.abstraction_level == AbstractionLevel.EXECUTIVE:
            criteria.extend(
                [
                    "Strategic objectives clearly defined and achievable",
                    "Key architectural decisions made and documented",
                    "Resource requirements and timeline established",
                    "Risk assessment completed with mitigation strategies",
                ]
            )

        elif context.abstraction_level == AbstractionLevel.MANAGERIAL:
            criteria.extend(
                [
                    "Technical approach defined and validated",
                    "Implementation plan created with clear milestones",
                    "Team coordination and resource allocation planned",
                    "Integration strategy established",
                ]
            )

        elif context.abstraction_level == AbstractionLevel.OPERATIONAL:
            criteria.extend(
                [
                    "Detailed implementation completed and tested",
                    "Documentation created and up-to-date",
                    "Quality standards met and validated",
                    "Operational readiness confirmed",
                ]
            )

        else:  # TECHNICAL
            criteria.extend(
                [
                    "All code written, tested, and documented",
                    "Best practices implemented and validated",
                    "Performance and security requirements met",
                    "Production deployment ready",
                ]
            )

        return "\n".join([f"- {criterion}" for criterion in criteria])

    def _categorize_tools(self, available_tools: List[str]) -> List[str]:
        """Categorize available tools for instruction generation"""
        categories = []

        research_tools = ["web_search", "academic_search", "knowledge_search"]
        code_tools = ["code_generation", "file_editor", "compiler"]
        file_tools = ["file_system", "directory_manager"]
        comm_tools = ["handoff", "communication", "notification"]

        if any(tool in available_tools for tool in research_tools):
            categories.append("research")
        if any(tool in available_tools for tool in code_tools):
            categories.append("code_generation")
        if any(tool in available_tools for tool in file_tools):
            categories.append("file_system")
        if any(tool in available_tools for tool in comm_tools):
            categories.append("communication")

        return categories

    def _extract_strategic_info(self, results: Dict) -> str:
        """Extract strategic information for executive level"""
        strategic_items = []

        if "decisions" in results:
            strategic_items.extend(results["decisions"][:3])  # Top 3 decisions
        if "business_impact" in results:
            strategic_items.append(f"Business Impact: {results['business_impact']}")
        if "risks" in results:
            critical_risks = [r for r in results["risks"] if "critical" in r.lower()]
            strategic_items.extend(critical_risks)

        return "\n".join([f"- {item}" for item in strategic_items])

    def _extract_tactical_info(self, results: Dict) -> str:
        """Extract tactical information for managerial level"""
        tactical_items = []

        if "architecture" in results:
            tactical_items.append(f"Architecture: {results['architecture']}")
        if "technology_stack" in results:
            tactical_items.append(f"Tech Stack: {results['technology_stack']}")
        if "implementation_approach" in results:
            tactical_items.append(f"Approach: {results['implementation_approach']}")

        return "\n".join([f"- {item}" for item in tactical_items])

    def _extract_operational_info(self, results: Dict) -> str:
        """Extract operational information for operational level"""
        operational_items = []

        if "implementation_details" in results:
            operational_items.extend(results["implementation_details"])
        if "testing_strategy" in results:
            operational_items.append(f"Testing: {results['testing_strategy']}")
        if "deployment_plan" in results:
            operational_items.append(f"Deployment: {results['deployment_plan']}")

        return "\n".join([f"- {item}" for item in operational_items])

    def _extract_technical_info(self, results: Dict) -> str:
        """Extract technical information for technical level"""
        # Technical level gets full details
        technical_items = []

        for key, value in results.items():
            if key in ["code", "configurations", "technical_specs", "error_logs"]:
                technical_items.append(f"{key}: {value}")

        return "\n".join([f"- {item}" for item in technical_items])

    def _initialize_templates(self) -> Dict[str, FractalPromptTemplate]:
        """Initialize prompt templates for different scenarios"""
        # This would contain pre-built templates for common patterns
        return {}

    def _create_personality_mappings(self) -> Dict[AbstractionLevel, PromptPersonality]:
        """Create mappings between abstraction levels and personalities"""
        return {
            AbstractionLevel.EXECUTIVE: PromptPersonality.STRATEGIC_EXECUTIVE,
            AbstractionLevel.MANAGERIAL: PromptPersonality.TACTICAL_MANAGER,
            AbstractionLevel.OPERATIONAL: PromptPersonality.OPERATIONAL_LEAD,
            AbstractionLevel.TECHNICAL: PromptPersonality.TECHNICAL_EXPERT,
        }


# Usage example for integration with OAMAT system
def example_fractal_prompt_generation():
    """Example of generating prompts for different fractal levels"""

    prompt_engineer = FractalPromptEngineer()

    # Executive level prompt
    executive_context = PromptContext(
        hierarchy_level=0,
        abstraction_level=AbstractionLevel.EXECUTIVE,
        agent_role=AgentRole.PROJECT_MANAGER,
        parent_context="",
        focused_request="Build a complete e-commerce platform",
        available_tools=["research", "planning", "coordination"],
        complexity_score=9,
        is_subdivision_candidate=True,
        execution_constraints={"timeline": "3 months", "budget": "$500K"},
    )

    executive_prompt = prompt_engineer.generate_fractal_prompt(
        context=executive_context,
        user_request="Build a complete e-commerce platform with user management, product catalog, shopping cart, and payment processing",
    )

    # Technical level prompt (after subdivision)
    technical_context = PromptContext(
        hierarchy_level=3,
        abstraction_level=AbstractionLevel.TECHNICAL,
        agent_role=AgentRole.BACKEND_DEVELOPER,
        parent_context="Build a complete e-commerce platform",
        focused_request="Implement user authentication system",
        available_tools=["code_generation", "file_system", "testing"],
        complexity_score=4,
        is_subdivision_candidate=False,
        execution_constraints={"framework": "FastAPI", "database": "PostgreSQL"},
    )

    technical_prompt = prompt_engineer.generate_fractal_prompt(
        context=technical_context,
        user_request="Implement user authentication system with JWT tokens, password hashing, and session management",
    )

    return executive_prompt, technical_prompt
