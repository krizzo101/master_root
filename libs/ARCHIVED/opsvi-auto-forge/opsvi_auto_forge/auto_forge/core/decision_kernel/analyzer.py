from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional
from uuid import UUID

from .interfaces import IPromptGateway

logger = logging.getLogger(__name__)


class TaskAnalyzer:
    """Enhanced task analyzer with LLM-based analysis and heuristics."""

    def __init__(self, prompt_gateway: Optional[IPromptGateway] = None):
        """Initialize the task analyzer.

        Args:
            prompt_gateway: Optional prompt gateway for LLM analysis
        """
        self.prompt_gateway = prompt_gateway
        self._model_pricing = {
            "o4-mini": {"input": 0.15, "output": 0.60},  # per 1M tokens
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4.1": {"input": 3.00, "output": 15.00},
            "o3": {"input": 15.00, "output": 60.00},
        }

    async def analyze_task(
        self,
        task_id: UUID,
        agent: str,
        task_type: str,
        budget_hint: Dict[str, Any],
        task_input: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enhanced task analysis with LLM-based assessment.

        Args:
            task_id: Task identifier
            agent: Agent name
            task_type: Type of task
            budget_hint: Budget constraints
            task_input: Optional task input for analysis
            context: Optional context for analysis

        Returns:
            Analysis results with complexity, risk, cost, latency, and retrieval hints
        """
        start_time = time.time()

        try:
            # Step 1: Fast heuristics analysis
            heuristic_analysis = self._analyze_heuristics(
                agent, task_type, task_input, context
            )

            # Step 2: LLM-based analysis if enabled and budget allows
            llm_analysis = None
            if self.prompt_gateway and self._should_use_llm_analysis(budget_hint):
                llm_analysis = await self._analyze_with_llm(
                    task_id, agent, task_type, task_input, context
                )

            # Step 3: Combine analyses
            final_analysis = self._combine_analyses(heuristic_analysis, llm_analysis)

            # Step 4: Add cost estimation
            final_analysis["expected_cost_usd"] = self._estimate_cost(
                final_analysis, budget_hint
            )

            # Step 5: Add latency targets
            final_analysis["latency_target_ms"] = self._estimate_latency(
                final_analysis, budget_hint
            )

            # Step 6: Generate retrieval hints
            final_analysis["retrieval_hint"] = self._generate_retrieval_hints(
                agent, task_type, final_analysis, context
            )

            # Step 7: Add analysis metadata
            final_analysis.update(
                {
                    "task_id": str(task_id),
                    "agent": agent,
                    "task_type": task_type,
                    "analysis_duration_ms": (time.time() - start_time) * 1000,
                    "analysis_method": "llm" if llm_analysis else "heuristics",
                }
            )

            logger.info(
                f"Task analysis completed for {task_id}: complexity={final_analysis['complexity']:.2f}, risk={final_analysis['risk']:.2f}"
            )
            return final_analysis

        except Exception as e:
            logger.error(f"Task analysis failed for {task_id}: {e}")
            # Fallback to basic analysis
            return self._fallback_analysis(task_id, agent, task_type, budget_hint)

    def _analyze_heuristics(
        self,
        agent: str,
        task_type: str,
        task_input: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Fast heuristic analysis based on task characteristics."""

        # Complexity heuristics
        complexity = 0.3  # Base complexity

        # Agent-based complexity adjustments
        agent_complexity = {
            "ResearcherAgent": 0.4,
            "CoderAgent": 0.6,
            "CriticAgent": 0.5,
            "ArchitectAgent": 0.7,
            "TesterAgent": 0.4,
        }
        complexity += agent_complexity.get(agent, 0.3)

        # Task type complexity
        task_complexity = {
            "research": 0.3,
            "code": 0.7,
            "test": 0.4,
            "review": 0.5,
            "architect": 0.8,
            "debug": 0.6,
        }
        complexity += task_complexity.get(task_type, 0.4)

        # Input size complexity
        if task_input:
            input_size = len(task_input)
            if input_size > 10000:
                complexity += 0.2
            elif input_size > 5000:
                complexity += 0.1
            elif input_size > 1000:
                complexity += 0.05

        # Context complexity
        if context:
            if context.get("dependencies", []):
                complexity += 0.1
            if context.get("constraints", []):
                complexity += 0.1
            if context.get("performance_requirements"):
                complexity += 0.15

        complexity = min(1.0, complexity)

        # Risk assessment
        risk = 0.2  # Base risk

        # High complexity = higher risk
        if complexity > 0.7:
            risk += 0.3
        elif complexity > 0.5:
            risk += 0.2

        # Agent-specific risks
        agent_risk = {
            "CoderAgent": 0.1,  # Code generation can be risky
            "ArchitectAgent": 0.2,  # Architecture decisions are critical
            "CriticAgent": 0.05,  # Review is lower risk
        }
        risk += agent_risk.get(agent, 0.0)

        # Task type risks
        task_risk = {
            "debug": 0.2,  # Debugging can be unpredictable
            "architect": 0.3,  # Architecture is critical
            "code": 0.15,  # Code generation has risks
        }
        risk += task_risk.get(task_type, 0.0)

        risk = min(1.0, risk)

        return {
            "complexity": complexity,
            "risk": risk,
            "confidence": 0.7,  # Heuristic confidence
        }

    async def _analyze_with_llm(
        self,
        task_id: UUID,
        agent: str,
        task_type: str,
        task_input: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """LLM-based task analysis."""

        try:
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(
                task_id, agent, task_type, task_input, context
            )

            # Define analysis schema
            analysis_schema = {
                "type": "object",
                "properties": {
                    "complexity": {"type": "number", "minimum": 0, "maximum": 1},
                    "risk": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reasoning": {"type": "string"},
                    "retrieval_hints": {
                        "type": "object",
                        "properties": {
                            "entities": {"type": "array", "items": {"type": "string"}},
                            "namespaces": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "keywords": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "required": ["complexity", "risk", "confidence", "reasoning"],
            }

            # Call LLM for analysis
            response = await self.prompt_gateway.create_structured_response(
                run_id=str(task_id),
                role="TaskAnalyzer",
                task_type="analysis",
                user_goal=analysis_prompt,
                schema=analysis_schema,
                verifier_model="gpt-4o-mini",
                max_repair_attempts=1,
            )

            return {
                "complexity": response.get("complexity", 0.5),
                "risk": response.get("risk", 0.3),
                "confidence": response.get("confidence", 0.8),
                "reasoning": response.get("reasoning", ""),
                "retrieval_hints": response.get("retrieval_hints", {}),
            }

        except Exception as e:
            logger.warning(f"LLM analysis failed for {task_id}: {e}")
            return None

    def _create_analysis_prompt(
        self,
        task_id: UUID,
        agent: str,
        task_type: str,
        task_input: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Create analysis prompt for LLM."""

        prompt = f"""Analyze the following task for complexity, risk, and retrieval needs:

Task ID: {task_id}
Agent: {agent}
Task Type: {task_type}

Task Input: {task_input[:1000] if task_input else "No specific input provided"}

Context: {json.dumps(context, indent=2) if context else "No additional context"}

Please analyze:
1. Complexity (0-1): How complex is this task? Consider input size, agent capabilities, task type
2. Risk (0-1): How risky is this task? Consider potential failures, criticality
3. Confidence (0-1): How confident are you in this analysis?
4. Reasoning: Brief explanation of your analysis
5. Retrieval hints: What entities, namespaces, or keywords would be useful for context?

Provide a structured analysis focusing on practical factors that affect task execution."""

        return prompt

    def _combine_analyses(
        self, heuristic: Dict[str, Any], llm: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Combine heuristic and LLM analyses."""

        if not llm:
            return heuristic

        # Weighted combination (heuristic: 0.3, LLM: 0.7)
        complexity = heuristic["complexity"] * 0.3 + llm["complexity"] * 0.7
        risk = heuristic["risk"] * 0.3 + llm["risk"] * 0.7
        confidence = max(heuristic["confidence"], llm["confidence"])

        return {
            "complexity": complexity,
            "risk": risk,
            "confidence": confidence,
            "reasoning": llm.get("reasoning", ""),
            "retrieval_hints": llm.get("retrieval_hints", {}),
        }

    def _estimate_cost(
        self, analysis: Dict[str, Any], budget_hint: Dict[str, Any]
    ) -> float:
        """Estimate cost based on analysis and budget."""

        base_cost = 0.01  # Base cost for any task

        # Complexity-based cost scaling
        complexity_cost = analysis["complexity"] * 0.05

        # Risk-based cost scaling (higher risk = more attempts)
        risk_cost = analysis["risk"] * 0.03

        # Agent-specific costs
        agent_costs = {
            "CoderAgent": 0.02,
            "ArchitectAgent": 0.03,
            "CriticAgent": 0.01,
            "ResearcherAgent": 0.015,
        }
        agent_cost = agent_costs.get(analysis.get("agent", ""), 0.01)

        estimated_cost = base_cost + complexity_cost + risk_cost + agent_cost

        # Respect budget constraints
        max_cost = budget_hint.get("max_cost_usd", 1.0)
        return min(estimated_cost, max_cost)

    def _estimate_latency(
        self, analysis: Dict[str, Any], budget_hint: Dict[str, Any]
    ) -> int:
        """Estimate latency target based on analysis."""

        base_latency = 30_000  # 30 seconds base

        # Complexity-based latency scaling
        complexity_latency = analysis["complexity"] * 60_000  # Up to 60s additional

        # Risk-based latency scaling
        risk_latency = analysis["risk"] * 30_000  # Up to 30s additional

        estimated_latency = base_latency + complexity_latency + risk_latency

        # Respect budget constraints
        max_latency = budget_hint.get("max_latency_ms", 300_000)  # 5 minutes
        return min(int(estimated_latency), max_latency)

    def _generate_retrieval_hints(
        self,
        agent: str,
        task_type: str,
        analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate retrieval hints for context assembly."""

        hints = {
            "entities": [],
            "namespaces": ["project"],
            "keywords": [],
        }

        # Agent-specific hints
        agent_hints = {
            "CoderAgent": {
                "entities": ["code", "function", "class", "module"],
                "namespaces": ["project", "code", "tests"],
                "keywords": ["implementation", "function", "class", "api"],
            },
            "ArchitectAgent": {
                "entities": ["architecture", "component", "service", "database"],
                "namespaces": ["project", "architecture", "design"],
                "keywords": ["architecture", "design", "component", "service"],
            },
            "CriticAgent": {
                "entities": ["code", "test", "documentation"],
                "namespaces": ["project", "code", "tests", "docs"],
                "keywords": ["review", "quality", "test", "documentation"],
            },
            "ResearcherAgent": {
                "entities": ["requirement", "specification", "documentation"],
                "namespaces": ["project", "requirements", "docs"],
                "keywords": ["research", "requirement", "specification"],
            },
        }

        if agent in agent_hints:
            hints.update(agent_hints[agent])

        # Task type hints
        task_hints = {
            "code": {"keywords": ["implementation", "function", "api"]},
            "test": {"keywords": ["test", "validation", "coverage"]},
            "review": {"keywords": ["review", "quality", "standards"]},
            "debug": {"keywords": ["error", "bug", "issue", "fix"]},
        }

        if task_type in task_hints:
            hints["keywords"].extend(task_hints[task_type]["keywords"])

        # Context-based hints
        if context:
            if context.get("dependencies"):
                hints["entities"].extend(["dependency", "library", "package"])
            if context.get("performance_requirements"):
                hints["keywords"].extend(["performance", "optimization", "efficiency"])

        # Remove duplicates
        hints["entities"] = list(set(hints["entities"]))
        hints["keywords"] = list(set(hints["keywords"]))

        return hints

    def _should_use_llm_analysis(self, budget_hint: Dict[str, Any]) -> bool:
        """Determine if LLM analysis should be used based on budget."""

        # Check if LLM analysis is enabled
        if not self.prompt_gateway:
            return False

        # Check budget constraints
        max_cost = budget_hint.get("max_cost_usd", 1.0)
        if max_cost < 0.05:  # Too small budget for LLM analysis
            return False

        return True

    def _fallback_analysis(
        self, task_id: UUID, agent: str, task_type: str, budget_hint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback analysis when main analysis fails."""

        return {
            "task_id": str(task_id),
            "agent": agent,
            "task_type": task_type,
            "complexity": 0.5,
            "risk": 0.3,
            "expected_cost_usd": float(budget_hint.get("max_cost_usd", 10.0)) * 0.1,
            "latency_target_ms": 30_000,
            "retrieval_hint": {
                "entities": [],
                "namespaces": ["project"],
                "keywords": [],
            },
            "confidence": 0.5,
            "analysis_method": "fallback",
        }


# Backward compatibility function
async def analyze_task(
    task_id: UUID, agent: str, task_type: str, budget_hint: Dict[str, Any]
) -> Dict[str, Any]:
    """Lightweight, fast analysis to shape strategy selection.

    Returns a dict including:
      - complexity: float [0..1]
      - risk: float [0..1]
      - expected_cost_usd: float
      - latency_target_ms: int
      - retrieval_hint: dict (entities, namespaces)
    """
    analyzer = TaskAnalyzer()
    return await analyzer.analyze_task(task_id, agent, task_type, budget_hint)
