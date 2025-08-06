#!/usr/bin/env python3
"""
OPSVI Library Template Generator

Creates a new OPSVI library with consistent structure and patterns.
"""

import argparse
from pathlib import Path

LIBRARY_TEMPLATE = {
    "directories": [
        "{lib_name}",
        "{lib_name}/core",
        "{lib_name}/utils",
        "tests",
        "docs",
    ],
    "files": {
        "pyproject.toml": """[project]
name = "{lib_name}"
version = "1.0.0"
description = "{description}"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [
    {{ name = "OPSVI Team", email = "team@opsvi.com" }}
]
keywords = ["{domain}", "opsvi", "ai", "ml"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Framework :: AsyncIO",
]

dependencies = [
    "opsvi-foundation>=1.0.0",
    "pydantic>=2.0.0",
    "structlog>=24.1.0",
    "httpx>=0.25.0",
{custom_dependencies}
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
    "coverage>=7.4.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
    "black>=24.0.0",
    "pre-commit>=3.6.0",
]

docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.5.0",
    "mkdocstrings[python]>=0.24.0",
]

[project.urls]
Homepage = "https://github.com/opsvi/master_root"
Repository = "https://github.com/opsvi/master_root"
Documentation = "https://github.com/opsvi/master_root/tree/main/libs/{lib_name}"
Issues = "https://github.com/opsvi/master_root/issues"

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["{package_name}*"]

# Standard OPSVI tool configurations...
[tool.pytest.ini_options]
minversion = "8.0"
addopts = ["-ra", "--strict-markers", "--strict-config", "--cov={package_name}"]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
ignore = ["E501", "B008", "C901"]

[tool.black]
target-version = ["py311"]
line-length = 88
""",
        "{lib_name}/__init__.py": '''"""
{lib_title}

{description}
"""

__version__ = "1.0.0"
__author__ = "OPSVI Team"
__email__ = "team@opsvi.com"

# Import foundation components
from opsvi_foundation import (
    config as foundation_config,
    AuthManager,
    CircuitBreaker,
    MetricsCollector,
    BaseComponent,
)

# Library-specific imports
from .core import {class_name}Config
{custom_imports}

__all__ = [
    "{class_name}Config",
{custom_exports}
]
''',
        "{lib_name}/core/__init__.py": '''"""
Core components for {lib_name}.
"""

from .config import {class_name}Config
from .exceptions import {class_name}Error

__all__ = ["{class_name}Config", "{class_name}Error"]
''',
        "{lib_name}/core/config.py": '''"""
Configuration management for {lib_name}.
"""

from typing import Optional
from pydantic import BaseModel, Field
from opsvi_foundation import FoundationConfig


class {class_name}Config(BaseModel):
    """Configuration for {lib_name}."""

    # Inherit foundation settings
    foundation: FoundationConfig = Field(default_factory=FoundationConfig.from_env)

    # Library-specific settings
    {custom_config_fields}

    @classmethod
    def from_env(cls) -> "{class_name}Config":
        """Create configuration from environment variables."""
        return cls(
            foundation=FoundationConfig.from_env(),
            {custom_config_values}
        )


# Global configuration instance
config = {class_name}Config.from_env()
''',
        "{lib_name}/core/exceptions.py": '''"""
Exception hierarchy for {lib_name}.
"""

from opsvi_foundation.patterns import ComponentError


class {class_name}Error(ComponentError):
    """Base exception for {lib_name}."""
    pass


class {class_name}ValidationError({class_name}Error):
    """Validation error specific to {lib_name}."""
    pass


class {class_name}ConfigurationError({class_name}Error):
    """Configuration error specific to {lib_name}."""
    pass
''',
        "README.md": """# {lib_title}

{description}

## Features

- Integration with OPSVI Foundation
- Modern async/await patterns
- Comprehensive error handling
- Production-ready observability
- Type-safe configuration

## Installation

```bash
pip install {lib_name}
```

## Quick Start

```python
from {package_name} import {class_name}Config

# Initialize with configuration
config = {class_name}Config.from_env()

# Use the library...
```

## Architecture

This library follows OPSVI ecosystem patterns:
- Uses `opsvi-foundation` for shared components
- Implements domain-specific logic only
- Follows async-first design principles
- Includes comprehensive observability

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run quality checks
ruff check .
black .
mypy .
```

## Contributing

1. Follow OPSVI coding standards
2. Add tests for new functionality
3. Update documentation
4. Ensure all quality checks pass
""",
        "tests/test_{package_name}.py": '''"""
Test suite for {lib_name}.
"""

import pytest
from {package_name} import {class_name}Config


def test_config_creation():
    """Test configuration creation."""
    config = {class_name}Config.from_env()
    assert config.foundation is not None


@pytest.mark.asyncio
async def test_basic_functionality():
    """Test basic library functionality."""
    # Add your tests here
    pass
''',
    },
}


def create_library(
    name: str,
    description: str,
    domain: str,
    custom_dependencies: list = None,
    custom_config_fields: str = "",
    custom_imports: str = "",
    custom_exports: str = "",
    custom_config_values: str = "",
) -> None:
    """Create a new OPSVI library from template."""

    if custom_dependencies is None:
        custom_dependencies = []

    # Format dependencies
    deps_str = ""
    for dep in custom_dependencies:
        deps_str += f'    "{dep}",\n'

    # Prepare template variables
    lib_name = name
    package_name = name.replace("-", "_")
    class_name = "".join(
        word.capitalize() for word in name.replace("opsvi-", "").split("-")
    )
    lib_title = f"OPSVI {class_name} Library"

    template_vars = {
        "lib_name": lib_name,
        "package_name": package_name,
        "class_name": class_name,
        "lib_title": lib_title,
        "description": description,
        "domain": domain,
        "custom_dependencies": deps_str,
        "custom_config_fields": custom_config_fields,
        "custom_imports": custom_imports,
        "custom_exports": custom_exports,
        "custom_config_values": custom_config_values,
    }

    # Create directory structure
    base_path = Path(lib_name)
    if base_path.exists():
        print(f"❌ Directory {lib_name} already exists!")
        return

    print(f"📁 Creating {lib_name} directory structure...")
    for directory in LIBRARY_TEMPLATE["directories"]:
        dir_path = base_path / directory.format(**template_vars)
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create files from templates
    print("📝 Creating files...")
    for file_path, content in LIBRARY_TEMPLATE["files"].items():
        full_path = base_path / file_path.format(**template_vars)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "w") as f:
            f.write(content.format(**template_vars))

    print(f"✅ Library {lib_name} created successfully!")
    print("")
    print("📋 Next steps:")
    print(f"  1. cd {lib_name}")
    print("  2. Customize the configuration and core logic")
    print("  3. Add domain-specific modules")
    print("  4. Write comprehensive tests")
    print("  5. Update documentation")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create a new OPSVI library")
    parser.add_argument("name", help="Library name (e.g., 'opsvi-newlib')")
    parser.add_argument("description", help="Library description")
    parser.add_argument("domain", help="Domain/category (e.g., 'llm', 'rag', 'agents')")
    parser.add_argument("--deps", nargs="*", help="Additional dependencies")

    args = parser.parse_args()

    create_library(
        name=args.name,
        description=args.description,
        domain=args.domain,
        custom_dependencies=args.deps or [],
    )


if __name__ == "__main__":
    main()
