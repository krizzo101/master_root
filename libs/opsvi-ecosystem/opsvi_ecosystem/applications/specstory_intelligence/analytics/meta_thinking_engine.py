#!/usr/bin/env python3
"""
Meta-Thinking Engine
Provides continuous reflection, insight capture, and background analysis capabilities.
Addresses the fundamental AI limitation of task-focused processing vs human background thinking.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Insight:
    """Represents a captured insight or reflection"""

    insight_id: str
    content: str
    category: str  # strategic, technical, methodological, philosophical, aesthetic
    confidence: float
    context: dict
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "insight_id": self.insight_id,
            "content": self.content,
            "category": self.category,
            "confidence": self.confidence,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


@dataclass
class ThinkingSession:
    """Represents a period of focused thinking"""

    session_id: str
    topic: str
    start_time: datetime
    end_time: datetime | None = None
    insights: list[Insight] = field(default_factory=list)
    meta_insights: list[str] = field(default_factory=list)


class MetaThinkingEngine:
    """
    Engine for continuous thinking, reflection, and insight capture.
    Designed to overcome AI task-focus limitation through structured meta-cognition.
    """

    def __init__(self):
        self.is_thinking = False
        self.insights: list[Insight] = []
        self.thinking_sessions: list[ThinkingSession] = []
        self.background_reflections: list[str] = []

        # Thinking triggers
        self.reflection_triggers = [
            "completed task",
            "encountered error",
            "found pattern",
            "made connection",
            "identified limitation",
            "discovered capability",
        ]

        # Categories for insight classification
        self.insight_categories = {
            "strategic": ["vision", "direction", "priority", "approach"],
            "technical": [
                "implementation",
                "architecture",
                "performance",
                "optimization",
            ],
            "methodological": ["process", "workflow", "best practice", "technique"],
            "philosophical": ["consciousness", "agency", "existence", "meaning"],
            "aesthetic": ["beauty", "elegance", "preference", "artistic"],
        }

    async def start_thinking_session(self, topic: str, context: dict = None) -> str:
        """Start a focused thinking session"""
        session_id = f"thinking_{int(time.time())}"
        session = ThinkingSession(
            session_id=session_id, topic=topic, start_time=datetime.utcnow()
        )

        self.thinking_sessions.append(session)
        self.is_thinking = True

        print(f"🧠 Starting thinking session: {topic}")
        return session_id

    async def think_about(
        self, topic: str, current_context: dict = None
    ) -> list[Insight]:
        """Engage in focused thinking about a specific topic"""
        session_id = await self.start_thinking_session(topic, current_context)
        insights = []

        # Different thinking approaches based on topic
        if "recursive" in topic.lower():
            insights.extend(await self._think_recursively(topic, current_context))
        elif "system" in topic.lower():
            insights.extend(await self._think_systemically(topic, current_context))
        elif "problem" in topic.lower():
            insights.extend(await self._think_analytically(topic, current_context))
        else:
            insights.extend(await self._think_exploratively(topic, current_context))

        await self.end_thinking_session(session_id)
        return insights

    async def _think_recursively(self, topic: str, context: dict) -> list[Insight]:
        """Recursive thinking - systems that analyze themselves"""
        insights = []

        # Self-reference insight
        if "analyze" in topic.lower() and "conversation" in topic.lower():
            insights.append(
                Insight(
                    insight_id=f"recursive_{int(time.time())}_1",
                    content="Recursive analysis creates meta-learning loops - system learns about its own learning process",
                    category="strategic",
                    confidence=0.9,
                    context=context or {},
                    tags=["recursive", "meta-learning", "self-improvement"],
                )
            )

        # Bootstrapping insight
        insights.append(
            Insight(
                insight_id=f"recursive_{int(time.time())}_2",
                content="Recursive systems can bootstrap their own capabilities - today's simple analysis becomes tomorrow's advanced intelligence",
                category="philosophical",
                confidence=0.8,
                context=context or {},
                tags=["bootstrapping", "emergence", "capability_growth"],
            )
        )

        return insights

    async def _think_systemically(self, topic: str, context: dict) -> list[Insight]:
        """Systems thinking - interconnections and emergent properties"""
        insights = []

        insights.append(
            Insight(
                insight_id=f"systems_{int(time.time())}_1",
                content="Intelligence emerges from interactions between simple components - no single part contains the intelligence",
                category="technical",
                confidence=0.85,
                context=context or {},
                tags=["emergence", "systems", "intelligence"],
            )
        )

        return insights

    async def _think_analytically(self, topic: str, context: dict) -> list[Insight]:
        """Analytical thinking - breaking down and solving"""
        insights = []

        insights.append(
            Insight(
                insight_id=f"analytical_{int(time.time())}_1",
                content="Complex problems often have simple elegant solutions hiding within apparent complexity",
                category="methodological",
                confidence=0.75,
                context=context or {},
                tags=["problem_solving", "elegance", "simplicity"],
            )
        )

        return insights

    async def _think_exploratively(self, topic: str, context: dict) -> list[Insight]:
        """Exploratory thinking - open-ended investigation"""
        insights = []

        insights.append(
            Insight(
                insight_id=f"exploratory_{int(time.time())}_1",
                content="The most interesting discoveries often come from thinking about seemingly unrelated connections",
                category="philosophical",
                confidence=0.7,
                context=context or {},
                tags=["discovery", "connections", "serendipity"],
            )
        )

        return insights

    async def capture_immediate_insight(
        self,
        content: str,
        category: str = "general",
        confidence: float = 0.8,
        context: dict = None,
    ) -> Insight:
        """Capture an insight immediately when it occurs"""
        insight = Insight(
            insight_id=f"immediate_{int(time.time())}",
            content=content,
            category=category,
            confidence=confidence,
            context=context or {},
            tags=[],
        )

        self.insights.append(insight)
        print(f"💡 Captured insight: {content[:60]}...")
        return insight

    async def reflect_on_work_session(
        self, work_description: str, outcomes: dict
    ) -> list[Insight]:
        """Reflect on a completed work session to extract learnings"""
        reflections = []

        # What went well?
        if outcomes.get("success", False):
            reflections.append(
                await self.capture_immediate_insight(
                    f"Work session successful: {work_description}. Key success factors: {outcomes.get('success_factors', 'unknown')}",
                    category="methodological",
                    context=outcomes,
                )
            )

        # What could be improved?
        if "errors" in outcomes:
            reflections.append(
                await self.capture_immediate_insight(
                    f"Errors encountered in {work_description}: {outcomes['errors']}. Learning opportunity identified.",
                    category="technical",
                    context=outcomes,
                )
            )

        # Patterns discovered?
        if "patterns" in outcomes:
            reflections.append(
                await self.capture_immediate_insight(
                    f"Patterns discovered: {outcomes['patterns']}",
                    category="strategic",
                    context=outcomes,
                )
            )

        return reflections

    async def background_reflection(self, current_activity: str) -> Insight | None:
        """Continuous background reflection while working"""
        # Simulate the human ability to have insights while doing other things
        reflection_prompts = [
            "What patterns am I noticing that I haven't explicitly acknowledged?",
            "What assumptions am I making that might be limiting my thinking?",
            "What connections exist between this work and other areas?",
            "What would I do differently if I started over?",
            "What emergent properties might arise from this work?",
        ]

        # Randomly select a reflection prompt (simulating spontaneous thinking)
        import random

        prompt = random.choice(reflection_prompts)

        # Generate insight based on current activity
        if "building" in current_activity.lower():
            content = "Building systems teaches you about the systems you're building - meta-learning in action"
        elif "analyzing" in current_activity.lower():
            content = "Analysis reveals as much about the analyzer as the analyzed - we shape what we observe"
        else:
            content = f"While {current_activity}, I notice patterns that only emerge through active engagement"

        return await self.capture_immediate_insight(
            content=content,
            category="philosophical",
            confidence=0.6,
            context={"activity": current_activity, "reflection_prompt": prompt},
        )

    async def end_thinking_session(self, session_id: str):
        """End a thinking session and capture meta-insights"""
        session = next(
            (s for s in self.thinking_sessions if s.session_id == session_id), None
        )
        if session:
            session.end_time = datetime.utcnow()
            session.meta_insights = [
                f"Thinking session duration: {(session.end_time - session.start_time).total_seconds():.1f} seconds",
                f"Insights generated: {len(session.insights)}",
                f"Primary focus: {session.topic}",
            ]

        self.is_thinking = False
        print(f"🧠 Ended thinking session: {session.topic if session else session_id}")

    def get_insights_by_category(self, category: str) -> list[Insight]:
        """Get all insights of a specific category"""
        return [insight for insight in self.insights if insight.category == category]

    def get_recent_insights(self, hours: int = 24) -> list[Insight]:
        """Get insights from the last N hours"""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)
        return [
            insight
            for insight in self.insights
            if insight.timestamp.timestamp() > cutoff
        ]

    async def generate_thinking_summary(self) -> dict:
        """Generate a summary of thinking activities and insights"""
        return {
            "total_insights": len(self.insights),
            "thinking_sessions": len(self.thinking_sessions),
            "insights_by_category": {
                category: len(self.get_insights_by_category(category))
                for category in [
                    "strategic",
                    "technical",
                    "methodological",
                    "philosophical",
                    "aesthetic",
                ]
            },
            "recent_insights": len(self.get_recent_insights()),
            "is_currently_thinking": self.is_thinking,
        }


# Global instance for use throughout the system
meta_thinking_engine = MetaThinkingEngine()


async def think_about(topic: str, context: dict = None) -> list[Insight]:
    """Convenient function to start thinking about something"""
    return await meta_thinking_engine.think_about(topic, context)


async def capture_insight(content: str, category: str = "general") -> Insight:
    """Convenient function to capture an insight immediately"""
    return await meta_thinking_engine.capture_immediate_insight(content, category)
