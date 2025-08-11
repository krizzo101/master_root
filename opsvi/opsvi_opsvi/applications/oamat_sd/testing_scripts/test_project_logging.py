#!/usr/bin/env python3
"""
Test script to demonstrate project-specific logging

This shows how logs are now created within each project directory.
"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

from src.applications.oamat_sd.src.operations.file_manager import FileOperationsManager
from src.applications.oamat_sd.src.sd_logging import LoggerFactory
from src.applications.oamat_sd.src.sd_logging.log_config import default_config


def test_project_logging():
    """Test that logging is correctly redirected to project directories"""

    print("🧪 Testing project-specific logging...")

    # Create project path first
    from datetime import datetime

    test_request = "Test project for logging demonstration"
    clean_request = "".join(
        c for c in test_request.lower() if c.isalnum() or c in " _-"
    )[:50]
    clean_request = "_".join(clean_request.split())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"{clean_request}_{timestamp}"

    projects_dir = Path(__file__).parent / "projects"
    projects_dir.mkdir(exist_ok=True)
    project_path = projects_dir / project_name
    project_path.mkdir(exist_ok=True)
    (project_path / "src").mkdir(exist_ok=True)
    (project_path / "docs").mkdir(exist_ok=True)

    # Update config BEFORE creating logger factory
    project_logs_dir = project_path / "logs"
    project_logs_dir.mkdir(exist_ok=True)
    default_config.log_dir = project_logs_dir

    print(f"📁 Created project: {project_path}")

    # Now create logger factory with updated config
    logger_factory = LoggerFactory(default_config, setup_file_handlers=False)
    logger_factory._setup_file_handlers()  # Set up with project-specific config
    file_manager = FileOperationsManager(logger_factory)

    # Test various loggers
    console_logger = logger_factory.get_console_logger()
    debug_logger = logger_factory.get_debug_logger()
    api_logger = logger_factory.get_api_logger()
    workflow_logger = logger_factory.get_workflow_logger()

    # Create some test log entries
    console_logger.info("🎯 This is a console log message")
    debug_logger.debug("🔍 This is a debug log message")
    api_logger.info("🌐 This is an API log message")
    workflow_logger.info("⚡ This is a workflow log message")

    # Check that logs directory was created in project
    logs_dir = project_path / "logs"
    print(f"📋 Logs directory created: {logs_dir.exists()}")

    if logs_dir.exists():
        print("📄 Log files created:")
        for log_file in logs_dir.glob("*.log"):
            print(f"  - {log_file.name}")

    print(f"✅ Test complete! Check project directory: {project_path}")
    return project_path


if __name__ == "__main__":
    test_project_logging()
