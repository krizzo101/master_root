#!/usr/bin/env python3
"""
AI Assistant Framework - Agent Implementation
Created during DEVELOPMENT phase after proper SDLC process
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

class AgentStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    COMPLETED = "completed"

@dataclass
class Message:
    """Message passed between agents"""
    id: str
    sender: str
    recipient: str
    content: Dict[str, Any]
    timestamp: float

@dataclass
class Capability:
    """Agent capability description"""
    name: str
    description: str
    parameters: Dict[str, str]

class Agent:
    """Base agent class for the AI Assistant Framework"""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.status = AgentStatus.IDLE
        self.capabilities: List[Capability] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
    
    async def process(self, message: Message) -> Dict[str, Any]:
        """Process incoming message"""
        self.status = AgentStatus.PROCESSING
        try:
            # Process the message
            result = await self._handle_message(message)
            self.status = AgentStatus.COMPLETED
            return {
                "status": "success",
                "agent_id": self.agent_id,
                "result": result
            }
        except Exception as e:
            self.status = AgentStatus.ERROR
            return {
                "status": "error",
                "agent_id": self.agent_id,
                "error": str(e)
            }
    
    async def _handle_message(self, message: Message) -> Any:
        """Override in subclasses"""
        raise NotImplementedError("Subclasses must implement _handle_message")
    
    def get_capabilities(self) -> List[Capability]:
        """Return agent capabilities"""
        return self.capabilities
    
    def add_capability(self, capability: Capability):
        """Add a capability to the agent"""
        self.capabilities.append(capability)

class ToolAgent(Agent):
    """Agent that can execute tools"""
    
    def __init__(self, agent_id: str, name: str, tools: Dict[str, Any]):
        super().__init__(agent_id, name)
        self.tools = tools
        
        # Register tool capabilities
        for tool_name, tool_func in tools.items():
            self.add_capability(
                Capability(
                    name=tool_name,
                    description=f"Execute {tool_name} tool",
                    parameters={}
                )
            )
    
    async def _handle_message(self, message: Message) -> Any:
        """Execute tool based on message"""
        tool_name = message.content.get("tool")
        params = message.content.get("params", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Execute tool
        tool_func = self.tools[tool_name]
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**params)
        else:
            return tool_func(**params)

# Example usage
if __name__ == "__main__":
    async def example_tool(text: str) -> str:
        """Example async tool"""
        await asyncio.sleep(0.1)  # Simulate work
        return f"Processed: {text}"
    
    # Create agent with tool
    agent = ToolAgent(
        agent_id="agent_001",
        name="Example Agent",
        tools={"process_text": example_tool}
    )
    
    print(f"Agent {agent.name} created with capabilities:")
    for cap in agent.get_capabilities():
        print(f"  - {cap.name}: {cap.description}")