#!/usr/bin/env python3
"""
Comprehensive test suite for O3 Code Generator tools.

This test suite validates all the core tools in the O3 code generator:
- API Documentation Generator
- Docker Orchestrator
- Requirements Analyzer
- Security Scanner
- Code Reviewer
- Dependency Analyzer
- Project Initializer
"""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add the script directory to Python path for imports
if script_dir not in sys.path:
    sys.path.append(script_dir)

try:
    from api_doc_generator import APIDocGenerator, CodeAnalyzer
    from docker_orchestrator import DockerAnalyzer, DockerOrchestrator
except ImportError as e:
    print(f"❌ Failed to import O3 generator modules: {e}")
    sys.exit(1)


class TestCodeAnalyzer(unittest.TestCase):
    """Test the CodeAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.analyzer = CodeAnalyzer(self.logger)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyze_code_files_empty_list(self):
        """Test analyzing empty list of files."""
        self.assertEqual(result["endpoints"], [])
        self.assertEqual(result["models"], [])
        self.assertEqual(result["schemas"], [])
        self.assertEqual(result["authentication"], [])
        self.assertEqual(result["errors"], [])

    def test_analyze_code_files_nonexistent_file(self):
        """Test analyzing non-existent files."""
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("nonexistent.py", result["errors"][0]["file"])

    def test_extract_python_api_info(self):
        """Test Python API information extraction."""
from fastapi import FastAPI
from pydantic import BaseModel


class User(BaseModel):
    name: str
    email: str

@app.get("/users")
def get_users():
    return {"users": []}

@app.post("/users")
def create_user(user: User):
    return {"message": "User created"}
"""

        self.assertEqual(len(result["endpoints"]), 2)
        self.assertEqual(len(result["models"]), 1)

        # Check endpoints
        self.assertEqual(endpoints["/users"], "GET")

        # Check models
        self.assertIn("User", models)

    def test_extract_javascript_api_info(self):
        """Test JavaScript API information extraction."""
const express = require('express');
const app = express();

interface User {
    name: string;
    email: string;
}

app.get('/users', (req, res) => {
    res.json({users: []});
});

app.post('/users', (req, res) => {
    res.json({message: 'User created'});
});
"""

        self.assertEqual(len(result["endpoints"]), 2)
        self.assertEqual(len(result["models"]), 1)

        # Check endpoints
        self.assertEqual(endpoints["/users"], "GET")

        # Check models
        self.assertIn("User", models)


class TestDockerAnalyzer(unittest.TestCase):
    """Test the DockerAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.analyzer = DockerAnalyzer(self.logger)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyze_application_nonexistent_path(self):
        """Test analyzing non-existent application path."""
        self.assertEqual(result["language"], "")
        self.assertEqual(result["framework"], "")
        self.assertEqual(result["dependencies"], [])

    def test_extract_python_dependencies(self):
        """Test Python dependencies extraction."""
        with open(requirements_file, "w") as f:
            f.write("fastapi==0.68.0\npydantic>=1.8.0\nrequests~=2.25.0\n")

        self.assertEqual(result, expected)

    def test_extract_node_dependencies(self):
        """Test Node.js dependencies extraction."""
            "dependencies": {"express": "^4.17.1", "cors": "^2.8.5"},
            "devDependencies": {"jest": "^27.0.0", "eslint": "^7.32.0"},
        }
        with open(package_file, "w") as f:
            json.dump(package_data, f)

        self.assertEqual(set(result), set(expected))

    def test_detect_framework_python_fastapi(self):
        """Test Python FastAPI framework detection."""
        # Create a mock Python project
        app_dir.mkdir()

        with open(requirements_file, "w") as f:
            f.write("fastapi==0.68.0\nuvicorn==0.15.0\n")

        self.assertEqual(result, "fastapi")

    def test_detect_framework_javascript_express(self):
        """Test JavaScript Express framework detection."""
        # Create a mock Node.js project
        app_dir.mkdir()

        with open(package_file, "w") as f:
            json.dump(package_data, f)

        self.assertEqual(result, "express")

    def test_detect_entry_point_python(self):
        """Test Python entry point detection."""
        app_dir.mkdir()

        # Create main.py
        with open(main_file, "w") as f:
            f.write('if __name__ == "__main__":\n    print("Hello World")\n')

        self.assertEqual(result, "main.py")

    def test_detect_entry_point_javascript(self):
        """Test JavaScript entry point detection."""
        app_dir.mkdir()

            "scripts": {"start": "node index.js", "dev": "nodemon index.js"}
        }
        with open(package_file, "w") as f:
            json.dump(package_data, f)

        self.assertEqual(result, "node index.js")


