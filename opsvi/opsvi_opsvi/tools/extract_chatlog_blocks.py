"""
Chat Log Code Block Extractor (Block-Span Replacement)

Extracts all code blocks (any type) from a markdown chat log, writes each to a type-specific subdirectory, and replaces the entire block (from opening to closing ```) with a single placeholder tag at the position where the block started. Replacements are processed bottom-to-top to avoid index shifting.
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("extractor")
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(handler)
    else:
        pass
    logger.setLevel(logging.INFO)
    return logger


logger = setup_logger()
CODE_BLOCK_RE = re.compile("^```([a-zA-Z0-9_+-]*)\\s*$")
END_BLOCK_RE = re.compile("^```\\s*$")
EXTENSION_MAP = {
    "python": ".py",
    "toml": ".toml",
    "mermaid": ".mmd",
    "js": ".js",
    "typescript": ".ts",
    "yaml": ".yaml",
    "jsonc": ".jsonc",
    "bash": ".sh",
    "dockerfile": ".dockerfile",
    "markdown": ".md",
    "diff": ".diff",
    "tsx": ".tsx",
    "sh": ".sh",
}


def get_extension(block_type: str) -> str:
    return EXTENSION_MAP.get(block_type, ".txt")


class Block:
    def __init__(self, block_type: str, start_line: int, start_idx: int):
        self.block_type = block_type or "plain"
        self.start_line = start_line
        self.start_idx = start_idx
        self.end_line: int | None = None
        self.end_idx: int | None = None
        self.lines: list[str] = []

    def set_end(self, end_line: int, end_idx: int):
        self.end_line = end_line
        self.end_idx = end_idx

    def filename(self) -> str:
        ext = get_extension(self.block_type)
        return f"{self.block_type}_{self.start_line}_{self.end_line}{ext}"

    def __repr__(self):
        return f"Block(type={self.block_type}, start={self.start_line}, end={self.end_line})"


def extract_blocks(
    input_path: str, output_dir: Path, main_output_path: Path
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(input_path, encoding="utf-8") as infile:
        lines = infile.readlines()
    preprocessed_lines = []
    for line in lines:
        if line.startswith("``````"):
            rest = line[6:]
            preprocessed_lines.append("```" + rest)
        else:
            preprocessed_lines.append(line)
    else:
        pass
    lines = preprocessed_lines
    found_types = set()
    extracted_blocks: list[dict] = []
    all_blocks: list[Block] = []
    mapped_blocks = []
    in_block_map = False
    block_type_map = None
    block_start_line_map = None
    block_lines_map = []
    for idx, line in enumerate(lines):
        line_num = idx + 1
        start_match = CODE_BLOCK_RE.match(line)
        if not in_block_map and start_match and start_match.group(1).strip():
            block_type_map = start_match.group(1).strip().lower()
            in_block_map = True
            block_start_line_map = line_num
            block_lines_map = [line]
            continue
        else:
            pass
        if in_block_map and line.strip() == "```":
            block_lines_map.append(line)
            mapped_blocks.append(
                {
                    "type": block_type_map,
                    "start": block_start_line_map,
                    "end": line_num,
                    "lines": block_lines_map[:],
                }
            )
            in_block_map = False
            block_type_map = None
            block_start_line_map = None
            block_lines_map = []
            continue
        else:
            pass
        if in_block_map:
            block_lines_map.append(line)
        else:
            pass
    else:
        pass
    for b in mapped_blocks:
        pass
    else:
        pass
    in_block = False
    block_type = None
    block_start_line = None
    block_start_idx = None
    block_lines = []
    skipped_first_tick = False
    for idx, line in enumerate(lines):
        line_num = idx + 1
        if not skipped_first_tick and line.strip() == "```":
            skipped_first_tick = True
            continue
        else:
            pass
        start_match = CODE_BLOCK_RE.match(line)
        if not in_block and start_match and start_match.group(1).strip():
            block_type = start_match.group(1).strip().lower()
            if block_type in ("markdown", "plain"):
                in_block = False
                block_type = None
                block_start_line = None
                block_start_idx = None
                block_lines = []
                continue
            else:
                pass
            in_block = True
            block_start_line = line_num
            block_start_idx = idx
            block_lines = [line]
            found_types.add(block_type)
            logger.debug(f"Block start detected at line {line_num}: {line.rstrip()}")
            continue
        else:
            pass
        if in_block and line.strip() == "```":
            block_lines.append(line)
            content_lines = block_lines[1:-1] if len(block_lines) >= 2 else []
            if len(content_lines) < 10:
                in_block = False
                block_type = None
                block_start_line = None
                block_start_idx = None
                block_lines = []
                continue
            else:
                pass
            block = Block(block_type, block_start_line, block_start_idx)
            block.lines = block_lines[:]
            block.set_end(line_num, idx)
            all_blocks.append(block)
            type_dir = output_dir / block.block_type
            type_dir.mkdir(parents=True, exist_ok=True)
            out_path = type_dir / block.filename()
            try:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.writelines(content_lines)
            except Exception as e:
                logger.error(f"Failed to write block {block}: {e}")
            else:
                pass
            finally:
                pass
            extracted_blocks.append(
                {
                    "type": block.block_type,
                    "start": block.start_line,
                    "end": block.end_line,
                    "path": str(out_path),
                }
            )
            logger.debug(f"Block end detected at line {line_num}: {line.rstrip()}")
            in_block = False
            block_type = None
            block_start_line = None
            block_start_idx = None
            block_lines = []
            continue
        else:
            pass
        if in_block:
            block_lines.append(line)
        else:
            pass
    else:
        pass
    if in_block:
        logger.error(
            f"Unclosed block at EOF: Block(type={block_type}, start={block_start_line}, end=None)"
        )
    else:
        pass
    lines_out = lines[:]
    for block in sorted(all_blocks, key=lambda b: b.start_idx, reverse=True):
        if block.block_type not in ("markdown", "plain"):
            tag = f"<-- {block.block_type} block extracted: {block.filename()} -->\n"
            lines_out[block.start_idx : block.end_idx + 1] = [tag]
        else:
            pass
    else:
        pass
    cleaned_lines = []
    i = 0
    while i < len(lines_out):
        if (
            i + 2 < len(lines_out)
            and lines_out[i].strip() == ""
            and (lines_out[i + 1].strip() == "---")
            and (lines_out[i + 2].strip() == "")
        ):
            cleaned_lines.append("\n")
            i += 3
        else:
            cleaned_lines.append(lines_out[i])
            i += 1
    else:
        pass
    final_lines = []
    prev_blank = False
    for line in cleaned_lines:
        if line.strip() == "":
            if not prev_blank:
                final_lines.append(line)
            else:
                pass
            prev_blank = True
        else:
            final_lines.append(line)
            prev_blank = False
    else:
        pass
    try:
        with open(main_output_path, "w", encoding="utf-8") as f:
            f.writelines(final_lines)
        logger.info(f"Main extracted file written: {main_output_path}")
    except Exception as e:
        logger.error(f"Failed to write main output file: {e}")
    else:
        pass
    finally:
        pass
    type_counts = {}
    for block in extracted_blocks:
        t = block["type"]
        type_counts.setdefault(t, 0)
        type_counts[t] += 1
    else:
        pass
    output_dir_path = Path(output_dir)
    for t in sorted(type_counts):
        subdir = output_dir_path / t
        try:
            count = len([f for f in subdir.iterdir() if f.is_file()])
        except Exception:
            count = 0
        else:
            pass
        finally:
            pass
    else:
        pass
    report_path = output_dir_path / "extraction_report.txt"
    with open(report_path, "w", encoding="utf-8") as report:
        report.write("Extraction Report\n=================\n\n")
        report.write(f"Original file lines: {len(lines)}\n")
        report.write(f"New file lines: {len(final_lines)}\n\n")
        report.write("Files per type:\n")
        for t in sorted(type_counts):
            subdir = output_dir_path / t
            try:
                count = len([f for f in subdir.iterdir() if f.is_file()])
            except Exception:
                count = 0
            else:
                pass
            finally:
                pass
            report.write(f"  {t}/: {count} file(s)\n")
        else:
            pass
        report.write("\nExtracted Files:\n")
        report.write(f"{'Type':<12} {'Start':<7} {'End':<7} {'Filename'}\n")
        report.write("-" * 50 + "\n")
        for block in extracted_blocks:
            rel_path = os.path.relpath(block["path"], output_dir_path)
            report.write(
                f"{block['type']:<12} {block['start']:<7} {block['end']:<7} {rel_path}\n"
            )
        else:
            pass

    def find_largest_blocks(path, block_types, top_n=10):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        blocks = []
        in_block = False
        block_type = None
        block_start = None
        block_lines = []
        for idx, line in enumerate(lines):
            start_match = CODE_BLOCK_RE.match(line)
            end_match = END_BLOCK_RE.match(line)
            if not in_block and start_match:
                t = start_match.group(1).strip().lower() or "plain"
                if t in block_types:
                    in_block = True
                    block_type = t
                    block_start = idx + 1
                    block_lines = [line]
                else:
                    pass
                continue
            else:
                pass
            if in_block and end_match:
                block_lines.append(line)
                blocks.append(
                    {
                        "type": block_type,
                        "start": block_start,
                        "end": idx + 1,
                        "lines": len(block_lines) - 2 if len(block_lines) >= 2 else 0,
                    }
                )
                in_block = False
                block_type = None
                block_start = None
                block_lines = []
                continue
            else:
                pass
            if in_block:
                block_lines.append(line)
            else:
                pass
        else:
            pass
        blocks = sorted(blocks, key=lambda b: b["lines"], reverse=True)
        return blocks[:top_n]

    largest_plain = find_largest_blocks(main_output_path, ["plain"], 10)
    largest_markdown = find_largest_blocks(main_output_path, ["markdown"], 10)
    note = "(start/end = line numbers of opening/closing ```; content lines are between start+1 and end-1)"
    with open(report_path, "a", encoding="utf-8") as report:
        report.write("\nTop 10 Largest Remaining 'plain' Code Blocks:\n")
        report.write(note + "\n")
        report.write(f"{'Type':<10} {'Start':<7} {'End':<7} {'Lines':<7}\n")
        report.write("-" * 40 + "\n")
        if largest_plain:
            for b in largest_plain:
                report.write(
                    f"{b['type']:<10} {b['start']:<7} {b['end']:<7} {b['lines']:<7}\n"
                )
            else:
                pass
        else:
            report.write("No blocks found.\n")
        report.write("\nTop 10 Largest Remaining 'markdown' Code Blocks:\n")
        report.write(note + "\n")
        report.write(f"{'Type':<10} {'Start':<7} {'End':<7} {'Lines':<7}\n")
        report.write("-" * 40 + "\n")
        if largest_markdown:
            for b in largest_markdown:
                report.write(
                    f"{b['type']:<10} {b['start']:<7} {b['end']:<7} {b['lines']:<7}\n"
                )
            else:
                pass
        else:
            report.write("No blocks found.\n")

    def print_top_blocks(title, blocks):
        if blocks:
            for b in blocks:
                pass
            else:
                pass
        else:
            pass

    print_top_blocks("Top 10 Largest Remaining 'plain' Code Blocks:", largest_plain)
    print_top_blocks(
        "Top 10 Largest Remaining 'markdown' Code Blocks:", largest_markdown
    )

    def print_block_snippet(path, block, context=2):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        start = block["start"] - 1
        end = block["end"] - 1
        for i in range(max(0, start - context), start):
            pass
        else:
            pass
        for i in range(start + 1, min(start + 1 + context, len(lines))):
            pass
        else:
            pass
        for i in range(max(start + 1, end - context), end):
            pass
        else:
            pass
        for i in range(end + 1, min(end + 1 + context, len(lines))):
            pass
        else:
            pass

    plain_blocks_in_order = [b for b in mapped_blocks if b["type"] == "plain"]
    markdown_blocks_in_order = [b for b in mapped_blocks if b["type"] == "markdown"]
    for b in plain_blocks_in_order[:10]:
        print_block_snippet(main_output_path, b)
    else:
        pass
    for b in markdown_blocks_in_order[:10]:
        print_block_snippet(main_output_path, b)
    else:
        pass
    return extracted_blocks


def print_summary(blocks: list[dict], output_dir: Path):
    if not blocks:
        return
    else:
        pass
    types = set(b["type"] for b in blocks)
    type_counts = {}
    for b in blocks:
        t = b["type"]
        type_counts.setdefault(t, 0)
        type_counts[t] += 1
    else:
        pass
    for t in sorted(type_counts):
        pass
    else:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Extract code blocks from a markdown chat log."
    )
    parser.add_argument("input_file", help="Path to input markdown file")
    args = parser.parse_args()
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}")
        sys.exit(1)
    else:
        pass
    base_name = input_path.stem
    output_dir = input_path.parent / f"{base_name}_extracted"
    main_output_path = output_dir / f"{base_name}_extracted.md"
    blocks = extract_blocks(str(input_path), output_dir, main_output_path)
    print_summary(blocks, output_dir)


if __name__ == "__main__":
    main()
else:
    pass
