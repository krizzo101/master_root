# Project Organization Enhancement Guide

## Overview

The AgentTask class has been enhanced with project organization fields that help maintain proper separation between project deliverables and orchestrator operations. These fields provide standardized ways to specify where outputs should be created and how they should be organized.

## New Fields

### 1. `project_location` (Optional[str])

Specifies the expected project path where deliverables should be created.

```json
{
  "project_location": "/home/opsvi/master_root/apps/my-awesome-project/"
}
```

**Guidelines:**
- Always use absolute paths
- Follow the pattern `/home/opsvi/master_root/apps/PROJECT-NAME/`
- Use kebab-case for project names (e.g., `my-awesome-project`)

### 2. `deliverable_structure` (Optional[Dict[str, str]])

Defines the expected output file organization with logical names mapped to absolute paths.

```json
{
  "deliverable_structure": {
    "main_deliverable": "/home/opsvi/master_root/apps/my-project/",
    "documentation": "/home/opsvi/master_root/apps/my-project/docs/",
    "source_code": "/home/opsvi/master_root/apps/my-project/src/",
    "configuration": "/home/opsvi/master_root/apps/my-project/config/",
    "tests": "/home/opsvi/master_root/apps/my-project/tests/"
  }
}
```

**Common Structure Keys:**
- `main_deliverable` - Primary project output
- `documentation` - Documentation files
- `source_code` - Source code files
- `configuration` - Configuration files
- `scripts` - Utility scripts
- `tests` - Test files
- `data` - Data files

### 3. `directory_permissions` (Optional[List[str]])

Required `--add-dir` parameters for agent execution.

```json
{
  "directory_permissions": [
    "/home/opsvi/master_root/apps/my-project/",
    "/home/opsvi/master_root/apps/"
  ]
}
```

**Best Practices:**
- Include the specific project directory
- Include the base apps directory for flexibility
- Use absolute paths only
- Order from most specific to most general

### 4. `output_validation` (Optional[Dict[str, Any]])

Validation rules for ensuring outputs are in correct locations.

```json
{
  "output_validation": {
    "required_structure": true,
    "validate_paths": true,
    "check_project_standards": true,
    "required_files": ["README.md", "package.json"],
    "required_directories": ["src", "docs", "tests"],
    "validate_markdown": true,
    "minimum_doc_quality": 8
  }
}
```

**Validation Options:**
- `required_structure` - Enforce directory structure
- `validate_paths` - Check path validity
- `check_project_standards` - Apply project naming conventions
- `required_files` - List of mandatory files
- `required_directories` - List of mandatory directories
- `validate_markdown` - Check markdown syntax
- `check_internal_links` - Validate internal links
- `minimum_doc_quality` - Quality score threshold (1-10)

## Automatic Enhancement

The orchestrator automatically enhances tasks that don't have project organization fields:

### Project Detection

If a task prompt contains phrases like:
- "create a new project"
- "build an application called"
- "implement a project named"
- "initialize a project"

The orchestrator will:

1. **Auto-detect the project name** from the prompt
2. **Clean the name** to follow kebab-case conventions
3. **Suggest a project_location** following standard patterns
4. **Generate a standard deliverable_structure**
5. **Add appropriate directory_permissions**
6. **Set basic output_validation rules**

### Example Enhancement

**Original Task:**
```json
{
  "task_id": "create_app",
  "task_type": "development",
  "prompt": "Create a new project called MyAwesome App with React frontend"
}
```

