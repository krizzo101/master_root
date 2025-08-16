#!/bin/bash
# Script to build documentation for Project Mapper

set -e  # Exit on error

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building documentation for Project Mapper${NC}"

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Create directory for built docs
mkdir -p docs/_build

# Check if sphinx-build is installed
if ! command -v sphinx-build &> /dev/null; then
    echo -e "${RED}sphinx-build not found. Please install Sphinx:${NC}"
    echo -e "${YELLOW}pip install sphinx sphinx-rtd-theme myst-parser${NC}"
    exit 1
fi

# Check if required theme is installed
python -c "import sphinx_rtd_theme" 2>/dev/null || {
    echo -e "${RED}sphinx_rtd_theme not found. Please install:${NC}"
    echo -e "${YELLOW}pip install sphinx-rtd-theme${NC}"
    exit 1
}

# Check if myst-parser is installed
python -c "import myst_parser" 2>/dev/null || {
    echo -e "${RED}myst-parser not found. Please install:${NC}"
    echo -e "${YELLOW}pip install myst-parser${NC}"
    exit 1
}

echo -e "${YELLOW}Building HTML documentation...${NC}"
cd docs
sphinx-build -b html . _build/html || { echo -e "${RED}HTML documentation build failed${NC}"; exit 1; }

echo -e "${YELLOW}Building PDF documentation...${NC}"
if command -v make &> /dev/null; then
    make latexpdf || { echo -e "${YELLOW}PDF documentation build failed (optional)${NC}"; }
else
    echo -e "${YELLOW}Skipping PDF build (make not available)${NC}"
fi

# Make the script executable
chmod +x "$0"

echo -e "${GREEN}Documentation built successfully!${NC}"
echo -e "${GREEN}HTML documentation available at docs/_build/html/index.html${NC}"
if [ -f docs/_build/latex/projectmapper.pdf ]; then
    echo -e "${GREEN}PDF documentation available at docs/_build/latex/projectmapper.pdf${NC}"
fi 