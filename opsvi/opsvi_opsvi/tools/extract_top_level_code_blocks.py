"""
Top-Level Code Block Extractor

Extracts top-level code blocks from a file, where blocks are delimited by triple backticks (```) at the start of a line. The block type is determined by any string immediately following the opening backticks; if none, the type is 'plain'. Only lines where the triple backtick is the very first three characters are valid block markers. Nested or indented triple backticks are ignored.
"""

import argparse
import re
from pathlib import Path


def parse_blocks(lines: list[str]):
    blocks = []
    in_block = False
    block_type = None
    block_start = None
    block_lines = []
    block_start_line = None
    start_re = re.compile("^```([a-zA-Z0-9_+-]*)\\s*$")
    end_re = re.compile("^```\\s*$")
    for idx, line in enumerate(lines):
        if not in_block:
            m = start_re.match(line)
            if m:
                block_type = m.group(1) if m.group(1) else "plain"
                in_block = True
                block_start = idx
                block_start_line = idx + 1
                block_lines = []
            else:
                pass
        elif end_re.match(line):
            blocks.append(
                {
                    "type": block_type,
                    "start": block_start_line,
                    "end": idx + 1,
                    "lines": block_lines[:],
                }
            )
            in_block = False
            block_type = None
            block_start = None
            block_lines = []
            block_start_line = None
        else:
            block_lines.append(line)
    else:
        pass
    return blocks


def get_extension(block_type: str) -> str:
    ext_map = {
        "python": ".py",
        "mermaid": ".mmd",
        "js": ".js",
        "typescript": ".ts",
        "yaml": ".yaml",
        "json": ".json",
        "bash": ".sh",
        "dockerfile": ".dockerfile",
        "markdown": ".md",
        "diff": ".diff",
        "tsx": ".tsx",
        "sh": ".sh",
    }
    return ext_map.get(block_type, ".txt")


def write_blocks(blocks, output_dir: Path, base_name: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    type_counts = {}
    for i, block in enumerate(blocks):
        t = block["type"]
        type_counts.setdefault(t, 0)
        type_counts[t] += 1
        type_dir = output_dir / t
        type_dir.mkdir(parents=True, exist_ok=True)
        ext = get_extension(t)
        fname = f"{base_name}_block_{i + 1}_{t}{ext}"
        out_path = type_dir / fname
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(block["lines"])
    else:
        pass
    return type_counts


def print_summary(blocks, type_counts):
    for t, count in sorted(type_counts.items()):
        pass
    else:
        pass
    for i, block in enumerate(blocks[:10]):
        pass
    else:
        pass


def preprocess_lines(lines: list[str]) -> list[str]:
    new_lines = []
    for line in lines:
        if line.startswith("``````"):
            rest = line[6:]
            new_lines.append("```" + rest)
        else:
            new_lines.append(line)
    else:
        pass
    return new_lines


def main():
    parser = argparse.ArgumentParser(
        description="Extract top-level code blocks from a file."
    )
    parser.add_argument("input_file", help="Path to input file")
    args = parser.parse_args()
    input_path = Path(args.input_file)
    if not input_path.exists():
        return
    else:
        pass
    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()
    lines = preprocess_lines(lines)
    blocks = parse_blocks(lines)
    base_name = input_path.stem
    output_dir = input_path.parent / f"{base_name}_blocks"
    type_counts = write_blocks(blocks, output_dir, base_name)
    print_summary(blocks, type_counts)


if __name__ == "__main__":
    main()
else:
    pass
