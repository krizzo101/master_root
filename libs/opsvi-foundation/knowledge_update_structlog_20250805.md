# Knowledge Update: Structlog (Generated 2025-08-05)

## Current State (2025)

Structlog is the production-ready structured logging solution for Python with significant 2025 improvements:
- **Performance**: Optimized processor chains, caching mechanisms, and filtering loggers
- **Integration**: Enhanced standard library logging integration with async support
- **Modern Features**: Context variables, structured tracebacks, type hints
- **JSON Rendering**: Fast JSON serialization with orjson support
- **Processor Chain**: Flexible processor-based architecture
- **Testing Support**: Comprehensive testing utilities with capture_logs
- **Production Ready**: Used in production at every scale since 2013

## Best Practices & Patterns

### Modern Installation and Setup (2025)
```python
# Install with optional dependencies for performance
pip install -U structlog[orjson]

# For development with rich console output
pip install -U structlog[rich]
```

### Fast Production Configuration (2025)
```python
import logging
import orjson
import structlog

# Optimized production configuration
structlog.configure(
    cache_logger_on_first_use=True,
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(serializer=orjson.dumps),
    ],
    logger_factory=structlog.BytesLoggerFactory(),
)

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)
```

### Development vs Production Configuration (2025)
```python
import sys
import structlog

shared_processors = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
]

if sys.stderr.isatty():
    # Development: Pretty console output with rich
    processors = shared_processors + [
        structlog.dev.ConsoleRenderer(colors=True),
    ]
else:
    # Production: JSON output with structured tracebacks
    processors = shared_processors + [
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ]

structlog.configure(processors=processors)
```

### Advanced Configuration with ProcessorFormatter (2025)
```python
import logging
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Create formatter with custom processors
formatter = structlog.stdlib.ProcessorFormatter(
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    foreign_pre_chain=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
    ],
)

# Set up handler
handler = logging.StreamHandler()
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)
```

### Advanced JSON Configuration (2025)
```python
import structlog

structlog.configure(
    processors=[
        # Filter by level early for performance
        structlog.stdlib.filter_by_level,
        # Add logger name and level
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        # Format positional arguments
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add stack info
        structlog.processors.StackInfoRenderer(),
        # Format exceptions
        structlog.processors.format_exc_info,
        # Decode Unicode
        structlog.processors.UnicodeDecoder(),
        # Add callsite parameters
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        # Render as JSON
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## Tools & Frameworks

### Core Components
- **BoundLogger**: Main logger interface with context binding
- **LoggerFactory**: Creates underlying loggers
- **Processors**: Chain of functions that transform log events
- **Renderers**: Convert event dictionaries to output format

### Standard Library Integration
- **structlog.stdlib.LoggerFactory**: Creates standard library loggers
- **structlog.stdlib.BoundLogger**: Bound logger compatible with stdlib
- **structlog.stdlib.ProcessorFormatter**: Formatter for stdlib integration
- **structlog.stdlib.filter_by_level**: Level-based filtering

### Processors
- **add_log_level**: Adds log level to event dict
- **add_logger_name**: Adds logger name to event dict
- **TimeStamper**: Adds timestamps to events
- **StackInfoRenderer**: Adds stack information
- **format_exc_info**: Formats exception information
- **JSONRenderer**: Renders events as JSON
- **ConsoleRenderer**: Pretty console output
- **KeyValueRenderer**: Key-value pair output
- **dict_tracebacks**: Structured traceback formatting

### Performance Optimizations (2025)
```python
import orjson
import structlog

# Fast production configuration
structlog.configure(
    cache_logger_on_first_use=True,
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer(serializer=orjson.dumps),
    ],
    logger_factory=structlog.BytesLoggerFactory(),
)

# Local binding for high-frequency logging
logger = structlog.get_logger()
def f():
    log = logger.bind()
    for i in range(1000000000):
       log.info("iterated", i=i)
```

## Implementation Guidance

### For OPSVI Core Library (2025)
```python
import structlog
import logging
import sys
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "json"
    include_timestamp: bool = True
    include_process: bool = True
    include_thread: bool = True
    cache_loggers: bool = True
    enable_colors: bool = False

