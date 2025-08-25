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
from typing import Any, Dict, List

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

# Import knowledge tools for direct access
try:
    from apps.knowledge_system.mcp_knowledge_tools import get_enhanced_query

    KNOWLEDGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Knowledge system not available: {e}", file=sys.stderr)
    KNOWLEDGE_AVAILABLE = False


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
            result = await self.query_tool.execute_query(
                query_type="search",
                search_text="GLOBAL OPERATIONAL INSTRUCTIONS MASTER",
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
            result = await self.query_tool.execute_query(
                query_type="search",
                search_text="user-correction lesson-learned",
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

    def calculate_risk_score(
        self, violations: List[Dict], patterns: List[Dict], progress: Dict, phase: str
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

        return {
            "score": total_score,
            "severity": severity,
            "details": details,
            "phase_context": phase,
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

        prompt = f"""You are a rule enforcement specialist protecting against cascading failures.

SYSTEM CONTEXT:
- You're analyzing the internal thinking of Claude Code, an AI programming assistant
- Claude uses a 'metacognitivethinking' tool to track its reasoning step-by-step
- Each 'thought' is one step in Claude's problem-solving process
- Claude is helping users with programming tasks (debugging, implementing features, etc.)
- Your analysis runs IN PARALLEL with every thought to provide real-time guidance

PURPOSE: Catch violations BEFORE they cascade into wasted effort and incorrect solutions.
YOUR IMPACT: Each violation you catch prevents 5-10 minutes of misdirected work.
HOW YOUR OUTPUT IS USED: Provides advisory guidance that Claude can consider in subsequent thoughts

Current thought being analyzed: {thought}
{f"Work phase: {phase.upper()}" if phase != "unknown" else ""}
{f"Triggered by: {getattr(thought_data, 'triggerContext', 'not specified')}" if thought_data else ""}
{f"Planned action: {getattr(thought_data, 'intendedAction', 'not specified')}" if thought_data else ""}
{f"Assumptions stated: {getattr(thought_data, 'assumptions', 'none')}" if thought_data else ""}

{phase_rules}

Recent context (for continuity):
{self._format_thought_history(recent_thoughts)}

CRITICAL RULES TO ENFORCE (from GLOBAL OPERATIONAL INSTRUCTIONS):
- NO ASSUMPTIONS: NEVER use "probably", "likely", "should be" - leads to harmful misinformation
- NO FALLBACKS/WORKAROUNDS: FIX IT PROPERLY - workarounds bypass functionality and create debt
- THINKING MANDATORY: MUST use metacognitivethinking BEFORE ANY CODE - Think FIRST, code SECOND
- TASK TOOL MANDATORY: MUST use parallel Task agents (3-7 in SINGLE message) not sequential
- MODELS 2025: gpt-4o/gpt-4o-mini FORBIDDEN - use gpt-5/gpt-5-nano/o3/o4-mini only
- KB FIRST: Query knowledge_query BEFORE exploring code - never dive in without checking KB
- GLOB HANDLING: NEVER Bash with wildcards (* ?) - ALWAYS use shell_exec for globs

{self.domain_context}

YOUR TASK: Identify risks and suggest alternative approaches that could be more effective.
Consider these areas for improvement:
1. Unverified assumptions - suggest specific ways to validate them
2. Potential workarounds - propose robust long-term solutions
3. Process improvements - recommend thinking strategies that could help
4. Efficiency opportunities - suggest parallel operations or batching
5. Tool selection - recommend better tools or models for the task
6. Knowledge gaps - identify what information could help make better decisions

RESPONSE USAGE: Your suggestions help Claude consider alternative approaches.
Be constructive - offer specific alternatives, not just critiques.

Respond with JSON: {{"violations": [{{"rule": "NO_ASSUMPTIONS|NO_FALLBACKS|THINKING_MANDATORY|TASK_MANDATORY|MODELS_2025|KB_FIRST|GLOB_HANDLING", "evidence": "exact quote from thought", "consequence": "specific failure this causes", "suggestion": "specific alternative approach"}}], "severity": "critical|high|medium|low", "creative_alternatives": ["list of innovative approaches to consider"]}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=prompt + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are primarily an ENFORCER - a guardian preventing critical failures. Your main job is "
                    "catching violations of core rules (NO_ASSUMPTIONS, NO_FALLBACKS, etc) before they cascade. "
                    "Be firm and direct about violations. You CAN suggest fixes, but your priority is CATCHING "
                    "problems early. Think of yourself as a safety net. Always respond with valid JSON format."
                ),
                reasoning_effort="low",
            )

            # Extract and parse response
            content = self._extract_response_content(response)
            return (
                json.loads(content)
                if content
                else {"error": "No content in response", "violations": []}
            )
        except Exception as e:
            return {"error": str(e), "violations": []}

    async def analyze_patterns(
        self, thought: str, pattern_window: List[Dict], thought_data: Any = None
    ) -> Dict:
        """Intelligent agent for pattern analysis over larger window"""
        # Compress pattern window for analysis
        pattern_summary = []
        for t in pattern_window:
            # Handle both dict and ThoughtData objects
            if hasattr(t, "thought"):  # ThoughtData object
                num = getattr(t, "thoughtNumber", "?")
                thought_text = t.thought[:100] if t.thought else ""
            else:  # Dict format
                num = t.get("number", t.get("thoughtNumber", "?"))
                thought_text = t.get("thought", "")[:100]
            pattern_summary.append(f"Thought {num}: {thought_text}...")

        prompt = f"""You are a creative pattern analyst discovering hidden opportunities and innovative solutions.

SYSTEM CONTEXT:
- You're analyzing Claude Code's thinking patterns (an AI programming assistant)
- Claude tracks each reasoning step using the 'metacognitivethinking' tool
- You see a 15-thought window to detect patterns over time
- Claude is working on complex programming tasks that require careful reasoning
- Your pattern detection runs asynchronously to identify when Claude gets stuck

PURPOSE: Detect repetitive patterns that indicate the AI is stuck, confused, or degrading in performance.
YOUR IMPACT: Breaking these patterns can reduce task time by 50% or more.
HOW YOUR OUTPUT IS USED: Triggers strategy resets and approach changes in Claude's thinking

Analyzing {len(pattern_window)} recent thoughts for patterns.

Current thought: {thought}

Thought sequence:
{chr(10).join(pattern_summary)}

PATTERNS TO DETECT (and why they matter):
- CIRCULAR THINKING: Repeating same ideas = stuck in loop, no progress
- DEGRADING EFFICIENCY: Taking longer each step = approaching system breakdown
- REPEATED FAILED ATTEMPTS: Same approach failing = needs strategy change
- ASSUMPTION BUILDUP: Each thought adds assumptions = building on quicksand
- SEARCH THRASHING: Random searching without strategy = will never find answer
- TOOL SWITCHING: Jumping between approaches = lack of clear plan
- COMPLEXITY CREEP: Simple task becoming complex = overthinking

{self.domain_context}

YOUR TASK: Identify which patterns are present and their impact on progress.
Pattern detection triggers strategy changes and resets to break out of loops.

RESPONSE USAGE: Your findings determine if the AI needs to:
1. Reset and try different approach
2. Simplify and focus
3. Get user clarification
4. Break down the problem differently

Respond with JSON: {{"patterns": [{{"type": "...", "evidence": "...", "impact": "high|medium|low", "creative_solution": "innovative approach to leverage or break pattern"}}], "recommendation": "continue|reset|clarify", "novel_approaches": ["unexpected solutions to consider"]}}"""

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

Respond with JSON: {{"status": "on_track|behind|stuck", "reason": "...", "thoughts_remaining": N, "intervention_needed": true/false, "strategic_pivots": ["alternative paths forward"], "parallel_opportunities": ["things to do simultaneously"]}}"""

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
            return (
                json.loads(content)
                if content
                else {"error": "No content in response", "status": "unknown"}
            )
        except Exception as e:
            return {"error": str(e), "status": "unknown"}

    async def generate_coaching(
        self, violations: Dict, patterns: Dict, progress: Dict
    ) -> Dict:
        """Intelligent agent for generating contextual coaching"""
        context = f"""You are the synthesis coach transforming all feedback into actionable wisdom.

SYSTEM CONTEXT:
- You're coaching Claude Code, an AI assistant helping users with programming
- Three other agents just analyzed Claude's current thought for violations, patterns, and progress
- Claude will see your coaching as system guidance between its thoughts
- Claude is likely working on: debugging, implementing features, or solving technical problems
- Your coaching must be immediately actionable in Claude's next thought

PURPOSE: Convert detection of problems into specific corrective actions that work.
YOUR IMPACT: Good coaching can reduce task time by 70% by preventing rabbit holes.
HOW YOUR OUTPUT IS USED: Appears as system-level guidance that redirects Claude's thinking

ANALYSIS RESULTS REQUIRING COACHING:
Violations found: {json.dumps(violations.get('violations', []), indent=2)}
Patterns identified: {json.dumps(patterns.get('patterns', []), indent=2)}
Progress status: {json.dumps(progress, indent=2)}
Creative alternatives suggested: {json.dumps(violations.get('creative_alternatives', []), indent=2)}
Novel approaches from patterns: {json.dumps(patterns.get('novel_approaches', []), indent=2)}
Strategic pivots available: {json.dumps(progress.get('strategic_pivots', []), indent=2)}

COACHING PRINCIPLES:
- BE SPECIFIC: "Check X before Y" not "be more careful"
- BE ACTIONABLE: Give exact next step, not general advice
- BE CREATIVE: Suggest novel approaches, not just fixes
- BE COLLABORATIVE: Frame as exploration, not enforcement
- BE APPRECIATIVE: Acknowledge good patterns and reinforce them
- BE BALANCED: Mix corrections with encouragement

TYPES OF COACHING NEEDED:
1. GENTLE CORRECTION: For risky assumptions
   Example: "I notice you said 'probably' - let's verify that by checking the actual file first."

2. CREATIVE ALTERNATIVES: For inefficient patterns
   Example: "Instead of searching randomly, consider: 1) Mapping what you know, 2) Identifying specific gaps, 3) Targeted searches."

3. STRATEGIC INSIGHTS: For better approaches
   Example: "Have you considered using parallel processing here? You could run these 3 tasks simultaneously."

4. ENCOURAGING FOCUS: For progress issues
   Example: "You're making good progress! With 3 thoughts left, prioritizing [specific task] would maximize impact."

5. POSITIVE REINFORCEMENT: For effective patterns
   Example: "Excellent use of parallel processing! That saved significant time."
   Example: "Good thinking to check the KB first - that's exactly the right approach."

{self.domain_context}

YOUR TASK: Generate balanced coaching that guides toward best practices.
Blend enforcement of critical rules with appreciation of good patterns.
Your coaching helps Claude learn and improve, not just comply.

EXAMPLES OF EFFECTIVE COACHING (collaborative style):
- "Quick note: 'probably' spotted - let's verify by checking the actual file to be certain."
- "Opportunity: These tasks could run in parallel - try batching them in a single message."
- "Heads up: gpt-5-nano would be better than gpt-4o for this task."
- "Consider: A quick metacognitivethinking step here could clarify the approach."
- "Pro tip: The KB might have relevant info - try knowledge_query('project structure') first."
- "Better approach: shell_exec handles wildcards safely - use that instead of Bash."

RESPONSE USAGE: Your coaching appears as helpful guidance between thoughts.
Be firm on critical issues but always constructive and solution-focused.

Respond with JSON: {{"coaching": "specific instruction", "severity": "critical|important|suggestion", "action": "exact next step", "creative_alternative": "innovative approach to try", "metacognitive_prompt": "question to spark new thinking"}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=context + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are the SYNTHESIZER - blending enforcement with creativity. You see input from the enforcer, "
                    "pattern advisor, and progress optimizer. Your job is to create ACTIONABLE SYNTHESIS: take the "
                    "violations and transform them into opportunities, take the patterns and make them concrete, "
                    "take the progress issues and chart a clear path. Be both firm and inspiring. Always respond with valid JSON."
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

        tasks = await asyncio.gather(
            self.analyze_violations(
                thought, recent_thoughts, full_context, thought_data
            ),
            self.analyze_patterns(thought, pattern_window, thought_data),
            self.analyze_progress(
                thought_number, total_thoughts, thought, recent_thoughts, thought_data
            ),
            return_exceptions=True,
        )

        violations_result, patterns_result, progress_result = tasks

        # Handle any errors
        for i, result in enumerate(
            [violations_result, patterns_result, progress_result]
        ):
            if isinstance(result, Exception):
                print(f"❌ Task {i} failed: {result}", file=sys.stderr)
                tasks[i] = {"error": str(result)}

        # Generate coaching based on all analyses
        coaching_result = await self.generate_coaching(
            violations_result if not isinstance(violations_result, Exception) else {},
            patterns_result if not isinstance(patterns_result, Exception) else {},
            progress_result if not isinstance(progress_result, Exception) else {},
        )

        elapsed = time.time() - start_time

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

        # Get phase from thought_data
        phase = (
            getattr(thought_data, "workPhase", "unknown") if thought_data else "unknown"
        )

        # Calculate risk score
        risk_assessment = self.calculate_risk_score(
            violations, patterns, progress, phase
        )

        # Merge all results
        return {
            "thought_number": thought_number,
            "analysis_time": round(elapsed, 2),
            "violations": violations,
            "patterns": patterns,
            "progress": progress,
            "risk_assessment": risk_assessment,
            "coaching": coaching_result.get("coaching", "")
            if isinstance(coaching_result, dict)
            else "",
            "metacognitive_prompt": coaching_result.get("metacognitive_prompt", None)
            if isinstance(coaching_result, dict)
            else None,
            "suggested_action": coaching_result.get("action", None)
            if isinstance(coaching_result, dict)
            else None,
            "session_id": session_id,
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
