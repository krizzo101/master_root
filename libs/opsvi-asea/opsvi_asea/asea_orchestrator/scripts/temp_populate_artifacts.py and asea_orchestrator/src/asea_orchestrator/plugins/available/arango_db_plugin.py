result = await orchestrator.run_workflow("insert_artifact", {})

# The result of the workflow is the final state dictionary.
# Check for an error message from the plugin's PluginResult.
# This requires a slight change in the plugin to output errors to the state.
if result.get("error_message"):
    print(f"  ERROR: {result['error_message']}")
else:
    print("  SUCCESS.")
