# Sleuth Intel Documentation

## Overview

This directory contains comprehensive API documentation for the Sleuth Intel OSINT investigation framework. The documentation is built using Sphinx and includes:

- **Getting Started Guides**: Installation, configuration, and quickstart tutorials
- **User Guides**: Workflow design, best practices, and usage patterns
- **Technical Documentation**: Architecture, performance, security details
- **Integration Guides**: Orchestrator, webhooks, databases, custom agents
- **API Reference**: Complete API documentation with examples
- **Examples**: Real-world investigation scenarios and code samples

## Documentation Structure

```
docs/
├── source/                  # Documentation source files
│   ├── index.rst           # Main documentation index
│   ├── conf.py            # Sphinx configuration
│   ├── getting_started/   # Installation and quickstart guides
│   ├── guides/            # User guides and tutorials
│   ├── technical/         # Technical documentation
│   ├── integration/       # Integration guides
│   ├── api/              # API reference documentation
│   ├── examples/         # Code examples and use cases
│   └── reference/        # Reference materials
├── build/                # Generated documentation (HTML, PDF)
├── requirements.txt      # Documentation dependencies
├── Makefile             # Build commands for Unix/Linux
└── build_docs.sh        # Automated build script
```

## Building Documentation

### Prerequisites

```bash
# Install Python 3.9+
python --version

# Install documentation dependencies
pip install -r docs/requirements.txt
```

### Quick Build

```bash
# Make build script executable
chmod +x docs/build_docs.sh

# Run build script
./docs/build_docs.sh
```

### Manual Build

```bash
cd docs

# Install dependencies
pip install -r requirements.txt

# Clean previous builds
make clean

# Build HTML documentation
make html

# View documentation
open build/html/index.html  # macOS
xdg-open build/html/index.html  # Linux
start build/html/index.html  # Windows
```

### Other Build Formats

```bash
# Build PDF documentation
make latexpdf

# Build EPUB
make epub

# Check for broken links
make linkcheck

# Check documentation coverage
make coverage
```

## Development

### Live Reload Server

For documentation development with auto-reload:

```bash
# Install sphinx-autobuild
pip install sphinx-autobuild

# Start development server
make livehtml

# Visit http://localhost:8000
```

### Adding New Documentation

1. **Create RST file** in appropriate directory
2. **Add to toctree** in parent index file
3. **Build documentation** to verify
4. **Commit changes**

Example:

```rst
.. New Feature Documentation

================
New Feature Name
================

Feature description here...

Basic Usage
===========

.. code-block:: python

   from sleuth_intel import NewFeature

   feature = NewFeature()
   result = feature.execute()
```

## Documentation Features

### Sphinx Extensions Used

- **autodoc**: Automatic API documentation from docstrings
- **napoleon**: Support for Google/NumPy style docstrings
- **viewcode**: Add links to source code
- **intersphinx**: Link to other project documentation
- **sphinx-rtd-theme**: Read the Docs theme
- **myst-parser**: Markdown support
- **sphinxcontrib-mermaid**: Diagram support
- **autodoc-pydantic**: Pydantic model documentation

### Search Functionality

The generated HTML documentation includes:
- Full-text search
- API index
- Module index
- General index

### Code Examples

All code examples are:
- Syntax highlighted
- Copy-to-clipboard enabled
- Tested and validated
- Runnable standalone

## API Documentation Generation

The API documentation is automatically generated from source code docstrings:

```bash
# Generate/update API docs from source
sphinx-apidoc -f -o docs/source/api src/

# Then rebuild HTML
make html
```

## Writing Documentation

### Style Guide

- Use **reStructuredText** for documentation files
- Follow **Google-style** docstrings in Python code
- Include **code examples** for all features
- Add **type hints** for better documentation
- Write **clear descriptions** for parameters
- Document **exceptions** and **return values**

### Docstring Example

```python
def investigate(self, query: Dict[str, Any]) -> InvestigationResult:
    """
    Execute investigation based on provided query.

    Args:
        query: Investigation parameters including:
            - name (str): Subject name
            - location (str, optional): Location constraint
            - depth (int, optional): Investigation depth (default: 3)

    Returns:
        InvestigationResult: Investigation results containing:
            - data: Raw investigation data
            - summary: Executive summary
            - confidence: Confidence score (0-1)

    Raises:
        ValidationError: If query parameters are invalid
        APIError: If external API call fails
        RateLimitError: If rate limit exceeded

    Example:
        >>> agent = PersonSearchAgent()
        >>> result = agent.investigate({
        ...     "name": "John Doe",
        ...     "location": "New York"
        ... })
        >>> print(result.summary)
    """
```

## Deployment

### GitHub Pages

```bash
# Install ghp-import
pip install ghp-import

# Deploy to GitHub Pages
make deploy
```

### Read the Docs

1. Connect repository to Read the Docs
2. Configure `.readthedocs.yml`
3. Build will trigger on commits

### Self-Hosted

```bash
# Build static site
make html

# Serve with any web server
python -m http.server 8000 --directory build/html
# Or nginx, Apache, etc.
```

## Contributing

### Adding Documentation

1. Fork repository
2. Create feature branch
3. Add/update documentation
4. Build and verify locally
5. Submit pull request

### Reporting Issues

Report documentation issues at:
https://github.com/yourusername/sleuth-intel/issues

Use label: `documentation`

## Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Read the Docs](https://readthedocs.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

## License

Documentation is licensed under the same license as the Sleuth Intel project.
