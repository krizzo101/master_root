from asea_orchestrator.celery_app import celery_app
import time


def run_inspection():
    """
    Calls the debug_inspect_environment task and waits for the result.
    """
    print("--- Triggering Celery Environment Inspection Task ---")
    try:
        # Send the task to the queue
        task_result = celery_app.send_task("asea.debug_inspect_environment")
        print(f"Task sent with ID: {task_result.id}")

        # Wait for the result with a timeout
        print("Waiting for task to complete...")
        result = task_result.get(timeout=30)  # 30-second timeout

        print("\n--- Task Result ---")
        print(f"Status: {task_result.status}")
        print(f"Result: {result}")

    except Exception as e:
        print(f"\nAn error occurred while trying to run the task: {e}")
        print("Please ensure the Celery worker is running.")


if __name__ == "__main__":
    run_inspection()
    print("\n--- Next Step ---")
    print("Check the log file for detailed environment information:")
    print("tail -f /tmp/celery_env_inspection.log")
