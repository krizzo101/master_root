# Knowledge Update: Python Workspace Management & Monorepo Setup (Generated 2025-01-15)

## Current State (Last 12+ Months)
- **uv** has emerged as the fastest Python package manager (10-100x faster than pip/poetry)
- **Workspace support** in uv is now mature with full monorepo capabilities
- **pyproject.toml** is the standard for Python project configuration
- **Git worktrees** are recommended for safe parallel development
- **Systemd user services** are preferred over cron for automated tasks

## Best Practices & Patterns
- **Workspace Structure**: Use `[tool.uv.workspace]` with `members = ["libs/*", "apps/*"]`
- **Dependency Management**: Use `[tool.uv.sources]` with `workspace = true` for local packages
- **Build Backend**: Prefer `uv_build` for pure Python projects
- **Git Safety**: Never force push to protected branches, use worktrees for experiments
- **Automation**: Use systemd user services for autosave, systemd timers for snapshots

## Tools & Frameworks
- **uv**: Fast Python package manager with workspace support
- **hatchling**: Recommended build backend for libraries
- **uv_build**: Fast build backend for pure Python projects
- **Qdrant**: Vector database for RAG systems
- **Tempo + Grafana**: Observability stack
- **OpenTelemetry**: Standard for observability

## Implementation Guidance
- **Monorepo Structure**: apps/, libs/, platform/, tools/, scripts/
- **Workspace Members**: Define in root pyproject.toml with glob patterns
- **Local Dependencies**: Use `workspace = true` in tool.uv.sources
- **Git Workflow**: MAIN (protected) + AUTOSAVE (never deleted) branches
- **Safety Scripts**: Autosave every 10min, snapshots every 12h

## Limitations & Considerations
- **uv** requires Python 3.8+ for workspace support
- **Git worktrees** need careful cleanup to avoid disk space issues
- **Systemd services** require user session management
- **MCP registry** needs environment variable configuration
- **Observability stack** requires Docker Compose setup