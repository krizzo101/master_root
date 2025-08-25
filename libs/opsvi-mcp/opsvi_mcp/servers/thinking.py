#!/usr/bin/env python3
"""
FastMCP-based thinking server with integrated triage support.
Direct module integration for sub-50ms triage latency.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

# Add paths
sys.path.insert(0, "/home/opsvi/master_root/libs")
sys.path.insert(0, "/home/opsvi/master_root/apps")

from fastmcp import FastMCP  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

# Import triage module directly for speed
sys.path.insert(0, "/home/opsvi/master_root/apps/thinking-supervisor/triage-service")
from triage_module import TriageAnalyzer  # noqa: E402


class ThoughtData(BaseModel):
    """Validated thought data structure"""

    thought: str = Field(description="Current thinking step")
    thoughtNumber: int = Field(description="Current thought number", ge=1)
    totalThoughts: int = Field(description="Estimated total thoughts", ge=1)
    nextThoughtNeeded: bool = Field(description="Whether another thought is needed")

    # Optional revision/branching
    isRevision: Optional[bool] = Field(
        None, description="Whether this revises previous thinking"
    )
    revisesThought: Optional[int] = Field(
        None, description="Which thought is being reconsidered"
    )
    branchFromThought: Optional[int] = Field(
        None, description="Branching point thought number"
    )
    branchId: Optional[str] = Field(None, description="Branch identifier")
    needsMoreThoughts: Optional[bool] = Field(
        None, description="If more thoughts are needed"
    )

    # Metacognitive fields
    metaObservation: Optional[str] = Field(
        None, description="Observation about the thinking process"
    )
    questionAssumption: Optional[str] = Field(
        None, description="An assumption being questioned"
    )
    patternRecognized: Optional[str] = Field(
        None, description="A pattern you've noticed"
    )
    improvementIdentified: Optional[str] = Field(
        None, description="A potential improvement"
    )
    redundancyDetected: Optional[str] = Field(
        None, description="Unnecessary complexity spotted"
    )
    metacognitiveType: Optional[str] = Field(
        None, description="Category of metacognitive observation"
    )


class StoredInsight(BaseModel):
    """Stored metacognitive insight"""

    timestamp: float
    type: str
    content: str
    thoughtContext: int


class ThinkingServer:
    """Fast thinking server with integrated triage"""

    def __init__(self):
        self.thought_history: List[ThoughtData] = []
        self.branches: Dict[str, List[ThoughtData]] = {}
        self.metacognitive_insights: List[StoredInsight] = []
        self.metacognitive_counter = 0
        self.metacognitive_interval = int(os.getenv("METACOGNITIVE_INTERVAL", "5"))

        # Initialize triage analyzer
        self.triage_analyzer = TriageAnalyzer()
        self.triage_mode = os.getenv(
            "TRIAGE_MODE", "advisory"
        )  # shadow|advisory|enforce
        self.session_id = os.getenv("SESSION_ID", "default")

    def generate_metacognitive_prompt(self) -> str:
        """Generate rotating metacognitive prompts"""
        prompts = [
            "Is there redundancy or unnecessary complexity here?",
            "What assumptions am I making? Should I verify them?",
            "Is this a pattern I've seen before that needs a systemic fix?",
            "Am I solving the real problem or just the symptom?",
            "How could this process or instruction be improved?",
            "Is there a simpler way to achieve this goal?",
            "What would happen if I questioned this requirement?",
            "Could this be automated or abstracted?",
        ]
        return prompts[self.metacognitive_counter % len(prompts)]

    def store_insight(self, insight_type: str, content: str, thought_number: int):
        """Store metacognitive insight"""
        self.metacognitive_insights.append(
            StoredInsight(
                timestamp=time.time(),
                type=insight_type,
                content=content,
                thoughtContext=thought_number,
            )
        )

    async def process_thought(self, data: ThoughtData) -> Dict[str, Any]:
        """Process a thought with optional triage"""

        # Adjust total thoughts if needed
        if data.thoughtNumber > data.totalThoughts:
            data.totalThoughts = data.thoughtNumber

        # Store thought
        self.thought_history.append(data)
        self.metacognitive_counter += 1

        # Store metacognitive insights
        if data.metaObservation:
            self.store_insight("observation", data.metaObservation, data.thoughtNumber)
        if data.improvementIdentified:
            self.store_insight(
                "improvement", data.improvementIdentified, data.thoughtNumber
            )
        if data.redundancyDetected:
            self.store_insight(
                "redundancy", data.redundancyDetected, data.thoughtNumber
            )
        if data.patternRecognized:
            self.store_insight("pattern", data.patternRecognized, data.thoughtNumber)

        # Prepare response
        response = {
            "thoughtNumber": data.thoughtNumber,
            "totalThoughts": data.totalThoughts,
            "nextThoughtNeeded": data.nextThoughtNeeded,
            "branches": list(self.branches.keys()),
            "thoughtHistoryLength": len(self.thought_history),
            "metacognitivePrompt": None,
            "recentInsights": [],
            "insightCount": len(self.metacognitive_insights),
            "triage": None,
            "triageError": None,
        }

        # Add metacognitive prompt periodically
        if self.metacognitive_counter % self.metacognitive_interval == 0:
            response["metacognitivePrompt"] = self.generate_metacognitive_prompt()

        # Get recent insights
        if self.metacognitive_insights:
            response["recentInsights"] = [
                {"type": i.type, "content": i.content}
                for i in self.metacognitive_insights[-3:]
            ]

        # Run triage analysis (only if enabled and every 5 thoughts)
        if self.triage_mode != "disabled" and data.thoughtNumber % 5 == 0:
            try:
                # Build history
                history = [t.thought for t in self.thought_history[-5:]]

                # Run triage analysis
                triage_result = await self.triage_analyzer.analyze(
                    thought=data.thought,
                    thought_number=data.thoughtNumber,
                    session_id=self.session_id,
                    history=history,
                    context={"mode": self.triage_mode},
                )

                # Include triage if it found issues or in advisory mode
                if (
                    triage_result.get("violations")
                    or triage_result.get("patterns")
                    or self.triage_mode == "advisory"
                ):
                    response["triage"] = triage_result

            except Exception as e:
                response["triageError"] = str(e)

        return response

    def get_insights_summary(self) -> Dict[str, Any]:
        """Get summary of metacognitive insights"""
        if not self.metacognitive_insights:
            return {"message": "No insights collected yet", "count": 0}

        # Group by type
        by_type = {}
        for insight in self.metacognitive_insights:
            if insight.type not in by_type:
                by_type[insight.type] = []
            by_type[insight.type].append(
                {"content": insight.content, "thoughtContext": insight.thoughtContext}
            )

        return {
            "totalInsights": len(self.metacognitive_insights),
            "insightsByType": by_type,
            "recentInsights": [
                {
                    "type": i.type,
                    "content": i.content,
                    "thoughtContext": i.thoughtContext,
                }
                for i in self.metacognitive_insights[-10:]
            ],
        }


# Create FastMCP app
mcp = FastMCP("thinking-server")

# Create server instance
thinking_server = ThinkingServer()


@mcp.tool()
async def metacognitivethinking(
    thought: str = Field(description="Your current thinking step"),
    thoughtNumber: int = Field(description="Current thought number", ge=1),
    totalThoughts: int = Field(description="Estimated total thoughts needed", ge=1),
    nextThoughtNeeded: bool = Field(
        description="Whether another thought step is needed"
    ),
    isRevision: Optional[bool] = Field(
        None, description="Whether this revises previous thinking"
    ),
    revisesThought: Optional[int] = Field(
        None, description="Which thought is being reconsidered"
    ),
    branchFromThought: Optional[int] = Field(
        None, description="Branching point thought number"
    ),
    branchId: Optional[str] = Field(None, description="Branch identifier"),
    needsMoreThoughts: Optional[bool] = Field(
        None, description="If more thoughts are needed"
    ),
    metaObservation: Optional[str] = Field(
        None, description="Observation about the thinking process itself"
    ),
    questionAssumption: Optional[str] = Field(
        None, description="An assumption you're questioning"
    ),
    patternRecognized: Optional[str] = Field(
        None, description="A pattern you've noticed"
    ),
    improvementIdentified: Optional[str] = Field(
        None, description="A potential improvement to process or system"
    ),
    redundancyDetected: Optional[str] = Field(
        None, description="Unnecessary complexity or duplication spotted"
    ),
    metacognitiveType: Optional[str] = Field(
        None, description="Category of metacognitive observation"
    ),
) -> Dict[str, Any]:
    """
    Enhanced thinking tool with metacognitive awareness.
    Includes integrated triage for detecting violations and patterns.
    """

    # Create validated thought data
    thought_data = ThoughtData(
        thought=thought,
        thoughtNumber=thoughtNumber,
        totalThoughts=totalThoughts,
        nextThoughtNeeded=nextThoughtNeeded,
        isRevision=isRevision,
        revisesThought=revisesThought,
        branchFromThought=branchFromThought,
        branchId=branchId,
        needsMoreThoughts=needsMoreThoughts,
        metaObservation=metaObservation,
        questionAssumption=questionAssumption,
        patternRecognized=patternRecognized,
        improvementIdentified=improvementIdentified,
        redundancyDetected=redundancyDetected,
        metacognitiveType=metacognitiveType,
    )

    # Process thought
    return await thinking_server.process_thought(thought_data)


@mcp.tool()
async def getthinkinginsights() -> Dict[str, Any]:
    """
    Retrieve a summary of metacognitive insights collected during thinking sessions.
    """
    return thinking_server.get_insights_summary()


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
