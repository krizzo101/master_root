"""
File Map Generator

This script generates a file map for various file types and adds it to the beginning of the file.
The file map provides AI agents with a quick overview of the file contents for better context.
"""

import os
import sys
import re
import time
import hashlib
import asyncio
import multiprocessing
from fnmatch import fnmatch
from pathlib import Path
import argparse
import json
from typing import List, Optional

# For API clients
from openai import AsyncOpenAI
from openai import RateLimitError, APIError, APITimeoutError

# Configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_VENDOR = "openai"
SUPPORTED_VENDORS = ["openai", "anthropic", "cohere"]  # Add more as needed

# File comment styles for different file types
COMMENT_STYLES = {
    # Format: (start_multi, end_multi, single_line)
    ".py": ('"""', '"""', "# "),
    ".js": ("/*", "*/", "// "),
    ".ts": ("/*", "*/", "// "),
    ".tsx": ("/*", "*/", "// "),
    ".jsx": ("/*", "*/", "// "),
    ".css": ("/*", "*/", "/* "),
    ".html": ("<!--", "-->", "<!-- "),
    ".md": ("<!--", "-->", "<!-- "),
    ".sql": ("/*", "*/", "-- "),
    ".sh": (":<<!EOF", "!EOF", "# "),
    ".bash": (":<<!EOF", "!EOF", "# "),
    ".txt": ("", "", ""),
    # Add more file types as needed
}

# Default comment style for unknown file types
DEFAULT_COMMENT_STYLE = ("/*", "*/", "// ")

# Custom templates storage
TEMPLATES_DIR = os.path.expanduser("~/.file_map_templates")

# Report data
report_data = {
    "processed_files": 0,
    "updated_files": 0,
    "skipped_files": 0,
    "errors": 0,
    "api_calls": 0,
    "api_tokens_used": 0,
    "duration": 0,
    "detailed_logs": [],
}


class APIClient:
    """Base class for API clients"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_completion(
        self, system_message: str, user_message: str, model: str, max_tokens: int = 1500
    ) -> str:
        """Generate a completion - to be implemented by specific vendor clients"""
        raise NotImplementedError("Must be implemented by subclass")


class OpenAIClient(APIClient):
    """OpenAI API client"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_completion(
        self, system_message: str, user_message: str, model: str, max_tokens: int = 1500
    ) -> str:
        """Generate a completion using OpenAI API"""
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


# Add other API clients here (Anthropic, Cohere, etc.)


def create_api_client(vendor: str, api_key: str) -> APIClient:
    """Factory function to create the appropriate API client"""
    if vendor == "openai":
        return OpenAIClient(api_key)
    # Add other vendors as needed
    raise ValueError(f"Unsupported vendor: {vendor}")


def get_api_key(vendor: str, api_key_var: Optional[str] = None) -> str:
    """Get API key from environment variables based on vendor"""
    # Use provided API key variable if specified
    if api_key_var:
        api_key = os.environ.get(api_key_var)
        if not api_key:
            raise ValueError(f"{api_key_var} environment variable not set")
        return api_key

    # Otherwise use default based on vendor
    if vendor == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return api_key
    elif vendor == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        return api_key
    elif vendor == "cohere":
        api_key = os.environ.get("COHERE_API_KEY")
        if not api_key:
            raise ValueError("COHERE_API_KEY environment variable not set")
        return api_key
    else:
        raise ValueError(f"Unsupported vendor: {vendor}")


def get_comment_style(file_path):
    """Get the appropriate comment style for the file type"""
    ext = Path(file_path).suffix.lower()
    return COMMENT_STYLES.get(ext, DEFAULT_COMMENT_STYLE)


def calculate_file_hash(content: str) -> str:
    """Calculate a hash for the file content to detect changes"""
    return hashlib.md5(content.encode()).hexdigest()


def extract_existing_file_map(content, comment_style):
    """Extract existing file map from the content if it exists"""
    start_multi, end_multi, single_line = comment_style

    # Pattern to match file map section
    if start_multi and end_multi:
        pattern = re.escape(start_multi) + r"\s*FILE MAP.*?" + re.escape(end_multi)
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(0), content[match.end() :].lstrip()

    # Try to match single-line comment style file maps
    if single_line:
        pattern = (
            f"^{re.escape(single_line)}FILE MAP.*?{re.escape(single_line)}END FILE MAP"
        )
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        if match:
            return match.group(0), content[match.end() :].lstrip()

    return None, content


