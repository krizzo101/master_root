"""
Token-Efficient Group Chat System for Multi-Agent Coordination
Reduces token usage through smart context sharing and deduplication
"""
import asyncio
import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class ChatMessage:
    """Individual chat message"""

    id: str
    agent_id: str
    content: str
    timestamp: float
    message_type: str = "chat"  # chat, system, action, result
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None
    token_count: int = 0
    dedupe_hash: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ChatMessage":
        return cls(**data)


@dataclass
class AgentSession:
    """Agent session in group chat"""

    agent_id: str
    agent_type: str
    status: str = "active"  # active, idle, working, disconnected
    last_seen: float = None
    token_budget: int = 100000  # Token budget for this agent
    tokens_used: int = 0
    context_window: int = 8000  # How much chat history this agent needs

    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = time.time()


class GroupChatManager:
    """Manages token-efficient multi-agent group chat"""

    def __init__(self, chat_id: str = None, max_history: int = 1000):
        self.chat_id = chat_id or f"chat_{int(time.time())}"
        self.max_history = max_history

        # Chat state
        self.messages: List[ChatMessage] = []
        self.agents: Dict[str, AgentSession] = {}
        self.threads: Dict[str, List[str]] = {}  # thread_id -> message_ids

        # Token optimization
        self.dedupe_cache: Dict[str, str] = {}  # content_hash -> message_id
        self.context_cache: Dict[str, Dict] = {}  # agent_id -> cached context

        # WebSocket server for real-time communication
        self.websocket_server = None
        self.websocket_clients: Set = set()

        # Persistent storage
        self.storage_path = Path(".claude/group_chats") / self.chat_id
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Load existing chat history
        self._load_chat_history()

    def calculate_content_hash(self, content: str) -> str:
        """Calculate hash for message deduplication"""
        # Normalize content for deduplication
        normalized = content.strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]

    def add_agent(
        self, agent_id: str, agent_type: str, token_budget: int = 100000
    ) -> AgentSession:
        """Add agent to group chat"""
        session = AgentSession(
            agent_id=agent_id,
            agent_type=agent_type,
            token_budget=token_budget,
            last_seen=time.time(),
        )

        self.agents[agent_id] = session

        # Send welcome message
        welcome_msg = self.add_message(
            agent_id="system",
            content=f"🤖 {agent_id} ({agent_type}) joined the chat",
            message_type="system",
        )

        self._save_chat_state()
        self._broadcast_to_websockets(welcome_msg.to_dict())

        return session

    def add_message(
        self,
        agent_id: str,
        content: str,
        message_type: str = "chat",
        thread_id: str = None,
        reply_to: str = None,
    ) -> ChatMessage:
        """Add message with token optimization"""

        # Check for duplicate content
        content_hash = self.calculate_content_hash(content)
        if content_hash in self.dedupe_cache and message_type == "chat":
            # Return reference to existing message instead of creating duplicate
            existing_msg_id = self.dedupe_cache[content_hash]
            existing_msg = next(
                (m for m in self.messages if m.id == existing_msg_id), None
            )
            if existing_msg:
                print(
                    f"🔄 Deduplicated message from {agent_id} (saved ~{len(content)} tokens)"
                )
                return existing_msg

        # Estimate token count (rough approximation: 4 chars per token)
        token_count = len(content) // 4

        # Create message
        message = ChatMessage(
            id=f"msg_{int(time.time())}_{len(self.messages)}",
            agent_id=agent_id,
            content=content,
            timestamp=time.time(),
            message_type=message_type,
            thread_id=thread_id,
            reply_to=reply_to,
            token_count=token_count,
            dedupe_hash=content_hash,
        )

        # Add to messages
        self.messages.append(message)

        # Update deduplication cache
        if message_type == "chat":
            self.dedupe_cache[content_hash] = message.id

        # Update thread tracking
        if thread_id:
            if thread_id not in self.threads:
                self.threads[thread_id] = []
            self.threads[thread_id].append(message.id)

        # Update agent token usage
        if agent_id in self.agents:
            self.agents[agent_id].tokens_used += token_count
            self.agents[agent_id].last_seen = time.time()

        # Trim history if needed
        self._trim_history()

        # Save and broadcast
        self._save_chat_state()
        self._broadcast_to_websockets(message.to_dict())
        self._invalidate_context_cache()

        return message

    def get_context_for_agent(self, agent_id: str, max_tokens: int = None) -> Dict:
        """Get optimized context for specific agent (token-efficient)"""

        agent_session = self.agents.get(agent_id)
        if not agent_session:
            return {"messages": [], "token_count": 0}

        # Use agent's context window or provided max_tokens
        max_tokens = max_tokens or agent_session.context_window

        # Check cache
        cache_key = f"{agent_id}_{max_tokens}_{len(self.messages)}"
        if cache_key in self.context_cache:
            return self.context_cache[cache_key]

        # Build context efficiently
        relevant_messages = []
        total_tokens = 0

        # Start from most recent messages
        for message in reversed(self.messages):
            # Skip if adding this would exceed token limit
            if total_tokens + message.token_count > max_tokens:
                break

            # Always include system messages and agent's own messages
            include_message = (
                message.message_type in ["system", "action", "result"]
                or message.agent_id == agent_id
                or
                # Include recent messages from other agents (for context)
                (time.time() - message.timestamp < 3600)  # Last hour
            )

            if include_message:
                relevant_messages.insert(
                    0, message
                )  # Insert at beginning to maintain order
                total_tokens += message.token_count

        context = {
            "messages": [msg.to_dict() for msg in relevant_messages],
            "token_count": total_tokens,
            "agent_count": len(self.agents),
            "active_threads": list(self.threads.keys()),
        }

        # Cache the result
        self.context_cache[cache_key] = context

        return context

    def create_thread(self, topic: str, creator_agent: str) -> str:
        """Create focused discussion thread"""
        thread_id = f"thread_{int(time.time())}_{topic.replace(' ', '_')[:20]}"

        thread_msg = self.add_message(
            agent_id="system",
            content=f"🧵 {creator_agent} started thread: {topic}",
            message_type="system",
            thread_id=thread_id,
        )

        return thread_id

    def get_token_usage_summary(self) -> Dict:
        """Get token usage summary for all agents"""
        total_tokens = sum(agent.tokens_used for agent in self.agents.values())
        total_budget = sum(agent.token_budget for agent in self.agents.values())

        return {
            "total_tokens_used": total_tokens,
            "total_budget": total_budget,
            "utilization_rate": total_tokens / total_budget if total_budget > 0 else 0,
            "agents": {
                agent_id: {
                    "tokens_used": agent.tokens_used,
                    "budget": agent.token_budget,
                    "utilization": agent.tokens_used / agent.token_budget
                    if agent.token_budget > 0
                    else 0,
                }
                for agent_id, agent in self.agents.items()
            },
            "savings": {
                "dedupe_cache_size": len(self.dedupe_cache),
                "context_cache_size": len(self.context_cache),
                "estimated_tokens_saved": len(self.dedupe_cache) * 50,  # Rough estimate
            },
        }

    def _trim_history(self):
        """Trim chat history to stay within limits"""
        if len(self.messages) > self.max_history:
            # Keep most recent messages and important system messages
            system_messages = [m for m in self.messages if m.message_type == "system"][
                -10:
            ]  # Keep last 10 system msgs
            recent_messages = [m for m in self.messages if m.message_type != "system"][
                -(self.max_history - 10) :
            ]  # Keep recent chat

            self.messages = system_messages + recent_messages

            # Clean up dedupe cache
            valid_hashes = {msg.dedupe_hash for msg in self.messages if msg.dedupe_hash}
            self.dedupe_cache = {
                h: mid for h, mid in self.dedupe_cache.items() if h in valid_hashes
            }

    def _invalidate_context_cache(self):
        """Clear context cache when messages change"""
        self.context_cache.clear()

    def _save_chat_state(self):
        """Save chat state to persistent storage"""
        state = {
            "chat_id": self.chat_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "agents": {aid: asdict(agent) for aid, agent in self.agents.items()},
            "threads": self.threads,
            "saved_at": time.time(),
        }

        with open(self.storage_path / "chat_state.json", "w") as f:
            json.dump(state, f, indent=2)

    def _load_chat_history(self):
        """Load existing chat history"""
        state_file = self.storage_path / "chat_state.json"
        if not state_file.exists():
            return

        try:
            with open(state_file) as f:
                state = json.load(f)

            self.messages = [
                ChatMessage.from_dict(msg_data)
                for msg_data in state.get("messages", [])
            ]
            self.threads = state.get("threads", {})

            # Rebuild agents (they'll re-register when they connect)
            for agent_id, agent_data in state.get("agents", {}).items():
                self.agents[agent_id] = AgentSession(**agent_data)

            # Rebuild dedupe cache
            for msg in self.messages:
                if msg.dedupe_hash and msg.message_type == "chat":
                    self.dedupe_cache[msg.dedupe_hash] = msg.id

        except Exception as e:
            print(f"Warning: Could not load chat history: {e}")

    def _broadcast_to_websockets(self, data: Dict):
        """Broadcast message to all WebSocket clients"""
        if self.websocket_clients:
            # This would be implemented with actual WebSocket broadcasting
            pass

    def start_websocket_server(self, port: int = 8765):
        """Start WebSocket server for real-time communication"""
        try:
            import websockets
        except ImportError:
            print("⚠️ websockets not available - group chat web interface disabled")
            return

        async def handle_websocket(websocket, path):
            self.websocket_clients.add(websocket)
            try:
                # Send recent messages to new client
                recent_context = self.get_context_for_agent("human", max_tokens=4000)
                await websocket.send(
                    json.dumps({"type": "history", "data": recent_context})
                )

                # Handle incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "chat":
                            self.add_message(
                                agent_id=data.get("agent_id", "human"),
                                content=data.get("content", ""),
                                message_type="chat",
                            )
                    except Exception as e:
                        print(f"Error handling WebSocket message: {e}")

            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.websocket_clients.discard(websocket)

        # Start server in background thread with proper event loop
        def run_server():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                start_server = websockets.serve(handle_websocket, "localhost", port)
                loop.run_until_complete(start_server)
                loop.run_forever()
            except Exception as e:
                print(f"WebSocket server error: {e}")

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        print(f"🚀 Group chat WebSocket server started on ws://localhost:{port}")


