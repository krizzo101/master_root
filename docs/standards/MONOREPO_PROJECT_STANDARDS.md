# Monorepo Project Standards

## Purpose
This document defines mandatory standards for all projects within the OPSVI AI Factory monorepo. These standards ensure consistency, reusability, and maintainability across all AI agent-generated applications.

## Core Philosophy
- **Develop Once, Reuse Everywhere**: Shared functionality goes in `libs/`
- **Over-Modularize**: Many small modules > few large modules
- **Scaffold First, Code Second**: Complete structure before implementation
- **Observability by Default**: Comprehensive logging and tracing built-in

## Directory Structure

### Monorepo Layout
```
master_root/
├── libs/                 # Shared, reusable packages
│   └── opsvi-<name>/    # Package distribution name (hyphens)
│       ├── opsvi_<name>/ # Python module name (underscores)
│       ├── tests/
│       ├── README.md
│       └── pyproject.toml
├── apps/                 # Application implementations
│   └── <app-name>/      # Specific applications
├── projects/            # SDLC-managed projects (temporary)
├── intake/              # Candidates for migration
├── docs/                # Global documentation
└── .proj-intel/         # Project intelligence
```

### New Library Structure (libs/)
```
libs/opsvi-<functionality>/
├── opsvi_<functionality>/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── base.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/
│   ├── README.md
│   ├── API.md
│   └── CHANGELOG.md
├── pyproject.toml
├── README.md
└── LICENSE
```

### New Application Structure (apps/)
```
apps/<app-name>/
├── src/
│   └── <app_name>/      # Note: underscores in module name
│       ├── __init__.py
│       ├── __main__.py  # Entry point for python -m
│       ├── core/        # Core business logic
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   └── processor.py
│       ├── models/      # Data models
│       │   ├── __init__.py
│       │   ├── domain.py
│       │   └── dto.py
│       ├── services/    # Service layer
│       │   ├── __init__.py
│       │   ├── api_service.py
│       │   └── data_service.py
│       ├── api/         # API endpoints (if applicable)
│       │   ├── __init__.py
│       │   ├── routes.py
│       │   └── handlers.py
│       ├── cli/         # CLI interface
│       │   ├── __init__.py
│       │   └── commands.py
│       ├── utils/       # Utilities
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   └── validators.py
│       ├── config/      # Configuration
│       │   ├── __init__.py
│       │   ├── settings.py
│       │   └── constants.py
│       └── app.py       # Main application
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
├── configs/             # External configuration files
│   ├── config.yaml
│   ├── config.dev.yaml
│   ├── config.prod.yaml
│   └── logging.yaml
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── api.md
│   └── deployment.md
├── scripts/             # Utility scripts
│   ├── setup.sh
│   ├── test.sh
│   └── deploy.sh
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── .env.example
```

## Mandatory Requirements

### 1. Module Execution
All applications MUST be executable as modules:
```python
# __main__.py
import sys
from .app import main

if __name__ == "__main__":
    sys.exit(main())
```

Usage: `python -m <app_name> [args]`

### 2. Centralized Configuration
```python
# config/settings.py
from pydantic import BaseSettings, Field
from pathlib import Path

class Settings(BaseSettings):
    """Centralized configuration for the application."""
    
    # Application settings
    app_name: str = Field("my-app", env="APP_NAME")
    app_version: str = Field("0.1.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = Field(None, env="DATA_DIR")
    log_dir: Path = Field(None, env="LOG_DIR")
    
    # API settings
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_key: str = Field(None, env="API_KEY")
    
    # Database
    database_url: str = Field(None, env="DATABASE_URL")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    enable_tracing: bool = Field(True, env="ENABLE_TRACING")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Singleton instance
settings = Settings()
```

### 3. Comprehensive Logging
```python
# utils/logging.py
import logging
import structlog
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor

def setup_logging(
    level: str = "INFO",
    debug: bool = False,
    enable_tracing: bool = True
) -> None:
    """Setup structured logging with OpenTelemetry integration."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.dict_tracebacks,
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.processors.JSONRenderer() if not debug 
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup OpenTelemetry if enabled
    if enable_tracing:
        LoggingInstrumentor().instrument(set_logging_format=True)
        tracer = trace.get_tracer(__name__)
    
    # Set log level
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
```

### 4. CLI with Logging Control
```python
# cli/commands.py
import click
from ..config import settings
from ..utils.logging import setup_logging, get_logger

@click.command()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--log-level', default='INFO', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']))
@click.option('--trace/--no-trace', default=True, 
              help='Enable/disable OpenTelemetry tracing')
def main(debug: bool, log_level: str, trace: bool):
    """Main application entry point."""
    
    # Override settings with CLI flags
    if debug:
        settings.debug = True
        log_level = 'DEBUG'
    
    # Setup logging
    setup_logging(
        level=log_level,
        debug=debug,
        enable_tracing=trace
    )
    
    logger = get_logger(__name__)
    logger.info(
        "Application started",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=debug,
        log_level=log_level,
        tracing_enabled=trace
    )
    
    # Run application
    from ..app import run
    run()
```