def validate_line_numbers(file_map: str, content: str) -> bool:
    """Enhanced validation of line numbers in the file map against the actual content"""
    # Extract line numbers mentioned in the file map
    line_number_pattern = r"lines?\s+(\d+)[-–](\d+)|lines?\s+(\d+)|line\s+(\d+)"
    matches = re.findall(line_number_pattern, file_map, re.IGNORECASE)

    # Count actual lines in the content
    content_lines = content.split("\n")
    actual_lines = len(content_lines)

    # Check if any line number exceeds the actual line count
    for match in matches:
        # Handle range format (lines X-Y)
        if match[0] and match[1]:
            start = int(match[0])
            end = int(match[1])
            if end > actual_lines:
                return False
        # Handle single line format (line X)
        elif match[2]:
            line_num = int(match[2])
            if line_num > actual_lines:
                return False
        elif match[3]:
            line_num = int(match[3])
            if line_num > actual_lines:
                return False

    # Enhanced validation: Check for structural elements
    structural_patterns = {
        "class": r"class\s+\w+",
        "function/method": r"(def|function)\s+\w+",
        "imports": r"import\s+|from\s+\w+\s+import",
        "constants": r"[A-Z_]{2,}\s*=",
        "async functions": r"async\s+def",
        "exports": r"module\.exports|export\s+",
        "components": r"React\.Component|extends\s+Component|function\s+\w+\s*\(",
    }

    # Check if major structural elements are mentioned in the file map
    for element_name, pattern in structural_patterns.items():
        # If the file contains this structural element
        if re.search(pattern, content):
            # Check if the element is mentioned in the file map (with some flexibility)
            element_terms = element_name.split("/")
            element_mentioned = any(
                re.search(rf"{term}s?", file_map, re.IGNORECASE)
                for term in element_terms
            )
            if not element_mentioned:
                return False

    # Validate section headers match
    section_headers = re.findall(r"^#+\s+(.*?)$", content, re.MULTILINE)
    for header in section_headers[:5]:  # Check first 5 headers
        if header and not re.search(re.escape(header), file_map, re.IGNORECASE):
            return False

    return True


def load_template(template_name: str) -> Optional[str]:
    """Load a custom file map template"""
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.template")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


