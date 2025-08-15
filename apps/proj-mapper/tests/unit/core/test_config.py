"""Unit tests for the configuration subsystem."""

import os
import pytest
import tempfile
from pathlib import Path

from proj_mapper.core.config import (
    ConfigurationSchema,
    ConfigurationSource,
    DefaultConfigurationSource,
    FileConfigurationSource,
    EnvironmentConfigurationSource,
    Configuration
)


def test_configuration_schema_default_values():
    """Test that ConfigurationSchema has appropriate default values."""
    config = ConfigurationSchema()
    assert config.project_name is None
    assert config.output_dir == ".maps"
    assert config.include_patterns == ["**/*.py", "**/*.java", "**/*.js", "**/*.ts"]
    assert config.exclude_patterns == ["**/.git/**", "**/node_modules/**", "**/__pycache__/**"]
    assert config.max_file_size == 1048576  # 1MB
    assert config.analyze_code is True
    assert config.analyze_documentation is True
    assert config.parallel_processing is True
    assert config.output_format == "html"


def test_configuration_schema_custom_values():
    """Test ConfigurationSchema with custom values."""
    config = ConfigurationSchema(
        project_name="Test Project",
        output_dir="custom_output",
        include_patterns=["*.py"],
        exclude_patterns=["*.tmp"],
        max_file_size=2048,
        analyze_code=False,
        analyze_documentation=False,
        parallel_processing=False,
        output_format="json"
    )
    
    assert config.project_name == "Test Project"
    assert config.output_dir == "custom_output"
    assert config.include_patterns == ["*.py"]
    assert config.exclude_patterns == ["*.tmp"]
    assert config.max_file_size == 2048
    assert config.analyze_code is False
    assert config.analyze_documentation is False
    assert config.parallel_processing is False
    assert config.output_format == "json"


def test_default_configuration_source():
    """Test DefaultConfigurationSource returns default configuration."""
    source = DefaultConfigurationSource()
    config = source.get_config()
    
    assert isinstance(config, dict)
    assert config.get("output_dir") == ".maps"
    assert source.priority == 0


def test_file_configuration_source_with_valid_file():
    """Test FileConfigurationSource with a valid configuration file."""
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp:
        temp.write(b"""
project_name: Test Project
output_dir: custom_output
max_file_size: 2048
        """)
        temp_path = temp.name
    
    try:
        source = FileConfigurationSource(temp_path)
        config = source.get_config()
        
        assert config["project_name"] == "Test Project"
        assert config["output_dir"] == "custom_output"
        assert config["max_file_size"] == 2048
        assert source.priority == 50
    finally:
        # Clean up
        os.unlink(temp_path)


def test_file_configuration_source_file_not_found():
    """Test FileConfigurationSource raises error for non-existent file."""
    source = FileConfigurationSource("/path/does/not/exist.yaml")
    with pytest.raises(FileNotFoundError):
        source.get_config()


def test_environment_configuration_source():
    """Test EnvironmentConfigurationSource reads from environment variables."""
    # Set environment variables
    os.environ["PROJ_MAPPER_PROJECT_NAME"] = "Env Project"
    os.environ["PROJ_MAPPER_OUTPUT_DIR"] = "env_output"
    os.environ["PROJ_MAPPER_MAX_FILE_SIZE"] = "4096"
    os.environ["PROJ_MAPPER_ANALYZE_CODE"] = "false"
    
    source = EnvironmentConfigurationSource(prefix="PROJ_MAPPER_")
    config = source.get_config()
    
    assert config["project_name"] == "Env Project"
    assert config["output_dir"] == "env_output"
    assert config["max_file_size"] == 4096
    assert config["analyze_code"] is False
    assert source.priority == 100
    
    # Clean up environment
    del os.environ["PROJ_MAPPER_PROJECT_NAME"]
    del os.environ["PROJ_MAPPER_OUTPUT_DIR"]
    del os.environ["PROJ_MAPPER_MAX_FILE_SIZE"]
    del os.environ["PROJ_MAPPER_ANALYZE_CODE"]


def test_configuration_with_default_source():
    """Test Configuration with only default source."""
    config = Configuration()
    config.add_source(DefaultConfigurationSource())
    config.load()
    
    assert config.get("output_dir") == ".maps"
    assert config.get("include_patterns") == ["**/*.py", "**/*.java", "**/*.js", "**/*.ts"]


def test_configuration_with_multiple_sources():
    """Test Configuration merges multiple sources with correct priority."""
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp:
        temp.write(b"""
project_name: File Project
output_dir: file_output
        """)
        temp_path = temp.name
    
    try:
        # Set environment variables
        os.environ["PROJ_MAPPER_PROJECT_NAME"] = "Env Project"
        
        # Create configuration with multiple sources
        config = Configuration()
        config.add_source(DefaultConfigurationSource())
        config.add_source(FileConfigurationSource(temp_path))
        config.add_source(EnvironmentConfigurationSource(prefix="PROJ_MAPPER_"))
        config.load()
        
        # Environment should override file, which overrides default
        assert config.get("project_name") == "Env Project"  # From environment
        assert config.get("output_dir") == "file_output"  # From file
        assert config.get("include_patterns") == ["**/*.py", "**/*.java", "**/*.js", "**/*.ts"]  # From default
    finally:
        # Clean up
        os.unlink(temp_path)
        del os.environ["PROJ_MAPPER_PROJECT_NAME"]


def test_configuration_create_from_file():
    """Test creating a Configuration from a file."""
    # Create a temporary YAML file
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp:
        temp.write(b"""
project_name: File Project
output_dir: file_output
        """)
        temp_path = temp.name
    
    try:
        config = Configuration.from_file(temp_path)
        assert config.get("project_name") == "File Project"
        assert config.get("output_dir") == "file_output"
        # Default values should still be available
        assert config.get("include_patterns") == ["**/*.py", "**/*.java", "**/*.js", "**/*.ts"]
    finally:
        # Clean up
        os.unlink(temp_path)


def test_configuration_as_dict():
    """Test getting the entire configuration as a dictionary."""
    config = Configuration()
    config.add_source(DefaultConfigurationSource())
    config.load()
    
    config_dict = config.as_dict()
    assert isinstance(config_dict, dict)
    assert "output_dir" in config_dict
    assert "include_patterns" in config_dict
    assert config_dict["output_dir"] == ".maps" 