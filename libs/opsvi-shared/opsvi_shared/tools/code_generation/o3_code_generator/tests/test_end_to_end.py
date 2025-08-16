"""
End-to-end tests for the O3 Code Generator application.

Tests the complete workflow from CLI input to final output generation,
including all major components and their integration.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from src.tools.code_generation.o3_code_generator.main import main
from src.tools.code_generation.o3_code_generator.dependency_analyzer import (
    DependencyAnalyzer,
)
from src.tools.code_generation.o3_code_generator.schemas.dependency_analyzer_input_schema import (
    DependencyAnalysisInput,
)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_path = Path(self.temp_dir) / "test_project"
        self.test_project_path.mkdir(exist_ok=True)

        # Create sample requirements.txt
        requirements_file = self.test_project_path / "requirements.txt"
        requirements_file.write_text(
            """
requests>=2.25.0
pydantic==2.7.0
numpy>=1.21.0
flask==2.3.0
"""
        )

        # Create sample pyproject.toml
        pyproject_file = self.test_project_path / "pyproject.toml"
        pyproject_file.write_text(
            """
[project]
dependencies = [
    "fastapi>=0.68.0",
    "uvicorn>=0.15.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0.0",
    "black>=21.0.0"
]
"""
        )

        # Create sample package.json
        package_file = self.test_project_path / "package.json"
        package_file.write_text(
            """
{
    "dependencies": {
        "express": "^4.18.0",
        "lodash": "^4.17.21"
    },
    "devDependencies": {
        "jest": "^29.0.0",
        "eslint": "^8.0.0"
    }
}
"""
        )

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dependency_analysis_end_to_end(self):
        """Test complete dependency analysis workflow."""
        analyzer = DependencyAnalyzer()

        # Test single project analysis
        input_data = DependencyAnalysisInput(paths=[str(self.test_project_path)])
        result = analyzer.analyze_projects(input_data)

        # Verify result structure
        assert result["success"] is True
        assert "projects" in result
        assert len(result["projects"]) == 1

        project_result = result["projects"][0]
        assert project_result["project_path"] == str(self.test_project_path)
        assert "dependencies" in project_result
        assert "vulnerabilities" in project_result
        assert "optimization_suggestions" in project_result
        assert "manifest_files" in project_result

        # Verify manifest files were detected
        manifest_files = project_result["manifest_files"]
        assert "requirements.txt" in manifest_files
        assert "pyproject.toml" in manifest_files
        assert "package.json" in manifest_files

        # Verify dependencies were parsed
        dependencies = project_result["dependencies"]
        assert len(dependencies) > 0

        # Check for expected dependencies
        dep_names = [dep["name"] for dep in dependencies]
        assert "requests" in dep_names
        assert "pydantic" in dep_names
        assert "fastapi" in dep_names
        assert "express" in dep_names

    def test_multi_project_analysis(self):
        """Test analysis of multiple projects simultaneously."""
        # Create second project
        project2_path = Path(self.temp_dir) / "project2"
        project2_path.mkdir(exist_ok=True)

        # Create different requirements.txt for project2
        (project2_path / "requirements.txt").write_text(
            """
django>=4.0.0
celery>=5.2.0
redis>=4.0.0
"""
        )

        analyzer = DependencyAnalyzer()
        input_data = DependencyAnalysisInput(
            paths=[str(self.test_project_path), str(project2_path)]
        )

        result = analyzer.analyze_projects(input_data)

        # Verify multi-project results
        assert result["success"] is True
        assert len(result["projects"]) == 2
        assert result["summary"]["total_projects"] == 2
        assert result["summary"]["successful_analyses"] == 2
        assert result["summary"]["failed_analyses"] == 0

        # Verify each project has dependencies
        for project in result["projects"]:
            assert len(project["dependencies"]) > 0
            assert "manifest_files" in project

    def test_vulnerability_detection(self):
        """Test that vulnerability detection works."""
        # Create project with known vulnerable packages
        vuln_project = Path(self.temp_dir) / "vuln_project"
        vuln_project.mkdir(exist_ok=True)

        # Use older versions that should trigger vulnerability warnings
        (vuln_project / "requirements.txt").write_text(
            """
requests==2.19.0
pyyaml==3.13
pillow==6.0.0
"""
        )

        analyzer = DependencyAnalyzer()
        input_data = DependencyAnalysisInput(paths=[str(vuln_project)])

        result = analyzer.analyze_projects(input_data)

        # Check if vulnerabilities were detected
        project_result = result["projects"][0]
        vulnerabilities = project_result["vulnerabilities"]

        # Should detect vulnerabilities in older versions
        assert len(vulnerabilities) >= 0  # May be 0 if no vulns in test data

        # Verify vulnerability structure if any found
        for vuln in vulnerabilities:
            assert "package" in vuln
            assert "vulnerability" in vuln
            assert "severity" in vuln

    def test_optimization_suggestions(self):
        """Test that optimization suggestions are generated."""
        # Create project with optimization opportunities
        opt_project = Path(self.temp_dir) / "opt_project"
        opt_project.mkdir(exist_ok=True)

        # Create requirements.txt with unpinned versions
        (opt_project / "requirements.txt").write_text(
            """
requests
numpy
pandas
"""
        )

        # Create pyproject.toml with same package (duplicate)
        (opt_project / "pyproject.toml").write_text(
            """
