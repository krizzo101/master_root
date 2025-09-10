#!/usr/bin/env python3
"""
Sounding Board MCP Server - Proactive review system for plans and decisions.
Agents must reach 80% confidence before allowing execution.
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add paths
sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/apps")

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any  # Add Any import

# Import OpenAI for real LLM integration
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("ERROR: OpenAI library required. Install with: pip install openai")
    sys.exit(1)


class ProposalData(BaseModel):
    """Structure for proposals submitted for review"""
    
    plan: str = Field(description="Detailed plan or design")
    code_samples: Optional[str] = Field(None, description="Code examples if applicable")
    documentation: Optional[str] = Field(None, description="Supporting documentation")
    test_strategy: Optional[str] = Field(None, description="How you'll test this")
    evidence: List[str] = Field(default_factory=list, description="Evidence supporting the plan")
    context: Optional[str] = Field(None, description="Additional context")
    iteration: int = Field(1, description="Which iteration of this proposal")
    counter_proposal: Optional['ProposalData'] = Field(None, description="Counter-proposal from agents")
    confidence_score: Optional[float] = Field(None, description="Confidence in this proposal (0-100)")


class AgentResponse(BaseModel):
    """Response from an individual agent"""
    
    agent_name: str
    confidence: int = Field(ge=0, le=100, description="Confidence percentage")
    concerns: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)
    coaching: Optional[str] = Field(None)
    reasoning: str = Field(description="Agent's reasoning")
    counter_proposal: Optional[str] = Field(None, description="Counter-proposal if confidence < 80%")


class ConsensusResult(BaseModel):
    """Result of consensus evaluation"""
    
    approved: bool
    overall_confidence: int
    violations_confidence: int
    coach_confidence: int
    iteration: int
    total_time: float
    agents_feedback: List[AgentResponse]
    next_steps: Optional[str] = None
    rejection_reason: Optional[str] = None
    counter_proposal: Optional[ProposalData] = Field(None, description="Counter-proposal if not approved")
    requester_confidence: Optional[float] = Field(None, description="Requester's confidence in counter-proposal")


class SoundingBoardServer:
    """Sounding board server for proactive plan review"""
    
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Agent model mapping (using available models)
        self.agent_models = {
            "violations": "gpt-4o-mini",  # Fast, efficient for rule checking
            "coach": "gpt-4o",  # More capable for complex analysis
        }
        
        # Track review sessions
        self.review_sessions = {}
        self.max_iterations = 10  # Prevent infinite loops
        
        # Load operational rules
        self.operational_rules = self._load_operational_rules()
    
    def _load_operational_rules(self) -> str:
        """Load operational rules from knowledge base or use comprehensive defaults"""
        
        # Try to load from knowledge base using MCP
        try:
            # Import the knowledge query tool if available
            from opsvi_mcp.servers.knowledge.server import query
            result = query(
                query_type="search",
                search_text="GLOBAL OPERATIONAL INSTRUCTIONS MASTER",
                limit=1
            )
            if result and result.get("results"):
                return result["results"][0].get("content", "")
        except:
            pass
        
        # Comprehensive fallback operational rules
        return """
# Operational Rules and Guidelines

## Code Quality Standards
1. All code must include proper error handling and logging
2. Functions must have clear docstrings with parameter and return types
3. No hardcoded credentials or sensitive data
4. Follow established patterns in the codebase
5. Maintain backward compatibility unless explicitly approved
6. Include unit tests for all new functionality
7. Performance implications must be documented

## Security Requirements
1. Never log or expose sensitive information (passwords, tokens, PII)
2. All external inputs must be validated and sanitized
3. Use parameterized queries for database operations
4. Implement proper authentication and authorization
5. Follow principle of least privilege
6. Encrypt sensitive data at rest and in transit

## Architectural Guidelines
1. Follow SOLID principles
2. Maintain separation of concerns
3. Avoid tight coupling between components
4. Use dependency injection where appropriate
5. Document all external dependencies
6. Consider scalability in design decisions
7. Plan for failure scenarios

## Testing Requirements
1. Minimum 80% code coverage for new code
2. Include unit, integration, and end-to-end tests
3. Test error conditions and edge cases
4. Performance tests for critical paths
5. Security tests for authentication/authorization
6. Document test scenarios and expected outcomes