async def generate_file_map(
    file_path: str,
    content: str,
    comment_style: tuple,
    api_client: APIClient,
    model: str,
    template: Optional[str] = None,
) -> Optional[str]:
    """Generate a file map using the API"""
    start_multi, end_multi, single_line = comment_style

    # If the file type doesn't support comments, use a generic format
    if not (start_multi or single_line):
        start_multi = "/*"
        end_multi = "*/"

    # Extract existing file map if it exists
    existing_map, _ = extract_existing_file_map(content, comment_style)

    # Calculate hash of the content without the file map
    content_hash = calculate_file_hash(_)

    # Check if there's a stored hash for this file
    hash_file = f"{file_path}.hash"
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            stored_hash = f.read().strip()

        # If hash matches and we have an existing map, no need to update
        if (
            stored_hash == content_hash
            and existing_map
            and validate_line_numbers(existing_map, content)
        ):
            return None

    # If there's an existing map, validate it
    if existing_map and validate_line_numbers(existing_map, content):
        print(f"Found valid file map in {file_path}, checking if it needs updating...")
    else:
        # If validation fails or no existing map, we need a new one
        if existing_map:
            print(
                f"File map in {file_path} has invalid line numbers, generating new map..."
            )

    # Load custom template if specified
    template_content = ""
    if template:
        template_content = load_template(template)
        if not template_content:
            print(f"Warning: Template '{template}' not found, using default template")

    system_message = """You are a specialized AI assistant that creates detailed file maps for code and documentation files.
    
Task: Analyze the provided file and create a comprehensive file map that will help AI agents understand the file structure within the first 50 lines of the file.

Purpose:
The file map is designed to solve a specific problem with AI code assistants. Many AI agents only read the first 50 lines of a file by default to get context before making suggestions or edits, which often results in incomplete understanding of the file's structure and purpose. By placing a detailed file map at the top of the file, we ensure the AI gets complete context even when reading only the first 50 lines.

Your file map should:
1. Include a table of contents with accurate line numbers for each major section
2. Provide brief descriptions of each section's purpose and functionality
3. For code files: list important functions, classes, components with their line numbers, parameters, and return values
4. For documentation: outline key sections, subsections, and important elements
5. Be concise yet informative enough for an AI to understand the entire file from just this map
6. Only include factual content about the file structure (no interpretations or speculation)
7. Ensure line numbers are accurate and match the current file state

Format the file map between the comment markers appropriate for the file type.
Do NOT modify any of the original file content outside the file map section.
If you detect an existing file map, validate its line numbers against the actual content. If line numbers don't match or the file map doesn't accurately reflect the content, generate a new one.
"""

    # Add custom template instructions if available
    if template_content:
        system_message += f"\n\nUse the following template format for the file map:\n{template_content}"

    prompt = f"""Analyze the following file and create a FILE MAP:

FILE PATH: {file_path}

FILE CONTENT:
{content}

Create a structured, informative file map for this content. Include accurate line numbers, section descriptions, and key components.
The file map should help AI agents quickly understand the file structure when they can only read the first 50 lines.

If you detect an existing file map at the beginning of the file:
1. Validate the line numbers against the actual content
2. Check if sections in the file map match the actual file structure
3. Only keep the existing file map if both line numbers and section descriptions are accurate
4. If there are discrepancies, generate a new file map that correctly reflects the current file state

If you determine a new file map is needed, ensure it is comprehensive yet concise, capturing all important elements with their line numbers and purpose.
If the existing file map is already correct and sufficient, indicate that no changes are needed.

Start your file map with "FILE MAP START" and end with "FILE MAP END" markers.
"""

    # Update API usage stats
    report_data["api_calls"] += 1

    # Generate with exponential backoff for rate limits
    max_retries = 5
    base_delay = 1
    for attempt in range(max_retries):
        try:
            result = await api_client.generate_completion(system_message, prompt, model)
            break
        except (RateLimitError, APIError, APITimeoutError) as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2**attempt)
            print(f"API rate limit hit. Retrying in {delay:.2f} seconds...")
            await asyncio.sleep(delay)

    # Extract just the file map part
    map_start = result.find("FILE MAP START")
    map_end = result.find("FILE MAP END")

    if map_start == -1 or map_end == -1:
        # If no markers found, use the whole response
        file_map_content = result
    else:
        # Extract content between markers
        file_map_content = result[map_start + len("FILE MAP START") : map_end].strip()

    # Check if the response indicates no changes needed
    if (
        "no changes" in result.lower()
        or "already correct" in result.lower()
        or "already up to date" in result.lower()
    ):
        # Save the current hash
        with open(hash_file, "w") as f:
            f.write(content_hash)
        return None  # No changes needed

    # Format the file map with the appropriate comment style
    if start_multi and end_multi:
        file_map = f"{start_multi}\nFILE MAP\n{file_map_content}\n{end_multi}\n\n"
    else:
        # Fall back to single-line comments
        lines = [f"{single_line}{line}" for line in file_map_content.split("\n")]
        file_map = (
            f"{single_line}FILE MAP\n"
            + "\n".join(lines)
            + f"\n{single_line}END FILE MAP\n\n"
        )

    # Save the current hash
    with open(hash_file, "w") as f:
        f.write(content_hash)

    return file_map


