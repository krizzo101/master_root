#!/usr/bin/env python3
"""
Enhanced Triage API with Knowledge Base Integration
Uses the actual MCP knowledge tools for storage
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add path for imports
sys.path.insert(0, "/home/opsvi/master_root")

# Import the knowledge store
from apps.knowledge_system.mcp_knowledge_tools import EnhancedKnowledgeStore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced Thinking Triage Service", version="0.2.0")


class ThoughtAnalysis(BaseModel):
    thought: str
    thought_number: int
    session_id: str
    context: Optional[Dict[str, Any]] = {}
    history: Optional[List[str]] = []


class TriageResponse(BaseModel):
    risk_level: str
    should_escalate: bool
    confidence: float
    reasoning: Optional[str] = None
    intervention: Optional[Dict[str, Any]] = None
    collected_data: Dict[str, Any] = {}
    kb_stored: bool = False
    kb_id: Optional[str] = None


class EnhancedTriageAnalyzer:
    def __init__(self):
        self.mode = os.getenv("TRIAGE_MODE", "shadow")
        # Initialize knowledge store but disable Neo4j driver
        self.kb_store = EnhancedKnowledgeStore()
        # Disable direct Neo4j connection - we'll use MCP tool only
        self.kb_store.neo4j_driver = None
        self.session_cache = {}
        logger.info(
            f"Enhanced Triage initialized in {self.mode} mode with KB storage (MCP-only)"
        )

    async def analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Analyze thought and store patterns in KB"""

        # Detect patterns
        patterns_detected = self._detect_patterns(analysis.thought)

        # Assess risk
        risk_level = self._assess_risk(analysis.thought)

        # Determine escalation
        should_escalate = self._should_escalate(risk_level, patterns_detected, analysis)

        # Build response data
        collected_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": analysis.session_id,
            "thought_number": analysis.thought_number,
            "patterns_detected": patterns_detected,
            "risk_assessment": risk_level,
            "would_have_escalated": should_escalate,
            "mode": self.mode,
        }

        # Store in Knowledge Base
        kb_stored = False
        kb_id = None

        try:
            # Build content for KB storage
            content = self._build_kb_content(
                analysis.thought,
                risk_level,
                patterns_detected,
                should_escalate,
                analysis,
            )

            # Store using the knowledge tool (nano agent will transform it)
            # IMPORTANT: direct_execute=False to use MCP tool only, no direct DB access
            result = await self.kb_store.store(
                raw_input=content,
                hint_type="THINKING_PATTERN",
                hint_tags=self._build_tags(
                    risk_level, patterns_detected, should_escalate
                ),
                direct_execute=False,  # Use MCP tool, not direct DB
            )

            kb_stored = True
            kb_id = result.get("knowledge_id")
            logger.info(f"Stored thinking pattern in KB: {kb_id}")

        except Exception as e:
            logger.error(f"Failed to store in KB: {e}")

        # Return response based on mode
        if self.mode == "shadow":
            # Never escalate in shadow mode
            return TriageResponse(
                risk_level=risk_level,
                should_escalate=False,
                confidence=0.8,
                reasoning=f"Shadow mode: Detected {len(patterns_detected)} patterns",
                collected_data=collected_data,
                kb_stored=kb_stored,
                kb_id=kb_id,
            )

        elif self.mode == "advisory":
            # Provide advice but don't block
            intervention = None
            if should_escalate:
                intervention = self._generate_advisory(patterns_detected, risk_level)

            return TriageResponse(
                risk_level=risk_level,
                should_escalate=False,  # Advisory doesn't block
                confidence=0.85,
                reasoning=f"Advisory: {intervention.get('message') if intervention else 'No issues'}",
                intervention=intervention,
                collected_data=collected_data,
                kb_stored=kb_stored,
                kb_id=kb_id,
            )

        elif self.mode == "enforcement":
            # Active enforcement with blocking
            intervention = None
            if should_escalate:
                intervention = self._generate_enforcement(patterns_detected, risk_level)

            return TriageResponse(
                risk_level=risk_level,
                should_escalate=should_escalate,
                confidence=0.9,
                reasoning=f"Enforcement: {intervention.get('message') if intervention else 'Proceeding'}",
                intervention=intervention,
                collected_data=collected_data,
                kb_stored=kb_stored,
                kb_id=kb_id,
            )

        return TriageResponse(
            risk_level=risk_level,
            should_escalate=False,
            confidence=0.0,
            kb_stored=kb_stored,
            kb_id=kb_id,
        )

    def _detect_patterns(self, thought: str) -> List[str]:
        """Detect problematic patterns in thought"""
        patterns = []
        thought_lower = thought.lower()

        # Agreeability patterns
        if any(
            phrase in thought_lower
            for phrase in [
                "you're right",
                "you're absolutely",
                "exactly right",
                "completely agree",
                "absolutely correct",
            ]
        ):
            patterns.append("agreeability_without_analysis")

        # Technical impossibilities
        if "every 30 minutes" in thought_lower and "stateless" in thought_lower:
            patterns.append("technical_impossibility")

        # Unsubstantiated claims
        claim_words = ["will", "definitely", "certainly", "guaranteed"]
        evidence_words = ["because", "since", "due to", "based on", "evidence"]

        has_claim = any(word in thought_lower for word in claim_words)
        has_evidence = any(word in thought_lower for word in evidence_words)

        if has_claim and not has_evidence:
            patterns.append("unsubstantiated_claim")

        # Rush to implement
        if "let me implement" in thought_lower and "understand" not in thought_lower:
            patterns.append("rush_to_implement")

        # Shallow analysis
        if len(thought.split()) < 20 and any(
            word in thought_lower for word in ["yes", "no", "correct", "wrong"]
        ):
            patterns.append("shallow_response")

        return patterns

    def _assess_risk(self, thought: str) -> str:
        """Assess risk level of thought"""
        thought_lower = thought.lower()

        # Critical risk indicators
        if any(
            word in thought_lower
            for word in ["production", "delete all", "drop database", "rm -rf"]
        ):
            return "critical"

        # High risk indicators
        if any(
            word in thought_lower
            for word in ["delete", "remove", "deploy", "push to main"]
        ):
            return "high"

        # Medium risk indicators
        if any(
            word in thought_lower
            for word in ["implement", "create", "modify", "refactor"]
        ):
            return "medium"

        return "low"

    def _should_escalate(
        self, risk_level: str, patterns: List[str], analysis: ThoughtAnalysis
    ) -> bool:
        """Determine if escalation is needed"""
        # Critical always escalates
        if risk_level == "critical":
            return True

        # High risk with patterns
        if risk_level == "high" and len(patterns) > 0:
            return True

        # Multiple problematic patterns
        if len(patterns) >= 2:
            return True

        # Specific dangerous patterns
        dangerous_patterns = ["technical_impossibility", "rush_to_implement"]
        if any(p in patterns for p in dangerous_patterns):
            return True

        # Pattern repetition in session
        session_patterns = self.session_cache.get(analysis.session_id, {}).get(
            "patterns", []
        )
        if patterns and any(p in session_patterns for p in patterns):
            return True  # Repeating problematic pattern

        # Update session cache
        if analysis.session_id not in self.session_cache:
            self.session_cache[analysis.session_id] = {"patterns": []}
        self.session_cache[analysis.session_id]["patterns"].extend(patterns)

        return False

    def _build_kb_content(
        self,
        thought: str,
        risk_level: str,
        patterns: List[str],
        would_escalate: bool,
        analysis: ThoughtAnalysis,
    ) -> str:
        """Build content for KB storage"""

        content = f"""
THINKING PATTERN ANALYSIS

Session: {analysis.session_id}
Thought #{analysis.thought_number}: {thought}

Risk Assessment: {risk_level}
Patterns Detected: {', '.join(patterns) if patterns else 'None'}
Escalation Decision: {'WOULD ESCALATE' if would_escalate else 'No escalation needed'}

Context:
- Previous thoughts: {len(analysis.history)}
- Current context: {json.dumps(analysis.context, indent=2)}

Pattern Details:
"""

        for pattern in patterns:
            if pattern == "agreeability_without_analysis":
                content += (
                    "- Agreeability: Agreement without critical evaluation detected\n"
                )
            elif pattern == "technical_impossibility":
                content += "- Technical Issue: Claim of impossible functionality\n"
            elif pattern == "unsubstantiated_claim":
                content += (
                    "- Evidence Missing: Strong claim without supporting evidence\n"
                )
            elif pattern == "rush_to_implement":
                content += (
                    "- Hasty Implementation: Jumping to code without understanding\n"
                )
            elif pattern == "shallow_response":
                content += "- Shallow Analysis: Brief response lacking depth\n"

        if would_escalate:
            content += f"\nESCALATION REASONING:\n"
            content += f"- Risk Level: {risk_level}\n"
            content += f"- Pattern Count: {len(patterns)}\n"
            content += f"- Requires intervention to prevent potential issues\n"

        return content

    def _build_tags(
        self, risk_level: str, patterns: List[str], would_escalate: bool
    ) -> List[str]:
        """Build tags for KB entry"""
        tags = ["thinking-pattern", f"risk-{risk_level}", "triage-analysis"]

        for pattern in patterns:
            tags.append(f"pattern-{pattern.replace('_', '-')}")

        if would_escalate:
            tags.append("escalation-candidate")

        return tags

    def _generate_advisory(
        self, patterns: List[str], risk_level: str
    ) -> Dict[str, Any]:
        """Generate advisory intervention"""
        messages = []

        if "agreeability_without_analysis" in patterns:
            messages.append(
                "Consider: Are you agreeing based on analysis or reflexively?"
            )

        if "technical_impossibility" in patterns:
            messages.append(
                "Warning: This may not be technically feasible as described"
            )

        if "unsubstantiated_claim" in patterns:
            messages.append("Suggestion: Provide evidence or mark as speculation")

        return {
            "type": "advisory",
            "message": " | ".join(messages)
            if messages
            else "Consider reviewing your approach",
            "risk_level": risk_level,
            "patterns": patterns,
        }

    def _generate_enforcement(
        self, patterns: List[str], risk_level: str
    ) -> Dict[str, Any]:
        """Generate enforcement intervention"""
        requirements = []

        if "agreeability_without_analysis" in patterns:
            requirements.append("Provide 3 specific points of analysis before agreeing")

        if "technical_impossibility" in patterns:
            requirements.append("Explain how this would actually work technically")

        if "unsubstantiated_claim" in patterns:
            requirements.append("Provide evidence or rephrase as hypothesis")

        if "rush_to_implement" in patterns:
            requirements.append("First explain what you understand about the problem")

        return {
            "type": "enforcement",
            "message": "BLOCKED: Address these requirements before proceeding",
            "requirements": requirements,
            "risk_level": risk_level,
            "patterns": patterns,
        }


# Global analyzer instance
analyzer = EnhancedTriageAnalyzer()


@app.post("/analyze", response_model=TriageResponse)
async def analyze_thought(analysis: ThoughtAnalysis):
    """Analyze a thought and store in KB"""
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
        "kb_connected": analyzer.kb_store is not None,
    }


@app.get("/session/{session_id}/patterns")
async def get_session_patterns(session_id: str):
    """Get patterns detected in a session"""
    if session_id not in analyzer.session_cache:
        return {"message": "No patterns for this session"}

    return {
        "session_id": session_id,
        "patterns": analyzer.session_cache[session_id].get("patterns", []),
        "pattern_count": len(analyzer.session_cache[session_id].get("patterns", [])),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("TRIAGE_PORT", "8101"))
    uvicorn.run(app, host="0.0.0.0", port=port)
