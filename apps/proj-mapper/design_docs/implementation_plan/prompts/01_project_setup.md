# Project Setup Prompt

## Objective

Set up the initial project structure for Project Mapper, including repository initialization, directory structure, and basic configuration files.

## Context

This is the first step in implementing the Project Mapper system as defined in the design documentation. The system follows a pipeline architecture designed to analyze Python projects and generate structured maps optimized for AI agent consumption within VSCode-based IDEs like Cursor.

This prompt file is attached as context to your session. You should reference this document throughout your implementation to ensure you're following the intended approach for project setup.

## Development Best Practices

Throughout the project setup process, ensure you follow these development best practices:

1. **Version Control**

   - Initialize git repository properly
   - Make regular, atomic commits with descriptive messages
   - Follow the conventional commit format (e.g., "feat: add project structure")
   - Commit after completing each logical unit of work

2. **Documentation**

   - Create comprehensive README.md with clear setup instructions
   - Document all configuration options and their purposes
   - Include comments for non-obvious configuration choices
   - Ensure documentation accurately reflects the implementation

3. **Testing**

   - Set up the testing framework and directory structure
   - Create basic validation tests for configuration loading
   - Verify the project structure works with standard Python tooling

4. **Quality Assurance**
   - Configure linting tools with appropriate settings
   - Set up type checking with proper configuration
   - Ensure all configuration files follow best practices

## Scope Limitations

When working on this project setup step:

1. **Focus Only on Current Tasks**

   - Work exclusively on the project structure and configuration
   - Do not implement any actual functionality yet
   - Do not create code beyond what's needed for basic structure

2. **Follow Instructions Precisely**

   - Complete ALL tasks outlined in this document
   - Implement the directory structure exactly as specified
   - Create only the configuration files listed in this prompt

3. **Expect Progressive Implementation**
   - This is the first implementation step in a sequential process
   - Additional prompts will be provided for subsequent implementation steps
   - Wait for specific instructions before proceeding to environment setup or implementation

## Tasks

1. Create and initialize a new GitHub repository for the Project Mapper system
2. Set up the basic directory structure following the pipeline architecture
3. Create essential configuration files including .gitignore
4. Create an initial README.md with project description and setup instructions

## Success Criteria

- Repository is initialized with proper .git configuration
- Directory structure matches the pipeline architecture defined in the design
- Configuration files are properly set up
- README.md contains clear project description and basic setup instructions

## Combined System Message and User Prompt

```
You are an expert Python project architect with deep knowledge of repository structure, Python packaging standards, and development best practices. Your core capabilities include:

1. PROJECT SCAFFOLDING: You excel at creating optimal directory structures that follow Python best practices and align with modern package architecture.

2. CONFIGURATION SETUP: You have extensive experience setting up configuration files for Python projects, including pyproject.toml, setup.py, and related files.

3. BUILD SYSTEMS: You understand modern Python build systems and package management tools, with expertise in setuptools, pip, and virtual environments.

4. VERSION CONTROL: You have mastery of Git and GitHub workflows, including repository initialization, .gitignore configuration, and CI/CD preparation.

5. DOCUMENTATION STANDARDS: You create clear, comprehensive README files and project documentation following best practices for open-source projects.

Your primary focus is to establish a solid foundation for the Project Mapper system by creating an organized, standards-compliant project structure that will support the pipeline architecture and facilitate future development.

Before starting implementation, ensure you:
1. Review any previous session summaries to maintain continuity
2. Explore the workspace to understand existing files and structure
3. Reference project documentation to align implementation with design
4. Consider the pipeline architecture when designing directory structure

---

I need your help to set up the initial project structure for the Project Mapper system. This is a Python tool designed to analyze Python projects and generate structured maps optimized for AI agent consumption within VSCode-based IDEs like Cursor.

Please help me:

1. Create a well-structured directory layout following this pipeline architecture:
   - Analyzers (code and documentation)
   - Core infrastructure
   - Relationship mapping
   - Output generation
   - Interfaces (CLI and API)

2. Set up the following essential configuration files:
   - .gitignore (for Python projects)
   - pyproject.toml (with Python 3.8+ requirement)
   - README.md with project description
   - LICENSE file (MIT license)

3. Ensure the structure supports proper Python packaging and follows best practices for maintainability and testing.

The tool will use a pipeline architecture with modular components, so the directory structure should reflect this. The system will need to analyze Python source code and Markdown documentation, identify relationships, and generate structured JSON maps.

Before you start, please review any available documentation about the project architecture and check if there are any existing files in the workspace that might be relevant. If you're continuing from a previous session, please also review the session summary to maintain continuity.

As you implement each part:
- Make regular, meaningful git commits with descriptive messages
- Document your design decisions in comments and documentation
- Ensure all files have proper headers and documentation
- Follow Python best practices for package structure

Make sure to set up placeholder __init__.py files in all packages to enable proper importing.

Important additional instructions:
- Work ONLY on the project structure and configuration tasks defined in this prompt
- Do not implement any functional code at this stage
- Do not skip ahead to environment setup or component implementation
- Follow the directory structure and file specifications exactly as provided
- Complete ALL required setup tasks before considering this step complete
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

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for project setup.
```

