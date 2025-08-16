#!/bin/bash
set -e

echo "=== DEPLOYING OPSVI ECOSYSTEM ==="

# Install all libraries
cd libs
for lib in opsvi-*; do
    echo "Installing $lib..."
    pip install -e $lib
done

# Install main ecosystem
pip install -e opsvi-ecosystem

# Run integration tests
cd opsvi-ecosystem
python -m pytest tests/ -v

echo "=== ECOSYSTEM DEPLOYMENT COMPLETE ==="
