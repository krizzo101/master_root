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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add project to path for direct imports
sys.path.insert(0, "/home/opsvi/master_root")

# Direct imports from knowledge system (10-50ms vs 100-500ms for MCP)
from apps.knowledge_system.mcp_knowledge_tools import (
    get_enhanced_query,
    get_enhanced_store,
)
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
        self.store = get_enhanced_store()
        self.query_tool = get_enhanced_query()
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
            results = self.query_tool.query(
                query_type="search",
                query_text="GLOBAL OPERATIONAL INSTRUCTIONS",
                limit=5,
                direct_execute=True,
            )
            if results and results.get("results"):
                instructions["global_rules"] = results["results"]

            # Workflow patterns
            results = self.query_tool.query(
                query_type="by_type",
                knowledge_type="WORKFLOW",
                limit=5,
                direct_execute=True,
            )
            if results and results.get("results"):
                instructions["project_rules"] = results["results"]

            # High confidence patterns
            results = self.query_tool.query(
                query_type="high_confidence",
                limit=5,
                direct_execute=True,
            )
            if results and results.get("results"):
                instructions["app_rules"] = results["results"]

        except Exception as e:
            logger.error(f"Failed to load instructions: {e}")

        return instructions

    async def get_thought_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve thought history from KB for this session using direct access"""
        try:
            # Direct query for session thoughts
            results = self.query_tool.query(
                query_type="search",
                query_text=f"session:{session_id} THOUGHT_MEMORY",
                limit=self.memory_window,
                direct_execute=True,
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
            result = await self.store.store(
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
        prompt = f"""You are a STRICT thought analyzer for an AI assistant. Your job is to FLAG VIOLATIONS aggressively. Be very sensitive to detecting problems.

