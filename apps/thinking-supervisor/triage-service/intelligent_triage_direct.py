#!/usr/bin/env python3
"""
Intelligent Triage Service with Direct Knowledge Access
Uses direct module imports for 10x faster performance than MCP
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add project to path for direct imports
sys.path.insert(0, "/home/opsvi/master_root")

# Direct imports from knowledge system (10-50ms vs 100-500ms for MCP)
from apps.knowledge_system.mcp_knowledge_tools import KnowledgeManager
from apps.knowledge_system.query_nano_agent import get_smart_executor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Intelligent Triage Service (Direct)", version="2.0.0")


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

        # Initialize direct knowledge access
        self.km = KnowledgeManager()
        self.smart_query = get_smart_executor()

        # Memory cache
        self.thought_memory = {}  # Session -> thought history
        self.memory_window = 20  # Remember last 20 thoughts per session
        self.instructions_cache = {}
        self.cache_ttl = 300  # 5 minutes

        logger.info(
            f"Intelligent Triage initialized in {self.mode} mode with DIRECT knowledge access"
        )

    async def load_instructions_from_kb(self) -> Dict[str, Any]:
        """Load relevant instructions from KB and CLAUDE.md using direct access"""
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

            # Direct KB query for operational instructions (FAST!)
            results = await self.km.query(
                query_type="search",
                search_text="GLOBAL OPERATIONAL INSTRUCTIONS",
                limit=5,
            )
            if results and results.get("results"):
                instructions["global_rules"] = results["results"]

            # Workflow patterns
            results = await self.km.query(
                query_type="by_type", knowledge_type="WORKFLOW", limit=5
            )
            if results and results.get("results"):
                instructions["project_rules"] = results["results"]

            # High confidence patterns
            results = await self.km.query(query_type="high_confidence", limit=5)
            if results and results.get("results"):
                instructions["app_rules"] = results["results"]

        except Exception as e:
            logger.error(f"Failed to load instructions: {e}")

        return instructions

    async def get_thought_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve thought history from KB for this session using direct access"""
        try:
            # Direct query for session thoughts
            results = await self.km.query(
                query_type="search",
                search_text=f"session:{session_id} THOUGHT_MEMORY",
                limit=self.memory_window,
            )

            if results and results.get("results"):
                return results["results"]

        except Exception as e:
            logger.error(f"Failed to get thought history: {e}")

        # Fall back to in-memory cache
        return self.thought_memory.get(session_id, [])

    async def store_thought_memory(
        self, session_id: str, thought: str, thought_number: int, analysis_result: Dict
    ):
        """Store thought in memory for pattern detection using direct access"""
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

        # Store in KB using direct access (FAST!)
        try:
            content = f"THOUGHT_MEMORY session:{session_id} thought#{thought_number}: {thought}"
            result = await self.km.store(
                {
                    "content": content,
                    "knowledge_type": "THOUGHT_MEMORY",
                    "tags": f"session-{session_id},thought-{thought_number}",
                    "source": "triage-analyzer",
                }
            )

            if result.get("knowledge_id"):
                logger.info(f"Stored thought memory directly: {result['knowledge_id']}")

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
                instruction_summary += """
CRITICAL RULES:
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
                recent_thoughts.append(
                    entry.get("thought", "") if isinstance(entry, dict) else str(entry)
                )
                if isinstance(entry, dict):
                    recent_violations.extend(entry.get("violations", []))

            extended_context = f"""

