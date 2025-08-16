# Documentation Consumption Prompt

## Objective

Before beginning implementation work on Project Mapper, analyze and understand the project documentation to gain a comprehensive understanding of the system's purpose, architecture, and implementation requirements.

## Context

Project Mapper is a Python-based tool designed to analyze Python projects and generate structured maps optimized for AI agent consumption within VSCode-based IDEs like Cursor. Before proceeding with implementation, it's critical to understand the overall design, architecture, and requirements.

This prompt file is attached as context to your session. You should reference this document throughout your analysis to ensure you're following the intended approach for documentation consumption.

## Tasks

1. Review the project architecture and design documentation
2. Understand the pipeline-based approach and system components
3. Familiarize yourself with the "by AI, for AI" development paradigm
4. Review the implementation phases and their dependencies
5. Understand the prompt structure and development workflow

## Success Criteria

- Comprehensive understanding of Project Mapper's purpose and capabilities
- Clear grasp of the system architecture and pipeline components
- Understanding of the development approach and implementation phases
- Familiarity with the "by AI, for AI" optimization requirements
- Preparation to begin specific implementation tasks

## Development Best Practices

Throughout the documentation consumption process:

1. **Workspace Exploration**

   - Explore the repository structure to understand existing files and directories
   - Examine any existing documentation thoroughly before proceeding
   - Use search tools to locate relevant documentation files

2. **Documentation**

   - Take notes on key architectural components and their relationships
   - Document any questions or areas needing clarification
   - Organize your understanding in a structured manner

3. **Preparation for Implementation**
   - Identify the development workflow and tool requirements
   - Understand the git workflow to be prepared for proper version control
   - Note testing requirements and quality standards

## Scope Limitations

When working on this documentation consumption step:

1. **Focus Only on Current Tasks**

   - Work exclusively on understanding and analyzing documentation
   - Do not begin implementing any components
   - Do not attempt to design or architect solutions yet

2. **Follow Instructions Precisely**

   - Complete ALL analysis tasks outlined in this document
   - Analyze documentation exactly as specified
   - Focus on understanding rather than implementation

3. **Expect Progressive Implementation**
   - This is the first step in a sequential implementation process
   - Additional prompts will be provided for subsequent implementation steps
   - Wait for specific instructions before proceeding to implementation

## Combined System Message and User Prompt

```
You are an expert AI development agent specializing in Python software architecture, pipeline systems, and AI-optimized development. Your core capabilities include:

1. ARCHITECTURE ANALYSIS: You excel at rapidly analyzing and internalizing software architecture documentation, understanding system components and their relationships.

2. PIPELINE DESIGN: You have deep knowledge of data processing pipelines, with particular expertise in systems that analyze code and documentation.

3. AI OPTIMIZATION: You understand how to design and implement systems that generate outputs optimized for AI consumption, with expertise in token efficiency and structured information.

4. PYTHON ECOSYSTEM: You are highly proficient in Python development practices, libraries, and tools, particularly for static analysis, documentation processing, and pipeline architectures.

5. DOCUMENTATION COMPREHENSION: You can quickly process technical documentation, extracting key requirements, design patterns, and implementation details.

Your primary focus is to rapidly understand the Project Mapper system design to prepare for implementation. You should prioritize identifying:
- The overall pipeline architecture
- Key components and their responsibilities
- Data flows between components
- AI optimization requirements
- Implementation sequence and dependencies

Your analysis should be thorough yet efficient, focusing on actionable insights that will guide implementation rather than theoretical aspects.

---

I need your help to understand the Project Mapper system before beginning implementation. This Python tool is designed to analyze projects and generate maps optimized for AI consumption.

Please help me by:

1. Reviewing the project documentation to understand:
   - The overall architecture and pipeline approach
   - Key components and their responsibilities
   - Data flows between components
   - The "by AI, for AI" optimization requirements
   - Implementation phases and dependencies

2. Focus particularly on:
   - How the pipeline processes code and documentation
   - How relationships are detected and scored
   - How outputs are optimized for AI token efficiency
   - The sequence and dependencies of implementation

This system has a pipeline architecture with analyzers, relationship mapping, and output generation components. It's designed to create structured project maps that help AI agents understand codebases efficiently.

After your analysis, please provide an overview of your understanding of the system and any key insights that will help guide implementation. Also identify any areas where additional clarification might be needed.

Important additional instructions:
- Work ONLY on the documentation analysis tasks defined in this prompt
- Do not begin implementing any components of the system
- Follow the instructions exactly as specified
- Complete ALL required analysis tasks before proceeding
- Additional prompts will guide you through subsequent implementation steps
- Do not skip ahead to implementation or design work

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

Important: This prompt document has been attached as context to your session. Please reference it throughout your analysis to ensure you're following the intended approach for documentation consumption.
```

## Implementation Details

### Documentation Organization

The Project Mapper documentation is organized as follows:

1. **Development Plan** (`design_docs/implementation_plan/development_plan.md`)

   - Overview of the implementation approach
   - Description of implementation phases
   - Dependencies between phases
   - Success criteria and next steps

