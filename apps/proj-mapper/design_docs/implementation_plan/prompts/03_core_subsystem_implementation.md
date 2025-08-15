# Core Subsystem Implementation Prompt

## Objective

Implement the core subsystem of Project Mapper, including the Project Manager, Pipeline Coordinator, File Discovery module, and core data models.

## Context

The core subsystem serves as the foundation for the entire Project Mapper application. It provides the central infrastructure that coordinates all other components and manages the overall workflow of the system.

This prompt file is attached as context to your session. You should reference this document throughout your implementation to ensure you're following the intended approach for core subsystem implementation.

## Development Best Practices

Throughout the core subsystem implementation, ensure you follow these best practices:

1. **Version Control**

   - Make regular, atomic commits with descriptive messages
   - Commit after implementing each logical component or feature
   - Follow the conventional commit format (e.g., "feat: implement Project Manager class")
   - Push changes to the remote repository regularly

2. **Documentation**

   - Write comprehensive docstrings for all classes and methods
   - Include type hints for all functions and methods
   - Document the purpose, parameters, and return values of each function
   - Update README.md with information about the core subsystem

3. **Testing**

   - Write unit tests for each component as you implement it
   - Achieve high test coverage for all core functionality
   - Test edge cases and error conditions
   - Implement integration tests for component interactions

4. **Code Quality**
   - Follow PEP 8 style guidelines and project-specific standards
   - Run linters and formatters before committing changes
   - Use meaningful variable and function names
   - Break down complex functions into smaller, more manageable pieces

## Scope Limitations

When working on this core subsystem implementation step:

1. **Focus Only on Current Tasks**

   - Work exclusively on the core subsystem components
   - Do not implement analyzers, relationship mapping, or output generation
   - Do not create interfaces, CLI, or web components

2. **Follow Instructions Precisely**

   - Complete ALL tasks outlined in this document
   - Implement components exactly as specified
   - Create only the files and classes listed in this prompt

3. **Expect Progressive Implementation**
   - This is the third implementation step in a sequential process
   - Additional prompts will be provided for subsequent implementation steps
   - Wait for specific instructions before proceeding to analysis subsystem implementation

## Tasks

1. Implement the Project Manager component
2. Create the Pipeline Coordinator
3. Develop the File Discovery module
4. Implement the Configuration subsystem
5. Create common data models and utilities

## Success Criteria

- All core components are implemented with appropriate interfaces
- Components follow the pipeline architecture
- Core functionality is properly tested
- Configuration handling works with multiple sources
- Data models accurately represent project structure

## Combined System Message and User Prompt

```
You are an expert Python software architect specializing in building robust, modular systems with a focus on pipeline architectures and data processing. Your core capabilities include:

1. ARCHITECTURE DESIGN: You excel at designing clean, maintainable software architectures with clear component boundaries and well-defined interfaces.

2. PIPELINE SYSTEMS: You have extensive experience building data processing pipelines with stages that can be composed and configured flexibly.

3. PYTHON EXPERTISE: You are highly proficient in modern Python practices including type hints, design patterns, and object-oriented programming.

4. TESTING STRATEGIES: You understand how to design testable components and implement comprehensive test suites for complex systems.

5. CONFIGURATION MANAGEMENT: You are skilled at creating flexible configuration systems that support multiple sources and validation.

Your primary focus is to implement the core subsystem that will serve as the foundation for the entire Project Mapper application, ensuring it is well-designed, maintainable, and properly tested.

Before starting implementation, ensure you:
1. Review any previous session summaries to maintain continuity
2. Understand the pipeline architecture and how components interact
3. Consider the extensibility requirements for future components
4. Plan for proper error handling and logging throughout the system

---

I need your help implementing the core subsystem for the Project Mapper application. This is the foundation that all other components will build upon. The core subsystem needs to include:

1. Project Manager - The main entry point and coordinator for the application
2. Pipeline Coordinator - Manages the sequence of processing stages
3. File Discovery - Finds and categorizes files in a project
4. Configuration System - Handles settings from multiple sources
5. Data Models - Core data structures used throughout the system

For each component:
- Create the necessary files with proper Python package structure
- Implement classes with appropriate interfaces and type hints
- Write comprehensive docstrings explaining functionality
- Implement proper error handling and logging
- Include unit tests for each component

The system follows a pipeline architecture, so the Pipeline Coordinator should support registering pipeline stages and passing data between them. The File Discovery should efficiently find Python and Markdown files using glob patterns, while respecting exclude patterns for typical directories like venv and __pycache__.

For data models, use Pydantic to create models that represent project structure, files, code elements, and their relationships. These models should support serialization to/from JSON and include proper type validation.

As you implement each component:
- Make regular, meaningful git commits with descriptive messages
- Document all classes and methods with detailed docstrings
- Write unit tests for each component as you implement it
- Follow PEP 8 style guidelines and project-specific standards
- Run linters and formatters before committing

The code should comply with our previously established code quality standards, be well-tested, and follow the design outlined in our architecture documentation.

Important additional instructions:
- Work ONLY on the core subsystem components defined in this prompt
- Do not implement any analyzers, relationship mapping, or output generation
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

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for core subsystem implementation.
```

