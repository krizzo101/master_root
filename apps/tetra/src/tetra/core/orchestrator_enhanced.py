"""
Enhanced orchestrator with monitoring and advanced features.
"""

import logging
from typing import Any, Dict, List, Optional

from .orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class EnhancedOrchestrator(Orchestrator):
    """Enhanced orchestrator with additional monitoring and features."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced orchestrator."""
        super().__init__(config)
        self.monitoring_enabled = True

    def list_sessions_enhanced(self) -> List[Dict[str, Any]]:
        """
        List all sessions with enhanced details.

        Returns:
            List of session dictionaries
        """
        sessions = []
        for session_id, session_data in self.sessions.items():
            sessions.append(
                {
                    "id": session_id,
                    "status": session_data.get("status", "unknown"),
                    "start_time": session_data.get("start_time"),
                    "end_time": session_data.get("end_time"),
                    "elapsed_time": session_data.get("elapsed_time"),
                }
            )
        return sessions
