#!/usr/bin/env python3
"""
Test suite for API Documentation Generator

This module contains comprehensive tests for the API documentation generator
functionality, including input validation, API parsing, documentation generation,
and output validation.
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

from api_doc_generator import (
    ApiDocGenerator,
    ApiParser,
    DocumentationGenerator,
    InputLoader,
    OpenApiGenerator,
)


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
                "file_paths": ["src/"],
                "app_name": "Test API",
                "description": "A test API",
                "version": "1.0.0",
                "output_format": "markdown",
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


class TestApiParser(unittest.TestCase):
    """Test cases for ApiParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.api_parser = ApiParser(self.logger)

    def test_detect_framework_fastapi(self):
        """Test FastAPI framework detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a FastAPI-like file
            fastapi_file.write_text(
                """
from fastapi import FastAPI


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/items/")
def create_item(item: dict):
    return item
"""
            )

            self.assertEqual(result, "fastapi")

    def test_detect_framework_flask(self):
        """Test Flask framework detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a Flask-like file
            flask_file.write_text(
                """
from flask import Flask


@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/api/items', methods=['POST'])
def create_item():
    return {'status': 'created'}
"""
            )

            self.assertEqual(result, "flask")

    def test_extract_fastapi_endpoints(self):
        """Test FastAPI endpoint extraction."""
from fastapi import FastAPI


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/items/")
def create_item(item: dict):
    return item

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
"""

        self.assertEqual(len(endpoints), 3)

        # Check first endpoint
        self.assertEqual(endpoints[0]["method"], "GET")
        self.assertEqual(endpoints[0]["path"], "/")
        self.assertEqual(endpoints[0]["function_name"], "read_root")

    def test_extract_pydantic_models(self):
        """Test Pydantic model extraction."""
from pydantic import BaseModel
from typing import Optional

class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float

class User(BaseModel):
    id: int
    username: str
    email: str
"""

        self.assertEqual(len(models), 2)

        # Check first model
        self.assertEqual(models[0]["name"], "Item")
        self.assertEqual(len(models[0]["fields"]), 4)


class TestOpenApiGenerator(unittest.TestCase):
    """Test cases for OpenApiGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.generator = OpenApiGenerator(self.logger)

    def test_generate_openapi_spec(self):
        """Test OpenAPI specification generation."""
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/",
                    "function_name": "read_root",
                    "description": "Read root endpoint",
                },
                {
                    "method": "POST",
                    "path": "/items/",
                    "function_name": "create_item",
                    "description": "Create new item",
                },
            ],
            "models": [
                {
                    "name": "Item",
                    "fields": [
                        {"name": "id", "type": "int"},
                        {"name": "name", "type": "str"},
                    ],
                }
            ],
        }


        # Verify basic structure
        self.assertEqual(spec["openapi"], "3.0.0")
        self.assertEqual(spec["info"]["title"], "Test API")
        self.assertIn("paths", spec)
        self.assertIn("components", spec)

    def test_generate_openapi_spec_empty(self):
        """Test OpenAPI specification generation with empty API info."""


        self.assertEqual(spec["openapi"], "3.0.0")
        self.assertEqual(spec["info"]["title"], "Empty API")
        self.assertEqual(len(spec["paths"]), 0)


class TestDocumentationGenerator(unittest.TestCase):
    """Test cases for DocumentationGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.generator = DocumentationGenerator(self.logger)

    def test_generate_documentation(self):
        """Test documentation generation."""
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/",
                    "function_name": "read_root",
                    "description": "Read root endpoint",
                }
            ],
            "models": [
                {
                    "name": "Item",
                    "fields": [
                        {"name": "id", "type": "int"},
                        {"name": "name", "type": "str"},
                    ],
                }
            ],
        }

            "openapi": "3.0.0",
            "info": {"title": "Test API"},
            "paths": {},
            "components": {},
        }


        self.assertIn("endpoints", docs)
        self.assertIn("models", docs)
        self.assertIn("examples", docs)
        self.assertEqual(len(docs["endpoints"]), 1)

    def test_generate_html_documentation(self):
        """Test HTML documentation generation."""
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/",
                    "function_name": "read_root",
                    "description": "Read root endpoint",
                }
            ],
            "models": [
                {
                    "name": "Item",
                    "fields": [
                        {"name": "id", "type": "int"},
                        {"name": "name", "type": "str"},
                    ],
                }
            ],
            "examples": [],
        }


        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Test API", html)
        self.assertIn("GET", html)
        self.assertIn("Item", html)


class TestApiDocGenerator(unittest.TestCase):
    """Test cases for main ApiDocGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = ApiDocGenerator()

    @patch("api_doc_generator.OpenAI")
    def test_generate_api_docs(self, mock_openai):
        """Test complete API documentation generation."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "endpoints": [
                    {
                        "method": "GET",
                        "path": "/",
                        "function_name": "read_root",
                        "description": "Read root endpoint",
                    }
                ],
                "models": [],
                "examples": [],
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create test input
        input_data.file_paths = ["src/"]
        input_data.app_name = "Test API"
        input_data.description = "A test API"
        input_data.version = "1.0.0"
        input_data.output_format = "markdown"

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

            # Mock the file path to point to our test directory
            with patch.object(input_data, "file_paths", [temp_dir]):

                # Verify result structure
                self.assertIsNotNone(result)
                self.assertIn("generated_files", result.__dict__)
                self.assertIn("api_info", result.__dict__)
                self.assertIn("openapi_spec", result.__dict__)
                self.assertIn("documentation", result.__dict__)

    def test_setup_directories(self):
        """Test directory setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.generator, "output_dir", temp_dir):
                self.generator._setup_directories()

                # Check that directories were created
                    "api_docs",
                    "openapi_specs",
                    "generated_docs",
                    "examples",
                ]

                for dir_name in expected_dirs:
                    self.assertTrue(dir_path.exists())


class TestApiDocGeneratorIntegration(unittest.TestCase):
    """Integration tests for API documentation generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.generator = ApiDocGenerator()

    @patch("api_doc_generator.OpenAI")
    def test_end_to_end_generation(self, mock_openai):
        """Test end-to-end API documentation generation."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "endpoints": [
                    {
                        "method": "GET",
                        "path": "/",
                        "function_name": "read_root",
                        "description": "Read root endpoint",
                    }
                ],
                "models": [],
                "examples": [],
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create test project structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.py
            main_file.write_text(
                """
from fastapi import FastAPI
from pydantic import BaseModel


class Item(BaseModel):
    id: int
    name: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/items/")
def create_item(item: Item):
    return item
"""
            )

            # Create models.py
            models_file.write_text(
                """
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
"""
            )

            # Create input data
            input_data.file_paths = [temp_dir]
            input_data.app_name = "Integration Test API"
            input_data.description = "An integration test API"
            input_data.version = "1.0.0"
            input_data.output_format = "markdown"

            # Generate documentation

            # Verify results
            self.assertIsNotNone(result)
            self.assertIn("generated_files", result.__dict__)
            self.assertIn("api_info", result.__dict__)
            self.assertIn("openapi_spec", result.__dict__)
            self.assertIn("documentation", result.__dict__)


if __name__ == "__main__":
    unittest.main()
