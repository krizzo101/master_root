#!/usr/bin/env python3
"""
Test suite for Docker Orchestrator

This module contains comprehensive tests for the Docker orchestrator
functionality, including application analysis, Docker configuration generation,
and multi-stage build management.
"""

import json
import os
from pathlib import Path

# Add the script directory to Python path for imports
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

if script_dir not in sys.path:
    sys.path.append(script_dir)

from docker_orchestrator import DockerAnalyzer, DockerOrchestrator, InputLoader


class TestInputLoader(unittest.TestCase):
    """Test cases for InputLoader class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.input_loader = InputLoader(self.logger)

    def test_load_input_file_valid_json(self):
        """Test loading a valid JSON input file."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                "app_path": "src/",
                "multi_stage": True,
                "security_scanning": True,
                "performance_optimization": True,
                "orchestration": "docker-compose",
            }
            json.dump(test_data, f)

        try:
            self.assertEqual(result, test_data)
            self.logger.log_info.assert_called()
        finally:
            os.unlink(temp_file)

    def test_load_input_file_not_found(self):
        """Test loading a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.input_loader.load_input_file("nonexistent.json")

    def test_load_input_file_invalid_json(self):
        """Test loading a file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")

        try:
            with self.assertRaises(ValueError):
                self.input_loader.load_input_file(temp_file)
        finally:
            os.unlink(temp_file)


class TestDockerAnalyzer(unittest.TestCase):
    """Test cases for DockerAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.analyzer = DockerAnalyzer(self.logger)

    def test_analyze_application_python(self):
        """Test Python application analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt
            requirements_file.write_text(
                """
"""
            )

            # Create main.py
            main_file.write_text(
                """
from fastapi import FastAPI


@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
            )


            self.assertEqual(result["language"], "python")
            self.assertIn("fastapi", result["dependencies"])
            self.assertIn("uvicorn", result["dependencies"])
            self.assertIn("pydantic", result["dependencies"])

    def test_analyze_application_nodejs(self):
        """Test Node.js application analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_file.write_text(
                """
{
  "name": "test-app",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5"
  }
}
"""
            )

            # Create index.js
            index_file.write_text(
                """
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello World!' });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});
"""
            )


            self.assertEqual(result["language"], "javascript")
            self.assertIn("express", result["dependencies"])
            self.assertIn("cors", result["dependencies"])

    def test_extract_python_dependencies(self):
        """Test Python dependency extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements_file.write_text(
                """
uvicorn[standard]==0.24.0
pydantic>=2.0.0
requests
"""
            )


            self.assertIn("fastapi", dependencies)
            self.assertIn("uvicorn", dependencies)
            self.assertIn("pydantic", dependencies)
            self.assertIn("requests", dependencies)

    def test_extract_node_dependencies(self):
        """Test Node.js dependency extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            package_file.write_text(
                """
{
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5"
  },
  "devDependencies": {
    "jest": "^29.7.0"
  }
}
"""
            )


            self.assertIn("express", dependencies)
            self.assertIn("cors", dependencies)
            self.assertIn("jest", dependencies)

    def test_detect_framework_python_fastapi(self):
        """Test FastAPI framework detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create FastAPI app
            main_file.write_text(
                """
from fastapi import FastAPI


@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
            )

            self.assertEqual(framework, "fastapi")

    def test_detect_framework_python_flask(self):
        """Test Flask framework detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Flask app
            app_file.write_text(
                """
from flask import Flask


@app.route('/')
def hello():
    return 'Hello World!'
"""
            )

            self.assertEqual(framework, "flask")

    def test_detect_framework_javascript_express(self):
        """Test Express framework detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Express app
            index_file.write_text(
                """
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello World!' });
});

app.listen(3000);
"""
            )

            self.assertEqual(framework, "express")

    def test_detect_entry_point_python(self):
        """Test Python entry point detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.py
            main_file.write_text(
                """
from fastapi import FastAPI


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
            )

            self.assertEqual(entry_point, "main.py")

    def test_detect_entry_point_javascript(self):
        """Test JavaScript entry point detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create index.js
            index_file.write_text(
                """
const express = require('express');
const app = express();

app.listen(3000);
"""
            )

                Path(temp_dir), "javascript"
            )
            self.assertEqual(entry_point, "index.js")


class TestDockerOrchestrator(unittest.TestCase):
    """Test cases for main DockerOrchestrator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = DockerOrchestrator()

    @patch("docker_orchestrator.OpenAI")
    def test_generate_docker_configuration(self, mock_openai):
        """Test Docker configuration generation."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "base_image": "python:3.11-slim",
                "dependencies": ["fastapi", "uvicorn"],
                "entry_point": "main.py",
                "ports": [8000],
                "environment": ["PORT=8000"],
                "volumes": [],
                "security_scanning": True,
                "multi_stage": True,
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create test input
        input_data.app_path = "src/"
        input_data.multi_stage = True
        input_data.security_scanning = True
        input_data.performance_optimization = True
        input_data.orchestration = "docker-compose"

        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file
            test_file.write_text(
                """
from fastapi import FastAPI


