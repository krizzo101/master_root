from celery import Celery
from celery.signals import worker_process_init
import os

# It's a common practice to define the Celery app instance in a separate file.
# This prevents circular import issues.

# The broker is the message queue (e.g., Redis, RabbitMQ) that Celery uses
# to send and receive messages. The result backend is where task results are stored.
celery_app = Celery(
    "asea_orchestrator",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "asea_orchestrator.tasks"
    ],  # List of modules to import when the worker starts
)


@worker_process_init.connect
def on_worker_init(**kwargs):
    """
    Ensures that plugins are loaded by the worker process.
    """
    # Import inside the function to avoid circular dependencies at startup
    from asea_orchestrator.plugins.plugin_manager import PluginManager
    from asea_orchestrator.plugins.available.qa_plugin import QAPlugin

    print("--- Celery Worker Process Initializing: Explicitly Loading Plugins ---")

    # Initialize the plugin manager with an explicit list of plugins
    # This ensures the worker knows about the QA Plugin.
    plugin_manager = PluginManager(plugins=[QAPlugin])

    print(f"--- Worker initialized with {len(plugin_manager.plugins)} plugins. ---")


# Optional configuration
celery_app.conf.update(
    task_track_started=True,
)

# --- TASKS ---
# All tasks should be defined below this line, decorated with @celery_app.task


@celery_app.task(name="asea.debug_inspect_environment")
def debug_inspect_environment():
    """
    A temporary debug task to inspect the Celery worker's environment.
    Imports the inspector function and executes it.
    """
    print("Executing debug_inspect_environment task.")
    try:
        from asea_orchestrator.scripts.celery_inspector import inspect_environment

        result_message = inspect_environment()
        print(f"Inspection script finished: {result_message}")
        return result_message
    except Exception as e:
        print(f"ERROR during environment inspection: {e}")
        raise


@celery_app.task(name="asea.execute_plugin_task")
def execute_plugin_task(plugin_name, method_name, *args, **kwargs):
    """
    Finds a plugin by name and executes one of its methods.
    This is the primary entry point for running plugin logic.
    """
    # Import inside the function to avoid circular dependencies at startup
    from asea_orchestrator.plugins.plugin_manager import PluginManager

    print(f"Received task for {plugin_name}.{method_name}")
    try:
        plugin = PluginManager.get_plugin(plugin_name)
        method = getattr(plugin, method_name)
        result = method(*args, **kwargs)
        print(f"Task {plugin_name}.{method_name} completed successfully.")
        return result
    except Exception as e:
        print(f"ERROR in task {plugin_name}.{method_name}: {e}")
        # It's often better to raise the exception to let Celery handle it
        raise


if __name__ == "__main__":
    celery_app.start()
