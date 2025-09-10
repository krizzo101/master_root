#!/usr/bin/env python3
"""
Intelligent Triage Agent - Uses LLM to decide when full consult team is needed
No brittle keyword matching - real intelligence
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TriageDecision:
    needs_escalation: bool
    confidence: float
    reasoning: str
    risk_level: str  # "low", "medium", "high", "critical"
    suggested_agents: List[str]
    immediate: bool


class IntelligentTriageAgent:
    """
    Lightweight LLM agent that runs on EVERY thought
    Decides intelligently when to escalate to full consult suite
    """

    def __init__(self, model="gpt-5-nano"):  # Fast, cheap model
        self.model = model
        self.context_window = []
        self.escalation_history = []
        self.learning_enabled = True

    async def evaluate_thought(self, thought: str, context: Dict) -> TriageDecision:
        """
        Use LLM to intelligently evaluate if escalation needed
        This runs on EVERY thought - must be fast
        """

        # Build context for triage decision
        triage_prompt = self._build_triage_prompt(thought, context)

        # Call fast LLM for triage decision
        # In production, this would be actual API call
        decision = await self._call_triage_llm(triage_prompt)

        # Learn from decision outcomes
        if self.learning_enabled:
            self._update_learning(thought, decision)

        return decision

    def _build_triage_prompt(self, thought: str, context: Dict) -> str:
        """
        Build intelligent prompt for triage decision
        No keyword matching - let the model understand
        """

        return f"""You are a triage agent deciding if a thought needs expert review.

Current thought: {thought}

Recent context: {self._get_recent_context()}

Task context: {context.get('current_task', 'general thinking')}

Evaluate based on:
1. Risk level - Could this thought lead to breaking changes?
2. Uncertainty - Is the thinker unsure or making assumptions?
3. Complexity - Does this need architectural review?
4. Pattern - Is this repeating a problematic pattern?
5. Quality - Is the thinking shallow or missing analysis?

Respond with JSON:
{{
    "needs_escalation": boolean,
    "confidence": 0.0-1.0,
    "reasoning": "why or why not",
    "risk_level": "low|medium|high|critical",
    "suggested_agents": ["critic", "gatekeeper", etc] or [],
    "immediate": boolean
}}

