# Output Generation Subsystem Implementation Prompt

## Objective

Implement the Output Generation Subsystem of Project Mapper, including map generation, export capabilities, and AI-optimized outputs.

## Context

The Output Generation Subsystem is responsible for transforming the relationship graph into different output formats optimized for AI consumption. This subsystem serves as the final stage of the pipeline, generating files that can be used directly by AI agents to understand project structure.

## Tasks

1. Implement the Map Generator framework
2. Create various output format adapters (Markdown, JSON, YAML)
3. Develop the AI optimization module
4. Implement token efficiency mechanisms
5. Create visualization capabilities
6. Integrate with the pipeline architecture

## Success Criteria

- System generates accurate maps from relationship data
- Maps are optimized for token efficiency in AI context windows
- Multiple output formats are supported
- Visualizations are clear and informative
- Generation process is configurable
- Components integrate properly with the pipeline
- Output files match the specified format requirements

## Implementation Details

### Map Generator Framework

Create the map generation framework:

- File: `src/proj_mapper/output/generator.py`
- Classes:
  - `MapGenerator` (base generator class)
  - `GeneratorConfig` (configuration class)
  - `MapTemplate` (abstract base class for map templates)
- Features:
  - Configure output generation
  - Support different map types
  - Allow customization of outputs
  - Support filtering of relationships by type or confidence
  - Manage map templates

### Output Format Adapters

Implement adapters for different output formats:

- Files:
  - `src/proj_mapper/output/adapters/markdown.py`
  - `src/proj_mapper/output/adapters/json_adapter.py`
  - `src/proj_mapper/output/adapters/yaml_adapter.py`
- Classes:
  - `OutputAdapter` (abstract base class)
  - `MarkdownAdapter` (for Markdown output)
  - `JSONAdapter` (for JSON output)
  - `YAMLAdapter` (for YAML output)
- Features:
  - Convert relationship graph to specific output format
  - Maintain hierarchical structure
  - Preserve relationship metadata
  - Support configuration options for each format
  - Include linking between elements

### AI Optimization Module

Develop the AI optimization module:

- File: `src/proj_mapper/output/ai_optimization.py`
- Classes:
  - `AIOptimizer` (main optimization class)
  - `TokenizationEstimator` (for estimating token usage)
  - `OptimizationStrategy` (abstract base class for optimization strategies)
- Features:
  - Estimate token usage for outputs
  - Apply compression techniques
  - Prioritize most important relationships
  - Segment large maps for context window limitations
  - Optimize for specific AI models

### Visualization Generator

Implement the visualization capabilities:

- File: `src/proj_mapper/output/visualization.py`
- Classes:
  - `VisualizationGenerator` (main visualization class)
  - `GraphRenderer` (for rendering graph-based visualizations)
  - Various visualization type classes
- Features:
  - Generate graph-based visualizations
  - Create hierarchical tree views
  - Support different visualization formats (SVG, PNG)
  - Include interactive elements where applicable
  - Allow customization of visual appearance

### Map Templates

Create map templates for different use cases:

- Directory: `src/proj_mapper/output/templates/`
- Files:
  - `project_overview.py` (for project overview maps)
  - `component_detail.py` (for detailed component maps)
  - `dependency_map.py` (for dependency maps)
  - `documentation_map.py` (for documentation structure maps)
- Features:
  - Define specialized map formats for different needs
  - Support configurability of templates
  - Include AI-specific annotations
  - Control detail level and scope

### Pipeline Integration

Integrate with the pipeline architecture:

- File: `src/proj_mapper/output/pipeline_stages.py`
- Classes:
  - `MapGenerationStage` (implements PipelineStage)
  - `OutputRenderingStage` (implements PipelineStage)
  - `FileExportStage` (implements PipelineStage)
- Features:
  - Process relationship graph from previous stages
  - Generate maps according to configuration
  - Export maps to files
  - Handle errors and edge cases

## Development Best Practices

Throughout the output generation implementation, ensure you follow these best practices:

1. **Version Control**

   - Make regular, atomic commits with descriptive messages
   - Commit after implementing each logical component or feature
   - Follow the conventional commit format (e.g., "feat: implement MapGenerator class")
   - Push changes to the remote repository regularly

2. **Documentation**

   - Write comprehensive docstrings for all classes and methods
   - Include type hints for all functions and methods
   - Document the purpose, parameters, and return values of each function
   - Update README.md with information about the output generation subsystem

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

