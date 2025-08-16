"""InterfaceAgent - Human and system interaction."""

from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import structlog

from ..core import BaseAgent, AgentConfig, AgentContext, AgentResult


logger = structlog.get_logger()


class InteractionType(Enum):
    """Types of interactions."""
    HUMAN = "human"
    SYSTEM = "system"
    API = "api"
    AGENT = "agent"
    CLI = "cli"
    GUI = "gui"


class MessageType(Enum):
    """Types of messages."""
    QUERY = "query"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    CONFIRMATION = "confirmation"
    PROMPT = "prompt"


class ResponseFormat(Enum):
    """Response formatting options."""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    STRUCTURED = "structured"


@dataclass
class Message:
    """Interaction message."""
    id: str
    type: MessageType
    content: Any
    sender: str
    recipient: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class Interaction:
    """Complete interaction session."""
    id: str
    type: InteractionType
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    status: str = "active"
    
    def add_message(self, message: Message):
        """Add message to interaction."""
        self.messages.append(message)
    
    def get_last_message(self) -> Optional[Message]:
        """Get the last message."""
        return self.messages[-1] if self.messages else None
    
    def get_messages_by_type(self, msg_type: MessageType) -> List[Message]:
        """Get messages by type."""
        return [msg for msg in self.messages if msg.type == msg_type]
    
    def end(self):
        """End the interaction."""
        self.ended_at = time.time()
        self.status = "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
            "duration": self.ended_at - self.started_at if self.ended_at else None
        }