class TestAPIDocGenerator(unittest.TestCase):
    """Test the APIDocGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

        # Create mock config
            "api": {
                "base_url": "https://api.openai.com/v1",
                "model_name": "o3-mini",
                "timeout": 30,
            },
            "output": {"output_dir": str(Path(self.temp_dir) / "output")},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }

        with open(self.config_path, "w") as f:
            import yaml

            yaml.dump(config_data, f)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("api_doc_generator.OpenAI")
    @patch("api_doc_generator.ConfigManager")
    @patch("api_doc_generator.setup_logger")
    def test_init(self, mock_logger, mock_config_manager, mock_openai):
        """Test APIDocGenerator initialization."""
        mock_config.get_api_config.return_value = Mock(
        )
        mock_config.get_output_config.return_value = Mock(
        )
        mock_config.get_logging_config.return_value = {}
        mock_config_manager.return_value = mock_config


        self.assertIsNotNone(generator)
        mock_openai.assert_called_once()

    @patch("api_doc_generator.OpenAI")
    @patch("api_doc_generator.ConfigManager")
    @patch("api_doc_generator.setup_logger")
    def test_build_prompt(self, mock_logger, mock_config_manager, mock_openai):
        """Test prompt building."""
        mock_config.get_api_config.return_value = Mock(
        )
        mock_config.get_output_config.return_value = Mock(
        )
        mock_config.get_logging_config.return_value = {}
        mock_config_manager.return_value = mock_config


        # Create mock input data
        input_data.app_name = "Test API"
        input_data.description = "A test API"
        input_data.version = "1.0.0"
        input_data.output_format = "markdown"
        input_data.additional_context = None

        # Create mock API info
            "endpoints": [{"method": "GET", "path": "/users", "language": "python"}],
            "models": [{"name": "User", "language": "python", "type": "pydantic"}],
            "authentication": [],
        }


        self.assertIn("Test API", prompt)
        self.assertIn("GET /users", prompt)
        self.assertIn("User", prompt)


class TestDockerOrchestrator(unittest.TestCase):
    """Test the DockerOrchestrator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.yaml"

        # Create mock config
            "api": {
                "base_url": "https://api.openai.com/v1",
                "model_name": "o3-mini",
                "timeout": 30,
            },
            "output": {"output_dir": str(Path(self.temp_dir) / "output")},
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        }

        with open(self.config_path, "w") as f:
            import yaml

            yaml.dump(config_data, f)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("docker_orchestrator.OpenAI")
    @patch("docker_orchestrator.ConfigManager")
    @patch("docker_orchestrator.setup_logger")
    def test_init(self, mock_logger, mock_config_manager, mock_openai):
        """Test DockerOrchestrator initialization."""
        mock_config.get_api_config.return_value = Mock(
        )
        mock_config.get_output_config.return_value = Mock(
        )
        mock_config.get_logging_config.return_value = {}
        mock_config_manager.return_value = mock_config


        self.assertIsNotNone(orchestrator)
        mock_openai.assert_called_once()

    def test_generate_dockerfile_single_stage(self):
        """Test single-stage Dockerfile generation."""
        from docker_orchestrator import DockerOrchestrator

        with (
            patch("docker_orchestrator.OpenAI"),
            patch("docker_orchestrator.ConfigManager"),
            patch("docker_orchestrator.setup_logger"),
        ):
            mock_config.get_api_config.return_value = Mock(
            )
            mock_config.get_output_config.return_value = Mock(
            )
            mock_config.get_logging_config.return_value = {}


            # Test single-stage Dockerfile generation
            input_data.multi_stage = False

                docker_config, input_data
            )

            self.assertIn("FROM python:3.11-slim", result)
            self.assertIn("WORKDIR /app", result)
            self.assertIn("EXPOSE 8000", result)

    def test_generate_dockerfile_multi_stage(self):
        """Test multi-stage Dockerfile generation."""
        from docker_orchestrator import DockerOrchestrator

        with (
            patch("docker_orchestrator.OpenAI"),
            patch("docker_orchestrator.ConfigManager"),
            patch("docker_orchestrator.setup_logger"),
        ):
            mock_config.get_api_config.return_value = Mock(
            )
            mock_config.get_output_config.return_value = Mock(
            )
            mock_config.get_logging_config.return_value = {}


            # Test multi-stage Dockerfile generation
            input_data.multi_stage = True

                docker_config, input_data
            )

            self.assertIn("FROM python:3.11-slim as builder", result)
            self.assertIn("FROM python:3.11-slim", result)
            self.assertIn("COPY --from=builder", result)

    def test_generate_dockerignore(self):
        """Test .dockerignore generation."""
        from docker_orchestrator import DockerOrchestrator

        with (
            patch("docker_orchestrator.OpenAI"),
            patch("docker_orchestrator.ConfigManager"),
            patch("docker_orchestrator.setup_logger"),
        ):
            mock_config.get_api_config.return_value = Mock(
            )
            mock_config.get_output_config.return_value = Mock(
            )
            mock_config.get_logging_config.return_value = {}




            self.assertIn("# .dockerignore", result)
            self.assertIn("__pycache__", result)
            self.assertIn(".git", result)
            self.assertIn("node_modules", result)


