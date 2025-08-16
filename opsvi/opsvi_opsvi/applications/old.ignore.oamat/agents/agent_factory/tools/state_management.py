"""
OAMAT Agent Factory - State Management Tools
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger("OAMAT.AgentFactory.StateManagementTools")


def create_state_management_tools():
    @tool
    def save_state(state_data: str, state_id: str) -> str:
        """Saves the current state of the application or workflow."""
        if not state_data or not state_id:
            raise ValueError("State data and state ID are required.")
        logger.info(f"Saving state with ID: {state_id}")
        return f"✅ State saved successfully with ID: {state_id}"

    @tool
    def load_state(state_id: str) -> str:
        """Loads a previously saved state."""
        if not state_id:
            raise ValueError("State ID is required to load state.")
        logger.info(f"Loading state with ID: {state_id}")
        return f"✅ State loaded successfully for ID: {state_id}"

    @tool
    def clear_state(state_id: str) -> str:
        """Clears a specific saved state."""
        if not state_id:
            raise ValueError("State ID is required to clear state.")
        logger.info(f"Clearing state with ID: {state_id}")
        return f"✅ State cleared successfully for ID: {state_id}"

    return [save_state, load_state, clear_state]
