# /home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/tasks.py
from dataclasses import asdict

from .celery_app import app
from .plugins.types import ExecutionContext, PluginConfig, PluginResult


@app.task(bind=True)
def execute_plugin_task(self, plugin_name: str, config: dict, context: dict) -> dict:
    """
    Celery task to initialize and execute a single plugin.
    This function will be executed by a Celery worker.
    """
    try:
        # This is a critical assumption: The worker environment must have the
        # same plugins available as the main orchestrator process. This is
        # typically handled by ensuring both run from the same installed package.
        from .plugins.available.qa_plugin import QAPlugin
        from .plugins.available.arango_db_plugin import ArangoDBPlugin

        # ... import other plugins as needed, or create a central registry ...

        # A simple registry to find the plugin class by name
        # In a real system, this would be more robust.
        plugin_registry = {
            "QA Plugin": QAPlugin,
            "arango_db": ArangoDBPlugin,
        }

        plugin_class = plugin_registry.get(plugin_name)

        if not plugin_class:
            raise ValueError(f"Plugin '{plugin_name}' not found on worker.")

        instance = plugin_class()
        instance.initialize_sync(PluginConfig(**config), None)

        exec_context = ExecutionContext(**context)
        result = instance.execute_sync(exec_context)
        return asdict(result)
    except Exception as e:
        # Convert any exception to a failed PluginResult
        failed_result = PluginResult(success=False, data=None, error_message=str(e))
        return asdict(failed_result)
