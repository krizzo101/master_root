"""Configuration management for Project Mapper.

This module provides configuration loading, validation, and access.
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set
import yaml
import json

from pydantic import BaseModel, Field, ValidationError

# Configure logging
logger = logging.getLogger(__name__)


class ConfigurationSchema(BaseModel):
    """Schema for validating configuration data.

    This schema defines the structure and validation rules for Project Mapper configuration.
    """

    # General settings
    project_name: Optional[str] = Field(None, description="Name of the project")
    output_dir: str = Field(".maps", description="Directory for storing output maps")

    # File discovery settings
    include_patterns: List[str] = Field(
        default_factory=lambda: ["**/*.py", "**/*.md", "**/*.markdown"],
        description="Glob patterns for files to include",
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/__pycache__/**",
            "**/.maps/**",
            "**/node_modules/**",
            "**/build/**",
            "**/dist/**",
        ],
        description="Glob patterns for files to exclude",
    )

    # Analysis settings
    max_file_size: int = Field(
        1048576, description="Maximum file size to analyze in bytes (1MB)"
    )
    analyze_code: bool = Field(True, description="Whether to analyze code files")
    analyze_docs: bool = Field(
        True, description="Whether to analyze documentation files"
    )

    # Relationship settings
    detect_relationships: bool = Field(
        True, description="Whether to detect relationships"
    )
    min_confidence: float = Field(
        0.5, description="Minimum confidence score for relationships"
    )

    # Output settings
    output_format: str = Field("json", description="Format for output files")
    pretty_print: bool = Field(
        True, description="Whether to format output for readability"
    )
    chunk_size: int = Field(
        100000, description="Maximum size for output chunks in bytes"
    )

    # Performance settings
    parallel_processing: bool = Field(
        False, description="Whether to use parallel processing"
    )
    max_workers: int = Field(4, description="Maximum number of worker processes")

    # Gitignore settings
    respect_gitignore: bool = Field(
        True, description="Whether to respect .gitignore files"
    )
    gitignore_files: List[str] = Field(
        default_factory=lambda: [".gitignore", ".ignore"],
        description="Names of gitignore-style files to respect",
    )
    additional_ignore_patterns: List[str] = Field(
        default_factory=list, description="Additional ignore patterns beyond .gitignore"
    )

    class Config:
        """Configuration for the model."""

        extra = "allow"  # Allow extra fields


class ConfigSource:
    """Base class for configuration sources."""

    def get_config(self) -> Dict[str, Any]:
        """Get configuration from this source.

        Returns:
            Dictionary of configuration values
        """
        return {}

    @property
    def priority(self) -> int:
        """Get the priority of this source.

        Higher priority sources override lower priority ones.

        Returns:
            Priority value (0-100)
        """
        return 0


class EnvironmentConfigSource(ConfigSource):
    """Configuration source that reads from environment variables."""

    ENV_PREFIX = "PROJ_MAPPER_"

    def get_config(self) -> Dict[str, Any]:
        """Get configuration from environment variables.

        Returns:
            Dictionary of configuration values
        """
        config = {}

        for key, value in os.environ.items():
            if key.startswith(self.ENV_PREFIX):
                config_key = key[len(self.ENV_PREFIX) :].lower()
                config[config_key] = value

        return config

    @property
    def priority(self) -> int:
        """Get the priority of environment variables.

        Returns:
            Priority value (50)
        """
        return 50


class FileConfigSource(ConfigSource):
    """Configuration source that reads from a file."""

    def __init__(self, file_path: Union[str, Path]):
        """Initialize the file config source.

        Args:
            file_path: Path to the configuration file
        """
        self.file_path = Path(file_path)

    def get_config(self) -> Dict[str, Any]:
        """Get configuration from the file.

        Returns:
            Dictionary of configuration values
        """
        if not self.file_path.exists():
            return {}

        try:
            with open(self.file_path, "r") as f:
                if self.file_path.suffix in [".yml", ".yaml"]:
                    return yaml.safe_load(f) or {}
                elif self.file_path.suffix == ".json":
                    return json.load(f) or {}
                else:
                    logger.warning(
                        f"Unsupported config file extension: {self.file_path.suffix}"
                    )
                    return {}
        except Exception as e:
            logger.error(f"Error reading config file {self.file_path}: {e}")
            return {}

    @property
    def priority(self) -> int:
        """Get the priority of file configuration.

        Returns:
            Priority value (25)
        """
        return 25


class Configuration:
    """Configuration manager for Project Mapper."""

    def __init__(
        self,
        project_name: Optional[str] = None,
        output_dir: str = ".maps",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size: int = 1048576,
        analyze_code: bool = True,
        analyze_docs: bool = True,
        detect_relationships: bool = True,
        min_confidence: float = 0.5,
        output_format: str = "json",
        pretty_print: bool = True,
        chunk_size: int = 100000,
        parallel_processing: bool = False,
        max_workers: int = 4,
        format_type: str = "json",
        include_code: bool = True,
        include_documentation: bool = True,
        include_metadata: bool = True,
        enable_chunking: bool = True,
        max_tokens: int = 2048,
        ai_optimize: bool = True,
        respect_gitignore: bool = True,
        gitignore_files: Optional[List[str]] = None,
        additional_ignore_patterns: Optional[List[str]] = None,
    ):
        """Initialize the configuration manager.

        Args:
            project_name: Name of the project
            output_dir: Directory for storing output maps
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude
            max_file_size: Maximum file size to analyze in bytes
            analyze_code: Whether to analyze code files
            analyze_docs: Whether to analyze documentation files
            detect_relationships: Whether to detect relationships
            min_confidence: Minimum confidence score for relationships
            output_format: Format for output files
            pretty_print: Whether to format output for readability
            chunk_size: Maximum size for output chunks in bytes
            parallel_processing: Whether to use parallel processing
            max_workers: Maximum number of worker processes
            format_type: Format type for output (json, yaml, etc.)
            include_code: Whether to include code elements in output
            include_documentation: Whether to include documentation in output
            include_metadata: Whether to include metadata in output
            enable_chunking: Whether to enable chunking for large outputs
            max_tokens: Maximum token estimate (0 for no limit)
            ai_optimize: Whether to apply AI optimization
        """
        # Project settings
        self.project_name = project_name
        self.output_dir = output_dir

        # File discovery settings
        self.include_patterns = include_patterns or [
            "**/*.py",  # Python files
            "**/*.js",  # JavaScript files
            "**/*.ts",  # TypeScript files
            "**/*.md",  # Markdown files
            "**/*.rst",  # reStructuredText files
        ]
        self.exclude_patterns = exclude_patterns or [
            "**/venv/**",  # Virtual environments
            "**/__pycache__/**",  # Python cache
            "**/node_modules/**",  # Node.js modules
            "**/.git/**",  # Git directory
            "**/.svn/**",  # SVN directory
            "**/.hg/**",  # Mercurial directory
            "**/build/**",  # Build directories
            "**/dist/**",  # Distribution directories
            "**/.tox/**",  # Tox test environments
            "**/.eggs/**",  # Python egg directories
            "**/*.pyc",  # Python compiled files
            "**/*.pyo",  # Python optimized files
            "**/*.pyd",  # Python DLL files
            "**/*.so",  # Shared libraries
            "**/*.dll",  # DLL files
            "**/*.exe",  # Executable files
        ]
        self.max_file_size = max_file_size

        # Analysis settings
        self.analyze_code = analyze_code
        self.analyze_docs = analyze_docs
        self.detect_relationships = detect_relationships
        self.min_confidence = min_confidence

        # Output settings
        self.output_format = output_format
        self.pretty_print = pretty_print
        self.chunk_size = chunk_size

        # Performance settings
        self.parallel_processing = parallel_processing
        self.max_workers = max_workers

        # Generator settings
        self.format_type = format_type
        self.include_code = include_code
        self.include_documentation = include_documentation
        self.include_metadata = include_metadata
        self.enable_chunking = enable_chunking
        self.max_tokens = max_tokens
        self.ai_optimize = ai_optimize
        self.respect_gitignore = respect_gitignore
        self.gitignore_files = gitignore_files or [".gitignore", ".ignore"]
        self.additional_ignore_patterns = additional_ignore_patterns or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            "project_name": self.project_name,
            "output_dir": self.output_dir,
            "include_patterns": self.include_patterns,
            "exclude_patterns": self.exclude_patterns,
            "max_file_size": self.max_file_size,
            "analyze_code": self.analyze_code,
            "analyze_docs": self.analyze_docs,
            "detect_relationships": self.detect_relationships,
            "min_confidence": self.min_confidence,
            "output_format": self.output_format,
            "pretty_print": self.pretty_print,
            "chunk_size": self.chunk_size,
            "parallel_processing": self.parallel_processing,
            "max_workers": self.max_workers,
            "format_type": self.format_type,
            "include_code": self.include_code,
            "include_documentation": self.include_documentation,
            "include_metadata": self.include_metadata,
            "enable_chunking": self.enable_chunking,
            "max_tokens": self.max_tokens,
            "ai_optimize": self.ai_optimize,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Configuration":
        """Create a configuration instance from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            Configuration instance
        """
        return cls(**config_dict)

    @classmethod
    def create_default(cls) -> "Configuration":
        """Create a configuration instance with default values.

        Returns:
            Configuration instance with default values
        """
        return cls()
