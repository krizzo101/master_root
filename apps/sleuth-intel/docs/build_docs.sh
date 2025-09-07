#!/bin/bash

# Build script for Sleuth Intel documentation

echo "Building Sleuth Intel Documentation..."
echo "======================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install documentation dependencies
echo "Installing documentation dependencies..."
pip install -q -r requirements.txt

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/*

# Generate API documentation from source code
echo "Generating API documentation..."
sphinx-apidoc -f -o source/api ../src

# Build HTML documentation
echo "Building HTML documentation..."
sphinx-build -b html source build/html

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Documentation built successfully!"
    echo "📁 Location: docs/build/html/index.html"
    echo ""
    echo "To view the documentation:"
    echo "  1. Open docs/build/html/index.html in a browser"
    echo "  2. Or run: python -m http.server 8000 --directory build/html"
    echo "     Then visit: http://localhost:8000"
else
    echo ""
    echo "❌ Documentation build failed!"
    exit 1
fi

# Optional: Start local server
read -p "Start local documentation server? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting documentation server on http://localhost:8000"
    python -m http.server 8000 --directory build/html
fi