def setup_logging(config: LoggingConfig) -> None:
    """Setup structured logging for OPSVI applications."""

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.level.upper()),
    )

    # Build processor chain
    processors = []

    # Add level filtering
    processors.append(structlog.stdlib.filter_by_level)

    # Add context variables
    processors.append(structlog.contextvars.merge_contextvars)

    # Add log level and logger name
    processors.append(structlog.stdlib.add_log_level)
    processors.append(structlog.stdlib.add_logger_name)

    # Add timestamp
    if config.include_timestamp:
        processors.append(structlog.processors.TimeStamper(fmt="iso", utc=True))

    # Add process/thread info
    if config.include_process or config.include_thread:
        callsite_params = []
        if config.include_process:
            callsite_params.append(structlog.processors.CallsiteParameter.PROCESS_NAME)
        if config.include_thread:
            callsite_params.append(structlog.processors.CallsiteParameter.THREAD_NAME)

        processors.append(
            structlog.processors.CallsiteParameterAdder(callsite_params)
        )

    # Add stack info and exception formatting
    processors.append(structlog.processors.StackInfoRenderer())
    processors.append(structlog.processors.format_exc_info)

    # Add Unicode decoding
    processors.append(structlog.processors.UnicodeDecoder())

    # Add output renderer
    if config.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=config.enable_colors))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=config.cache_loggers,
    )

def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

# Enhanced logger with context binding
class OPSVILogger:
    def __init__(self, name: str):
        self.logger = get_logger(name)

    def bind_context(self, **kwargs) -> structlog.BoundLogger:
        """Bind context variables to logger."""
        return self.logger.bind(**kwargs)

    def log_event(self, event: str, level: str = "info", **kwargs) -> None:
        """Log an event with structured data."""
        log_method = getattr(self.logger, level.lower())
        log_method(event, **kwargs)

    def log_error(self, event: str, error: Exception, **kwargs) -> None:
        """Log an error with exception information."""
        self.logger.exception(event, error=str(error), **kwargs)

    async def log_event_async(self, event: str, level: str = "info", **kwargs) -> None:
        """Log an event asynchronously."""
        log_method = getattr(self.logger, f"a{level.lower()}")
        await log_method(event, **kwargs)
```

### For RAG Library (2025)
```python
import structlog
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class DocumentProcessEvent:
    doc_id: str
    content_length: int
    processing_time: float
    embedding_dim: Optional[int] = None

@dataclass
class SearchEvent:
    query: str
    results_count: int
    search_time: float
    collection_name: str

class RAGLogger:
    def __init__(self, name: str = "opsvi_rag"):
        self.logger = structlog.get_logger(name)

    def log_document_processed(self, event: DocumentProcessEvent, **kwargs) -> None:
        """Log document processing event."""
        self.logger.info(
            "Document processed",
            doc_id=event.doc_id,
            content_length=event.content_length,
            processing_time=event.processing_time,
            embedding_dim=event.embedding_dim,
            **kwargs
        )

    def log_embedding_created(self, doc_id: str, embedding_dim: int, **kwargs) -> None:
        """Log embedding creation event."""
        self.logger.info(
            "Embedding created",
            doc_id=doc_id,
            embedding_dim=embedding_dim,
            **kwargs
        )

    def log_search_performed(self, event: SearchEvent, **kwargs) -> None:
        """Log search event."""
        self.logger.info(
            "Search performed",
            query=event.query,
            results_count=event.results_count,
            search_time=event.search_time,
            collection_name=event.collection_name,
            **kwargs
        )

    def log_collection_operation(self, operation: str, collection_name: str, **kwargs) -> None:
        """Log collection operation."""
        self.logger.info(
            "Collection operation",
            operation=operation,
            collection_name=collection_name,
            **kwargs
        )

    async def log_search_async(self, event: SearchEvent, **kwargs) -> None:
        """Log search event asynchronously."""
        await self.logger.ainfo(
            "Search performed",
            query=event.query,
            results_count=event.results_count,
            search_time=event.search_time,
            collection_name=event.collection_name,
            **kwargs
        )
