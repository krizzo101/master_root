"""
Data models for Gemini Agent MCP Server
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class GeminiMode(Enum):
    """Execution modes for Gemini agent"""
    
    CHAT = "chat"  # Interactive chat mode
    CODE = "code"  # Code generation mode
    ANALYZE = "analyze"  # Code analysis mode
    DEBUG = "debug"  # Debugging mode
    TEST = "test"  # Test generation mode
    DOCUMENT = "document"  # Documentation mode
    REFACTOR = "refactor"  # Code refactoring mode
    REVIEW = "review"  # Code review mode
    SEARCH = "search"  # Search and research mode
    REACT = "react"  # ReAct loop mode (default)


class GeminiCapabilities(Enum):
    """Capabilities of Gemini agent"""
    
    WEB_SEARCH = "web_search"
    FILE_OPERATIONS = "file_operations"
    SHELL_COMMANDS = "shell_commands"
    MCP_SERVERS = "mcp_servers"
    GOOGLE_CLOUD = "google_cloud"
    GITHUB_INTEGRATION = "github_integration"
    LARGE_CONTEXT = "large_context"  # 1M tokens
    REACT_LOOP = "react_loop"


@dataclass
class GeminiRequest:
    """Request to Gemini agent"""
    
    task: str
    mode: GeminiMode = GeminiMode.REACT
    context_files: List[str] = field(default_factory=list)
    working_directory: Optional[str] = None
    timeout: int = 300
    max_iterations: int = 10
    enable_web_search: bool = True
    enable_file_ops: bool = True
    enable_shell: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_cli_prompt(self) -> str:
        """Convert request to CLI prompt"""
        prompt = self.task
        
        if self.context_files:
            prompt += f"\n\nContext files: {', '.join(self.context_files)}"
        
        if self.mode != GeminiMode.REACT:
            prompt += f"\n\nMode: {self.mode.value}"
        
        return prompt


@dataclass
class GeminiResponse:
    """Response from Gemini agent"""
    
    request_id: str
    status: str  # 'success', 'failure', 'timeout', 'partial'
    mode: GeminiMode
    output: str
    reasoning_steps: List[str] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    commands_executed: List[str] = field(default_factory=list)
    web_searches: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    tokens_used: int = 0
    cost_estimate: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GeminiTask:
    """Internal task representation"""
    
    id: str
    request: GeminiRequest
    status: str = "pending"  # pending, running, completed, failed
    process_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output_file: Optional[str] = None
    error_file: Optional[str] = None
    
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class GeminiMetrics:
    """Metrics for Gemini agent usage"""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_response_time_ms: float = 0.0
    requests_today: int = 0
    requests_this_minute: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests