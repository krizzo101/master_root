import subprocess
import os
import time

# --- Configuration ---
SERVICE_NAME = "ArangoDB Service"
HOST = "0.0.0.0"
PORT = 5001
WORKERS = 4  # Adjust based on server core count
LOG_DIR = "/home/opsvi/asea/development/arango_service/logs"
ACCESS_LOG = os.path.join(LOG_DIR, "gunicorn_access.log")
ERROR_LOG = os.path.join(LOG_DIR, "gunicorn_error.log")
PID_FILE = f"/tmp/{SERVICE_NAME.lower().replace(' ', '_')}.pid"

# --- Main Functions ---


def create_log_dir():
    """Create the log directory if it doesn't exist."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"Created log directory: {LOG_DIR}")


def start_service():
    """Starts the Gunicorn service."""
    create_log_dir()

    command = [
        "gunicorn",
        "--bind",
        f"{HOST}:{PORT}",
        "--workers",
        str(WORKERS),
        "--access-logfile",
        ACCESS_LOG,
        "--error-logfile",
        ERROR_LOG,
        "--pid",
        PID_FILE,
        "--daemon",
        "arango_service:app",  # Assumes the Flask app instance is named 'app' in 'arango_service.py'
    ]

    print(f"Starting {SERVICE_NAME}...")
    try:
        # We need to run this from the correct directory
        process = subprocess.Popen(
            command, cwd=os.path.dirname(os.path.abspath(__file__))
        )
        time.sleep(2)  # Give it a moment to start

        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                pid = f.read().strip()
            print(f"{SERVICE_NAME} started successfully with PID: {pid}.")
            print(f"Logs available at: {LOG_DIR}")
        else:
            print(
                f"!! {SERVICE_NAME} may not have started correctly. PID file not found."
            )

    except FileNotFoundError:
        print(
            "!! Gunicorn not found. Please ensure it's installed (`pip install gunicorn`)."
        )
    except Exception as e:
        print(f"!! An error occurred while starting the service: {e}")


def stop_service():
    """Stops the Gunicorn service."""
    if not os.path.exists(PID_FILE):
        print(f"{SERVICE_NAME} does not appear to be running (PID file not found).")
        return

    try:
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()

        print(f"Stopping {SERVICE_NAME} (PID: {pid})...")
        subprocess.run(["kill", pid], check=True)
        os.remove(PID_FILE)
        print(f"{SERVICE_NAME} stopped.")
    except FileNotFoundError:
        print(f"{SERVICE_NAME} was already stopped.")
    except Exception as e:
        print(f"!! An error occurred while stopping the service: {e}")
        print("!! You may need to kill the process manually.")


def status_service():
    """Checks the status of the Gunicorn service."""
    if not os.path.exists(PID_FILE):
        print(f"{SERVICE_NAME} is stopped.")
        return

    try:
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()

        # Check if the process is actually running
        subprocess.run(["ps", "-p", pid], check=True, capture_output=True)
        print(f"{SERVICE_NAME} is running with PID: {pid}.")
    except subprocess.CalledProcessError:
        print(f"{SERVICE_NAME} is stopped (stale PID file found and will be removed).")
        os.remove(PID_FILE)
    except Exception as e:
        print(f"An error occurred while checking status: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "start":
            start_service()
        elif action == "stop":
            stop_service()
        elif action == "restart":
            stop_service()
            time.sleep(1)
            start_service()
        elif action == "status":
            status_service()
        else:
            print(f"Unknown command: {action}")
            print("Usage: python start_service.py [start|stop|restart|status]")
    else:
        print("Usage: python start_service.py [start|stop|restart|status]")