```

### For LLM Library (2025)
```python
import structlog
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ModelCallEvent:
    model: str
    messages_count: int
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None

@dataclass
class FunctionCallEvent:
    model: str
    function_name: str
    arguments: Dict[str, Any]
    response_time: Optional[float] = None

class LLMLogger:
    def __init__(self, name: str = "opsvi_llm"):
        self.logger = structlog.get_logger(name)

    def log_model_call(self, event: ModelCallEvent, **kwargs) -> None:
        """Log LLM model call."""
        self.logger.info(
            "Model call",
            model=event.model,
            messages_count=event.messages_count,
            tokens_used=event.tokens_used,
            response_time=event.response_time,
            **kwargs
        )

    def log_function_call(self, event: FunctionCallEvent, **kwargs) -> None:
        """Log function calling event."""
        self.logger.info(
            "Function call",
            model=event.model,
            function_name=event.function_name,
            arguments=event.arguments,
            response_time=event.response_time,
            **kwargs
        )

    def log_response_received(self, model: str, response_length: int, **kwargs) -> None:
        """Log response received."""
        self.logger.info(
            "Response received",
            model=model,
            response_length=response_length,
            **kwargs
        )

    def log_error(self, model: str, error_type: str, error_message: str, **kwargs) -> None:
        """Log LLM error."""
        self.logger.error(
            "LLM error",
            model=model,
            error_type=error_type,
            error_message=error_message,
            **kwargs
        )

    async def log_model_call_async(self, event: ModelCallEvent, **kwargs) -> None:
        """Log LLM model call asynchronously."""
        await self.logger.ainfo(
            "Model call",
            model=event.model,
            messages_count=event.messages_count,
            tokens_used=event.tokens_used,
            response_time=event.response_time,
            **kwargs
        )
```

### For Agent Framework (2025)
```python
import structlog
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentEvent:
    agent_type: str
    agent_id: str
    task_name: Optional[str] = None
    execution_time: Optional[float] = None

@dataclass
class CrewEvent:
    crew_id: str
    agent_count: int
    workflow_name: Optional[str] = None

class AgentLogger:
    def __init__(self, name: str = "opsvi_agents"):
        self.logger = structlog.get_logger(name)

    def log_agent_started(self, event: AgentEvent, **kwargs) -> None:
        """Log agent startup."""
        self.logger.info(
            "Agent started",
            agent_type=event.agent_type,
            agent_id=event.agent_id,
            **kwargs
        )

    def log_task_executed(self, event: AgentEvent, **kwargs) -> None:
        """Log task execution."""
        self.logger.info(
            "Task executed",
            agent_id=event.agent_id,
            task_name=event.task_name,
            execution_time=event.execution_time,
            **kwargs
        )

    def log_crew_created(self, event: CrewEvent, **kwargs) -> None:
        """Log crew creation."""
        self.logger.info(
            "Crew created",
            crew_id=event.crew_id,
            agent_count=event.agent_count,
            workflow_name=event.workflow_name,
            **kwargs
        )

    def log_workflow_step(self, workflow_id: str, step_name: str, **kwargs) -> None:
        """Log workflow step."""
        self.logger.info(
            "Workflow step",
            workflow_id=workflow_id,
            step_name=step_name,
            **kwargs
        )

    async def log_agent_started_async(self, event: AgentEvent, **kwargs) -> None:
        """Log agent startup asynchronously."""
        await self.logger.ainfo(
            "Agent started",
            agent_type=event.agent_type,
            agent_id=event.agent_id,
            **kwargs
        )
```

### Production-Ready Logging Service (2025)
```python
import asyncio
import structlog
from typing import Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class LogRequest:
    level: str
    event: str
    context: Dict[str, Any]
    logger_name: Optional[str] = None

@dataclass
class LogResponse:
    success: bool
    message: str
    timestamp: str

