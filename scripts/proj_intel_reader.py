#!/usr/bin/env python3
"""
Project Intelligence Byte-Offset Reader

This script implements the ACTUAL byte-offset reading strategy described in
.proj-intel/AGENT_ONBOARDING.md that agents typically fail to implement.

Usage:
    python proj_intel_reader.py --action <action> [options]

Actions:
    read-bytes: Read specific byte range from JSONL
    read-by-path: Read all items for a specific file path
    read-collector: Read items from a specific collector
    stream-jsonl: Stream JSONL line by line (memory efficient)

Examples:
    # Read specific byte range
    python proj_intel_reader.py --action read-bytes --offset 1024 --size 512

    # Read all items about a file
    python proj_intel_reader.py --action read-by-path --path "src/main.py"

    # Stream FileElements collector items
    python proj_intel_reader.py --action read-collector --collector FileElementsCollector
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


class ProjectIntelReader:
    """Implements proper byte-offset reading for project intelligence."""

    def __init__(self, intel_dir: str = ".proj-intel"):
        self.intel_dir = Path(intel_dir)
        self.jsonl_file = self.intel_dir / "project_analysis.jsonl"
        self.index_file = self.intel_dir / "project_analysis.index.json"
        self.reverse_index_file = self.intel_dir / "reverse_index.json"
        self.blocks_index_file = self.intel_dir / "blocks.index.json"

        # Load indices
        self._load_indices()

    def _load_indices(self):
        """Load all index files into memory (they're small)."""
        with open(self.index_file) as f:
            self.index = json.load(f)

        if self.reverse_index_file.exists():
            with open(self.reverse_index_file) as f:
                self.reverse_index = json.load(f)
        else:
            self.reverse_index = {}

        if self.blocks_index_file.exists():
            with open(self.blocks_index_file) as f:
                self.blocks_index = json.load(f)
        else:
            self.blocks_index = {}

    def read_bytes(self, offset: int, size: int) -> Dict[str, Any]:
        """Read exact byte range from JSONL file."""
        with open(self.jsonl_file, "rb") as f:
            f.seek(offset)
            data = f.read(size)
            return json.loads(data.decode("utf-8"))

    def read_by_path(self, file_path: str) -> List[Dict[str, Any]]:
        """Read all items related to a specific file path using reverse index."""
        if file_path not in self.reverse_index:
            return []

        items = []
        path_info = self.reverse_index[file_path]

        # Handle the structure: {"file_path": ..., "collectors": [...], "symbols": [...]}
        if isinstance(path_info, dict) and "collectors" in path_info:
            for entry in path_info["collectors"]:
                item = self.read_bytes(entry["byte_offset"], entry["byte_size"])
                items.append(item)
        # Fallback for different structure
        elif isinstance(path_info, list):
            for entry in path_info:
                item = self.read_bytes(entry["byte_offset"], entry["byte_size"])
                items.append(item)

        return items

    def read_collector_items(self, collector_name: str) -> Iterator[Dict[str, Any]]:
        """Stream items from a specific collector."""
        for record in self.index["records"]:
            if record.get("collector") == collector_name:
                if record["kind"] == "collector_item":
                    yield self.read_bytes(record["byte_offset"], record["byte_size"])

    def stream_jsonl(self, max_items: Optional[int] = None) -> Iterator[Dict[str, Any]]:
        """Stream JSONL line by line without loading into memory."""
        count = 0
        with open(self.jsonl_file, "r") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
                    count += 1
                    if max_items and count >= max_items:
                        break

    def get_file_elements(self, min_only: bool = True) -> Iterator[Dict[str, Any]]:
        """Get file elements efficiently."""
        if min_only:
            # Use the min file for quick triage
            min_file = self.intel_dir / "file_elements.min.jsonl"
            if min_file.exists():
                with open(min_file) as f:
                    for line in f:
                        if line.strip():
                            yield json.loads(line)
        else:
            # Use collector items
            yield from self.read_collector_items("FileElementsCollector")

    def get_agent_architecture(self) -> Iterator[Dict[str, Any]]:
        """Get agent architecture items efficiently."""
        arch_file = self.intel_dir / "agent_architecture.jsonl"
        if arch_file.exists():
            with open(arch_file) as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)
        else:
            yield from self.read_collector_items("AgentArchitectureCollector")


def main():
    """Command line interface for the reader."""
    parser = argparse.ArgumentParser(
        description="Project Intelligence Byte-Offset Reader"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=[
            "read-bytes",
            "read-by-path",
            "read-collector",
            "stream-jsonl",
            "file-elements",
            "agents",
        ],
        help="Action to perform",
    )
    parser.add_argument("--offset", type=int, help="Byte offset for read-bytes")
    parser.add_argument("--size", type=int, help="Byte size for read-bytes")
    parser.add_argument("--path", help="File path for read-by-path")
    parser.add_argument("--collector", help="Collector name")
    parser.add_argument("--limit", type=int, help="Max items to return")
    parser.add_argument(
        "--format", default="json", choices=["json", "summary"], help="Output format"
    )

    args = parser.parse_args()

    reader = ProjectIntelReader()

    try:
        if args.action == "read-bytes":
            if not args.offset or not args.size:
                print("Error: --offset and --size required for read-bytes")
                sys.exit(1)
            result = reader.read_bytes(args.offset, args.size)
            print(json.dumps(result, indent=2))

        elif args.action == "read-by-path":
            if not args.path:
                print("Error: --path required for read-by-path")
                sys.exit(1)
            items = reader.read_by_path(args.path)
            if args.format == "summary":
                print(f"Found {len(items)} items for {args.path}")
                for item in items:
                    kind = item.get("kind", "unknown")
                    name = item.get("data", {}).get("name", "N/A")
                    print(f"  - {kind}: {name}")
            else:
                print(json.dumps(items, indent=2))

        elif args.action == "read-collector":
            if not args.collector:
                print("Error: --collector required")
                sys.exit(1)
            count = 0
            for item in reader.read_collector_items(args.collector):
                if args.format == "summary":
                    data = item.get("data", {})
                    file_path = data.get("file_path", "unknown")
                    name = data.get("name", "N/A")
                    print(f"{file_path}: {name}")
                else:
                    print(json.dumps(item))
                count += 1
                if args.limit and count >= args.limit:
                    break

        elif args.action == "stream-jsonl":
            count = 0
            for item in reader.stream_jsonl(args.limit):
                if args.format == "summary":
                    print(f"Line {count+1}: {item.get('kind', 'unknown')}")
                else:
                    print(json.dumps(item))
                count += 1

        elif args.action == "file-elements":
            count = 0
            for item in reader.get_file_elements(min_only=True):
                if args.format == "summary":
                    path = item["path"]
                    fn_count = item["fn_count"]
                    class_count = item["class_count"]
                    print(f"{path}: {fn_count} functions, {class_count} classes")
                else:
                    print(json.dumps(item))
                count += 1
                if args.limit and count >= args.limit:
                    break

        elif args.action == "agents":
            count = 0
            for item in reader.get_agent_architecture():
                data = item.get("data", {})
                if args.format == "summary":
                    file_path = data["file_path"]
                    name = data["name"]
                    method_count = len(data.get("methods", []))
                    print(f"{file_path}: {name} ({method_count} methods)")
                else:
                    print(json.dumps(item))
                count += 1
                if args.limit and count >= args.limit:
                    break

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure to run 'project-intelligence full-package' first")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