async def update_file_with_map(
    file_path: str,
    api_client: APIClient,
    model: str,
    template: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """Update the file with a generated file map"""
    try:
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Get the appropriate comment style
        comment_style = get_comment_style(file_path)

        # Extract existing file map if it exists
        existing_map, remaining_content = extract_existing_file_map(
            content, comment_style
        )

        # Generate a new file map
        new_map = await generate_file_map(
            file_path, content, comment_style, api_client, model, template
        )

        # If the file map generator decided no changes are needed, exit
        if new_map is None:
            print(f"File map for {file_path} is already up to date. No changes made.")
            report_data["skipped_files"] += 1
            report_data["detailed_logs"].append(
                {"file": file_path, "action": "skipped", "reason": "up-to-date"}
            )
            return False

        # If dry run, just print the changes
        if dry_run:
            print(f"\n--- Would update file map for {file_path} ---")
            print(f"New file map:\n{new_map}")
            report_data["detailed_logs"].append(
                {"file": file_path, "action": "dry-run", "new_map": new_map}
            )
            return True

        # Write the updated content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_map + remaining_content)

        print(f"Updated file map for {file_path}")
        report_data["updated_files"] += 1
        report_data["detailed_logs"].append({"file": file_path, "action": "updated"})
        return True

    except Exception as e:
        print(f"Error updating file {file_path}: {str(e)}")
        report_data["errors"] += 1
        report_data["detailed_logs"].append(
            {"file": file_path, "action": "error", "error": str(e)}
        )
        return False


def should_ignore_file(file_path: str, ignore_patterns: List[str]) -> bool:
    """Check if a file should be ignored based on patterns"""
    if not ignore_patterns:
        return False

    # Convert to relative path if it's absolute
    if os.path.isabs(file_path):
        rel_path = os.path.relpath(file_path)
    else:
        rel_path = file_path

    # Check if file matches any ignore pattern
    for pattern in ignore_patterns:
        if fnmatch(rel_path, pattern) or fnmatch(os.path.basename(rel_path), pattern):
            return True

    return False


def load_ignore_patterns(ignore_file: str) -> List[str]:
    """Load ignore patterns from a file (gitignore-style)"""
    patterns = []
    if os.path.exists(ignore_file):
        with open(ignore_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    return patterns


async def process_files_async(args):
    """Process files using async operations"""
    start_time = time.time()

    # Get API client
    api_key = get_api_key(args.vendor, args.api_key_var)
    api_client = create_api_client(args.vendor, api_key)

    # Load ignore patterns
    ignore_patterns = []
    if args.ignore_file:
        ignore_patterns = load_ignore_patterns(args.ignore_file)

    # Collect files to process
    files_to_process = []

    if os.path.isfile(args.path):
        if not should_ignore_file(args.path, ignore_patterns):
            files_to_process.append(args.path)
    elif os.path.isdir(args.path):
        # Collect all files, recursively if specified
        if args.recursive:
            for root, _, files in os.walk(args.path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if should_ignore_file(file_path, ignore_patterns):
                        continue

                    file_ext = Path(file_path).suffix.lower()

                    # Apply include/exclude filters
                    if args.include and file_ext not in args.include:
                        continue
                    if args.exclude and file_ext in args.exclude:
                        continue

                    files_to_process.append(file_path)
        else:
            for file in os.listdir(args.path):
                file_path = os.path.join(args.path, file)
                if not os.path.isfile(file_path) or should_ignore_file(
                    file_path, ignore_patterns
                ):
                    continue

                file_ext = Path(file_path).suffix.lower()

                # Apply include/exclude filters
                if args.include and file_ext not in args.include:
                    continue
                if args.exclude and file_ext in args.exclude:
                    continue

                files_to_process.append(file_path)
    else:
        print(f"Error: Path {args.path} does not exist")
        return False

    # Update report data
    report_data["processed_files"] = len(files_to_process)

    # Process files in parallel with a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(args.concurrency)

    async def process_with_semaphore(file_path):
        async with semaphore:
            return await update_file_with_map(
                file_path, api_client, args.model, args.template, args.dry_run
            )

    # Create tasks for all files
    tasks = [process_with_semaphore(file) for file in files_to_process]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    success = True
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error processing {files_to_process[i]}: {str(result)}")
            report_data["errors"] += 1
            success = False
        elif not result:
            # File was skipped or had an error
            pass

    # Calculate duration
    report_data["duration"] = time.time() - start_time

    # Generate report if requested
    if args.report:
        generate_report(args.report)

    return success


def generate_project_map(
    path: str,
    ignore_patterns: List[str],
    include: Optional[List[str]],
    exclude: Optional[List[str]],
    output_path: str,
    recursive: bool = True,
):
    """
    Generate a project-level file map that consolidates references to all project files and their file maps.
    """
    lines = []
    lines.append("# Project File Map\n")
    lines.append(
        "This document provides an overview of all project files and their file maps.\n"
    )

    if recursive:
        walker = os.walk(path)
    else:
        # If not recursive, list files in the top-level directory only
        walker = [(path, [], os.listdir(path))]

    for root, _, files in walker:
        for file in files:
            file_path = os.path.join(root, file)
            if should_ignore_file(file_path, ignore_patterns):
                continue
            file_ext = Path(file_path).suffix.lower()
            if include and file_ext not in include:
                continue
            if exclude and file_ext in exclude:
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                comment_style = get_comment_style(file_path)
                file_map, _ = extract_existing_file_map(content, comment_style)
                lines.append(f"## {file_path}")
                if file_map:
                    lines.append("```")
                    lines.append(file_map)
                    lines.append("```")
                else:
                    lines.append("_No file map available_")
                lines.append("\n")
            except Exception as e:
                lines.append(f"## {file_path}")
                lines.append(f"_Error reading file: {str(e)}_")
                lines.append("\n")
    output = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\nProject-level file map generated at {output_path}")


def generate_report(report_path: str):
    """Generate a summary report of file map operations"""
    report = {
        "summary": {
            "total_processed": report_data["processed_files"],
            "updated": report_data["updated_files"],
            "skipped": report_data["skipped_files"],
            "errors": report_data["errors"],
            "api_calls": report_data["api_calls"],
            "api_tokens_estimated": report_data["api_tokens_used"],
            "duration_seconds": report_data["duration"],
        },
        "detailed_logs": report_data["detailed_logs"],
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport generated at {report_path}")

    # Also print summary to console
    print("\nSummary:")
    print(f"  Files processed: {report_data['processed_files']}")
    print(f"  Files updated: {report_data['updated_files']}")
    print(f"  Files skipped: {report_data['skipped_files']}")
    print(f"  Errors: {report_data['errors']}")
    print(f"  API calls: {report_data['api_calls']}")
    print(f"  Duration: {report_data['duration']:.2f} seconds")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate file maps for better AI agent context"
    )
    parser.add_argument(
        "path", help="Path to the file or directory to update with file maps"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process directories recursively"
    )
    parser.add_argument(
        "-i",
        "--include",
        help="Only process these file types (comma-separated extensions including the dot, e.g., .py,.js)",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        help="Exclude these file types (comma-separated extensions including the dot, e.g., .md,.txt)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-v",
        "--vendor",
        default=DEFAULT_VENDOR,
        choices=SUPPORTED_VENDORS,
        help=f"API vendor to use (default: {DEFAULT_VENDOR})",
    )
    parser.add_argument(
        "-k", "--api-key-var", help="Environment variable name for API key"
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show changes without writing to files",
    )
    parser.add_argument(
        "-t", "--template", help="Custom template name to use for file maps"
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=5,
        help="Maximum number of concurrent file operations",
    )
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Number of processes for CPU-bound operations",
    )
    parser.add_argument(
        "-g",
        "--ignore-file",
        help="Path to a gitignore-style file with patterns to ignore",
    )
    parser.add_argument(
        "-o", "--report", help="Generate a JSON report file at the specified path"
    )
    # New arguments for project-level file map generation
    parser.add_argument(
        "--project-map",
        action="store_true",
        help="Generate a project-level file map with references to all project files and their file maps",
    )
    parser.add_argument(
        "--project-map-out",
        default="PROJECT_FILE_MAP.md",
        help="Output file for the project-level file map",
    )

    args = parser.parse_args()

    # Convert comma-separated strings to lists
    args.include = args.include.split(",") if args.include else None
    args.exclude = args.exclude.split(",") if args.exclude else None

    # Create templates directory if it doesn't exist
    if args.template and not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)

    # If project-level file map option is set, generate it first
    if args.project_map:
        ignore_patterns = (
            load_ignore_patterns(args.ignore_file) if args.ignore_file else []
        )
        generate_project_map(
            args.path,
            ignore_patterns,
            args.include,
            args.exclude,
            args.project_map_out,
            recursive=args.recursive,
        )

    # Run async code for per-file file maps
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        success = asyncio.run(process_files_async(args))
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
