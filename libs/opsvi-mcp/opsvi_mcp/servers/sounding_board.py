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

# Import LLM interfaces - using mock for now due to Pydantic v1/v2 conflict
# TODO: Fix opsvi_llm to be Pydantic v2 compatible
class LLMConfig:
    def __init__(self, **kwargs):
        self.provider_name = kwargs.get("provider_name", "openai")
        self.default_model = kwargs.get("default_model", "gpt-5")
        self.reasoning_effort = kwargs.get("reasoning_effort", "medium")
        self.enable_audit_logging = kwargs.get("enable_audit_logging", False)

class OpenAIUnifiedInterface:
    def __init__(self, config):
        self.config = config
    
    async def responses_create(self, messages, response_format=None):
        # Mock response for testing
        import random
        confidence = random.randint(70, 95)
        text = json.dumps({
            "confidence": confidence,
            "violations": [] if confidence > 80 else ["Test violation"],
            "concerns": [] if confidence > 85 else ["Test concern"],
            "questions": ["What about X?"] if confidence < 90 else [],
            "suggestions": ["Consider Y"] if confidence < 85 else [],
            "reasoning": f"Mock response with {confidence}% confidence",
            "counter_proposal": "Improved proposal" if confidence < 80 else None,
            "coaching": "Test coaching" if self.config.default_model == "gpt-5" else None
        })
        
        class MockContent:
            pass
        class MockOutput:
            def __init__(self):
                self.content = [MockContent()]
                self.content[0].text = text
        class MockResponse:
            def __init__(self):
                self.output = [MockOutput()]
        return MockResponse()

# Import knowledge tools if available
try:
    from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_query
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False


class ProposalData(BaseModel):
    """Structure for proposals submitted for review"""
    
    plan: str = Field(description="Detailed plan or design")
    code_samples: Optional[str] = Field(None, description="Code examples if applicable")
    documentation: Optional[str] = Field(None, description="Supporting documentation")
    test_strategy: Optional[str] = Field(None, description="How you'll test this")
    evidence: Optional[List[str]] = Field(default_factory=list, description="Evidence supporting the plan")
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
        # Initialize LLM clients for agents
        self.violations_client = self._init_violations_client()
        self.coach_client = self._init_coach_client()
        
        # Track review sessions
        self.review_sessions = {}
        self.max_iterations = 10  # Prevent infinite loops
        
        # Load operational instructions
        self.operational_rules = self._load_operational_rules()
        
    def _init_violations_client(self) -> OpenAIUnifiedInterface:
        """Initialize Violations agent with gpt-5-nano"""
        config = LLMConfig(
            provider_name="openai",
            default_model="gpt-5-nano",
            reasoning_effort="low",  # Low reasoning as specified
            enable_audit_logging=False,
        )
        return OpenAIUnifiedInterface(config)
    
    def _init_coach_client(self) -> OpenAIUnifiedInterface:
        """Initialize Coach agent with gpt-5"""
        config = LLMConfig(
            provider_name="openai",
            default_model="gpt-5",
            reasoning_effort="medium",  # Medium reasoning as specified
            enable_audit_logging=False,
        )
        return OpenAIUnifiedInterface(config)
    
    def _load_operational_rules(self) -> str:
        """Load operational rules from KB"""
        rules = """
GLOBAL OPERATIONAL RULES:
- NO ASSUMPTIONS: Verify everything with evidence
- NO FALLBACKS: Fix root causes, not symptoms
- NO WORKAROUNDS: Implement proper solutions
- Think BEFORE coding: Plans must be approved
- Test everything: Include test strategy
"""
        
        if KNOWLEDGE_AVAILABLE:
            try:
                query_tool = get_enhanced_query()
                result = query_tool.query(
                    query_type="search",
                    query_text="GLOBAL OPERATIONAL INSTRUCTIONS MASTER",
                    limit=1
                )
                if result.get("results"):
                    rules = result["results"][0].get("content", rules)
            except:
                pass  # Use default rules
                
        return rules
    
    async def review_violations(self, proposal: ProposalData) -> AgentResponse:
        """Violations agent review using common sense + operational rules"""
        
        prompt = f"""You are the Violations Agent reviewing a proposal.
        
Use common sense and these operational rules to identify violations:
{self.operational_rules}

PROPOSAL (Iteration {proposal.iteration}):
Plan: {proposal.plan}

Code Samples: {proposal.code_samples or 'None provided'}

Documentation: {proposal.documentation or 'None provided'}

Test Strategy: {proposal.test_strategy or 'None provided'}

Evidence: {json.dumps(proposal.evidence) if proposal.evidence else 'None provided'}

Context: {proposal.context or 'None provided'}

Your job:
1. Check for violations of operational rules
2. Identify missing evidence or unsupported claims
3. Find potential risks or problems
4. Rate your confidence (0-100%) that this plan is safe and correct
5. If confidence < 80%, provide a SPECIFIC counter-proposal

Respond with JSON:
{{
    "confidence": <0-100>,
    "violations": ["list of rule violations found"],
    "concerns": ["list of concerns about the plan"],
    "questions": ["specific questions that need answers"],
    "suggestions": ["how to improve the proposal"],
    "reasoning": "explain your confidence level",
    "counter_proposal": "specific actionable counter-proposal if confidence < 80%"
}}"""

        response = await self.violations_client.responses_create(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.output[0].content[0].text)
        
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
            agent_response.counter_proposal = result.get("counter_proposal")
        
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
Plan: {proposal.plan}

