"""End-to-end tests for CLI operations."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def test_project_dir(tmp_path):
    """Create a temporary directory with test project files."""
    # Copy test project to temporary directory
    src_dir = Path(__file__).parent.parent / "fixtures" / "small_project"
    dest_dir = tmp_path / "test_project"
    
    # Create destination directory
    dest_dir.mkdir()
    
    # Copy files
    for file_path in src_dir.glob("*"):
        if file_path.is_file():
            shutil.copy(file_path, dest_dir / file_path.name)
        elif file_path.is_dir():
            shutil.copytree(file_path, dest_dir / file_path.name)
    
    return dest_dir


@pytest.fixture
def project_config(test_project_dir):
    """Create a configuration file for the test project."""
    config_file = test_project_dir / "proj_mapper.json"
    
    config = {
        "project": {
            "name": "test_project",
            "root": str(test_project_dir)
        },
        "analyzers": {
            "python": {
                "enabled": True,
                "include_patterns": ["**/*.py"]
            },
            "markdown": {
                "enabled": True,
                "include_patterns": ["**/*.md"]
            }
        },
        "output": {
            "format": "json",
            "directory": str(test_project_dir / ".maps")
        }
    }
    
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    return config_file


class TestCLIOperations:
    """E2E tests for CLI operations."""
    
    @pytest.mark.e2e
    def test_generate_map_command(self, test_project_dir, project_config):
        """Test the 'generate-map' command."""
        # Run the CLI command
        cmd = ["python", "-m", "proj_mapper", "generate-map", 
               "--config", str(project_config),
               "--output-dir", str(test_project_dir / ".maps")]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command output
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Map generated successfully" in result.stdout
        
        # Verify output file exists
        output_file = test_project_dir / ".maps" / "test_project.json"
        assert output_file.exists()
        
        # Verify output content
        with open(output_file, "r") as f:
            output_data = json.load(f)
        
        assert "nodes" in output_data
        assert "relationships" in output_data
    
    @pytest.mark.e2e
    def test_analyze_command(self, test_project_dir, project_config):
        """Test the 'analyze' command."""
        # Run the CLI command
        cmd = ["python", "-m", "proj_mapper", "analyze", 
               "--config", str(project_config)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command output
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Analysis completed" in result.stdout
    
    @pytest.mark.e2e
    def test_validate_config_command(self, project_config):
        """Test the 'validate-config' command."""
        # Run the CLI command
        cmd = ["python", "-m", "proj_mapper", "validate-config", 
               "--config", str(project_config)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command output
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Configuration is valid" in result.stdout
    
    @pytest.mark.e2e
    def test_help_command(self):
        """Test the help command."""
        # Run the CLI command
        cmd = ["python", "-m", "proj_mapper", "--help"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command output
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "usage:" in result.stdout
        assert "generate-map" in result.stdout
        assert "analyze" in result.stdout
    
    @pytest.mark.e2e
    def test_version_command(self):
        """Test the version command."""
        # Run the CLI command
        cmd = ["python", "-m", "proj_mapper", "--version"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command output
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "Project Mapper" in result.stdout
        assert "version" in result.stdout.lower()
    
    @pytest.mark.e2e
    def test_invalid_command(self):
        """Test behavior with an invalid command."""
        # Run the CLI command
        cmd = ["python", "-m", "proj_mapper", "invalid-command"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Check command output
        assert result.returncode != 0, "Command should have failed"
        assert "error" in result.stderr.lower() 