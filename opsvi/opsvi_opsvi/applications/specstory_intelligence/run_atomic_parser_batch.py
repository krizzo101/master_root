"""
Batch Atomic Parser Runner (Async)

Processes all files in .cursor/import/ using the minimal atomic parser.
Outputs each file's atomic components as a JSON file in data/artifacts/atomic/.

Reference: docs/applications/agent_intelligence_pipeline.md (authoritative schema)
"""

import asyncio
from dataclasses import asdict
import enum
import json
import logging
from pathlib import Path

from atomic_parser import AtomicSpecStoryParser

INPUT_DIR = Path(".cursor/import/")
OUTPUT_DIR = Path("data/artifacts/atomic/")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def enum_to_value(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: enum_to_value(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [enum_to_value(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(enum_to_value(i) for i in obj)
    else:
        return obj


async def process_file(file_path: Path, parser: AtomicSpecStoryParser):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        components, relationships = await parser.parse_file(file_path)
        # Defensive: ensure both are lists
        if not isinstance(components, list):
            logging.warning(
                f"[DEFENSIVE] 'components' was type {type(components)} for file {file_path}; wrapping in list."
            )
            components = [components]
        if not isinstance(relationships, list):
            logging.warning(
                f"[DEFENSIVE] 'relationships' was type {type(relationships)} for file {file_path}; wrapping in list."
            )
            relationships = [relationships]
        logging.info(
            f"[DEBUG] components type: {type(components)}, relationships type: {type(relationships)}"
        )
        out_path = OUTPUT_DIR / (file_path.stem + ".atomic.json")
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(
                {
                    "file": str(file_path),
                    "components": [enum_to_value(asdict(c)) for c in components],
                    "relationships": [enum_to_value(asdict(r)) for r in relationships],
                },
                out_f,
                indent=2,
            )
        logging.info(f"Processed {file_path} -> {out_path}")
    except Exception as e:
        logging.error(f"Failed to process {file_path}: {e}")


async def main():
    parser = AtomicSpecStoryParser()
    files = list(INPUT_DIR.glob("*.md"))
    if not files:
        logging.warning(f"No .md files found in {INPUT_DIR}")
        return
    for file_path in files:
        await process_file(file_path, parser)


if __name__ == "__main__":
    asyncio.run(main())
