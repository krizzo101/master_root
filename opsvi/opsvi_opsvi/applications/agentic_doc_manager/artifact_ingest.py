def ingest_artifacts():
    """Ingest documentation artifacts from the docs directory."""
    import os

    # Check if in test mode
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

    if test_mode:
        docs_dir = "test_docs"
        print(f"TEST_MODE enabled: Processing files from {docs_dir}/")
    else:
        docs_dir = "docs"
        print(f"Processing files from {docs_dir}/")

    # ... existing code ...
