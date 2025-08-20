#!/usr/bin/env python3
"""
Create setup.py for opsvi libraries that don't have one
"""

import json
import sys
from pathlib import Path


def create_setup_py(lib_path):
    """Create a setup.py for a library"""
    lib_path = Path(lib_path)
    lib_name = lib_path.name
    module_name = lib_name.replace("-", "_")

    # Check if setup.py already exists
    setup_file = lib_path / "setup.py"
    if setup_file.exists():
        print(f"✓ {lib_name} already has setup.py")
        return

    # Determine appropriate dependencies based on library
    dependencies = {
        "opsvi-core": [
            "pydantic>=2.0.0",
            "typing-extensions>=4.0.0",
        ],
        "opsvi-data": [
            "pydantic>=2.0.0",
            "sqlalchemy>=2.0.0",
            "typing-extensions>=4.0.0",
        ],
        "opsvi-llm": [
            "anthropic>=0.39.0",
            "openai>=1.0.0",
            "langchain>=0.1.0",
            "tiktoken>=0.5.0",
            "pydantic>=2.0.0",
        ],
        "opsvi-fs": [
            "pathlib2>=2.3.0",
            "watchdog>=3.0.0",
        ],
        "opsvi-auth": [
            "pyjwt>=2.8.0",
            "passlib>=1.7.4",
            "python-multipart>=0.0.6",
            "python-jose[cryptography]>=3.3.0",
        ],
        "opsvi-visualization": [
            "graphviz>=0.20.0",
            "matplotlib>=3.7.0",
            "plotly>=5.0.0",
        ],
        "opsvi-monitoring": [
            "prometheus-client>=0.19.0",
            "opentelemetry-api>=1.20.0",
            "opentelemetry-sdk>=1.20.0",
            "structlog>=23.0.0",
        ],
        "opsvi-docker": [
            "docker>=6.1.0",
            "python-on-whales>=0.60.0",
        ],
        "opsvi-api": [
            "fastapi>=0.104.0",
            "httpx>=0.25.0",
            "uvicorn>=0.24.0",
        ],
    }

    # Get dependencies for this library
    install_requires = dependencies.get(
        lib_name,
        [
            "pydantic>=2.0.0",
            "typing-extensions>=4.0.0",
        ],
    )

    # Determine description
    descriptions = {
        "opsvi-core": "Core abstractions and base classes for OpsVi system",
        "opsvi-data": "Data models, schemas, and database interfaces for OpsVi",
        "opsvi-llm": "Unified LLM interfaces for Anthropic, OpenAI, and other providers",
        "opsvi-fs": "File system operations and utilities for OpsVi",
        "opsvi-auth": "Authentication and authorization for OpsVi services",
        "opsvi-visualization": "Visualization and diagram generation for OpsVi",
        "opsvi-monitoring": "Monitoring, metrics, and observability for OpsVi",
        "opsvi-docker": "Docker and container management for OpsVi",
        "opsvi-api": "API clients and servers for OpsVi services",
        "opsvi-interfaces": "CLI and configuration interfaces for OpsVi",
    }

    description = descriptions.get(lib_name, f"{lib_name} library for OpsVi system")

    # Create setup.py content
    setup_content = f'''"""
Setup configuration for {lib_name}
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README if it exists
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="{lib_name}",
    version="0.1.0",
    description="{description}",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="OpsVi Team",
    author_email="team@opsvi.ai",
    url="https://github.com/opsvi/master_root",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    install_requires={json.dumps(install_requires, indent=8).strip()},
    extras_require={{
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
        ],
    }},
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="opsvi {lib_name.replace('opsvi-', '')} autonomous ai ml",
    project_urls={{
        "Bug Reports": "https://github.com/opsvi/master_root/issues",
        "Source": "https://github.com/opsvi/master_root",
    }},
)
'''

    # Write setup.py
    setup_file.write_text(setup_content)
    print(f"✓ Created setup.py for {lib_name}")

    # Create basic README if it doesn't exist
    readme_file = lib_path / "README.md"
    if not readme_file.exists():
        readme_content = f"""# {lib_name}

{description}

## Installation

```bash
pip install -e libs/{lib_name}
```

## Usage

```python
from {module_name} import ...
```

## Development

```bash
# Install with dev dependencies
pip install -e "libs/{lib_name}[dev]"

# Run tests
pytest libs/{lib_name}

# Format code
black libs/{lib_name}
ruff check libs/{lib_name}
```

## License

MIT
"""
        readme_file.write_text(readme_content)
        print(f"✓ Created README.md for {lib_name}")


def main():
    if len(sys.argv) < 2:
        # Default to core libraries
        libs = [
            "libs/opsvi-core",
            "libs/opsvi-data",
            "libs/opsvi-llm",
            "libs/opsvi-fs",
            "libs/opsvi-auth",
            "libs/opsvi-visualization",
            "libs/opsvi-api",
        ]
        print("No libraries specified, using core libraries:")
        for lib in libs:
            print(f"  - {lib}")
        print()
    else:
        libs = sys.argv[1:]

    for lib_path in libs:
        lib_path = Path(lib_path)
        if not lib_path.exists():
            print(f"✗ {lib_path} does not exist")
            continue
        create_setup_py(lib_path)

    print("\nDone! To install these libraries:")
    print("  pip install -e libs/opsvi-core libs/opsvi-data libs/opsvi-llm")


if __name__ == "__main__":
    main()
