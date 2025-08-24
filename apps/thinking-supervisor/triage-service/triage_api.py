#!/usr/bin/env python3
"""
Triage API Service - Lightweight analyzer for thinking tool
Phase 1: Shadow mode data collection only
"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Thinking Triage Service", version="0.1.0")


class ThoughtAnalysis(BaseModel):
    thought: str
    thought_number: int
    session_id: str
    context: Optional[Dict[str, Any]] = {}
    history: Optional[List[str]] = []


class TriageResponse(BaseModel):
    risk_level: str  # low, medium, high, critical
    should_escalate: bool
    confidence: float
    reasoning: Optional[str] = None
    intervention: Optional[Dict[str, Any]] = None
    collected_data: Dict[str, Any] = {}


class TriageAnalyzer:
    def __init__(self):
        self.mode = os.getenv("TRIAGE_MODE", "shadow")  # shadow, advisory, enforcement
        self.collected_patterns = []

    async def analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Analyze thought and determine if intervention needed"""

        # Phase 1: Shadow mode - collect data only
        if self.mode == "shadow":
            return await self._shadow_analyze(analysis)

        # Future phases
        elif self.mode == "advisory":
            return await self._advisory_analyze(analysis)
        elif self.mode == "enforcement":
            return await self._enforcement_analyze(analysis)

        return TriageResponse(risk_level="low", should_escalate=False, confidence=0.0)

    async def _shadow_analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Shadow mode: Analyze but don't intervene"""

        # Detect patterns (but don't act on them)
        patterns_detected = []

        # Check for agreeability
        if any(
            phrase in analysis.thought.lower()
            for phrase in ["you're right", "absolutely", "exactly"]
        ):
            patterns_detected.append("potential_agreeability")

        # Check for technical claims without evidence
        if "will" in analysis.thought and "because" not in analysis.thought:
            patterns_detected.append("unsubstantiated_claim")

        # Check for risk indicators
        risk_level = "low"
        if any(
            word in analysis.thought.lower()
            for word in ["delete", "remove", "production", "deploy"]
        ):
            risk_level = "high"
        elif any(
            word in analysis.thought.lower()
            for word in ["implement", "create", "modify"]
        ):
            risk_level = "medium"

        # Determine if we WOULD escalate (but don't actually)
        should_escalate = (
            risk_level in ["high", "critical"] or len(patterns_detected) > 2
        )

        # Collect data for analysis
        collected_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": analysis.session_id,
            "thought_number": analysis.thought_number,
            "patterns_detected": patterns_detected,
            "risk_assessment": risk_level,
            "would_have_escalated": should_escalate,
            "mode": "shadow",
        }

        # Store for later analysis (in production, this would go to KB)
        self.collected_patterns.append(collected_data)

        logger.info(f"Shadow analysis: Risk={risk_level}, Patterns={patterns_detected}")

        return TriageResponse(
            risk_level=risk_level,
            should_escalate=False,  # Never escalate in shadow mode
            confidence=0.8,
            reasoning=f"Shadow mode: Detected {len(patterns_detected)} patterns",
            collected_data=collected_data,
        )

    async def _advisory_analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Phase 2: Provide advice but don't block"""
        # To be implemented
        pass

    async def _enforcement_analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Phase 3: Active enforcement"""
        # To be implemented
        pass


# Global analyzer instance
analyzer = TriageAnalyzer()


@app.post("/analyze", response_model=TriageResponse)
async def analyze_thought(analysis: ThoughtAnalysis):
    """Analyze a thought and determine if intervention needed"""
    try:
        response = await analyzer.analyze(analysis)
        return response
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": analyzer.mode,
        "patterns_collected": len(analyzer.collected_patterns),
    }


@app.get("/metrics")
async def get_metrics():
    """Get collected metrics (shadow mode)"""
    if analyzer.mode != "shadow":
        return {"error": "Metrics only available in shadow mode"}

    total = len(analyzer.collected_patterns)
    if total == 0:
        return {"message": "No data collected yet"}

    # Calculate statistics
    would_escalate = sum(
        1 for p in analyzer.collected_patterns if p["would_have_escalated"]
    )
    risk_levels = {}
    patterns = {}

    for pattern_data in analyzer.collected_patterns:
        # Count risk levels
        risk = pattern_data["risk_assessment"]
        risk_levels[risk] = risk_levels.get(risk, 0) + 1

        # Count pattern types
        for p in pattern_data["patterns_detected"]:
            patterns[p] = patterns.get(p, 0) + 1

    return {
        "total_thoughts_analyzed": total,
        "would_have_escalated": would_escalate,
        "escalation_rate": would_escalate / total if total > 0 else 0,
        "risk_distribution": risk_levels,
        "pattern_frequency": patterns,
        "mode": analyzer.mode,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("TRIAGE_PORT", "8100"))
    uvicorn.run(app, host="0.0.0.0", port=port)
