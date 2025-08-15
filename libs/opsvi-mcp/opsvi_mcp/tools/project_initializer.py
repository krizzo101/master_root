#!/usr/bin/env python3
"""
Project Initializer - Creates standardized project structure for the monorepo
Enforces all monorepo standards automatically
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import textwrap

class ProjectInitializer:
    """Initialize new projects with monorepo standards."""
    
    def __init__(self, workspace_root: str = "/home/opsvi/master_root"):
        self.workspace = Path(workspace_root)
        self.apps_dir = self.workspace / "apps"
        self.libs_dir = self.workspace / "libs"
        
    def create_app(
        self,
        app_name: str,
        description: str,
        author: str = "OPSVI Team",
        python_version: str = ">=3.10"
    ) -> Dict[str, Any]:
        """Create a new application with full standard structure."""
        
        # Sanitize name for directory (hyphens) and module (underscores)
        dir_name = app_name.lower().replace(" ", "-").replace("_", "-")
        module_name = dir_name.replace("-", "_")
        
        app_path = self.apps_dir / dir_name
        
        if app_path.exists():
            return {
                "status": "error",
                "message": f"App {dir_name} already exists"
            }
        
        # Create directory structure
        self._create_app_structure(app_path, module_name)
        
        # Create configuration files
        self._create_app_config(app_path, module_name, description, author, python_version)
        
        # Create source files
        self._create_app_source(app_path, module_name, description)
        
        # Create test structure
        self._create_app_tests(app_path, module_name)
        
        # Create documentation
        self._create_app_docs(app_path, app_name, description)
        
        return {
            "status": "success",
            "message": f"App '{app_name}' created successfully",
            "path": str(app_path),
            "module_name": module_name,
            "next_steps": [
                f"cd {app_path}",
                "python -m venv .venv",
                "source .venv/bin/activate",
                "pip install -e .",
                f"python -m {module_name} --help"
            ]
        }
    
    def create_library(
        self,
        lib_name: str,
        description: str,
        author: str = "OPSVI Team"
    ) -> Dict[str, Any]:
        """Create a new shared library with standard structure."""
        
        # Ensure opsvi- prefix
        if not lib_name.startswith("opsvi-"):
            lib_name = f"opsvi-{lib_name}"
        
        # Directory name (hyphens) and module name (underscores)
        dir_name = lib_name.lower()
        module_name = dir_name.replace("-", "_")
        
        lib_path = self.libs_dir / dir_name
        
        if lib_path.exists():
            return {
                "status": "error",
                "message": f"Library {dir_name} already exists"
            }
        
        # Create directory structure
        self._create_lib_structure(lib_path, module_name)
        
        # Create configuration files
        self._create_lib_config(lib_path, module_name, description, author)
        
        # Create source files
        self._create_lib_source(lib_path, module_name, description)
        
        # Create test structure
        self._create_lib_tests(lib_path, module_name)
        
        return {
            "status": "success",
            "message": f"Library '{lib_name}' created successfully",
            "path": str(lib_path),
            "module_name": module_name,
            "import_as": module_name
        }
    
    def _create_app_structure(self, app_path: Path, module_name: str):
        """Create application directory structure."""
        
        # Main directories
        directories = [
            app_path / "src" / module_name,
            app_path / "src" / module_name / "core",
            app_path / "src" / module_name / "models",
            app_path / "src" / module_name / "services",
            app_path / "src" / module_name / "api",
            app_path / "src" / module_name / "cli",
            app_path / "src" / module_name / "utils",
            app_path / "src" / module_name / "config",
            app_path / "tests" / "unit",
            app_path / "tests" / "integration",
            app_path / "tests" / "e2e",
            app_path / "tests" / "fixtures",
            app_path / "configs",
            app_path / "docs",
            app_path / "scripts",
            app_path / "docker"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            if "src" in directory.parts or "tests" in directory.parts:
                if not directory.name in ["configs", "docs", "scripts", "docker", "fixtures"]:
                    (directory / "__init__.py").touch()
    
    def _create_app_config(
        self, 
        app_path: Path, 
        module_name: str, 
        description: str,
        author: str,
        python_version: str
    ):
        """Create application configuration files."""
        
        # pyproject.toml
        pyproject_content = f'''[project]
name = "{module_name}"
version = "0.1.0"
description = "{description}"
authors = [{{name = "{author}"}}]
requires-python = "{python_version}"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "structlog>=23.0",
    "click>=8.0",
    "python-dotenv>=1.0",
    "opentelemetry-api>=1.20",
    "opentelemetry-sdk>=1.20",
    "opentelemetry-instrumentation-logging>=0.41b0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.21",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[project.scripts]
{module_name} = "{module_name}.cli.commands:main"

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
'''
        (app_path / "pyproject.toml").write_text(pyproject_content)
        
        # .env.example
        env_example = f'''# {module_name.upper()} Configuration

# Application
APP_NAME={module_name}
APP_VERSION=0.1.0
DEBUG=false

# Paths
DATA_DIR=./data
LOG_DIR=./logs

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-api-key-here

# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_TRACING=true

# External Services
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
'''
        (app_path / ".env.example").write_text(env_example)
        
        # configs/config.yaml
        config_yaml = f'''# Default configuration for {module_name}

app:
  name: {module_name}
  version: 0.1.0
  debug: false

logging:
  level: INFO
  format: json
  enable_tracing: true
  
api:
  host: 0.0.0.0
  port: 8000
  
paths:
  data: ./data
  logs: ./logs
  cache: ./cache
'''
        (app_path / "configs" / "config.yaml").write_text(config_yaml)
        
        # .gitignore
        gitignore = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.coverage
htmlcov/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Environment
.env
.env.local

# Application
logs/
data/
cache/
*.log

# OS
.DS_Store
Thumbs.db
'''
        (app_path / ".gitignore").write_text(gitignore)
    
    def _create_app_source(self, app_path: Path, module_name: str, description: str):
        """Create application source files."""
        
        src_path = app_path / "src" / module_name
        
        # __init__.py
        init_content = f'''"""
{description}
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"

