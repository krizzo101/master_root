"""Test complete pipeline integration."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from database import create_job, init_db
from pipeline import _SequentialPipeline, build_pipeline

from schemas import ProjectType


class TestPipelineIntegration:
    """Test complete pipeline execution."""

    def setup_method(self):
        """Setup test environment."""
        # Create temporary directories
        self.test_dir = Path(tempfile.mkdtemp())
        self.job_output_dir = self.test_dir / "jobs"
        self.job_output_dir.mkdir()

        # Setup test database
        self.test_db_path = self.test_dir / "test_jobs.db"
        self.db_patcher = patch("database._db_path", self.test_db_path)
        self.db_patcher.start()
        init_db()

        # Mock config
        self.config_patcher = patch("pipeline.config")
        self.mock_config = self.config_patcher.start()
        self.mock_config.job_output_dir = self.job_output_dir

    def teardown_method(self):
        """Cleanup test environment."""
        self.db_patcher.stop()
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch("pipeline.detect_project_type_with_ai")
    @patch("pipeline.extract_requirements_with_ai")
    @patch("pipeline.generate_architecture_with_ai")
    @patch("pipeline.AICodeGenerator")
    @patch("pipeline.AITestGenerator")
    @patch("pipeline.AIDocumentationGenerator")
    def test_complete_pipeline_execution(
        self,
        mock_doc_gen,
        mock_test_gen,
        mock_code_gen,
        mock_arch_gen,
        mock_req_extract,
        mock_type_detect,
    ):
        """Test complete pipeline execution with mocked AI."""
        # Setup mocks
        mock_type_detect.return_value = ProjectType.WEB_APP

        mock_requirements = Mock()
        mock_requirements.title = "Test App"
        mock_req_extract.return_value = mock_requirements

        mock_architecture = Mock()
        mock_architecture.components = [Mock(name="main")]
        mock_arch_gen.return_value = mock_architecture

        # Mock code generation
        mock_code_instance = Mock()
        mock_code_generation = Mock()
        mock_code_generation.main_files = [
            Mock(filename="app.py", content="# Main app", purpose="Main")
        ]
        mock_code_generation.dependencies = ["flask"]
        mock_code_generation.setup_instructions = "pip install flask"
        mock_code_instance.generate_project_code.return_value = mock_code_generation
        mock_code_gen.return_value = mock_code_instance

        # Mock test generation
        mock_test_instance = Mock()
        mock_test_suite = Mock()
        mock_test_suite.test_files = [Mock(filename="test_app.py", test_cases=[])]
        mock_test_suite.pytest_config = {"testpaths": ["tests"]}
        mock_test_instance.generate_ai_tests.return_value = mock_test_suite
        mock_test_gen.return_value = mock_test_instance

        # Mock documentation generation
        mock_doc_instance = Mock()
        mock_docs = Mock()
        mock_docs.readme = Mock(content="# Test App")
        mock_doc_instance.generate_ai_documentation.return_value = mock_docs
        mock_doc_gen.return_value = mock_doc_instance

        # Create job
        job_id = "test-pipeline-job"
        create_job(job_id, "Create a test web application")

        # Setup pipeline state
        output_dir = self.job_output_dir / job_id
        output_dir.mkdir()

        state = {
            "request": "Create a test web application",
            "job_id": job_id,
            "output_dir": output_dir,
        }

        # Build and execute pipeline
        pipeline = build_pipeline([])
        result_state = pipeline.invoke(state)

        # Verify pipeline executed all steps
        assert "project_type" in result_state
        assert "requirements" in result_state
        assert "architecture" in result_state
        assert "generation" in result_state

        # Verify files were created
        assert (output_dir / "app.py").exists()
        assert (output_dir / "requirements.txt").exists()
        assert (output_dir / "README.md").exists()

    def test_pipeline_step_order(self):
        """Test that pipeline steps execute in correct order."""
        pipeline = build_pipeline([])

        # Should be SequentialPipeline
        assert isinstance(pipeline, _SequentialPipeline)

        # Verify step order
        step_names = [step.__name__ for step in pipeline.steps]
        expected_order = [
            "parse_input",
            "generate_requirements",
            "generate_architecture",
            "generate_code",
            "run_tests",
            "generate_docs",
            "package_artifacts",
        ]

        assert step_names == expected_order

    @patch("pipeline.detect_project_type_with_ai")
    def test_pipeline_error_handling(self, mock_type_detect):
        """Test pipeline error handling."""
        # Make AI detection fail
        mock_type_detect.side_effect = Exception("AI service unavailable")

        job_id = "test-error-job"
        output_dir = self.job_output_dir / job_id
        output_dir.mkdir()

        state = {
            "request": "Create a test application",
            "job_id": job_id,
            "output_dir": output_dir,
        }

        pipeline = build_pipeline([])

        # Pipeline should handle error gracefully
        with pytest.raises(Exception):
            pipeline.invoke(state)

    @patch("pipeline.update_job")
    @patch("pipeline.publish_progress_update")
    def test_pipeline_progress_updates(self, mock_publish, mock_update):
        """Test that pipeline publishes progress updates."""
        # Mock all AI functions to avoid actual API calls
        with patch("pipeline.detect_project_type_with_ai") as mock_type:
            mock_type.return_value = ProjectType.SIMPLE_SCRIPT

            with patch("pipeline.extract_requirements_with_ai") as mock_req:
                mock_req.return_value = Mock()

                job_id = "test-progress-job"
                output_dir = self.job_output_dir / job_id
                output_dir.mkdir()

                state = {
                    "request": "Create a simple script",
                    "job_id": job_id,
                    "output_dir": output_dir,
                }

                # Execute just first few steps
                pipeline = build_pipeline([])

                try:
                    pipeline.invoke(state)
                except Exception:
                    pass  # Expected due to mocking

                # Verify progress updates were called
                assert mock_update.called
                assert mock_publish.called

    def test_pipeline_state_persistence(self):
        """Test that pipeline state is maintained across steps."""
        # Mock minimal AI responses
        with patch("pipeline.detect_project_type_with_ai") as mock_type:
            mock_type.return_value = ProjectType.SIMPLE_SCRIPT

            with patch("pipeline.extract_requirements_with_ai") as mock_req:
                mock_requirements = Mock()
                mock_requirements.title = "Test Script"
                mock_req.return_value = mock_requirements

                job_id = "test-state-job"
                output_dir = self.job_output_dir / job_id
                output_dir.mkdir()

                initial_state = {
                    "request": "Create a simple script",
                    "job_id": job_id,
                    "output_dir": output_dir,
                    "test_data": "should_persist",
                }

                pipeline = build_pipeline([])

                # Execute first two steps only
                pipeline.steps = pipeline.steps[
                    :2
                ]  # Only parse_input and generate_requirements

                result_state = pipeline.invoke(initial_state)

                # Verify state persistence
                assert result_state["test_data"] == "should_persist"
                assert result_state["job_id"] == job_id
                assert "project_type" in result_state
                assert "requirements" in result_state

    def test_pipeline_output_directory_creation(self):
        """Test that pipeline creates necessary directories."""
        job_id = "test-dirs-job"
        output_dir = self.job_output_dir / job_id

        # Don't create output_dir initially
        state = {
            "request": "Create a test application",
            "job_id": job_id,
            "output_dir": output_dir,
        }

        # Mock AI to avoid actual calls
        with patch("pipeline.detect_project_type_with_ai") as mock_type:
            mock_type.return_value = ProjectType.SIMPLE_SCRIPT

            with patch("pipeline.extract_requirements_with_ai") as mock_req:
                mock_req.return_value = Mock()

                with patch("pipeline.generate_architecture_with_ai") as mock_arch:
                    mock_arch.return_value = Mock(components=[])

                    pipeline = build_pipeline([])

                    # Execute first few steps
                    try:
                        pipeline.invoke(state)
                    except Exception:
                        pass  # Expected due to incomplete mocking

                    # Verify directories were created
                    assert output_dir.exists()
                    assert (output_dir / "architecture").exists()


class TestPipelineSteps:
    """Test individual pipeline steps."""

    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.job_output_dir = self.test_dir / "jobs"
        self.job_output_dir.mkdir()

    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.test_dir)

    @patch("pipeline.detect_project_type_with_ai")
    def test_parse_input_step(self, mock_detect):
        """Test parse_input step."""
        from pipeline import parse_input

        mock_detect.return_value = ProjectType.WEB_APP

        state = {"request": "Create a web application"}
        result = parse_input(state)

        assert result["project_type"] == ProjectType.WEB_APP
        mock_detect.assert_called_once_with("Create a web application")

    @patch("pipeline.extract_requirements_with_ai")
    def test_generate_requirements_step(self, mock_extract):
        """Test generate_requirements step."""
        from pipeline import generate_requirements

        mock_requirements = Mock()
        mock_extract.return_value = mock_requirements

        state = {"request": "Create a web app", "project_type": ProjectType.WEB_APP}

        result = generate_requirements(state)

        assert result["requirements"] == mock_requirements
        mock_extract.assert_called_once()

    @patch("pipeline.generate_architecture_with_ai")
    def test_generate_architecture_step(self, mock_generate):
        """Test generate_architecture step."""
        from pipeline import generate_architecture

        mock_architecture = Mock()
        mock_generate.return_value = mock_architecture

        job_id = "test-arch-job"
        output_dir = self.job_output_dir / job_id
        output_dir.mkdir()

        state = {"requirements": Mock(), "output_dir": output_dir}

        result = generate_architecture(state)

        assert result["architecture"] == mock_architecture
        assert (output_dir / "architecture").exists()

    def test_package_artifacts_step(self):
        """Test package_artifacts step."""
        from pipeline import package_artifacts

        job_id = "test-package-job"
        output_dir = self.job_output_dir / job_id
        output_dir.mkdir()

        # Create some test files
        (output_dir / "app.py").write_text("# Test app")
        (output_dir / "README.md").write_text("# Test README")

        state = {"output_dir": output_dir}

        result = package_artifacts(state)

        # Verify zip file was created
        zip_path = output_dir / "artifacts.zip"
        assert zip_path.exists()
        assert result["artifacts_path"] == str(zip_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
