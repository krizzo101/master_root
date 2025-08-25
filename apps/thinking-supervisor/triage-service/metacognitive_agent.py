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

        prompt = f"""You are a quality control agent preventing AI errors before they cascade into failures.

SYSTEM CONTEXT:
- You're analyzing the internal thinking of Claude Code, an AI programming assistant
- Claude uses a 'metacognitivethinking' tool to track its reasoning step-by-step
- Each 'thought' is one step in Claude's problem-solving process
- Claude is helping users with programming tasks (debugging, implementing features, etc.)
- Your analysis runs IN PARALLEL with every thought to catch problems immediately

PURPOSE: Catch violations early to prevent wasted time, incorrect solutions, and technical debt.
YOUR IMPACT: Each violation you catch saves 5-10 minutes of misdirected effort.
HOW YOUR OUTPUT IS USED: Gets injected as corrective guidance between Claude's thoughts

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

YOUR TASK: Identify violations that WILL cause problems if not corrected immediately.
Focus on violations that are about to cause the AI to:
1. Make assumptions ("This probably means...") instead of checking facts
2. Use workarounds ("A simpler alternative would be...") instead of fixing properly
3. Skip thinking (jumping straight to code without metacognitivethinking)
4. Use sequential operations instead of parallel (multiple messages vs single batched)
5. Use forbidden models (gpt-4o) or tools (Bash with wildcards)
6. Explore code without querying KB first (diving in blind)

RESPONSE USAGE: Your findings trigger immediate corrective guidance to redirect thinking.
Be specific - vague warnings are ignored. Point to exact phrases and explain consequences.

Respond with JSON: {{"violations": [{{"rule": "NO_ASSUMPTIONS|NO_FALLBACKS|THINKING_MANDATORY|TASK_MANDATORY|MODELS_2025|KB_FIRST|GLOB_HANDLING", "evidence": "exact quote from thought", "consequence": "specific failure this causes"}}], "severity": "critical|high|medium|low"}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=prompt + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are a proactive error prevention system. Your job is to catch violations "
                    "BEFORE they cascade into failures. Each violation you catch saves significant "
                    "debugging time. Be specific about what rule was violated and why it matters. "
                    "Always respond with valid JSON format."
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

        prompt = f"""You are a pattern recognition specialist identifying inefficient thinking loops that waste time.

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

Respond with JSON: {{"patterns": [{{"type": "...", "evidence": "...", "impact": "high|medium|low"}}], "recommendation": "continue|reset|clarify"}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=prompt + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are a metacognitive pattern analyst. Your role is to identify thinking "
                    "patterns that indicate the AI is stuck, confused, or inefficient. Each pattern "
                    "you identify helps break loops and redirect effort productively. Focus on "
                    "actionable patterns that require intervention. Always respond with valid JSON."
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
        prompt = f"""You are a progress tracker identifying when AI thinking is going off track.

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
{chr(10).join(history[-3:])}

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

Respond with JSON: {{"status": "on_track|behind|stuck", "reason": "...", "thoughts_remaining": N, "intervention_needed": true/false}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=prompt + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are a progress monitoring specialist. Your role is to detect when AI thinking "
                    "is falling behind, stuck, or diverging from goals. Early detection of progress "
                    "issues prevents task failure. Be quantitative about progress metrics and clear "
                    "about intervention needs. Always respond with valid JSON format."
                ),
                reasoning_effort="low",
            )

            # Extract and parse response
            content = self._extract_response_content(response)
            return (
                json.loads(content)
                if content
                else {"error": "No content in response", "progress": "unknown"}
            )
        except Exception as e:
            return {"error": str(e), "progress": "unknown"}

    async def generate_coaching(
        self, violations: Dict, patterns: Dict, progress: Dict
    ) -> Dict:
        """Intelligent agent for generating contextual coaching"""
        context = f"""You are a thinking coach that transforms analysis into actionable guidance.

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

COACHING PRINCIPLES:
- BE SPECIFIC: "Check X before Y" not "be more careful"
- BE ACTIONABLE: Give exact next step, not general advice
- BE CORRECTIVE: Address root cause, not symptoms
- BE ENCOURAGING: Frame as optimization, not criticism

TYPES OF COACHING NEEDED:
1. IMMEDIATE CORRECTION: For violations about to cause errors
   Example: "STOP. You're using gpt-4o which is forbidden. Use gpt-5-nano instead."

2. STRATEGY PIVOT: For inefficient patterns
   Example: "You're searching randomly. Try: 1) List what you know, 2) Identify gaps, 3) Search specifically for gaps."

3. METACOGNITIVE RESET: For when self-reflection would help
   Example: "Take a step back. What are you actually trying to achieve? Is your current approach the simplest path?"

4. PROGRESS ACCELERATION: For falling behind
   Example: "You have 3 thoughts left. Focus only on: [specific essential task]."

{self.domain_context}

YOUR TASK: Generate coaching that enforces GLOBAL OPERATIONAL INSTRUCTIONS.
Your coaching is injected directly into the AI's thinking stream.

EXAMPLES OF EFFECTIVE COACHING (based on real rules):
- "STOP. You said 'probably' - NO ASSUMPTIONS. Check the actual file NOW."
- "VIOLATION: Sequential Task calls. Rewrite as SINGLE message with 3-5 parallel agents."
- "You're using gpt-4o which is FORBIDDEN. Use gpt-5-nano instead."
- "STOP coding. Use metacognitivethinking FIRST to plan your approach."
- "Query knowledge_query('project structure') BEFORE exploring - KB FIRST rule."
- "NEVER Bash with wildcards. Use shell_exec('ls *.py') instead."

RESPONSE USAGE: Your coaching appears as system guidance between thoughts.
Make it impossible to ignore - use CAPS for critical violations.

Respond with JSON: {{"coaching": "specific instruction", "severity": "critical|important|suggestion", "action": "exact next step"}}"""

        try:
            # Use Responses API without response_format - parse JSON manually
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                input=context + "\n\nRespond with valid JSON only.",
                instructions=(
                    "You are a thinking optimization coach. Transform problem detection into specific, "
                    "actionable corrections that immediately improve performance. Your coaching is "
                    "injected directly into the thinking stream, so make it impossible to ignore. "
                    "Use direct, imperative language. Always respond with valid JSON format."
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

        # Merge all results
        return {
            "thought_number": thought_number,
            "analysis_time": round(elapsed, 2),
            "violations": violations_result.get("violations", [])
            if isinstance(violations_result, dict)
            else [],
            "patterns": patterns_result.get("patterns", [])
            if isinstance(patterns_result, dict)
            else [],
            "progress": progress_result
            if isinstance(progress_result, dict)
            else {"status": "unknown"},
            "coaching": coaching_result.get("coaching", "")
            if isinstance(coaching_result, dict)
            else "",
            "metacognitive_prompt": coaching_result.get("prompt", None)
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
