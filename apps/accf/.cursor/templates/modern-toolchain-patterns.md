<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Modern Toolchain Patterns","description":"Documentation detailing integration examples and performance metrics for the Ruff toolchain within modern development workflows.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document focusing on the hierarchical structure of headings and their content to create logical, non-overlapping sections. Identify and map key elements such as code blocks and performance metrics that are critical for understanding the toolchain patterns. Ensure all line numbers are 1-indexed and precisely reflect the document's layout including blank lines and formatting. Provide clear, descriptive section names and element descriptions to facilitate navigation and comprehension.","sections":[{"name":"Introduction to Modern Toolchain Patterns","description":"Overview and primary heading introducing the document's focus on modern toolchain patterns.","line_start":7,"line_end":8},{"name":"Ruff Integration Examples","description":"Section covering practical examples for integrating the Ruff tool, including configuration and command usage.","line_start":9,"line_end":20},{"name":"Basic Configuration for Ruff","description":"Detailed example of the basic TOML configuration settings for Ruff integration.","line_start":11,"line_end":17},{"name":"Command Patterns for Daily Development","description":"Examples of common command-line usage patterns for Ruff during daily development workflows.","line_start":19,"line_end":22},{"name":"Performance Metrics","description":"Summary of Ruff's performance advantages compared to other tools, highlighting speed and memory usage.","line_start":23,"line_end":28}],"key_elements":[{"name":"TOML Configuration Code Block","description":"Code block showing the basic TOML configuration for Ruff including target version, line length, and source directories.","line":12},{"name":"Bash Command Code Block","description":"Code block demonstrating typical Ruff commands used in daily development for formatting and linting.","line":20},{"name":"Performance Metrics List","description":"Bullet list outlining Ruff's performance benefits such as speed improvements and reduced memory usage.","line":24}]}
-->
<!-- FILE_MAP_END -->

# Modern Toolchain Patterns

## Ruff Integration Examples

### Basic Configuration
```toml
[tool.ruff]
target-version = "py39"
line-length = 88
src = ["src"]
```

### Command Patterns
```bash
# Daily development
ruff format .
ruff check . --fix
```

### Performance Metrics
- Formatting: 100x faster than Black
- Linting: 100x faster than flake8
- Memory usage: 20x less than legacy tools
