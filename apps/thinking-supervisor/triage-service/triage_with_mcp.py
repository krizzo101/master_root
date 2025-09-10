#!/usr/bin/env python3
"""
Enhanced Triage API with MCP Client Integration
Properly calls the knowledge MCP server instead of direct DB access
"""
import asyncio
import json
import logging
import os
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# FastMCP client for connecting to knowledge MCP server
try:
    from fastmcp import Client
except ImportError:
    print("Installing fastmcp...")
    subprocess.run(["/home/opsvi/miniconda/bin/pip", "install", "fastmcp"], check=True)
    from fastmcp import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Triage Service with MCP", version="0.3.0")


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


class TriageAnalyzerWithMCP:
    def __init__(self):
        self.mode = os.getenv("TRIAGE_MODE", "shadow")
        self.session_cache = {}
        self.knowledge_client = None
        logger.info(f"Triage initialized in {self.mode} mode with MCP client")

    @asynccontextmanager
    async def get_knowledge_client(self):
        """Get or create MCP client connection to knowledge server"""
        if self.knowledge_client is None:
            # Connect to knowledge MCP server using stdio transport
            server_params = {
                "command": "/home/opsvi/miniconda/bin/python",
                "args": ["-m", "opsvi_mcp.servers.knowledge.server"],
                "env": {
                    "PYTHONPATH": "/home/opsvi/master_root/libs:/home/opsvi/master_root/apps",
                    "NEO4J_URI": "bolt://localhost:7687",
                    "NEO4J_USER": "neo4j",
                    "NEO4J_PASSWORD": "password",
                },
            }

            try:
                self.knowledge_client = Client(server_params)
                await self.knowledge_client.__aenter__()
                logger.info("Connected to knowledge MCP server")
            except Exception as e:
                logger.error(f"Failed to connect to knowledge MCP: {e}")
                self.knowledge_client = None

        yield self.knowledge_client

    async def store_pattern_via_mcp(
        self,
        content: str,
        knowledge_type: str = "THINKING_PATTERN",
        tags: List[str] = None,
    ) -> Optional[str]:
        """Store pattern using the knowledge MCP server"""
        try:
            async with self.get_knowledge_client() as client:
                if client is None:
                    logger.warning("No MCP client available")
                    return None

                # Call the knowledge_store tool via MCP
                result = await client.call_tool(
                    "knowledge_store",
                    {
                        "content": content,
                        "knowledge_type": knowledge_type,
                        "tags": ",".join(tags) if tags else None,
                    },
                )

                # Parse the result
                if result and result.content:
                    result_data = json.loads(result.content[0].text)
                    if result_data.get("success"):
                        return result_data.get("knowledge_id")

        except Exception as e:
            logger.error(f"Failed to store via MCP: {e}")

        return None

    async def analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Analyze thought and store patterns via MCP"""

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

        # Store in Knowledge Base via MCP
        kb_stored = False
        kb_id = None

        # Build content for KB storage
        content = self._build_kb_content(
            analysis.thought, risk_level, patterns_detected, should_escalate, analysis
        )

        # Build tags
        tags = self._build_tags(risk_level, patterns_detected, should_escalate)

        # Store via MCP client
        kb_id = await self.store_pattern_via_mcp(content, "THINKING_PATTERN", tags)
        kb_stored = kb_id is not None

        if kb_stored:
            logger.info(f"Stored thinking pattern via MCP: {kb_id}")
        else:
            logger.warning("Failed to store pattern via MCP")

        # Return response based on mode
        if self.mode == "shadow":
            return TriageResponse(
                risk_level=risk_level,
                should_escalate=False,
                confidence=0.8,
                reasoning=f"Shadow mode: Detected {len(patterns_detected)} patterns",
                collected_data=collected_data,
                kb_stored=kb_stored,
                kb_id=kb_id,
            )

        # Other modes would go here...
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

        if any(
            phrase in thought_lower
            for phrase in ["you're right", "you're absolutely", "exactly right"]
        ):
            patterns.append("agreeability_without_analysis")

        if "every 30 minutes" in thought_lower and "stateless" in thought_lower:
            patterns.append("technical_impossibility")

        claim_words = ["will", "definitely", "certainly"]
        evidence_words = ["because", "since", "due to"]
        has_claim = any(word in thought_lower for word in claim_words)
        has_evidence = any(word in thought_lower for word in evidence_words)

        if has_claim and not has_evidence:
            patterns.append("unsubstantiated_claim")

        return patterns

    def _assess_risk(self, thought: str) -> str:
        """Assess risk level of thought"""
        thought_lower = thought.lower()

        if any(
            word in thought_lower
            for word in ["production", "delete all", "drop database"]
        ):
            return "critical"

        if any(word in thought_lower for word in ["delete", "remove", "deploy"]):
            return "high"

        if any(word in thought_lower for word in ["implement", "create", "modify"]):
            return "medium"

        return "low"

    def _should_escalate(
        self, risk_level: str, patterns: List[str], analysis: ThoughtAnalysis
    ) -> bool:
        """Determine if escalation is needed"""
        if risk_level == "critical":
            return True

        if risk_level == "high" and len(patterns) > 0:
            return True

        if len(patterns) >= 2:
            return True

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


# Global analyzer instance
analyzer = TriageAnalyzerWithMCP()


@app.post("/analyze", response_model=TriageResponse)
async def analyze_thought(analysis: ThoughtAnalysis):
    """Analyze a thought and store via MCP"""
    try:
        response = await analyzer.analyze(analysis)
        return response
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "mode": analyzer.mode, "mcp_client": "configured"}


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MCP client on shutdown"""
    if analyzer.knowledge_client:
        try:
            await analyzer.knowledge_client.__aexit__(None, None, None)
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("TRIAGE_PORT", "8102"))
    uvicorn.run(app, host="0.0.0.0", port=port)
