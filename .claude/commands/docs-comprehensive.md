# Generate Comprehensive Documentation

Create or update project documentation based on current codebase.

## Documentation to Generate

### 1. **README.md** (if needed)
- Project name and description
- Installation instructions
- Quick start guide
- Usage examples
- API reference (key functions/classes)
- Configuration options
- Contributing guidelines
- License information

### 2. **API Documentation**
For each public module/class/function:
- Purpose and behavior
- Parameters with types and descriptions
- Return values
- Exceptions/errors that may be raised
- Usage examples
- Related functions/methods

### 3. **Architecture Documentation** (`docs/ARCHITECTURE.md`)
- System overview and design decisions
- Component relationships (with diagrams if applicable)
- Data flow
- Key design patterns used
- Technology choices and rationale

### 4. **Development Guide** (`docs/DEVELOPMENT.md`)
- Development environment setup
- Running tests
- Code style guidelines
- Debugging tips
- Common tasks and how to do them
- Troubleshooting guide

### 5. **Inline Documentation**
Review and improve:
- Docstrings/JSDoc comments
- Complex algorithm explanations
- TODO/FIXME comments
- Type hints/annotations

## Process

1. Scan codebase structure
2. Identify undocumented or poorly documented areas
3. Generate missing documentation
4. Update outdated documentation
5. Ensure consistency across all docs
6. Add code examples where helpful
7. Include diagrams for complex relationships (use Mermaid)

## Quality Checks
- ✓ All public APIs documented
- ✓ Examples are runnable
- ✓ No broken internal links
- ✓ Terminology is consistent
- ✓ Newcomer-friendly language
- ✓ Version/compatibility info included

Output location: Update existing docs in place or create in `docs/` directory
