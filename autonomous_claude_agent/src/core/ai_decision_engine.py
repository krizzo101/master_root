"""
AI Decision Engine - All decisions go through Claude AI first
Replaces all hardcoded logic with AI intelligence

This module ensures every non-trivial decision leverages Claude's semantic understanding
rather than rudimentary Python conditionals.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionType(Enum):
    """Types of decisions the AI can make"""
    STATE_ASSESSMENT = "state_assessment"
    PATTERN_RECOGNITION = "pattern_recognition"
    ERROR_ANALYSIS = "error_analysis"
    STRATEGY_SELECTION = "strategy_selection"
    CODE_GENERATION = "code_generation"
    RESOURCE_ALLOCATION = "resource_allocation"
    CONTINUATION = "continuation"
    IMPROVEMENT_OPPORTUNITY = "improvement_opportunity"
    RISK_ASSESSMENT = "risk_assessment"
    LEARNING_EXTRACTION = "learning_extraction"


@dataclass
class AIDecision:
    """Container for AI-driven decisions with full context"""
    decision_type: DecisionType
    decision: str
    reasoning: str
    confidence: float
    action_plan: Dict[str, Any]
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    insights: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def should_execute(self, threshold: float = 0.7) -> bool:
        """Determine if decision confidence meets execution threshold"""
        return self.confidence >= threshold
    
    def get_primary_action(self) -> Optional[str]:
        """Extract primary action from action plan"""
        if self.action_plan:
            immediate = self.action_plan.get('immediate_steps', [])
            if immediate:
                return immediate[0]
        return None
    
    def has_fallback(self) -> bool:
        """Check if decision includes fallback strategy"""
        return bool(self.action_plan.get('fallback_strategy'))


class AIDecisionEngine:
    """
    Central AI decision engine that routes ALL decisions through Claude.
    
    This replaces:
    - if/else conditionals with AI reasoning
    - switch statements with intelligent selection
    - hardcoded thresholds with dynamic assessment
    - rule-based logic with semantic understanding
    """
    
    def __init__(self, claude_client):
        self.claude = claude_client
        self.decision_cache = {}
        self.decision_history = []
        self.confidence_threshold = 0.7
        self.max_history = 100
        
    async def make_decision(self,
                          context: Dict[str, Any],
                          decision_type: Union[DecisionType, str],
                          options: Optional[List[str]] = None,
                          constraints: Optional[Dict[str, Any]] = None,
                          use_cache: bool = True) -> AIDecision:
        """
        Route ANY decision through Claude AI for intelligent processing.
        
        This is the PRIMARY method that replaces ALL hardcoded decision logic.
        
        Args:
            context: Full context for decision making
            decision_type: Type of decision needed
            options: Available options to choose from (optional)
            constraints: Constraints to consider (optional)
            use_cache: Whether to use cached decisions for similar contexts
            
        Returns:
            AIDecision with reasoning, confidence, and action plan
        """
        
        # Convert string to enum if needed
        if isinstance(decision_type, str):
            decision_type = DecisionType[decision_type.upper()]
        
        # Check cache for similar decisions
        if use_cache:
            cached = self._check_cache(context, decision_type)
            if cached:
                logger.debug(f"Using cached decision for {decision_type.value}")
                return cached
        
        # Build comprehensive prompt for Claude
        prompt = self._build_decision_prompt(
            context, decision_type, options, constraints
        )
        
        try:
            # Execute AI decision making
            result = await self.claude.execute(prompt, mode="sync")
            
            # Parse and validate result
            decision = self._parse_decision(result, decision_type)
            
            # Store in cache and history
            self._cache_decision(context, decision)
            self._record_history(decision)
            
            logger.info(f"AI Decision ({decision_type.value}): {decision.decision} "
                       f"[Confidence: {decision.confidence:.2f}]")
            
            return decision
            
        except Exception as e:
            logger.error(f"AI decision failed: {e}")
            # Return low-confidence fallback decision
            return self._create_fallback_decision(decision_type, str(e))
    
    def _build_decision_prompt(self,
                              context: Dict[str, Any],
                              decision_type: DecisionType,
                              options: Optional[List[str]],
                              constraints: Optional[Dict[str, Any]]) -> str:
        """Build comprehensive prompt for AI decision making"""
        
        # Decision-specific prompt templates
        prompts = {
            DecisionType.STATE_ASSESSMENT: """
                Assess the current state of the system with deep analysis.
                Look for patterns, bottlenecks, opportunities, and risks.
                Consider system dynamics, not just current metrics.
            """,
            
            DecisionType.PATTERN_RECOGNITION: """
                Identify patterns using semantic understanding.
                Look beyond keywords to find behavioral, causal, and emergent patterns.
                Consider context, relationships, and implications.
            """,
            
            DecisionType.ERROR_ANALYSIS: """
                Perform root cause analysis on the error.
                Identify contributing factors, system state correlations, and prevention strategies.
                Focus on causes, not symptoms.
            """,
            
            DecisionType.STRATEGY_SELECTION: """
                Select optimal strategy using strategic reasoning.
                Consider multiple objectives, constraints, and future implications.
                Balance immediate needs with long-term goals.
            """,
            
            DecisionType.CODE_GENERATION: """
                Determine best approach for code generation or modification.
                Consider maintainability, performance, and system architecture.
                Favor creative solutions over template-based approaches.
            """,
            
            DecisionType.RESOURCE_ALLOCATION: """
                Optimize resource allocation across competing needs.
                Consider efficiency, priority, and opportunity costs.
                Balance current usage with future requirements.
            """,
            
            DecisionType.CONTINUATION: """
                Decide whether to continue, pivot, or stop.
                Assess progress, resource consumption, and likelihood of success.
                Consider alternative approaches if current path is suboptimal.
            """,
            
            DecisionType.IMPROVEMENT_OPPORTUNITY: """
                Identify and prioritize improvement opportunities.
                Consider impact, effort, and strategic alignment.
                Look for multiplicative improvements, not just incremental ones.
            """,
            
            DecisionType.RISK_ASSESSMENT: """
                Assess risks and their potential impacts.
                Consider probability, severity, and mitigation strategies.
                Identify cascading risks and systemic vulnerabilities.
            """,
            
            DecisionType.LEARNING_EXTRACTION: """
                Extract deep insights and learnings.
                Identify causal relationships, not just correlations.
                Generate actionable recommendations and hypotheses.
            """
        }
        
        base_prompt = prompts.get(decision_type, "Make an intelligent decision based on the context.")
        
        prompt = f"""
        You are the AI brain of an autonomous system. Make an intelligent decision using deep reasoning.
        
        Decision Type: {decision_type.value}
        {base_prompt}
        
        Context:
        {json.dumps(context, indent=2)}
        
        {"Available Options: " + json.dumps(options) if options else "Determine the best approach."}
        
        {"Constraints: " + json.dumps(constraints, indent=2) if constraints else ""}
        
        Recent Decision History:
        {json.dumps([d.metadata for d in self.decision_history[-3:]], indent=2) if self.decision_history else "No history"}
        
        Provide a comprehensive decision with:
        {{
            "decision": "The chosen action/approach",
            "reasoning": "Detailed explanation of why this decision using AI reasoning",
            "confidence": 0.0-1.0,
            "action_plan": {{
                "immediate_steps": ["step1", "step2", ...],
                "parallel_tasks": ["task1", "task2", ...],
                "decision_points": [{{"condition": "...", "action": "..."}}],
                "fallback_strategy": {{
                    "trigger": "when to fallback",
                    "action": "fallback action"
                }}
            }},
            "alternatives": [
                {{
                    "option": "alternative approach",
                    "pros": ["advantage1", ...],
                    "cons": ["disadvantage1", ...],
                    "confidence": 0.0-1.0
                }}
            ],
            "insights": {{
                "patterns_detected": ["pattern1", ...],
                "risks_identified": ["risk1", ...],
                "opportunities_found": ["opportunity1", ...],
                "key_observation": "most important insight"
            }},
            "metadata": {{
                "decision_complexity": "low|medium|high",
                "time_sensitivity": "immediate|short|long",
                "reversibility": "easily_reversible|difficult|irreversible"
            }}
        }}
        """
        
        return prompt
    
    def _parse_decision(self, result: Dict[str, Any], decision_type: DecisionType) -> AIDecision:
        """Parse AI response into AIDecision object"""
        
        return AIDecision(
            decision_type=decision_type,
            decision=result.get('decision', 'undefined'),
            reasoning=result.get('reasoning', ''),
            confidence=float(result.get('confidence', 0.5)),
            action_plan=result.get('action_plan', {}),
            alternatives=result.get('alternatives', []),
            insights=result.get('insights', {}),
            metadata=result.get('metadata', {})
        )
    
    def _check_cache(self, context: Dict[str, Any], decision_type: DecisionType) -> Optional[AIDecision]:
        """Check if similar decision exists in cache"""
        
        # Create cache key from context and type
        cache_key = self._create_cache_key(context, decision_type)
        
        if cache_key in self.decision_cache:
            cached = self.decision_cache[cache_key]
            # Check if cache is still valid (within 5 minutes)
            if (datetime.now() - cached.timestamp).seconds < 300:
                return cached
        
        return None
    
    def _create_cache_key(self, context: Dict[str, Any], decision_type: DecisionType) -> str:
        """Create cache key from context and decision type"""
        
        # Extract key elements from context
        key_elements = {
            'type': decision_type.value,
            'goal': context.get('goal', ''),
            'state': context.get('state', ''),
            'error': context.get('error_type', '')
        }
        
        return json.dumps(key_elements, sort_keys=True)
    
    def _cache_decision(self, context: Dict[str, Any], decision: AIDecision):
        """Cache decision for reuse"""
        
        cache_key = self._create_cache_key(context, decision.decision_type)
        self.decision_cache[cache_key] = decision
        
        # Limit cache size
        if len(self.decision_cache) > 100:
            # Remove oldest entries
            oldest = sorted(self.decision_cache.items(), 
                          key=lambda x: x[1].timestamp)[:20]
            for key, _ in oldest:
                del self.decision_cache[key]
    
    def _record_history(self, decision: AIDecision):
        """Record decision in history"""
        
        self.decision_history.append(decision)
        
        # Limit history size
        if len(self.decision_history) > self.max_history:
            self.decision_history = self.decision_history[-self.max_history:]
    
    def _create_fallback_decision(self, decision_type: DecisionType, error: str) -> AIDecision:
        """Create fallback decision when AI fails"""
        
        return AIDecision(
            decision_type=decision_type,
            decision="fallback_required",
            reasoning=f"AI decision failed: {error}. Using fallback strategy.",
            confidence=0.3,
            action_plan={
                'immediate_steps': ['retry_with_reduced_context'],
                'fallback_strategy': {
                    'trigger': 'ai_failure',
                    'action': 'use_conservative_defaults'
                }
            }
        )
    
    async def make_parallel_decisions(self,
                                    decisions: List[Dict[str, Any]]) -> List[AIDecision]:
        """
        Make multiple decisions in parallel for efficiency.
        
        Args:
            decisions: List of decision requests with context and type
            
        Returns:
            List of AIDecision objects
        """
        
        tasks = []
        for decision_request in decisions:
            task = self.make_decision(
                context=decision_request.get('context', {}),
                decision_type=decision_request.get('type', DecisionType.STATE_ASSESSMENT),
                options=decision_request.get('options'),
                constraints=decision_request.get('constraints')
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        decisions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Parallel decision {i} failed: {result}")
                decisions.append(self._create_fallback_decision(
                    DecisionType.STATE_ASSESSMENT, str(result)
                ))
            else:
                decisions.append(result)
        
        return decisions
    
    async def review_decision(self,
                            decision: AIDecision,
                            outcome: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a decision's outcome for learning.
        
        Args:
            decision: The original decision
            outcome: The actual outcome
            
        Returns:
            Analysis of decision quality and learnings
        """
        
        prompt = f"""
        Review this AI decision and its outcome:
        
        Original Decision:
        - Type: {decision.decision_type.value}
        - Decision: {decision.decision}
        - Reasoning: {decision.reasoning}
        - Confidence: {decision.confidence}
        - Action Plan: {json.dumps(decision.action_plan, indent=2)}
        
        Actual Outcome:
        {json.dumps(outcome, indent=2)}
        
        Analyze:
        1. Was the decision correct?
        2. Was the confidence appropriate?
        3. What can be learned?
        4. How to improve future decisions?
        
        Return:
        {{
            "decision_quality": "excellent|good|adequate|poor",
            "confidence_calibration": "overconfident|calibrated|underconfident",
            "key_learnings": [...],
            "improvement_suggestions": [...],
            "pattern_updates": [...]
        }}
        """
        
        result = await self.claude.execute(prompt, mode="sync")
        
        # Update decision metadata with review
        decision.metadata['review'] = result
        
        return result
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get statistics about decision making"""
        
        if not self.decision_history:
            return {'total_decisions': 0}
        
        stats = {
            'total_decisions': len(self.decision_history),
            'average_confidence': sum(d.confidence for d in self.decision_history) / len(self.decision_history),
            'decision_types': {},
            'high_confidence_decisions': sum(1 for d in self.decision_history if d.confidence > 0.8),
            'low_confidence_decisions': sum(1 for d in self.decision_history if d.confidence < 0.5),
            'decisions_with_fallback': sum(1 for d in self.decision_history if d.has_fallback())
        }
        
        # Count by type
        for decision in self.decision_history:
            type_name = decision.decision_type.value
            stats['decision_types'][type_name] = stats['decision_types'].get(type_name, 0) + 1
        
        return stats