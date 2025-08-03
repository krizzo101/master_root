FROM ubuntu:22.04

# Create non-root user
RUN useradd -m -s /bin/bash ubuntu

# Install system dependencies
RUN apt-get update && \
    apt-get install -y software-properties-common wget curl git build-essential && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.12 python3.12-pip python3.12-dev python3.12-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default (matching the setup guide)
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Install Node.js 22.x (as specified in setup guide)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

# Set working directory
WORKDIR /workspace

# Create the exact directory structure from setup guide
RUN mkdir -p tests/{unit,integration,system} config logs && \
    touch tests/{unit,integration,system}/__init__.py

# Create virtual environment as specified in setup guide
RUN python3.12 -m venv .venv

# Activate virtual environment and upgrade pip
RUN . .venv/bin/activate && \
    pip install --upgrade pip setuptools wheel

# Install all Python dependencies (matching requirements.txt and setup guide)
RUN . .venv/bin/activate && pip install \
    black==25.1.0 \
    flake8==7.2.0 \
    mypy==1.15.0 \
    isort==6.0.1 \
    pytest==8.3.5 \
    pytest-asyncio==0.26.0 \
    openai \
    requests==2.32.3 \
    pydantic \
    tinydb==4.8.2 \
    psutil \
    PyYAML==6.0.2 \
    jinja2==3.1.3 \
    numpy==2.2.6 \
    pandas==2.2.3 \
    matplotlib==3.10.3 \
    tiktoken==0.7.0 \
    pre-commit==4.2.0 \
    cfgv==3.4.0 \
    click==8.2.1 \
    contourpy==1.3.2 \
    cycler==0.12.1 \
    distlib==0.3.9 \
    filelock==3.18.0 \
    fonttools==4.58.0 \
    identify==2.6.10 \
    iniconfig==2.1.0 \
    kiwisolver==1.4.8 \
    mccabe==0.7.0 \
    mypy_extensions==1.1.0 \
    nodeenv==1.9.1 \
    packaging==25.0 \
    pathspec==0.12.1 \
    pillow==11.2.1 \
    platformdirs==4.3.8 \
    pluggy==1.6.0 \
    pycodestyle==2.13.0 \
    pyflakes==3.3.2 \
    pyparsing==3.2.3 \
    python_dateutil==2.9.0.post0 \
    pytz==2025.2 \
    regex==2024.11.6 \
    six==1.17.0 \
    sniffio==1.3.1 \
    tqdm==4.67.1 \
    typing_extensions==4.13.2 \
    urllib3==2.4.0 \
    virtualenv==20.31.2

# Install ruff for linting (used in pre-commit)
RUN . .venv/bin/activate && pip install ruff

# Create sample test files as specified in setup guide
RUN echo '"""Test configuration for pytest."""' > tests/conftest.py && \
    echo 'import os' >> tests/conftest.py && \
    echo 'import sys' >> tests/conftest.py && \
    echo 'from pathlib import Path' >> tests/conftest.py && \
    echo '' >> tests/conftest.py && \
    echo '# Add the project root directory to the Python path' >> tests/conftest.py && \
    echo 'sys.path.insert(0, str(Path(__file__).parent.parent))' >> tests/conftest.py && \
    echo '' >> tests/conftest.py && \
    echo '# Setup fixtures shared across tests' >> tests/conftest.py && \
    echo 'import pytest' >> tests/conftest.py && \
    echo '' >> tests/conftest.py && \
    echo '@pytest.fixture' >> tests/conftest.py && \
    echo 'def sample_config():' >> tests/conftest.py && \
    echo '    """Provide a sample configuration for testing."""' >> tests/conftest.py && \
    echo '    return {' >> tests/conftest.py && \
    echo '        "logging": {' >> tests/conftest.py && \
    echo '            "level": "DEBUG",' >> tests/conftest.py && \
    echo '            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"' >> tests/conftest.py && \
    echo '        },' >> tests/conftest.py && \
    echo '        "system": {' >> tests/conftest.py && \
    echo '            "max_evolution_cycles": 10,' >> tests/conftest.py && \
    echo '            "timeout_seconds": 3600' >> tests/conftest.py && \
    echo '        }' >> tests/conftest.py && \
    echo '    }' >> tests/conftest.py

RUN echo '"""Example unit test file."""' > tests/unit/test_example.py && \
    echo 'import pytest' >> tests/unit/test_example.py && \
    echo '' >> tests/unit/test_example.py && \
    echo 'def test_simple_assertion():' >> tests/unit/test_example.py && \
    echo '    """Simple test to verify pytest is working."""' >> tests/unit/test_example.py && \
    echo '    assert 1 + 1 == 2' >> tests/unit/test_example.py && \
    echo '' >> tests/unit/test_example.py && \
    echo 'def test_with_sample_config(sample_config):' >> tests/unit/test_example.py && \
    echo '    """Test using a fixture."""' >> tests/unit/test_example.py && \
    echo '    assert "logging" in sample_config' >> tests/unit/test_example.py && \
    echo '    assert sample_config["system"]["max_evolution_cycles"] == 10' >> tests/unit/test_example.py

# Switch to non-root user
USER ubuntu

# Set environment variables for consistent behavior
ENV PYTHONPATH=/workspace/src
ENV PYTHONUNBUFFERED=1
ENV PATH="/workspace/.venv/bin:$PATH"

# Add validation script will be copied when repo is cloned

# Add basic healthcheck using python version check (validation script copied at runtime)
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
  CMD /workspace/.venv/bin/python --version || exit 1