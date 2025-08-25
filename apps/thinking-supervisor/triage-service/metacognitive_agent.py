#!/usr/bin/env python3
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
    from apps.knowledge_system.mcp_knowledge_tools import (
        get_enhanced_query,
        get_smart_executor,
    )

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
            self.smart_query = get_smart_executor()
        else:
            self.query_tool = None
            self.smart_query = None

        # Cache for instructions
        self._cached_instructions = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

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

    async def analyze_violations(
        self, thought: str, recent_thoughts: List[str], instructions: str
    ) -> Dict:
        """Intelligent agent for violation detection"""
        prompt = f"""Analyze this thought for violations of operational rules.

Current thought: {thought}

Recent context (last 5 thoughts):
{chr(10).join(recent_thoughts)}

Key rules to check:
- NO ASSUMPTIONS - must verify facts
- NO FALLBACKS/WORKAROUNDS - fix root causes
- NO REFLEXIVE AGREEMENT - evaluate on merits
- BE EXPERT ADVISOR - provide better alternatives

Identify specific violations with evidence."""

        try:
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "You detect violations of operational rules in thinking patterns.",  # noqa: E501
                    },
                    {"role": "user", "content": prompt},
                ],
                reasoning_effort="low",
                temperature=0.3,
                max_completion_tokens=400,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e), "violations": []}

    async def analyze_patterns(self, thought: str, pattern_window: List[Dict]) -> Dict:
        """Intelligent agent for pattern analysis over larger window"""
        # Compress pattern window for analysis
        pattern_summary = []
        for t in pattern_window:
            pattern_summary.append(
                f"Thought {t.get('number', '?')}: {t.get('thought', '')[:100]}..."
            )

        prompt = f"""Analyze thinking patterns across these {len(pattern_window)} thoughts.

Current thought: {thought}

Thought sequence:
{chr(10).join(pattern_summary)}

Identify patterns:
- Circular thinking (repeating same ideas)
- Degrading efficiency (taking longer over time)
- Repeated failed attempts
- Assumption buildup
- Search thrashing"""

        try:
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "You identify patterns in thinking sequences.",
                    },
                    {"role": "user", "content": prompt},
                ],
                reasoning_effort="medium",  # Higher reasoning for pattern detection
                temperature=0.4,
                max_completion_tokens=300,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e), "patterns": []}

    async def analyze_progress(
        self, thought_number: int, total_thoughts: int, thought: str, history: List[str]
    ) -> Dict:
        """Intelligent agent for progress tracking"""
        prompt = f"""Analyze progress of this thinking session.

Current: Thought {thought_number} of {total_thoughts} estimated
Current thought: {thought}

Recent progress:
{chr(10).join(history[-3:])}

Assess:
- Is progress on track, behind, or stuck?
- Why might it be taking longer than estimated?
- Are we making forward progress or spinning?"""

        try:
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "You track and assess thinking progress.",
                    },
                    {"role": "user", "content": prompt},
                ],
                reasoning_effort="low",
                temperature=0.3,
                max_completion_tokens=200,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e), "progress": "unknown"}

    async def generate_coaching(
        self, violations: Dict, patterns: Dict, progress: Dict
    ) -> Dict:
        """Intelligent agent for generating contextual coaching"""
        context = f"""Based on this analysis, provide specific coaching:

Violations found: {json.dumps(violations.get('violations', []), indent=2)}
Patterns identified: {json.dumps(patterns.get('patterns', []), indent=2)}
Progress status: {json.dumps(progress, indent=2)}

Generate:
1. Specific coaching for immediate improvement
2. Metacognitive prompt if self-reflection needed
3. Suggested next action"""

        try:
            response = await self.interface.responses_create(
                model="gpt-5-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "You provide specific coaching to improve thinking.",
                    },
                    {"role": "user", "content": context},
                ],
                reasoning_effort="low",
                temperature=0.5,  # Slightly creative for coaching
                max_completion_tokens=300,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": str(e), "coaching": "Continue with best judgment"}

    async def analyze(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        thought_history: List[Dict[str, Any]],
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

        recent_thoughts = [t.get("thought", "") for t in recent_detailed]

        # Load instructions (cached)
        instructions = await self.load_instructions()

        # Launch ALL analyses in parallel
        print("🧠 Launching parallel metacognitive analysis...", file=sys.stderr)

        tasks = await asyncio.gather(
            self.analyze_violations(thought, recent_thoughts, instructions),
            self.analyze_patterns(thought, pattern_window),
            self.analyze_progress(
                thought_number, total_thoughts, thought, recent_thoughts
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
