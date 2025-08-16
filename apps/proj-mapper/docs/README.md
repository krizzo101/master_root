# Project Mapper Documentation

This directory contains the documentation for the Project Mapper system.

## Structure

- `api/`: API reference documentation
- `user/`: User guides and tutorials
- `developer/`: Developer documentation and architecture overview

## Building the Documentation

We use Sphinx for documentation generation. To build the docs:

1. Make sure you have set up the development environment:

   ```bash
   # On Linux/Mac
   ./scripts/setup_dev_env.sh

   # On Windows
   .\scripts\setup_dev_env.bat
   ```

2. Build the documentation:

   ```bash
   # Activate virtual environment if not already active
   source .venv/bin/activate  # On Linux/Mac
   .\.venv\Scripts\activate   # On Windows

   # Build the docs
   cd docs
   make html
   ```

3. View the documentation:
   ```bash
   # Open in your browser
   open _build/html/index.html  # On Mac
   xdg-open _build/html/index.html  # On Linux
   start _build/html/index.html  # On Windows
   ```

## Contributing to Documentation

When contributing to documentation:

1. Write clear, concise, and comprehensive documentation
2. Use proper formatting with Markdown and reStructuredText
3. Include examples where appropriate
4. Ensure all code examples are tested and working
5. Update documentation when making changes to the codebase

## Style Guide

- Use present tense
- Be direct and concise
- Use active voice
- Include code examples for complex concepts
- Document both "how" and "why"
