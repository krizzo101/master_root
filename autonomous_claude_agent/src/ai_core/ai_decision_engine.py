"""
AI Decision Engine - Routes ALL decisions through Claude's intelligence
Replaces all hardcoded if/else logic with AI reasoning
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib


@dataclass
class AIDecision:
    """Container for AI-driven decisions with full reasoning"""
    decision_type: str
    decision: str
    reasoning: str
    confidence: float
    action_plan: Dict[str, Any]
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'decision_type': self.decision_type,
            'decision': self.decision,
            'reasoning': self.reasoning,
            'confidence': self.confidence,
            'action_plan': self.action_plan,
            'alternatives': self.alternatives,
            'risks': self.risks,
            'opportunities': self.opportunities,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class AIDecisionEngine:
    """
    Central AI brain that makes ALL non-trivial decisions
    Replaces hardcoded logic with Claude's intelligence
    """
    
    def __init__(self, claude_client=None):
        """Initialize with Claude MCP client"""
        self.claude = claude_client
        self.decision_cache = {}
        self.decision_history = []
        self.context_memory = {}
        self.learning_insights = []
        
        # Decision type templates for optimal prompting
        self.decision_templates = {
            'pattern_recognition': self._pattern_recognition_prompt,
            'error_analysis': self._error_analysis_prompt,
            'code_generation': self._code_generation_prompt,
            'strategy_selection': self._strategy_selection_prompt,
            'learning_extraction': self._learning_extraction_prompt,
            'optimization_opportunity': self._optimization_prompt
        }
        
    async def make_decision(self, 
                          context: Dict[str, Any],
                          decision_type: str,
                          options: Optional[List[str]] = None,
                          constraints: Optional[Dict[str, Any]] = None,
                          use_batch: bool = False) -> AIDecision:
        """
        Route ALL decisions through Claude AI
        
        Args:
            context: Full context for decision
            decision_type: Type of decision to make
            options: Available options (optional, AI can determine)
            constraints: Any constraints to consider
            use_batch: Use batch processing for parallel decisions
            
        Returns:
            AIDecision with full reasoning and action plan
        """
        
        # Check cache for recent similar decisions
        cache_key = self._generate_cache_key(context, decision_type)
        if cache_key in self.decision_cache:
            cached = self.decision_cache[cache_key]
            if (datetime.now() - cached.timestamp).seconds < 300:  # 5 min cache
                return cached
        
        # Build prompt using template
        if decision_type in self.decision_templates:
            prompt = self.decision_templates[decision_type](context, options, constraints)
        else:
            prompt = self._generic_decision_prompt(context, decision_type, options, constraints)
        
        # Add historical context for better decisions
        prompt = self._enrich_with_history(prompt, decision_type)
        
        try:
            # Execute through Claude MCP
            if use_batch and self.claude:
                # Use batch for multiple parallel decisions
                result = await self._batch_decision(prompt, context)
            else:
                # Direct Claude execution
                result = await self._execute_claude_decision(prompt)
            
            # Parse and validate AI response
            decision = self._parse_ai_response(result, decision_type)
            
            # Cache the decision
            self.decision_cache[cache_key] = decision
            self.decision_history.append(decision)
            
            # Extract learning insights
            if 'insights' in result:
                self.learning_insights.extend(result['insights'])
            
            return decision
            
        except Exception as e:
            # Fallback to best-effort decision
            return self._fallback_decision(context, decision_type, str(e))
    
    async def make_parallel_decisions(self, 
                                    decisions: List[Tuple[Dict, str]]) -> List[AIDecision]:
        """
        Make multiple decisions in parallel using Claude batch processing
        
        Args:
            decisions: List of (context, decision_type) tuples
            
        Returns:
            List of AIDecisions
        """
        if not self.claude:
            # Fallback to sequential if no Claude client
            results = []
            for context, dtype in decisions:
                results.append(await self.make_decision(context, dtype))
            return results
        
        # Create batch tasks for Claude
        tasks = []
        for context, dtype in decisions:
            if dtype in self.decision_templates:
                prompt = self.decision_templates[dtype](context, None, None)
            else:
                prompt = self._generic_decision_prompt(context, dtype, None, None)
            tasks.append(prompt)
        
        # Execute batch through Claude MCP
        try:
            # Use claude_run_batch for parallel execution
            batch_results = await self.claude.execute_batch(tasks)
            
            # Parse all results
            decisions = []
            for i, result in enumerate(batch_results):
                decision = self._parse_ai_response(result, decisions[i][1])
                decisions.append(decision)
                
            return decisions
            
        except Exception as e:
            # Fallback to sequential
            return await self._sequential_fallback(decisions)
    
    def _pattern_recognition_prompt(self, context: Dict, options: Any, constraints: Any) -> str:
        """Generate prompt for pattern recognition decisions"""
        return f"""
        You are an expert pattern recognition AI. Analyze this data for meaningful patterns.
        
        Data Stream: {json.dumps(context.get('data', []), indent=2)}
        
        Previous Patterns: {json.dumps(context.get('known_patterns', []), indent=2)}
        
        Identify:
        1. Behavioral patterns (what actions lead to what outcomes)
        2. Temporal patterns (time-based sequences)
        3. Causal patterns (cause and effect relationships)
        4. Optimization patterns (what could be improved)
        5. Anomaly patterns (unusual behaviors)
        6. Emergent patterns (unexpected correlations)
        
        Use SEMANTIC understanding, not keyword matching.
        Consider implicit relationships and hidden correlations.
        
        Return JSON:
        {{
            "decision": "primary_pattern_type_found",
            "reasoning": "detailed explanation of pattern discovery",
            "confidence": 0.0-1.0,
            "action_plan": {{
                "immediate_steps": ["apply_pattern_x", "monitor_pattern_y"],
                "parallel_tasks": ["analyze_sub_pattern_a", "validate_pattern_b"],
                "monitoring_strategy": {{...}}
            }},
            "patterns_found": [
                {{
                    "type": "behavioral|temporal|causal|optimization|anomaly|emergent",
                    "description": "...",
                    "trigger_conditions": [...],
                    "expected_outcomes": [...],
                    "confidence": 0.0-1.0,
                    "evidence": [...]
                }}
            ],
            "alternatives": [...],
            "risks": ["pattern_misidentification", "overfitting"],
            "opportunities": ["new_optimization_path", "predictive_capability"]
        }}
        """
    
    def _error_analysis_prompt(self, context: Dict, options: Any, constraints: Any) -> str:
        """Generate prompt for error analysis and recovery"""
        return f"""
        You are an expert debugging and error recovery AI. Perform root cause analysis.
        
        Error Details:
        - Type: {context.get('error_type', 'Unknown')}
        - Message: {context.get('error_message', '')}
        - Stack Trace: {context.get('stack_trace', '')}
        - Context: {json.dumps(context.get('execution_context', {}), indent=2)}
        - Previous Attempts: {json.dumps(context.get('recovery_attempts', []), indent=2)}
        - System State: {json.dumps(context.get('system_state', {}), indent=2)}
        
        Analyze:
        1. Root cause (not just symptoms)
        2. Contributing factors
        3. Similar past errors and successful recoveries
        4. Impact assessment
        5. Recovery strategies (ranked by likelihood of success)
        6. Prevention strategies
        
        Consider:
        - Cascading failures
        - Race conditions
        - Resource constraints
        - External dependencies
        - Data corruption
        
        Return JSON:
        {{
            "decision": "primary_recovery_strategy",
            "reasoning": "detailed root cause analysis",
            "confidence": 0.0-1.0,
            "root_cause": {{
                "primary": "...",
                "contributing_factors": [...],
                "evidence": [...]
            }},
            "action_plan": {{
                "immediate_steps": ["isolate_component", "rollback_state"],
                "recovery_sequence": [...],
                "verification_steps": [...],
                "fallback_strategy": {{...}}
            }},
            "alternatives": [
                {{"strategy": "...", "success_probability": 0.0-1.0, "risks": [...]}}
            ],
            "prevention": {{
                "code_changes": [...],
                "monitoring_additions": [...],
                "test_cases": [...]
            }},
            "risks": ["data_loss", "cascading_failure"],
            "opportunities": ["improve_error_handling", "add_resilience"]
        }}
        """
    
    def _code_generation_prompt(self, context: Dict, options: Any, constraints: Any) -> str:
        """Generate prompt for AI code generation"""
        return f"""
        You are an expert code generation AI. Generate optimal code for this requirement.
        
        Requirement: {context.get('requirement', '')}
        Current Code Context: {context.get('current_code', '')}
        Performance Metrics: {json.dumps(context.get('metrics', {}), indent=2)}
        Constraints: {json.dumps(constraints or {}, indent=2)}
        Available Libraries: {context.get('available_libraries', [])}
        Coding Standards: {context.get('standards', 'PEP8, clean code')}
        
        Generate:
        1. Optimal implementation (not just working code)
        2. Consider multiple approaches
        3. Include error handling
        4. Add performance optimizations
        5. Ensure maintainability
        6. Include tests
        
        Be creative - don't just follow templates. Consider:
        - Novel algorithms
        - Parallel processing opportunities
        - Caching strategies
        - Resource optimization
        - Edge cases
        
        Return JSON:
        {{
            "decision": "generation_approach",
            "reasoning": "why this approach is optimal",
            "confidence": 0.0-1.0,
            "generated_code": "...",
            "action_plan": {{
                "implementation_steps": [...],
                "testing_strategy": {{...}},
                "integration_plan": {{...}}
            }},
            "optimizations": [
                {{"type": "performance|memory|readability", "description": "...", "impact": "..."}}
            ],
            "alternatives": [
                {{"approach": "...", "code_snippet": "...", "pros": [...], "cons": [...]}}
            ],
            "test_cases": [...],
            "risks": ["compatibility", "performance_regression"],
            "opportunities": ["further_optimization", "reusability"]
        }}
        """
    
    def _strategy_selection_prompt(self, context: Dict, options: Any, constraints: Any) -> str:
        """Generate prompt for strategic planning decisions"""
        return f"""
        You are a strategic planning AI. Create optimal execution strategy.
        
        Goal: {context.get('goal', '')}
        Current State: {json.dumps(context.get('current_state', {}), indent=2)}
        Available Resources: {json.dumps(context.get('resources', {}), indent=2)}
        Constraints: {json.dumps(constraints or {}, indent=2)}
        Historical Performance: {json.dumps(context.get('history', {}), indent=2)}
        
        Develop strategy considering:
        1. Multiple paths to goal
        2. Resource optimization
        3. Risk mitigation
        4. Parallel execution opportunities
        5. Contingency planning
        6. Success metrics
        
        Think strategically:
        - Short-term vs long-term tradeoffs
        - Direct vs indirect approaches
        - Exploration vs exploitation
        - Speed vs quality
        - Known vs innovative solutions
        
        Return JSON:
        {{
            "decision": "recommended_strategy",
            "reasoning": "strategic analysis",
            "confidence": 0.0-1.0,
            "strategy": {{
                "approach": "direct|indirect|hybrid",
                "phases": [
                    {{"phase": "...", "objectives": [...], "success_criteria": {{...}}}}
                ],
                "resource_allocation": {{...}},
                "timeline": {{...}}
            }},
            "action_plan": {{
                "immediate_steps": [...],
                "parallel_tracks": [...],
                "decision_points": [...],
                "success_metrics": {{...}}
            }},
            "alternatives": [...],
            "risks": ["resource_exhaustion", "timeline_slip"],
            "opportunities": ["early_completion", "bonus_objectives"]
        }}
        """
    
    def _learning_extraction_prompt(self, context: Dict, options: Any, constraints: Any) -> str:
        """Generate prompt for deep learning extraction"""
        return f"""
        You are a learning extraction AI. Extract deep insights from this experience.
        
        Experience Data: {json.dumps(context.get('experience', {}), indent=2)}
        Outcome: {json.dumps(context.get('outcome', {}), indent=2)}
        Previous Similar: {json.dumps(context.get('similar_experiences', []), indent=2)}
        Current Knowledge: {json.dumps(context.get('knowledge_base', {}), indent=2)}
        
        Extract:
        1. Causal relationships (what caused what)
        2. Success factors (what made it work)
        3. Failure points (what went wrong and why)
        4. Generalizable principles
        5. Transferable patterns
        6. Meta-insights (insights about learning itself)
        
        Go beyond surface observations:
        - Hidden correlations
        - Non-obvious causation
        - Emergent properties
        - System dynamics
        - Feedback loops
        
        Return JSON:
        {{
            "decision": "primary_insight_type",
            "reasoning": "deep analysis of experience",
            "confidence": 0.0-1.0,
            "insights": [
                {{
                    "type": "causal|success_factor|failure_mode|principle|pattern|meta",
                    "description": "...",
                    "evidence": [...],
                    "applicability": "specific|general|universal",
                    "confidence": 0.0-1.0
                }}
            ],
            "action_plan": {{
                "knowledge_updates": [...],
                "behavior_modifications": [...],
                "experiments_to_run": [...]
            }},
            "connections": [
                {{"from": "experience_x", "to": "pattern_y", "relationship": "..."}}
            ],
            "predictions": [
                {{"condition": "if_x", "prediction": "then_y", "confidence": 0.0-1.0}}
            ],
            "risks": ["overgeneralization", "confirmation_bias"],
            "opportunities": ["new_capability", "performance_improvement"]
        }}
        """
    
    def _optimization_prompt(self, context: Dict, options: Any, constraints: Any) -> str:
        """Generate prompt for optimization decisions"""
        return f"""
        You are an optimization expert AI. Find optimal improvements.
        
        Current Performance: {json.dumps(context.get('metrics', {}), indent=2)}
        Code/Process: {context.get('target', '')}
        Bottlenecks: {json.dumps(context.get('bottlenecks', []), indent=2)}
        Constraints: {json.dumps(constraints or {}, indent=2)}
        
        Identify optimizations:
        1. Algorithm improvements
        2. Parallel processing opportunities
        3. Caching strategies
        4. Resource utilization
        5. Code simplification
        6. Architectural changes
        
        Consider tradeoffs:
        - Speed vs memory
        - Complexity vs maintainability
        - Latency vs throughput
        - Cost vs performance
        
        Return JSON with specific optimization plan...
        """
    
    def _generic_decision_prompt(self, context: Dict, decision_type: str, 
                                options: Any, constraints: Any) -> str:
        """Generic prompt for any decision type"""
        return f"""
        You are an expert AI making a {decision_type} decision.
        
        Context: {json.dumps(context, indent=2)}
        Options: {json.dumps(options, indent=2) if options else 'Determine best approach'}
        Constraints: {json.dumps(constraints, indent=2) if constraints else 'None'}
        
        Make the optimal decision using deep reasoning.
        Consider multiple perspectives and alternatives.
        
        Return JSON:
        {{
            "decision": "chosen_action",
            "reasoning": "detailed explanation",
            "confidence": 0.0-1.0,
            "action_plan": {{
                "immediate_steps": [...],
                "parallel_tasks": [...],
                "success_criteria": {{...}}
            }},
            "alternatives": [...],
            "risks": [...],
            "opportunities": [...]
        }}
        """
    
    def _enrich_with_history(self, prompt: str, decision_type: str) -> str:
        """Add historical context to improve decision quality"""
        recent_decisions = [d for d in self.decision_history[-10:] 
                          if d.decision_type == decision_type]
        
        if recent_decisions:
            history_context = "\n\nRecent similar decisions:\n"
            for d in recent_decisions[-3:]:
                history_context += f"- {d.decision}: {d.confidence:.2f} confidence\n"
            
            prompt += history_context
        
        if self.learning_insights:
            insights_context = "\n\nLearned insights:\n"
            for insight in self.learning_insights[-5:]:
                insights_context += f"- {insight}\n"
            
            prompt += insights_context
        
        return prompt
    
    async def _execute_claude_decision(self, prompt: str) -> Dict[str, Any]:
        """Execute decision through Claude MCP"""
        if self.claude:
            try:
                # Use claude_run for synchronous decision
                result = await self.claude.execute(prompt, mode="sync")
                
                # Parse JSON response
                if isinstance(result, str):
                    return json.loads(result)
                return result
                
            except Exception as e:
                print(f"Claude execution failed: {e}")
                
        # Fallback response structure
        return {
            "decision": "fallback_action",
            "reasoning": "Claude unavailable, using fallback",
            "confidence": 0.3,
            "action_plan": {"immediate_steps": ["proceed_with_caution"]},
            "alternatives": [],
            "risks": ["limited_intelligence"],
            "opportunities": []
        }
    
    def _parse_ai_response(self, response: Dict[str, Any], decision_type: str) -> AIDecision:
        """Parse Claude's response into AIDecision object"""
        return AIDecision(
            decision_type=decision_type,
            decision=response.get('decision', 'unknown'),
            reasoning=response.get('reasoning', 'No reasoning provided'),
            confidence=float(response.get('confidence', 0.5)),
            action_plan=response.get('action_plan', {}),
            alternatives=response.get('alternatives', []),
            risks=response.get('risks', []),
            opportunities=response.get('opportunities', []),
            metadata=response
        )
    
    def _generate_cache_key(self, context: Dict, decision_type: str) -> str:
        """Generate cache key for decision"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(f"{decision_type}:{context_str}".encode()).hexdigest()
    
    def _fallback_decision(self, context: Dict, decision_type: str, error: str) -> AIDecision:
        """Create fallback decision when AI is unavailable"""
        return AIDecision(
            decision_type=decision_type,
            decision="safe_default",
            reasoning=f"Fallback due to: {error}",
            confidence=0.2,
            action_plan={"immediate_steps": ["proceed_cautiously", "retry_later"]},
            alternatives=[],
            risks=["operating_without_full_intelligence"],
            opportunities=[]
        )
    
    async def explain_decision(self, decision: AIDecision) -> str:
        """Get detailed explanation of a decision from AI"""
        prompt = f"""
        Explain this decision in detail for a human operator:
        
        Decision: {decision.decision}
        Type: {decision.decision_type}
        Reasoning: {decision.reasoning}
        Confidence: {decision.confidence}
        
        Provide:
        1. Why this decision was made
        2. What alternatives were considered
        3. Key risks to watch for
        4. Expected outcomes
        5. How to monitor success
        
        Make it clear and actionable.
        """
        
        if self.claude:
            explanation = await self.claude.execute(prompt, mode="sync")
            return explanation
        
        return f"Decision: {decision.decision}\nReasoning: {decision.reasoning}"
    
    def get_decision_history(self, decision_type: Optional[str] = None) -> List[AIDecision]:
        """Get history of decisions, optionally filtered by type"""
        if decision_type:
            return [d for d in self.decision_history if d.decision_type == decision_type]
        return self.decision_history
    
    def get_learning_insights(self) -> List[str]:
        """Get accumulated learning insights"""
        return self.learning_insights
    
    def clear_cache(self):
        """Clear decision cache"""
        self.decision_cache.clear()