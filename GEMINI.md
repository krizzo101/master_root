# Gemini Project: OPSVI Master Workspace

## Project Overview

This repository, "opsvi-master," is a comprehensive Python-based monorepo with a dual purpose:

1.  **Production-Ready AI Service:** It contains the "Enhanced Research Assistant," a sophisticated RAG (Retrieval-Augmented Generation) service built with FastAPI. This service leverages Qdrant, OpenAI, and Perplexity to provide answers to research queries.
2.  **Advanced AI R&D Platform:** The repository serves as a workspace for developing and orchestrating complex AI agents. This is evident from the numerous documents on agent architecture, orchestration plans, and multi-critic systems.

The entire system is built upon a modular, internal framework of `opsvi-*` libraries (e.g., `opsvi-core`, `opsvi-llm`, `opsvi-rag`), as defined in `pyproject.toml`, indicating a scalable and well-architected platform.

## System Capabilities

This project is designed for serious operational maturity, including:

*   **Observability Stack:** A built-in observability platform featuring Grafana and Tempo can be launched with `just up-obs`.
*   **Persistent Services:** The project is designed to run long-term, automated tasks using `systemd` timers for features like `autosave` and `snapshot`.
*   **Automated Workflows:** The `justfile` is the primary entry point for all tasks, providing a consistent interface for development, testing, and platform management.
*   **Custom Git Tooling:** Includes custom scripts for managing `git worktree`, suggesting a sophisticated branching and development strategy.

## Building and Running

The project uses Docker for containerization and a `justfile` for command automation.

### Key Commands

*   **Run the full demo of the Research Assistant:**
    ```bash
    bash scripts/full_demo.sh
    ```

*   **Run services with Docker Compose:**
    ```bash
    docker compose up --build
    ```
    The API will be available at `http://localhost:8000/docs`.

*   **Using `just` (Recommended):**
    *   `just dev`: Format, lint, and test the code.
    *   `just test`: Run the test suite.
    *   `just up`: Start all Dockerized services (RAG, Observability).
    *   `just down`: Stop all Dockerized services.
    *   `just --list`: See all available commands.

## Development Conventions

*   **Monorepo Management:** `uv` is used to manage the Python dependencies and workspaces.
*   **Code Quality:** A strict suite of tools is used, including `ruff` for linting, `black` for formatting, and `mypy` for type checking.
*   **Testing:** `pytest` is the testing framework. The project also includes `playwright`, suggesting capabilities for browser automation, likely for advanced data gathering or end-to-end testing.
*   **API:** The main application exposes a RESTful API built with FastAPI.