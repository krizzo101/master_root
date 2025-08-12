"""
OAMAT Request Analyzer Module

Handles sophisticated analysis of user requests with comprehensive understanding.
Extracted from manager.py for better modularity and maintainability.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.applications.oamat.agents.llm_base_agent import LLMBaseAgent
from src.applications.oamat.agents.models import (
    EnhancedRequestAnalysis,
    ExpandedPrompt,
)
from src.applications.oamat.agents.registry import SYSTEM_IDENTITY

logger = logging.getLogger("OAMAT.RequestAnalyzer")


class UserContext(BaseModel):
    scope: str = Field(..., description="personal, team, or enterprise level")
    experience_level: str = Field(..., description="beginner, intermediate, or expert")
    time_constraints: Optional[str] = Field(None, description="Any urgency indicators")
    specific_constraints: List[str] = Field(
        default_factory=list, description="Budget, technology, or other limitations"
    )


class ContextAnalysis(BaseModel):
    primary_domain: str = Field(
        ..., description="Main field/industry/technology domain"
    )
    complexity_level: str = Field(
        ..., description="low_complexity, moderate_complexity, or high_complexity"
    )
    task_type: str = Field(
        ..., description="development, analysis, design, optimization, or consultation"
    )
    user_context: UserContext
    specialized_requirements: List[str] = Field(default_factory=list)
    inferred_technologies: List[str] = Field(default_factory=list)
    suggested_approach: str = Field(
        ..., description="Brief description of recommended approach"
    )


class RequestAnalyzer:
    """
    Sophisticated request analysis component that understands user intent,
    scope, and technical requirements.
    """

    def __init__(self, llm_base_agent: LLMBaseAgent):
        self.llm_base_agent = llm_base_agent
        self.logger = logger

    def analyze_task_context(
        self, user_request: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze the user request using LLM to determine actual requirements rather than keyword matching.
        This replaces the hardcoded domain detection with intelligent analysis.

        Args:
            user_request: The user's request
            context: Additional context information

        Returns:
            Task context dictionary with intelligent analysis of requirements
        """

        analysis_prompt = f"""
Analyze this user request to determine what expertise, approach, and context are needed:

USER REQUEST: "{user_request}"

ADDITIONAL CONTEXT: {json.dumps(context or {}, indent=2)}

Provide analysis in the following areas:

1. **PRIMARY DOMAIN**: What is the main field/industry/technology domain this request falls into?

2. **COMPLEXITY ASSESSMENT**: Based on the request language and scope, what complexity level is appropriate?
   - low_complexity: Simple, straightforward tasks
   - moderate_complexity: Standard professional work with some challenges
   - high_complexity: Advanced, sophisticated, or enterprise-level requirements

3. **TASK TYPE**: What type of work is being requested?
   - development: Building, creating, implementing something
   - analysis: Research, investigation, evaluation
   - design: Planning, architecture, conceptual work
   - optimization: Improving, enhancing existing systems
   - consultation: Advice, recommendations, guidance

4. **USER CONTEXT CLUES**: What can you infer about the user from their request?
   - scope: personal, team, or enterprise level
   - experience_level: beginner, intermediate, or expert (based on terminology used)
   - time_constraints: any urgency indicators
   - specific_constraints: budget, technology, or other limitations mentioned

5. **SPECIALIZED REQUIREMENTS**: What specific knowledge, tools, or considerations are needed?

Respond with a JSON object containing your analysis that adheres to the `ContextAnalysis` schema.
"""
        messages = [
            SystemMessage(content=SYSTEM_IDENTITY),
            HumanMessage(content=analysis_prompt),
        ]

        context_analysis = self.llm_base_agent.llm_call(
            messages, response_format=ContextAnalysis
        )

        if isinstance(context_analysis, ContextAnalysis):
            return context_analysis.model_dump()
        else:
            # If the LLM call fails to return the expected Pydantic object,
            # it will now raise an exception, which is the desired behavior.
            raise ValueError("LLM call did not return a valid ContextAnalysis object.")

    def analyze_request(
        self,
        user_request: str,
        context: Dict[str, Any] = None,
        dynamic_identity: str = None,
    ) -> EnhancedRequestAnalysis:
        """
        Perform sophisticated analysis of user request with comprehensive understanding.

        This method applies deep understanding of OAMAT capabilities to analyze
        user requests and generate sophisticated insights for workflow planning.
        """

        # Use provided dynamic identity or fall back to system identity
        system_identity = dynamic_identity or SYSTEM_IDENTITY

        analysis_prompt = f"""
{system_identity}

COMPREHENSIVE REQUEST ANALYSIS TASK:
Analyze the user's request to understand their true requirements, scope, and technical approach.

Transform their request into a detailed understanding that includes:
1. Clear objective and scope
2. Detailed deliverables and requirements
3. Technical architecture decisions
4. Strategic clarification questions
5. Risk assessment and success criteria

ANALYSIS REQUIREMENTS:

**CONSERVATIVE INFERENCE PRINCIPLES:**
- Only infer details when the request provides clear context
- When multiple architectural approaches are reasonable, require clarification
- Distinguish between what the user explicitly stated vs. what you're assuming
- Focus on high-impact decisions that significantly affect the solution

**REQUIRE CLARIFICATION WHEN:**
- Multiple valid architectural approaches exist
- Target audience is unclear
- Integration requirements are ambiguous
- Usage context is not specified
- Performance, security, or scale requirements are unspecified

**CRITICAL AMBIGUITY SIGNALS:**
- Requests without specifying how the solution will be used
- Missing integration details
- Unclear audience or user base
- Vague scope indicators without specifics

**HIGH-IMPACT CLARIFICATIONS (focus on these types):**
- Usage patterns: interactive vs automated vs integrated
- Target users: personal vs team vs external vs public
- Integration approach: standalone vs integrated vs service
- Access method: user interface vs programmatic vs hybrid

**STRATEGIC UNDERSTANDING FRAMEWORK:**

**PURPOSE & CONTEXT (Critical):**
- What problem is being solved and why?
- Who will use this and in what context?
- How does this fit into existing workflows?
- What does success look like?

**USAGE & INTEGRATION (Critical):**
- Will this be used interactively or automated?
- Is this standalone or integrated with other systems?
- What's the expected usage pattern?
- How will users or systems interact with this?

**SCOPE & COMPLEXITY (Critical):**
- What is the core functionality vs additional features?
- What level of sophistication is appropriate?
- What are the immediate vs long-term needs?
- What constraints or requirements exist?

**TECHNICAL APPROACH (Moderate Impact):**
- Are there specific technology preferences or constraints?
- What are the data handling and persistence needs?
- What security and compliance requirements exist?
- What performance and reliability standards apply?

USER REQUEST: "{user_request}"

CONTEXT: {json.dumps(context or {}, indent=2)}

Generate a comprehensive analysis following the EnhancedRequestAnalysis schema.
"""

        try:
            messages = [
                SystemMessage(content=SYSTEM_IDENTITY),
                HumanMessage(content=analysis_prompt),
            ]

            # Use structured response with EnhancedRequestAnalysis Pydantic model
            result = self.llm_base_agent.llm_call(
                messages, response_format=EnhancedRequestAnalysis
            )

            if isinstance(result, EnhancedRequestAnalysis):
                self.logger.info(
                    "✅ Successfully analyzed request with comprehensive understanding"
                )
                return result
            else:
                raise ValueError(
                    "Structured response was not of the expected EnhancedRequestAnalysis type."
                )

        except Exception as e:
            self.logger.error(f"Request analysis failed: {e}")
            # No fallbacks - let the failure propagate
            raise RuntimeError(f"Request analysis failed: {str(e)}")

    def analyze_user_request(
        self,
        user_request: str,
        context: Dict[str, Any] = None,
        dynamic_identity: str = None,
    ) -> ExpandedPrompt:
        """
        Analyzes the request to understand requirements rather than just expanding text.

        1. Analyzes the request to understand true requirements and scope
        2. Identifies technical architecture decisions needed
        3. Generates strategic clarification questions
        4. Assesses risks and defines success criteria
        """

        # Use provided dynamic identity or fall back to system identity
        system_identity = dynamic_identity or SYSTEM_IDENTITY

        expansion_prompt = f"""
{system_identity}

COMPREHENSIVE REQUEST ANALYSIS TASK:
Analyze the user's request to understand their true requirements, scope, and technical approach.

Transform their request into a detailed understanding that includes:
1. Clear objective and scope
2. Detailed deliverables and requirements
3. Technical architecture decisions
4. Strategic clarification questions
5. Risk assessment and success criteria

ANALYSIS REQUIREMENTS:

**CONSERVATIVE INFERENCE PRINCIPLES:**
- Only infer details when the request provides clear context
- When multiple architectural approaches are reasonable, require clarification
- Distinguish between what the user explicitly stated vs. what you're assuming
- Focus on high-impact decisions that significantly affect the solution

**REQUIRE CLARIFICATION WHEN:**
- Multiple valid architectural approaches exist
- Target audience is unclear
- Integration requirements are ambiguous
- Usage context is not specified
- Performance, security, or scale requirements are unspecified

**CRITICAL AMBIGUITY SIGNALS:**
- Requests without specifying how the solution will be used
- Missing integration details
- Unclear audience or user base
- Vague scope indicators without specifics

**HIGH-IMPACT CLARIFICATIONS (focus on these types):**
- Usage patterns: interactive vs automated vs integrated
- Target users: personal vs team vs external vs public
- Integration approach: standalone vs integrated vs service
- Access method: user interface vs programmatic vs hybrid

**STRATEGIC UNDERSTANDING FRAMEWORK:**

**PURPOSE & CONTEXT (Critical):**
- What problem is being solved and why?
- Who will use this and in what context?
- How does this fit into existing workflows?
- What does success look like?

**USAGE & INTEGRATION (Critical):**
- Will this be used interactively or automated?
- Is this standalone or integrated with other systems?
- What's the expected usage pattern?
- How will users or systems interact with this?

**SCOPE & COMPLEXITY (Critical):**
- What is the core functionality vs additional features?
- What level of sophistication is appropriate?
- What are the immediate vs long-term needs?
- What constraints or requirements exist?

**TECHNICAL APPROACH (Moderate Impact):**
- Are there specific technology preferences or constraints?
- What are the data handling and persistence needs?
- What security and compliance requirements exist?
- What performance and reliability standards apply?

USER REQUEST: "{user_request}"
CONTEXT: {json.dumps(context or {}, indent=2)}

Generate a comprehensive analysis that identifies what we know vs. what needs clarification.
"""

        try:
            messages = [
                SystemMessage(content=SYSTEM_IDENTITY),
                HumanMessage(content=expansion_prompt),
            ]

            result = self.llm_base_agent.llm_call(
                messages, response_format=ExpandedPrompt
            )

            if isinstance(result, ExpandedPrompt):
                self.logger.info(
                    "✅ Successfully analyzed user request and identified requirements"
                )
                return result
            else:
                raise ValueError(
                    "Structured response format not received for expanded prompt"
                )

        except Exception as e:
            self.logger.error(f"User request analysis failed: {e}")
            # No fallbacks - let the failure propagate
            raise RuntimeError(f"User request analysis failed: {str(e)}")
