# CLI and User Interface Implementation Prompt

## Objective

Implement the Command Line Interface (CLI) and User Interface components for Project Mapper, providing efficient and user-friendly ways to interact with the system.

## Context

The CLI and UI provide the entry points for users to interact with Project Mapper. The CLI offers command-line access for automation and scripting, while the UI provides a more visual and interactive experience. These components build upon the core functionality to provide a complete user experience.

## Tasks

1. Implement the CLI framework and commands
2. Create the configuration file handling
3. Develop the interactive mode
4. Implement progress reporting and logging
5. Create the web-based UI (optional enhancement)
6. Ensure integration with the core subsystems

## Success Criteria

- CLI supports all required commands and options
- Configuration files are correctly loaded and validated
- Progress reporting provides clear feedback on processing
- Error messages are informative and actionable
- Interactive mode provides guidance and accepts user input
- Web UI (if implemented) provides visualization and interaction
- Complete documentation of all commands and options

## Implementation Details

### CLI Framework

Implement the CLI framework:

- File: `src/proj_mapper/cli/main.py`
- Classes:
  - `CLI` (main CLI class)
  - `CommandRegistry` (for registering commands)
  - Various command classes
- Features:
  - Parse command-line arguments
  - Dispatch to appropriate commands
  - Provide help and documentation
  - Support common flags and options
  - Return appropriate exit codes

### Core Commands

Implement the core commands:

- File: `src/proj_mapper/cli/commands.py`
- Commands:
  - `analyze` (analyze a project and generate maps)
  - `config` (manage configuration)
  - `info` (get information about a project)
  - `version` (display version information)
  - `interactive` (start interactive mode)
- Features:
  - Process command-specific arguments
  - Validate inputs
  - Execute appropriate core functionality
  - Format and display results
  - Handle errors gracefully

### Configuration Management

Implement configuration file handling:

- File: `src/proj_mapper/cli/config_handler.py`
- Classes:
  - `ConfigManager` (main configuration class)
  - `ConfigValidator` (for validating configuration)
- Features:
  - Load configuration from files
  - Merge with command-line options
  - Validate configuration
  - Save configuration changes
  - Provide default values

### Progress Reporting

Implement progress reporting and logging:

- File: `src/proj_mapper/cli/progress.py`
- Classes:
  - `ProgressReporter` (main progress reporting class)
  - `LogHandler` (for handling logs)
- Features:
  - Display progress bars for long-running operations
  - Show stage completion status
  - Provide verbose and quiet modes
  - Support logging to files
  - Format output for different terminal types

### Interactive Mode

Implement the interactive mode:

- File: `src/proj_mapper/cli/interactive.py`
- Classes:
  - `InteractiveShell` (main interactive class)
  - `CommandPrompt` (for command prompting)
- Features:
  - Provide a guided experience
  - Offer command completion
  - Support history navigation
  - Interactive configuration
  - Contextual help

### Web UI (Optional)

Implement the web-based UI:

- Directory: `src/proj_mapper/web/`
- Files:
  - `app.py` (main web application)
  - `routes.py` (URL routes)
  - `templates/` (HTML templates)
  - `static/` (static assets)
- Features:
  - Display project structure and maps
  - Interactive graph visualization
  - Configuration management
  - Project analysis triggering
  - Download of generated maps

### Entrypoint Script

Create the main entrypoint script:

- File: `src/proj_mapper/__main__.py`
- Features:
  - Provide main entry point for the package
  - Parse top-level arguments
  - Initialize logging
  - Dispatch to CLI
  - Handle top-level exceptions

## Combined System Message and User Prompt

