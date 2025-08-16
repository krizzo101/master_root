"""Integration tests for O3 Code Generator."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.tools.code_generation.o3_code_generator.main import run_analyze
from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
    DirectoryManager,
)


class TestIntegration:
    """Integration test cases."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create a sample requirements.txt
            (project_path / "requirements.txt").write_text(
                "requests>=2.25.0\n" "pytest>=6.0.0\n" "openai>=1.0.0\n"
            )

            # Create a sample package.json
            package_json = {
                "name": "test-project",
                "version": "1.0.0",
                "dependencies": {"express": "^4.18.0", "lodash": "^4.17.21"},
                "devDependencies": {"jest": "^29.0.0"},
            }
            (project_path / "package.json").write_text(
                json.dumps(package_json, indent=2)
            )

            yield project_path

    def test_dependency_analysis_integration(self, temp_project):
        """Test end-to-end dependency analysis."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as output_file:
            output_path = output_file.name

        try:
            # Mock the DependencyAnalyzer to avoid actual OpenAI calls
            with patch(
                "src.tools.code_generation.o3_code_generator.main.DependencyAnalyzer"
            ) as mock_analyzer_class:
                mock_analyzer = MagicMock()
                mock_analyzer_class.return_value = mock_analyzer

                # Mock the analyze_projects method
                mock_analyzer.analyze_projects.return_value = {
                    "success": True,
                    "reports": [
                        {
                            "project_path": str(temp_project),
                            "dependencies": {
                                "direct": ["requests", "pytest", "openai"]
                            },
                            "vulnerabilities": [],
                            "optimization": {"score": 85},
                            "success": True,
                        }
                    ],
                }

                # Run the analysis
                run_analyze([str(temp_project)], output_path)

                # Verify the output file was created
                assert Path(output_path).exists()

                # Verify the content
                with open(output_path) as f:
                    result = json.load(f)

                assert result["success"] is True
                assert len(result["reports"]) == 1
                assert result["reports"][0]["project_path"] == str(temp_project)

        finally:
            # Cleanup
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_directory_manager_integration(self):
        """Test DirectoryManager with real filesystem operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the base_output_dir to use temp directory
            dm = DirectoryManager()
            dm.base_output_dir = Path(temp_dir) / "generated_files"

            # Test module directory creation
            dm.create_module_directories("test_module", ["data", "logs"])

            # Verify directories exist
            assert (dm.base_output_dir / "test_module").exists()
            assert (dm.base_output_dir / "test_module" / "data").exists()
            assert (dm.base_output_dir / "test_module" / "logs").exists()

            # Test cleanup
            dm.cleanup_empty_directories(dm.base_output_dir)

    @pytest.mark.parametrize(
        "project_paths", [["path1"], ["path1", "path2"], ["path1", "path2", "path3"]]
    )
    def test_multi_project_analysis(self, project_paths):
        """Test analysis with multiple project paths."""
        with patch(
            "src.tools.code_generation.o3_code_generator.main.DependencyAnalyzer"
        ) as mock_analyzer_class:
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer

            # Mock successful analysis for each project
            mock_reports = []
            for path in project_paths:
                mock_reports.append(
                    {
                        "project_path": path,
                        "success": True,
                        "dependencies": {"direct": ["test-dep"]},
                        "vulnerabilities": [],
                        "optimization": {"score": 90},
                    }
                )

            mock_analyzer.analyze_projects.return_value = {
                "success": True,
                "reports": mock_reports,
            }

            # Run analysis without output file (console output)
            run_analyze(project_paths, None)

            # Verify analyzer was called with correct input
            mock_analyzer.analyze_projects.assert_called_once()
            call_args = mock_analyzer.analyze_projects.call_args[0][0]
            assert call_args.paths == project_paths
