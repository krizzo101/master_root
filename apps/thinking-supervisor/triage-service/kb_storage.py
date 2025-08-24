#!/usr/bin/env python3
"""
KB Storage Integration for Thinking Patterns
Uses the existing knowledge tool with nano agents for automatic transformation
"""
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ThinkingPatternStorage:
    """
    Store thinking patterns in the Knowledge Base using the existing knowledge tools.
    The nano agent will automatically transform and structure the data.
    """

    def __init__(self):
        self.stored_patterns = []  # Local cache for debugging

    async def store_thinking_pattern(
        self,
        thought: str,
        risk_level: str,
        patterns_detected: List[str],
        would_escalate: bool,
        session_id: str,
        thought_number: int,
        confidence: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Store a thinking pattern in the Knowledge Base.

        The nano agent will automatically transform this into proper structure.
        """

        # Build the content that will be transformed by nano agent
        content = f"""
        THINKING PATTERN ANALYSIS

        Thought: {thought}
        Risk Level: {risk_level}
        Patterns Detected: {', '.join(patterns_detected) if patterns_detected else 'None'}
        Would Escalate: {'Yes' if would_escalate else 'No'}
        Session: {session_id}
        Thought Number: {thought_number}
        Confidence: {confidence}
        Timestamp: {datetime.utcnow().isoformat()}

        Analysis Details:
        - This thought was analyzed by the triage system
        - Risk assessment determined: {risk_level}
        - Pattern detection found: {len(patterns_detected)} patterns
        - Escalation decision: {'Would have escalated for intervention' if would_escalate else 'No escalation needed'}
        """

        # Add specific insights based on patterns
        if "potential_agreeability" in patterns_detected:
            content += "\n- Agreeability pattern detected: User agreement without critical analysis"
        if "unsubstantiated_claim" in patterns_detected:
            content += (
                "\n- Unsubstantiated claim: Statement made without supporting evidence"
            )
        if "technical_impossibility" in patterns_detected:
            content += "\n- Technical impossibility: Claim that cannot be implemented as described"

        # Tags for easier retrieval
        tags = [
            f"risk_{risk_level}",
            f"session_{session_id}",
            "thinking_pattern",
            "triage_analysis",
        ]
        tags.extend([f"pattern_{p}" for p in patterns_detected])

        if would_escalate:
            tags.append("escalation_candidate")

        # This will be sent to the knowledge tool
        # The nano agent will transform it automatically
        result = {
            "content": content,
            "knowledge_type": "THINKING_PATTERN",
            "tags": ", ".join(tags),
            "metadata": {
                "risk_level": risk_level,
                "patterns": patterns_detected,
                "would_escalate": would_escalate,
                "session_id": session_id,
                "thought_number": thought_number,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        # Store locally for debugging
        self.stored_patterns.append(result)

        # In production, this would call the knowledge MCP tool:
        # mcp__knowledge__knowledge_store(
        #     content=content,
        #     knowledge_type="THINKING_PATTERN",
        #     tags=', '.join(tags)
        # )

        logger.info(
            f"Stored thinking pattern: risk={risk_level}, patterns={patterns_detected}"
        )

        return {
            "success": True,
            "knowledge_id": self._generate_id(thought, session_id, thought_number),
            "stored_data": result,
        }

    async def query_similar_patterns(
        self, thought: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query for similar thinking patterns from the KB.

        In production, this would use:
        mcp__knowledge__knowledge_query(
            query_type="search",
            search_text=thought,
            limit=limit
        )
        """
        # For now, return from local cache
        similar = []
        thought_words = set(thought.lower().split())

        for pattern in self.stored_patterns[-100:]:  # Check last 100
            pattern_words = set(pattern["content"].lower().split())
            overlap = len(thought_words.intersection(pattern_words))
            if overlap > 3:  # Simple similarity
                similar.append(pattern)
                if len(similar) >= limit:
                    break

        return similar

    async def get_pattern_statistics(
        self, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about stored patterns.

        In production, would query KB with:
        mcp__knowledge__knowledge_query(
            query_type="by_type",
            knowledge_type="THINKING_PATTERN"
        )
        """
        if session_id:
            patterns = [
                p
                for p in self.stored_patterns
                if p["metadata"]["session_id"] == session_id
            ]
        else:
            patterns = self.stored_patterns

        if not patterns:
            return {"message": "No patterns stored yet"}

        # Calculate statistics
        total = len(patterns)
        risk_dist = {}
        pattern_freq = {}
        escalation_count = 0

        for p in patterns:
            meta = p["metadata"]

            # Risk distribution
            risk = meta["risk_level"]
            risk_dist[risk] = risk_dist.get(risk, 0) + 1

            # Pattern frequency
            for pattern in meta["patterns"]:
                pattern_freq[pattern] = pattern_freq.get(pattern, 0) + 1

            # Escalation count
            if meta["would_escalate"]:
                escalation_count += 1

        return {
            "total_patterns": total,
            "risk_distribution": risk_dist,
            "pattern_frequency": pattern_freq,
            "escalation_rate": escalation_count / total if total > 0 else 0,
            "escalation_count": escalation_count,
            "session_id": session_id,
        }

    def _generate_id(self, thought: str, session_id: str, thought_number: int) -> str:
        """Generate a unique ID for the knowledge entry"""
        content = f"{thought}:{session_id}:{thought_number}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
