"""Configuration for Simple Python MCP Server."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class SimpleConfig(BaseModel):
    """Configuration for Simple Python MCP Server."""
    
    # Server settings
    server_name: str = Field(
        default="simple_python",
        description="Name of the MCP server"
    )
    version: str = Field(
        default="1.0.0",
        description="Server version"
    )
    
    # Execution settings
    timeout: int = Field(
        default=30,
        description="Default timeout for Python execution in seconds"
    )
    max_output_size: int = Field(
        default=1000000,
        description="Maximum output size in bytes"
    )
    
    # Security settings
    allow_imports: bool = Field(
        default=True,
        description="Allow import statements in executed code"
    )
    restricted_modules: list[str] = Field(
        default_factory=lambda: ["os", "sys", "subprocess", "eval", "exec", "__import__"],
        description="List of restricted Python modules"
    )
    
    # Sandbox settings
    use_sandbox: bool = Field(
        default=True,
        description="Execute code in a sandboxed environment"
    )
    sandbox_memory_limit: Optional[int] = Field(
        default=512 * 1024 * 1024,  # 512MB
        description="Memory limit for sandboxed execution in bytes"
    )
    
    # Logging settings
    log_executions: bool = Field(
        default=True,
        description="Log all code executions"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    # Advanced settings
    enable_matplotlib: bool = Field(
        default=True,
        description="Enable matplotlib for plotting"
    )
    enable_numpy: bool = Field(
        default=True,
        description="Enable numpy for numerical operations"
    )
    enable_pandas: bool = Field(
        default=True,
        description="Enable pandas for data manipulation"
    )
    
    # Custom context
    custom_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom variables to inject into execution context"
    )
    
    class Config:
        """Pydantic config."""
        validate_assignment = True
        extra = "forbid"