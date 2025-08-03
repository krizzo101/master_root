<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Automation Patterns","description":"Documentation describing automation patterns including pre-commit setup, Makefile commands, and script integration for code quality and automation.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify key automation patterns and their implementations. Focus on extracting structured sections based on the main headings and capture important code blocks that illustrate configuration and usage. Ensure line numbers are accurate and sections do not overlap. Provide clear descriptions for each section and key element to facilitate navigation and understanding of automation setup and integration.","sections":[{"name":"Automation Patterns Overview","description":"Introduction and main title of the document presenting the overall topic of automation patterns.","line_start":7,"line_end":8},{"name":"Pre-commit Setup","description":"Details the configuration for pre-commit hooks using a YAML snippet to automate code fixes and formatting.","line_start":9,"line_end":16},{"name":"Makefile Commands","description":"Lists common Makefile commands used for formatting, linting, and running all checks with example bash commands.","line_start":17,"line_end":23},{"name":"Script Integration","description":"Provides a Python class example illustrating how to integrate automation scripts for running quality checks programmatically.","line_start":24,"line_end":31}],"key_elements":[{"name":"Pre-commit YAML Configuration","description":"YAML code block defining pre-commit hooks for the ruff tool to automatically fix and format code.","line":10},{"name":"Makefile Command Examples","description":"Bash code block showing commands to format code, lint, and run all checks using Makefile targets.","line":18},{"name":"Python Script Integration Example","description":"Python code block demonstrating a DevTools class with a method stub for running all quality checks.","line":25}]}
-->
<!-- FILE_MAP_END -->

# Automation Patterns

## Pre-commit Setup
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Makefile Commands
```bash
make format      # Format code
make lint        # Lint code  
make all         # Complete check
```

## Script Integration
```python
class DevTools:
    def run_all_checks(self) -> bool:
        # Quality pipeline implementation
        pass
```
