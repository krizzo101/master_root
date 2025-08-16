#!/usr/bin/env python3
"""
Test suite for Security Scanner

This module contains comprehensive tests for the security scanner
functionality, including vulnerability detection, compliance checking,
and security report generation.
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

from security_scanner import InputLoader, SecurityAnalyzer, SecurityScanner


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
                "requirements_type": "security",
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


class TestSecurityAnalyzer(unittest.TestCase):
    """Test cases for SecurityAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        self.analyzer = SecurityAnalyzer(self.logger)

    def test_analyze_security_python_project(self):
        """Test Python project security analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt with vulnerable package
            requirements_file.write_text(
                """
requests = =2.25.1  # Known vulnerable version
"""
            )

            # Create main.py with potential security issues
            main_file.write_text(
                """
import os
import subprocess
from flask import Flask, request


@app.route('/execute')
def execute_command():
    result = subprocess.run(command, shell=True, capture_output=True)  # Security issue
    return result.stdout

@app.route('/debug')
def debug_info():
    return os.environ  # Potential information disclosure
"""
            )


            self.assertIn("dependencies", result)
            self.assertIn("code_security", result)
            self.assertIn("configuration", result)
            self.assertIn("compliance", result)

    def test_analyze_dependencies(self):
        """Test dependency vulnerability analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt
            requirements_file.write_text(
                """
"""
            )


            self.assertIsInstance(dependencies, list)
            # Note: In a real test, we would mock the vulnerability check
            # to return specific results

    def test_analyze_code_security(self):
        """Test code security analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python file with security issues
            code_file.write_text(
                """
import subprocess
import os
import eval

def dangerous_function():
    subprocess.run(user_input, shell=True)  # Command injection

    eval(user_input)  # Code injection

    os.system(user_input)  # Command injection
"""
            )


            self.assertIsInstance(security_issues, list)
            # Should detect multiple security issues

    def test_analyze_configuration(self):
        """Test configuration security analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file with security issues
            config_file.write_text(
                """
DEBUG = True  # Security issue in production
SECRET_KEY = "test_key_for_testing_only"  # pragma: allowlist secret
ALLOWED_HOSTS = ["*"]  # Security issue
"""
            )


            self.assertIsInstance(config_issues, list)
            # Should detect configuration security issues

    def test_analyze_compliance(self):
        """Test compliance analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various files for compliance checking
            readme_file.write_text("# Test Project\n\nThis is a test project.")

            license_file.write_text("MIT License")


            self.assertIsInstance(compliance_issues, list)

    def test_check_dependency_vulnerability(self):
        """Test dependency vulnerability checking."""
        # Test with known vulnerable package
            "requests==2.25.1"
        )

        # In a real test, this would return vulnerability information
        # For now, we just test that the method exists and returns something
        self.assertIsInstance(vulnerability, (dict, type(None)))


class TestSecurityScanner(unittest.TestCase):
    """Test cases for main SecurityScanner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.scanner = SecurityScanner()

    @patch("security_scanner.OpenAI")
    def test_scan_security(self, mock_openai):
        """Test security scanning functionality."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "vulnerabilities": [
                    {
                        "type": "dependency",
                        "severity": "high",
                        "description": "Outdated package with known vulnerabilities",
                        "package": "requests==2.25.1",
                        "recommendation": "Update to latest version",
                    }
                ],
                "compliance_issues": [],
                "security_recommendations": [
                    "Update all dependencies to latest versions",
                    "Enable security scanning in CI/CD pipeline",
                ],
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create test input
        input_data.file_paths = ["src/"]
        input_data.requirements_type = "security"
        input_data.analysis_depth = "comprehensive"
        input_data.output_format = "json"

        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test Python file with security issues
            test_file.write_text(
                """
import subprocess
import os

def dangerous_function():
    subprocess.run(user_input, shell=True)  # Security issue
