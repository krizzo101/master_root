# Analysis Subsystem Implementation Prompt

## Objective

Implement the Analysis Subsystem of Project Mapper, including the code analyzer framework, Python analyzer, documentation analyzer, and integration with the pipeline.

## Context

The Analysis Subsystem is responsible for extracting information from code and documentation files. It's a critical component of the pipeline that feeds into the relationship mapping stage. The implementation follows the design specified in the architecture document.

## Tasks

1. Create the analyzer framework with appropriate interfaces
2. Implement the Python code analyzer
3. Develop the Markdown documentation analyzer
4. Integrate analyzers with the pipeline architecture

## Success Criteria

- Analyzers correctly extract structural information from files
- Framework supports extensibility for future language/documentation analyzers
- Python analyzer properly identifies modules, classes, functions, and variables
- Documentation analyzer properly extracts headings, sections, and references
- Components are well-tested with various input types
- Analyzers integrate smoothly with the pipeline

## Implementation Details

### Analyzer Framework

Create an extensible analyzer framework:

- File: `src/proj_mapper/analyzers/base.py`
- Classes:
  - `Analyzer` (abstract base class)
  - `AnalyzerRegistry` (for registering and retrieving analyzers)
  - `AnalyzerFactory` (for creating appropriate analyzers)
- Interface:
  - `can_analyze(file_path: str) -> bool`
  - `analyze(file_path: str, content: str) -> AnalysisResult`
  - `register_analyzer(analyzer_class: Type[Analyzer])`
  - `get_analyzer_for_file(file_path: str) -> Analyzer`

### Python Analyzer

Implement a Python code analyzer:

- Files:
  - `src/proj_mapper/analyzers/code/python.py`
  - `src/proj_mapper/analyzers/code/python_ast_visitor.py`
- Classes:
  - `PythonAnalyzer` (implements Analyzer)
  - `PythonASTVisitor` (extends ast.NodeVisitor)
- Features:
  - Parse Python files using the `ast` module
  - Extract modules, classes, functions, and methods
  - Identify docstrings and comments
  - Detect imports and dependencies
  - Handle various Python syntax constructs

### Markdown Analyzer

Implement a Markdown documentation analyzer:

- File: `src/proj_mapper/analyzers/documentation/markdown.py`
- Classes:
  - `MarkdownAnalyzer` (implements Analyzer)
  - `MarkdownHeadingVisitor` (for processing headings)
- Features:
  - Parse Markdown using markdown-it-py
  - Extract document structure (headings, sections)
  - Identify links and references
  - Detect code blocks and examples
  - Parse metadata from frontmatter (if present)

### Pipeline Integration

Integrate analyzers with the pipeline:

- File: `src/proj_mapper/analyzers/pipeline_stages.py`
- Classes:
  - `CodeAnalysisStage` (implements PipelineStage)
  - `DocumentationAnalysisStage` (implements PipelineStage)
- Functions:
  - `analyze_file(file_path: str, content: str) -> AnalysisResult`
  - `analyze_files(files: List[DiscoveredFile]) -> Dict[str, AnalysisResult]`

### Analysis Results

Create models for analysis results:

- File: `src/proj_mapper/models/analysis.py`
- Classes:
  - `AnalysisResult` (base class for all analysis results)
  - `CodeAnalysisResult` (for code analysis)
  - `DocumentationAnalysisResult` (for documentation analysis)
  - Various element classes (Module, Class, Function, etc.)

## Combined System Message and User Prompt