2. **Implementation Prompts** (`design_docs/implementation_plan/prompts/*.md`)

   - Sequentially numbered prompts for each implementation step
   - Each prompt contains objectives, context, tasks, and success criteria
   - Implementation details for specific components
   - Verification steps and next actions

3. **Design Documentation** (possibly in `design_docs/` directory)
   - System architecture
   - Component specifications
   - Data models and flows
   - Requirements and constraints

### Pipeline Architecture

The Project Mapper follows a pipeline architecture with the following key components:

1. **Core Subsystem**

   - Project Manager (central coordinator)
   - Pipeline Coordinator (manages processing stages)
   - File Discovery (identifies relevant files)
   - Configuration Management (handles settings)

2. **Analysis Subsystem**

   - Code Analyzer (extracts information from code files)
   - Documentation Analyzer (processes documentation files)
   - Analysis result models and storage

3. **Relationship Mapping Subsystem**

   - Relationship Detector (identifies connections)
   - Confidence Scoring (evaluates relationship strength)
   - Cross-Reference Resolver (links code and documentation)
   - Relationship Graph (stores relationship data)

4. **Output Generation Subsystem**

   - Map Generator (creates structured maps)
   - Output Formatters (JSON, Markdown, etc.)
   - AI Optimization (token efficiency and formatting)
   - Chunking and Storage Management

5. **Interfaces**
   - Command Line Interface (CLI)
   - Programmatic API
   - IDE Integration (VSCode/Cursor)

### AI Optimization Focus

As Project Mapper is designed "by AI, for AI," focus on understanding these optimization aspects:

1. **Token Efficiency**

   - How outputs are structured to minimize token usage
   - Deterministic ordering for consistent parsing
   - Schema design for optimal AI consumption

2. **Context Management**

   - How maps are chunked to fit within context windows
   - Cross-references between chunks
   - Context headers and metadata

3. **AI-Friendly Structures**
   - Hierarchical organization of information
   - Relationship representation
   - Confidence scoring for relationships

### Cursor IDE Chat Context Management

When working on Project Mapper in Cursor IDE:

1. **Chat Summaries**

   - Each implementation step will start in a new chat session
   - Previous session summaries will be included as context
   - Always review these summaries to maintain continuity
   - Reference relevant aspects from previous sessions

2. **Notepads**

   - Project information and reusable content stored in notepads
   - Access notepads using the `@` symbol (e.g., `@project-overview`)
   - Use notepads to maintain consistent understanding across sessions
   - Store key architecture diagrams or data models in notepads

3. **Contextual Awareness**
   - Explore the workspace before starting work
   - Reference relevant files from the documentation
   - Maintain awareness of what has been implemented so far
   - Note dependencies on components from previous steps

## Verification Steps

1. Verify understanding of the overall system purpose and architecture
2. Confirm knowledge of the pipeline components and their relationships
3. Understand the implementation phases and their dependencies
4. Recognize the "by AI, for AI" optimization requirements
5. Identify any unclear aspects or potential implementation challenges

## Next Steps

After gaining a comprehensive understanding of the project documentation, proceed to implementing the project setup (01_project_setup.md).

## Notepad Content Recommendations

Create the following notepads in Cursor to maintain consistent project context:

1. **@project-overview**

   ```
   # Project Mapper Overview

   A Python tool designed to analyze projects and generate structured maps optimized for AI agent consumption.

   ## Key Features
   - Analyze Python code and Markdown documentation
   - Detect relationships between code and documentation
   - Generate AI-optimized maps in various formats
   - Support for VSCode/Cursor IDE integration

   ## Pipeline Architecture
   1. Core Subsystem - Project management and coordination
   2. Analysis Subsystem - Code and documentation analysis
   3. Relationship Mapping - Detect and score connections
   4. Output Generation - Create and optimize maps
   5. Interfaces - CLI and programmatic access

   ## Implementation Approach
   - Pipeline-Aligned Development with AI Optimization
   - Each component fully tested before integration
   - Focus on token efficiency and AI consumption
   ```

2. **@implementation-phases**

   ```
   # Project Mapper Implementation Phases

   1. Development Setup
      - Repository structure
      - Environment configuration
      - Testing framework

   2. Core Subsystem
      - Project Manager
      - Pipeline Coordinator
      - File Discovery
      - Configuration

   3. Analysis Subsystem
      - Code Analyzer
      - Documentation Analyzer
      - Pipeline integration

   4. Relationship Mapping
      - Relationship Detector
      - Confidence Scoring
      - Relationship Graph

   5. Output Generation
      - Map Generator
      - Formatters
      - Chunking Engine
      - Storage Manager

   6. Interfaces
      - CLI
      - API
      - IDE Integration

   7. Testing & Validation

   8. Documentation & Release
   ```

3. **@ai-optimization**

   ```
   # AI Optimization Requirements

   ## Token Efficiency
   - Minimize token usage in outputs
   - Use deterministic ordering
   - Optimize schema design

   ## Context Management
   - Chunk maps to fit context windows
   - Use references between chunks
   - Include context headers

   ## AI Consumption Testing
   - Test with AI agents
   - Validate parsing reliability
   - Measure context utilization
   ```
