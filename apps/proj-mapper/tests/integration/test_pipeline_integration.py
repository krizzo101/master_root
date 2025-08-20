"""Integration tests for the complete Project Mapper pipeline."""

import json
import os
import shutil
from pathlib import Path

import pytest

from proj_mapper.claude_code_adapter import AnalyzerManager
from proj_mapper.core.config import ConfigManager
from proj_mapper.core.pipeline import Pipeline
from proj_mapper.output.formatters import JSONFormatter
from proj_mapper.output.generator import MapGenerator
from proj_mapper.relationship.detector import RelationshipDetector


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
def output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def config_manager(test_project_dir, output_dir):
    """Create a configuration manager for testing."""
    # Create config dictionary
    config = {
        "project": {"name": "test_project", "root": str(test_project_dir)},
        "analyzers": {
            "python": {"enabled": True, "include_patterns": ["**/*.py"]},
            "markdown": {"enabled": True, "include_patterns": ["**/*.md"]},
        },
        "output": {"format": "json", "directory": str(output_dir)},
    }

    # Create config manager
    config_manager = ConfigManager()
    config_manager.load_dict(config)

    return config_manager


@pytest.fixture
def pipeline(config_manager):
    """Create the complete pipeline for testing."""
    # Create components
    analyzer_manager = AnalyzerManager(config_manager)
    relationship_detector = RelationshipDetector(config_manager)
    map_generator = MapGenerator(
        output_dir=Path(config_manager.get("output.directory"))
    )

    # Register formatters
    map_generator.register_formatter(JSONFormatter())

    # Create pipeline
    pipeline = Pipeline(
        config_manager=config_manager,
        analyzer_manager=analyzer_manager,
        relationship_detector=relationship_detector,
        map_generator=map_generator,
    )

    return pipeline


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""

    def test_end_to_end_processing(self, pipeline, test_project_dir, output_dir):
        """Test the complete pipeline from analysis to output generation."""
        # Run the pipeline
        result = pipeline.run()

        # Assertions about the pipeline execution
        assert result is not None
        assert result.get("success") is True
        assert "analysis_results" in result
        assert "relationship_map" in result
        assert "output" in result

        # Check that output files exist
        output_file = output_dir / "test_project.json"
        assert output_file.exists()

        # Verify output content
        with open(output_file, "r") as f:
            output_data = json.load(f)

        assert "nodes" in output_data
        assert "relationships" in output_data

        # Verify Python module was detected
        python_nodes = [n for n in output_data["nodes"] if n["id"].endswith(".py")]
        assert len(python_nodes) >= 1

        # Verify Markdown file was detected
        md_nodes = [n for n in output_data["nodes"] if n["id"].endswith(".md")]
        assert len(md_nodes) >= 1

        # Verify relationships were detected
        assert len(output_data["relationships"]) > 0

    def test_pipeline_with_invalid_project(self, pipeline, test_project_dir):
        """Test pipeline behavior with an invalid project directory."""
        # Change to a non-existent directory
        pipeline.config_manager.set(
            "project.root", str(test_project_dir / "non_existent")
        )

        # Run the pipeline and expect an error
        result = pipeline.run()

        # Check error handling
        assert result is not None
        assert result.get("success") is False
        assert "error" in result

    def test_analyzer_integration(self, pipeline, test_project_dir):
        """Test the integration between analyzers and relationship detection."""
        # Get analyzer manager from pipeline
        analyzer_manager = pipeline.analyzer_manager

        # Run analysis step
        analysis_results = analyzer_manager.analyze(test_project_dir)

        # Check analysis results
        assert analysis_results is not None
        assert len(analysis_results) > 0

        # Get relationship detector from pipeline
        relationship_detector = pipeline.relationship_detector

        # Detect relationships
        relationship_map = relationship_detector.detect_relationships(analysis_results)

        # Check relationship map
        assert relationship_map is not None
        assert len(relationship_map.get_nodes()) > 0
        assert len(relationship_map.get_relationships()) > 0

        # Verify specific relationships were detected
        # For example, test_module.py should be documented by README.md
        py_file = [n for n in relationship_map.get_nodes() if n.endswith(".py")]
        md_file = [n for n in relationship_map.get_nodes() if n.endswith(".md")]

        if py_file and md_file:
            # Check if there's a relationship between them
            relationships = relationship_map.get_relationships_between(
                py_file[0], md_file[0]
            )
            # There should be at least one relationship in one direction or the other
            relationships.extend(
                relationship_map.get_relationships_between(md_file[0], py_file[0])
            )

            assert len(relationships) > 0
