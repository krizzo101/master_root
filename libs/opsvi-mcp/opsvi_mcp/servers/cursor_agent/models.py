"""
Data models for Cursor Agent MCP Server
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class AgentType(str, Enum):
    """Types of Cursor agents"""

    DIAGRAM = "@diagram"
    CODE_REVIEW = "@code_review"
    DOCUMENTATION = "@documentation"
    TEST = "@test"
    REFACTOR = "@refactor"
    CUSTOM = "@custom"


class DiagramType(str, Enum):
    """Types of diagrams for @diagram agent"""

    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"
    ERD = "erd"
    GANTT = "gantt"
    MINDMAP = "mindmap"
    C4 = "c4"
    AUTO = "auto"


class CommunicationMethod(str, Enum):
    """Communication methods with Cursor"""

    WEBSOCKET = "websocket"
    FILE = "file"
    PIPE = "pipe"
    CLI = "cli"


class CursorAgent(BaseModel):
    """Cursor agent definition"""

    name: str = Field(description="Agent name (e.g., @diagram)")
    type: AgentType = Field(description="Agent type")
    description: str = Field(description="Agent description")
    capabilities: List[str] = Field(
        default_factory=list, description="Agent capabilities"
    )
    custom_prompt: Optional[str] = Field(
        default=None, description="Custom prompt for agent"
    )
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific config"
    )


class AgentRequest(BaseModel):
    """Request to invoke a Cursor agent"""

    agent: str = Field(description="Agent to invoke (e.g., @diagram)")
    prompt: str = Field(description="Prompt for the agent")
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context"
    )
    files: Optional[List[str]] = Field(
        default=None, description="Files to include as context"
    )
    workspace: Optional[str] = Field(default=None, description="Workspace directory")
    timeout: Optional[int] = Field(default=None, description="Timeout in seconds")

    # Diagram-specific options
    diagram_type: Optional[DiagramType] = Field(
        default=None, description="Type of diagram"
    )
    diagram_theme: Optional[str] = Field(default=None, description="Diagram theme")

    # Output options
    output_format: Optional[str] = Field(default=None, description="Output format")
    inline_render: bool = Field(default=True, description="Render inline if possible")

    # Metadata
    request_id: Optional[str] = Field(default=None, description="Unique request ID")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class AgentResponse(BaseModel):
    """Response from a Cursor agent invocation"""

    success: bool = Field(description="Whether the invocation succeeded")
    agent: str = Field(description="Agent that was invoked")
    result: Optional[str] = Field(default=None, description="Agent output")
    rendered_output: Optional[str] = Field(
        default=None, description="Rendered output (e.g., SVG)"
    )
    artifacts: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Generated artifacts"
    )
    execution_time: float = Field(default=0.0, description="Execution time in seconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    # For async operations
    job_id: Optional[str] = Field(
        default=None, description="Job ID for async operations"
    )
    status: Optional[str] = Field(default=None, description="Job status")

    # Metadata
    request_id: Optional[str] = Field(default=None, description="Original request ID")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


class DiagramRequest(BaseModel):
    """Specialized request for @diagram agent"""

    data: Union[str, Dict, List] = Field(description="Data to visualize")
    diagram_type: DiagramType = Field(
        default=DiagramType.AUTO, description="Diagram type"
    )
    title: Optional[str] = Field(default=None, description="Diagram title")
    theme: str = Field(default="high-contrast", description="Visual theme")
    options: Dict[str, Any] = Field(default_factory=dict, description="Diagram options")

    # Accessibility options
    alt_text: Optional[str] = Field(default=None, description="Alternative text")
    color_blind_safe: bool = Field(
        default=True, description="Use color-blind safe palette"
    )
    high_contrast: bool = Field(default=True, description="Use high contrast")

    # Output options
    format: str = Field(
        default="mermaid", description="Output format (mermaid, svg, png)"
    )
    width: Optional[int] = Field(default=None, description="Diagram width")
    height: Optional[int] = Field(default=None, description="Diagram height")


class AgentJob(BaseModel):
    """Job tracking for async agent operations"""

    job_id: str = Field(description="Unique job identifier")
    agent: str = Field(description="Agent being invoked")
    status: str = Field(default="pending", description="Job status")
    request: AgentRequest = Field(description="Original request")
    response: Optional[AgentResponse] = Field(
        default=None, description="Response when complete"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Job creation time"
    )
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion time"
    )
    output_file: Optional[str] = Field(default=None, description="Output file path")
    error: Optional[str] = Field(default=None, description="Error if job failed")


class AgentCapability(BaseModel):
    """Agent capability definition"""

    name: str = Field(description="Capability name")
    description: str = Field(description="Capability description")
    input_schema: Optional[Dict[str, Any]] = Field(
        default=None, description="Expected input schema"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None, description="Expected output schema"
    )
    examples: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Usage examples"
    )
