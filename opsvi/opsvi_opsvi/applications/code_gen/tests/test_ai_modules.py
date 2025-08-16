"""Test AI modules with mocked OpenAI responses."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel

from ai_agents import (
    detect_project_type_with_ai,
    extract_requirements_with_ai,
    generate_architecture_with_ai,
    analyze_request_security_with_ai,
)
from ai_code_generator import AICodeGenerator
from ai_test_generator import AITestGenerator
from ai_documentation_generator import AIDocumentationGenerator
from schemas import ProjectType, RequirementsSpec, ArchitectureSpec


class TestAIAgents:
    """Test AI agent functions."""

    @patch("ai_agents.get_openai_interface")
    def test_detect_project_type_with_ai(self, mock_get_interface):
        """Test project type detection."""
        # Mock response
        mock_interface = Mock()
        mock_response = Mock()
        mock_response.project_type = "web_app"
        mock_response.confidence = 0.95
        mock_response.reasoning = "Flask web application request"
        mock_interface.create_structured_response.return_value = mock_response
        mock_get_interface.return_value = mock_interface

        result = detect_project_type_with_ai("Create a Flask web app")

        assert result == ProjectType.WEB_APP
        mock_interface.create_structured_response.assert_called_once()

    @patch("ai_agents.get_openai_interface")
    def test_extract_requirements_with_ai(self, mock_get_interface):
        """Test requirements extraction."""
        # Mock response
        mock_interface = Mock()
        mock_response = Mock()
        mock_response.title = "Weather App"
        mock_response.description = "Flask web application for weather data"
        mock_response.functional_requirements = ["Display weather", "Search by city"]
        mock_response.non_functional_requirements = ["Fast response", "Mobile friendly"]
        mock_response.technologies = ["Flask", "Python"]
        mock_response.constraints = ["Free weather API"]
        mock_interface.create_structured_response.return_value = mock_response
        mock_get_interface.return_value = mock_interface

        result = extract_requirements_with_ai("Weather app", ProjectType.WEB_APP)

        assert isinstance(result, RequirementsSpec)
        assert result.title == "Weather App"
        mock_interface.create_structured_response.assert_called_once()

    @patch("ai_agents.get_openai_interface")
    def test_generate_architecture_with_ai(self, mock_get_interface):
        """Test architecture generation."""
        # Mock response
        mock_interface = Mock()
        mock_response = Mock()
        mock_response.components = [
            Mock(name="main", type="controller", description="Main app"),
            Mock(name="weather", type="service", description="Weather service"),
        ]
        mock_response.data_flow = ["User -> Main -> Weather -> API"]
        mock_response.technology_choices = {"framework": "Flask"}
        mock_interface.create_structured_response.return_value = mock_response
        mock_get_interface.return_value = mock_interface

        requirements = Mock()
        result = generate_architecture_with_ai(requirements)

        assert isinstance(result, ArchitectureSpec)
        mock_interface.create_structured_response.assert_called_once()

    @patch("ai_agents.get_openai_interface")
    def test_analyze_request_security_with_ai(self, mock_get_interface):
        """Test security analysis."""
        # Mock response
        mock_interface = Mock()
        mock_response = Mock()
        mock_response.is_safe = True
        mock_response.risk_level = "low"
        mock_response.concerns = []
        mock_response.recommendations = ["Use HTTPS"]
        mock_interface.create_structured_response.return_value = mock_response
        mock_get_interface.return_value = mock_interface

        result = analyze_request_security_with_ai("Create a weather app")

        assert result.is_safe == True
        assert result.risk_level == "low"
        mock_interface.create_structured_response.assert_called_once()


class TestAICodeGenerator:
    """Test AI code generator."""

    @patch("ai_code_generator.get_openai_interface")
    def test_generate_project_code(self, mock_get_interface):
        """Test project code generation."""
        # Mock response
        mock_interface = Mock()
        mock_response = Mock()
        mock_response.main_files = [
            Mock(filename="app.py", content="# Flask app", purpose="Main application")
        ]
        mock_response.test_files = [
            Mock(filename="test_app.py", content="# Tests", purpose="Unit tests")
        ]
        mock_response.config_files = [
            Mock(filename="config.py", content="# Config", purpose="Configuration")
        ]
        mock_response.dependencies = ["flask", "requests"]
        mock_response.setup_instructions = "pip install -r requirements.txt"
        mock_interface.create_structured_response.return_value = mock_response
        mock_get_interface.return_value = mock_interface

        generator = AICodeGenerator()
        requirements = Mock()
        architecture = Mock()

        result = generator.generate_project_code(
            requirements, architecture, ProjectType.WEB_APP
        )

        assert len(result.main_files) == 1
        assert result.main_files[0].filename == "app.py"
        assert "flask" in result.dependencies
        mock_interface.create_structured_response.assert_called_once()


class TestAITestGenerator:
    """Test AI test generator."""

    @patch("ai_test_generator.get_openai_interface")
    def test_generate_ai_tests(self, mock_get_interface):
        """Test AI test generation."""
        # Mock response
        mock_interface = Mock()
        mock_response = Mock()
        mock_response.test_files = [
            Mock(
                filename="test_main.py",
                test_cases=[
                    Mock(name="test_app_runs", code="def test_app_runs(): pass")
                ],
            )
        ]
        mock_response.pytest_config = {"testpaths": ["tests"]}
        mock_response.coverage_config = {"source": ["app"]}
        mock_response.test_dependencies = ["pytest", "pytest-cov"]
        mock_interface.create_structured_response.return_value = mock_response
        mock_get_interface.return_value = mock_interface

        generator = AITestGenerator()
        requirements = Mock()
        architecture = Mock()
        code_generation = Mock(
            main_files=[Mock(filename="app.py", content="# Flask app")]
        )

        result = generator.generate_ai_tests(
            requirements, architecture, code_generation
        )

        assert len(result.test_files) == 1
        assert "pytest" in result.test_dependencies
        mock_interface.create_structured_response.assert_called_once()


class TestAIDocumentationGenerator:
    """Test AI documentation generator."""

    @patch("ai_documentation_generator.get_openai_interface")
    def test_generate_ai_documentation(self, mock_get_interface):
        """Test AI documentation generation."""
        # Mock response
        mock_interface = Mock()
        mock_response = Mock()
        mock_response.readme = Mock(
            content="# Weather App\nA Flask weather application"
        )
        mock_response.user_guide = Mock(content="## User Guide\nHow to use the app")
        mock_response.developer_guide = Mock(
            content="## Developer Guide\nHow to develop"
        )
        mock_response.api_docs = None
        mock_response.troubleshooting = Mock(
            content="## Troubleshooting\nCommon issues"
        )
        mock_response.changelog = Mock(content="## Changelog\n- Initial version")
        mock_interface.create_structured_response.return_value = mock_response
        mock_get_interface.return_value = mock_interface

        generator = AIDocumentationGenerator()
        requirements = Mock()
        architecture = Mock()
        code_generation = Mock(
            main_files=[Mock(filename="app.py", content="# Flask app")]
        )

        result = generator.generate_ai_documentation(
            requirements, architecture, code_generation
        )

        assert "Weather App" in result.readme.content
        assert result.user_guide.content.startswith("## User Guide")
        mock_interface.create_structured_response.assert_called_once()


class TestMockFailures:
    """Test handling of AI failures."""

    @patch("ai_agents.get_openai_interface")
    def test_detect_project_type_failure(self, mock_get_interface):
        """Test project type detection failure fallback."""
        # Mock interface failure
        mock_interface = Mock()
        mock_interface.create_structured_response.side_effect = Exception("API Error")
        mock_get_interface.return_value = mock_interface

        # Should fall back to simple script type
        result = detect_project_type_with_ai("Create something")
        assert result == ProjectType.SIMPLE_SCRIPT

    @patch("ai_code_generator.get_openai_interface")
    def test_code_generation_failure(self, mock_get_interface):
        """Test code generation failure handling."""
        # Mock interface failure
        mock_interface = Mock()
        mock_interface.create_structured_response.side_effect = Exception("API Error")
        mock_get_interface.return_value = mock_interface

        generator = AICodeGenerator()
        requirements = Mock()
        architecture = Mock()

        # Should handle failure gracefully
        with pytest.raises(Exception):
            generator.generate_project_code(
                requirements, architecture, ProjectType.WEB_APP
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
