# Knowledge Update: Ruff (Generated 2025-08-05)

## Current State (Last 12+ Months)

Ruff is an extremely fast Python linter and code formatter written in Rust, with significant recent improvements:
- **Performance**: 10-100x faster than traditional Python linters
- **Formatter**: Built-in code formatter with 2025 stable style guide
- **Rule Coverage**: 700+ rules from popular linters (flake8, pylint, pyupgrade, etc.)
- **Language Server**: Built-in LSP for IDE integration
- **Preview Features**: Experimental rules and formatting options
- **Jupyter Support**: Native Jupyter notebook linting and formatting
- **Type Checking**: Integration with type checkers and stub file support

## Best Practices & Patterns

### Basic Configuration
```toml
# pyproject.toml
[tool.ruff]
target-version = "py310"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long, handled by formatter
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### Advanced Configuration
```toml
[tool.ruff]
# Target Python version
target-version = "py310"

# Line length
line-length = 88

# Enable specific rule sets
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "N",   # pep8-naming
    "PLR", # pylint refactor
    "PLW", # pylint warnings
    "PLE", # pylint errors
    "PL",  # pylint
    "RUF", # ruff-specific rules
]

# Ignore specific rules
ignore = [
    "E501",  # line too long
    "B008",  # function calls in defaults
    "C901",  # too complex
]

# Per-file rule ignores
[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*.py" = ["PLR2004"]
"docs/**/*.py" = ["E501"]

# Import sorting
[tool.ruff.isort]
known-first-party = ["myapp"]
known-third-party = ["requests", "pandas"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]
```

### Formatter Configuration
```toml
[tool.ruff.format]
# Quote style
quote-style = "double"

# Indentation
indent-style = "space"
indent-width = 4

# Line endings
line-ending = "auto"

# Magic trailing comma
skip-magic-trailing-comma = false

# Docstring formatting
docstring-code-format = true

# Preview features
preview = true
```

### Language Server Configuration
```toml
[tool.ruff.lint]
# Enable specific rules
select = ["E", "F", "I", "UP"]

# Disable specific rules
ignore = ["E501"]

# Show fixes
show-fixes = true

# Show source
show-source = true

[tool.ruff.lint.rules]
# Configure specific rules
"noqa" = { "require-code-to-exist" = true }
"isort" = { "combine-as-imports" = true }
```

## Tools & Frameworks

### Core Components
- **ruff**: Main command-line interface
- **ruff check**: Lint Python files
- **ruff format**: Format Python files
- **ruff server**: Language server for IDE integration

### Command Line Usage
```bash
# Basic linting
ruff check .

# Format code
ruff format .

# Check and format
ruff check --fix .
ruff format .

# Show rule violations
ruff check --show-source .

# Generate configuration
ruff init

# Preview features
ruff check --preview .
ruff format --preview .
```

### IDE Integration
```json
// VS Code settings.json
{
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll": true,
        "source.organizeImports": true
    }
}
```

### Pre-commit Integration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Implementation Guidance

### Migration from Other Tools
```bash
# Migrate from flake8
ruff check --select E,W,F .

# Migrate from black
ruff format .

# Migrate from isort
ruff check --select I --fix .

# Migrate from pyupgrade
ruff check --select UP --fix .
```

### CI/CD Integration
```yaml
# GitHub Actions
- name: Lint with Ruff
  run: |
    pip install ruff
    ruff check .

- name: Format with Ruff
  run: |
    pip install ruff
    ruff format --check .
```

### Project Setup
```bash
# Initialize Ruff configuration
ruff init

# Check current configuration
ruff check --show-config