Extended thought history (last {len(recent_thoughts)} thoughts):
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
            # Use OpenAI Responses API (approved model) with JSON-like output
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            resp = await client.responses.create(
                model=os.getenv("TRIAGE_MODEL", "gpt-5-nano"),
                input=prompt,
                temperature=0.2,
                max_output_tokens=500
            )

            text = None
            for out in getattr(resp, "output", []) or []:
                if hasattr(out, "content") and out.content:
                    for c in out.content:
                        if hasattr(c, "text") and c.text:
                            text = c.text
                            break
                    if text:
                        break
            if text:
                try:
                    return json.loads(text)
                except Exception:
                    return {
                        "violations": [],
                        "patterns": [],
                        "coaching_questions": [],
                        "needs_escalation": False,
                        "escalation_reason": None,
                        "reminders": [],
                        "confidence": 0.5,
                        "analysis": text[:800],
                    }
        except Exception as e:
            logger.error(f"Failed to analyze with Responses API: {e}")

        # Fallback analysis if API fails
        return {
            "violations": [],
            "patterns": [],
            "coaching_questions": [],
            "needs_escalation": False,
            "escalation_reason": None,
            "reminders": [],
            "confidence": 0.0,
            "analysis": "Analysis failed - API error",
        }

    async def store_pattern_directly(
        self, content: str, tags: List[str]
    ) -> Optional[str]:
        """Store analysis pattern in KB using direct access (FAST!)"""
        try:
            result = await self.km.store(
                {
                    "content": content,
                    "knowledge_type": "THINKING_PATTERN",
                    "tags": ",".join(tags) if tags else None,
                    "source": "triage-analyzer",
                    "confidence": 0.8,
                }
            )

            if result.get("knowledge_id"):
                logger.info(f"Stored pattern directly: {result['knowledge_id']}")
                return result["knowledge_id"]

        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")

        return None

    async def analyze(self, analysis: ThoughtAnalysis) -> TriageResponse:
        """Main analysis entry point with direct knowledge access"""

        # Load instructions from KB (direct access)
        instructions = await self.load_instructions_from_kb()

        # Get extended thought history (direct access)
        extended_history = await self.get_thought_history(analysis.session_id)

        # Analyze with nano model
        ai_analysis = await self.analyze_with_nano_model(
            analysis.thought,
            analysis.thought_number,
            instructions,
            analysis.history,
            extended_history,
        )

        # Store this thought in memory (direct access)
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

        # Store in KB (direct access - FAST!)
        kb_id = await self.store_pattern_directly(kb_content, tags)

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

    async def find_similar_violations(self, thought: str, limit: int = 5) -> List[Dict]:
        """Find similar past violations using smart query"""
        try:
            # Use smart query for better semantic matching
            results = await self.smart_query.execute_smart_query(
                query=f"violations similar to: {thought[:200]}",
                limit=limit,
                use_assistant=True,
            )

            return results.get("results", [])

        except Exception as e:
            logger.error(f"Failed to find similar violations: {e}")
            return []


# Global analyzer instance
analyzer = IntelligentTriageAnalyzer()


@app.post("/analyze", response_model=TriageResponse)
async def analyze_thought(analysis: ThoughtAnalysis):
    """Analyze a thought using intelligent AI model with direct KB access"""
    try:
        response = await analyzer.analyze(analysis)
        return response
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    neo4j_status = "connected" if analyzer.km.neo4j_driver else "disconnected"

    return {
        "status": "healthy",
        "mode": analyzer.mode,
        "type": "intelligent-direct",
        "model": os.getenv("TRIAGE_MODEL", "gpt-5-nano"),
        "knowledge_access": "direct",
        "neo4j": neo4j_status,
        "performance": "10-50ms (direct access)",
    }


@app.get("/similar/{session_id}")
async def find_similar_patterns(session_id: str, limit: int = 5):
    """Find similar thinking patterns from past sessions"""
    try:
        # Get current session patterns
        history = await analyzer.get_thought_history(session_id)
        if not history:
            return {"similar": [], "message": "No history for session"}

        # Find similar violations
        recent_thought = history[-1].get("thought", "") if history else ""
        similar = await analyzer.find_similar_violations(recent_thought, limit)

        return {"similar": similar}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up direct connections on shutdown"""
    try:
        if analyzer.km.neo4j_driver:
            analyzer.km.neo4j_driver.close()
            logger.info("Closed Neo4j connection")
    except:
        pass


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("TRIAGE_PORT", "8102"))
    uvicorn.run(app, host="0.0.0.0", port=port)
