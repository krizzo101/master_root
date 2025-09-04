# Chat Search Tool Enhancement Proposal: --list-files-used

## Overview

Add a new `--list-files-used` switch to the chat_search tool that automatically extracts and lists all files that were referenced, read, written, or modified during a chat session.

## Proposed Implementation

### New Command Line Option

```bash
python3 apps/chat-search/chat_search.py --list-files-used [--file-filter SESSION_ID]
```

### New Method in ChatSearcher Class

```python
def extract_files_used(self, files_filter: List[str] = None) -> Dict[str, List[Dict]]:
    """
    Extract all files referenced in chat sessions

    Returns:
        Dict mapping session_id to list of file operations with metadata
    """
    file_operations = defaultdict(lambda: defaultdict(list))

    # Get all JSONL files
    jsonl_files = glob.glob(f"{self.log_dir}/*.jsonl")

    # Filter by specific files if requested
    if files_filter:
        jsonl_files = [
            f for f in jsonl_files if any(fname in f for fname in files_filter)
        ]

    # Patterns to match file operations
    file_patterns = {
        'read': [
            r'"name":\s*"read_file"',
            r'"name":\s*"read"',
            r'Used Read\s*\(file_path=([^)]+)\)',
            r'"file_path":\s*"([^"]+)"',
        ],
        'write': [
            r'"name":\s*"write"',
            r'"name":\s*"write_file"',
            r'Used Write\s*\(file_path=([^)]+)\)',
        ],
        'edit': [
            r'"name":\s*"search_replace"',
            r'"name":\s*"MultiEdit"',
            r'Used.*Edit.*\(file_path=([^)]+)\)',
        ],
        'delete': [
            r'"name":\s*"delete_file"',
            r'Used Delete.*\(file_path=([^)]+)\)',
        ],
        'list': [
            r'"name":\s*"list_dir"',
            r'"name":\s*"glob_file_search"',
            r'Used.*List.*\(target_directory=([^)]+)\)',
        ]
    }

    for file_path in jsonl_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        message_data = json.loads(line.strip())
                        session_id = message_data.get("sessionId", "unknown")
                        timestamp = message_data.get("timestamp", "")

                        # Check assistant messages for tool calls
                        if message_data.get("role") == "assistant":
                            content = message_data.get("content", "")

                            # Parse tool calls from content
                            for operation_type, patterns in file_patterns.items():
                                for pattern in patterns:
                                    matches = re.finditer(pattern, content, re.IGNORECASE)
                                    for match in matches:
                                        file_path_extracted = match.group(1) if match.groups() else "unknown"

                                        file_operations[session_id][operation_type].append({
                                            "file": file_path_extracted,
                                            "timestamp": timestamp,
                                            "line": line_num,
                                            "context": content[:200] + "..." if len(content) > 200 else content
                                        })

                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            continue

    return dict(file_operations)
```

### Enhanced Main Function

```python
def main():
    parser = argparse.ArgumentParser(description="Search chat logs quickly")
    parser.add_argument("query", nargs="?", help="Search query (regex supported)")
    parser.add_argument(
        "--type",
        "-t",
        choices=["user", "assistant", "all", "tools"],
        default="all",
        help="Content type to search",
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=10, help="Maximum results to return"
    )
    parser.add_argument(
        "--no-context", action="store_true", help="Disable context output"
    )
    parser.add_argument(
        "--files", "-f", action="store_true", help="List available chat log files"
    )
    parser.add_argument(
        "--list-files-used",
        action="store_true",
        help="Extract and list all files referenced in chat sessions"
    )
    parser.add_argument("--dir", "-d", default="chat_logs", help="Chat logs directory")
    parser.add_argument("--date-from", help="Start date filter (YYYY-MM-DD)")
    parser.add_argument("--date-to", help="End date filter (YYYY-MM-DD)")
    parser.add_argument(
        "--file-filter", nargs="+", help="Search only these specific files"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full verbose output (default is concise)",
    )

    args = parser.parse_args()

    searcher = ChatSearcher(args.dir)

    if args.files:
        print("Available chat log files:")
        files = searcher.list_files()
        for file_info in files:
            print(
                f"  {file_info['file']} - {file_info['sessions']} sessions - {file_info['first_timestamp']}"
            )
        return

    if args.list_files_used:
        print("Files referenced in chat sessions:\n")
        file_ops = searcher.extract_files_used(args.file_filter)

        for session_id, operations in file_ops.items():
            print(f"=== Session: {session_id} ===")

            for op_type, files in operations.items():
                if files:
                    print(f"\n{op_type.upper()} Operations:")
                    for file_op in files:
                        timestamp = file_op['timestamp'].split('T')[1][:8] if 'T' in file_op['timestamp'] else file_op['timestamp']
                        print(f"  {timestamp} | {file_op['file']}")
                        if args.verbose:
                            print(f"    Context: {file_op['context']}")
            print()
        return

    # ... rest of existing main function
```

## Example Usage

### Basic File List
```bash
python3 apps/chat-search/chat_search.py --list-files-used
```

### Files from Specific Session
```bash
python3 apps/chat-search/chat_search.py --list-files-used --file-filter 0678c5b6-69e0-41bb-9232-61b098314ad6.jsonl
```

### Verbose Output with Context
```bash
python3 apps/chat-search/chat_search.py --list-files-used --file-filter 0678c5b6-69e0-41bb-9232-61b098314ad6.jsonl --verbose
```

## Expected Output Format

```
Files referenced in chat sessions:

=== Session: 0678c5b6-69e0-41bb-9232-61b098314ad6 ===

READ Operations:
  03:47:10 | /home/opsvi/master_root/libs/opsvi-llm/src/opsvi_llm/openai_interface.py
  03:47:13 | /home/opsvi/master_root/libs/opsvi-llm/src/opsvi_llm/__init__.py
  03:47:19 | /home/opsvi/master_root/libs/opsvi-llm/pyproject.toml

WRITE Operations:
  03:48:45 | /home/opsvi/master_root/analysis_report.md

EDIT Operations:
  03:49:12 | /home/opsvi/master_root/.claude/commands/handoff.md

LIST Operations:
  03:46:50 | /home/opsvi/master_root/libs/opsvi-llm/
```

## Benefits

1. **Quick Session Overview**: Instantly see what files were touched during a session
2. **Handoff Context**: Perfect for session handoffs - know exactly what was worked on
3. **Audit Trail**: Track file operations across chat sessions
4. **Debugging**: Quickly identify which files were involved in a session
5. **Documentation**: Generate file operation summaries for reports

## Implementation Notes

- Uses regex patterns to extract file paths from tool call JSON
- Handles different tool naming conventions (read_file vs read)
- Groups operations by type (read, write, edit, delete, list)
- Provides timestamp and context information
- Compatible with existing file filtering and verbose options
- Maintains backward compatibility with existing functionality

## Future Enhancements

1. **File Operation Statistics**: Count how many times each file was accessed
2. **File Size Information**: Show file sizes when available
3. **Git Integration**: Show git status of files (modified, new, etc.)
4. **Export Options**: Export file lists to JSON/CSV for further analysis
5. **File Dependency Analysis**: Track relationships between files accessed in sequence
