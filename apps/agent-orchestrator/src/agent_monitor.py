#!/usr/bin/env python3
"""
Agent Monitor - Minimal Implementation
Simple monitoring system for agent status tracking
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class AgentStatus(Enum):
    """Agent execution status"""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentStatusInfo:
    """Agent status information"""

    agent_id: str
    status: AgentStatus
    task_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None


class AgentStatusMonitor:
    """Minimal agent status monitor"""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir
        self.agents = {}
        self.enabled = True

    async def start_monitoring(self, agent_id: str, task_id: str):
        """Start monitoring an agent"""
        if not self.enabled:
            return

        self.agents[agent_id] = AgentStatusInfo(
            agent_id=agent_id, status=AgentStatus.RUNNING, task_id=task_id
        )

    async def stop_monitoring(
        self, agent_id: str, status: AgentStatus, error: str = None
    ):
        """Stop monitoring an agent"""
        if not self.enabled or agent_id not in self.agents:
            return

        self.agents[agent_id].status = status
        if error:
            self.agents[agent_id].error = error

    def get_status(self, agent_id: str) -> Optional[AgentStatusInfo]:
        """Get agent status"""
        return self.agents.get(agent_id)

    def get_all_status(self) -> Dict[str, AgentStatusInfo]:
        """Get all agent statuses"""
        return self.agents.copy()

    def disable(self):
        """Disable monitoring"""
        self.enabled = False

    def enable(self):
        """Enable monitoring"""
        self.enabled = True
