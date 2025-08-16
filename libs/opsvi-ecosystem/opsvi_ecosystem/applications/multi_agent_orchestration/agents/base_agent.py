"""
Base agent interface for the multi-agent orchestration system.

Defines the abstract base class that all agents must implement,
providing a consistent interface for agent creation and interaction.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ..common.types import (
    AgentCapability,
    AgentError,
    CommunicationError,
    Message,
    MessageType,
    Task,
    TaskStatus,
)
from ..communication.message_broker import MessageBroker
from ..tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.

    Agents are autonomous entities that can execute tasks, communicate
    with other agents, and use tools to accomplish their goals.
    """

    def __init__(
        self,
        agent_id: str,
        name: str = "Base Agent",
        description: str = "Generic agent base class",
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            description: Agent description
            logger: Optional logger instance
        """
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.logger = logger or logging.getLogger(__name__)
        self.created_at = datetime.now()

        # Agent state
        self._is_active = False
        self._current_task: Task | None = None
        self._task_history: list[Task] = []
        self._message_broker: MessageBroker | None = None

        # Tools and capabilities
        self._tools: dict[str, BaseTool] = {}
        self._capabilities: list[AgentCapability] = []

        # Collaboration
        self._collaborators: set[str] = set()
        self._pending_messages: list[Message] = []

        logger.info(f"Agent {self.agent_id} ({self.name}) initialized")

    @abstractmethod
    async def execute_task(self, task: Task) -> dict[str, Any]:
        """
        Execute a specific task.

        Args:
            task: Task to execute

        Returns:
            Task execution results

        Raises:
            AgentError: If task execution fails
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> list[AgentCapability]:
        """
        Get the agent's capabilities.

        Returns:
            List of agent capabilities
        """
        pass

    def set_message_broker(self, broker: MessageBroker) -> None:
        """Set the message broker for the agent."""
        self._message_broker = broker

    async def start(self) -> None:
        """
        Start the agent and register with the message broker.
        """
        if self._is_active:
            self.logger.warning(f"Agent {self.agent_id} is already active")
            return
        if not self._message_broker:
            raise RuntimeError("Message broker must be set before starting the agent.")
        self._message_broker.register_agent(self.agent_id, self._handle_message)
        self._is_active = True
        self.logger.info(
            f"Agent {self.agent_id} started and registered with message broker"
        )

    async def stop(self) -> None:
        """Stop the agent and unregister from the message broker."""
        if not self._is_active:
            return

        if self._message_broker:
            self._message_broker.unregister_agent(self.agent_id)
            self._message_broker = None

        self._is_active = False
        logger.info(f"Agent {self.agent_id} stopped")

    def add_tool(self, tool: BaseTool) -> None:
        """
        Add a tool to the agent's toolkit.

        Args:
            tool: Tool to add
        """
        self._tools[tool.name] = tool
        logger.debug(f"Tool {tool.name} added to agent {self.agent_id}")

    def remove_tool(self, tool_name: str) -> bool:
        """
        Remove a tool from the agent's toolkit.

        Args:
            tool_name: Name of tool to remove

        Returns:
            True if tool was removed, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.debug(f"Tool {tool_name} removed from agent {self.agent_id}")
            return True
        return False

    def get_available_tools(self) -> list[str]:
        """
        Get list of available tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    async def use_tool(
        self, tool_name: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Use a specific tool with given parameters.

        Args:
            tool_name: Name of tool to use
            parameters: Tool parameters

        Returns:
            Tool execution results

        Raises:
            AgentError: If tool is not available or execution fails
        """
        if tool_name not in self._tools:
            raise AgentError(f"Tool {tool_name} not available to agent {self.agent_id}")

        tool = self._tools[tool_name]
        logger.info(f"Agent {self.agent_id} using tool {tool_name}")

        try:
            result = await tool.safe_execute(parameters)
            logger.debug(
                f"Tool {tool_name} execution completed for agent {self.agent_id}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Tool {tool_name} execution failed for agent {self.agent_id}: {e}"
            )
            raise AgentError(f"Tool execution failed: {str(e)}")

    async def send_message(
        self,
        recipient_id: str,
        message_type: MessageType,
        content: dict[str, Any],
        correlation_id: str | None = None,
    ) -> bool:
        """
        Send a message to another agent.

        Args:
            recipient_id: ID of recipient agent
            message_type: Type of message
            content: Message content
            correlation_id: Optional correlation ID

        Returns:
            True if message was sent successfully

        Raises:
            CommunicationError: If message sending fails
        """
        if not self._message_broker:
            raise CommunicationError("Agent not connected to message broker")

        message = Message(
            sender_id=self.agent_id,
            recipient_id=recipient_id,
            message_type=message_type,
            content=content,
            correlation_id=correlation_id,
        )

        try:
            success = await self._message_broker.send_message(message)
            if success:
                logger.debug(f"Message sent from {self.agent_id} to {recipient_id}")
            return success
        except Exception as e:
            logger.error(
                f"Failed to send message from {self.agent_id} to {recipient_id}: {e}"
            )
            raise CommunicationError(f"Failed to send message: {str(e)}")

    async def broadcast_message(
        self, message_type: MessageType, content: dict[str, Any]
    ) -> int:
        """
        Broadcast a message to all agents.

        Args:
            message_type: Type of message
            content: Message content

        Returns:
            Number of agents the message was sent to

        Raises:
            CommunicationError: If broadcast fails
        """
        if not self._message_broker:
            raise CommunicationError("Agent not connected to message broker")

        message = Message(
            sender_id=self.agent_id, message_type=message_type, content=content
        )

        try:
            count = await self._message_broker.broadcast_message(message)
            logger.debug(f"Message broadcast from {self.agent_id} to {count} agents")
            return count
        except Exception as e:
            logger.error(f"Failed to broadcast message from {self.agent_id}: {e}")
            raise CommunicationError(f"Failed to broadcast message: {str(e)}")

    async def request_collaboration(
        self, recipient_id: str, task_description: str, required_capabilities: list[str]
    ) -> bool:
        """
        Request collaboration from another agent.

        Args:
            recipient_id: ID of agent to collaborate with
            task_description: Description of the collaborative task
            required_capabilities: Capabilities needed for the task

        Returns:
            True if collaboration request was sent
        """
        content = {
            "task_description": task_description,
            "required_capabilities": required_capabilities,
            "requesting_agent": self.agent_id,
            "timestamp": datetime.now().isoformat(),
        }

        return await self.send_message(
            recipient_id, MessageType.COLLABORATION_REQUEST, content
        )

    async def safe_execute_task(self, task: Task) -> dict[str, Any]:
        """
        Safely execute a task with comprehensive error handling.

        Args:
            task: Task to execute

        Returns:
            Task execution results with error handling
        """
        self._current_task = task
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()

        try:
            logger.info(f"Agent {self.agent_id} starting task {task.id}: {task.name}")

            # Execute the task
            result = await self.execute_task(task)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            logger.info(f"Agent {self.agent_id} completed task {task.id}")

            return {
                "success": True,
                "result": result,
                "task_id": task.id,
                "agent_id": self.agent_id,
                "execution_time": (task.completed_at - task.started_at).total_seconds(),
                "error": None,
            }

        except Exception as e:
            # Update task status on failure
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)

            logger.error(f"Agent {self.agent_id} failed to execute task {task.id}: {e}")

            return {
                "success": False,
                "result": None,
                "task_id": task.id,
                "agent_id": self.agent_id,
                "execution_time": (task.completed_at - task.started_at).total_seconds(),
                "error": str(e),
            }
        finally:
            # Add to task history
            self._task_history.append(task)
            self._current_task = None

    async def _handle_message(self, message: Message) -> None:
        """
        Handle incoming messages from other agents.

        Args:
            message: Incoming message
        """
        try:
            logger.debug(
                f"Agent {self.agent_id} received message {message.id} "
                f"from {message.sender_id}"
            )

            # Store message for processing
            self._pending_messages.append(message)

            # Handle different message types
            if message.message_type == MessageType.COLLABORATION_REQUEST:
                await self._handle_collaboration_request(message)
            elif message.message_type == MessageType.TASK_REQUEST:
                await self._handle_task_request(message)
            elif message.message_type == MessageType.STATUS_UPDATE:
                await self._handle_status_update(message)
            else:
                # Default handling for other message types
                await self._handle_generic_message(message)

        except Exception as e:
            logger.error(
                f"Error handling message {message.id} in agent {self.agent_id}: {e}"
            )

    async def _handle_collaboration_request(self, message: Message) -> None:
        """
        Handle collaboration requests from other agents.

        Args:
            message: Collaboration request message
        """
        # Default implementation - can be overridden by subclasses
        logger.info(
            f"Agent {self.agent_id} received collaboration request "
            f"from {message.sender_id}"
        )

        # Simple acceptance logic - can be made more sophisticated
        content = message.content
        required_capabilities = content.get("required_capabilities", [])

        # Check if we have the required capabilities
        our_capabilities = [cap.name for cap in self.get_capabilities()]
        can_collaborate = any(cap in our_capabilities for cap in required_capabilities)

        if can_collaborate:
            self._collaborators.add(message.sender_id)
            response_content = {
                "accepted": True,
                "available_capabilities": our_capabilities,
                "message": f"Agent {self.agent_id} accepts collaboration",
            }
        else:
            response_content = {
                "accepted": False,
                "available_capabilities": our_capabilities,
                "message": f"Agent {self.agent_id} cannot provide required capabilities",
            }

        # Send response
        await self.send_message(
            message.sender_id, MessageType.TASK_RESPONSE, response_content, message.id
        )

    async def _handle_task_request(self, message: Message) -> None:
        """
        Handle task requests from other agents.

        Args:
            message: Task request message
        """
        # Default implementation - can be overridden by subclasses
        logger.info(
            f"Agent {self.agent_id} received task request from {message.sender_id}"
        )

        # For now, just acknowledge the request
        response_content = {
            "acknowledged": True,
            "message": f"Task request received by {self.agent_id}",
        }

        await self.send_message(
            message.sender_id, MessageType.TASK_RESPONSE, response_content, message.id
        )

    async def _handle_status_update(self, message: Message) -> None:
        """
        Handle status updates from other agents.

        Args:
            message: Status update message
        """
        # Default implementation - just log the update
        logger.info(
            f"Agent {self.agent_id} received status update from {message.sender_id}: "
            f"{message.content}"
        )

    async def _handle_generic_message(self, message: Message) -> None:
        """
        Handle generic messages that don't fit other categories.

        Args:
            message: Generic message
        """
        # Default implementation - just log the message
        logger.debug(
            f"Agent {self.agent_id} received generic message from {message.sender_id}"
        )

    def get_status(self) -> dict[str, Any]:
        """
        Get the current status of the agent.

        Returns:
            Dictionary containing agent status information
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "is_active": self._is_active,
            "current_task": self._current_task.id if self._current_task else None,
            "tasks_completed": len(
                [t for t in self._task_history if t.status == TaskStatus.COMPLETED]
            ),
            "tasks_failed": len(
                [t for t in self._task_history if t.status == TaskStatus.FAILED]
            ),
            "available_tools": list(self._tools.keys()),
            "collaborators": list(self._collaborators),
            "pending_messages": len(self._pending_messages),
            "created_at": self.created_at.isoformat(),
        }

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id='{self.agent_id}', name='{self.name}')"

    def __repr__(self) -> str:
        """Detailed string representation of the agent."""
        return (
            f"{self.__class__.__name__}(id='{self.agent_id}', name='{self.name}', "
            f"active={self._is_active}, tools={len(self._tools)})"
        )
