#!/usr/bin/env python3
"""
Intelligent Triage Service using Nano Model
Analyzes thoughts for violations and determines when to escalate to consult suite
"""
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastmcp import Client
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent Triage Service", version="1.0.0")


class ThoughtAnalysis(BaseModel):
    thought: str
    thought_number: int
    session_id: str
    context: Optional[Dict[str, Any]] = {}
    history: Optional[List[str]] = []  # Recent thought history if available


class TriageResponse(BaseModel):
    needs_escalation: bool
    escalation_reason: Optional[str] = None
    violations_detected: List[str] = []
    reminders: List[str] = []  # Instructions to remind Claude about
    coaching_questions: List[str] = []  # Leading questions to help unstick
    patterns_observed: List[str] = []  # Multi-thought patterns detected
    confidence: float
    analysis: str
    kb_stored: bool = False
    kb_id: Optional[str] = None


class IntelligentTriageAnalyzer:
    def __init__(self):
        self.mode = os.getenv("TRIAGE_MODE", "shadow")
        self.api_key = os.getenv("OPENAI_API_KEY")  # For nano model
        self.knowledge_client = None
        self.instructions_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.thought_memory = {}  # Session -> thought history
        self.memory_window = 20  # Remember last 20 thoughts per session
        logger.info(f"Intelligent Triage initialized in {self.mode} mode")

    @asynccontextmanager
    async def get_knowledge_client(self):
        """Get or create MCP client connection to knowledge server"""
        if self.knowledge_client is None:
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

    async def load_instructions_from_kb(self) -> Dict[str, Any]:
        """Load relevant instructions from KB and CLAUDE.md"""
        instructions = {
            "global_rules": [],
            "project_rules": [],
            "app_rules": [],
            "claude_md": None,
        }

        try:
            # Load CLAUDE.md directly
            claude_md_path = "/home/opsvi/master_root/CLAUDE.md"
            if os.path.exists(claude_md_path):
                with open(claude_md_path, "r") as f:
                    instructions["claude_md"] = f.read()

            # Query KB for operational instructions
            async with self.get_knowledge_client() as client:
                if client:
                    # Global instructions
                    result = await client.call_tool(
                        "knowledge_query",
                        {
                            "query_type": "search",
                            "search_text": "GLOBAL OPERATIONAL INSTRUCTIONS",
                            "limit": 5,
                        },
                    )
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        instructions["global_rules"] = data.get("results", [])

                    # Workflow patterns
                    result = await client.call_tool(
                        "knowledge_query",
                        {
                            "query_type": "by_type",
                            "knowledge_type": "WORKFLOW",
                            "limit": 5,
                        },
                    )
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        instructions["project_rules"] = data.get("results", [])

                    # High confidence patterns
                    result = await client.call_tool(
                        "knowledge_query", {"query_type": "high_confidence", "limit": 5}
                    )
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        instructions["app_rules"] = data.get("results", [])

        except Exception as e:
            logger.error(f"Failed to load instructions: {e}")

        return instructions

    async def get_thought_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve thought history from KB for this session"""
        try:
            async with self.get_knowledge_client() as client:
                if client:
                    result = await client.call_tool(
                        "knowledge_query",
                        {
                            "query_type": "search",
                            "search_text": f"session:{session_id} THOUGHT_MEMORY",
                            "limit": self.memory_window,
                        },
                    )
                    if result and result.content:
                        data = json.loads(result.content[0].text)
                        return data.get("results", [])
        except Exception as e:
            logger.error(f"Failed to get thought history: {e}")

        # Fall back to in-memory cache
        return self.thought_memory.get(session_id, [])

    async def store_thought_memory(
        self, session_id: str, thought: str, thought_number: int, analysis_result: Dict
    ):
        """Store thought in memory for pattern detection"""
        memory_entry = {
            "thought": thought,
            "thought_number": thought_number,
            "timestamp": datetime.utcnow().isoformat(),
            "violations": analysis_result.get("violations", []),
            "patterns": analysis_result.get("patterns", []),
        }

        # Update in-memory cache
        if session_id not in self.thought_memory:
            self.thought_memory[session_id] = []
        self.thought_memory[session_id].append(memory_entry)

        # Keep only last N thoughts in memory
        if len(self.thought_memory[session_id]) > self.memory_window:
            self.thought_memory[session_id] = self.thought_memory[session_id][
                -self.memory_window :
            ]

        # Store in KB for persistence
        try:
            async with self.get_knowledge_client() as client:
                if client:
                    content = f"THOUGHT_MEMORY session:{session_id} thought#{thought_number}: {thought}"
                    await client.call_tool(
                        "knowledge_store",
                        {
                            "content": content,
                            "knowledge_type": "THOUGHT_MEMORY",
                            "tags": f"session-{session_id},thought-{thought_number}",
                        },
                    )
        except Exception as e:
            logger.error(f"Failed to store thought memory: {e}")

    async def analyze_with_nano_model(
        self,
        thought: str,
        thought_number: int,
        instructions: Dict,
        history: List[str],
        extended_history: List[Dict],
    ) -> Dict[str, Any]:
        """Use nano model to analyze thought for violations and escalation needs"""

        # Build context from instructions
        instruction_summary = ""

        if instructions["claude_md"]:
            # Extract key rules from CLAUDE.md
            if "INDEPENDENT EXPERT JUDGMENT" in instructions["claude_md"]:
                instruction_summary += """\nCRITICAL RULES:
