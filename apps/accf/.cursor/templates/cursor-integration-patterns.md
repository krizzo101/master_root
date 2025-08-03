<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Cursor IDE Integration Patterns","description":"Documentation detailing integration patterns for Cursor IDE, including AI model configurations, rule pattern structures, effective AI prompts, and quality integration tools.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document by identifying major thematic sections based on headings and content, ensuring precise line number boundaries. Highlight key elements such as code blocks and lists that illustrate integration patterns and configurations. Structure the output to facilitate easy navigation and comprehension of Cursor IDE integration patterns, focusing on AI model usage, rule patterns, prompt examples, and quality tools integration.","sections":[{"name":"Document Introduction and AI Model Configuration","description":"Introduces the Cursor IDE integration patterns and details AI model configurations with example command lines for different tasks.","line_start":7,"line_end":15},{"name":"Rule Pattern Structure","description":"Describes the structure of rule patterns including triggers, principles, signatures, validation, and integration using a markdown code block.","line_start":16,"line_end":24},{"name":"Effective AI Prompts","description":"Provides example AI prompts in markdown format to guide implementation and refactoring tasks.","line_start":25,"line_end":31},{"name":"Quality Integration Tools","description":"Lists tools integrated for code quality such as Ruff, mypy, pytest, and pre-commit with brief descriptions.","line_start":32,"line_end":38}],"key_elements":[{"name":"AI Model Configuration Code Block","description":"Bash code block showing commands for selecting different AI models tailored to specific tasks like reasoning, context-heavy work, and fast coding.","line":10},{"name":"Rule Pattern Structure Code Block","description":"Markdown code block outlining the components of a rule pattern including triggers, principles, signatures, validation, and integration.","line":17},{"name":"Effective AI Prompts Code Block","description":"Markdown code block listing example AI prompts to implement secure endpoints, refactor functions, and create tests.","line":26},{"name":"Quality Integration List","description":"Bullet list enumerating quality assurance tools integrated into the workflow such as Ruff, mypy, pytest, and pre-commit.","line":33}]}
-->
<!-- FILE_MAP_END -->

# Cursor IDE Integration Patterns

## AI Model Configuration
```bash
# Model selection for different tasks
cursor --model o3-mini              # Reasoning & planning
cursor --model claude-3-5-sonnet-latest    # Context-heavy work
cursor --model gpt-4.1-mini         # Fast coding
```

## Rule Pattern Structure
```markdown
## Pattern Name
**Triggers**: Activation conditions
**Principles**: Core guidelines
**Signatures**: Implementation markers
**Validation**: Success indicators
**Integration**: System connections
```

## Effective AI Prompts
```markdown
"Implement a secure FastAPI endpoint with error handling"
"Refactor this function using modern Python patterns"
"Create comprehensive tests for this implementation"
```

## Quality Integration
- Ruff: Automatic formatting/linting
- mypy: Type checking integration
- pytest: Test runner integration
- pre-commit: Automated quality hooks
