#!/usr/bin/env python
"""
scaffold_all_shared_libs.py

A robust scaffolding utility that materialises a rich, DRY-compliant directory
skeleton for OPSVI shared-library packages.

Key Features
------------
1. Configurable, per-library-type directory and file layouts
2. Automatic generation of stub modules with sensible defaults
3. Symlink support to avoid code duplication across libraries
4. YAML / JSON manifest support for batch generation
5. Comprehensive logging, error handling, and type hints

Example
-------
# Scaffold a single library
python scaffold_all_shared_libs.py --name opsvi-core --type core --output libs

# Scaffold all libraries declared in a manifest
python scaffold_all_shared_libs.py --manifest tooling/lib_manifest.yaml --output libs
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # YAML is optional

###############################################################################
# Logging configuration
###############################################################################

_LOG = logging.getLogger("scaffold")
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(
    logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
_LOG.addHandler(_handler)
_LOG.setLevel(logging.INFO)

###############################################################################
# Template generators
###############################################################################


def _package_init_template(package_name: str) -> str:
    return (
        f'"""Top-level package for {package_name}."""\n\n'
        "from importlib.metadata import version as _version\n\n"
        "__all__ = (\"__version__\",)\n"
        "__version__: str = _version(__name__)\n"
    )


def _base_template(_: str) -> str:
    return (
        '"Base classes and mixins used across the library."\n\n'
        "from __future__ import annotations\n\n\n"
        "class BaseModel:\n"
        '    """A minimal base class – extend as required."""\n\n'
        "    def __repr__(self) -> str:  # pragma: no cover\n"
        '        return f"{self.__class__.__name__}()"\n'
    )


def _types_template(_: str) -> str:
    return (
        '"Common type aliases and protocols to avoid import cycles."\n\n'
        "from __future__ import annotations\n"
        "from typing import Protocol, TypeAlias\n\n"
        'JsonValue: TypeAlias = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]\n'
        'JsonDict: TypeAlias = dict[str, JsonValue]\n\n\n'
        "class SupportsToDict(Protocol):\n"
        '    """Objects that can be converted to a dictionary."""\n\n'
        "    def to_dict(self) -> JsonDict: ...\n"
    )


def _settings_template(package_name: str) -> str:
    return (
        '"Runtime configuration powered by Pydantic v2."\n\n'
        "from __future__ import annotations\n\n"
        "from functools import lru_cache\n\n"
        "from pydantic import Field\n"
        "from pydantic_settings import BaseSettings, SettingsConfigDict\n\n\n"
        "class Settings(BaseSettings):\n"
        '    """Application/runtime settings."""\n\n'
        f'    model_config = SettingsConfigDict(env_prefix="{package_name.upper()}_", extra="ignore")\n\n'
        '    debug: bool = Field(default=False, description="Enable debug mode")\n'
        '    log_level: str = Field(default="INFO", description="Logging level")\n\n'
        "    # Add additional settings here ----------------------------------\n\n"
        "    @classmethod\n"
        "    @lru_cache()\n"
        '    def instance(cls) -> "Settings":\n'
        '        """Return a cached Settings instance."""\n'
        "        return cls()\n\n\n"
        "# Public singleton-style accessor --------------------------------------\n"
        "settings = Settings.instance()\n"
    )


def _exceptions_template(_: str) -> str:
    return (
        '"Custom exceptions for the library."\n\n'
        "class LibraryError(Exception):\n"
        '    """Base exception for all library-specific errors."""\n'
    )


_TEMPLATE_FACTORY: Mapping[str, Callable[[str], str]] = {
    "package": _package_init_template,
    "base_module": _base_template,
    "types_module": _types_template,
    "settings_module": _settings_template,
    "exceptions_module": _exceptions_template,
}

###############################################################################
# Library-type definitions
###############################################################################

DEFAULT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "core": {
        "dirs": (
            "",  # root package directory
            "core",
            "config",
            "exceptions",
            "utils",
            "tests",
        ),
        "files": {
            "__init__.py": "package",
            # Core layer
            "core/__init__.py": "package",
            "core/base.py": "base_module",
            "core/types.py": "types_module",
            # Config & exceptions
            "config/__init__.py": "package",
            "config/settings.py": "settings_module",
            "exceptions/__init__.py": "exceptions_module",
            # Misc
            "utils/__init__.py": "package",
            "tests/__init__.py": "package",
            # Shared logging via symlink
            "logging.py": "symlink:opsvi_foundation/observability/logging.py",
        },
    },
    "rag": {
        "dirs": (
            "",
            "core",
            "config",
            "exceptions",
            "utils",
            "datastores",
            "embeddings",
            "processors",
            "tests",
        ),
        "files": {
            "__init__.py": "package",
            # Re-use generic stubs
            "core/__init__.py": "package",
            "core/base.py": "base_module",
            "core/types.py": "types_module",
            "config/__init__.py": "package",
            "config/settings.py": "settings_module",
            "exceptions/__init__.py": "exceptions_module",
            # Domain-specific placeholders
            "datastores/__init__.py": "package",
            "datastores/base.py": "base_module",
            "embeddings/__init__.py": "package",
            "embeddings/providers.py": "base_module",
            "processors/__init__.py": "package",
            "processors/json.py": "base_module",
            "utils/__init__.py": "package",
            "tests/__init__.py": "package",
            "logging.py": "symlink:opsvi_foundation/observability/logging.py",
        },
    },
    "service": {
        "dirs": (
            "",
            "core",
            "config",
            "exceptions",
            "utils",
            "providers",
            "schemas",
            "tests",
        ),
        "files": {
            "__init__.py": "package",
            "core/__init__.py": "package",
            "core/base.py": "base_module",
            "core/types.py": "types_module",
            "config/__init__.py": "package",
            "config/settings.py": "settings_module",
            "exceptions/__init__.py": "exceptions_module",
            "providers/__init__.py": "package",
            "providers/base.py": "base_module",
            "schemas/__init__.py": "package",
            "schemas/models.py": "base_module",
            "utils/__init__.py": "package",
            "tests/__init__.py": "package",
            "logging.py": "symlink:opsvi_foundation/observability/logging.py",
        },
    },
    "manager": {
        "dirs": (
            "",
            "core",
            "config",
            "exceptions",
            "utils",
            "coordinators",
            "schedulers",
            "tests",
        ),
        "files": {
            "__init__.py": "package",
            "core/__init__.py": "package",
            "core/base.py": "base_module",
            "core/types.py": "types_module",
            "config/__init__.py": "package",
            "config/settings.py": "settings_module",
            "exceptions/__init__.py": "exceptions_module",
            "coordinators/__init__.py": "package",
            "coordinators/base.py": "base_module",
            "schedulers/__init__.py": "package",
            "schedulers/base.py": "base_module",
            "utils/__init__.py": "package",
            "tests/__init__.py": "package",
            "logging.py": "symlink:opsvi_foundation/observability/logging.py",
        },
    },
    # Add additional library-type templates here.
}

###############################################################################
# Scaffolding engine
###############################################################################


class Scaffolder:
    """
    Handles the creation of directories, stub modules, and symlinks for a
    single library.
    """

    def __init__(
        self,
        root_dir: Path,
        library_name: str,
        library_type: str,
        template: Mapping[str, Any],
    ) -> None:
        self.root_dir = root_dir
        self.library_name = library_name.replace("-", "_")
        self.library_type = library_type
        self.template = template
        self.pkg_dir = self.root_dir / self.library_name

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def scaffold(self) -> None:
        """Orchestrate the full scaffolding process."""
        _LOG.info(
            "Scaffolding '%s' (type=%s) at %s",
            self.library_name,
            self.library_type,
            self.pkg_dir,
        )
        self._create_dirs()
        self._create_files()
        _LOG.info("✔ Completed scaffolding for '%s'", self.library_name)

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _create_dirs(self) -> None:
        """Create all directories defined in the template."""
        for rel_dir in self.template["dirs"]:
            path = self.pkg_dir / rel_dir
            path.mkdir(parents=True, exist_ok=True)
            _LOG.debug("Created directory: %s", path)

    def _create_files(self) -> None:
        """Create stub files and symlinks as per template."""
        files: Mapping[str, str] = self.template["files"]
        for rel_path, template_key in files.items():
            path = self.pkg_dir / rel_path

            if str(template_key).startswith("symlink:"):
                target = Path(str(template_key).split("symlink:", 1)[1])
                self._create_symlink(path, target)
            else:
                self._create_stub_file(path, template_key)

    def _create_stub_file(self, path: Path, template_key: str) -> None:
        """Generate a stub file using the relevant template."""
        if path.exists():
            _LOG.debug("File exists, skipping: %s", path)
            return

        generator = _TEMPLATE_FACTORY.get(template_key)
        content = generator(self.library_name) if generator else ""
        if generator is None:
            _LOG.warning("Unknown template key '%s' – creating empty file.", template_key)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{content}\n", encoding="utf-8")
        _LOG.debug("Created file: %s", path)

    def _create_symlink(self, link_path: Path, target: Path) -> None:
        """Attempt to create a symlink; fallback to copy if unsupported."""
        if link_path.exists():
            _LOG.debug("Symlink already exists, skipping: %s", link_path)
            return

        # Resolve target relative to the foundation library
        foundation_target = self.root_dir / "opsvi-foundation" / target
        if not foundation_target.exists():
            _LOG.error("Symlink target does not exist: %s", foundation_target)
            return

        try:
            link_path.symlink_to(foundation_target)
            _LOG.debug("Created symlink: %s → %s", link_path, foundation_target)
        except OSError as exc:
            _LOG.warning("Symlink failed (%s). Falling back to copy. %s", link_path, exc)
            from shutil import copy2

            link_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(foundation_target, link_path)
            _LOG.debug("Copied file instead of symlink: %s", link_path)


###############################################################################
# Manifest utilities
###############################################################################


def _load_manifest(manifest_path: Path) -> Iterable[Mapping[str, str]]:
    """
    Load a JSON or YAML manifest describing libraries to scaffold.

    Expected structure:
    {
      "libs": [
        {"name": "opsvi-core", "type": "core"},
        {"name": "opsvi-rag", "type": "rag"}
      ]
    }
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    text = manifest_path.read_text(encoding="utf-8")
    data: Mapping[str, Any]

    if manifest_path.suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required to parse YAML manifests.")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    libs: Iterable[Mapping[str, str]] | None = data.get("libs")  # type: ignore[index]
    if not libs:
        raise ValueError("Manifest must contain a top-level 'libs' list.")

    return libs