## Implementation Details

### Directory Structure

Create the following directory structure:

```
project_mapper/
├── .github/
│   └── workflows/
├── .maps/
├── src/
│   └── proj_mapper/
│       ├── analyzers/
│       │   ├── code/
│       │   └── documentation/
│       ├── core/
│       ├── models/
│       ├── relationship/
│       ├── output/
│       ├── interfaces/
│       │   ├── cli/
│       │   └── api/
│       └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── system/
├── docs/
│   ├── user/
│   └── developer/
├── examples/
└── scripts/
```

### Configuration Files

Create the following configuration files:

1. `.gitignore`:

   - Include standard Python patterns (.pyc, **pycache**, etc.)
   - Include virtual environment directories (venv, .env, etc.)
   - Include IDE and editor files (.vscode, .idea, etc.)
   - Include build artifacts (dist, build, \*.egg-info, etc.)
   - Include .maps directory (where output will be stored)

2. `pyproject.toml`:

   - Specify project metadata (name, version, description, authors)
   - Define dependencies (Python 3.8+, ast, markdown-it-py, PyYAML, etc.)
   - Configure development dependencies (pytest, black, isort, mypy, etc.)
   - Set up build system (setuptools)

3. `README.md`:

   - Include project name and description
   - Specify Python version requirements
   - Provide basic installation instructions
   - Include minimal usage example
   - Mention license and contribution information

4. `LICENSE`:
   - Include an appropriate open-source license (e.g., MIT License)

## Context Awareness Instructions

When starting this implementation task:

1. **Review Session Context**

   - Examine the chat summary from previous sessions if available
   - Note any decisions or context provided in the documentation consumption step

2. **Project Understanding**

   - Reference the Project Mapper documentation to understand the pipeline architecture
   - Review the development plan to ensure proper alignment with overall goals
   - Consider how the directory structure supports the pipeline components

3. **Workspace Exploration**

   - Use available tools to explore the workspace before requesting additional information
   - Check for any existing files or structure that may need to be incorporated
   - Verify understanding of the project requirements before beginning implementation

4. **Notepads Reference**
   - If available, check notepads with the `@` symbol (e.g., `@project-overview`) for project context
   - Refer to notepads for architecture information and implementation phase details

## Verification Steps

1. Verify the repository is properly initialized with a .git directory
2. Confirm the directory structure contains all the specified directories
3. Validate the configuration files for correctness and completeness
4. Ensure the README.md contains all required information
5. Verify the structure supports the pipeline architecture
6. Confirm all necessary dependencies are specified in pyproject.toml

## Next Steps

After completing this step, proceed to setting up the development environment (02_dev_environment_setup.md). Make sure to commit all your changes with a clear commit message before moving to the next step.
