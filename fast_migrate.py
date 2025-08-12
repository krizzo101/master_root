#!/usr/bin/env python3
import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def migrate_file(mapping):
    source = mapping["source"]
    target_path = mapping["target_path"]

    # Create target directory
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)

    # Copy file
    shutil.copy2(source, target_path)

    # Update imports if it's a Python file
    if target_path.endswith(".py"):
        with open(target_path) as f:
            content = f.read()

        # Replace imports
        content = content.replace("from agent_world", "from opsvi_")
        content = content.replace("from auto_forge", "from opsvi_auto_forge")
        content = content.replace("from master", "from opsvi_master")
        content = content.replace("from coordination", "from opsvi_coordination")

        with open(target_path, "w") as f:
            f.write(content)

    return target_path


def main():
    start_time = time.time()

    # Load mappings
    with open("migration_mapping.json") as f:
        mappings = json.load(f)

    print(f"Starting migration of {len(mappings)} files...")

    # Process all files in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(migrate_file, mappings))

    # Create __init__.py files
    for mapping in mappings:
        target_dir = os.path.dirname(mapping["target_path"])
        init_file = os.path.join(target_dir, "__init__.py")
        if not os.path.exists(init_file):
            Path(init_file).touch()

    end_time = time.time()
    print(f"Migration completed in {end_time - start_time:.2f} seconds!")
    print(f"Migrated {len(results)} files")


if __name__ == "__main__":
    main()