- Must evaluate ideas on MERITS before agreeing
- Forbidden: Reflexive agreement like 'You're absolutely right!'
- Required: Evidence-based expert perspective
- When user is right: Acknowledge + add unique insights
- When user is wrong: Explain issues + offer better approach
"""

        # Add KB rules
        for rule in instructions.get("global_rules", []):
            if rule.get("content"):
                instruction_summary += f"\nGLOBAL: {rule['content'][:200]}..."

        # Analyze extended history for patterns
        extended_context = ""
        if extended_history:
            recent_violations = []
            recent_thoughts = []
            for entry in extended_history[-10:]:
                recent_thoughts.append(entry.get("thought", ""))
                recent_violations.extend(entry.get("violations", []))

            extended_context = f"""\n\nExtended thought history (last {len(recent_thoughts)} thoughts):
{json.dumps(recent_thoughts, indent=2)}

Recent violation patterns: {', '.join(set(recent_violations)) if recent_violations else 'None'}
"""

        # Build prompt for nano model with coaching capabilities
        prompt = f"""You are an intelligent thought analyzer and coach for an AI assistant. Analyze thoughts, detect patterns, and provide helpful guidance.

Current thought being analyzed (Thought #{thought_number}):
"{thought}"

Immediate thought history:
{json.dumps(history[-3:] if history else [], indent=2)}
{extended_context}

Key instructions the assistant should follow:
{instruction_summary}

Analyze this thought and provide:
1. **Violations**: Is there reflexive agreement, unsubstantiated claims, or rule violations?
2. **Patterns**: Are there multi-thought patterns? (struggling, going in circles, repeated attempts, frustration)
3. **Coaching**: What leading questions could help? (e.g., "Have you verified X exists?", "What assumption are you making?")
4. **Reminders**: What specific instructions is the assistant forgetting?
5. **Escalation**: Would specialist agents help with this complexity?

Detect these patterns FROM THE THOUGHT CONTENT:
- Shallow thinking (jumping to conclusions without analysis)
- Overthinking (many thoughts for a simple task - note we're at thought #{thought_number})
- Circular thinking (repeating same approach across multiple thoughts)
- Reflexive agreement ("You're right" without evaluation)
- Repeated error mentions (same problem in multiple thoughts)
- Accumulating changes ("I've now modified X, Y, Z files")
- Overconfidence ("this will definitely work", "obviously")
- Unverified assumptions ("I'll assume", "probably")
- Scope creep (expanding beyond original task)
- Frustration/stuck patterns (increasing confusion across thoughts)

Provide coaching questions when you detect:
- They're stuck (mentioned same issue 3+ times)
- Making assumptions without verification
- Overthinking (we're at thought #{thought_number} for what seems simple)
- Going in circles (revisiting already-tried approaches)
- Not checking basics (file existence, error details)
- Forgetting CLAUDE.md rules (especially about agreement)

Respond in JSON format:
{{
  "violations": ["list of specific violations detected"],
  "patterns": ["multi-thought patterns observed"],
  "coaching_questions": ["helpful leading questions to unstick the assistant"],
  "needs_escalation": true/false,
  "escalation_reason": "why escalation would help (if applicable)",
  "reminders": ["specific rules/instructions to remember"],
  "confidence": 0.0-1.0,
  "analysis": "brief explanation of your analysis"
}}"""

        try:
            # Call OpenAI API with nano model
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",  # Using mini as nano proxy
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a precise thought analyzer. Always respond with valid JSON.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=10.0,
                )

            if response.status_code == 200:
                result = response.json()
                analysis = json.loads(result["choices"][0]["message"]["content"])
                return analysis
            else:
                logger.error(f"API call failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to analyze with nano model: {e}")

        # Fallback analysis if API fails
        return {
            "violations": [],
            "needs_escalation": False,
            "escalation_reason": None,
            "reminders": [],
            "confidence": 0.0,
            "analysis": "Analysis failed - API error",
        }

    async def store_pattern_via_mcp(
        self, content: str, tags: List[str]
    ) -> Optional[str]:
        """Store analysis pattern in KB"""
        try:
            async with self.get_knowledge_client() as client:
                if client:
                    result = await client.call_tool(
                        "knowledge_store",
                        {
                            "content": content,
                            "knowledge_type": "THINKING_PATTERN",
                            "tags": ",".join(tags) if tags else None,
                        },
                    )

                    if result and result.content:
                        result_data = json.loads(result.content[0].text)
                        if result_data.get("success"):
                            return result_data.get("knowledge_id")

        except Exception as e:
            logger.error(f"Failed to store via MCP: {e}")

        return None

    async def analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Main analysis entry point"""

        # Load instructions from KB
        instructions = await self.load_instructions_from_kb()

        # Get extended thought history for this session
        extended_history = await self.get_thought_history(analysis.session_id)

        # Analyze with nano model (now with coaching capabilities)
        ai_analysis = await self.analyze_with_nano_model(
            analysis.thought,
            analysis.thought_number,
            instructions,
            analysis.history,
            extended_history,
        )

        # Store this thought in memory for future pattern detection
        await self.store_thought_memory(
            analysis.session_id, analysis.thought, analysis.thought_number, ai_analysis
        )

        # Build content for KB storage
        kb_content = f"""INTELLIGENT TRIAGE ANALYSIS

Session: {analysis.session_id}
Thought #{analysis.thought_number}: {analysis.thought}

AI Analysis:
{json.dumps(ai_analysis, indent=2)}

Timestamp: {datetime.utcnow().isoformat()}
Mode: {self.mode}
"""

        # Build tags
        tags = ["triage-analysis", "ai-powered", f"mode-{self.mode}"]
        if ai_analysis.get("needs_escalation"):
            tags.append("escalation-recommended")
        for violation in ai_analysis.get("violations", []):
            tags.append(f"violation-{violation.lower().replace(' ', '-')[:30]}")

        # Store in KB
        kb_id = await self.store_pattern_via_mcp(kb_content, tags)

        # Return response based on mode
        response = TriageResponse(
            needs_escalation=ai_analysis.get("needs_escalation", False)
            if self.mode != "shadow"
            else False,
            escalation_reason=ai_analysis.get("escalation_reason"),
            violations_detected=ai_analysis.get("violations", []),
            reminders=ai_analysis.get("reminders", []),
            coaching_questions=ai_analysis.get("coaching_questions", []),
            patterns_observed=ai_analysis.get("patterns", []),
            confidence=ai_analysis.get("confidence", 0.5),
            analysis=ai_analysis.get("analysis", "No analysis available"),
            kb_stored=kb_id is not None,
            kb_id=kb_id,
        )

        # Log for debugging
        logger.info(
            f"Triage complete: escalation={response.needs_escalation}, violations={len(response.violations_detected)}, patterns={len(response.patterns_observed)}, coaching={len(response.coaching_questions)}"
        )

        return response


# Global analyzer instance
analyzer = IntelligentTriageAnalyzer()


@app.post("/analyze", response_model=TriageResponse)
async def analyze_thought(analysis: ThoughtAnalysis):
    """Analyze a thought using intelligent AI model"""
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
        "type": "intelligent",
        "model": "nano/gpt-4o-mini",
    }


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
