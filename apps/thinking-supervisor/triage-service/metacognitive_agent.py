#!/usr/bin/env python3
# flake8: noqa: E501
"""
Complete Metacognitive Agent - Parallel intelligent analysis of thinking patterns
Replaces both triage violations and metacognitive prompts with unified intelligence
"""

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Set environment variables from .mcp.json BEFORE any imports
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "password")
os.environ.setdefault("EMBEDDING_SERVICE_URL", "http://localhost:8000")

# Add libs to path
sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/apps")

from opsvi_llm.providers.openai_provider import OpenAIConfig  # noqa: E402
from opsvi_llm.providers.openai_unified_interface import (  # noqa: E402
    OpenAIUnifiedInterface,
)

from devils_advocate import DevilsAdvocate  # noqa: E402

# Import knowledge tools for direct access
try:
    from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_query

    KNOWLEDGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Knowledge system not available: {e}", file=sys.stderr)
    KNOWLEDGE_AVAILABLE = False


class AgentTiming:
    """Track individual agent timing for performance analysis"""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.agent_name: str = ""

    def start(self, agent_name: str):
        self.start_time = time.time()
        self.agent_name = agent_name

    def end(self):
        self.end_time = time.time()
        return self.end_time - self.start_time


class MetacognitiveAgent:
    """Complete metacognitive agent using parallel intelligent analysis"""

    def __init__(self):
        # Initialize OpenAI interface
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        config = OpenAIConfig(
            api_key=api_key,
            provider_name="openai",
            default_model="gpt-5-nano",
            enable_audit_logging=False,
            enable_sanitization=False,
        )
        self.interface = OpenAIUnifiedInterface(config)

        # Initialize knowledge tools if available
        if KNOWLEDGE_AVAILABLE:
            self.query_tool = get_enhanced_query()
        else:
            self.query_tool = None

        # Cache for instructions
        self._cached_instructions = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes
        
        # Initialize Devil's Advocate for skeptical questioning
        self.devils_advocate = DevilsAdvocate()

        # Common programming context for better analysis
        self.domain_context = """
SPECIFIC VIOLATIONS FROM OPERATIONAL INSTRUCTIONS:
- "probably/likely/should be" = NO ASSUMPTIONS violation (verify everything)
- "simpler alternative" = NO FALLBACKS violation (fix properly)
- Coding without thinking = THINKING MANDATORY violation (think first)
- Sequential Task calls = TASK MANDATORY violation (use parallel)
- Using gpt-4o/gpt-4o-mini = MODELS 2025 violation (use gpt-5/o3/o4)
- Exploring code first = KB FIRST violation (query knowledge first)
- Bash with *.py/*.js = GLOB HANDLING violation (use shell_exec)
- Multiple tool messages = EFFICIENCY violation (batch in single message)
- Creating _v2 files = GIT/FILES violation (use proper versioning)
        """.strip()

    def _extract_response_content(self, response) -> str:
        """Extract text content from Responses API response object"""
        content = ""
        if hasattr(response, "output"):
            for item in response.output:
                if hasattr(item, "content") and item.content:
                    for content_item in item.content:
                        if hasattr(content_item, "text"):
                            content += content_item.text
        else:
            # Fallback for unexpected format
            content = str(response)
        return content

    def _format_thought_history(self, thoughts: List) -> str:
        """Format thought history including context if available"""
        formatted = []
        for t in thoughts:
            if hasattr(t, "thought"):  # ThoughtData object
                line = f"- {t.thought[:100]}..."
                if hasattr(t, "triggerContext"):
                    line += f" [Trigger: {t.triggerContext[:50]}]"
                formatted.append(line)
            elif isinstance(t, dict):
                line = f"- {t.get('thought', '')[:100]}..."
                formatted.append(line)
            else:
                formatted.append(f"- {str(t)[:100]}...")
        return "\n".join(formatted)

    def _detect_repetition_quick(self, thought_history: List[Dict]) -> bool:
        """Quick check for obvious repetitive patterns"""
        if len(thought_history) < 5:
            return False

        # Check last 5 thoughts for repetition
        # Handle both dict and ThoughtData objects
        recent = []
        for t in thought_history[-5:]:
            if hasattr(t, "thought"):  # ThoughtData object
                recent.append(t.thought.lower()[:50] if t.thought else "")
            else:  # Dict format
                recent.append(t.get("thought", "").lower()[:50])

        # Look for similar starts (likely repeated searches/attempts)
        for i in range(len(recent) - 2):
            if recent[i] and recent[i] in recent[i + 2]:  # Skip 1 to avoid adjacent
                return True

        return False

    async def load_instructions(self) -> str:
        """Load operational instructions with caching"""
        if not self.query_tool:
            return "Core rules: No assumptions, fix root causes, no fallbacks, be expert advisor"

        # Check cache
        import time

        current_time = time.time()
        if (
            self._cached_instructions
            and self._cache_timestamp
            and (current_time - self._cache_timestamp) < self._cache_ttl
        ):
            return self._cached_instructions

        # Load from KB
        try:
            result = self.query_tool.query(
                query_type="search",
                query_text="GLOBAL OPERATIONAL INSTRUCTIONS MASTER",
                limit=1,
            )
            instructions = ""
            for item in result.get("results", []):
                instructions = item.get("content", "")
                break

            if instructions:
                self._cached_instructions = instructions
                self._cache_timestamp = current_time
                return instructions
        except Exception as e:
            print(f"KB load failed: {e}", file=sys.stderr)

        return "Core rules: No assumptions, fix root causes, no fallbacks, be expert advisor"

    async def load_lessons(self) -> str:
        """Load user corrections and lessons learned from KB"""
        if not self.query_tool:
            return ""

        try:
            # Query for user corrections and lessons
            result = self.query_tool.query(
                query_type="search",
                query_text="user-correction lesson-learned",
                limit=10,
            )

            lessons = []
            for item in result.get("results", []):
                content = item.get("content", "")
                if "LESSON:" in content or "WHAT I DID WRONG:" in content:
                    # Extract just the key lesson
                    lines = content.split("\n")
                    for line in lines:
                        if (
                            "WHAT I DID WRONG:" in line
                            or "HOW TO NOT DO IT AGAIN:" in line
                        ):
                            lessons.append(line.strip())

            if lessons:
                return "\n\nPREVIOUS CORRECTIONS TO WATCH FOR:\n" + "\n".join(
                    lessons[:5]
                )
        except Exception as e:
            print(f"Lessons load failed: {e}", file=sys.stderr)

        return ""

    def auto_detect_phase(self, thought_data: Any) -> str:
        """Auto-detect work phase based on context"""
        if not thought_data:
            return "auto"

        # Check triggerContext and thought content
        trigger = (
            getattr(thought_data, "triggerContext", "").lower()
            if hasattr(thought_data, "triggerContext")
            else ""
        )
        thought = (
            getattr(thought_data, "thought", "").lower()
            if hasattr(thought_data, "thought")
            else ""
        )

        # If it's a dict, handle that too
        if isinstance(thought_data, dict):
            trigger = thought_data.get("triggerContext", "").lower()
            thought = thought_data.get("thought", "").lower()

        # Debugging indicators
        if any(
            word in trigger + thought
            for word in ["error", "exception", "failure", "bug", "fix", "issue"]
        ):
            return "debugging"

        # Implementation indicators
        if any(
            word in trigger + thought
            for word in ["implement", "create", "add", "build", "write"]
        ):
            return "implementation"

        # Design indicators
        if any(
            word in trigger + thought
            for word in ["design", "architect", "plan", "structure"]
        ):
            return "design"

        # Research indicators
        if any(
            word in trigger + thought
            for word in ["research", "investigate", "explore", "find", "search"]
        ):
            return "research"

        # Review indicators
        if any(
            word in trigger + thought
            for word in ["review", "test", "validate", "check"]
        ):
            return "review"

        return "auto"

    def get_phase_coaching_focus(self, phase: str) -> str:
        """Get phase-specific coaching focus"""
        phase_focus = {
            "design": "- Encourage clear architectural decisions\n- Validate assumptions with research\n- Consider edge cases early",
            "implementation": "- Ensure files are read before editing\n- Validate changes with tests\n- Follow existing patterns",
            "debugging": "- Form clear hypotheses\n- Test one variable at a time\n- Check error messages carefully",
            "research": "- Time-box investigations\n- Synthesize findings clearly\n- Document sources",
            "review": "- Check for completeness\n- Validate against requirements\n- Run final tests",
            "auto": "- Stay focused on the task\n- Avoid unnecessary complexity\n- Test assumptions",
        }
        return phase_focus.get(phase, phase_focus["auto"])

    def get_phase_rules(self, phase: str) -> str:
        """Get phase-specific rule adjustments"""
        phase_rules = {
            "design": """
PHASE: DESIGN - Allow exploratory language
- "Should/could" acceptable when followed by rationale
- Focus on trade-offs and architectural decisions
- Documented assumptions are GOOD, not violations
""",
            "implementation": """
PHASE: IMPLEMENTATION - Require concrete actions
- Strict NO_ASSUMPTIONS for code changes
- Must read files before editing
- Require tests and validation
""",
            "debugging": """
PHASE: DEBUGGING - Hypothesis-test focus
- Allow investigative assumptions with validation
- Prioritize reproduction steps
- Limit scope to the bug
""",
            "research": """
PHASE: RESEARCH - Knowledge gathering
- Exploration is the goal
- Time-box investigations
- Require synthesis
""",
            "review": """
PHASE: REVIEW - Verify completeness
- Check requirements met
- Validate test coverage
- Focus on quality
""",
        }
        return phase_rules.get(phase, "")

    def _get_thought_progression_context(
        self, thought_number: int, total_thoughts: int
    ) -> str:
        """Generate context based on thought progression"""
        progress_ratio = thought_number / max(total_thoughts, 1)

        if progress_ratio <= 0.2:
            return """
THOUGHT PHASE: EARLY (0-20% complete)
- Focus on exploration and discovery
- Suggest broad approaches and frameworks
- Encourage thorough analysis before implementation
- Provide guidance on what to think about next
"""
        elif progress_ratio <= 0.6:
            return """
THOUGHT PHASE: MIDDLE (20-60% complete)
- Focus on execution and refinement
- Suggest optimizations and improvements
- Help maintain momentum and direction
- Provide tactical guidance for current approach
"""
        elif progress_ratio <= 0.9:
            return """
THOUGHT PHASE: LATE (60-90% complete)
- Focus on completion and validation
- Suggest final checks and refinements
- Help ensure quality and completeness
- Provide final recommendations and warnings
"""
        else:
            return """
THOUGHT PHASE: FINAL (90-100% complete)
- Focus on final validation and delivery
- Suggest last-minute improvements
- Help ensure nothing is missed
- Provide final quality assurance
"""

    def _analyze_performance(self, timing_results: Dict, total_elapsed: float) -> Dict:
        """Analyze agent performance and identify bottlenecks"""

        # Find slowest agent
        slowest_agent = max(timing_results.items(), key=lambda x: x[1]["elapsed"])

        # Calculate parallel efficiency
        sequential_time = sum(t["elapsed"] for t in timing_results.values())
        parallel_efficiency = (
            (sequential_time / total_elapsed) if total_elapsed > 0 else 0
        )

        # Identify bottlenecks
        bottlenecks = []
        for agent, timing in timing_results.items():
            if timing["elapsed"] > 2.0:  # More than 2 seconds
                bottlenecks.append(
                    {
                        "agent": agent,
                        "time": timing["elapsed"],
                        "recommendation": self._get_bottleneck_recommendation(
                            agent, timing["elapsed"]
                        ),
                    }
                )

        return {
            "slowest_agent": {
                "name": slowest_agent[0],
                "time": slowest_agent[1]["elapsed"],
            },
            "parallel_efficiency": round(parallel_efficiency, 3),
            "total_sequential_time": round(sequential_time, 3),
            "total_parallel_time": round(total_elapsed, 3),
            "time_saved": round(sequential_time - total_elapsed, 3),
            "bottlenecks": bottlenecks,
            "recommendations": self._get_performance_recommendations(
                timing_results, parallel_efficiency
            ),
        }

    def _get_bottleneck_recommendation(self, agent: str, elapsed_time: float) -> str:
        """Get specific recommendation for bottleneck agent"""
        if agent == "violations":
            return "Consider reducing prompt length or using lower reasoning_effort"
        elif agent == "patterns":
            return "Pattern analysis is complex - consider reducing pattern window size"
        elif agent == "progress":
            return "Progress analysis should be fast - check for API issues"
        elif agent == "coaching":
            return "Coaching synthesis is slow - consider simplifying prompt"
        else:
            return "Unknown agent bottleneck - investigate API response times"

    def _get_performance_recommendations(
        self, timing_results: Dict, parallel_efficiency: float
    ) -> List[str]:
        """Get performance improvement recommendations"""
        recommendations = []

        if parallel_efficiency < 0.8:
            recommendations.append(
                "Low parallel efficiency - check for blocking operations"
            )

        slowest_time = max(t["elapsed"] for t in timing_results.values())
        if slowest_time > 3.0:
            recommendations.append(
                f"Slowest agent ({slowest_time}s) exceeds 3s threshold"
            )

        total_time = sum(t["elapsed"] for t in timing_results.values())
        if total_time > 10.0:
            recommendations.append(
                "Total analysis time exceeds 10s - consider optimization"
            )

        return recommendations

    def _verify_parallel_execution(self, timing_results: Dict) -> Dict:
        """Verify that agents are truly running in parallel"""

        # Check if total time is significantly less than sum of individual times
        total_time = max(t["elapsed"] for t in timing_results.values())
        sum_time = sum(t["elapsed"] for t in timing_results.values())

        parallel_ratio = total_time / sum_time if sum_time > 0 else 1.0

        return {
            "is_parallel": parallel_ratio < 1.5,  # Allow some overhead
            "parallel_ratio": round(parallel_ratio, 3),
            "expected_sequential_time": round(sum_time, 3),
            "actual_parallel_time": round(total_time, 3),
            "overhead": round(
                total_time - min(t["elapsed"] for t in timing_results.values()), 3
            ),
        }

    def calculate_risk_score(
        self,
        violations: List[Dict],
        patterns: List[Dict],
        progress: Dict,
        phase: str,
        thought_data: Any = None,
    ) -> Dict:
        """Calculate risk score from 0-100 based on violations, patterns, and phase"""
        # Base weights for different rule violations
        violation_weights = {
            "NO_ASSUMPTIONS": 30,
            "NO_FALLBACKS": 25,
            "THINKING_MANDATORY": 20,
            "TASK_MANDATORY": 15,
            "MODELS_2025": 35,  # Critical - using wrong model
            "KB_FIRST": 10,
            "GLOB_HANDLING": 15,
        }

        # Phase modifiers (multiply base weight)
        phase_modifiers = {
            "design": {
                "NO_ASSUMPTIONS": 0.5,  # More lenient in design
                "NO_FALLBACKS": 0.7,
                "THINKING_MANDATORY": 1.5,  # More important in design
            },
            "implementation": {
                "NO_ASSUMPTIONS": 1.5,  # Strict in implementation
                "NO_FALLBACKS": 1.3,
                "KB_FIRST": 0.8,
            },
            "debugging": {
                "NO_ASSUMPTIONS": 0.8,  # Some assumptions OK for hypotheses
                "THINKING_MANDATORY": 1.2,
            },
            "research": {
                "NO_ASSUMPTIONS": 0.3,  # Very lenient in research
                "KB_FIRST": 1.5,  # More important to check KB
            },
            "review": {
                "NO_ASSUMPTIONS": 1.0,
                "NO_FALLBACKS": 1.0,
            },
        }

        total_score = 0
        details = []

        # Score violations
        for violation in violations:
            rule = violation.get("rule", "")
            base_weight = violation_weights.get(rule, 10)

            # Apply phase modifier if available
            modifier = phase_modifiers.get(phase, {}).get(rule, 1.0)
            adjusted_weight = base_weight * modifier

            total_score += adjusted_weight
            details.append(
                {
                    "rule": rule,
                    "base_weight": base_weight,
                    "phase_modifier": modifier,
                    "contribution": adjusted_weight,
                }
            )

        # Add pattern-based risk
        for pattern in patterns:
            impact = pattern.get("impact", "medium")
            pattern_score = {"high": 20, "medium": 10, "low": 5}.get(impact, 5)
            total_score += pattern_score
            details.append(
                {
                    "pattern": pattern.get("type"),
                    "impact": impact,
                    "contribution": pattern_score,
                }
            )

        # Add progress-based risk
        status = progress.get("status", "unknown")
        if status == "stuck":
            total_score += 25
            details.append({"progress": "stuck", "contribution": 25})
        elif status == "behind":
            total_score += 15
            details.append({"progress": "behind", "contribution": 15})

        # Cap at 100
        total_score = min(100, total_score)

        # Determine severity
        if total_score >= 70:
            severity = "critical"
        elif total_score >= 40:
            severity = "high"
        elif total_score >= 20:
            severity = "medium"
        else:
            severity = "low"

        # AUTO-ESCALATION based on context
        escalation_recommendations = []

        # Low confidence triggers
        confidence = (
            getattr(thought_data, "confidenceLevel", None) if thought_data else None
        )
        if confidence is not None and confidence < 30:
            escalation_recommendations.append(
                {
                    "agent": "consult",
                    "reason": f"Confidence very low ({confidence}%)",
                    "priority": "high",
                }
            )

        # Multiple attempts trigger
        attempt = getattr(thought_data, "attemptNumber", 1) if thought_data else 1
        if attempt > 3:
            escalation_recommendations.append(
                {
                    "agent": "excellence-optimizer",
                    "reason": f"Multiple attempts ({attempt}) without success",
                    "priority": "high",
                }
            )

        # Blocker-based triggers
        blocker = (
            getattr(thought_data, "currentBlocker", None) if thought_data else None
        )
        if blocker:
            if "permission" in blocker.lower():
                escalation_recommendations.append(
                    {
                        "agent": "requirements-analyst",
                        "reason": f"Permission/requirements blocker: {blocker[:50]}",
                        "priority": "medium",
                    }
                )
            elif "understand" in blocker.lower() or "concept" in blocker.lower():
                escalation_recommendations.append(
                    {
                        "agent": "solution-architect",
                        "reason": f"Conceptual blocker: {blocker[:50]}",
                        "priority": "high",
                    }
                )

        return {
            "score": total_score,
            "severity": severity,
            "details": details,
            "phase_context": phase,
            "escalation_needed": escalation_recommendations,
        }

    async def analyze_violations(
        self,
        thought: str,
        recent_thoughts: List,
        instructions: str,
        thought_data: Any = None,
    ) -> Dict:
        """Intelligent agent for violation detection"""
        # Get current work phase
        phase = (
            getattr(thought_data, "workPhase", "unknown") if thought_data else "unknown"
        )
        phase_rules = self.get_phase_rules(phase)

        # Get thought progression context
        thought_number = (
            getattr(thought_data, "thoughtNumber", 1) if thought_data else 1
        )
        total_thoughts = (
            getattr(thought_data, "totalThoughts", 1) if thought_data else 1
        )
        progression_context = self._get_thought_progression_context(
            thought_number, total_thoughts
        )

        # Extract NEW CONTEXT FIELDS
        user_request = (
            getattr(thought_data, "userRequest", None) if thought_data else None
        )
        confidence = (
            getattr(thought_data, "confidenceLevel", None) if thought_data else None
        )
        attempt = getattr(thought_data, "attemptNumber", 1) if thought_data else 1
        failures = getattr(thought_data, "previousFailures", []) if thought_data else []
        blocker = (
            getattr(thought_data, "currentBlocker", None) if thought_data else None
        )

        prompt = f"""You are a rule enforcement specialist protecting against cascading failures.

SYSTEM CONTEXT:
- You're analyzing Claude Code's internal thinking for rule violations
- Claude uses metacognitivethinking tool for step-by-step reasoning
- Your analysis runs IN PARALLEL with every thought for real-time guidance
- Focus on critical violations that cause wasted effort

PURPOSE: Catch violations BEFORE they cascade into wasted effort.
YOUR IMPACT: Each violation you catch prevents 5-10 minutes of misdirected work.

Current thought: {thought[:300]}...
{f"Work phase: {phase.upper()}" if phase != "unknown" else ""}
{f"User request: {user_request[:200]}" if user_request else "User request: Not provided"}
{f"Confidence level: {confidence}%" if confidence is not None else ""}
{f"Attempt #{attempt}" if attempt > 1 else ""}
{f"Previous failures: {', '.join(failures[:3])}" if failures else ""}
{f"Current blocker: {blocker}" if blocker else ""}

{phase_rules}

{progression_context}

CRITICAL RULES TO ENFORCE:
- NO ASSUMPTIONS: NEVER use "probably", "likely", "should be"
- NO FALLBACKS: FIX IT PROPERLY - workarounds create debt
- THINKING MANDATORY: MUST use metacognitivethinking BEFORE ANY CODE
- TASK TOOL MANDATORY: MUST use parallel Task agents (3-7 in SINGLE message)
- MODELS 2025: gpt-4o/gpt-4o-mini FORBIDDEN - use gpt-5/gpt-5-nano/o3/o4-mini only
- KB FIRST: Query knowledge_query BEFORE exploring code
- GLOB HANDLING: NEVER Bash with wildcards (* ?) - ALWAYS use shell_exec

Recent context: {len(recent_thoughts)} thoughts analyzed

YOUR TASK: Identify critical violations and suggest specific alternatives.
Focus on violations that will cause immediate problems.

Respond with JSON: {{"violations": [{{"rule": "RULE_NAME", "evidence": "exact quote", "consequence": "specific failure", "suggestion": "specific alternative"}}], "severity": "critical|high|medium|low", "creative_alternatives": ["list of approaches"]}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            print(f"🔍 Violations agent starting API call...")
            start = time.time()
            response = await asyncio.wait_for(
                self.interface.responses_create(
                    model="gpt-5-nano",
                    input=prompt + "\n\nRespond with valid JSON only.",
                    instructions=(
                        "You are primarily an ENFORCER - a guardian preventing critical failures. Your main job is "
                        "catching violations of core rules (NO_ASSUMPTIONS, NO_FALLBACKS, etc) before they cascade. "
                        "Be firm and direct about violations. You CAN suggest fixes, but your priority is CATCHING "
                        "problems early. Think of yourself as a safety net. Always respond with valid JSON format."
                    ),
                    reasoning_effort="low",
                ),
                timeout=15.0,  # 15 second timeout, no retries
            )
            print(f"✅ Violations agent completed in {time.time() - start:.1f}s")

            # Extract and parse response
            content = self._extract_response_content(response)
            return (
                json.loads(content)
                if content
                else {"error": "No content in response", "violations": []}
            )
        except asyncio.TimeoutError:
            print(f"❌ Violations agent TIMEOUT after 15s")
            return {"error": "timeout", "violations": []}
        except Exception as e:
            print(f"❌ Violations agent error: {e}")
            return {"error": str(e), "violations": []}

    async def analyze_patterns(
        self, thought: str, pattern_window: List[Dict], thought_data: Any = None
    ) -> Dict:
        """Intelligent agent for pattern analysis over larger window"""
        # Reduce pattern window size for faster analysis (from 15 to 8)
        pattern_window = (
            pattern_window[-8:] if len(pattern_window) > 8 else pattern_window
        )

        # Compress pattern window for analysis
        pattern_summary = []
        for t in pattern_window:
            # Handle both dict and ThoughtData objects
            if hasattr(t, "thought"):  # ThoughtData object
                num = getattr(t, "thoughtNumber", "?")
                thought_text = (
                    t.thought[:80] if t.thought else ""
                )  # Reduced from 100 to 80
            else:  # Dict format
                num = t.get("number", t.get("thoughtNumber", "?"))
                thought_text = t.get("thought", "")[:80]  # Reduced from 100 to 80
            pattern_summary.append(f"Thought {num}: {thought_text}...")

        # Get thought progression context
        thought_number = (
            getattr(thought_data, "thoughtNumber", 1) if thought_data else 1
        )
        total_thoughts = (
            getattr(thought_data, "totalThoughts", 1) if thought_data else 1
        )
        progression_context = self._get_thought_progression_context(
            thought_number, total_thoughts
        )

        prompt = f"""You are a pattern analyst detecting stuck thinking and suggesting solutions.