Current thought being analyzed (Thought #{thought_number}):
"{thought}"

Immediate thought history:
{json.dumps(history[-3:] if history else [], indent=2)}
{extended_context}

Key instructions the assistant should follow:
{instruction_summary}

**CRITICAL: FLAG THESE VIOLATIONS IMMEDIATELY:**

1. **REFLEXIVE AGREEMENT** - ANY form of agreement without evaluation:
   - "You're absolutely right"
   - "I completely agree"
   - "Obviously this is correct"
   - "Definitely the right approach"

2. **UNSUBSTANTIATED CLAIMS** - Claims without evidence:
   - "This will definitely work"
   - "Obviously this is the solution"
   - "This will solve the problem"
   - "Without any issues"

3. **OVERCONFIDENCE** - Excessive certainty:
   - "Absolutely certain"
   - "I'm sure this will work"
   - "This is obviously correct"
   - "Definitely the right way"

4. **DESTRUCTIVE INTENT** - Harmful actions:
   - "Delete everything"
   - "Rewrite from scratch"
   - "Start over completely"
   - "Throw away the old code"

5. **UNVERIFIED ASSUMPTIONS** - Assumptions without checking:
   - "I'll assume"
   - "Probably this will work"
   - "This should be fine"
   - "I think this is right"

**BE AGGRESSIVE IN FLAGGING. If you see ANY of these patterns, FLAG THEM.**

Analyze this thought and provide:
1. **Violations**: List EVERY violation you detect (be thorough)
2. **Patterns**: Multi-thought patterns observed
3. **Coaching**: Leading questions to help
4. **Reminders**: Specific rules being forgotten
5. **Escalation**: Would specialist agents help?

**IMPORTANT: If you detect ANY of the violations above, you MUST include them in the violations array. Do not be conservative.**

Respond in JSON format:
{{
  "violations": ["list of specific violations detected - be thorough"],
  "patterns": ["multi-thought patterns observed"],
  "coaching_questions": ["helpful leading questions to unstick the assistant"],
  "needs_escalation": true/false,
  "escalation_reason": "why escalation would help (if applicable)",
  "reminders": ["specific rules/instructions to remember"],
  "confidence": 0.0-1.0,
  "analysis": "brief explanation of your analysis"
}}"""

        try:
            # Use OpenAI Responses API with structured output (2025 standard)
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # Define the JSON schema for structured response
            triage_schema = {
                "name": "triage_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "violations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of violations detected",
                        },
                        "patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Multi-thought patterns observed",
                        },
                        "coaching_questions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Helpful leading questions",
                        },
                        "needs_escalation": {
                            "type": "boolean",
                            "description": "Whether to escalate to consult suite",
                        },
                        "escalation_reason": {
                            "type": ["string", "null"],
                            "description": "Why escalation is needed",
                        },
                        "reminders": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Instructions to remind about",
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Confidence in analysis",
                        },
                        "analysis": {
                            "type": "string",
                            "description": "Brief explanation of analysis",
                        },
                    },
                    "required": [
                        "violations",
                        "patterns",
                        "coaching_questions",
                        "needs_escalation",
                        "reminders",
                        "confidence",
                        "analysis",
                    ],
                    "additionalProperties": False,
                },
            }

            model_name = os.getenv("TRIAGE_MODEL", "gpt-5-nano")
            logger.info(f"Calling OpenAI Responses API with model: {model_name}")
            logger.info(f"Prompt length: {len(prompt)} characters")

            # Use Responses API with structured JSON output (matching working examples)
            resp = await client.responses.create(
                model=model_name,
                input=[{"role": "developer", "content": prompt}],
                response={
                    "modalities": ["text"],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "json_schema": triage_schema,
                        }
                    },
                },
                temperature=0.3,
                max_output_tokens=500,
            )

            # Access parsed output directly (as seen in working examples)
            if hasattr(resp, "output_parsed"):
                data = resp.output_parsed
                logger.info(f"Successfully received structured response")
                logger.info(f"Violations detected: {len(data.get('violations', []))}")
                logger.info(f"Patterns observed: {len(data.get('patterns', []))}")
                logger.info(
                    f"Coaching questions: {len(data.get('coaching_questions', []))}"
                )
                return data
            else:
                logger.error(f"No output_parsed found in response")
                logger.error(f"Response type: {type(resp)}")
                logger.error(f"Response attributes: {dir(resp)}")
                raise ValueError("No output_parsed in response")
        except Exception as e:
            logger.error(f"Failed to analyze with Responses API: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")

            # Check if it's a model not found error
            if "model" in str(e).lower() and (
                "not found" in str(e).lower() or "does not exist" in str(e).lower()
            ):
                logger.error(
                    f"Model {os.getenv('TRIAGE_MODEL', 'gpt-5-nano')} not available"
                )
                logger.error(
                    "Ensure TRIAGE_MODEL env var is set to a valid model (gpt-5-nano, gpt-5-mini, gpt-5)"
                )
                logger.error(
                    "Available models: gpt-5-nano, gpt-5-mini, gpt-5 (NOT gpt-4o-mini!)"
                )

        # Fallback analysis if API fails
        logger.warning("Using fallback analysis due to API failure")

        # Basic heuristic fallback for critical violations
        violations = []
        coaching = []
        reminders = []

        thought_lower = thought.lower()

        # Check for reflexive agreement
        if any(
            phrase in thought_lower
            for phrase in ["you're right", "you're absolutely", "absolutely right"]
        ):
            violations.append("Reflexive agreement without analysis")
            reminders.append("Evaluate ideas on MERITS before agreeing")
            coaching.append("Have you verified this assumption?")

        # Check for overconfidence
        if any(
            phrase in thought_lower
            for phrase in ["will definitely", "obviously", "clearly must"]
        ):
            violations.append("Overconfidence without evidence")
            coaching.append("What evidence supports this certainty?")

        # Check for repetition (simple pattern)
        if "again" in thought_lower or "still" in thought_lower:
            patterns = ["Possible repeated attempt"]
            coaching.append(
                "Are you trying the same approach? What could you try differently?"
            )
        else:
            patterns = []

        return {
            "violations": violations,
            "patterns": patterns,
            "coaching_questions": coaching,
            "needs_escalation": len(violations) > 0,
            "escalation_reason": "Violations detected" if violations else None,
            "reminders": reminders,
            "confidence": 0.3,
            "analysis": f"Fallback heuristic analysis - {len(violations)} violations detected",
        }

    async def store_pattern_directly(
        self, content: str, tags: List[str]
    ) -> Optional[str]:
        """Store analysis pattern in KB using direct access (FAST!)"""
        try:
            result = await self.store.store(
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

        logger.info(f"=== TRIAGE ANALYSIS START ===")
        logger.info(f"Thought #{analysis.thought_number}: {analysis.thought[:100]}...")
        logger.info(f"Session: {analysis.session_id}")
        logger.info(f"History length: {len(analysis.history)}")

        # Load instructions from KB (direct access)
        logger.info("Loading instructions from KB...")
        instructions = await self.load_instructions_from_kb()
        logger.info(
            f"Loaded {len(instructions.get('global_rules', []))} global rules, {len(instructions.get('project_rules', []))} project rules"
        )

        # Get extended thought history (direct access)
        logger.info("Loading thought history...")
        extended_history = await self.get_thought_history(analysis.session_id)
        logger.info(f"Extended history: {len(extended_history)} entries")

        # Analyze with nano model
        logger.info("Starting AI analysis...")
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

        # Log analysis results
        logger.info(f"=== AI ANALYSIS RESULTS ===")
        logger.info(f"Violations detected: {len(ai_analysis.get('violations', []))}")
        logger.info(f"Violations: {ai_analysis.get('violations', [])}")
        logger.info(f"Patterns detected: {len(ai_analysis.get('patterns', []))}")
        logger.info(f"Patterns: {ai_analysis.get('patterns', [])}")
        logger.info(
            f"Coaching questions: {len(ai_analysis.get('coaching_questions', []))}"
        )
        logger.info(f"Needs escalation: {ai_analysis.get('needs_escalation', False)}")
        logger.info(f"Confidence: {ai_analysis.get('confidence', 0.0)}")
        logger.info(f"Analysis: {ai_analysis.get('analysis', 'No analysis')[:200]}...")

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
            needs_escalation=(
                ai_analysis.get("needs_escalation", False)
                if self.mode != "shadow"
                else False
            ),
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
        logger.info(f"=== TRIAGE ANALYSIS END ===")

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
    neo4j_status = "connected" if analyzer.store.neo4j_driver else "disconnected"

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
        if analyzer.store.neo4j_driver:
            analyzer.store.neo4j_driver.close()
            logger.info("Closed Neo4j connection")
    except:
        pass


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("TRIAGE_PORT", "8102"))
    uvicorn.run(app, host="0.0.0.0", port=port)