from .app import Application

__all__ = ["Application"]
'''
        (src_path / "__init__.py").write_text(init_content)
        
        # __main__.py
        main_content = '''"""Entry point for module execution."""

import sys
from .cli.commands import main

if __name__ == "__main__":
    sys.exit(main())
'''
        (src_path / "__main__.py").write_text(main_content)
        
        # config/settings.py
        settings_content = '''"""Centralized configuration management."""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="app", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent.parent
    data_dir: Optional[Path] = Field(default=None, alias="DATA_DIR")
    log_dir: Optional[Path] = Field(default=None, alias="LOG_DIR")
    
    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_key: Optional[str] = Field(default=None, alias="API_KEY")
    
    # Database
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    enable_tracing: bool = Field(default=True, alias="ENABLE_TRACING")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Setup default paths if not provided
        if not self.data_dir:
            self.data_dir = self.base_dir / "data"
        if not self.log_dir:
            self.log_dir = self.base_dir / "logs"
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
'''
        (src_path / "config" / "settings.py").write_text(settings_content)
        
        # utils/logging.py
        logging_content = '''"""Logging configuration with observability support."""

import logging
import sys
from pathlib import Path
from typing import Optional

import structlog
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor


def setup_logging(
    level: str = "INFO",
    debug: bool = False,
    enable_tracing: bool = True,
    log_file: Optional[Path] = None
) -> None:
    """Configure structured logging with OpenTelemetry integration.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        debug: Enable debug mode with console output
        enable_tracing: Enable OpenTelemetry tracing
        log_file: Optional log file path
    """
    
    # Configure processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add call site info in debug mode
    if debug:
        processors.append(
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            )
        )
    
    # Choose renderer based on debug mode
    if debug:
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup standard logging
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        handlers=handlers,
    )
    
    # Setup OpenTelemetry if enabled
    if enable_tracing:
        LoggingInstrumentor().instrument(set_logging_format=True)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)
'''
        (src_path / "utils" / "logging.py").write_text(logging_content)
        
        # cli/commands.py
        cli_content = f'''"""Command-line interface."""

import sys
import click
from pathlib import Path

from ..config.settings import settings
from ..utils.logging import setup_logging, get_logger
from ..app import Application


