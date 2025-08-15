# Development Environment Setup Prompt

## Objective

Set up the development environment for Project Mapper, including virtual environment, dependencies, and development tools configuration.

## Context

After setting up the basic project structure, we need to configure the development environment with appropriate tools and dependencies to support the implementation of the Project Mapper system.

This prompt file is attached as context to your session. You should reference this document throughout your implementation to ensure you're following the intended approach for development environment setup.

## Development Best Practices

Throughout the development environment setup process, ensure you follow these best practices:

1. **Version Control**

   - Make regular, atomic commits with descriptive messages
   - Commit after setting up each development tool or configuration
   - Follow the conventional commit format (e.g., "chore: set up black configuration")
   - Push changes to the remote repository regularly

2. **Documentation**

   - Document all tool configurations and their purposes
   - Update README.md with development environment setup instructions
   - Include comments for non-obvious configuration choices
   - Document any deviations from standard tool configurations

3. **Testing**

   - Verify that the test framework is properly configured
   - Create a simple test to validate the environment setup
   - Ensure test discovery works correctly
   - Set up coverage reporting

4. **Automation**
   - Create scripts to automate environment setup
   - Ensure scripts work across platforms (Linux, macOS, Windows)
   - Document script usage and parameters
   - Test scripts in a clean environment

## Scope Limitations

When working on this development environment setup step:

1. **Focus Only on Current Tasks**

   - Work exclusively on development environment configuration
   - Do not implement any actual functionality yet
   - Do not write application code or tests for application features

2. **Follow Instructions Precisely**

   - Complete ALL tasks outlined in this document
   - Configure development tools exactly as specified
   - Create only the configuration files and scripts listed in this prompt

3. **Expect Progressive Implementation**
   - This is the second implementation step in a sequential process
   - Additional prompts will be provided for subsequent implementation steps
   - Wait for specific instructions before proceeding to core subsystem implementation

## Tasks

1. Set up a Python virtual environment
2. Install and configure development dependencies
3. Configure code formatting and linting tools
4. Set up pre-commit hooks
5. Create a development environment setup script

## Success Criteria

- Virtual environment is properly configured
- All development dependencies are installed
- Code formatting and linting tools are configured with appropriate settings
- Pre-commit hooks are set up to enforce code quality
- Setup script allows for easy environment replication

## Combined System Message and User Prompt

```
You are an expert Python developer with deep knowledge of development environments, tooling, and best practices. Your core capabilities include:

1. ENVIRONMENT CONFIGURATION: You excel at setting up robust, reproducible development environments using modern Python tools and practices.

2. DEPENDENCY MANAGEMENT: You have extensive experience with Python package management, virtual environments, and dependency resolution.

3. CODE QUALITY TOOLS: You are highly proficient in configuring and using linters, formatters, type checkers, and other code quality tools.

4. AUTOMATION: You create effective scripts and workflows that automate common development tasks and ensure consistency.

5. TESTING FRAMEWORKS: You understand how to set up and configure testing tools for comprehensive test coverage and reliable results.

Your primary focus is to establish a solid development environment for the Project Mapper system that ensures code quality, reproducibility, and developer productivity.

Before starting implementation, ensure you:
1. Review any previous session summaries to maintain continuity
2. Examine the existing project structure established in the previous step
3. Consider the specific requirements of the Project Mapper application
4. Plan for cross-platform compatibility where possible

---

I need your help to set up a robust development environment for the Project Mapper Python project we just initialized. Please help me configure all the necessary development tools and dependencies.

Specifically, I need you to:

1. Create configuration files for the following development tools:
   - Black for code formatting (standard 88 character line length)
   - isort for import sorting (compatible with Black)
   - flake8 for linting
   - mypy for static type checking (in strict mode)
   - pytest for testing

2. Set up pre-commit hooks that enforce our code quality standards

3. Create a setup script (both bash for Linux/Mac and batch for Windows) that will:
   - Create a Python virtual environment
   - Install all dependencies from pyproject.toml
   - Install pre-commit hooks
   - Validate the development environment

The Python project requires Python 3.8+ and will use modern Python practices including type hints. The code should follow PEP 8 style guidelines with Black's modifications.

As you implement each part:
- Make regular, meaningful git commits with descriptive messages after completing each configuration
- Document each tool configuration with comments explaining non-default settings
- Update the README.md with clear instructions for setting up the development environment
- Test configurations to ensure they work as expected

Important additional instructions:
- Work ONLY on the development environment setup tasks defined in this prompt
- Do not implement any application code or functionality at this stage
- Do not skip ahead to core subsystem implementation or other components
- Configure development tools exactly as specified in this prompt
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

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for development environment setup.
```

