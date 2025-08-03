<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Security Patterns","description":"Documentation outlining security patterns including automated security scanning tools, secure coding practices, and security configuration examples.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by identifying its main sections and subsections based on headings and content themes. Extract key elements such as code blocks and important security concepts. Ensure all line numbers are accurate and sections do not overlap. Provide clear, descriptive section names and descriptions that reflect the document's purpose of guiding secure coding and scanning practices. Highlight code snippets as key elements for quick reference.","sections":[{"name":"Introduction to Security Patterns","description":"Overview and introduction to the concept of security patterns covered in the document.","line_start":7,"line_end":8},{"name":"Automated Security Scanning","description":"Details on automated tools used for security scanning including Bandit, pip-audit, and detect-secrets with example commands.","line_start":9,"line_end":17},{"name":"Secure Coding Patterns","description":"Examples of secure coding practices including environment variable usage and secure token generation with Python code snippets.","line_start":18,"line_end":25},{"name":"Security Configuration","description":"Configuration example for Bandit tool showing directory exclusions and skipped checks in TOML format.","line_start":26,"line_end":32}],"key_elements":[{"name":"Automated Security Scanning Code Block","description":"Bash commands demonstrating usage of Bandit, pip-audit, and detect-secrets for automated security scanning.","line":10},{"name":"Secure Coding Patterns Code Block","description":"Python code illustrating correct usage of environment variables and secure token generation.","line":19},{"name":"Security Configuration Code Block","description":"TOML configuration snippet for Bandit tool specifying directories to exclude and checks to skip.","line":27},{"name":"Correct Environment Variables Concept","description":"Concept demonstrating the correct way to handle environment variables securely in code.","line":20},{"name":"Secure Token Generation Concept","description":"Concept showing how to securely generate tokens using Python's secrets module.","line":24}]}
-->
<!-- FILE_MAP_END -->

# Security Patterns

## Automated Security Scanning
```bash
# Bandit for code vulnerabilities
bandit -r src/ --severity-level high

# pip-audit for dependency vulnerabilities
pip-audit --desc --format=json

# detect-secrets for credential leaks
detect-secrets scan --all-files
```

## Secure Coding Patterns
```python
import os
import secrets

# ✅ CORRECT - Environment variables
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API key required")

# ✅ CORRECT - Secure token generation
token = secrets.token_urlsafe(32)
```

## Security Configuration
```toml
[tool.bandit]
exclude_dirs = ["tests", "archive", ".venv"]
skips = ["B101"]  # Skip assert_used in tests
```
