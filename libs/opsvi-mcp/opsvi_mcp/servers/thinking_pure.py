#!/usr/bin/env python3
"""
Pure Thinking Tool - Structured cognitive reasoning without agent assistance.
Supports 6 cognitive frameworks for organizing thoughts.
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict
import json
from enum import Enum

# Create the MCP app
mcp = FastMCP("thinking-pure")

class CognitiveFramework(str, Enum):
    """Available cognitive frameworks"""
    COT = "cot"  # Chain of Thought
    TOT = "tot"  # Tree of Thoughts
    REACT = "react"  # Reason-Act-Observe
    FIVE_WHYS = "five_whys"  # Root cause analysis
    SWOT = "swot"  # Strengths, Weaknesses, Opportunities, Threats
    FIRST_PRINCIPLES = "first_principles"  # Break down to fundamentals

class ThoughtData(BaseModel):
    """Data for a pure thinking step"""
    framework: CognitiveFramework = Field(description="Cognitive framework being used")
    thought: str = Field(description="Main thought or reasoning step")
    context: Optional[str] = Field(None, description="Additional context or background")
    
    # Framework-specific fields
    branch_id: Optional[str] = Field(None, description="Branch identifier for ToT")
    depth: int = Field(0, description="Depth level in recursive frameworks")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    conclusion: Optional[str] = Field(None, description="Resulting conclusion or insight")
    
    # For specific frameworks
    why_number: Optional[int] = Field(None, description="Which 'why' in 5 Whys")
    swot_category: Optional[str] = Field(None, description="SWOT category: S/W/O/T")
    principle_level: Optional[int] = Field(None, description="Level of first principle breakdown")

# Session storage for thoughts
thought_sessions: Dict[str, List[ThoughtData]] = {}
branches: Dict[str, Dict[str, List[ThoughtData]]] = {}  # For ToT


def process_cot(thoughts: List[ThoughtData]) -> str:
    """Process Chain of Thought reasoning"""
    output = "## Chain of Thought\n\n"
    for i, t in enumerate(thoughts, 1):
        output += f"{i}. {t.thought}\n"
        if t.evidence:
            output += f"   Evidence: {', '.join(t.evidence)}\n"
        if t.conclusion:
            output += f"   → {t.conclusion}\n"
    return output


def process_tot(session_id: str) -> str:
    """Process Tree of Thoughts with branches"""
    output = "## Tree of Thoughts\n\n"
    session_branches = branches.get(session_id, {})
    
    for branch_id, thoughts in session_branches.items():
        output += f"### Branch: {branch_id}\n"
        for t in thoughts:
            output += f"- {t.thought}\n"
            if t.conclusion:
                output += f"  Conclusion: {t.conclusion}\n"
    return output


def process_react(thoughts: List[ThoughtData]) -> str:
    """Process ReAct cycles"""
    output = "## ReAct Reasoning\n\n"
    for t in thoughts:
        if t.depth % 3 == 0:
            output += f"**Reason {t.depth//3 + 1}:** {t.thought}\n"
        elif t.depth % 3 == 1:
            output += f"**Action:** {t.thought}\n"
        else:
            output += f"**Observe:** {t.thought}\n\n"
    return output


def process_five_whys(thoughts: List[ThoughtData]) -> str:
    """Process 5 Whys analysis"""
    output = "## 5 Whys Analysis\n\n"
    for t in thoughts:
        if t.why_number:
            output += f"**Why {t.why_number}:** {t.thought}\n"
            if t.conclusion:
                output += f"Answer: {t.conclusion}\n\n"
    return output


def process_swot(thoughts: List[ThoughtData]) -> str:
    """Process SWOT analysis"""
    swot_data = {"S": [], "W": [], "O": [], "T": []}
    
    for t in thoughts:
        if t.swot_category:
            swot_data[t.swot_category].append(t.thought)
    
    output = "## SWOT Analysis\n\n"
    output += "### Strengths\n" + "\n".join(f"- {s}" for s in swot_data["S"]) + "\n\n"
    output += "### Weaknesses\n" + "\n".join(f"- {w}" for w in swot_data["W"]) + "\n\n" 
    output += "### Opportunities\n" + "\n".join(f"- {o}" for o in swot_data["O"]) + "\n\n"
    output += "### Threats\n" + "\n".join(f"- {t}" for t in swot_data["T"]) + "\n\n"
    return output


def process_first_principles(thoughts: List[ThoughtData]) -> str:
    """Process First Principles breakdown"""
    output = "## First Principles Analysis\n\n"
    
    # Group by principle level
    levels = {}
    for t in thoughts:
        level = t.principle_level or 0
        if level not in levels:
            levels[level] = []
        levels[level].append(t)
    
    for level in sorted(levels.keys()):
        output += f"### Level {level}\n"
        for t in levels[level]:
            output += f"- {t.thought}\n"
            if t.assumptions:
                output += f"  Assumptions: {', '.join(t.assumptions)}\n"
    return output


@mcp.tool()
def think(
    framework: str = Field(description="Cognitive framework: cot, tot, react, five_whys, swot, first_principles"),
    thought: str = Field(description="Your thought or reasoning step"),
    session_id: str = Field("default", description="Session ID for tracking thoughts"),
    context: Optional[str] = Field(None, description="Additional context"),
    branch_id: Optional[str] = Field(None, description="Branch ID for ToT"),
    depth: int = Field(0, description="Depth level for recursive frameworks"),
    evidence: Optional[List[str]] = Field(None, description="Supporting evidence"),
    assumptions: Optional[List[str]] = Field(None, description="Assumptions made"),
    conclusion: Optional[str] = Field(None, description="Conclusion reached"),
    why_number: Optional[int] = Field(None, description="Which 'why' in 5 Whys"),
    swot_category: Optional[str] = Field(None, description="SWOT category: S/W/O/T"),
    principle_level: Optional[int] = Field(None, description="Level for first principles"),
) -> str:
    """
    Record a structured thought using a cognitive framework.
    
    This tool helps organize thinking without agent assistance.
    Choose a framework that matches your reasoning style.
    """
    
    try:
        # Validate framework
        framework_enum = CognitiveFramework(framework)
    except ValueError:
        return f"Invalid framework. Choose from: {', '.join([f.value for f in CognitiveFramework])}"
    
    # Create thought data
    thought_data = ThoughtData(
        framework=framework_enum,
        thought=thought,
        context=context,
        branch_id=branch_id,
        depth=depth,
        evidence=evidence or [],
        assumptions=assumptions or [],
        conclusion=conclusion,
        why_number=why_number,
        swot_category=swot_category,
        principle_level=principle_level,
    )
    
    # Store thought in session
    if session_id not in thought_sessions:
        thought_sessions[session_id] = []
    
    # Handle branching for ToT
    if framework_enum == CognitiveFramework.TOT:
        if session_id not in branches:
            branches[session_id] = {}
        if branch_id:
            if branch_id not in branches[session_id]:
                branches[session_id][branch_id] = []
            branches[session_id][branch_id].append(thought_data)
        else:
            # Default branch
            if "main" not in branches[session_id]:
                branches[session_id]["main"] = []
            branches[session_id]["main"].append(thought_data)
    else:
        thought_sessions[session_id].append(thought_data)
    
    return f"✓ {framework_enum.value.upper()} thought recorded in session '{session_id}'"


@mcp.tool()
def export_thoughts(
    session_id: str = Field("default", description="Session ID to export"),
    format: str = Field("markdown", description="Export format: markdown or json"),
) -> str:
    """
    Export thinking session to markdown or JSON.
    """
    
    if session_id not in thought_sessions and session_id not in branches:
        return "No thoughts found for this session"
    
    thoughts = thought_sessions.get(session_id, [])
    
    if format == "json":
        # Export as JSON
        export_data = {
            "session_id": session_id,
            "thoughts": [t.dict() for t in thoughts],
        }
        if session_id in branches:
            export_data["branches"] = {
                bid: [t.dict() for t in ts] 
                for bid, ts in branches[session_id].items()
            }
        return json.dumps(export_data, indent=2)
    
    # Export as markdown
    output = f"# Thinking Session: {session_id}\n\n"
    
    # Group thoughts by framework
    by_framework = {}
    for t in thoughts:
        if t.framework not in by_framework:
            by_framework[t.framework] = []
        by_framework[t.framework].append(t)
    
    # Process each framework
    for framework, framework_thoughts in by_framework.items():
        if framework == CognitiveFramework.COT:
            output += process_cot(framework_thoughts)
        elif framework == CognitiveFramework.TOT:
            output += process_tot(session_id)
        elif framework == CognitiveFramework.REACT:
            output += process_react(framework_thoughts)
        elif framework == CognitiveFramework.FIVE_WHYS:
            output += process_five_whys(framework_thoughts)
        elif framework == CognitiveFramework.SWOT:
            output += process_swot(framework_thoughts)
        elif framework == CognitiveFramework.FIRST_PRINCIPLES:
            output += process_first_principles(framework_thoughts)
    
    return output


@mcp.tool()
def reset_session(
    session_id: str = Field("default", description="Session ID to reset"),
) -> str:
    """
    Reset a thinking session.
    """
    
    if session_id in thought_sessions:
        del thought_sessions[session_id]
    if session_id in branches:
        del branches[session_id]
    
    return f"Session '{session_id}' reset"


@mcp.tool()
def list_frameworks() -> str:
    """
    List available cognitive frameworks with descriptions.
    """
    
    descriptions = {
        CognitiveFramework.COT: "Chain of Thought - Linear, step-by-step reasoning",
        CognitiveFramework.TOT: "Tree of Thoughts - Explore multiple branches and paths",
        CognitiveFramework.REACT: "ReAct - Reason, Act, Observe cycles",
        CognitiveFramework.FIVE_WHYS: "5 Whys - Root cause analysis through iterative questioning",
        CognitiveFramework.SWOT: "SWOT - Analyze Strengths, Weaknesses, Opportunities, Threats",
        CognitiveFramework.FIRST_PRINCIPLES: "First Principles - Break down to fundamental truths",
    }
    
    output = "## Available Cognitive Frameworks\n\n"
    for framework, desc in descriptions.items():
        output += f"- **{framework.value}**: {desc}\n"
    
    return output


if __name__ == "__main__":
    mcp.run()