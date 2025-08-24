#!/usr/bin/env python3
"""
Curated Knowledge Ingestion - Selective import of high-value content
"""

import re
from pathlib import Path
from typing import Dict, List, Set


class CuratedIngestion:
    """Curated selection of reference materials"""

    # High-value patterns to INCLUDE
    INCLUDE_PATTERNS = [
        # Documentation
        "**/README.md",
        "**/api.md",
        "**/CHANGELOG.md",
        # Key reference files
        "gpt-5*.txt",
        "responses*.txt",
        "multi-agent*.txt",
        # Example code
        "**/examples/**/*.py",
        "**/sample*.py",
        "**/demo*.py",
        # Core implementations (not tests)
        "**/src/**/*.py",
        "**/lib/**/*.py",
        # API specs
        "**/openapi*.json",
        "**/swagger*.json",
        # Structured output examples
        "**/structured*.json",
    ]

    # Patterns to EXCLUDE
    EXCLUDE_PATTERNS = [
        # Test files
        "**/test_*.py",
        "**/*_test.py",
        "**/tests/**",
        # Build artifacts
        "**/__pycache__/**",
        "**/build/**",
        "**/dist/**",
        "**.pyc",
        # Config files
        "**/.vscode/**",
        "**/.git/**",
        "**/package*.json",
        "**/tsconfig.json",
        # Data files
        "**.jsonl",
        "**.csv",
        "**.pdf",
        "**.ipynb",
        # Media
        "**.jpg",
        "**.png",
        "**.gif",
        "**.mp4",
        # Dependencies
        "**/node_modules/**",
        "**/venv/**",
    ]

    # Content filters
    MIN_FILE_SIZE = 100  # bytes
    MAX_FILE_SIZE = 100_000  # 100KB per file

    @classmethod
    def should_include(cls, file_path: Path) -> bool:
        """Determine if file should be included"""

        # Check size
        try:
            size = file_path.stat().st_size
            if size < cls.MIN_FILE_SIZE or size > cls.MAX_FILE_SIZE:
                return False
        except:
            return False

        # Check exclude patterns first
        for pattern in cls.EXCLUDE_PATTERNS:
            if file_path.match(pattern):
                return False

        # Check include patterns
        for pattern in cls.INCLUDE_PATTERNS:
            if file_path.match(pattern):
                return True

        # Default: include .py and .md files not caught above
        if file_path.suffix in [".py", ".md", ".txt"]:
            # Additional content check for Python files
            if file_path.suffix == ".py":
                try:
                    content = file_path.read_text(errors="ignore")
                    # Skip if mostly imports or empty
                    if content.count("\n") < 10:
                        return False
                    # Skip if no functions/classes
                    if "def " not in content and "class " not in content:
                        return False
                except:
                    return False
            return True

        return False

    @classmethod
    def extract_valuable_content(cls, file_path: Path) -> List[Dict]:
        """Extract only valuable parts from a file"""
        chunks = []
        content = file_path.read_text(errors="ignore")

        if file_path.suffix == ".py":
            # Extract docstrings and function signatures
            # Pattern for functions with docstrings
            func_pattern = r'def\s+(\w+)\([^)]*\)[^:]*:\s*"""([^"]+)"""'
            for match in re.finditer(func_pattern, content, re.DOTALL):
                func_name, docstring = match.groups()
                chunks.append(
                    {
                        "content": f"Function {func_name}: {docstring[:500]}",
                        "type": "FUNCTION_DOC",
                        "source": str(file_path),
                    }
                )

            # Extract class definitions
            class_pattern = r'class\s+(\w+)[^:]*:\s*"""([^"]+)"""'
            for match in re.finditer(class_pattern, content, re.DOTALL):
                class_name, docstring = match.groups()
                chunks.append(
                    {
                        "content": f"Class {class_name}: {docstring[:500]}",
                        "type": "CLASS_DOC",
                        "source": str(file_path),
                    }
                )

        elif file_path.suffix == ".md":
            # Extract headers and code blocks
            # Code blocks
            code_blocks = re.findall(r"```(\w+)?\n(.*?)```", content, re.DOTALL)
            for lang, code in code_blocks:
                if len(code) > 50:
                    chunks.append(
                        {
                            "content": code[:1000],
                            "type": "CODE_EXAMPLE",
                            "source": str(file_path),
                            "language": lang or "unknown",
                        }
                    )

            # Important sections
            sections = re.split(r"^##\s+", content, flags=re.MULTILINE)
            for section in sections[1:3]:  # First 2 sections after intro
                if len(section) > 100:
                    chunks.append(
                        {
                            "content": section[:1000],
                            "type": "DOCUMENTATION",
                            "source": str(file_path),
                        }
                    )

        # If no specific extraction, take the most valuable part
        if not chunks and len(content) > 200:
            # Take first substantial paragraph
            chunks.append(
                {
                    "content": content[:1000],
                    "type": "REFERENCE",
                    "source": str(file_path),
                }
            )

        return chunks

    @classmethod
    def analyze_directory(cls, directory: str = "/home/opsvi/.reference"):
        """Analyze what would be included/excluded"""
        path = Path(directory)

        included = []
        excluded = []
        total_included_size = 0
        total_excluded_size = 0

        for file_path in path.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                if cls.should_include(file_path):
                    included.append(file_path)
                    total_included_size += size
                else:
                    excluded.append(file_path)
                    total_excluded_size += size

        print(f"CURATION ANALYSIS")
        print(f"=" * 60)
        print(f"Total files: {len(included) + len(excluded)}")
        print(f"Files to include: {len(included)}")
        print(f"Files to exclude: {len(excluded)}")
        print(f"Size to process: {total_included_size / 1024 / 1024:.1f} MB")
        print(f"Size excluded: {total_excluded_size / 1024 / 1024:.1f} MB")
        print(
            f"Reduction: {(total_excluded_size / (total_included_size + total_excluded_size)) * 100:.1f}%"
        )

        # Show sample of what's included
        print(f"\nSample of included files:")
        for f in included[:10]:
            print(f"  ✓ {f.relative_to(path)}")

        # Show what's being excluded
        excluded_types = {}
        for f in excluded:
            ext = f.suffix or "no_ext"
            excluded_types[ext] = excluded_types.get(ext, 0) + 1

        print(f"\nExcluded by type:")
        for ext, count in sorted(
            excluded_types.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  ✗ {ext}: {count} files")

        return included, excluded


if __name__ == "__main__":
    # Analyze what would be curated
    included, excluded = CuratedIngestion.analyze_directory()