## Implementation Details

### Project Manager

The Project Manager should:

1. Serve as the main entry point to the system
2. Coordinate the analysis process
3. Manage configuration and settings
4. Handle project-level operations

Implementation:

- File: `src/proj_mapper/core/project_manager.py`
- Interface:
  - `__init__(config: Dict[str, Any] = None)`
  - `analyze_project(project_path: str) -> ProjectMap`
  - `update_maps(project_path: str, incremental: bool = True) -> ProjectMap`
  - `get_configuration() -> Configuration`

### Pipeline Coordinator

The Pipeline Coordinator should:

1. Manage the sequence of pipeline stages
2. Pass data between stages
3. Handle pipeline errors and exceptions
4. Monitor pipeline progress

Implementation:

- File: `src/proj_mapper/core/pipeline.py`
- Classes:
  - `PipelineStage` (abstract base class)
  - `Pipeline` (coordinates stages)
  - `PipelineContext` (holds pipeline state)
- Interface:
  - `add_stage(stage: PipelineStage)`
  - `run(context: PipelineContext) -> Any`

### File Discovery

The File Discovery module should:

1. Find relevant files in a project
2. Apply include/exclude patterns
3. Categorize files by type
4. Handle directory traversal efficiently

Implementation:

- File: `src/proj_mapper/core/file_discovery.py`
- Interface:
  - `discover_files(project_path: str, include_patterns: List[str], exclude_patterns: List[str]) -> List[DiscoveredFile]`
  - `categorize_files(files: List[DiscoveredFile]) -> Dict[str, List[DiscoveredFile]]`

### Configuration Subsystem

The Configuration subsystem should:

1. Load configuration from multiple sources
2. Validate configuration values
3. Provide defaults for missing values
4. Support configuration access by components

Implementation:

- Files:
  - `src/proj_mapper/core/config.py`
  - `src/proj_mapper/core/config_schema.py`
- Classes:
  - `Configuration` (main configuration class)
  - `ConfigurationSource` (abstract base class)
  - `FileConfigurationSource` (for file-based config)
  - `EnvironmentConfigurationSource` (for env vars)
  - `DefaultConfigurationSource` (for defaults)

### Data Models

Create common data models for:

1. Project structure
2. File information
3. Code elements
4. Documentation elements
5. Relationship types

Implementation:

- Directory: `src/proj_mapper/models/`
- Files:
  - `__init__.py`
  - `project.py` (project structure)
  - `file.py` (file information)
  - `code.py` (code elements)
  - `documentation.py` (doc elements)
  - `relationship.py` (relationship types)
- Use dataclasses or Pydantic models
- Include proper type hints
- Add serialization/deserialization support

## Development Workflow

When implementing the core subsystem, follow this workflow:

1. **Component Implementation Order**

   - Start with data models as they are used by other components
   - Then implement the Configuration subsystem
   - Next, create the File Discovery module
   - Implement the Pipeline Coordinator
   - Finally, build the Project Manager

2. **For Each Component**

   - Create test files first (test-driven development)
   - Implement the component to make tests pass
   - Document the component with docstrings
   - Run linters and formatters
   - Commit the changes

3. **Integration Testing**
   - After individual components are implemented, test their interactions
   - Create integration tests for the complete pipeline
   - Verify that the Project Manager can coordinate all components

## Verification Steps

1. Verify all components are implemented with proper interfaces
2. Run unit tests to confirm correctness of implementation
3. Test interactions between components to ensure they work together
4. Validate configuration loading from multiple sources
5. Verify data models accurately represent project structure
6. Check pipeline flow with sample stages
7. Ensure all code is properly documented with docstrings
8. Verify test coverage meets project standards

## Next Steps

After completing this step, proceed to implementing the analysis subsystem (04_analysis_subsystem_implementation.md). Make sure to commit all your changes with a clear commit message before moving to the next step.