@click.command()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Set log level"
)
@click.option(
    "--trace/--no-trace",
    default=True,
    help="Enable/disable OpenTelemetry tracing"
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.version_option(version=settings.app_version)
def main(
    debug: bool,
    log_level: str,
    trace: bool,
    config: Optional[str]
) -> int:
    """
    {module_name} - {description}
    """
    
    # Override settings with CLI flags
    if debug:
        settings.debug = True
        log_level = "DEBUG"
    
    # Setup logging
    log_file = settings.log_dir / f"{{settings.app_name}}.log"
    setup_logging(
        level=log_level,
        debug=debug,
        enable_tracing=trace,
        log_file=log_file if not debug else None
    )
    
    logger = get_logger(__name__)
    logger.info(
        "Application starting",
        app_name=settings.app_name,
        version=settings.app_version,
        debug=debug,
        log_level=log_level,
        tracing_enabled=trace
    )
    
    try:
        # Create and run application
        app = Application(config_path=config)
        return app.run()
    except Exception as e:
        logger.exception("Application failed", error=str(e))
        return 1
    finally:
        logger.info("Application stopped")


if __name__ == "__main__":
    sys.exit(main())
'''
        (src_path / "cli" / "commands.py").write_text(cli_content)
        
        # app.py
        app_content = '''"""Main application logic."""

from pathlib import Path
from typing import Optional

from .config.settings import settings
from .utils.logging import get_logger
from .core.engine import Engine


class Application:
    """Main application class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize application.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = get_logger(__name__)
        self.config_path = config_path
        self.engine = Engine()
        
        self.logger.info(
            "Application initialized",
            config_path=config_path
        )
    
    def run(self) -> int:
        """Run the application.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            self.logger.info("Starting engine")
            self.engine.start()
            
            # Main application logic here
            self.logger.info("Processing...")
            self.engine.process()
            
            return 0
            
        except Exception as e:
            self.logger.error("Application error", error=str(e))
            return 1
        finally:
            self.engine.stop()
'''
        (src_path / "app.py").write_text(app_content)
        
        # core/engine.py
        engine_content = '''"""Core engine implementation."""

from ..utils.logging import get_logger


class Engine:
    """Core processing engine."""
    
    def __init__(self):
        """Initialize engine."""
        self.logger = get_logger(__name__)
        self.running = False
    
    def start(self):
        """Start the engine."""
        self.logger.info("Engine starting")
        self.running = True
        # Initialize resources
    
    def process(self):
        """Main processing logic."""
        if not self.running:
            raise RuntimeError("Engine not started")
        
        self.logger.info("Processing data")
        # TODO: Implement core logic
    
    def stop(self):
        """Stop the engine."""
        self.logger.info("Engine stopping")
        self.running = False
        # Cleanup resources
'''
        (src_path / "core" / "engine.py").write_text(engine_content)
        
        # Create empty files for other modules
        for module in ["models", "services", "api"]:
            init_file = src_path / module / "__init__.py"
            init_file.write_text(f'"""Module for {module}."""\n')
    
    def _create_app_tests(self, app_path: Path, module_name: str):
        """Create test structure and files."""
        
        # conftest.py
        conftest_content = '''"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Provide test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock application settings."""
    monkeypatch.setenv("APP_NAME", "test-app")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
'''
        (app_path / "tests" / "conftest.py").write_text(conftest_content)
        
        # Unit test example
        unit_test = f'''"""Unit tests for the engine."""

import pytest
from {module_name}.core.engine import Engine


class TestEngine:
    """Test the Engine class."""
    
    def test_engine_initialization(self):
        """Test engine can be initialized."""
        engine = Engine()
        assert engine is not None
        assert not engine.running
    
    def test_engine_start(self):
        """Test engine can be started."""
        engine = Engine()
        engine.start()
        assert engine.running
    
    def test_engine_process_requires_start(self):
        """Test processing requires engine to be started."""
        engine = Engine()
        with pytest.raises(RuntimeError):
            engine.process()
'''
        (app_path / "tests" / "unit" / "test_engine.py").write_text(unit_test)
    
    def _create_app_docs(self, app_path: Path, app_name: str, description: str):
        """Create documentation files."""
        
        # README.md
        readme_content = f'''# {app_name}

{description}

## Quick Start

### Installation

```bash
# Clone the repository
cd apps/{app_path.name}

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

# Install in development mode
pip install -e .
```

### Usage

```bash
# Run the application
python -m {app_path.name.replace("-", "_")}

# With debug mode
python -m {app_path.name.replace("-", "_")} --debug

# Show help
python -m {app_path.name.replace("-", "_")} --help
```

## Configuration

Configuration can be set via:
1. Environment variables (see `.env.example`)
2. Configuration file (`configs/config.yaml`)
3. Command-line arguments

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov={app_path.name.replace("-", "_")} --cov-report=html

# Run specific test type
pytest tests/unit/
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff src/

# Type checking
mypy src/
```

## Architecture

See [architecture.md](docs/architecture.md) for detailed system design.

## API Documentation

See [api.md](docs/api.md) for API reference.

## Deployment

See [deployment.md](docs/deployment.md) for deployment instructions.
'''
        (app_path / "README.md").write_text(readme_content)
        
        # Architecture doc
        arch_content = f'''# {app_name} Architecture

## Overview

{description}

## Components

### Core Engine
- Main processing logic
- State management
- Resource lifecycle

### Services Layer
- Business logic implementation
- External service integration
- Data transformation

### API Layer
- REST/GraphQL endpoints
- Request validation
- Response formatting

### Models
- Domain models
- Data transfer objects
- Validation schemas

## Data Flow

```
Input → Validation → Processing → Transformation → Output
```

## Technology Stack

- Python {">"}= 3.10
- Pydantic for data validation
- Structlog for logging
- Click for CLI
- OpenTelemetry for observability

## Deployment Architecture

- Containerized with Docker
- Orchestrated with Kubernetes
- Monitored with Prometheus/Grafana
'''
        (app_path / "docs" / "architecture.md").write_text(arch_content)
    
    def _create_lib_structure(self, lib_path: Path, module_name: str):
        """Create library directory structure."""
        
        directories = [
            lib_path / module_name,
            lib_path / module_name / "core",
            lib_path / module_name / "models",
            lib_path / module_name / "services",
            lib_path / module_name / "utils",
            lib_path / "tests" / "unit",
            lib_path / "tests" / "integration",
            lib_path / "docs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            if module_name in str(directory) or "tests" in str(directory):
                if directory.name != "docs":
                    (directory / "__init__.py").touch()
    
    def _create_lib_config(
        self,
        lib_path: Path,
        module_name: str,
        description: str,
        author: str
    ):
        """Create library configuration files."""
        
        # pyproject.toml
        pyproject_content = f'''[project]
name = "{lib_path.name}"
version = "0.1.0"
description = "{description}"
authors = [{{name = "{author}"}}]
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["{module_name}*"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py310"
'''
        (lib_path / "pyproject.toml").write_text(pyproject_content)
        
        # README
        readme = f'''# {lib_path.name}

{description}

## Installation

```bash
pip install -e libs/{lib_path.name}
```

## Usage

```python
from {module_name} import ...
```

## Development

```bash
cd libs/{lib_path.name}
pip install -e ".[dev]"
pytest
```
'''
        (lib_path / "README.md").write_text(readme)
    
    def _create_lib_source(self, lib_path: Path, module_name: str, description: str):
        """Create library source files."""
        
        # Main __init__.py
        init_content = f'''"""
{description}
"""

__version__ = "0.1.0"
__author__ = "OPSVI Team"

# Export public API here
'''
        (lib_path / module_name / "__init__.py").write_text(init_content)
        
        # Core module
        core_content = '''"""Core functionality."""

from typing import Any


class BaseClass:
    """Base class for the library."""
    
    def __init__(self):
        """Initialize base class."""
        pass
    
    def process(self, data: Any) -> Any:
        """Process data.
        
        Args:
            data: Input data
            
        Returns:
            Processed data
        """
        raise NotImplementedError
'''
        (lib_path / module_name / "core" / "base.py").write_text(core_content)
        (lib_path / module_name / "core" / "__init__.py").write_text(
            'from .base import BaseClass\n\n__all__ = ["BaseClass"]'
        )
    
    def _create_lib_tests(self, lib_path: Path, module_name: str):
        """Create library test files."""
        
        test_content = f'''"""Tests for {module_name}."""

import pytest
from {module_name}.core import BaseClass


def test_base_class_creation():
    """Test BaseClass can be instantiated."""
    obj = BaseClass()
    assert obj is not None


def test_base_class_process_not_implemented():
    """Test process method raises NotImplementedError."""
    obj = BaseClass()
    with pytest.raises(NotImplementedError):
        obj.process("data")
'''
        (lib_path / "tests" / "unit" / "test_core.py").write_text(test_content)


# MCP Tool interface
def project_init_tool(action: str, **kwargs) -> Dict[str, Any]:
    """MCP tool interface for project initialization."""
    
    initializer = ProjectInitializer()
    
    actions = {
        "create_app": initializer.create_app,
        "create_library": initializer.create_library,
    }
    
    if action not in actions:
        return {
            "status": "error",
            "message": f"Unknown action: {action}",
            "available_actions": list(actions.keys())
        }
    
    try:
        return actions[action](**kwargs)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error executing {action}: {str(e)}"
        }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Project Initializer - Create standardized projects")
        print("=" * 50)
        print("Usage: project_initializer.py <action> [args...]")
        print("\nActions:")
        print("  create_app <name> <description> - Create new application")
        print("  create_library <name> <description> - Create new library")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "create_app" and len(sys.argv) >= 4:
        result = project_init_tool(
            "create_app",
            app_name=sys.argv[2],
            description=" ".join(sys.argv[3:])
        )
    elif action == "create_library" and len(sys.argv) >= 4:
        result = project_init_tool(
            "create_library",
            lib_name=sys.argv[2],
            description=" ".join(sys.argv[3:])
        )
    else:
        print(f"Invalid usage for action: {action}")
        sys.exit(1)
    
    print(json.dumps(result, indent=2))