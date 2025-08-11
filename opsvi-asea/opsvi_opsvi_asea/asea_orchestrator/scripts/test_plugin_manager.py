from asea_orchestrator.plugins.plugin_manager import PluginManager


def main():
    print("Testing Plugin Manager with explicit loading...")

    plugin_list = ["asea_orchestrator.plugins.available.hello_world_plugin"]

    manager = PluginManager(plugin_modules=plugin_list)
    manager.load_plugins()

    print("\nLoaded plugin classes:")
    for plugin_cls in manager.plugins:
        print(f"- {plugin_cls.__name__}")

    if not manager.plugins:
        print("\nNo plugins loaded.")


if __name__ == "__main__":
    main()
