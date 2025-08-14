# Repository Guidelines

## Project Structure & Module Organization
- Source packages: `libs/opsvi-*/*` (e.g., `libs/opsvi-core/opsvi_core`).
- Applications: `apps/*` (e.g., `apps/auto-forge-factory`, `apps/proj-mapper`).
- Shared modules: `src/*` (core adapters, utils, schemas).
- Agents and prompts: `agents/`, `docs/` for design/specs.
- Platform services: `platform/{observability,rag,mcp}`.
- Tests: first-party smoke tests in `tests/smoke`; package tests in `libs/**/tests` and some apps.

## Build, Test, and Development Commands
- Install deps: `just sync` (uses `uv`).
- Format: `just fmt` (ruff format + black).
- Lint/Type-check: `just lint` (ruff + mypy).
- Tests (smoke by default): `just test`.
- Coverage HTML: `just test-cov` (outputs `htmlcov/`).
- All-in-one dev loop: `just dev`.
- Build packages: `just build`.
- Security scan: `just security` (bandit).
- Start platform: `just up` / stop: `just down`.

## Coding Style & Naming Conventions
- Language: Python ≥ 3.10; line length 88; 4-space indent.
- Formatters/Linters: ruff, black; type checking via mypy (strict settings).
- Quotes: prefer double quotes (ruff format).
- Packages: library dirs use hyphen (e.g., `opsvi-core`), Python modules use snake case (e.g., `opsvi_core`).
- Keep public APIs typed; avoid untyped defs/decorators per mypy config.

## Testing Guidelines
- Default discovery targets `tests/smoke` to keep a green baseline.
- To run a specific package’s tests: `uv run pytest libs/opsvi-core/tests -q`.
- Test naming: files `test_*.py`, classes `Test*`, functions `test_*`.
- Marks: `unit`, `integration`, `slow` (enable with `-m`).
- Coverage focuses on `libs` and `apps`; exclude generated and cache directories.

## Commit & Pull Request Guidelines
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `chore(scope): ...`.
- PRs must include: clear summary, linked issues, rationale, and test evidence (logs or `htmlcov` screenshot for significant changes).
- Run `just dev` and `just hooks` (pre-commit) before pushing.

## Security & Configuration
- Never commit secrets; use `.env` and reference `.env.example`.
- Containerized stacks via `docker-compose` under `platform/*` (grafana/qdrant/etc.).
- Validate third-party code and generated artifacts; avoid `.j2` references in `libs/` (enforced by pre-commit).
