
import sys
import os
from pathlib import Path
from typing import Iterator, List

# --- Configuration ---
EXCLUDE_DIRS = {"venv", ".venv", "env", ".env"}
INCLUDE_EXTS = {".py", ".json", ".md", ".txt"}
SEPARATOR = "=" * 60
OUTPUT_FILENAME = "cat_output.txt"


def find_files(root: Path, include_exts: set, exclude_dirs: set) -> Iterator[Path]:
    """Yield all files with given extensions, excluding specified directories."""
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in include_exts:
            # Exclude files in any excluded directory
            if any(part in exclude_dirs for part in path.parts):
                continue
            yield path


def write_file_with_header(outfile, file_path: Path, root: Path):
    """Write a header, separator, and file content to the output file."""
    rel_path = file_path.relative_to(root)
    header = f"\n{SEPARATOR}\nFILE: {rel_path}\n{SEPARATOR}\n"
    outfile.write(header)
    try:
        with file_path.open("r", encoding="utf-8") as infile:
            for line in infile:
                outfile.write(line)
    except UnicodeDecodeError:
        outfile.write("[Skipped: Non-UTF-8 or binary file]\n")
    except Exception as e:
        outfile.write(f"[Skipped: Error reading file: {e}]\n")


def main(root_dir: str = ".", output_file: str = OUTPUT_FILENAME):
    root = Path(root_dir).resolve()
    output_path = root / output_file
    files = list(find_files(root, INCLUDE_EXTS, EXCLUDE_DIRS))
    # Exclude the output file itself if in the same directory
    files = [f for f in files if f.resolve() != output_path.resolve()]
    with output_path.open("w", encoding="utf-8") as outfile:
        for file_path in sorted(files):
            write_file_with_header(outfile, file_path, root)
    print(f"Wrote {len(files)} files to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Concatenate .py, .json, .md, .txt files with headers, excluding venv/.venv.")
    parser.add_argument("-d", "--dir", default=".", help="Root directory to search (default: current directory)")
    parser.add_argument("-o", "--output", default=OUTPUT_FILENAME, help="Output filename (default: cat_output.txt)")
    args = parser.parse_args()
    main(args.dir, args.output)