class ProductionLoggingService:
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=4)
        setup_logging(config)
        self.logger = structlog.get_logger("logging_service")

    async def log_async(self, request: LogRequest) -> LogResponse:
        """Log asynchronously using thread pool."""
        try:
            logger = structlog.get_logger(request.logger_name or "default")
            log_method = getattr(logger, f"a{request.level.lower()}")

            # Run in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: log_method(request.event, **request.context)
            )

            return LogResponse(
                success=True,
                message="Log entry recorded successfully",
                timestamp=structlog.processors.TimeStamper(fmt="iso", utc=True)(None, "", {})["timestamp"]
            )
        except Exception as e:
            self.logger.error("Failed to log entry", error=str(e), request=request)
            return LogResponse(
                success=False,
                message=f"Failed to log entry: {str(e)}",
                timestamp=structlog.processors.TimeStamper(fmt="iso", utc=True)(None, "", {})["timestamp"]
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get logging service metrics."""
        return {
            "service": "production_logging",
            "version": "2025.1.0",
            "status": "healthy",
            "thread_pool_size": self.executor._max_workers,
            "active_threads": len(self.executor._threads),
        }

    def health_check(self) -> bool:
        """Health check for the logging service."""
        try:
            self.logger.info("Health check", service="production_logging")
            return True
        except Exception:
            return False

    async def shutdown(self) -> None:
        """Shutdown the logging service."""
        self.logger.info("Shutting down logging service")
        self.executor.shutdown(wait=True)
```

## Testing Support (2025)

### Testing Configuration
```python
import structlog
from structlog.testing import capture_logs

# Configure for testing
structlog.configure(
    processors=[structlog.processors.JSONRenderer()],
    logger_factory=structlog.PrintLoggerFactory(),
)

# Capture logs in tests
def test_logging():
    with capture_logs() as cap_logs:
        logger = structlog.get_logger()
        logger.info("test message", key="value")

    assert len(cap_logs) == 1
    assert cap_logs[0]["event"] == "test message"
    assert cap_logs[0]["key"] == "value"
```

### Performance Testing
```python
import time
import structlog

def benchmark_logging():
    logger = structlog.get_logger()

    start_time = time.time()
    for i in range(10000):
        logger.info("benchmark", iteration=i)

    end_time = time.time()
    print(f"Logged 10000 entries in {end_time - start_time:.2f} seconds")
```

## Limitations & Considerations

### Performance
- **Processor Chain**: Each processor adds overhead
- **JSON Serialization**: Can be expensive for large objects
- **Context Binding**: Repeated binding can impact performance
- **Logger Caching**: Enable caching for better performance

### Memory Usage
- **Event Dictionaries**: Can accumulate in memory
- **Context Variables**: Bound context persists until unbind
- **Exception Handling**: Large tracebacks can consume memory

### Configuration Complexity
- **Processor Order**: Order matters in processor chain
- **Integration**: Standard library integration can be complex
- **Testing**: Requires special configuration for testing

### Best Practices (2025)
- **Use Appropriate Renderers**: JSON for production, console for development
- **Enable Caching**: Use cache_logger_on_first_use=True
- **Filter Early**: Use filter_by_level at the start of processor chain
- **Handle Exceptions**: Use format_exc_info for proper exception logging
- **Context Management**: Use bind/unbind for context variables
- **Testing**: Use capture_logs for testing
- **Async Support**: Use a* methods for non-blocking logging
- **Performance**: Use local binding for high-frequency logging
- **Structured Data**: Use dataclasses for consistent log events

## Integration with OPSVI

### Configuration Management
- Use environment-based configuration
- Support both development and production modes
- Enable performance optimizations in production
- Provide consistent logging across all libraries

### Error Handling
- Structured error logging with context
- Exception formatting with tracebacks
- Error categorization and severity levels
- Integration with monitoring systems

### Performance Monitoring
- Log performance metrics
- Track operation durations
- Monitor resource usage
- Alert on performance issues

### Security
- Sanitize sensitive data in logs
- Use appropriate log levels
- Implement log rotation
- Secure log storage and transmission

### Modern Features (2025)
- **Context Variables**: Thread-safe context management
- **Async Logging**: Non-blocking log operations
- **Structured Tracebacks**: JSON-formatted exception data
- **Type Hints**: Full type annotation support
- **Performance**: Optimized filtering and caching
- **Testing**: Comprehensive testing utilities
- **Integration**: Seamless stdlib and framework integration