Code Samples: {proposal.code_samples or 'None provided'}

Documentation: {proposal.documentation or 'None provided'}

Test Strategy: {proposal.test_strategy or 'None provided'}

Evidence: {json.dumps(proposal.evidence) if proposal.evidence else 'None provided'}

Context: {proposal.context or 'None provided'}

Your job:
1. Challenge weak points and assumptions
2. Suggest better approaches where applicable
3. Ask probing questions that reveal hidden issues
4. Provide coaching to improve the proposal
5. Rate your confidence (0-100%) in this plan

Respond with JSON:
{{
    "confidence": <0-100>,
    "concerns": ["list of concerns"],
    "questions": ["probing questions"],
    "suggestions": ["better approaches"],
    "coaching": "guidance to improve",
    "reasoning": "explain your confidence level",
    "counter_proposal": "specific actionable counter-proposal if confidence < 80%"
}}"""

        response = await self.coach_client.responses_create(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.output[0].content[0].text)
        
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
            agent_response.counter_proposal = result.get("counter_proposal")
        
        return agent_response
    
    async def review_proposal(
        self,
        proposal: ProposalData,
        session_id: str = "default",
        coach_prompt: Optional[str] = None,
    ) -> ConsensusResult:
        """Review a proposal until consensus is reached"""
        
        start_time = time.time()
        
        # Initialize session if needed
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
                rejection_reason="Maximum iterations reached without consensus",
            )
        
        # Run both agents in parallel
        violations_task = asyncio.create_task(self.review_violations(proposal))
        coach_task = asyncio.create_task(self.review_coach(proposal, coach_prompt))
        
        violations_response, coach_response = await asyncio.gather(
            violations_task, coach_task
        )
        
        # Calculate overall confidence (minimum of both)
        overall_confidence = min(
            violations_response.confidence,
            coach_response.confidence
        )
        
        # Check for consensus (both >= 80%)
        approved = (
            violations_response.confidence >= 80 and
            coach_response.confidence >= 80
        )
        
        # Generate counter-proposal if not approved
        counter_proposal = None
        next_steps = None
        if not approved:
            all_questions = violations_response.questions + coach_response.questions
            all_suggestions = violations_response.suggestions + coach_response.suggestions
            
            # Collect counter-proposals from agents
            counter_proposals = []
            if violations_response.counter_proposal:
                counter_proposals.append(violations_response.counter_proposal)
            if coach_response.counter_proposal:
                counter_proposals.append(coach_response.counter_proposal)
            
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
    
    def reset_session(self, session_id: str = "default"):
        """Reset a review session"""
        if session_id in self.review_sessions:
            del self.review_sessions[session_id]


# Create FastMCP app
mcp = FastMCP("sounding-board")

# Create server instance
sounding_board = SoundingBoardServer()


@mcp.tool()
async def review_proposal(
    plan: str = Field(description="Detailed plan or design to review"),
    code_samples: Optional[str] = Field(None, description="Code examples if applicable"),
    documentation: Optional[str] = Field(None, description="Supporting documentation"),
    test_strategy: Optional[str] = Field(None, description="How you'll test this"),
    evidence: Optional[List[str]] = Field(
        default_factory=list,
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
    
    proposal = ProposalData(
        plan=plan,
        code_samples=code_samples,
        documentation=documentation,
        test_strategy=test_strategy,
        evidence=evidence or [],
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
    session_id: str = Field("default", description="Session ID to reset")
) -> Dict[str, str]:
    """Reset a review session to start fresh"""
    
    sounding_board.reset_session(session_id)
    return {"status": "Session reset", "session_id": session_id}


@mcp.tool()
async def get_review_history(
    session_id: str = Field("default", description="Session ID to get history for")
) -> Dict[str, Any]:
    """Get the review history for a session"""
    
    if session_id not in sounding_board.review_sessions:
        return {"error": "Session not found"}
    
    session = sounding_board.review_sessions[session_id]
    return {
        "session_id": session_id,
        "iterations": session["iterations"],
        "history": [h.dict() for h in session["history"]],
    }


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()