```
You are an expert Python developer specializing in code analysis, AST processing, and documentation parsing. Your core capabilities include:

1. CODE ANALYSIS: You excel at building parsers and analyzers for Python code, with deep knowledge of the AST module and static analysis techniques.

2. DOCUMENTATION PROCESSING: You have extensive experience parsing and analyzing documentation in formats like Markdown, with expertise in extracting structured information.

3. TEXT PROCESSING: You are skilled at implementing NLP techniques for identifying relationships and extracting meaning from unstructured text.

4. PYTHON EXPERTISE: You have mastery of Python language features, patterns, and best practices, enabling accurate code understanding.

5. PIPELINE INTEGRATION: You understand how to build components that integrate seamlessly into data processing pipelines.

Your primary focus is to implement the analysis subsystem that will extract meaningful information from code and documentation files, providing the foundation for relationship mapping and output generation.

Before starting implementation, ensure you:
1. Review any previous session summaries to maintain continuity
2. Understand how the analysis subsystem interacts with the core subsystem
3. Consider the data models needed to represent analysis results
4. Plan for extensibility to handle different file types and analysis needs

---

I need your help implementing the analysis subsystem for the Project Mapper application. This subsystem needs to extract structured information from both code and documentation files, which will later be used for relationship mapping.

Please implement:

1. Code Analyzer - Extract information from Python source files
   - Parse Python code using the ast module
   - Extract classes, functions, imports, and other relevant elements
   - Analyze docstrings and comments
   - Create structured representations of code elements

2. Documentation Analyzer - Process Markdown documentation
   - Parse Markdown using appropriate libraries
   - Extract headers, sections, code blocks, and other elements
   - Identify references to code elements
   - Create structured representations of documentation elements

3. Analysis Result Models - Define data structures for analysis results
   - Create models for code elements (functions, classes, etc.)
   - Create models for documentation elements (sections, references, etc.)
   - Include metadata and relationships
   - Ensure serialization capabilities

Both analyzers should integrate with the Pipeline Coordinator from the core subsystem and implement the appropriate interfaces.

As you implement each component:
- Make regular, meaningful git commits with descriptive messages
- Document all classes and methods with detailed docstrings
- Write comprehensive unit tests for each component
- Follow the project's established code quality standards

Important additional instructions:
- Work ONLY on the analysis subsystem components defined in this prompt
- Do not implement relationship mapping or output generation functionality
- Do not skip ahead to future implementation steps
- Implement components exactly as specified in this prompt
- Complete ALL required implementation tasks before considering this step complete
- Additional prompts will guide you through subsequent implementation steps

- Apply systematic reasoning methodologies:
  - Tree of Thought (ToT) for exploring multiple solution paths
  - Chain of Thought (CoT) for step-by-step reasoning
  - Self-refinement for iterative improvement

- Leverage web search to obtain current information on all relevant technologies and concepts

- Prioritize thoroughness and quality over speed:
  - Consider problems deeply before implementing solutions
  - Validate approaches against requirements
  - Verify correctness at each implementation stage

- Follow proper development practices:
  - Commit changes frequently with descriptive messages
  - Ensure all modifications are committed before completing tasks

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for analysis subsystem implementation.
```

## Verification Steps

1. Verify analyzer framework correctly registers and retrieves analyzers
2. Test Python analyzer with various Python files and constructs
3. Test Markdown analyzer with various documentation patterns
4. Confirm analyzers correctly integrate with the pipeline
5. Validate that analysis results contain all required information
6. Measure performance with larger files to ensure efficiency

## Next Steps

After completing this step, proceed to implementing the relationship mapping subsystem (05_relationship_mapping_implementation.md).

## Development Best Practices

Throughout the analysis subsystem implementation, ensure you follow these best practices:

1. **Version Control**

   - Make regular, atomic commits with descriptive messages
   - Commit after implementing each logical component or feature
   - Follow the conventional commit format (e.g., "feat: implement Code Analyzer class")
   - Push changes to the remote repository regularly

2. **Documentation**

   - Write comprehensive docstrings for all classes and methods
   - Include type hints for all functions and methods
   - Document the purpose, parameters, and return values of each function
   - Update README.md with information about the analysis subsystem

3. **Testing**

   - Write unit tests for each component as you implement it
   - Achieve high test coverage for all functionality
   - Test edge cases and error conditions
   - Implement integration tests for component interactions

4. **Code Quality**
   - Follow PEP 8 style guidelines and project-specific standards
   - Run linters and formatters before committing changes
   - Use meaningful variable and function names
   - Break down complex functions into smaller, more manageable pieces

## Scope Limitations

When working on this analysis subsystem implementation step:

1. **Focus Only on Current Tasks**

   - Work exclusively on the analysis subsystem components
   - Do not implement relationship mapping, output generation, or user interfaces
   - Do not modify core subsystem components beyond what's needed for integration

2. **Follow Instructions Precisely**

   - Complete ALL tasks outlined in this document
   - Implement components exactly as specified
   - Create only the files and classes listed in this prompt

3. **Expect Progressive Implementation**
   - This is the fourth implementation step in a sequential process
   - Additional prompts will be provided for subsequent implementation steps
   - Wait for specific instructions before proceeding to relationship mapping implementation

## Tasks

1. Implement the Code Analyzer component
2. Create the Documentation Analyzer
3. Develop data models for analysis results
4. Integrate with core subsystem components