# Generate rules documentation
ruff rule E501
```

## Limitations & Considerations

### Current Limitations
- **Preview Features**: Some features are in preview and may change
- **Rule Coverage**: Not all rules from other linters are implemented
- **Custom Rules**: Limited support for custom rule development
- **Legacy Python**: Some features require Python 3.8+

### Best Practices
- **Use Preview Features**: Enable preview for latest features
- **Configure Per-File**: Use per-file ignores for specific cases
- **IDE Integration**: Use language server for real-time feedback
- **CI/CD**: Include Ruff in automated checks
- **Migration**: Gradually migrate from other tools

### Migration Considerations
- **Rule Mapping**: Map existing linter rules to Ruff equivalents
- **Configuration**: Migrate configuration files gradually
- **Team Adoption**: Ensure team familiarity with Ruff commands
- **Breaking Changes**: Test preview features before production

## Recent Updates (2024-2025)

### Formatter Updates (2025 Style Guide)
- **f-string Formatting**: Expressions within f-strings are now formatted
- **f-string Quotes**: Alternate quotes for strings inside f-strings
- **Implicit Concatenation**: Improved string concatenation handling
- **Assert Statements**: Better parenthesizing of assert messages
- **Match-Case**: Improved formatting for match-case patterns
- **Type Annotations**: Avoid unnecessary parentheses around return types
- **With Statements**: Consistent formatting for context managers
- **Docstring Code Blocks**: Corrected line-width calculation

### New Rules (2024-2025)
- **PLW0211**: Bad staticmethod argument (pylint)
- **PLR1730, PLR1731**: If-stmt min/max optimization (pylint)
- **UP042**: StrEnum multiple inheritance (pyupgrade)
- **FURB110**: If-expr instead of or operator (refurb)
- **FURB166**: Int on sliced string (refurb)
- **FURB103**: Write whole file (refurb)
- **C419**: Sum/min/max comprehension (flake8-comprehensions)

### Preview Features
- **SIM108**: Further simplify to binary in preview
- **UP031**: Show violations without auto-fix in preview
- **ASYNC116**: Sleep interval warnings (flake8-async)
- **SIM115**: Extended to handle dbm.sqlite3
- **UP015**: Detect aiofiles.open calls
- **UP036**: Mark outdated Python version comparisons

### Stabilized Rules (2024-2025)
- **PLE1519**: Singledispatch method
- **PLE1520**: Singledispatchmethod function
- **PLW0211**: Bad staticmethod argument
- **PLR1730**: If-stmt min/max
- **PLE0308**: Invalid bytes return type
- **PLE0309**: Invalid hash return type
- **PLE0305**: Invalid index return type
- **PLEE303**: Invalid length return type
- **PLW0642**: Self or cls assignment
- **PYI057**: Byte string usage
- **PYI062**: Duplicate literal member
- **RUF101**: Redirected noqa

### Breaking Changes (2024-2025)
- **Target Python Version**: Default changed from 3.10 to 3.8
- **Default Exclusions**: Updated list of excluded directories
- **Line Width Calculation**: Updated unicode-width crate
- **Windows Support**: Minimum Windows 10 requirement
- **Docker Alpine**: Default Alpine tag updated to 3.21
- **Jupyter Notebooks**: Lint and format by default
- **Src Layouts**: Detect imports in src layouts by default
- **Pytest Rules**: Default to omitting decorator parentheses

### Performance Improvements
- **Faster Parsing**: Improved Python parser performance
- **Better Caching**: Enhanced caching for faster subsequent runs
- **Parallel Processing**: Parallel file processing
- **Memory Optimization**: Reduced memory usage for large codebases

### Language Server Features
- **Real-time Linting**: Instant feedback in IDEs
- **Quick Fixes**: Inline code fixes
- **Range Formatting**: Format specific code ranges
- **Import Organization**: Automatic import sorting
- **Configuration Updates**: Dynamic configuration reloading

### Ecosystem Integration
- **Pre-commit Hooks**: Official pre-commit integration
- **VS Code Extension**: Native VS Code support
- **PyCharm Plugin**: JetBrains IDE integration
- **Neovim Support**: LSP integration for Neovim
- **Documentation**: Comprehensive rule documentation