@dataclass
class UserPreferences:
    """User interaction preferences."""
    response_format: ResponseFormat = ResponseFormat.TEXT
    verbosity: str = "normal"  # minimal, normal, detailed
    language: str = "en"
    timezone: str = "UTC"
    confirmation_required: bool = True
    auto_format: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class InterfaceAgent(BaseAgent):
    """Manages human and system interactions."""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize interface agent."""
        super().__init__(config or AgentConfig(
            name="InterfaceAgent",
            description="Human and system interaction",
            capabilities=["interact", "communicate", "format", "translate", "validate"],
            max_retries=2,
            timeout=30
        ))
        self.interactions: Dict[str, Interaction] = {}
        self.message_queue: List[Message] = []
        self.response_handlers: Dict[str, Callable] = {}
        self.user_preferences: Dict[str, UserPreferences] = {}
        self._message_counter = 0
        self._interaction_counter = 0
    
    def initialize(self) -> bool:
        """Initialize the interface agent."""
        # Register default handlers
        self._register_default_handlers()
        logger.info("interface_agent_initialized", agent=self.config.name)
        return True
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute interface task."""
        action = task.get("action", "interact")
        
        if action == "interact":
            return self._handle_interaction(task)
        elif action == "send":
            return self._send_message(task)
        elif action == "receive":
            return self._receive_message(task)
        elif action == "format":
            return self._format_response(task)
        elif action == "validate":
            return self._validate_input(task)
        elif action == "prompt":
            return self._prompt_user(task)
        elif action == "notify":
            return self._send_notification(task)
        elif action == "history":
            return self._get_history(task)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def interact(self, 
                user_id: str,
                message: str,
                interaction_type: InteractionType = InteractionType.HUMAN) -> Dict[str, Any]:
        """Handle user interaction."""
        result = self.execute({
            "action": "interact",
            "user_id": user_id,
            "message": message,
            "interaction_type": interaction_type.value
        })
        
        if "error" in result:
            raise RuntimeError(result["error"])
        
        return result
    
    def _handle_interaction(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a complete interaction."""
        user_id = task.get("user_id", "anonymous")
        message_content = task.get("message", "")
        interaction_type = task.get("interaction_type", "human")
        context = task.get("context", {})
        
        if not message_content:
            return {"error": "Message is required"}
        
        # Get or create interaction
        interaction_id = f"{user_id}_{interaction_type}"
        if interaction_id not in self.interactions:
            self._interaction_counter += 1
            interaction = Interaction(
                id=f"interaction_{self._interaction_counter}",
                type=InteractionType[interaction_type.upper()],
                context=context
            )
            self.interactions[interaction_id] = interaction
        else:
            interaction = self.interactions[interaction_id]
        
        # Create incoming message
        self._message_counter += 1
        incoming_msg = Message(
            id=f"msg_{self._message_counter}",
            type=MessageType.QUERY,
            content=message_content,
            sender=user_id,
            recipient=self.config.name
        )
        interaction.add_message(incoming_msg)
        
        # Process message
        response = self._process_message(incoming_msg, interaction)
        
        # Create response message
        self._message_counter += 1
        response_msg = Message(
            id=f"msg_{self._message_counter}",
            type=MessageType.RESPONSE,
            content=response,
            sender=self.config.name,
            recipient=user_id
        )
        interaction.add_message(response_msg)
        
        # Format response based on preferences
        formatted_response = self._format_for_user(response, user_id)
        
        logger.info(
            "interaction_handled",
            user_id=user_id,
            interaction_type=interaction_type,
            message_count=len(interaction.messages)
        )
        
        return {
            "response": formatted_response,
            "interaction_id": interaction.id,
            "message_id": response_msg.id
        }
    
    def _process_message(self, message: Message, interaction: Interaction) -> Any:
        """Process incoming message."""
        content = message.content
        
        # Analyze message intent
        intent = self._analyze_intent(content)
        
        # Route to appropriate handler
        if intent in self.response_handlers:
            handler = self.response_handlers[intent]
            response = handler(message, interaction)
        else:
            # Default processing
            response = self._default_handler(message, interaction)
        
        return response
    
    def _analyze_intent(self, content: str) -> str:
        """Analyze message intent."""
        content_lower = content.lower() if isinstance(content, str) else str(content).lower()
        
        # Simple intent detection
        if any(word in content_lower for word in ["help", "assist", "how"]):
            return "help"
        elif any(word in content_lower for word in ["status", "progress", "state"]):
            return "status"
        elif any(word in content_lower for word in ["error", "problem", "issue"]):
            return "error"
        elif any(word in content_lower for word in ["confirm", "yes", "no", "approve"]):
            return "confirmation"
        elif any(word in content_lower for word in ["configure", "setting", "preference"]):
            return "configuration"
        else:
            return "general"
    
    def _register_default_handlers(self):
        """Register default response handlers."""
        self.response_handlers.update({
            "help": self._handle_help,
            "status": self._handle_status,
            "error": self._handle_error,
            "confirmation": self._handle_confirmation,
            "configuration": self._handle_configuration,
            "general": self._default_handler
        })
    
    def _handle_help(self, message: Message, interaction: Interaction) -> str:
        """Handle help requests."""
        return (
            "Available commands:\n"
            "- help: Show this message\n"
            "- status: Check current status\n"
            "- configure: Adjust settings\n"
            "- history: View interaction history"
        )
    
    def _handle_status(self, message: Message, interaction: Interaction) -> str:
        """Handle status requests."""
        return {
            "status": "active",
            "interactions": len(self.interactions),
            "messages_processed": self._message_counter,
            "uptime": time.time() - interaction.started_at
        }
    
    def _handle_error(self, message: Message, interaction: Interaction) -> str:
        """Handle error reports."""
        return "Error report received. Please provide details about the issue."
    
    def _handle_confirmation(self, message: Message, interaction: Interaction) -> str:
        """Handle confirmations."""
        content_lower = message.content.lower()
        if "yes" in content_lower or "approve" in content_lower:
            return "Confirmed. Proceeding with the action."
        elif "no" in content_lower or "deny" in content_lower:
            return "Cancelled. Action will not be performed."
        else:
            return "Please respond with 'yes' to confirm or 'no' to cancel."
    
    def _handle_configuration(self, message: Message, interaction: Interaction) -> Dict[str, Any]:
        """Handle configuration requests."""
        user_id = message.sender
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences()
        
        prefs = self.user_preferences[user_id]
        return {
            "current_preferences": {
                "response_format": prefs.response_format.value,
                "verbosity": prefs.verbosity,
                "language": prefs.language,
                "confirmation_required": prefs.confirmation_required
            },
            "message": "Use 'configure <setting> <value>' to update preferences"
        }
    
    def _default_handler(self, message: Message, interaction: Interaction) -> str:
        """Default message handler."""
        return f"Received: {message.content}. Processing your request..."
    
    def _format_for_user(self, response: Any, user_id: str) -> Any:
        """Format response based on user preferences."""
        # Get user preferences
        if user_id in self.user_preferences:
            prefs = self.user_preferences[user_id]
        else:
            prefs = UserPreferences()
        
        # Format based on preference
        if prefs.response_format == ResponseFormat.JSON:
            if isinstance(response, str):
                return json.dumps({"response": response})
            elif isinstance(response, dict):
                return json.dumps(response)
            else:
                return json.dumps({"response": str(response)})
        
        elif prefs.response_format == ResponseFormat.MARKDOWN:
            if isinstance(response, dict):
                # Convert dict to markdown
                lines = ["## Response\n"]
                for key, value in response.items():
                    lines.append(f"**{key}**: {value}")
                return "\n".join(lines)
            else:
                return f"## Response\n\n{response}"
        
        elif prefs.response_format == ResponseFormat.HTML:
            if isinstance(response, dict):
                # Convert dict to HTML
                html = ["<div class='response'>"]
                for key, value in response.items():
                    html.append(f"<p><strong>{key}:</strong> {value}</p>")
                html.append("</div>")
                return "\n".join(html)
            else:
                return f"<p>{response}</p>"
        
        else:  # TEXT or default
            if isinstance(response, dict):
                return "\n".join(f"{k}: {v}" for k, v in response.items())
            else:
                return str(response)
    
    def _send_message(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message."""
        recipient = task.get("recipient", "")
        content = task.get("content", "")
        msg_type = task.get("type", "info")
        
        if not recipient or not content:
            return {"error": "Recipient and content are required"}
        
        self._message_counter += 1
        message = Message(
            id=f"msg_{self._message_counter}",
            type=MessageType[msg_type.upper()],
            content=content,
            sender=self.config.name,
            recipient=recipient
        )
        
        # Add to queue
        self.message_queue.append(message)
        
        # Simulate sending (in real implementation, would use actual transport)
        logger.info(
            "message_sent",
            recipient=recipient,
            type=msg_type,
            message_id=message.id
        )
        
        return {
            "message_id": message.id,
            "sent": True
        }
    
    def _receive_message(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Receive messages."""
        sender_filter = task.get("sender")
        type_filter = task.get("type")
        limit = task.get("limit", 10)
        
        messages = self.message_queue[-limit:]
        
        # Apply filters
        if sender_filter:
            messages = [msg for msg in messages if msg.sender == sender_filter]
        
        if type_filter:
            msg_type = MessageType[type_filter.upper()]
            messages = [msg for msg in messages if msg.type == msg_type]
        
        return {
            "messages": [msg.to_dict() for msg in messages],
            "count": len(messages)
        }
    
    def _format_response(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Format a response."""
        content = task.get("content")
        format_type = task.get("format", "text")
        
        if content is None:
            return {"error": "Content is required"}
        
        try:
            format_enum = ResponseFormat[format_type.upper()]
        except KeyError:
            return {"error": f"Unknown format: {format_type}"}
        
        formatted = self._apply_format(content, format_enum)
        
        return {
            "formatted": formatted,
            "format": format_type
        }
    
    def _apply_format(self, content: Any, format_type: ResponseFormat) -> Any:
        """Apply specific formatting."""
        if format_type == ResponseFormat.JSON:
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return {"content": content}
            else:
                return content
        
        elif format_type == ResponseFormat.MARKDOWN:
            if isinstance(content, list):
                return "\n".join(f"- {item}" for item in content)
            elif isinstance(content, dict):
                lines = []
                for key, value in content.items():
                    lines.append(f"**{key}**")
                    if isinstance(value, list):
                        for item in value:
                            lines.append(f"  - {item}")
                    else:
                        lines.append(f"  {value}")
                return "\n".join(lines)
            else:
                return str(content)
        
        elif format_type == ResponseFormat.STRUCTURED:
            # Return as structured data
            if isinstance(content, str):
                # Try to parse structure
                lines = content.split('\n')
                return {"lines": lines, "raw": content}
            else:
                return content
        
        else:
            return str(content)
    
    def _validate_input(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user input."""
        input_data = task.get("input")
        validation_rules = task.get("rules", {})
        
        if input_data is None:
            return {"error": "Input is required"}
        
        errors = []
        warnings = []
        
        # Apply validation rules
        if "required" in validation_rules:
            for field in validation_rules["required"]:
                if isinstance(input_data, dict) and field not in input_data:
                    errors.append(f"Required field missing: {field}")
        
        if "type" in validation_rules:
            expected_type = validation_rules["type"]
            if not isinstance(input_data, eval(expected_type)):
                errors.append(f"Invalid type: expected {expected_type}")
        
        if "length" in validation_rules:
            if isinstance(input_data, str):
                min_len = validation_rules["length"].get("min", 0)
                max_len = validation_rules["length"].get("max", float('inf'))
                if len(input_data) < min_len:
                    errors.append(f"Input too short: minimum {min_len} characters")
                elif len(input_data) > max_len:
                    errors.append(f"Input too long: maximum {max_len} characters")
        
        if "pattern" in validation_rules:
            import re
            pattern = validation_rules["pattern"]
            if isinstance(input_data, str) and not re.match(pattern, input_data):
                errors.append(f"Input doesn't match required pattern")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _prompt_user(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Prompt user for input."""
        prompt_text = task.get("prompt", "Please enter input:")
        prompt_type = task.get("type", "text")
        options = task.get("options", [])
        default = task.get("default")
        
        # Create prompt message
        self._message_counter += 1
        prompt_msg = Message(
            id=f"msg_{self._message_counter}",
            type=MessageType.PROMPT,
            content={
                "prompt": prompt_text,
                "type": prompt_type,
                "options": options,
                "default": default
            },
            sender=self.config.name,
            recipient="user"
        )
        
        # Add to queue
        self.message_queue.append(prompt_msg)
        
        return {
            "prompt_id": prompt_msg.id,
            "prompt": prompt_text,
            "awaiting_response": True
        }
    
    def _send_notification(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification."""
        recipient = task.get("recipient", "all")
        message = task.get("message", "")
        level = task.get("level", "info")
        
        if not message:
            return {"error": "Message is required"}
        
        # Determine notification type
        if level == "error":
            msg_type = MessageType.ERROR
        elif level == "warning":
            msg_type = MessageType.WARNING
        else:
            msg_type = MessageType.NOTIFICATION
        
        # Create notification
        self._message_counter += 1
        notification = Message(
            id=f"msg_{self._message_counter}",
            type=msg_type,
            content=message,
            sender=self.config.name,
            recipient=recipient,
            metadata={"level": level}
        )
        
        # Add to queue
        self.message_queue.append(notification)
        
        # Log notification
        logger.info(
            "notification_sent",
            recipient=recipient,
            level=level,
            message_id=notification.id
        )
        
        return {
            "notification_id": notification.id,
            "sent": True
        }
    
    def _get_history(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get interaction history."""
        user_id = task.get("user_id")
        interaction_type = task.get("interaction_type")
        limit = task.get("limit", 10)
        
        # Filter interactions
        filtered = []
        for key, interaction in self.interactions.items():
            if user_id and not key.startswith(user_id):
                continue
            if interaction_type and interaction.type.value != interaction_type:
                continue
            filtered.append(interaction)
        
        # Sort by start time
        filtered.sort(key=lambda i: i.started_at, reverse=True)
        
        # Limit results
        filtered = filtered[:limit]
        
        return {
            "interactions": [i.to_dict() for i in filtered],
            "total": len(self.interactions)
        }
    
    def register_handler(self, intent: str, handler: Callable):
        """Register a response handler for specific intent."""
        self.response_handlers[intent] = handler
        logger.info(f"Handler registered for intent: {intent}")
    
    def set_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Set user preferences."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences()
        
        prefs = self.user_preferences[user_id]
        
        # Update preferences
        if "response_format" in preferences:
            prefs.response_format = ResponseFormat[preferences["response_format"].upper()]
        if "verbosity" in preferences:
            prefs.verbosity = preferences["verbosity"]
        if "language" in preferences:
            prefs.language = preferences["language"]
        if "confirmation_required" in preferences:
            prefs.confirmation_required = preferences["confirmation_required"]
        
        logger.info(f"Preferences updated for user: {user_id}")
    
    def shutdown(self) -> bool:
        """Shutdown the interface agent."""
        # End all active interactions
        for interaction in self.interactions.values():
            if interaction.status == "active":
                interaction.end()
        
        logger.info("interface_agent_shutdown", 
                   interactions_count=len(self.interactions),
                   messages_count=len(self.message_queue))
        
        self.interactions.clear()
        self.message_queue.clear()
        self.response_handlers.clear()
        self.user_preferences.clear()
        
        return True