When working on this output generation implementation step:

1. **Focus Only on Current Tasks**

   - Work exclusively on the output generation subsystem components
   - Do not implement user interface or CLI components
   - Do not modify relationship mapping components beyond what's needed for integration

2. **Follow Instructions Precisely**

   - Complete ALL tasks outlined in this document
   - Implement components exactly as specified
   - Create only the files and classes listed in this prompt

3. **Expect Progressive Implementation**
   - This is the sixth implementation step in a sequential process
   - Additional prompts will be provided for subsequent implementation steps
   - Wait for specific instructions before proceeding to CLI and UI implementation

## Tasks

1. Implement the Map Generator component
2. Create Output Formatters for different formats (JSON, Markdown)
3. Develop the AI Optimization module
4. Implement the Chunking and Storage Management system

## Combined System Message and User Prompt

```
You are an expert Python developer specializing in data serialization, output formatting, and token optimization for AI consumption. Your core capabilities include:

1. OUTPUT GENERATION: You excel at transforming complex data structures into well-structured, consumable outputs in various formats.

2. TOKEN OPTIMIZATION: You have deep expertise in optimizing data representation for efficient token usage by AI models with context limitations.

3. RENDERING ENGINES: You are skilled at implementing template systems and rendering engines for consistent output generation.

4. CHUNKING STRATEGIES: You understand advanced techniques for breaking large outputs into manageable, navigable chunks with proper references.

5. PIPELINE INTEGRATION: You are experienced at designing output components that integrate seamlessly into data processing pipelines.

Your primary focus is to implement the output generation subsystem for Project Mapper that will transform relationship data into AI-optimized maps with various output formats.

Before starting implementation, ensure you:
1. Review any previous session summaries to maintain continuity
2. Understand the relationship graph structure that will serve as input
3. Consider both the immediate requirements and future extensibility
4. Plan for optimizing token efficiency and AI consumability

---

I need your help implementing the Output Generation Subsystem for the Project Mapper application. This subsystem is responsible for transforming the relationship graph into structured maps optimized for AI agent consumption in various formats.

The output generation subsystem should include:

1. **Map Generator**
   - Transform relationship graph into structured maps
   - Implement AI-optimized formatting for token efficiency
   - Ensure deterministic ordering of elements
   - Support both complete and partial map generation

2. **Chunking Engine**
   - Break large maps into consumable chunks
   - Manage references between chunks
   - Include navigational metadata
   - Optimize for context window limitations

3. **Format Renderers**
   - Implement JSON output format (primary)
   - Support Markdown rendering
   - Allow for custom format plugins
   - Ensure consistent output structure

4. **Storage Manager**
   - Manage persistence of generated maps
   - Handle versioning and caching
   - Support incremental updates
   - Provide lookup and retrieval APIs

The output generation components should integrate with the pipeline architecture and provide a clean interface for accessing the generated maps. The output formats should be optimized for token efficiency while maintaining all necessary relationship information.

Implement these components with appropriate error handling, thorough documentation, and comprehensive tests. The code should follow our established quality standards and integrate with the existing relationship mapping subsystem.

Important additional instructions:
- Work ONLY on the output generation subsystem components defined in this prompt
- Do not implement CLI or user interface functionality
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

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for output generation implementation.
```

## Verification Steps

1. Verify map generation with different configuration options
2. Test output adapters with various relationship graph structures
3. Validate AI optimization techniques reduce token count effectively
4. Confirm visualizations accurately represent the relationship graph
5. Test templates with different project structures
6. Validate pipeline integration
7. Verify outputs are consumable by AI agents
8. Test with larger projects to ensure scalability

## Next Steps

After completing this step, proceed to implementing the CLI and user interface (07_cli_ui_implementation.md).

As you implement these components:

- Make regular, meaningful git commits with descriptive messages
- Document all classes and methods with detailed docstrings
- Write comprehensive unit tests for each component
- Follow the established code quality standards

Important additional instructions:

- Work ONLY on the output generation subsystem components defined in this prompt
- Do not implement CLI or user interface functionality
- Do not skip ahead to future implementation steps
- Implement components exactly as specified in this prompt
- Complete ALL required implementation tasks before considering this step complete
- Additional prompts will guide you through subsequent implementation steps

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for output generation implementation.