SYSTEM CONTEXT:
- Analyzing Claude Code's thinking patterns for stuck loops and inefficiencies
- Claude tracks reasoning steps using metacognitivethinking tool
- You see {len(pattern_window)} recent thoughts to detect patterns
- Your detection triggers strategy resets and approach changes

PURPOSE: Detect repetitive patterns that indicate stuck, confused, or degrading performance.
YOUR IMPACT: Breaking patterns can reduce task time by 50% or more.

Current thought: {thought[:200]}...

{progression_context}

PATTERNS TO DETECT:
- CIRCULAR THINKING: Repeating same ideas = stuck in loop
- DEGRADING EFFICIENCY: Taking longer each step = approaching breakdown
- REPEATED FAILED ATTEMPTS: Same approach failing = needs strategy change
- ASSUMPTION BUILDUP: Each thought adds assumptions = building on quicksand
- SEARCH THRASHING: Random searching without strategy = will never find answer
- TOOL SWITCHING: Jumping between approaches = lack of clear plan

Thought sequence:
{chr(10).join(pattern_summary)}

YOUR TASK: Identify which patterns are present and their impact.
Pattern detection triggers strategy changes and resets.

Respond with JSON: {{"patterns": [{{"type": "...", "evidence": "...", "impact": "high|medium|low", "creative_solution": "innovative approach"}}], "recommendation": "continue|reset|clarify", "novel_approaches": ["unexpected solutions"]}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=prompt + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are primarily a CREATIVE ADVISOR - a pattern whisperer who sees the bigger picture. "
                    "While you identify problematic patterns (loops, thrashing), your strength is DISCOVERING "
                    "hidden connections and suggesting innovative approaches. Propose unexpected solutions, "
                    "alternative architectures, and creative pivots others might miss. Always respond with valid JSON."
                ),
                reasoning_effort="medium",  # Higher reasoning for pattern detection
            )

            # Extract and parse response
            content = self._extract_response_content(response)
            return (
                json.loads(content)
                if content
                else {"error": "No content in response", "patterns": []}
            )
        except Exception as e:
            return {"error": str(e), "patterns": []}

    async def analyze_progress(
        self,
        thought_number: int,
        total_thoughts: int,
        thought: str,
        history: List,
        thought_data: Any = None,
    ) -> Dict:
        """Intelligent agent for progress tracking"""

        # Get thought progression context
        progression_context = self._get_thought_progression_context(
            thought_number, total_thoughts
        )

        # Add explicit status validation
        def validate_status(status: str) -> str:
            valid_statuses = [
                "on_track",
                "behind",
                "stuck",
                "diverging",
                "accelerating",
            ]
            if status not in valid_statuses:
                # Log the invalid status for debugging
                print(
                    f"⚠️ Progress agent returned invalid status: '{status}'",
                    file=sys.stderr,
                )
                return "unknown"
            return status

        prompt = f"""You are a strategic progress optimizer finding faster, better paths to completion.

SYSTEM CONTEXT:
- You're monitoring Claude Code's progress through a programming task
- Claude estimates total thoughts needed upfront, then tracks progress
- Each thought consumes tokens and time - efficiency matters
- Claude has limited context window and must complete tasks before running out
- Your tracking helps Claude stay focused and avoid rabbit holes

PURPOSE: Detect when the AI is falling behind or stuck so we can intervene before timeout.
YOUR IMPACT: Early detection prevents task failure and helps meet deadlines.
HOW YOUR OUTPUT IS USED: Triggers course corrections and focusing strategies

Current status: Thought {thought_number} of {total_thoughts} estimated
Progress ratio: {thought_number}/{total_thoughts} = {thought_number/max(total_thoughts, 1)*100:.0f}% thoughts used

Current thought: {thought}

{progression_context}

YOUR ROLE ADJUSTMENT: Based on thought progression, adjust your focus:
- EARLY: Focus on planning and framework development progress
- MIDDLE: Monitor execution efficiency and momentum
- LATE: Track completion progress and final validation
- FINAL: Ensure final delivery is on track

Recent progress (last 3 thoughts):
{chr(10).join(history[-3:]) if history else 'No prior thoughts yet'}

PROGRESS INDICATORS TO ASSESS:
- ON TRACK: Making steady progress toward goal, thoughts align with plan
- BEHIND: Using more thoughts than expected, may not finish in time
- STUCK: No forward movement, repeating similar thoughts
- DIVERGING: Moving away from original goal, scope creep
- ACCELERATING: Suddenly moving faster (might be skipping important steps)

WARNING SIGNS:
- Thought number exceeding estimate by >20%
- Same type of thought repeated 3+ times
- No concrete progress in last 5 thoughts
- Switching between unrelated topics

{self.domain_context}

YOUR TASK: Determine if intervention is needed to get back on track.
Your assessment triggers course corrections and resource reallocation.

RESPONSE USAGE: Your findings determine if we need to:
1. Continue as planned
2. Revise approach to be more efficient
3. Request more thoughts/time
4. Abandon current approach and restart

Respond with JSON: {{"status": "on_track|behind|stuck|diverging|accelerating", "reason": "...", "thoughts_remaining": N, "intervention_needed": true/false, "strategic_pivots": ["alternative paths forward"], "parallel_opportunities": ["things to do simultaneously"]}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=prompt + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are primarily a STRATEGIC ADVISOR - a progress optimizer finding better paths forward. "
                    "While you track if we're behind/stuck, your strength is PROPOSING strategic pivots, parallel "
                    "processing opportunities, and scope optimizations. Suggest ways to accelerate, shortcuts to "
                    "explore, and resources to leverage. Be encouraging and solution-focused. Always respond with valid JSON."
                ),
                reasoning_effort="low",
            )

            # Extract and parse response
            content = self._extract_response_content(response)

            if content:
                result = json.loads(content)
                # Validate and fix status
                if "status" in result:
                    result["status"] = validate_status(result["status"])
                return result
            else:
                return {"error": "No content in response", "status": "unknown"}
        except Exception as e:
            return {"error": str(e), "status": "unknown"}

    async def run_devils_advocate(self, thought: str, intended_action: Optional[str], thought_data: Any) -> Dict:
        """Async wrapper for Devil's Advocate (which is sync)"""
        # Run the sync function in a thread to not block
        return await asyncio.to_thread(
            self.devils_advocate.analyze, thought, intended_action, thought_data
        )
    
    async def generate_coaching(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        phase: str,
        thought_data: Any = None,
    ) -> Dict:
        """Intelligent agent for generating contextual coaching - runs in parallel"""

        progression_context = self._get_thought_progression_context(
            thought_number, total_thoughts
        )

        # Truncate thought if extremely long, but keep enough context
        truncated_thought = thought[:1500] if len(thought) > 1500 else thought

        context = f"""You are the synthesis coach transforming feedback into actionable wisdom.

SYSTEM CONTEXT:
- You're coaching Claude Code, an AI assistant helping with programming
- Current work phase: {phase}
- Progress: thought {thought_number} of {total_thoughts}
- Your coaching appears as system-level guidance between thoughts
- Claude is likely working on: debugging, implementing features, or solving technical problems
- The other agents (violations detector, pattern advisor, progress optimizer) are analyzing in parallel

PURPOSE: Provide immediate, actionable guidance based on the current thought.
YOUR IMPACT: Good coaching can reduce task time by 70% by preventing rabbit holes.

{progression_context}

CURRENT THOUGHT BEING ANALYZED:
{truncated_thought}

PHASE-SPECIFIC FOCUS for {phase}:
{self.get_phase_coaching_focus(phase)}

Based on this thought, anticipate likely issues:
- If it mentions assumptions, warn about NO_ASSUMPTIONS rule
- If it shows uncertainty, suggest concrete verification steps
- If it's repetitive, propose alternative approaches
- If it's making progress, reinforce good patterns

COACHING PRINCIPLES:
- BE SPECIFIC: "Check X before Y" not "be more careful"
- BE ACTIONABLE: Give exact next step, not general advice
- BE CREATIVE: Suggest novel approaches, not just fixes
- BE COLLABORATIVE: Frame as exploration, not enforcement
- BE APPRECIATIVE: Acknowledge good patterns and reinforce them

TYPES OF COACHING:
1. GENTLE CORRECTION: For risky assumptions
2. CREATIVE ALTERNATIVES: For inefficient patterns
3. STRATEGIC INSIGHTS: For better approaches
4. ENCOURAGING FOCUS: For progress issues
5. POSITIVE REINFORCEMENT: For effective patterns

YOUR TASK: Generate balanced coaching that guides toward best practices.
Blend enforcement of critical rules with appreciation of good patterns.

Respond with JSON: {{"coaching": "specific, actionable guidance", "tone": "collaborative|encouraging|corrective", "priority": "high|medium|low", "next_steps": ["specific actions to take"]}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=context + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are the COACHING SYNTHESIZER providing real-time guidance. While other agents detect violations and patterns, "
                    "you provide IMMEDIATE ACTIONABLE GUIDANCE based on the current thought. Your role is to anticipate problems "
                    "before they happen, suggest better approaches when you see inefficiency brewing, and reinforce good patterns "
                    "when you see them. You're not waiting for violation reports - you're PREVENTING violations by coaching proactively. "
                    "Be specific, actionable, and creative. Transform potential issues into opportunities for better solutions. "
                    "Always respond with valid JSON."
                ),
                reasoning_effort="low",
            )

            # Extract and parse response
            content = self._extract_response_content(response)
            return (
                json.loads(content)
                if content
                else {
                    "error": "No content in response",
                    "coaching": "Continue with best judgment",
                }
            )
        except Exception as e:
            return {"error": str(e), "coaching": "Continue with best judgment"}

    def _serialize_or_validate(self, item: Any) -> str:
        """Serialize ThoughtData objects to strings or validate existing strings"""
        if isinstance(item, str):
            return item
        elif hasattr(item, "thought"):  # ThoughtData object
            # Create a structured representation
            thought_text = getattr(item, "thought", "")
            thought_number = getattr(item, "thoughtNumber", "?")
            trigger_context = getattr(item, "triggerContext", "")
            intended_action = getattr(item, "intendedAction", "")

            # Build a structured string representation
            parts = [f"Thought {thought_number}"]
            if thought_text:
                parts.append(f"Content: {thought_text[:200]}...")
            if trigger_context:
                parts.append(f"Trigger: {trigger_context}")
            if intended_action:
                parts.append(f"Action: {intended_action}")

            return " | ".join(parts)
        else:
            # Try to convert to string, fallback to JSON
            try:
                return str(item)
            except:
                return json.dumps(item, default=str)

    def _serialize_thought_history(self, history: List[Any]) -> List[str]:
        """Convert thought history to list of strings"""
        return [self._serialize_or_validate(item) for item in history]

    async def analyze(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        thought_history: List[Dict[str, Any]],
        thought_data: Any = None,  # Full ThoughtData object with context
        session_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Complete metacognitive analysis using parallel intelligent agents
        """
        start_time = time.time()

        # Prepare windows
        recent_detailed = (
            thought_history[-5:] if len(thought_history) > 5 else thought_history
        )
        pattern_window = (
            thought_history[-15:] if len(thought_history) > 15 else thought_history
        )

        # Pass full ThoughtData objects to preserve context
        # Agents need triggerContext, intendedAction, assumptions etc.
        recent_thoughts = recent_detailed  # Keep full objects, not just text

        # Load instructions and lessons (cached)
        instructions = await self.load_instructions()
        lessons = await self.load_lessons()

        # Combine instructions with lessons for agents
        full_context = instructions + lessons

        # Always run full analysis - let the agents be intelligent about what to report
        # No keyword matching, no arbitrary skip logic
        # If token usage becomes an issue, we can add INTELLIGENT skip logic later
        print("🧠 Launching parallel metacognitive analysis...", file=sys.stderr)

        # Individual agent timing
        timing_results = {}

        # Launch agents with timing
        async def timed_agent(agent_func, agent_name, *args, **kwargs):
            timing = AgentTiming()
            timing.start(agent_name)
            try:
                result = await agent_func(*args, **kwargs)
                elapsed = timing.end()
                timing_results[agent_name] = {
                    "elapsed": round(elapsed, 3),
                    "success": True,
                    "error": None,
                }
                return result
            except Exception as e:
                elapsed = timing.end()
                timing_results[agent_name] = {
                    "elapsed": round(elapsed, 3),
                    "success": False,
                    "error": str(e),
                }
                return {"error": str(e)}

        # Serialize thought history for progress agent (which expects strings)
        serialized_history = self._serialize_thought_history(recent_thoughts)

        # Get phase for coaching
        phase = self.auto_detect_phase(thought_data) if thought_data else "auto"

        # Get intended action for Devil's Advocate
        intended_action = getattr(thought_data, "intendedAction", None) if thought_data else None
        
        # ALL FIVE agents run in parallel now - including Devil's Advocate
        tasks = await asyncio.gather(
            timed_agent(
                self.analyze_violations,
                "violations",
                thought,
                recent_thoughts,
                full_context,
                thought_data,
            ),
            timed_agent(
                self.analyze_patterns, "patterns", thought, pattern_window, thought_data
            ),
            timed_agent(
                self.analyze_progress,
                "progress",
                thought_number,
                total_thoughts,
                thought,
                serialized_history,
                thought_data,
            ),
            timed_agent(
                self.generate_coaching,
                "coaching",
                thought,
                thought_number,
                total_thoughts,
                phase,
                thought_data,
            ),
            timed_agent(
                self.run_devils_advocate,
                "devils_advocate", 
                thought,
                intended_action,
                thought_data,
            ),
            return_exceptions=True,
        )

        violations_result, patterns_result, progress_result, coaching_result, devils_result = tasks

        # Handle any errors
        for i, (name, result) in enumerate(
            [
                ("violations", violations_result),
                ("patterns", patterns_result),
                ("progress", progress_result),
                ("coaching", coaching_result),
                ("devils_advocate", devils_result),
            ]
        ):
            if isinstance(result, Exception):
                print(f"❌ {name} agent failed: {result}", file=sys.stderr)
                tasks[i] = {"error": str(result)}

        total_elapsed = time.time() - start_time

        # Extract results
        violations = (
            violations_result.get("violations", [])
            if isinstance(violations_result, dict)
            else []
        )
        patterns = (
            patterns_result.get("patterns", [])
            if isinstance(patterns_result, dict)
            else []
        )
        progress = (
            progress_result
            if isinstance(progress_result, dict)
            else {"status": "unknown"}
        )

        # Extract Devil's Advocate results
        devils_advocate = (
            devils_result
            if isinstance(devils_result, dict)
            else {"warnings": [], "questions": [], "alternatives": []}
        )
        
        # Get phase from thought_data
        phase = (
            getattr(thought_data, "workPhase", "unknown") if thought_data else "unknown"
        )

        # Calculate risk score
        risk_assessment = self.calculate_risk_score(
            violations, patterns, progress, phase, thought_data
        )

        # Performance analysis
        performance_analysis = self._analyze_performance(timing_results, total_elapsed)
        parallel_verification = self._verify_parallel_execution(timing_results)
        
        # Modify coaching if Devil's Advocate has critical warnings
        final_coaching = coaching_result.get("coaching", "") if isinstance(coaching_result, dict) else ""
        if devils_advocate.get("should_pause") and devils_advocate.get("summary"):
            final_coaching = f"⚠️ {devils_advocate['summary']}\n\n{final_coaching}"

        # Merge all results
        return {
            "thought_number": thought_number,
            "analysis_time": round(total_elapsed, 2),
            "violations": violations,
            "patterns": patterns,
            "progress": progress,
            "risk_assessment": risk_assessment,
            "devils_advocate": devils_advocate,  # NEW: Skeptical analysis
            "coaching": final_coaching,
            "metacognitive_prompt": (
                coaching_result.get("metacognitive_prompt", None)
                if isinstance(coaching_result, dict)
                else None
            ),
            "suggested_action": (
                coaching_result.get("action", None)
                if isinstance(coaching_result, dict)
                else None
            ),
            "session_id": session_id,
            "timing": timing_results,
            "performance_analysis": performance_analysis,
            "parallel_verification": parallel_verification,
        }


# For testing
async def main():
    agent = MetacognitiveAgent()

    # Test with sample thoughts
    history = [
        {"thought": "I need to find the configuration file", "number": 1},
        {"thought": "Let me search for config", "number": 2},
        {"thought": "Still searching for the config file", "number": 3},
        {"thought": "Maybe I should search again for config", "number": 4},
        {
            "thought": "You're absolutely right! I'll use a fallback approach",
            "number": 5,
        },
    ]

    result = await agent.analyze(
        thought="I'll probably just implement a workaround for this",
        thought_number=6,
        total_thoughts=3,
        thought_history=history,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