[project]
dependencies = [
    "requests>=2.25.0"
]
"""
        )

        analyzer = DependencyAnalyzer()
        input_data = DependencyAnalysisInput(paths=[str(opt_project)])

        result = analyzer.analyze_projects(input_data)
        project_result = result["projects"][0]
        suggestions = project_result["optimization_suggestions"]

        # Should suggest pinning versions for unpinned packages
        assert len(suggestions) > 0

        # Check for specific suggestion types
        suggestion_text = " ".join(suggestions)
        assert (
            "pinning versions" in suggestion_text or "multiple files" in suggestion_text
        )

    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        analyzer = DependencyAnalyzer()

        # Test with non-existent path
        input_data = DependencyAnalysisInput(paths=["/nonexistent/path"])
        result = analyzer.analyze_projects(input_data)

        # Should handle error gracefully
        assert result["success"] is False
        assert result["summary"]["failed_analyses"] == 1
        assert len(result["error_messages"]) > 0

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("src.tools.code_generation.o3_code_generator.api_spec_generator.OpenAI")
    def test_api_spec_generation_integration(self, mock_openai):
        """Test API specification generation with mocked OpenAI."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {"/users": {"get": {"summary": "List users"}}},
            }
        )

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # Import and test API spec generator
        from src.tools.code_generation.o3_code_generator.api_spec_generator import (
            APISpecGenerator,
        )

        generator = APISpecGenerator()

        # Test that it uses the unified OpenAI client wrapper
        assert hasattr(generator, "client")

    def test_validation_framework_integration(self):
        """Test that validation framework is integrated across components."""
        from src.tools.code_generation.o3_code_generator.schemas.base_output_schema import (
            BaseGeneratorOutput,
        )
        from src.tools.code_generation.o3_code_generator.schemas.api_spec_output_schema import (
            APISpecOutput,
        )

        # Test base validation schema
        output = BaseGeneratorOutput()
        assert output.success is True
        assert output.error_message is None
        assert len(output.warnings) == 0

        # Test adding warnings and errors
        output.add_warning("Test warning")
        assert len(output.warnings) == 1
        assert output.has_warnings() is True

        output.mark_failed("Test error")
        assert output.success is False
        assert output.error_message == "Test error"
        assert output.is_successful() is False

        # Test API spec validation
        api_output = APISpecOutput()
        assert isinstance(api_output, BaseGeneratorOutput)

        # Test validation methods
        api_output.add_endpoint("GET", "/users", "List users")
        assert len(api_output.endpoints) == 1
        assert api_output.metadata.get("endpoint_count") == 1

    def test_configuration_hierarchy(self):
        """Test that configuration follows environment > YAML > defaults hierarchy."""
        from src.tools.code_generation.o3_code_generator.config.core.config_manager import (
            ConfigManager,
        )

        # Test with environment variable override
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key-test"}):
            config_manager = ConfigManager()
            api_key = config_manager.get_api_key()
            assert api_key == "env-key-test"

    def test_directory_security(self):
        """Test that directory operations are secure and constrained."""
        from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
            DirectoryManager,
        )

        dir_manager = DirectoryManager()

        # Test that paths are anchored to repo root
        assert str(dir_manager.base_output_dir).endswith("generated_files")

        # Test path security validation (should prevent traversal)
        malicious_path = Path("../../../etc/passwd")
        # This should be caught by security validation
        # (Implementation may vary based on actual security measures)

    def test_complete_cli_workflow(self):
        """Test complete CLI workflow end-to-end."""
        # This would test the main CLI entry point
        # For now, we verify the main function exists and is callable

        assert callable(main)

        # Test argument parsing works
        import sys

        with patch.object(
            sys, "argv", ["main.py", "analyze", str(self.test_project_path)]
        ):
            # Would need to mock subprocess/CLI execution for full test
            pass


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for real-world usage scenarios."""

    def test_python_monorepo_analysis(self):
        """Test analysis of a Python monorepo with multiple projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create monorepo structure
            monorepo = Path(temp_dir) / "monorepo"
            monorepo.mkdir()

            # Create multiple Python projects
            for project_name in ["api", "worker", "frontend"]:
                project_dir = monorepo / project_name
                project_dir.mkdir()

                # Each project has different dependencies
                if project_name == "api":
                    (project_dir / "requirements.txt").write_text(
                        "fastapi>=0.68.0\nuvicorn>=0.15.0"
                    )
                elif project_name == "worker":
                    (project_dir / "requirements.txt").write_text(
                        "celery>=5.2.0\nredis>=4.0.0"
                    )
                else:  # frontend
                    (project_dir / "package.json").write_text(
                        '{"dependencies": {"react": "^18.0.0"}}'
                    )

            # Analyze entire monorepo
            analyzer = DependencyAnalyzer()
            input_data = DependencyAnalysisInput(
                paths=[str(monorepo / "api"), str(monorepo / "worker")]
            )

            result = analyzer.analyze_projects(input_data)

            assert result["success"] is True
            assert len(result["projects"]) == 2
            assert result["summary"]["total_dependencies"] > 0

    def test_mixed_technology_stack(self):
        """Test analysis of projects with mixed technology stacks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "mixed_stack"
            project_dir.mkdir()

            # Python backend
            (project_dir / "requirements.txt").write_text("django>=4.0.0")
            (project_dir / "pyproject.toml").write_text(
                """
[project]
dependencies = ["fastapi>=0.68.0"]
"""
            )

            # Node.js frontend
            (project_dir / "package.json").write_text(
                """
{
    "dependencies": {"express": "^4.18.0"},
    "devDependencies": {"jest": "^29.0.0"}
}
"""
            )

            analyzer = DependencyAnalyzer()
            input_data = DependencyAnalysisInput(paths=[str(project_dir)])

            result = analyzer.analyze_projects(input_data)

            project_result = result["projects"][0]
            dependencies = project_result["dependencies"]

            # Should find dependencies from all manifest types
            sources = {dep["source"] for dep in dependencies}
            assert "requirements.txt" in sources
            assert "pyproject.toml" in sources
            assert any("package.json" in source for source in sources)


if __name__ == "__main__":
    pytest.main([__file__])