###############################################################################
# CLI helpers
###############################################################################


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OPSVI shared-library scaffolder")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest", type=Path, help="Path to YAML/JSON manifest")
    group.add_argument("--name", type=str, help="Package name to scaffold (e.g. opsvi-core)")

    parser.add_argument(
        "--type",
        dest="library_type",
        choices=DEFAULT_TEMPLATES.keys(),
        help="Library type (required when --name is provided)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("libs"),
        help="Destination directory for generated libraries (default: ./libs)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    return parser.parse_args()


def _configure_logging(verbosity: int) -> None:
    if verbosity == 0:
        _LOG.setLevel(logging.INFO)
    elif verbosity == 1:
        _LOG.setLevel(logging.DEBUG)
    else:
        _LOG.setLevel(logging.NOTSET)
    _LOG.debug("Verbosity set to %d", verbosity)


###############################################################################
# Entry-point
###############################################################################


def main() -> None:
    args = _parse_args()
    _configure_logging(args.verbose)

    root_dir: Path = args.output
    root_dir.mkdir(parents=True, exist_ok=True)

    if args.manifest:
        libs = _load_manifest(Path(args.manifest))
    else:
        if not args.library_type:
            raise SystemExit("--type is required when scaffolding a single library")
        libs = ({"name": args.name, "type": args.library_type},)

    for lib in libs:
        name = lib["name"]
        lib_type = lib["type"]

        template = DEFAULT_TEMPLATES.get(lib_type)
        if template is None:
            _LOG.error("Unknown library type '%s' for %s", lib_type, name)
            continue

        try:
            Scaffolder(
                root_dir=root_dir,
                library_name=name,
                library_type=lib_type,
                template=template,
            ).scaffold()
        except Exception:  # pragma: no cover
            _LOG.exception("Failed to scaffold %s", name)


if __name__ == "__main__":
    main()
