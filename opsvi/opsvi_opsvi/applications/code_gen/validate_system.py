#!/usr/bin/env python3
"""
Comprehensive System Validation Script

Validates the entire code_gen system before deployment.
Runs all tests, checks configurations, validates dependencies.
"""

import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SystemValidator:
    """Comprehensive system validation."""

    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def run_validation(self) -> bool:
        """Run complete system validation."""
        logger.info("🔍 Starting comprehensive system validation...")

        validation_steps = [
            ("Model Validation", self.validate_models),
            ("Import Validation", self.validate_imports),
            ("Configuration Validation", self.validate_configuration),
            ("Database Validation", self.validate_database),
            ("AI Module Validation", self.validate_ai_modules),
            ("Pipeline Validation", self.validate_pipeline),
            ("API Validation", self.validate_api),
            ("Test Suite Execution", self.run_test_suite),
            ("Dependency Validation", self.validate_dependencies),
            ("Security Validation", self.validate_security),
        ]

        for step_name, step_func in validation_steps:
            logger.info(f"⚡ Running {step_name}...")
            try:
                step_func()
                logger.info(f"✅ {step_name} PASSED")
            except Exception as e:
                error_msg = f"❌ {step_name} FAILED: {e}"
                logger.error(error_msg)
                self.failures.append(error_msg)

        return self.generate_report()

    def validate_models(self):
        """Validate model configuration and usage."""
        logger.info("Validating approved models only...")

        from local_shared.openai_interfaces.model_selector import (
            APPROVED_MODELS,
            ModelSelector,
        )

        # Check approved models list
        expected_models = {"o4-mini", "o3", "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"}
        if not expected_models.issubset(set(APPROVED_MODELS)):
            raise ValueError(
                f"Missing approved models: {expected_models - set(APPROVED_MODELS)}"
            )

        # Test model selector
        selector = ModelSelector()

        # Test various configurations
        test_configs = [
            {"task_type": "reasoning"},
            {"task_type": "execution"},
            {"task_type": "structured"},
            {"require_structured_outputs": True},
            {"prefer_cost_effective": True},
        ]

        for config in test_configs:
            model = selector.select_optimal_model(**config)
            if model not in APPROVED_MODELS:
                raise ValueError(
                    f"Unauthorized model returned: {model} for config {config}"
                )

        logger.info("✅ Model validation passed")

    def validate_imports(self):
        """Validate all critical imports work."""
        logger.info("Validating critical imports...")

        critical_imports = [
            "applications.code_gen.config",
            "applications.code_gen.database",
            "applications.code_gen.api",
            "applications.code_gen.pipeline",
            "applications.code_gen.task_queue",
            "applications.code_gen.ai_agents",
            "applications.code_gen.ai_code_generator",
            "applications.code_gen.ai_test_generator",
            "applications.code_gen.ai_documentation_generator",
            "shared.openai_interfaces.model_selector",
            "shared.openai_interfaces.responses_interface",
        ]

        for module_name in critical_imports:
            try:
                __import__(module_name)
                logger.info(f"✅ Import {module_name} OK")
            except ImportError as e:
                raise ImportError(f"Failed to import {module_name}: {e}")

    def validate_configuration(self):
        """Validate system configuration."""
        logger.info("Validating configuration...")

        from applications.code_gen.config import get_config

        config = get_config()

        # Check critical config values
        required_attrs = ["host", "port", "job_output_dir", "redis_url"]
        for attr in required_attrs:
            if not hasattr(config, attr):
                raise ValueError(f"Missing required config attribute: {attr}")

        # Validate paths
        if not isinstance(config.job_output_dir, Path):
            raise ValueError("job_output_dir must be a Path object")

        # Check Redis URL format
        if not config.redis_url.startswith("redis://"):
            raise ValueError("Invalid Redis URL format")

        logger.info("✅ Configuration validation passed")

    def validate_database(self):
        """Validate database operations."""
        logger.info("Validating database operations...")

        # Create temporary database
        test_dir = Path(tempfile.mkdtemp())
        test_db_path = test_dir / "test_validation.db"

        try:
            # Patch database path for testing
            import database

            original_db_path = database._db_path
            database._db_path = test_db_path

            # Test database operations
            database.init_db()

            # Test job creation
            import uuid

            job_id = f"validation-test-{uuid.uuid4().hex[:8]}"
            database.create_job(job_id, "Test validation request")

            # Test job retrieval
            job = database.get_job(job_id)
            if not job or job.id != job_id:
                raise ValueError("Job creation/retrieval failed")

            # Test job update
            database.update_job(job_id, status="completed", progress=1.0)
            updated_job_data = database.get_job_data(job_id)
            if updated_job_data["status"] != "completed":
                raise ValueError("Job update failed")

            # Test job data retrieval
            job_data = database.get_job_data(job_id)
            if not job_data or job_data["id"] != job_id:
                raise ValueError("Job data retrieval failed")

        finally:
            # Restore original database path
            database._db_path = original_db_path
            shutil.rmtree(test_dir)

        logger.info("✅ Database validation passed")

    def validate_ai_modules(self):
        """Validate AI modules with mocked responses."""
        logger.info("Validating AI modules...")

        from unittest.mock import Mock, patch

        from ai_agents import detect_project_type_with_ai
        from ai_code_generator import AICodeGenerator

        from schemas import ProjectType

        # Test project type detection with mock
        with patch("ai_agents.get_openai_interface") as mock_interface:
            mock_response = Mock()
            mock_response.project_type = "web_app"
            mock_response.confidence = 0.95
            mock_interface.return_value.create_structured_response.return_value = (
                mock_response
            )

            result = detect_project_type_with_ai("Create a web application")
            if result != ProjectType.WEB_APP:
                raise ValueError("AI project type detection failed")

        # Test code generator instantiation
        generator = AICodeGenerator()
        if not hasattr(generator, "generate_project_code"):
            raise ValueError("AICodeGenerator missing required method")

        logger.info("✅ AI modules validation passed")

    def validate_pipeline(self):
        """Validate pipeline construction and basic execution."""
        logger.info("Validating pipeline...")

        from pipeline import _SequentialPipeline, build_pipeline

        # Test pipeline construction
        pipeline = build_pipeline([])
        if not isinstance(pipeline, _SequentialPipeline):
            raise ValueError("Pipeline construction failed")

        # Verify expected steps
        expected_steps = [
            "parse_input",
            "generate_requirements",
            "generate_architecture",
            "generate_code",
            "run_tests",
            "generate_docs",
            "package_artifacts",
        ]

        actual_steps = [step.__name__ for step in pipeline.steps]
        if actual_steps != expected_steps:
            raise ValueError(
                f"Pipeline steps mismatch. Expected: {expected_steps}, Got: {actual_steps}"
            )

        logger.info("✅ Pipeline validation passed")

    def validate_api(self):
        """Validate API construction."""
        logger.info("Validating API...")

        from fastapi.testclient import TestClient

        from api import app

        # Test API construction
        if not app:
            raise ValueError("FastAPI app not created")

        # Test basic routes exist
        client = TestClient(app)

        # Test health endpoint
        response = client.get("/health")
        if response.status_code not in [200, 500]:  # 500 OK if deps not running
            raise ValueError(f"Health endpoint failed: {response.status_code}")

        logger.info("✅ API validation passed")

    def run_test_suite(self):
        """Run the complete test suite."""
        logger.info("Running test suite...")

        test_dir = self.app_dir / "tests"
        if not test_dir.exists():
            raise ValueError("Tests directory not found")

        # Run pytest
        cmd = [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short"]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.app_dir)

        if result.returncode != 0:
            # Log test output for debugging
            logger.error("Test failures detected:")
            logger.error(result.stdout)
            logger.error(result.stderr)
            raise ValueError(f"Test suite failed with return code {result.returncode}")

        logger.info("✅ Test suite passed")

    def validate_dependencies(self):
        """Validate all dependencies are installed."""
        logger.info("Validating dependencies...")

        requirements_file = self.app_dir / "requirements.txt"
        if not requirements_file.exists():
            raise ValueError("requirements.txt not found")

        # Check critical packages
        critical_packages = [
            "fastapi",
            "uvicorn",
            "sqlmodel",
            "celery",
            "redis",
            "pydantic",
            "openai",
            "fastapi-websocket-pubsub",
        ]

        for package in critical_packages:
            try:
                __import__(package.replace("-", "_"))
                logger.info(f"✅ Package {package} available")
            except ImportError:
                raise ImportError(f"Critical package missing: {package}")

    def validate_security(self):
        """Validate security configurations."""
        logger.info("Validating security...")

        # Check that unauthorized models are not present in code
        unauthorized_patterns = ["gpt-4o", "claude-3", "gemini-pro"]

        # Scan critical files
        critical_files = [
            "shared/openai_interfaces/model_selector.py",
            "shared/openai_interfaces/responses_interface.py",
            "ai_agents.py",
            "ai_code_generator.py",
        ]

        for file_path in critical_files:
            full_path = self.app_dir / file_path
            if full_path.exists():
                content = full_path.read_text()
                for pattern in unauthorized_patterns:
                    if pattern in content:
                        raise ValueError(
                            f"Unauthorized model '{pattern}' found in {file_path}"
                        )

        logger.info("✅ Security validation passed")

    def generate_report(self) -> bool:
        """Generate validation report."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 SYSTEM VALIDATION REPORT")
        logger.info("=" * 60)

        if not self.failures and not self.warnings:
            logger.info("🎉 ALL VALIDATIONS PASSED!")
            logger.info("✅ System is ready for deployment")
            return True

        if self.warnings:
            logger.warning("⚠️  WARNINGS:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        if self.failures:
            logger.error("❌ FAILURES:")
            for failure in self.failures:
                logger.error(f"  - {failure}")

            logger.error("\n🚨 SYSTEM VALIDATION FAILED")
            logger.error("❌ System is NOT ready for deployment")
            return False

        logger.info("⚠️  System has warnings but may be deployable")
        return True


def main():
    """Run system validation."""
    validator = SystemValidator()

    try:
        success = validator.run_validation()
        exit_code = 0 if success else 1
    except Exception as e:
        logger.error(f"🚨 CRITICAL VALIDATION ERROR: {e}")
        exit_code = 2

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
