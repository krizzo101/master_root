#!/usr/bin/env python3
"""
Test script for current PluginManager API (plugin_dir based)
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

from asea_orchestrator.plugins.plugin_manager import PluginManager


def main():
    print("=== Testing Current PluginManager API ===")

    # Use the actual plugin directory path
    plugin_dir = (
        "/home/opsvi/asea/asea_orchestrator/src/asea_orchestrator/plugins/available"
    )

    print(f"Plugin directory: {plugin_dir}")
    print(f"Directory exists: {os.path.exists(plugin_dir)}")

    try:
        # Test current constructor signature
        print("\n1. Creating PluginManager with plugin_dir...")
        manager = PluginManager(plugin_dir=plugin_dir)
        print("✓ PluginManager created successfully")

        # Test plugin discovery
        print("\n2. Discovering plugins...")
        manager.discover_plugins()
        print(f"✓ Plugin discovery completed")

        # List discovered plugins
        print("\n3. Available plugins:")
        available_plugins = manager.list_available_plugins()
        for plugin_name in available_plugins:
            print(f"   - {plugin_name}")

        print(f"\nTotal plugins discovered: {len(available_plugins)}")

        # Test cache stats
        print("\n4. Cache statistics:")
        stats = manager.get_cache_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Test getting a plugin class
        if available_plugins:
            test_plugin = available_plugins[0]
            print(f"\n5. Testing plugin class retrieval for '{test_plugin}'...")
            plugin_class = manager.get_plugin_class(test_plugin)
            if plugin_class:
                print(f"✓ Retrieved plugin class: {plugin_class.__name__}")
                print(f"   Plugin name: {plugin_class.get_name()}")
            else:
                print(f"✗ Failed to retrieve plugin class for '{test_plugin}'")

        # Test getting a plugin instance
        if available_plugins:
            test_plugin = available_plugins[0]
            print(f"\n6. Testing plugin instance creation for '{test_plugin}'...")
            plugin_instance = manager.get_plugin_instance(test_plugin)
            if plugin_instance:
                print(f"✓ Created plugin instance: {type(plugin_instance).__name__}")
            else:
                print(f"✗ Failed to create plugin instance for '{test_plugin}'")

        print("\n=== PluginManager Test COMPLETED SUCCESSFULLY ===")
        return True

    except Exception as e:
        print(f"\n✗ PluginManager test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