Be selective - only escalate when truly needed. Most thoughts can proceed.
"""

    async def _call_triage_llm(self, prompt: str) -> TriageDecision:
        """
        Call lightweight LLM for fast triage decision
        """

        # This would be actual LLM call
        # For prototype, simulate intelligent decision

        # Simulated LLM response based on thought analysis
        response = {
            "needs_escalation": False,
            "confidence": 0.85,
            "reasoning": "Standard thinking process, no red flags detected",
            "risk_level": "low",
            "suggested_agents": [],
            "immediate": False,
        }

        # Real implementation would be:
        # response = await openai_client.chat.completions.create(
        #     model=self.model,
        #     messages=[{"role": "system", "content": prompt}],
        #     response_format={"type": "json_object"},
        #     temperature=0.3,  # More deterministic
        #     max_tokens=150  # Keep it fast
        # )

        return TriageDecision(**response)

    def _get_recent_context(self) -> str:
        """Get recent thought context for better decisions"""

        if not self.context_window:
            return "No recent context"

        return "\n".join(
            [
                f"[{i}]: {thought[:100]}..."
                for i, thought in enumerate(self.context_window[-3:])
            ]
        )

    def _update_learning(self, thought: str, decision: TriageDecision):
        """
        Learn from triage decisions to improve over time
        """

        self.escalation_history.append(
            {
                "thought": thought,
                "decision": decision,
                "timestamp": "now",  # Would be actual timestamp
                "outcome": None,  # Updated later based on results
            }
        )

        # Analyze patterns in escalation history
        if len(self.escalation_history) > 10:
            self._analyze_patterns()

    def _analyze_patterns(self):
        """
        Analyze escalation patterns to improve future decisions
        """

        # Look for patterns like:
        # - Over-escalation (escalated but not needed)
        # - Under-escalation (didn't escalate but should have)
        # - Successful catches (escalated and prevented issues)

        recent = self.escalation_history[-10:]
        escalation_rate = sum(1 for h in recent if h["decision"].needs_escalation) / 10

        # Adjust sensitivity based on patterns
        if escalation_rate > 0.5:
            # Might be over-escalating
            self.adjustment = "decrease_sensitivity"
        elif escalation_rate < 0.1:
            # Might be under-escalating
            self.adjustment = "increase_sensitivity"


class ThinkingServerWithIntelligentTriage:
    """
    MCP Thinking Server with intelligent triage before consult escalation
    """

    def __init__(self):
        self.triage_agent = IntelligentTriageAgent()
        self.consult_calls = 0
        self.thoughts_processed = 0

    async def process_thought(self, thought: str, context: Dict) -> Dict:
        """
        Process every thought through intelligent triage
        """

        self.thoughts_processed += 1

        # EVERY thought goes through triage (lightweight, fast)
        triage_decision = await self.triage_agent.evaluate_thought(thought, context)

        response = {
            "thoughtNumber": context.get("thoughtNumber", 1),
            "triageEvaluation": {
                "risk": triage_decision.risk_level,
                "confidence": triage_decision.confidence,
            },
        }

        # Only escalate when triage agent says necessary
        if triage_decision.needs_escalation:
            self.consult_calls += 1

            # Now bring in the full team
            consult_result = await self._run_consult_team(
                thought=thought,
                reasoning=triage_decision.reasoning,
                suggested_agents=triage_decision.suggested_agents,
                immediate=triage_decision.immediate,
            )

            response["consultIntervention"] = consult_result
            response["blocked"] = consult_result.get("critical_issues", False)

        else:
            # Thought proceeds without intervention
            response["status"] = "proceed"

        # Add stats for monitoring
        response["stats"] = {
            "thoughts_processed": self.thoughts_processed,
            "consult_calls": self.consult_calls,
            "escalation_rate": self.consult_calls / max(1, self.thoughts_processed),
        }

        return response

    async def _run_consult_team(
        self, thought: str, reasoning: str, suggested_agents: List[str], immediate: bool
    ) -> Dict:
        """
        Run full consult suite when triage determines it's needed
        """

        # Configure based on triage recommendations
        config = {
            "agent_type": "consult",
            "prompt": f"Review this thought: {thought}\nTriage concern: {reasoning}",
            "quality": "better" if immediate else "normal",
            "agents": suggested_agents or ["critic", "gatekeeper"],
            "max_time": 3 if immediate else 10,
        }

        # Would call actual consult suite
        # result = await mcp__consult_suite_enhanced__consult_suite(**config)

        # Simulated result
        return {
            "feedback": "Based on team analysis...",
            "issues": ["Issue 1", "Issue 2"] if immediate else [],
            "critical_issues": immediate,
        }


# The key advantages:

ADVANTAGES = """
1. INTELLIGENT DECISIONS - LLM understands context, not just keywords
2. RUNS ON EVERY THOUGHT - But lightweight enough to not slow down
3. LEARNS PATTERNS - Improves escalation decisions over time
4. RISK-BASED - Escalates based on actual risk, not arbitrary counts
5. ADAPTIVE - Adjusts sensitivity based on outcomes
6. RESOURCE EFFICIENT - Only calls expensive consult when needed

Example flow:
- Thought: "I'll implement this feature"
  → Triage: Low risk, proceed

- Thought: "I'll just delete these files"
  → Triage: HIGH RISK! Escalate immediately
  → Consult: Full team reviews before allowing

- Thought: "This should probably work"
  → Triage: Medium risk (uncertainty detected)
  → Consult: Critic agent reviews assumptions
"""

# Real-world analogy:
ANALOGY = """
This is like having a smart junior engineer reviewing all code changes:
- Most changes: "Looks fine, proceed"
- Risky changes: "We need senior review on this"
- Uncertain changes: "Let me get a second opinion"

The junior (triage agent) handles 90% efficiently,
only escalating the 10% that truly needs senior team (consult suite).
"""
