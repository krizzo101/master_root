#!/usr/bin/env python3
"""
scaffold_all_shared_libs.py

Create all remaining OPSVI shared-libraries in one shot.

Key features
------------
• Idempotent – safe to run repeatedly (use --force to overwrite)
• DRY – symlinks shared utilities (falls back to copy on platforms
  without symlink support)
• Fully typed, logged, and production-ready
• Requires Python ≥ 3.10

Example
-------
python scaffold_all_shared_libs.py               # create libraries
python scaffold_all_shared_libs.py --dry-run     # preview only
python scaffold_all_shared_libs.py --force -vv   # overwrite, verbose
python scaffold_all_shared_libs.py --help
"""
from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path
from textwrap import dedent

# --------------------------------------------------------------------------- #
# Global configuration
# --------------------------------------------------------------------------- #

LOG = logging.getLogger("scaffold_libs")
DEFAULT_ENCODING = "utf-8"

# Libraries to create (hyphen-case names mapped to short description)
LIB_SPECS: dict[str, str] = {
    "opsvi-fs": "File-system and storage management",
    "opsvi-web": "Web interface and API framework",
    "opsvi-data": "Data management and database access",
    "opsvi-auth": "Authentication and authorization",
    "opsvi-orchestration": "Advanced orchestration engine",
    "opsvi-memory": "Memory and state management",
    "opsvi-communication": "Inter-agent communication",
    "opsvi-interfaces": "Multi-interface management",
    "opsvi-pipeline": "Data-pipeline management",
    "opsvi-deploy": "Deployment and operations",
    "opsvi-monitoring": "Advanced monitoring and observability",
    "opsvi-security": "Advanced security and threat-detection",
}

# Where the reusable logging implementation lives
SHARED_LOGGING_SRC = (
    Path("libs")
    / "opsvi-foundation"
    / "opsvi_foundation"
    / "observability"
    / "logging.py"
)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #


def snake_case_from_kebab(name: str) -> str:
    """
    Convert *name* from kebab-case (e.g. ``opsvi-fs``)
    to snake_case (e.g. ``opsvi_fs``).
    """
    return name.replace("-", "_")


def write_text(path: Path, content: str, *, force: bool) -> None:
    """
    Write *content* to *path* in UTF-8 unless the file already exists
    and *force* is False.
    """
    if path.exists() and not force:
        LOG.debug("Skip existing file %s", path)
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).lstrip(), encoding=DEFAULT_ENCODING)
    LOG.info("Wrote %s", path)


def create_symlink(target: Path, link_path: Path, *, force: bool) -> None:
    """
    Create a symlink *link_path* → *target*.  If the platform or user
    permissions prevent symlink creation, fall back to copying *target*.

    If *force* is True, any existing path at *link_path* is removed first.
    """
    if link_path.exists():
        if force:
            if link_path.is_symlink() or link_path.is_file():
                link_path.unlink()
            else:  # directory
                shutil.rmtree(link_path)
        else:
            LOG.debug("Skip existing path %s", link_path)
            return

    link_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        link_path.symlink_to(target)
        LOG.info("Symlink %s → %s", link_path, target)
    except (OSError, NotImplementedError):
        # Fallback: deep copy
        try:
            if target.is_dir():
                shutil.copytree(target, link_path)
            else:
                shutil.copy2(target, link_path)
            LOG.warning(
                "Symlink not supported – copied %s to %s instead", target, link_path
            )
        except Exception as exc:  # pragma: no cover
            LOG.error(
                "Failed to copy %s to %s during symlink fallback: %s",
                target,
                link_path,
                exc,
                exc_info=True,
            )


# --------------------------------------------------------------------------- #
# Content generators
# --------------------------------------------------------------------------- #


def generate_pyproject(lib_name: str, description: str) -> str:
    """
    Build a minimal ``pyproject.toml`` using Hatchling.
    """
    python_package = snake_case_from_kebab(lib_name)
    return f"""
    [build-system]
    requires = ["hatchling>=1.20"]
    build-backend = "hatchling.build"

    [project]
    name = "{lib_name}"
    version = "0.0.1"
    description = "{description}"
    authors = [{{ name = "OPSVI", email = "opensource@opsvi.dev" }}]
    readme = "README.md"
    requires-python = ">=3.10"
    dependencies = ["opsvi-foundation>=0.1.0"]

    [project.urls]
    Homepage = "https://github.com/opsvi/master-workspace"
    Documentation = "https://github.com/opsvi/master-workspace/tree/main/libs/{lib_name}"
    Source = "https://github.com/opsvi/master-workspace"

    [tool.hatch.build.targets.wheel]
    packages = ["{python_package}"]
    """


def generate_readme(lib_name: str, description: str) -> str:
    """
    Produce a simple README.md.
    """
    return f"""
    # {lib_name}

    {description}

    This package is part of the **OPSVI** library ecosystem.

    ## Installation

    ```bash
    pip install '{lib_name} @ git+https://github.com/opsvi/master-workspace.git#subdirectory=libs/{lib_name}'
    ```

    ## Usage

    ```python
    from {snake_case_from_kebab(lib_name)} import __version__
    print(__version__)
    ```
    """


def generate_init(lib_name: str) -> str:
    """
    Generate ``__init__.py`` with version exposure.
    """
    return f'''
    """Top-level package for {lib_name}."""

    from importlib.metadata import version as _v

    __all__: list[str] = ["__version__"]

    try:
        __version__: str = _v("{lib_name}")
    except Exception:  # pragma: no cover
        __version__ = "0.0.0.dev0"
    '''


