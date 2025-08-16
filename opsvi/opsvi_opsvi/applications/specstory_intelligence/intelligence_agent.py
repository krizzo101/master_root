"""
Intelligence Agent Prototype

Extracts high-value intelligence insights from cleaned logs or atomic parser output.
- User guidance
- Agent realizations
- Learning opportunities
- Decision points

Links each insight to atomic component IDs (if available).

Reference: docs/applications/agent_intelligence_pipeline.md (authoritative schema)
"""

from datetime import datetime
from typing import Dict, List, Optional
import uuid


class IntelligenceAgent:
    def __init__(self):
        pass

    def extract_insights(
        self, cleaned_lines: List[str], atomic_components: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Extract intelligence insights from cleaned log lines and/or atomic components.
        Returns a list of dicts matching the minimal intelligence schema.
        """
        insights = []
        # TODO: Implement more sophisticated NLP/agent workflows
        for i, line in enumerate(cleaned_lines):
            # Example: User guidance
            if any(
                kw in line.lower()
                for kw in ["do not", "always", "never", "must", "should"]
            ):
                insights.append(
                    {
                        "insight_id": str(uuid.uuid4()),
                        "type": "user_guidance",
                        "text": line.strip(),
                        "source_file": None,  # Fill in as needed
                        "atomic_component_ids": self._find_related_components(
                            i, atomic_components
                        ),
                        "confidence": 0.8,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {"line_number": i + 1},
                    }
                )
            # Example: Agent realization
            if "realization" in line.lower() or "aha" in line.lower():
                insights.append(
                    {
                        "insight_id": str(uuid.uuid4()),
                        "type": "agent_realization",
                        "text": line.strip(),
                        "source_file": None,
                        "atomic_component_ids": self._find_related_components(
                            i, atomic_components
                        ),
                        "confidence": 0.7,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {"line_number": i + 1},
                    }
                )
            # Example: Learning opportunity
            if "learn" in line.lower() or "opportunity" in line.lower():
                insights.append(
                    {
                        "insight_id": str(uuid.uuid4()),
                        "type": "learning_opportunity",
                        "text": line.strip(),
                        "source_file": None,
                        "atomic_component_ids": self._find_related_components(
                            i, atomic_components
                        ),
                        "confidence": 0.7,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {"line_number": i + 1},
                    }
                )
            # Example: Decision point
            if any(
                kw in line.lower()
                for kw in ["decided", "chose", "selected", "opted for"]
            ):
                insights.append(
                    {
                        "insight_id": str(uuid.uuid4()),
                        "type": "decision_point",
                        "text": line.strip(),
                        "source_file": None,
                        "atomic_component_ids": self._find_related_components(
                            i, atomic_components
                        ),
                        "confidence": 0.7,
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {"line_number": i + 1},
                    }
                )
        return insights

    def _find_related_components(
        self, line_idx: int, atomic_components: Optional[List[Dict]]
    ) -> List[str]:
        """
        Prototype: Link insight to atomic component IDs based on line number proximity.
        TODO: Improve with richer mapping logic.
        """
        if not atomic_components:
            return []
        related = []
        for comp in atomic_components:
            if "line_start" in comp and abs(comp["line_start"] - (line_idx + 1)) < 5:
                related.append(comp.get("component_id", ""))
        return related


# TODO: Expand with agent workflow orchestration, richer NLP, and cross-file analysis.