### 5. Dependency Management
```toml
# pyproject.toml
[project]
name = "my-app"
version = "0.1.0"
description = "Application description"
requires-python = ">=3.10"
dependencies = [
    # Import from libs/ packages
    "opsvi-core",
    "opsvi-llm",
    "opsvi-mcp",
    # External dependencies
    "pydantic>=2.0",
    "structlog>=23.0",
    "click>=8.0",
    "opentelemetry-api>=1.20",
    "opentelemetry-sdk>=1.20",
    "opentelemetry-instrumentation-logging>=0.41b0",
]

[project.scripts]
my-app = "my_app.cli.commands:main"

[tool.setuptools.packages.find]
where = ["src"]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

## Development Workflow

### 1. Create New App
```bash
# Use SDLC enforcer
python libs/opsvi-mcp/tools/sdlc_enforcer_scoped.py create_project \
    project_name "My App" \
    root_path "apps/my-app"
```

### 2. Scaffold Structure
Before writing ANY code:
1. Create complete directory structure
2. Create all empty module files with docstrings
3. Define interfaces and contracts
4. Setup configuration
5. Setup logging
6. Create test structure

### 3. Shared vs. App-Specific Code
Decision tree:
```
Is this functionality reusable by other apps?
├── YES → Develop in libs/opsvi-<functionality>/
│   └── Import into app
└── NO → Develop in apps/<app-name>/src/
```

### 4. Import Shared Libraries
```python
# In app code
from opsvi_core import BaseService
from opsvi_llm import LLMClient
from opsvi_mcp.tools import sdlc_enforcer
```

## Testing Standards

### Test Structure
```
tests/
├── unit/           # Unit tests (mock all dependencies)
├── integration/    # Integration tests (real dependencies)
├── e2e/           # End-to-end tests (full system)
└── fixtures/      # Test data and fixtures
```

### Coverage Requirements
- Minimum 80% code coverage
- 100% coverage for core business logic
- All error paths must be tested

## Documentation Standards

### Required Documentation
1. **README.md** - Project overview, quickstart, basic usage
2. **architecture.md** - System design, component interaction
3. **api.md** - API documentation (if applicable)
4. **deployment.md** - Deployment instructions
5. **CHANGELOG.md** - Version history

### Docstring Standards
```python
def process_data(
    data: Dict[str, Any],
    validate: bool = True
) -> ProcessedResult:
    """Process input data according to business rules.
    
    Args:
        data: Input data dictionary containing required fields
        validate: Whether to validate input data
        
    Returns:
        ProcessedResult object containing transformed data
        
    Raises:
        ValidationError: If validation is enabled and data is invalid
        ProcessingError: If data processing fails
        
    Example:
        >>> result = process_data({"key": "value"})
        >>> print(result.status)
        'success'
    """
```

## Observability Standards

### Metrics to Track
- Request/response times
- Error rates and types
- Resource utilization
- Business metrics specific to app

### Tracing Requirements
- Trace all external API calls
- Trace database operations
- Trace critical business operations
- Include correlation IDs

### Logging Levels
- **DEBUG**: Detailed diagnostic info
- **INFO**: General operational events
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical failures

## Security Standards

### Configuration Security
- Never hardcode secrets
- Use environment variables
- Provide .env.example (no real values)
- Use secret management service in production

### Input Validation
- Validate all inputs
- Sanitize user data
- Use parameterized queries
- Implement rate limiting

## Migration Path

### For Existing Projects in intake/
1. Evaluate against these standards
2. Create migration plan
3. Refactor to match structure
4. Move shared code to libs/
5. Move app to apps/
6. Update imports and dependencies

### For Active Tools (Currently Symlinked)
1. Create feature branch
2. Refactor incrementally
3. Test thoroughly
4. Update symlinks last
5. Gradual cutover

## Enforcement

### Automated Checks
- Pre-commit hooks for structure validation
- CI/CD pipeline checks
- Test coverage enforcement
- Documentation linting

### Manual Review
- Architecture review for new apps
- Code review for shared libraries
- Security review for external APIs

## Quick Checklist for New Apps

- [ ] Created with SDLC enforcer
- [ ] Complete directory structure scaffolded
- [ ] Centralized configuration implemented
- [ ] Logging with debug flag setup
- [ ] Executable as module (python -m)
- [ ] Shared code identified and placed in libs/
- [ ] Tests structure created
- [ ] Documentation templates created
- [ ] Observability instrumentation added
- [ ] Security considerations documented

---

**Remember**: Over-modularize during scaffolding. It's easier to merge small modules later than to split large ones.