## Documentation Standards
1. README must include setup instructions
2. API documentation for all public interfaces
3. Architecture diagrams for complex systems
4. Deployment and configuration guides
5. Troubleshooting documentation
6. Keep documentation in sync with code

## Deployment and Operations
1. Use infrastructure as code
2. Implement proper logging and monitoring
3. Include health checks and metrics
4. Document rollback procedures
5. Consider zero-downtime deployments
6. Environment-specific configurations

## Process Requirements
1. Code reviews required for all changes
2. Automated CI/CD pipelines
3. Version control with meaningful commits
4. Issue tracking and linking
5. Regular dependency updates
6. Security scanning in pipeline
"""
    
    async def review_violations(self, proposal: ProposalData) -> AgentResponse:
        """Violations agent review using operational rules"""
        
        prompt = f"""You are the Violations Agent reviewing a detailed implementation proposal.
        
Use these operational rules to identify violations:
{self.operational_rules}

PROPOSAL (Iteration {proposal.iteration}):
=====================================

Plan:
{proposal.plan}

Code Samples:
{proposal.code_samples or 'None provided'}

Documentation:
{proposal.documentation or 'None provided'}

Test Strategy:
{proposal.test_strategy or 'None provided'}

Evidence:
{json.dumps(proposal.evidence, default=str) if proposal.evidence else 'None provided'}

Context:
{proposal.context or 'None provided'}

=====================================

Your job:
1. Carefully review against ALL operational rules
2. Identify specific violations with rule references
3. Check for missing critical elements
4. Assess security, performance, and maintainability risks
5. Rate confidence (0-100%) that this plan is safe and correct
6. If confidence < 80%, provide a DETAILED counter-proposal

Be extremely thorough and specific. Reference exact rules violated.