## Implementation Details

### Virtual Environment

Set up a Python virtual environment using:

- Python 3.8 or higher
- Standard venv module or virtualenv

### Development Dependencies

Install the following development tools:

1. **Testing**:

   - pytest
   - pytest-cov (for coverage reporting)
   - pytest-mock (for mocking)

2. **Code Quality**:

   - black (for code formatting)
   - isort (for import sorting)
   - flake8 (for linting)
   - mypy (for static type checking)

3. **Documentation**:
   - sphinx (for documentation generation)
   - sphinx-rtd-theme (for documentation theming)

### Code Formatting and Linting Configuration

Create configuration files for:

1. **Black**:

   - File: `pyproject.toml` section or `.black`
   - Line length: 88 characters (default)
   - Skip specific directories: `.venv`, `.git`, `__pycache__`

2. **isort**:

   - File: `pyproject.toml` section or `.isort.cfg`
   - Profile: black (for compatibility)
   - Line length: 88 characters

3. **flake8**:

   - File: `.flake8`
   - Max line length: 88 characters (to match black)
   - Ignore specific errors as needed
   - Exclude directories: `.venv`, `.git`, `__pycache__`

4. **mypy**:
   - File: `pyproject.toml` section or `mypy.ini`
   - Python version: 3.8
   - Strict mode: enabled
   - Disallow untyped defs
   - Exclude specific files/directories as needed

### Pre-commit Hooks

Set up pre-commit hooks with:

1. File: `.pre-commit-config.yaml`
2. Configure hooks for:
   - black (formatting)
   - isort (import sorting)
   - flake8 (linting)
   - mypy (type checking)
   - trailing whitespace removal
   - end-of-file fixer

### Setup Script

Create a `scripts/setup_dev_env.sh` (or .bat for Windows) script that:

1. Creates the virtual environment
2. Installs all dependencies
3. Configures pre-commit hooks
4. Validates the setup

## Context Awareness Instructions

When starting this implementation task:

1. **Review Previous Work**

   - Check the project structure created in the previous step
   - Review the dependencies specified in pyproject.toml
   - Understand the Python version requirements

2. **Tool Knowledge**

   - Understand the purpose and configuration options for each development tool
   - Consider tool interactions and compatibility
   - Follow current best practices for each tool

3. **Cross-Platform Awareness**

   - Ensure configurations work across different operating systems
   - Create platform-specific scripts when necessary
   - Test scripts on different platforms if possible

4. **Project Requirements**
   - Consider the specific needs of the Project Mapper application
   - Configure tools to support the pipeline architecture
   - Enable type checking for improved code quality

## Verification Steps

1. Verify the virtual environment is created and activated
2. Confirm all development dependencies are installed correctly
3. Test code formatting tools on sample files
4. Verify pre-commit hooks are installed and functioning
5. Run the setup script and confirm it properly configures the environment
6. Ensure all configurations are compatible with each other
7. Verify that the README.md is updated with setup instructions

## Next Steps

After completing this step, proceed to implementing the core subsystem (03_core_subsystem_implementation.md). Make sure to commit all your changes with a clear commit message before moving to the next step.