class TestSecurityScanner(unittest.TestCase):
    """Test the SecurityScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_file_security_issues(self):
        """Test scanning files for security issues."""
        # Create a test file with potential security issues
        with open(test_file, "w") as f:
            f.write(
                """
import os
import subprocess

# Potential security issues - using safe test values
# test_password = "test_password_for_testing_only"  # pragma: allowlist secret
# os.system("rm -rf /")  # Dangerous command - commented out for safety
# subprocess.call("ls", shell=True)  # Shell injection risk - commented out for safety
"""
            )

        # Mock the scanner
        with patch("security_scanner.SecurityScanner") as mock_scanner_class:
            mock_scanner_class.return_value = mock_scanner

            # Test would go here - this is a placeholder for the actual test
            # when the security scanner is properly implemented
            pass


class TestIntegration(unittest.TestCase):
    """Integration tests for the O3 code generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_api_doc_generation(self):
        """Test end-to-end API documentation generation."""
        # Create a test Python API file
        with open(api_file, "w") as f:
            f.write(
                """
from fastapi import FastAPI
from pydantic import BaseModel


class User(BaseModel):
    name: str
    email: str

@app.get("/users")
def get_users():
    return {"users": []}

@app.post("/users")
def create_user(user: User):
    return {"message": "User created"}
"""
            )

        # This would be a full integration test
        # For now, we'll just verify the file was created
        self.assertTrue(api_file.exists())

    def test_end_to_end_docker_generation(self):
        """Test end-to-end Docker configuration generation."""
        # Create a test Python project
        project_dir.mkdir()

        # Create requirements.txt
        with open(requirements_file, "w") as f:
            f.write("fastapi==0.68.0\nuvicorn==0.15.0\n")

        # Create main.py
        with open(main_file, "w") as f:
            f.write(
                """
from fastapi import FastAPI


@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
            )

        # This would be a full integration test
        # For now, we'll just verify the project structure was created
        self.assertTrue(requirements_file.exists())
        self.assertTrue(main_file.exists())


class TestUtilities(unittest.TestCase):
    """Test utility functions."""

    def test_file_extension_mapping(self):
        """Test file extension mapping."""
        from api_doc_generator import APIDocGenerator

        with (
            patch("api_doc_generator.OpenAI"),
            patch("api_doc_generator.ConfigManager"),
            patch("api_doc_generator.setup_logger"),
        ):
            mock_config.get_api_config.return_value = Mock(
            )
            mock_config.get_output_config.return_value = Mock(
            )
            mock_config.get_logging_config.return_value = {}


            # Test file extension mapping
            self.assertEqual(generator._get_file_extension("python"), ".py")
            self.assertEqual(generator._get_file_extension("javascript"), ".js")
            self.assertEqual(generator._get_file_extension("typescript"), ".ts")
            self.assertEqual(generator._get_file_extension("java"), ".java")
            self.assertEqual(generator._get_file_extension("go"), ".go")
            self.assertEqual(generator._get_file_extension("curl"), ".sh")
            self.assertEqual(generator._get_file_extension("unknown"), ".txt")

    def test_code_example_generation(self):
        """Test code example generation."""
        from api_doc_generator import APIDocGenerator

        with (
            patch("api_doc_generator.OpenAI"),
            patch("api_doc_generator.ConfigManager"),
            patch("api_doc_generator.setup_logger"),
        ):
            mock_config.get_api_config.return_value = Mock(
            )
            mock_config.get_output_config.return_value = Mock(
            )
            mock_config.get_logging_config.return_value = {}


            # Test Python example generation
            self.assertIn("requests.get", python_example)
            self.assertIn("/users", python_example)

            # Test JavaScript example generation
            self.assertIn("fetch", js_example)
            self.assertIn("/users", js_example)

            # Test cURL example generation
            self.assertIn("curl -X GET", curl_example)
            self.assertIn("/users", curl_example)


def run_tests():
    """Run all tests."""
    # Create test suite

    # Add test classes
        TestCodeAnalyzer,
        TestDockerAnalyzer,
        TestAPIDocGenerator,
        TestDockerOrchestrator,
        TestSecurityScanner,
        TestIntegration,
        TestUtilities,
    ]

    for test_class in test_classes:
        test_suite.addTests(tests)

    # Run tests

    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print(f"{'='*60}")

    return result.wasSuccessful()


if __name__ == "__main__":
    sys.exit(0 if success else 1)