def generate_core_stub(lib_name: str) -> str:
    """
    Generate a stubbed ``core.py`` with a dataclass placeholder.
    """
    class_name = snake_case_from_kebab(lib_name).title().replace("_", "")
    return f"""
    \"\"\"Core stubs for {lib_name}.\"\"\"

    from __future__ import annotations

    import logging
    from dataclasses import dataclass

    LOG = logging.getLogger("{lib_name}.core")


    @dataclass(slots=True)
    class Base{class_name}:
        \"\"\"Base class – extend me.\"\"\"

        name: str

        def run(self) -> None:
            \"\"\"Execute the primary action (no-op stub).\"\"\"
            LOG.info("Running %s (stub)", self.name)
    """


def generate_config_stub() -> str:
    """
    Generate a minimal ``config.py`` using Pydantic V2.
    """
    return """
    \"\"\"Package configuration (Pydantic V2 stub).\"\"\"

    from __future__ import annotations

    from pydantic import BaseModel, Field


    class Settings(BaseModel):
        \"\"\"Runtime settings.\"\"\"

        debug: bool = Field(default=False, description="Enable debug logging")

        @property
        def log_level(self) -> str:
            return "DEBUG" if self.debug else "INFO"
    """


def generate_exceptions_stub(lib_name: str) -> str:
    """
    Produce an ``exceptions.py`` with base exception.
    """
    base_exc = snake_case_from_kebab(lib_name).title().replace("_", "")
    return f"""
    \"\"\"Exception hierarchy for {lib_name}.\"\"\"

    class {base_exc}Error(Exception):
        \"\"\"Base exception for {lib_name}.\"\"\"
    """


def generate_test_stub(package_name: str) -> str:
    """
    Produce a trivial pytest test ensuring the package imports.
    """
    return f"""
    \"\"\"Trivial pytest stub for CI wiring.\"\"\"

    from {package_name} import __version__


    def test_version() -> None:
        assert isinstance(__version__, str) and __version__
    """


# --------------------------------------------------------------------------- #
# Library scaffold logic
# --------------------------------------------------------------------------- #


def scaffold_library(
    *,
    libs_root: Path,
    lib_name: str,
    description: str,
    force: bool,
    dry_run: bool,
) -> None:
    """
    Create the on-disk skeleton for *lib_name* under *libs_root*.
    """
    hyphen_name = lib_name
    snake_name = snake_case_from_kebab(hyphen_name)
    lib_dir = libs_root / hyphen_name
    pkg_dir = lib_dir / snake_name
    tests_dir = lib_dir / "tests"

    if dry_run:
        LOG.info("[DRY-RUN] Would scaffold %s", lib_dir)
        return

    LOG.info("Scaffolding %s", lib_name)

    # Directories
    for directory in (pkg_dir, tests_dir):
        directory.mkdir(parents=True, exist_ok=True)

    # Content files
    write_text(
        lib_dir / "pyproject.toml",
        generate_pyproject(lib_name, description),
        force=force,
    )
    write_text(
        lib_dir / "README.md",
        generate_readme(lib_name, description),
        force=force,
    )
    write_text(pkg_dir / "__init__.py", generate_init(lib_name), force=force)
    write_text(pkg_dir / "core.py", generate_core_stub(lib_name), force=force)
    write_text(pkg_dir / "config.py", generate_config_stub(), force=force)
    write_text(pkg_dir / "exceptions.py", generate_exceptions_stub(lib_name), force=force)
    write_text(
        tests_dir / f"test_{snake_name}.py",
        generate_test_stub(snake_name),
        force=force,
    )

    # Shared logging symlink
    if SHARED_LOGGING_SRC.exists():
        create_symlink(
            target=SHARED_LOGGING_SRC.resolve(),
            link_path=pkg_dir / "logging.py",
            force=force,
        )
    else:
        LOG.warning("Shared logging module not found at %s", SHARED_LOGGING_SRC)


# --------------------------------------------------------------------------- #
# CLI helpers
# --------------------------------------------------------------------------- #


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scaffold OPSVI shared libraries.")
    parser.add_argument(
        "--libs-root",
        type=Path,
        default=Path("libs"),
        help="Destination root directory (default: ./libs)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files/directories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without touching the filesystem.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (repeat for more detail).",
    )
    return parser


def configure_logging(verbosity: int) -> None:
    """
    Initialise stdout logging based on *verbosity* flag count.
    """
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(levelname)-8s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    configure_logging(args.verbose)

    libs_root: Path = args.libs_root
    if not libs_root.exists():
        if args.dry_run:
            LOG.info("[DRY-RUN] Would create root directory %s", libs_root)
        else:
            libs_root.mkdir(parents=True, exist_ok=True)

    for lib_name, description in LIB_SPECS.items():
        try:
            scaffold_library(
                libs_root=libs_root,
                lib_name=lib_name,
                description=description,
                force=args.force,
                dry_run=args.dry_run,
            )
        except Exception as exc:  # pragma: no cover
            LOG.error("Failed to scaffold %s: %s", lib_name, exc, exc_info=True)

    LOG.info("✅ All requested libraries processed.")


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        sys.stderr.write("Python 3.10 or newer is required.\n")
        sys.exit(1)

    main()
