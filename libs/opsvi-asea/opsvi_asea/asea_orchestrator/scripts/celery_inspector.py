import sys
import logging
from pathlib import Path
import importlib.util
import datetime

# Configure logging
LOG_FILE = "/tmp/celery_env_inspection.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",  # Overwrite log file on each run
)


def inspect_environment():
    """
    Inspects the Python environment from within the execution context
    and logs the findings.
    """
    logging.info("--- Starting Celery Worker Environment Inspection ---")

    # 1. Log Python executable
    python_executable = sys.executable
    logging.info(f"Python Executable: {python_executable}")

    # 2. Log Python version
    python_version = sys.version
    logging.info(f"Python Version: {python_version}")

    # 3. Log sys.path
    logging.info("--- sys.path ---")
    for p in sys.path:
        logging.info(p)
    logging.info("--- end of sys.path ---")

    # 4. Find the location of the asea_orchestrator package
    try:
        spec = importlib.util.find_spec("asea_orchestrator")
        if spec and spec.origin:
            orchestrator_path = Path(spec.origin).parent
            logging.info(f"Found 'asea_orchestrator' at: {orchestrator_path}")

            # 5. Find and inspect the qa_plugin.py file
            qa_plugin_path = (
                orchestrator_path / "plugins" / "available" / "qa_plugin.py"
            )
            logging.info(f"Attempting to inspect: {qa_plugin_path}")

            if qa_plugin_path.exists():
                stat_info = qa_plugin_path.stat()
                mod_time = datetime.datetime.fromtimestamp(stat_info.st_mtime)
                logging.info(f"QA Plugin found at: {qa_plugin_path}")
                logging.info(f"  -> Size: {stat_info.st_size} bytes")
                logging.info(f"  -> Last Modified: {mod_time.isoformat()}")
            else:
                logging.warning("QA Plugin file does not exist at the expected path.")

        else:
            logging.error("'asea_orchestrator' could not be found via importlib.")

    except Exception as e:
        logging.error(f"An error occurred during module inspection: {e}", exc_info=True)

    logging.info("--- Inspection Complete ---")
    return f"Inspection complete. Results logged to {LOG_FILE}"


if __name__ == "__main__":
    # This allows running the script directly for testing if needed
    result = inspect_environment()
    print(result)
    with open(LOG_FILE, "r") as f:
        print(f.read())