@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
            )

            # Create requirements.txt
            requirements_file.write_text("fastapi==0.104.1\nuvicorn==0.24.0")

            # Mock the app path to point to our test directory
            with patch.object(input_data, "app_path", temp_dir):

                # Verify result structure
                self.assertIsNotNone(result)
                self.assertIn("generated_files", result.__dict__)
                self.assertIn("docker_config", result.__dict__)
                self.assertIn("orchestration_files", result.__dict__)

    def test_create_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.orchestrator, "output_dir", temp_dir):
                self.orchestrator._create_directories()

                # Check that directories were created
                    "docker_files",
                    "orchestration",
                    "security_scripts",
                    "build_scripts",
                ]

                for dir_name in expected_dirs:
                    self.assertTrue(dir_path.exists())

    def test_generate_dockerfile_single_stage(self):
        """Test single-stage Dockerfile generation."""
            "base_image": "python:3.11-slim",
            "dependencies": ["fastapi", "uvicorn"],
            "entry_point": "main.py",
            "ports": [8000],
            "environment": ["PORT=8000"],
        }

        input_data.app_path = "src/"
        input_data.multi_stage = False

            docker_config, input_data
        )

        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn("COPY requirements.txt", dockerfile)
        self.assertIn("RUN pip install", dockerfile)
        self.assertIn("EXPOSE 8000", dockerfile)
        self.assertIn("CMD", dockerfile)

    def test_generate_dockerfile_multi_stage(self):
        """Test multi-stage Dockerfile generation."""
            "base_image": "python:3.11-slim",
            "dependencies": ["fastapi", "uvicorn"],
            "entry_point": "main.py",
            "ports": [8000],
            "environment": ["PORT=8000"],
        }

        input_data.app_path = "src/"
        input_data.multi_stage = True

            docker_config, input_data
        )

        self.assertIn("FROM python:3.11-slim AS builder", dockerfile)
        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn("COPY --from=builder", dockerfile)
        self.assertIn("EXPOSE 8000", dockerfile)

    def test_generate_dockerignore(self):
        """Test .dockerignore generation."""
            "base_image": "python:3.11-slim",
            "dependencies": ["fastapi", "uvicorn"],
        }

        input_data.app_path = "src/"

            docker_config, input_data
        )

        self.assertIn("__pycache__", dockerignore)
        self.assertIn("*.pyc", dockerignore)
        self.assertIn(".git", dockerignore)
        self.assertIn("node_modules", dockerignore)

    def test_generate_docker_compose(self):
        """Test Docker Compose generation."""
            "base_image": "python:3.11-slim",
            "dependencies": ["fastapi", "uvicorn"],
            "ports": [8000],
            "environment": ["PORT=8000"],
        }

        input_data.app_path = "src/"
        input_data.orchestration = "docker-compose"

            docker_config, input_data
        )

        self.assertIn("version", compose_config)
        self.assertIn("services", compose_config)
        self.assertIn("app", compose_config["services"])
        self.assertIn("build", compose_config["services"]["app"])

    def test_generate_kubernetes_manifest(self):
        """Test Kubernetes manifest generation."""
            "base_image": "python:3.11-slim",
            "dependencies": ["fastapi", "uvicorn"],
            "ports": [8000],
            "environment": ["PORT=8000"],
        }

        input_data.app_path = "src/"
        input_data.orchestration = "kubernetes"

            docker_config, input_data
        )

        self.assertIn("apiVersion", k8s_config)
        self.assertIn("kind", k8s_config)
        self.assertIn("metadata", k8s_config)
        self.assertIn("spec", k8s_config)

    def test_generate_security_scan_script(self):
        """Test security scan script generation."""
            "base_image": "python:3.11-slim",
            "dependencies": ["fastapi", "uvicorn"],
        }

        input_data.app_path = "src/"
        input_data.security_scanning = True

            docker_config, input_data
        )

        self.assertIn("#!/bin/bash", script)
        self.assertIn("docker run", script)
        self.assertIn("security scan", script.lower())

    def test_generate_build_script(self):
        """Test build script generation."""
            "base_image": "python:3.11-slim",
            "dependencies": ["fastapi", "uvicorn"],
        }

        input_data.app_path = "src/"
        input_data.multi_stage = True


        self.assertIn("#!/bin/bash", script)
        self.assertIn("docker build", script)
        self.assertIn("docker run", script)


class TestDockerOrchestratorIntegration(unittest.TestCase):
    """Integration tests for Docker orchestrator."""

    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = DockerOrchestrator()

    @patch("docker_orchestrator.OpenAI")
    def test_end_to_end_docker_generation(self, mock_openai):
        """Test end-to-end Docker configuration generation."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "base_image": "python:3.11-slim",
                "dependencies": ["fastapi", "uvicorn"],
                "entry_point": "main.py",
                "ports": [8000],
                "environment": ["PORT=8000"],
                "volumes": [],
                "security_scanning": True,
                "multi_stage": True,
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create test project structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.py
            main_file.write_text(
                """
from fastapi import FastAPI


@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
            )

            # Create requirements.txt
            requirements_file.write_text(
                """
uvicorn[standard]==0.24.0
"""
            )

            # Create input data
            input_data.app_path = temp_dir
            input_data.multi_stage = True
            input_data.security_scanning = True
            input_data.performance_optimization = True
            input_data.orchestration = "docker-compose"

            # Generate Docker configuration

            # Verify results
            self.assertIsNotNone(result)
            self.assertIn("generated_files", result.__dict__)
            self.assertIn("docker_config", result.__dict__)
            self.assertIn("orchestration_files", result.__dict__)


if __name__ == "__main__":
    unittest.main()
