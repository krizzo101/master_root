#!/bin/bash
# Python Project Template Generator

PROJECT_NAME=${1:-"new-project"}
PROJECT_PATH=${2:-"./COMPLETE SUMMARY"}

echo "🐍 Creating Python project: $PROJECT_NAME"

# Create project structure
mkdir -p "$PROJECT_PATH/$PROJECT_NAME"/{src,tests,docs,scripts,data}
cd "$PROJECT_PATH/$PROJECT_NAME"

# Create pyproject.toml
cat > pyproject.toml << EOF
[tool.poetry]
name = "$PROJECT_NAME"
version = "0.1.0"
description = "A new Python project"
authors = ["Your Name <email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"

[tool.poetry.dev-dependencies]
pytest = "^7.0"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.0"
pytest-cov = "^4.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88

[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
EOF

# Create .gitignore
cat > .gitignore << EOF
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
pip-log.txt
.coverage
.pytest_cache/
.mypy_cache/
.ruff_cache/
*.egg-info/
dist/
build/
.idea/
.vscode/
*.swp
.DS_Store
EOF

# Create README
cat > README.md << EOF
# $PROJECT_NAME

## Description
A new Python project

## Installation
\`\`\`bash
poetry install
\`\`\`

## Usage
\`\`\`python
from $PROJECT_NAME import main
main()
\`\`\`

## Testing
\`\`\`bash
pytest
\`\`\`

## License
MIT
EOF

# Create main module
cat > "src/__init__.py" << EOF
"""$PROJECT_NAME - Main module"""

__version__ = "0.1.0"
EOF

cat > "src/main.py" << EOF
"""Main entry point for $PROJECT_NAME"""

def main():
    """Main function"""
    print("Hello from $PROJECT_NAME!")

if __name__ == "__main__":
    main()
EOF

# Create test file
cat > "tests/test_main.py" << EOF
"""Tests for main module"""

import pytest
from src.main import main

def test_main():
    """Test main function"""
    # This test will be implemented
    assert main is not None
EOF

# Create CLAUDE.md
cat > CLAUDE.md << EOF
# $PROJECT_NAME - Claude Code Instructions

## Project Overview
This is a Python project using Poetry for dependency management.

## Development Workflow
1. Install dependencies: \`poetry install\`
2. Run tests: \`pytest\`
3. Format code: \`black .\`
4. Lint: \`ruff check .\`
5. Type check: \`mypy .\`

## Project Structure
- src/ - Source code
- tests/ - Test files
- docs/ - Documentation
- scripts/ - Utility scripts
- data/ - Data files

## Standards
- Use type hints
- Write docstrings
- Maintain >80% test coverage
- Follow PEP 8
EOF

echo "✅ Python project '$PROJECT_NAME' created successfully!"
echo "Next steps:"
echo "  cd $PROJECT_PATH/$PROJECT_NAME"
echo "  poetry install"
echo "  poetry run pytest"
