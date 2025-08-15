#!/bin/bash
# Project Mapper Development Environment Setup
# This script creates a virtual environment and installs all dependencies for development

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if Python 3.8+ is available
echo -e "${YELLOW}Checking for Python 3.8+...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo -e "${RED}Error: Python 3.8 or higher is required. Found Python $PYTHON_VERSION${NC}"
        exit 1
    else
        PYTHON_CMD=python3
        echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"
    fi
else
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi

# Create and activate a virtual environment
echo -e "${YELLOW}Creating a virtual environment...${NC}"
cd "$PROJECT_ROOT"

if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Do you want to recreate it? [y/N]${NC}"
    read -r recreate
    if [[ $recreate =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf venv
    else
        echo -e "${GREEN}Using existing virtual environment${NC}"
    fi
fi

if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment based on OS
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
    source venv/bin/activate
else
    echo -e "${RED}Error: Unsupported OS. Please activate the virtual environment manually${NC}"
    exit 1
fi

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing development dependencies...${NC}"
pip install -e ".[dev]"

# Install pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
pre-commit install

# Validate the setup
echo -e "${YELLOW}Validating setup...${NC}"
echo -e "Checking Black..."
black --version
echo -e "Checking isort..."
isort --version
echo -e "Checking flake8..."
flake8 --version
echo -e "Checking mypy..."
mypy --version
echo -e "Checking pytest..."
pytest --version
echo -e "Checking pre-commit..."
pre-commit --version

echo -e "${GREEN}Development environment setup successfully!${NC}"
echo -e "${YELLOW}Activate the virtual environment with: source venv/bin/activate${NC}" 