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

# Import metacognitive agent for parallel intelligent analysis
sys.path.insert(0, "/home/opsvi/master_root/apps/thinking-supervisor/triage-service")
from metacognitive_agent import MetacognitiveAgent  # noqa: E402


class ThoughtData(BaseModel):
    """Validated thought data structure"""

    thought: str = Field(description="Current thinking step")
    triggerContext: str = Field(
        description="What triggered this thought (user request, error, result, etc.)"
    )
    thoughtNumber: int = Field(description="Current thought number", ge=1)
    totalThoughts: int = Field(description="Estimated total thoughts", ge=1)
    nextThoughtNeeded: bool = Field(description="Whether another thought is needed")

    # Optional action planning
    intendedAction: Optional[str] = Field(
        None, description="What specific action will be taken next"
    )
    assumptions: Optional[str] = Field(
        None, description="Key assumptions that could be wrong"
    )

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

        # Initialize metacognitive agent for parallel analysis
        self.metacognitive_agent = MetacognitiveAgent()
        self.triage_mode = os.getenv(
            "TRIAGE_MODE", "advisory"
        )  # shadow|advisory|enforce
        self.session_id = os.getenv("SESSION_ID", "default")

    # Metacognitive prompts now come from intelligent agent, not hardcoded

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

        # Metacognitive prompts now come from the intelligent agent, not hardcoded intervals

        # Get recent insights
        if self.metacognitive_insights:
            response["recentInsights"] = [
                {"type": i.type, "content": i.content}
                for i in self.metacognitive_insights[-3:]
            ]

        # Run metacognitive analysis on EVERY thought
        # The agent will intelligently decide when to provide feedback
        if self.triage_mode != "disabled":
            try:
                # Let the metacognitive agent decide when to intervene
                triage_result = await self.metacognitive_agent.analyze(
                    thought=data.thought,
                    thought_number=data.thoughtNumber,
                    total_thoughts=data.totalThoughts,
                    thought_history=self.thought_history,
                    session_id=self.session_id,
                )

                # Include results if analysis found something meaningful
                if (
                    triage_result.get("violations")
                    or triage_result.get("patterns")
                    or triage_result.get("coaching")
                    or triage_result.get("metacognitive_prompt")
                ):
                    response["triage"] = triage_result
                    # Add metacognitive prompt if provided
                    if triage_result.get("metacognitive_prompt"):
                        response["metacognitivePrompt"] = triage_result[
                            "metacognitive_prompt"
                        ]

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
    triggerContext: str = Field(
        description="What triggered this thought (user request, error, previous result, etc.)"
    ),
    thoughtNumber: int = Field(description="Current thought number", ge=1),
    totalThoughts: int = Field(description="Estimated total thoughts needed", ge=1),
    nextThoughtNeeded: bool = Field(
        description="Whether another thought step is needed"
    ),
    intendedAction: Optional[str] = Field(
        None, description="What specific action you plan to take next"
    ),
    assumptions: Optional[str] = Field(
        None, description="Key assumptions you're making that could be wrong"
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
        triggerContext=triggerContext,
        thoughtNumber=thoughtNumber,
        totalThoughts=totalThoughts,
        nextThoughtNeeded=nextThoughtNeeded,
        intendedAction=intendedAction,
        assumptions=assumptions,
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
