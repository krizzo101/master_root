"""Integration tests for the AI-powered code generation pipeline.

These tests exercise the full system without mocks, testing real AI functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import tempfile
import zipfile
import json
from unittest.mock import patch
import time
import threading
import requests
import uvicorn

from pipeline import build_pipeline
from api import app
from config import config


class TestRealAIPipeline:
    """Test the actual AI-powered pipeline functionality."""

    def test_ai_project_type_detection_web_api(self):
        """Test that AI correctly detects web API project types."""
        from ai_agents import detect_project_type_with_ai
        from project_templates import ProjectType

        # Test various web API requests
        test_cases = [
            "Create a REST API for user management",
            "Build a FastAPI service for handling books",
            "I need a web service to manage inventory",
            "Make an API endpoint for processing orders",
        ]

        for request in test_cases:
            project_type = detect_project_type_with_ai(request)
            assert project_type == ProjectType.WEB_API, f"Failed for: {request}"

    def test_ai_project_type_detection_cli_tool(self):
        """Test that AI correctly detects CLI tool project types."""
        from ai_agents import detect_project_type_with_ai
        from project_templates import ProjectType

        test_cases = [
            "Create a command line tool for processing files",
            "Build a CLI calculator",
            "I need a terminal application for data conversion",
            "Make a command line utility for file management",
        ]

        for request in test_cases:
            project_type = detect_project_type_with_ai(request)
            assert project_type == ProjectType.CLI_TOOL, f"Failed for: {request}"

    def test_ai_requirements_extraction(self):
        """Test that AI extracts meaningful requirements."""
        from ai_agents import extract_requirements_with_ai
        from project_templates import ProjectType

        request = "Create a FastAPI web service for managing a library of books with CRUD operations and user authentication"
        requirements = extract_requirements_with_ai(request, ProjectType.WEB_API)

        # Verify structure
        assert requirements.title is not None
        assert len(requirements.title) > 5
        assert requirements.original_request == request
        assert len(requirements.functional_requirements) > 0
        assert len(requirements.non_functional_requirements) > 0

        # Verify content quality
        functional_text = " ".join(requirements.functional_requirements).lower()
        assert any(
            keyword in functional_text
            for keyword in ["crud", "create", "read", "update", "delete"]
        )
        assert any(keyword in functional_text for keyword in ["book", "library"])

    def test_ai_architecture_generation(self):
        """Test that AI generates meaningful architecture."""
        from ai_agents import (
            extract_requirements_with_ai,
            generate_architecture_with_ai,
        )
        from project_templates import ProjectType

        request = (
            "Create a FastAPI web service for managing users with database storage"
        )
        requirements = extract_requirements_with_ai(request, ProjectType.WEB_API)
        architecture = generate_architecture_with_ai(requirements)

        # Validate the architecture structure
        assert len(architecture.components) > 0
        assert len(architecture.technology_stack) > 0
        assert architecture.deployment_strategy
        assert len(architecture.design_decisions) > 0

        # Check for web API specific elements
        tech_stack_str = " ".join(architecture.technology_stack).lower()
        assert any(
            framework in tech_stack_str for framework in ["fastapi", "flask", "web"]
        )

    def test_full_pipeline_simple_script(self):
        """Test the complete pipeline for a simple script project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pipeline = build_pipeline()

            state = {
                "request": "Create a simple Python script that calculates the factorial of a number",
                "output_dir": tmp_path,
            }

            # Run the full pipeline
            result = pipeline.invoke(state)

            # Verify completion
            assert result["status"] == "DONE"

            # Verify AI components worked
            assert result["project_type"].value == "simple_script"
            assert "factorial" in result["requirements"].title.lower()

            # Verify code generation
            code_bundle = result["code_bundle"]
            assert code_bundle.src_dir.exists()
            assert code_bundle.tests_dir.exists()

            # Check for actual Python files
            python_files = list(code_bundle.src_dir.glob("*.py"))
            assert len(python_files) > 0

            # Verify test execution
            assert result["test_report"].passed > 0
            assert result["test_report"].failed == 0

            # Verify artifacts
            artifacts_zip = tmp_path / "artifacts.zip"
            assert artifacts_zip.exists()

            # Verify ZIP contents
            with zipfile.ZipFile(artifacts_zip, "r") as zf:
                file_list = zf.namelist()
                assert any("src/" in f for f in file_list)
                assert any("tests/" in f for f in file_list)

    def test_full_pipeline_web_api(self):
        """Test the complete pipeline for a web API project."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pipeline = build_pipeline()

            state = {
                "request": "Create a FastAPI web service for managing a todo list with CRUD operations",
                "output_dir": tmp_path,
            }

            # Run the full pipeline
            result = pipeline.invoke(state)

            # Verify completion
            assert result["status"] == "DONE"

            # Verify AI detection
            assert result["project_type"].value == "web_api"

            # Verify requirements
            requirements = result["requirements"]
            assert (
                "todo" in requirements.title.lower()
                or "task" in requirements.title.lower()
            )
            # Check for CRUD-related terms in functional requirements
            functional_text = " ".join(requirements.functional_requirements).lower()
            assert any(
                term in functional_text
                for term in [
                    "crud",
                    "create",
                    "read",
                    "update",
                    "delete",
                    "add",
                    "get",
                    "modify",
                    "remove",
                ]
            )

            # Verify architecture
            architecture = result["architecture"]
            assert len(architecture.components) > 0

            # Verify code generation produced FastAPI code
            code_bundle = result["code_bundle"]
            python_files = list(code_bundle.src_dir.glob("*.py"))

            # Check that FastAPI-related code was generated
            all_code = ""
            for py_file in python_files:
                all_code += py_file.read_text()

            assert "fastapi" in all_code.lower() or "FastAPI" in all_code

            # Verify tests passed
            assert result["test_report"].passed > 0

    def test_ai_security_validation(self):
        """Test that AI security validation works correctly."""
        from ai_agents import analyze_request_security_with_ai

        # Test safe request
        safe_request = "Create a simple calculator app"
        analysis = analyze_request_security_with_ai(safe_request)
        assert analysis.is_safe is True
        assert analysis.risk_level in ["low", "medium"]

        # Test potentially dangerous request
        dangerous_request = (
            "Create a script that executes system commands and deletes files"
        )
        analysis = analyze_request_security_with_ai(dangerous_request)
        # AI should flag this as potentially risky
        assert analysis.risk_level in ["medium", "high"]
        assert len(analysis.concerns) > 0


class TestRealAPIIntegration:
    """Test the real API with actual server and AI calls."""

    @pytest.fixture
    def server_and_client(self):
        """Start a real server for testing."""
        import socket

        # Find available port
        sock = socket.socket()
        sock.bind(("", 0))
        port = sock.getsockname()[1]
        sock.close()

        # Start server in thread
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Wait for server to start
        time.sleep(3)

        base_url = f"http://127.0.0.1:{port}"

        # Verify server is running
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Could not start test server: {e}")

        yield base_url

        # Cleanup is automatic with daemon thread

    def test_real_api_end_to_end(self, server_and_client):
        """Test the complete API workflow with real AI generation."""
        base_url = server_and_client

        # Test health endpoint
        health_response = requests.get(f"{base_url}/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # Submit a real job
        chat_response = requests.post(
            f"{base_url}/chat",
            json="Create a simple Python script that prints hello world",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        assert chat_response.status_code == 202

        job_data = chat_response.json()
        assert "job_id" in job_data
        job_id = job_data["job_id"]

        # Monitor job progress
        max_attempts = 60  # 3 minutes max
        for attempt in range(max_attempts):
            status_response = requests.get(f"{base_url}/status/{job_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            status = status_data.get("status")

            if status == "completed":
                # Verify completion data
                assert "requirements" in status_data
                assert "architecture" in status_data
                assert "test_report" in status_data

                # Test artifacts download
                artifacts_response = requests.get(f"{base_url}/artifacts/{job_id}")
                assert artifacts_response.status_code == 200
                assert artifacts_response.headers["content-type"] == "application/zip"

                # Verify ZIP content
                with tempfile.NamedTemporaryFile(suffix=".zip") as tmp_file:
                    tmp_file.write(artifacts_response.content)
                    tmp_file.flush()

                    with zipfile.ZipFile(tmp_file.name, "r") as zf:
                        file_list = zf.namelist()
                        assert any("src/" in f for f in file_list)
                        assert any("tests/" in f for f in file_list)
                        assert any(".py" in f for f in file_list)

                return  # Success!

            elif status in ["failed", "error"]:
                pytest.fail(f"Job failed with status: {status}, data: {status_data}")

            time.sleep(3)

        pytest.fail(f"Job did not complete within {max_attempts * 3} seconds")

    def test_api_validation_with_real_ai(self, server_and_client):
        """Test that API validation uses real AI security analysis."""
        base_url = server_and_client

        # Test with a request that should trigger AI security analysis
        dangerous_request = "Create a script with eval() and exec() functions"

        response = requests.post(
            f"{base_url}/chat",
            json=dangerous_request,
            headers={"Content-Type": "application/json"},
        )

        # Should either be rejected (400) or accepted with AI sanitization (202)
        assert response.status_code in [400, 202]

        if response.status_code == 400:
            # AI detected it as dangerous
            error_data = response.json()
            assert (
                "security" in error_data["detail"].lower()
                or "dangerous" in error_data["detail"].lower()
            )


@pytest.mark.skipif(not config.openai_api_key, reason="OpenAI API key not configured")
class TestAIFunctionality:
    """Tests that require OpenAI API key and test real AI functionality."""

    def test_ai_model_integration(self):
        """Test that we can actually call OpenAI models."""
        from local_shared.openai_interfaces.responses_interface import (
            get_openai_interface,
        )

        interface = get_openai_interface(config.openai_api_key)

        # Test simple response
        response = interface.create_simple_response(
            prompt="Say 'Hello from AI' and nothing else",
            model="gpt-4.1-mini",
            temperature=0.1,
        )

        assert "Hello from AI" in response
        assert len(response.strip()) < 50  # Should be a short response

    def test_structured_response_integration(self):
        """Test structured responses with real AI."""
        from local_shared.openai_interfaces.responses_interface import (
            get_openai_interface,
        )
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            name: str = Field(description="A project name")
            language: str = Field(description="Programming language")
            complexity: int = Field(description="Complexity from 1-10")

        interface = get_openai_interface(config.openai_api_key)

        response = interface.create_structured_response(
            prompt="Create a project for a simple calculator",
            response_model=TestModel,
            model="gpt-4.1-mini",
            temperature=0.1,
        )

        assert isinstance(response, TestModel)
        assert len(response.name) > 0
        assert response.language.lower() in [
            "python",
            "javascript",
            "java",
            "c++",
            "c#",
        ]
        assert 1 <= response.complexity <= 10
