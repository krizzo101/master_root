"""Test database operations."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from database import create_job, get_job, get_job_data, get_session, init_db, update_job


class TestDatabase:
    """Test database operations."""

    def setup_method(self):
        """Setup test database."""
        # Create temporary directory for test database
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_db_path = self.test_dir / "test_jobs.db"

        # Patch the database path
        self.db_patcher = patch("database._db_path", self.test_db_path)
        self.db_patcher.start()

        # Initialize test database
        init_db()

    def teardown_method(self):
        """Cleanup test database."""
        self.db_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_init_db(self):
        """Test database initialization."""
        assert self.test_db_path.exists()

        # Should be able to create session
        with get_session() as session:
            assert session is not None

    def test_create_job(self):
        """Test job creation."""
        job_id = "test-job-123"
        request_text = "Create a test application"

        create_job(job_id, request_text)

        # Verify job was created
        job_data = get_job_data(job_id)
        assert job_data is not None
        assert job_data["id"] == job_id
        assert job_data["request_text"] == request_text
        assert job_data["status"] == "queued"
        assert job_data["progress"] == 0.0

    def test_update_job(self):
        """Test job updates."""
        job_id = "test-job-456"
        create_job(job_id, "Test request")

        # Update job status
        update_job(job_id, status="in_progress", phase="generate_code", progress=0.5)

        job = get_job(job_id)
        assert job.status == "in_progress"
        assert job.phase == "generate_code"
        assert job.progress == 0.5
        assert job.updated_at > job.created_at

    def test_update_job_with_error(self):
        """Test job update with error."""
        job_id = "test-job-error"
        create_job(job_id, "Test request")

        # Update job with error
        error_message = "Test error occurred"
        update_job(job_id, status="failed", error=error_message)

        job = get_job(job_id)
        assert job.status == "failed"
        assert job.error == error_message

    def test_update_job_with_artifacts(self):
        """Test job update with artifacts path."""
        job_id = "test-job-artifacts"
        create_job(job_id, "Test request")

        artifacts_path = "/path/to/artifacts.zip"
        update_job(job_id, status="completed", artifacts_path=artifacts_path)

        job = get_job(job_id)
        assert job.status == "completed"
        assert job.artifacts_path == artifacts_path

    def test_get_job_nonexistent(self):
        """Test getting non-existent job."""
        job = get_job("nonexistent-job")
        assert job is None

    def test_get_job_data(self):
        """Test getting job data as dict."""
        job_id = "test-job-data"
        request_text = "Test request for data"
        create_job(job_id, request_text)

        job_data = get_job_data(job_id)
        assert job_data is not None
        assert isinstance(job_data, dict)
        assert job_data["id"] == job_id
        assert job_data["request_text"] == request_text
        assert job_data["status"] == "queued"

    def test_get_job_data_nonexistent(self):
        """Test getting data for non-existent job."""
        job_data = get_job_data("nonexistent-job")
        assert job_data is None

    def test_multiple_jobs(self):
        """Test handling multiple jobs."""
        job_ids = ["job-1", "job-2", "job-3"]

        # Create multiple jobs
        for i, job_id in enumerate(job_ids):
            create_job(job_id, f"Request {i+1}")

        # Verify all jobs exist
        for job_id in job_ids:
            job = get_job(job_id)
            assert job is not None
            assert job.id == job_id

    def test_job_timestamps(self):
        """Test job timestamp handling."""
        job_id = "test-timestamps"
        create_time = datetime.now()

        create_job(job_id, "Test request")
        job = get_job(job_id)

        # Check created_at is recent
        assert job.created_at >= create_time
        assert job.updated_at >= create_time

        # Update job and check updated_at changed
        original_updated = job.updated_at
        import time

        time.sleep(0.01)  # Small delay

        update_job(job_id, status="in_progress")
        updated_job = get_job(job_id)
        assert updated_job.updated_at > original_updated

    def test_database_persistence(self):
        """Test that data persists across connections."""
        job_id = "test-persistence"
        create_job(job_id, "Persistence test")

        # Close and reopen database connection
        with get_session() as session:
            # Session closed here
            pass

        # Should still be able to retrieve job
        job = get_job(job_id)
        assert job is not None
        assert job.id == job_id

    def test_concurrent_access(self):
        """Test concurrent database access."""
        import queue
        import threading

        results = queue.Queue()

        def create_test_job(job_number):
            try:
                job_id = f"concurrent-job-{job_number}"
                create_job(job_id, f"Concurrent request {job_number}")
                job = get_job(job_id)
                results.put(job.id if job else None)
            except Exception as e:
                results.put(f"Error: {e}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_test_job, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        created_jobs = []
        while not results.empty():
            result = results.get()
            if isinstance(result, str) and not result.startswith("Error"):
                created_jobs.append(result)

        # Should have created all jobs successfully
        assert len(created_jobs) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
