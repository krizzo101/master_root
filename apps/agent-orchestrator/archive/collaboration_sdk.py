#!/usr/bin/env python3
"""
Agent Collaboration SDK
Easy-to-use SDK for agents to participate in collaborative workflows
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

import aiohttp
import websockets
from agent_collaboration_api import (
    AgentInfo,
    AgentStatus,
    HelpRequestMessage,
    Message,
    MessageType,
    Priority,
    TaskHandoffMessage,
    WorkspaceUpdate,
    create_discovery_share,
    create_help_request,
    create_task_handoff,
    create_workspace_update,
)

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class CollaborationConfig:
    """Configuration for collaboration SDK"""

    server_url: str = "http://localhost:8000"
    websocket_url: str = "ws://localhost:8000"
    agent_id: str = ""
    agent_type: str = ""
    capabilities: List[str] = field(default_factory=list)
    workspace_id: Optional[str] = None
    api_key: Optional[str] = None
    heartbeat_interval: int = 30  # seconds
    reconnect_interval: int = 5  # seconds
    max_reconnect_attempts: int = 10
    message_timeout: int = 30  # seconds


class CollaborationSDK:
    """
    Main SDK class for agent collaboration
    Provides high-level interface for messaging, coordination, and workspace sharing
    """

    def __init__(self, config: CollaborationConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.agent_id}")

        # Connection state
        self.connection_state = ConnectionState.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.session: Optional[aiohttp.ClientSession] = None

        # Message handling
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.correlation_handlers: Dict[str, Callable] = {}

        # Internal queues and tasks
        self.outbound_queue = asyncio.Queue()
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.message_processor_task: Optional[asyncio.Task] = None
        self.websocket_task: Optional[asyncio.Task] = None

        # Stats and monitoring
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "connection_attempts": 0,
            "last_heartbeat": None,
            "errors": 0,
        }

        # Default handlers
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Setup default message handlers"""
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.SYSTEM_ALERT, self._handle_system_alert)
        self.register_handler(
            MessageType.ERROR_NOTIFICATION, self._handle_error_notification
        )

    async def start(self) -> bool:
        """Start the collaboration SDK"""
        self.logger.info(f"Starting collaboration SDK for agent {self.config.agent_id}")

        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.config.message_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # Register agent
            success = await self._register_agent()
            if not success:
                return False

            # Start WebSocket connection
            self.websocket_task = asyncio.create_task(self._websocket_handler())

            # Start message processor
            self.message_processor_task = asyncio.create_task(
                self._process_outbound_messages()
            )

            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self.logger.info("Collaboration SDK started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start SDK: {e}")
            await self.stop()
            return False

    async def stop(self):
        """Stop the collaboration SDK"""
        self.logger.info("Stopping collaboration SDK")

        # Cancel tasks
        for task in [
            self.websocket_task,
            self.message_processor_task,
            self.heartbeat_task,
        ]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None

        self.connection_state = ConnectionState.DISCONNECTED
        self.logger.info("Collaboration SDK stopped")

    async def _register_agent(self) -> bool:
        """Register agent with collaboration server"""
        try:
            agent_data = {
                "agent_id": self.config.agent_id,
                "agent_type": self.config.agent_type,
                "capabilities": self.config.capabilities,
                "workspace_id": self.config.workspace_id,
                "metadata": {},
            }

            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            async with self.session.post(
                f"{self.config.server_url}/api/v1/agents/register",
                json=agent_data,
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Agent registered successfully: {result}")
                    return True
                else:
                    self.logger.error(
                        f"Registration failed: {response.status} - {await response.text()}"
                    )
                    return False
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            return False

    async def _websocket_handler(self):
        """Handle WebSocket connection with auto-reconnection"""
        reconnect_attempts = 0

        while reconnect_attempts < self.config.max_reconnect_attempts:
            try:
                self.connection_state = ConnectionState.CONNECTING
                self.stats["connection_attempts"] += 1

                ws_url = f"{self.config.websocket_url}/ws/collaboration/{self.config.agent_id}"

                async with websockets.connect(ws_url) as websocket:
                    self.websocket = websocket
                    self.connection_state = ConnectionState.CONNECTED
                    reconnect_attempts = 0  # Reset on successful connection

                    self.logger.info("WebSocket connected")

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self._handle_incoming_message(data)
                        except json.JSONDecodeError:
                            self.logger.error(f"Invalid JSON received: {message}")
                        except Exception as e:
                            self.logger.error(f"Message handling error: {e}")
                            self.stats["errors"] += 1

            except (
                websockets.exceptions.ConnectionClosed,
                websockets.exceptions.WebSocketException,
                ConnectionRefusedError,
            ) as e:
                self.connection_state = ConnectionState.RECONNECTING
                reconnect_attempts += 1

                self.logger.warning(
                    f"WebSocket connection lost ({e}), attempt {reconnect_attempts}"
                )

                if reconnect_attempts < self.config.max_reconnect_attempts:
                    await asyncio.sleep(self.config.reconnect_interval)
                else:
                    self.logger.error("Max reconnection attempts reached")
                    self.connection_state = ConnectionState.FAILED
                    break

            except Exception as e:
                self.logger.error(f"Unexpected WebSocket error: {e}")
                self.connection_state = ConnectionState.FAILED
                break

    async def _handle_incoming_message(self, data: Dict[str, Any]):
        """Handle incoming messages from WebSocket"""
        try:
            message_type = MessageType(data.get("message_type"))
            self.stats["messages_received"] += 1

            # Check for correlation ID (request-response pattern)
            correlation_id = data.get("correlation_id")
            if correlation_id and correlation_id in self.correlation_handlers:
                handler = self.correlation_handlers.pop(correlation_id)
                await handler(data)
                return

            # Handle with registered handler
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](data)
            else:
                self.logger.debug(f"No handler for message type: {message_type}")

        except ValueError:
            self.logger.error(f"Unknown message type: {data.get('message_type')}")
        except Exception as e:
            self.logger.error(f"Message handling error: {e}")

    async def _process_outbound_messages(self):
        """Process outbound message queue"""
        while True:
            try:
                message_data = await self.outbound_queue.get()

                if (
                    self.websocket
                    and self.connection_state == ConnectionState.CONNECTED
                ):
                    await self.websocket.send(json.dumps(message_data))
                    self.stats["messages_sent"] += 1
                else:
                    self.logger.warning("WebSocket not connected, message not sent")

                self.outbound_queue.task_done()

            except Exception as e:
                self.logger.error(f"Outbound message processing error: {e}")

    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages"""
        while True:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                heartbeat_data = {
                    "type": "heartbeat",
                    "agent_id": self.config.agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "online",
                }

                await self.outbound_queue.put(heartbeat_data)
                self.stats["last_heartbeat"] = datetime.now().isoformat()

            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")

    # Public API Methods

    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register message handler for specific message type"""
        self.message_handlers[message_type] = handler
        self.logger.debug(f"Registered handler for {message_type}")

    async def send_message(self, message: Message) -> bool:
        """Send message to collaboration system"""
        try:
            # Set message ID if not provided
            if not message.message_id:
                message.message_id = str(uuid.uuid4())

            # Ensure from_agent is set
            if not message.from_agent:
                message.from_agent = self.config.agent_id

            message_data = {"type": "message", **message.to_dict()}

            await self.outbound_queue.put(message_data)
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    async def send_task_handoff(
        self, to_agent: str, task_data: TaskHandoffMessage
    ) -> bool:
        """Send task handoff to specific agent"""
        message = create_task_handoff(self.config.agent_id, to_agent, task_data)
        return await self.send_message(message)

    async def request_help(self, help_data: HelpRequestMessage) -> bool:
        """Broadcast help request to available agents"""
        message = create_help_request(self.config.agent_id, help_data)
        return await self.send_message(message)

    async def share_discovery(self, discovery_data: Dict[str, Any]) -> bool:
        """Share discovery/insight with other agents"""
        message = create_discovery_share(self.config.agent_id, discovery_data)
        return await self.send_message(message)

    async def update_workspace(self, workspace_data: WorkspaceUpdate) -> bool:
        """Notify about workspace changes"""
        message = create_workspace_update(self.config.agent_id, workspace_data)
        return await self.send_message(message)

    async def update_status(self, status: AgentStatus, metadata: Dict = None) -> bool:
        """Update agent status"""
        try:
            data = {"status": status.value, "metadata": metadata or {}}

            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            async with self.session.post(
                f"{self.config.server_url}/api/v1/agents/{self.config.agent_id}/status",
                json=data,
                headers=headers,
            ) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Status update error: {e}")
            return False

    async def get_active_agents(self) -> List[Dict]:
        """Get list of active collaborating agents"""
        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            async with self.session.get(
                f"{self.config.server_url}/api/v1/agents/active", headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("agents", [])
                return []
        except Exception as e:
            self.logger.error(f"Get active agents error: {e}")
            return []

    async def wait_for_response(
        self, correlation_id: str, timeout: int = 30
    ) -> Optional[Dict]:
        """Wait for response message with specific correlation ID"""
        response_future = asyncio.Future()

        async def response_handler(data):
            response_future.set_result(data)

        self.correlation_handlers[correlation_id] = response_handler

        try:
            return await asyncio.wait_for(response_future, timeout)
        except asyncio.TimeoutError:
            self.correlation_handlers.pop(correlation_id, None)
            return None

    def get_connection_state(self) -> ConnectionState:
        """Get current connection state"""
        return self.connection_state

    def get_stats(self) -> Dict[str, Any]:
        """Get SDK statistics"""
        return self.stats.copy()

    # Default message handlers

    async def _handle_heartbeat(self, data: Dict[str, Any]):
        """Default heartbeat handler"""
        self.logger.debug("Heartbeat received")

    async def _handle_system_alert(self, data: Dict[str, Any]):
        """Default system alert handler"""
        content = data.get("content", {})
        self.logger.warning(f"System alert: {content}")

    async def _handle_error_notification(self, data: Dict[str, Any]):
        """Default error notification handler"""
        content = data.get("content", {})
        self.logger.error(f"Error notification: {content}")


# Convenience functions and decorators


def collaboration_handler(message_type: MessageType):
    """Decorator for message handlers"""

    def decorator(func: Callable):
        func._message_type = message_type
        return func

    return decorator


class CollaborativeAgent:
    """
    Base class for collaborative agents
    Provides common patterns and helper methods
    """

    def __init__(self, agent_id: str, agent_type: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.sdk: Optional[CollaborationSDK] = None
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")

    async def initialize_collaboration(self, config: CollaborationConfig):
        """Initialize collaboration SDK"""
        config.agent_id = self.agent_id
        config.agent_type = self.agent_type
        config.capabilities = self.capabilities

        self.sdk = CollaborationSDK(config)

        # Auto-register handlers using decorators
        self._register_decorated_handlers()

        return await self.sdk.start()

    def _register_decorated_handlers(self):
        """Register methods decorated with @collaboration_handler"""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "_message_type"):
                self.sdk.register_handler(attr._message_type, attr)
                self.logger.debug(
                    f"Auto-registered handler {attr_name} for {attr._message_type}"
                )

    async def shutdown_collaboration(self):
        """Shutdown collaboration SDK"""
        if self.sdk:
            await self.sdk.stop()

    # Helper methods for common operations

    async def broadcast_status(self, status: str, details: Dict = None):
        """Broadcast status update to interested agents"""
        if self.sdk:
            await self.sdk.update_status(AgentStatus(status), details)

    async def find_capable_agent(
        self, required_capabilities: List[str]
    ) -> Optional[str]:
        """Find agent with required capabilities"""
        if not self.sdk:
            return None

        agents = await self.sdk.get_active_agents()
        for agent in agents:
            agent_caps = set(agent.get("capabilities", []))
            if set(required_capabilities).issubset(agent_caps):
                return agent["agent_id"]

        return None

    async def delegate_task(
        self,
        task_id: str,
        task_type: str,
        description: str,
        required_capabilities: List[str],
    ) -> bool:
        """Delegate task to capable agent"""
        target_agent = await self.find_capable_agent(required_capabilities)

        if not target_agent:
            self.logger.warning(
                f"No capable agent found for capabilities: {required_capabilities}"
            )
            return False

        task_data = TaskHandoffMessage(
            task_id=task_id,
            task_type=task_type,
            task_description=description,
            from_agent=self.agent_id,
            to_agent=target_agent,
            context={"required_capabilities": required_capabilities},
        )

        return await self.sdk.send_task_handoff(target_agent, task_data)


# Example usage
async def example_collaborative_agent():
    """Example of using the collaboration SDK"""

    class ExampleAgent(CollaborativeAgent):
        def __init__(self):
            super().__init__(
                agent_id="example_agent_001",
                agent_type="research_agent",
                capabilities=["web_research", "data_analysis", "report_generation"],
            )

        @collaboration_handler(MessageType.TASK_HANDOFF)
        async def handle_task_handoff(self, data: Dict[str, Any]):
            """Handle incoming task handoffs"""
            content = data.get("content", {})
            task_id = content.get("task_id")
            self.logger.info(f"Received task handoff: {task_id}")

            # Process the task...
            await asyncio.sleep(2)  # Simulate work

            # Update status
            await self.broadcast_status("busy", {"current_task": task_id})

        @collaboration_handler(MessageType.HELP_REQUEST)
        async def handle_help_request(self, data: Dict[str, Any]):
            """Handle help requests from other agents"""
            content = data.get("content", {})
            skills_needed = content.get("skills_needed", [])

            # Check if we can help
            if any(skill in self.capabilities for skill in skills_needed):
                self.logger.info(f"Can help with: {skills_needed}")
                # Send help response...

    # Create and start agent
    agent = ExampleAgent()

    config = CollaborationConfig(
        server_url="http://localhost:8000", websocket_url="ws://localhost:8000"
    )

    await agent.initialize_collaboration(config)

    # Run for a while
    await asyncio.sleep(60)

    await agent.shutdown_collaboration()


if __name__ == "__main__":
    asyncio.run(example_collaborative_agent())
