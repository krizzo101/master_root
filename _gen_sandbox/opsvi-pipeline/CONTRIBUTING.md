# Contributing to opsvi-pipeline

Thank you for considering contributing! Please follow these guidelines:

- Fork the repo and create a feature branch
- Run tests and linters locally
- Write clear commit messages and PR descriptions
- Add tests for new functionality

## Dev Setup

```bash
pip install -e ".[dev]"
pre-commit install
```

## Commands

```bash
ruff check .
black .
mypy .
pytest -q
```