```
You are an expert Python developer specializing in command-line interfaces, user experience design, and application integration. Your core capabilities include:

1. CLI DESIGN: You excel at creating intuitive, feature-rich command-line interfaces with excellent user experience.

2. ARGUMENT PARSING: You have deep experience implementing robust command argument parsing with proper validation and help text.

3. INTERFACE INTEGRATION: You are skilled at connecting user interfaces to underlying application logic and services.

4. INTERACTIVE FEATURES: You understand how to implement interactive features like progress bars, colorized output, and autocomplete.

5. ERROR HANDLING: You are adept at implementing user-friendly error handling and helpful feedback in command-line tools.

Your primary focus is to implement the command-line interface and optional web UI for Project Mapper, making the powerful underlying functionality accessible to users.

Before starting implementation, ensure you:
1. Review any previous session summaries to maintain continuity
2. Understand the existing subsystems that your interface will invoke
3. Consider both immediate requirements and future extensibility
4. Plan for excellent user experience with helpful feedback and documentation

---

I need your help implementing the Command-Line Interface (CLI) and optional Web UI for the Project Mapper application. These interfaces will allow users to access the functionality of all previously implemented subsystems.

The interface implementation should include:

1. **Command-Line Interface**
   - Create a main CLI entry point
   - Implement subcommands for various operations (analyze, map, list, etc.)
   - Design intuitive argument and option parsing
   - Provide helpful error messages, progress indicators, and colorized output
   - Generate clear help text and usage examples

2. **Configuration Loading**
   - Load configuration from files, environment variables, and CLI arguments
   - Implement configuration validation
   - Support profiles or presets for different use cases
   - Handle default configuration values

3. **Console Output Formatting**
   - Format output based on verbosity levels
   - Support multiple output formats (text, JSON, etc.)
   - Implement colorized output for terminal
   - Show progress for long-running operations

4. **Optional Web Interface**
   - Create a simple Flask-based web interface
   - Implement project upload and processing
   - Display map visualization and navigation
   - Allow configuration of generation options

The interfaces should be user-friendly, well-documented, and provide access to all the core functionality of Project Mapper. They should integrate with the previously implemented subsystems while providing a clean separation between interface and business logic.

Implement these components with appropriate error handling, thorough documentation, and comprehensive tests. The code should follow our established quality standards and provide intuitive access to the underlying functionality.

Important additional instructions:
- Work ONLY on the CLI and UI components defined in this prompt
- Do not implement testing and documentation functionality (next step)
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

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for CLI and UI implementation.
```

## Verification Steps

1. Verify all CLI commands work as expected with various arguments
2. Test configuration loading from different sources
3. Validate progress reporting with long-running operations
4. Test interactive mode functionality
5. Verify error handling and messaging
6. If implemented, test web UI functionality
7. Ensure documentation is complete and accurate
8. Verify integration with core subsystems

## Next Steps

After completing this step, proceed to implementing the testing and documentation (08_testing_documentation_implementation.md).

## Development Best Practices

Throughout the CLI and UI implementation, ensure you follow these best practices:

1. **Version Control**

   - Make regular, atomic commits with descriptive messages
   - Commit after implementing each logical component or feature
   - Follow the conventional commit format (e.g., "feat: implement CLI command structure")
   - Push changes to the remote repository regularly

2. **Documentation**

   - Write comprehensive docstrings for all classes and methods
   - Include type hints for all functions and methods
   - Document the purpose, parameters, and return values of each function
   - Update README.md with information about the CLI and UI components

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

When working on this CLI and UI implementation step:

1. **Focus Only on Current Tasks**

   - Work exclusively on the CLI and UI components
   - Do not modify output generation components beyond what's needed for integration
   - Do not implement testing and documentation components (covered in the next step)

2. **Follow Instructions Precisely**

   - Complete ALL tasks outlined in this document
   - Implement components exactly as specified
   - Create only the files and classes listed in this prompt

3. **Expect Progressive Implementation**
   - This is the seventh implementation step in a sequential process
   - Additional prompts will be provided for subsequent implementation steps
   - Wait for specific instructions before proceeding to testing and documentation implementation

## Tasks

1. Implement the Command Line Interface (CLI)
2. Create the Programmatic API
3. Develop the IDE Integration module (if applicable)
4. Implement the Configuration Interface

As you implement these components:

- Make regular, meaningful git commits with descriptive messages
- Document all classes and methods with detailed docstrings
- Write comprehensive unit tests for each component
- Follow the established code quality standards
- Create helpful help messages for all commands

Important additional instructions:

- Work ONLY on the CLI and UI components defined in this prompt
- Do not implement testing and documentation functionality (next step)
- Do not skip ahead to future implementation steps
- Implement components exactly as specified in this prompt
- Complete ALL required implementation tasks before considering this step complete
- Additional prompts will guide you through subsequent implementation steps

Important: This prompt document has been attached as context to your session. Please reference it throughout your implementation to ensure you're following the intended approach for CLI and UI implementation.