**Auto-Enhanced Task:**
```json
{
  "task_id": "create_app",
  "task_type": "development",
  "prompt": "Create a new project called MyAwesome App with React frontend",
  "project_location": "/home/opsvi/master_root/apps/my-awesome-app/",
  "deliverable_structure": {
    "main_deliverable": "/home/opsvi/master_root/apps/my-awesome-app/",
    "documentation": "/home/opsvi/master_root/apps/my-awesome-app/docs/",
    "source_code": "/home/opsvi/master_root/apps/my-awesome-app/src/",
    "configuration": "/home/opsvi/master_root/apps/my-awesome-app/config/"
  },
  "directory_permissions": [
    "/home/opsvi/master_root/apps/my-awesome-app/",
    "/home/opsvi/master_root/apps/"
  ],
  "output_validation": {
    "required_structure": true,
    "validate_paths": true,
    "check_project_standards": true
  }
}
```

## Validation and Warnings

The orchestrator validates project organization and provides warnings:

### Directory Standards Validation

- Checks if paths follow the `/apps/PROJECT-NAME/` pattern
- Validates project names use kebab-case
- Warns about writing to inappropriate directories
- Suggests proper project structure

### Example Validation Messages

```
[task_123] Project organization warnings:
  • Task appears to create a new project but lacks 'project_location' field
  • Deliverable path 'config' should be absolute: config/app.json

Suggestions:
  • Add project_location: '/home/opsvi/master_root/apps/my-project/'
  • Use absolute paths starting with '/' for all deliverables
  • Consider adding directory_permissions: ['/home/opsvi/master_root/apps/my-project/']
```

## Backward Compatibility

All new fields are optional with sensible defaults:

- `project_location`: `None`
- `deliverable_structure`: `{}`
- `directory_permissions`: `[]`
- `output_validation`: `{}`

Existing task files will continue to work unchanged.

## Integration with Command Execution

Directory permissions from tasks are automatically applied to agent commands:

```bash
claude --session-id xyz --add-dir /output/dir --add-dir /apps --add-dir /project/path -- "prompt"
```

The orchestrator:
1. Adds standard directories (`output_dir`, `/apps`)
2. Adds task-specific directories from `directory_permissions`
3. Avoids duplicates
4. Maintains proper command structure

## Best Practices

### For Task Authors

1. **Always specify project_location** for tasks that create new projects
2. **Use absolute paths** in all directory references
3. **Follow kebab-case** for project names
4. **Include comprehensive deliverable_structure** for complex projects
5. **Add appropriate directory_permissions** for agent access
6. **Set meaningful output_validation** rules

### For Project Organization

1. **Separate project deliverables** from orchestrator operations
2. **Use standard directory structures**:
   ```
   /apps/project-name/
   ├── README.md
   ├── docs/
   ├── src/
   ├── tests/
   ├── config/
   └── scripts/
   ```
3. **Keep orchestrator files** in `/apps/agent-orchestrator/`
4. **Use descriptive project names** that indicate purpose

### For Validation

1. **Enable structure validation** for important projects
2. **Require key files** like README.md and proper documentation
3. **Check link validity** in documentation
4. **Set appropriate quality thresholds**

## Example Complete Task

See `example_enhanced_task.json` for a comprehensive example showing all features working together to create a complete fullstack web application with proper project organization.

## Migration Guide

### Updating Existing Tasks

To update existing task files:

1. **Add project_location** for tasks that create deliverables
2. **Define deliverable_structure** for organized outputs
3. **Specify directory_permissions** for proper access
4. **Set output_validation** rules for quality assurance

### Testing Changes

Use the test script to validate changes:

```bash
python test_task_organization.py
```

This verifies:
- Backward compatibility with existing tasks
- New fields work correctly
- JSON loading compatibility
- Orchestrator validation functions properly

## Troubleshooting

### Common Issues

1. **Paths not absolute**: Always use full paths starting with `/`
2. **Project name validation**: Use lowercase with hyphens only
3. **Directory permissions missing**: Include both project-specific and general directories
4. **Validation too strict**: Adjust output_validation rules as needed

### Debug Information

The orchestrator logs detailed validation information:

```
DEBUG:generic_orchestrator:AUDIT: task_organization_validation - {...}
```

Check orchestrator logs for validation details and suggestions.