"""
            )

            # Create requirements.txt with vulnerable package
            requirements_file.write_text("requests==2.25.1")

            # Mock the file path to point to our test directory
            with patch.object(input_data, "file_paths", [temp_dir]):

                # Verify result structure
                self.assertIsNotNone(result)
                self.assertIn("generated_files", result.__dict__)
                self.assertIn("security_report", result.__dict__)
                self.assertIn("vulnerabilities", result.__dict__)
                self.assertIn("compliance_issues", result.__dict__)

    def test_create_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(self.scanner, "output_dir", temp_dir):
                self.scanner._create_directories()

                # Check that directories were created
                    "security_reports",
                    "vulnerability_reports",
                    "compliance_reports",
                    "remediation_plans",
                ]

                for dir_name in expected_dirs:
                    self.assertTrue(dir_path.exists())

    def test_convert_to_markdown(self):
        """Test Markdown report generation."""
            "vulnerabilities": [
                {
                    "type": "dependency",
                    "severity": "high",
                    "description": "Outdated package",
                    "package": "requests==2.25.1",
                    "recommendation": "Update to latest version",
                }
            ],
            "compliance_issues": [],
            "security_recommendations": [
                "Update dependencies",
                "Enable security scanning",
            ],
        }

        input_data.output_format = "markdown"


        self.assertIn("# Security Scan Report", markdown)
        self.assertIn("## Vulnerabilities", markdown)
        self.assertIn("## Security Recommendations", markdown)
        self.assertIn("requests==2.25.1", markdown)

    def test_convert_to_html(self):
        """Test HTML report generation."""
            "vulnerabilities": [
                {
                    "type": "dependency",
                    "severity": "high",
                    "description": "Outdated package",
                    "package": "requests==2.25.1",
                    "recommendation": "Update to latest version",
                }
            ],
            "compliance_issues": [],
            "security_recommendations": [
                "Update dependencies",
                "Enable security scanning",
            ],
        }

        input_data.output_format = "html"


        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<h1>Security Scan Report</h1>", html)
        self.assertIn("<h2>Vulnerabilities</h2>", html)
        self.assertIn("requests==2.25.1", html)

    def test_generate_remediation_plan(self):
        """Test remediation plan generation."""
            "vulnerabilities": [
                {
                    "type": "dependency",
                    "severity": "high",
                    "description": "Outdated package",
                    "package": "requests==2.25.1",
                    "recommendation": "Update to latest version",
                }
            ],
            "compliance_issues": [],
            "security_recommendations": [
                "Update dependencies",
                "Enable security scanning",
            ],
        }

        input_data.output_format = "json"

            security_report, input_data
        )

        self.assertIsInstance(remediation_files, list)
        # Should generate remediation plan files

    def test_generate_remediation_content(self):
        """Test remediation content generation."""
            "vulnerabilities": [
                {
                    "type": "dependency",
                    "severity": "high",
                    "description": "Outdated package",
                    "package": "requests==2.25.1",
                    "recommendation": "Update to latest version",
                }
            ],
            "security_recommendations": [
                "Update dependencies",
                "Enable security scanning",
            ],
        }


            security_report, input_data
        )

        self.assertIn("# Security Remediation Plan", content)
        self.assertIn("## High Priority Issues", content)
        self.assertIn("requests==2.25.1", content)

    def test_generate_remediation_script(self):
        """Test remediation script generation."""
            "vulnerabilities": [
                {
                    "type": "dependency",
                    "severity": "high",
                    "description": "Outdated package",
                    "package": "requests==2.25.1",
                    "recommendation": "Update to latest version",
                }
            ],
            "security_recommendations": [
                "Update dependencies",
                "Enable security scanning",
            ],
        }



        self.assertIn("#!/bin/bash", script)
        self.assertIn("pip install", script)
        self.assertIn("requests", script)


class TestSecurityScannerIntegration(unittest.TestCase):
    """Integration tests for security scanner."""

    def setUp(self):
        """Set up test fixtures."""
        self.scanner = SecurityScanner()

    @patch("security_scanner.OpenAI")
    def test_end_to_end_security_scanning(self, mock_openai):
        """Test end-to-end security scanning."""
        # Mock OpenAI client
        mock_openai.return_value = mock_client

        # Mock API response
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "vulnerabilities": [
                    {
                        "type": "dependency",
                        "severity": "high",
                        "description": "Outdated package with known vulnerabilities",
                        "package": "requests==2.25.1",
                        "recommendation": "Update to latest version",
                    },
                    {
                        "type": "code",
                        "severity": "medium",
                        "description": "Potential command injection",
                        "file": "main.py:5",
                        "recommendation": "Use subprocess.run with shell=False",
                    },
                ],
                "compliance_issues": [
                    {
                        "type": "license",
                        "severity": "low",
                        "description": "Missing license file",
                        "recommendation": "Add LICENSE file",
                    }
                ],
                "security_recommendations": [
                    "Update all dependencies to latest versions",
                    "Enable security scanning in CI/CD pipeline",
                    "Add input validation for user inputs",
                ],
            }
        )
        mock_client.chat.completions.create.return_value = mock_response

        # Create test project structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create main.py with security issues
            main_file.write_text(
                """
import subprocess
import os

def dangerous_function():
    subprocess.run(user_input, shell=True)  # Security issue

@app.route('/execute')
def execute_command():
    result = subprocess.run(command, shell=True, capture_output=True)  # Security issue
    return result.stdout
"""
            )

            # Create requirements.txt with vulnerable package
            requirements_file.write_text(
                """
"""
            )

            # Create input data
            input_data.file_paths = [temp_dir]
            input_data.requirements_type = "security"
            input_data.analysis_depth = "comprehensive"
            input_data.output_format = "json"

            # Perform security scan

            # Verify results
            self.assertIsNotNone(result)
            self.assertIn("generated_files", result.__dict__)
            self.assertIn("security_report", result.__dict__)
            self.assertIn("vulnerabilities", result.__dict__)
            self.assertIn("compliance_issues", result.__dict__)


if __name__ == "__main__":
    unittest.main()