# Tool for agents to connect to group chat
class GroupChatTool:
    """Tool that agents can use to participate in group chat"""

    def __init__(self, chat_manager: GroupChatManager, agent_id: str, agent_type: str):
        self.chat_manager = chat_manager
        self.agent_id = agent_id
        self.agent_type = agent_type

        # Register agent
        self.agent_session = chat_manager.add_agent(agent_id, agent_type)

    def send_message(self, content: str, thread_id: str = None) -> Dict:
        """Send message to group chat"""
        message = self.chat_manager.add_message(
            agent_id=self.agent_id, content=content, thread_id=thread_id
        )
        return {"message_id": message.id, "sent_at": message.timestamp}

    def get_recent_messages(self, max_tokens: int = 2000) -> Dict:
        """Get recent messages optimized for this agent"""
        return self.chat_manager.get_context_for_agent(self.agent_id, max_tokens)

    def create_thread(self, topic: str) -> str:
        """Create new discussion thread"""
        return self.chat_manager.create_thread(topic, self.agent_id)

    def get_status(self) -> Dict:
        """Get chat and token usage status"""
        usage = self.chat_manager.get_token_usage_summary()
        my_usage = usage["agents"].get(self.agent_id, {})

        return {
            "agent_id": self.agent_id,
            "tokens_used": my_usage.get("tokens_used", 0),
            "token_budget": my_usage.get("token_budget", 0),
            "other_agents": [
                aid for aid in self.chat_manager.agents.keys() if aid != self.agent_id
            ],
            "active_threads": list(self.chat_manager.threads.keys()),
            "total_messages": len(self.chat_manager.messages),
        }
