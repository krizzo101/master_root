# Apps Directory

This directory contains active applications that are ready for development and integration.

## Current Status

- **Empty** - Applications are staged in `../intake/` until ready for active development
- **Git-tracked** - Changes here are committed to the main branch

## Workflow

1. **Staging**: New applications are added to `../intake/` (git-ignored)
2. **Review**: Applications are reviewed and prepared for integration
3. **Activation**: When ready, applications are moved from `intake/` to `apps/`
4. **Development**: Active development and integration work begins

## Structure

```
apps/
├── README.md          # This file
└── [app-name]/        # Active applications (when ready)

intake/                # Staging area (git-ignored)
├── ACCF/              # Staged for future integration
├── asea/              # Staged for future integration  
├── auto_forge/        # Staged for future integration
├── genFileMap/        # Staged for future integration
└── project-intelligence/ # Staged for future integration
```

## Guidelines

- Keep `apps/` clean and focused on active development
- Use `intake/` for staging and preparation
- Commit changes immediately when moving apps from `intake/` to `apps/`
- Follow the established workflow to prevent confusion 