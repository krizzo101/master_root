#!/usr/bin/env python3
"""
Test suite for Requirements Analyzer

This module contains comprehensive tests for the requirements analyzer
functionality, including natural language processing, requirements extraction,
and structured output generation.
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

from requirements_analyzer import (
    InputLoader,
    RequirementsAnalyzer,
    RequirementsProcessor,
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
                "requirements_text": "The system should allow users to create accounts and login.",
                "requirements_type": "functional",
                "analysis_depth": "comprehensive",
                "output_format": "json",
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


class TestRequirementsAnalyzer(unittest.TestCase):
    """Test cases for RequirementsAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.analyzer = RequirementsAnalyzer(self.logger)

    def test_analyze_requirements_basic(self):
        """Test basic requirements analysis."""
        The system should allow users to create accounts and login.
        Users should be able to upload files and share them with other users.
        The system must be secure and handle user data privacy.
        Performance should be good with response times under 2 seconds.
        """


        self.assertIn("functional_requirements", result)
        self.assertIn("non_functional_requirements", result)
        self.assertIn("user_stories", result)
        self.assertIn("acceptance_criteria", result)
        self.assertIn("technical_constraints", result)
        self.assertIn("dependencies", result)
        self.assertIn("assumptions", result)
        self.assertIn("risks", result)

    def test_extract_functional_requirements(self):
        """Test functional requirements extraction."""
        The system should allow users to create accounts and login.
        Users should be able to upload files and share them with other users.
        The system must support file versioning and backup.
        """


        self.assertIsInstance(requirements, list)
        self.assertGreater(len(requirements), 0)

        # Check that requirements are properly structured
        for req in requirements:
            self.assertIn("description", req)
            self.assertIn("priority", req)
            self.assertIn("category", req)

    def test_extract_non_functional_requirements(self):
        """Test non-functional requirements extraction."""
        The system must be secure and handle user data privacy.
        Performance should be good with response times under 2 seconds.
        The system should be available 99.9% of the time.
        The interface should be user-friendly and accessible.
        """


        self.assertIsInstance(requirements, list)
        self.assertGreater(len(requirements), 0)

        # Check that requirements are properly structured
        for req in requirements:
            self.assertIn("description", req)
            self.assertIn("category", req)
            self.assertIn("metrics", req)

    def test_extract_user_stories(self):
        """Test user stories extraction."""
        As a user, I want to create an account so that I can access the system.
        As a user, I want to upload files so that I can store my documents.
        As a user, I want to share files so that I can collaborate with others.
        """


        self.assertIsInstance(stories, list)
        self.assertGreater(len(stories), 0)

        # Check that user stories are properly structured
        for story in stories:
            self.assertIn("as_a", story)
            self.assertIn("i_want", story)
            self.assertIn("so_that", story)
            self.assertIn("priority", story)

    def test_extract_acceptance_criteria(self):
        """Test acceptance criteria extraction."""
        Given a user is on the login page
        When they enter valid credentials
        Then they should be redirected to the dashboard

        Given a user wants to upload a file
        When they select a file and click upload
        Then the file should be stored and a success message shown
        """


        self.assertIsInstance(criteria, list)
        self.assertGreater(len(criteria), 0)

        # Check that acceptance criteria are properly structured
        for criterion in criteria:
            self.assertIn("given", criterion)
            self.assertIn("when", criterion)
            self.assertIn("then", criterion)

    def test_extract_technical_constraints(self):
        """Test technical constraints extraction."""
        The system must use Python 3.11 or higher.
        The database must be PostgreSQL.
        The system must run on Linux servers.
        The API must follow REST principles.
        """


        self.assertIsInstance(constraints, list)
        self.assertGreater(len(constraints), 0)

        # Check that constraints are properly structured
        for constraint in constraints:
            self.assertIn("description", constraint)
            self.assertIn("category", constraint)
            self.assertIn("impact", constraint)

    def test_extract_dependencies(self):
        """Test dependencies extraction."""
        The system depends on a third-party authentication service.
        File storage requires cloud storage integration.
        The system needs email service for notifications.
        """


        self.assertIsInstance(dependencies, list)
        self.assertGreater(len(dependencies), 0)

        # Check that dependencies are properly structured
        for dep in dependencies:
            self.assertIn("name", dep)
            self.assertIn("type", dep)
            self.assertIn("description", dep)

    def test_extract_assumptions(self):
        """Test assumptions extraction."""
        We assume users have basic computer literacy.
        We assume the system will have stable internet connectivity.
        We assume users will provide valid email addresses.
        """


        self.assertIsInstance(assumptions, list)
        self.assertGreater(len(assumptions), 0)

        # Check that assumptions are properly structured
        for assumption in assumptions:
            self.assertIn("description", assumption)
            self.assertIn("impact", assumption)

    def test_extract_risks(self):
        """Test risks extraction."""
        Risk: Users may not adopt the new system.
        Risk: Data security breaches could occur.
        Risk: Performance issues under high load.
        """


        self.assertIsInstance(risks, list)
        self.assertGreater(len(risks), 0)

        # Check that risks are properly structured
        for risk in risks:
            self.assertIn("description", risk)
            self.assertIn("probability", risk)
            self.assertIn("impact", risk)
            self.assertIn("mitigation", risk)

    def test_analyze_priority_levels(self):
        """Test priority level analysis."""
        High priority: User authentication and security.
        Medium priority: File sharing features.
        Low priority: Advanced search functionality.
        """


        self.assertIsInstance(priorities, dict)
        self.assertIn("high", priorities)
        self.assertIn("medium", priorities)
        self.assertIn("low", priorities)

    def test_analyze_complexity_estimates(self):
        """Test complexity estimation."""
        Simple: User registration form.
        Medium: File upload with progress tracking.
        Complex: Real-time collaboration features.
        """


        self.assertIsInstance(complexities, dict)
        self.assertIn("simple", complexities)
        self.assertIn("medium", complexities)
        self.assertIn("complex", complexities)


class TestRequirementsProcessor(unittest.TestCase):
    """Test cases for main RequirementsProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = RequirementsProcessor()

    @patch("requirements_analyzer.OpenAI")
    def test_analyze_requirements(self, mock_openai):
        """Test requirements analysis functionality."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "functional_requirements": [
                    {
                        "description": "User authentication system",
                        "priority": "high",
                        "category": "security",
                    }
                ],
                "non_functional_requirements": [
                    {
                        "description": "Response time under 2 seconds",
                        "category": "performance",
                        "metrics": "2 seconds",
                    }
                ],
                "user_stories": [
                    {
                        "as_a": "user",
                        "i_want": "to create an account",
                        "so_that": "I can access the system",
                        "priority": "high",
                    }
                ],
                "acceptance_criteria": [],
                "technical_constraints": [],
                "dependencies": [],
                "assumptions": [],
                "risks": [],
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create test input
        input_data.requirements_text = (
            "The system should allow users to create accounts and login."
        )
        input_data.requirements_type = "functional"
        input_data.analysis_depth = "comprehensive"
        input_data.output_format = "json"


        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIn("generated_files", result.__dict__)
        self.assertIn("requirements_analysis", result.__dict__)
        self.assertIn("structured_requirements", result.__dict__)

    def test_create_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.processor, "output_dir", temp_dir):
                self.processor._create_directories()

                # Check that directories were created
                    "requirements_analysis",
                    "user_stories",
                    "acceptance_criteria",
                    "technical_specs",
                ]

                for dir_name in expected_dirs:
                    self.assertTrue(dir_path.exists())

    def test_convert_to_markdown(self):
        """Test Markdown report generation."""
            "functional_requirements": [
                {
                    "description": "User authentication system",
                    "priority": "high",
                    "category": "security",
                }
            ],
            "non_functional_requirements": [
                {
                    "description": "Response time under 2 seconds",
                    "category": "performance",
                    "metrics": "2 seconds",
                }
            ],
            "user_stories": [
                {
                    "as_a": "user",
                    "i_want": "to create an account",
                    "so_that": "I can access the system",
                    "priority": "high",
                }
            ],
            "acceptance_criteria": [],
            "technical_constraints": [],
            "dependencies": [],
            "assumptions": [],
            "risks": [],
        }

        input_data.output_format = "markdown"

            requirements_analysis, input_data
        )

        self.assertIn("# Requirements Analysis Report", markdown)
        self.assertIn("## Functional Requirements", markdown)
        self.assertIn("## Non-Functional Requirements", markdown)
        self.assertIn("## User Stories", markdown)
        self.assertIn("User authentication system", markdown)

    def test_convert_to_html(self):
        """Test HTML report generation."""
            "functional_requirements": [
                {
                    "description": "User authentication system",
                    "priority": "high",
                    "category": "security",
                }
            ],
            "non_functional_requirements": [
                {
                    "description": "Response time under 2 seconds",
                    "category": "performance",
                    "metrics": "2 seconds",
                }
            ],
            "user_stories": [
                {
                    "as_a": "user",
                    "i_want": "to create an account",
                    "so_that": "I can access the system",
                    "priority": "high",
                }
            ],
            "acceptance_criteria": [],
            "technical_constraints": [],
            "dependencies": [],
            "assumptions": [],
            "risks": [],
        }

        input_data.output_format = "html"


        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<h1>Requirements Analysis Report</h1>", html)
        self.assertIn("<h2>Functional Requirements</h2>", html)
        self.assertIn("User authentication system", html)

    def test_generate_user_stories_template(self):
        """Test user stories template generation."""
            "user_stories": [
                {
                    "as_a": "user",
                    "i_want": "to create an account",
                    "so_that": "I can access the system",
                    "priority": "high",
                },
                {
                    "as_a": "user",
                    "i_want": "to upload files",
                    "so_that": "I can store my documents",
                    "priority": "medium",
                },
            ]
        }


        self.assertIn("# User Stories", template)
        self.assertIn("## High Priority", template)
        self.assertIn("## Medium Priority", template)
        self.assertIn("As a user", template)
        self.assertIn("I want to create an account", template)

    def test_generate_acceptance_criteria_template(self):
        """Test acceptance criteria template generation."""
            "acceptance_criteria": [
                {
                    "given": "a user is on the login page",
                    "when": "they enter valid credentials",
                    "then": "they should be redirected to the dashboard",
                }
            ]
        }

            requirements_analysis
        )

        self.assertIn("# Acceptance Criteria", template)
        self.assertIn("## User Authentication", template)
        self.assertIn("**Given**", template)
        self.assertIn("**When**", template)
        self.assertIn("**Then**", template)


class TestRequirementsProcessorIntegration(unittest.TestCase):
    """Integration tests for requirements processor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = RequirementsProcessor()

    @patch("requirements_analyzer.OpenAI")
    def test_end_to_end_requirements_analysis(self, mock_openai):
        """Test end-to-end requirements analysis."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "functional_requirements": [
                    {
                        "description": "User authentication system",
                        "priority": "high",
                        "category": "security",
                    },
                    {
                        "description": "File upload and sharing",
                        "priority": "medium",
                        "category": "features",
                    },
                ],
                "non_functional_requirements": [
                    {
                        "description": "Response time under 2 seconds",
                        "category": "performance",
                        "metrics": "2 seconds",
                    },
                    {
                        "description": "99.9% uptime",
                        "category": "availability",
                        "metrics": "99.9%",
                    },
                ],
                "user_stories": [
                    {
                        "as_a": "user",
                        "i_want": "to create an account",
                        "so_that": "I can access the system",
                        "priority": "high",
                    },
                    {
                        "as_a": "user",
                        "i_want": "to upload files",
                        "so_that": "I can store my documents",
                        "priority": "medium",
                    },
                ],
                "acceptance_criteria": [
                    {
                        "given": "a user is on the login page",
                        "when": "they enter valid credentials",
                        "then": "they should be redirected to the dashboard",
                    }
                ],
                "technical_constraints": [
                    {
                        "description": "Must use Python 3.11+",
                        "category": "technology",
                        "impact": "high",
                    }
                ],
                "dependencies": [
                    {
                        "name": "Authentication service",
                        "type": "external",
                        "description": "Third-party authentication provider",
                    }
                ],
                "assumptions": [
                    {
                        "description": "Users have basic computer literacy",
                        "impact": "medium",
                    }
                ],
                "risks": [
                    {
                        "description": "Low user adoption",
                        "probability": "medium",
                        "impact": "high",
                        "mitigation": "User training and support",
                    }
                ],
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create input data
        input_data.requirements_text = """
        The system should allow users to create accounts and login.
        Users should be able to upload files and share them with other users.
        The system must be secure and handle user data privacy.
        Performance should be good with response times under 2 seconds.
        The system should be available 99.9% of the time.
        """
        input_data.requirements_type = "functional"
        input_data.analysis_depth = "comprehensive"
        input_data.output_format = "json"

        # Perform requirements analysis

        # Verify results
        self.assertIsNotNone(result)
        self.assertIn("generated_files", result.__dict__)
        self.assertIn("requirements_analysis", result.__dict__)
        self.assertIn("structured_requirements", result.__dict__)


if __name__ == "__main__":
    unittest.main()