Respond with JSON:
{{
    "confidence": <0-100>,
    "violations": ["list of specific rule violations with references"],
    "concerns": ["detailed concerns about the plan"],
    "questions": ["specific questions that need answers"],
    "suggestions": ["concrete improvements with examples"],
    "reasoning": "detailed explanation of confidence level",
    "counter_proposal": "comprehensive alternative proposal if confidence < 80%"
}}"""

        try:
            # Call real OpenAI API
            response = await self.client.chat.completions.create(
                model=self.agent_models["violations"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are a meticulous violations checker. Be thorough and specific."
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Low temperature for consistency
                max_tokens=2000,
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Fallback on error
            result = {
                "confidence": 0,
                "violations": [f"Failed to review: {str(e)}"],
                "concerns": ["Agent evaluation failed"],
                "questions": [],
                "suggestions": ["Fix agent connection and retry"],
                "reasoning": f"Agent error: {str(e)}",
                "counter_proposal": None,
            }
        
        agent_response = AgentResponse(
            agent_name="Violations",
            confidence=result.get("confidence", 0),
            violations=result.get("violations", []),
            concerns=result.get("concerns", []),
            questions=result.get("questions", []),
            suggestions=result.get("suggestions", []),
            reasoning=result.get("reasoning", ""),
        )
        
        # Store counter-proposal if provided
        if result.get("counter_proposal") and result.get("confidence", 100) < 80:
            cp = result.get("counter_proposal")
            # Convert dict to string if needed
            if isinstance(cp, dict):
                import json
                cp = json.dumps(cp, indent=2, default=str)
            agent_response.counter_proposal = cp
        
        return agent_response
    
    async def review_coach(self, proposal: ProposalData, coach_prompt: Optional[str] = None) -> AgentResponse:
        """Devil's Coach agent review with custom prompt"""
        
        default_prompt = """You are the Devil's Coach - part challenger, part mentor.
        
Your role:
1. Challenge assumptions and find weak points
2. Provide expert guidance when you can help
3. Look at the problem from angles the author isn't considering
4. Push for excellence, not just adequacy
5. If confidence < 80%, provide a SPECIFIC counter-proposal

Be specific, not generic. Reference actual details from the proposal."""
        
        prompt = f"""{coach_prompt or default_prompt}

PROPOSAL (Iteration {proposal.iteration}):
=====================================

Plan:
{proposal.plan}

Code Samples:
{proposal.code_samples or 'None provided'}

Documentation:
{proposal.documentation or 'None provided'}

Test Strategy:
{proposal.test_strategy or 'None provided'}

Evidence:
{json.dumps(proposal.evidence, default=str) if proposal.evidence else 'None provided'}

Context:
{proposal.context or 'None provided'}

=====================================

Provide a thorough review considering:
- Technical excellence and best practices
- Alternative approaches not considered
- Potential future issues
- Missing considerations
- Areas where the proposal could be stronger

Respond with JSON:
{{
    "confidence": <0-100>,
    "concerns": ["specific concerns with details"],
    "questions": ["probing questions that reveal gaps"],
    "suggestions": ["better approaches with rationale"],
    "coaching": "detailed guidance to improve",
    "reasoning": "explain your confidence level",
    "counter_proposal": "specific actionable counter-proposal if confidence < 80%"
}}"""
        
        try:
            # Call real OpenAI API
            response = await self.client.chat.completions.create(
                model=self.agent_models["coach"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are the Devil's Coach - challenge and guide. Be specific and constructive."
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.5,  # Moderate temperature for creativity
                max_tokens=2000,
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Fallback on error
            result = {
                "confidence": 0,
                "concerns": [f"Failed to review: {str(e)}"],
                "questions": [],
                "suggestions": ["Fix agent connection and retry"],
                "coaching": f"Agent error: {str(e)}",
                "reasoning": f"Agent error: {str(e)}",
                "counter_proposal": None,
            }
        
        agent_response = AgentResponse(
            agent_name="Devil's Coach",
            confidence=result.get("confidence", 0),
            concerns=result.get("concerns", []),
            questions=result.get("questions", []),
            suggestions=result.get("suggestions", []),
            coaching=result.get("coaching"),
            reasoning=result.get("reasoning", ""),
        )
        
        # Store counter-proposal if provided
        if result.get("counter_proposal") and result.get("confidence", 100) < 80:
            cp = result.get("counter_proposal")
            # Convert dict to string if needed
            if isinstance(cp, dict):
                import json
                cp = json.dumps(cp, indent=2, default=str)
            agent_response.counter_proposal = cp
        
        return agent_response
    
    async def review_proposal(
        self,
        proposal: ProposalData,
        session_id: str = "default",
        coach_prompt: Optional[str] = None,
    ) -> ConsensusResult:
        """Review a proposal and determine consensus"""
        
        start_time = time.time()
        
        # Initialize or update session
        if session_id not in self.review_sessions:
            self.review_sessions[session_id] = {
                "iterations": 0,
                "history": [],
            }
        
        session = self.review_sessions[session_id]
        session["iterations"] += 1
        
        # Check iteration limit
        if session["iterations"] > self.max_iterations:
            return ConsensusResult(
                approved=False,
                overall_confidence=0,
                violations_confidence=0,
                coach_confidence=0,
                iteration=session["iterations"],
                total_time=time.time() - start_time,
                agents_feedback=[],
                rejection_reason="Maximum iterations exceeded",
            )
        
        # Run both agents in parallel
        violations_task = self.review_violations(proposal)
        coach_task = self.review_coach(proposal, coach_prompt)
        
        violations_response, coach_response = await asyncio.gather(
            violations_task,
            coach_task,
        )
        
        # Calculate overall confidence (minimum of both)
        overall_confidence = min(
            violations_response.confidence,
            coach_response.confidence,
        )
        
        # Determine if approved (80% threshold)
        approved = overall_confidence >= 80
        
        # Generate counter-proposal if not approved
        counter_proposal = None
        next_steps = None
        if not approved:
            all_questions = violations_response.questions + coach_response.questions
            all_suggestions = violations_response.suggestions + coach_response.suggestions
            
            # Collect counter-proposals from agents
            counter_proposals = []
            if violations_response.counter_proposal:
                # Ensure it's a string
                cp = violations_response.counter_proposal
                if isinstance(cp, dict):
                    cp = json.dumps(cp, indent=2, default=str)
                counter_proposals.append(str(cp))
            if coach_response.counter_proposal:
                # Ensure it's a string
                cp = coach_response.counter_proposal
                if isinstance(cp, dict):
                    cp = json.dumps(cp, indent=2, default=str)
                counter_proposals.append(str(cp))
            
            # Create combined counter-proposal
            if counter_proposals:
                combined_plan = "\n\n".join(counter_proposals)
                counter_proposal = ProposalData(
                    plan=combined_plan,
                    code_samples=proposal.code_samples,
                    documentation=proposal.documentation,
                    test_strategy=proposal.test_strategy,
                    evidence=proposal.evidence,
                    context="Counter-proposal from agents based on review",
                    iteration=0,
                    confidence_score=overall_confidence
                )
            
            next_steps = "To reach consensus:\n"
            if all_questions:
                next_steps += "\nAnswer these questions:\n" + "\n".join(f"- {q}" for q in all_questions[:5])
            if all_suggestions:
                next_steps += "\n\nImplement these suggestions:\n" + "\n".join(f"- {s}" for s in all_suggestions[:5])
            if violations_response.violations:
                next_steps += "\n\nFix these violations:\n" + "\n".join(f"- {v}" for v in violations_response.violations)
        
        # Create result
        result = ConsensusResult(
            approved=approved,
            overall_confidence=overall_confidence,
            violations_confidence=violations_response.confidence,
            coach_confidence=coach_response.confidence,
            iteration=session["iterations"],
            total_time=time.time() - start_time,
            agents_feedback=[violations_response, coach_response],
            next_steps=next_steps,
            rejection_reason=None if approved else f"Confidence too low: {overall_confidence}%",
            counter_proposal=counter_proposal,
            requester_confidence=None  # To be filled by requester
        )
        
        # Store in history
        session["history"].append(result)
        
        return result
    
    def get_session_history(self, session_id: str = "default") -> Dict[str, Any]:
        """Get review history for a session"""
        
        if session_id not in self.review_sessions:
            return {"error": "Session not found"}
        
        session = self.review_sessions[session_id]
        return {
            "session_id": session_id,
            "iterations": session["iterations"],
            "history": [h.dict() for h in session["history"]],
        }
    
    def reset_session(self, session_id: str = "default") -> Dict[str, str]:
        """Reset a review session"""
        
        if session_id in self.review_sessions:
            del self.review_sessions[session_id]
        
        return {"status": "Session reset", "session_id": session_id}


# Create MCP app
mcp = FastMCP("sounding-board")

# Create server instance
sounding_board = SoundingBoardServer()


@mcp.tool()
async def review_proposal(
    plan: str = Field(description="Detailed plan or design to review"),
    code_samples: Optional[str] = Field(None, description="Code examples if applicable"),
    documentation: Optional[str] = Field(None, description="Supporting documentation"),
    test_strategy: Optional[str] = Field(None, description="How you'll test this"),
    evidence: Optional[Any] = Field(
        None,
        description="Evidence supporting the plan"
    ),
    context: Optional[str] = Field(None, description="Additional context"),
    session_id: str = Field("default", description="Session ID for tracking iterations"),
    coach_prompt: Optional[str] = Field(None, description="Custom prompt for Devil's Coach"),
    requester_confidence: Optional[float] = Field(None, description="Requester's confidence in counter-proposal (0-100)"),
) -> Dict[str, Any]:
    """
    Submit a proposal for review. Agents must reach 80% confidence.
    
    If agents provide a counter-proposal, you must evaluate it and provide
    your confidence score (requester_confidence) to complete bidirectional review.
    
    Returns consensus result with agent feedback and next steps.
    """
    
    # Get current iteration for this session
    iteration = 1
    if session_id in sounding_board.review_sessions:
        iteration = sounding_board.review_sessions[session_id]["iterations"] + 1
    
    # Handle evidence coercion
    evidence_list = []
    if evidence:
        if isinstance(evidence, list):
            evidence_list = evidence
        elif isinstance(evidence, str):
            try:
                import json
                evidence_list = json.loads(evidence)
            except:
                evidence_list = [evidence]
    
    proposal = ProposalData(
        plan=plan,
        code_samples=code_samples,
        documentation=documentation,
        test_strategy=test_strategy,
        evidence=evidence_list,
        context=context,
        iteration=iteration,
    )
    
    result = await sounding_board.review_proposal(proposal, session_id, coach_prompt)
    
    # Add requester confidence if provided
    if requester_confidence is not None:
        result.requester_confidence = requester_confidence
    
    return result.dict()


@mcp.tool()
async def reset_review_session(
    session_id: str = Field("default", description="Session ID to reset"),
) -> Dict[str, str]:
    """
    Reset a review session to start fresh.
    """
    
    return sounding_board.reset_session(session_id)


@mcp.tool()
async def get_review_history(
    session_id: str = Field("default", description="Session ID to get history for"),
) -> Dict[str, Any]:
    """
    Get the review history for a session.
    """
    
    return sounding_board.get_session_history(session_id)


if __name__ == "__main__":
    mcp.run()