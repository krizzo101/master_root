import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import Agent


class ResearchAgent(Agent):
    """Specialized agent for research and documentation tasks."""

    def __init__(self, name="ResearchAgent", **kwargs):
        """Initialize ResearchAgent with research-specific capabilities.

        Args:
            name: Name for this agent instance
            **kwargs: Additional arguments (ignored)
        """
        capabilities = [
            "analyze_code",
            "generate_documentation",
            "create_readme",
            "extract_metadata",
            "generate_api_docs",
            "create_changelog",
        ]
        super().__init__(name=name, capabilities=capabilities)
        self.documentation_formats = ["markdown", "rst", "html", "plaintext"]

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research or documentation task.

        Args:
            task: Task dictionary with keys:
                - type: Task type (e.g., 'analyze_code')
                - target: Target code or project to research
                - options: Task-specific parameters

        Returns:
            Dictionary with research results and documentation
        """
        task_type = task.get("type", "")
        target = task.get("target", "")
        options = task.get("options", {})

        result = {"success": False, "content": "", "message": "", "metadata": {}}

        try:
            if task_type == "analyze_code":
                result = self.analyze_code(target, options)
            elif task_type == "generate_documentation":
                result = self.generate_documentation(target, options)
            elif task_type == "create_readme":
                result = self.create_readme(options)
            elif task_type == "extract_metadata":
                result = self.extract_metadata(target)
            elif task_type == "generate_api_docs":
                result = self.generate_api_docs(target, options)
            elif task_type == "create_changelog":
                result = self.create_changelog(options)
            else:
                result["message"] = f"Unsupported task type: {task_type}"
        except Exception as e:
            result["message"] = f"Error executing task: {str(e)}"

        self.log_task(task, result)
        return result

    def analyze_code(self, code: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code and extract insights.

        Args:
            code: Source code to analyze
            options: Analysis options

        Returns:
            Analysis results
        """
        lines = code.splitlines()

        analysis = {
            "total_lines": len(lines),
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "functions": [],
            "classes": [],
            "imports": [],
            "complexity_estimate": "low",
        }

        for line in lines:
            stripped = line.strip()
            if not stripped:
                analysis["blank_lines"] += 1
            elif stripped.startswith("#") or stripped.startswith("//"):
                analysis["comment_lines"] += 1
            else:
                analysis["code_lines"] += 1

                if stripped.startswith("def "):
                    func_name = re.match(r"def\s+(\w+)", stripped)
                    if func_name:
                        analysis["functions"].append(func_name.group(1))
                elif stripped.startswith("class "):
                    class_name = re.match(r"class\s+(\w+)", stripped)
                    if class_name:
                        analysis["classes"].append(class_name.group(1))
                elif stripped.startswith("import ") or stripped.startswith("from "):
                    analysis["imports"].append(stripped)

        if len(analysis["functions"]) > 10 or len(analysis["classes"]) > 5:
            analysis["complexity_estimate"] = "high"
        elif len(analysis["functions"]) > 5 or len(analysis["classes"]) > 2:
            analysis["complexity_estimate"] = "medium"

        summary = f"""Code Analysis Summary:
- Total Lines: {analysis['total_lines']}
- Code Lines: {analysis['code_lines']}
- Comment Lines: {analysis['comment_lines']}
- Functions: {len(analysis['functions'])}
- Classes: {len(analysis['classes'])}
- Complexity: {analysis['complexity_estimate']}"""

        return {
            "success": True,
            "content": summary,
            "message": "Code analyzed successfully",
            "metadata": analysis,
        }

    def generate_documentation(self, code: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate documentation for code.

        Args:
            code: Source code to document
            options: Documentation options (format, style, etc.)

        Returns:
            Generated documentation
        """
        format_type = options.get("format", "markdown")
        title = options.get("title", "Code Documentation")

        functions = re.findall(r"def\s+(\w+)\((.*?)\)", code)
        classes = re.findall(r"class\s+(\w+)", code)

        if format_type == "markdown":
            doc = f"# {title}\n\n"
            doc += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            if classes:
                doc += "## Classes\n\n"
                for cls in classes:
                    doc += f"### {cls}\n"
                    doc += f"Class implementation for {cls}.\n\n"

            if functions:
                doc += "## Functions\n\n"
                for func_name, params in functions:
                    doc += f"### {func_name}\n"
                    doc += f"**Parameters:** {params if params else 'None'}\n\n"
                    doc += f"Function implementation for {func_name}.\n\n"
        elif format_type == "plaintext":
            doc = f"{title}\n{'=' * len(title)}\n\n"
            doc += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            if classes:
                doc += "Classes:\n"
                for cls in classes:
                    doc += f"  - {cls}\n"
                doc += "\n"

            if functions:
                doc += "Functions:\n"
                for func_name, params in functions:
                    doc += f"  - {func_name}({params})\n"
        else:
            doc = f"Documentation format '{format_type}' not fully implemented yet."

        return {
            "success": True,
            "content": doc,
            "message": "Documentation generated successfully",
            "metadata": {
                "format": format_type,
                "functions_documented": len(functions),
                "classes_documented": len(classes),
            },
        }

    def create_readme(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a README file template.

        Args:
            options: README options (project_name, description, etc.)

        Returns:
            README content
        """
        project_name = options.get("project_name", "Project Name")
        description = options.get("description", "Project description goes here.")
        author = options.get("author", "Author Name")
        license_type = options.get("license", "MIT")

        readme = f"""# {project_name}

{description}

## Installation

```bash
# Installation instructions here
pip install {project_name.lower().replace(' ', '-')}
```

## Usage

```python
# Usage example here
from {project_name.lower().replace(' ', '_')} import main

main()
```

## Features

- Feature 1
- Feature 2
- Feature 3

## Requirements

- Python 3.7+
- Additional requirements...

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the {license_type} License.

## Author

{author}

## Acknowledgments

- Thanks to contributors
- Special mentions...

---
Generated by ResearchAgent on {datetime.now().strftime('%Y-%m-%d')}"""

        return {
            "success": True,
            "content": readme,
            "message": "README created successfully",
            "metadata": {
                "sections": [
                    "Installation",
                    "Usage",
                    "Features",
                    "Requirements",
                    "Contributing",
                    "License",
                    "Author",
                    "Acknowledgments",
                ]
            },
        }

    def extract_metadata(self, code: str) -> Dict[str, Any]:
        """Extract metadata from code.

        Args:
            code: Source code to analyze

        Returns:
            Extracted metadata
        """
        metadata = {
            "language": "unknown",
            "dependencies": [],
            "author_comments": [],
            "todos": [],
            "version_info": None,
            "docstrings": [],
        }

        if "import " in code or "from " in code:
            metadata["language"] = "python"
            imports = re.findall(r"(?:import|from)\s+([\w.]+)", code)
            metadata["dependencies"] = list(set(imports))
        elif "require(" in code or "const " in code:
            metadata["language"] = "javascript"
            requires = re.findall(r'require\([\'"](.+?)[\'"]\)', code)
            metadata["dependencies"] = list(set(requires))

        todos = re.findall(r"#\s*TODO:?\s*(.+)", code, re.IGNORECASE)
        metadata["todos"] = todos

        docstrings = re.findall(r'"""(.+?)"""', code, re.DOTALL)
        metadata["docstrings"] = [ds.strip() for ds in docstrings[:5]]

        version = re.search(r'__version__\s*=\s*[\'"](.+?)[\'"]', code)
        if version:
            metadata["version_info"] = version.group(1)

        return {
            "success": True,
            "content": f"Extracted metadata for {metadata['language']} code",
            "message": "Metadata extracted successfully",
            "metadata": metadata,
        }

    def generate_api_docs(self, code: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API documentation.

        Args:
            code: Source code containing API definitions
            options: API documentation options

        Returns:
            API documentation
        """
        api_format = options.get("format", "openapi")
        base_url = options.get("base_url", "http://api.example.com")
        version = options.get("version", "1.0.0")

        endpoints = re.findall(r'@app\.route\([\'"](.+?)[\'"]\)', code)

        if api_format == "openapi":
            api_doc = f"""openapi: 3.0.0
info:
  title: API Documentation
  version: {version}
  description: Auto-generated API documentation

servers:
  - url: {base_url}

paths:"""

            for endpoint in endpoints:
                api_doc += f"""
  {endpoint}:
    get:
      summary: Endpoint for {endpoint}
      responses:
        200:
          description: Successful response
        404:
          description: Not found"""
        else:
            api_doc = f"# API Documentation\n\nVersion: {version}\n\nBase URL: {base_url}\n\n"
            api_doc += "## Endpoints\n\n"
            for endpoint in endpoints:
                api_doc += f"- `GET {endpoint}`\n"

        return {
            "success": True,
            "content": api_doc,
            "message": "API documentation generated successfully",
            "metadata": {"format": api_format, "endpoints_documented": len(endpoints)},
        }

    def create_changelog(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a changelog template.

        Args:
            options: Changelog options (version, changes, etc.)

        Returns:
            Changelog content
        """
        version = options.get("version", "1.0.0")
        changes = options.get("changes", [])
        date = datetime.now().strftime("%Y-%m-%d")

        changelog = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features in development

### Changed
- Updates to existing functionality

### Fixed
- Bug fixes in progress

## [{version}] - {date}

### Added
"""

        if changes:
            for change in changes:
                changelog += f"- {change}\n"
        else:
            changelog += """- Initial release
- Core functionality implemented
- Basic documentation added
"""

        changelog += """
### Changed
- Performance improvements
- Code refactoring

### Fixed
- Initial bug fixes

## [0.1.0] - 2024-01-01

### Added
- Project initialization
- Basic structure setup

---
Generated by ResearchAgent"""

        return {
            "success": True,
            "content": changelog,
            "message": "Changelog created successfully",
            "metadata": {
                "version": version,
                "sections": ["Unreleased", version, "0.1.0"],
            },
        }
