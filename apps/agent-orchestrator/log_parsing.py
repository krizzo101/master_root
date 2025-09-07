"""
Log Parsing and Formatting Module for Claude Code Session Logs

This module provides utilities for parsing JSONL log files and formatting
log entries for display in terminal-based monitoring applications.
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import hashlib


class LogParser:
    """Parse and format Claude Code session log entries."""
    
    # Role indicators for different log entry types
    ROLE_INDICATORS = {
        'user': '👤',
        'assistant': '🤖',
        'system': '⚙️',
        'summary': '📝',
        'tool_use': '🔧',
        'tool_result': '📊',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    
    # ANSI color codes for terminal output
    COLORS = {
        'user': '\033[94m',        # Blue
        'assistant': '\033[92m',   # Green
        'system': '\033[93m',       # Yellow
        'summary': '\033[95m',      # Magenta
        'error': '\033[91m',        # Red
        'warning': '\033[93m',      # Yellow
        'reset': '\033[0m',         # Reset
        'bold': '\033[1m',          # Bold
        'dim': '\033[2m'            # Dim
    }
    
    # Maximum content length before truncation
    MAX_CONTENT_LENGTH = 200
    MAX_TOOL_INPUT_LENGTH = 100
    
    def __init__(self, color_enabled: bool = True, truncate_enabled: bool = True):
        """
        Initialize the LogParser.
        
        Args:
            color_enabled: Whether to include ANSI color codes in output
            truncate_enabled: Whether to truncate long content
        """
        self.color_enabled = color_enabled
        self.truncate_enabled = truncate_enabled
        self._ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    
    def parse_jsonl_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single JSONL line into a dictionary.
        
        Args:
            line: Raw JSONL string
            
        Returns:
            Parsed JSON object or None if parsing fails
        """
        if not line or not line.strip():
            return None
            
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError as e:
            # Try to recover from common issues
            if '}{' in line:
                # Handle concatenated JSON objects
                parts = line.split('}{')
                if parts:
                    try:
                        return json.loads(parts[0] + '}')
                    except:
                        pass
            return None
    
    def parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse ISO 8601 timestamp string.
        
        Args:
            timestamp_str: ISO 8601 formatted timestamp
            
        Returns:
            datetime object or None if parsing fails
        """
        if not timestamp_str:
            return None
            
        try:
            # Handle both Z and +00:00 timezone formats
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, AttributeError):
            return None
    
    def format_timestamp(self, timestamp: Union[str, datetime], 
                        format_str: str = "%H:%M:%S") -> str:
        """
        Format timestamp for display.
        
        Args:
            timestamp: datetime object or ISO string
            format_str: strftime format string
            
        Returns:
            Formatted timestamp string
        """
        if isinstance(timestamp, str):
            dt = self.parse_timestamp(timestamp)
        else:
            dt = timestamp
            
        if dt:
            return dt.strftime(format_str)
        return "??:??:??"
    
    def get_agent_color(self, uuid: str) -> str:
        """
        Generate a consistent color for an agent based on UUID.
        
        Args:
            uuid: Agent UUID
            
        Returns:
            ANSI color code
        """
        if not uuid or not self.color_enabled:
            return ""
            
        # Use last 8 chars of UUID for color generation
        uuid_suffix = uuid[-8:] if len(uuid) >= 8 else uuid
        hash_val = int(hashlib.md5(uuid_suffix.encode()).hexdigest()[:6], 16)
        
        # Generate color in 256-color mode
        color_index = 16 + (hash_val % 216)  # Use extended colors
        return f"\033[38;5;{color_index}m"
    
    def truncate_content(self, content: str, max_length: int = None) -> str:
        """
        Intelligently truncate content while preserving meaning.
        
        Args:
            content: Content to truncate
            max_length: Maximum length (uses default if None)
            
        Returns:
            Truncated content with ellipsis if needed
        """
        if not self.truncate_enabled:
            return content
            
        max_length = max_length or self.MAX_CONTENT_LENGTH
        
        if len(content) <= max_length:
            return content
        
        # Try to break at word boundary
        truncated = content[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If space is reasonably close to end
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def strip_ansi_codes(self, text: str) -> str:
        """
        Remove ANSI escape codes from text.
        
        Args:
            text: Text with potential ANSI codes
            
        Returns:
            Clean text without ANSI codes
        """
        return self._ansi_escape.sub('', text)
    
    def extract_content(self, entry: Dict[str, Any]) -> str:
        """
        Extract main content from a log entry.
        
        Args:
            entry: Parsed log entry
            
        Returns:
            Extracted content string
        """
        entry_type = entry.get('type', '')
        
        if entry_type == 'user':
            message = entry.get('message', {})
            content = message.get('content', '')
            
            # Check for tool results
            tool_results = entry.get('toolUseResult', [])
            if tool_results:
                results = []
                for result in tool_results:
                    if result.get('type') == 'text':
                        results.append(result.get('text', ''))
                if results:
                    content = f"[Tool Result] {' | '.join(results)}"
            
            # Handle session hooks
            if '<session-start-hook>' in content:
                content = "[Session Start]"
            elif '<session-end-hook>' in content:
                content = "[Session End]"
                
        elif entry_type == 'assistant':
            message = entry.get('message', {})
            content_items = message.get('content', [])
            
            if isinstance(content_items, list):
                parts = []
                for item in content_items:
                    if item.get('type') == 'text':
                        parts.append(item.get('text', ''))
                    elif item.get('type') == 'tool_use':
                        tool_name = item.get('name', 'unknown')
                        tool_input = json.dumps(item.get('input', {}))
                        tool_input = self.truncate_content(tool_input, 
                                                          self.MAX_TOOL_INPUT_LENGTH)
                        parts.append(f"[Tool: {tool_name}] {tool_input}")
                content = ' '.join(parts)
            else:
                content = str(content_items)
                
        elif entry_type == 'system':
            content = entry.get('content', '')
            # Strip ANSI codes from system messages
            content = self.strip_ansi_codes(content)
            
        elif entry_type == 'summary':
            content = entry.get('summary', '')
            
        else:
            content = str(entry)
        
        return content
    
    def get_role_indicator(self, entry: Dict[str, Any]) -> str:
        """
        Get role indicator emoji/symbol for entry type.
        
        Args:
            entry: Parsed log entry
            
        Returns:
            Role indicator string
        """
        entry_type = entry.get('type', '')
        
        # Check for special cases
        if entry_type == 'user':
            if entry.get('toolUseResult'):
                return self.ROLE_INDICATORS.get('tool_result', '📊')
        elif entry_type == 'assistant':
            message = entry.get('message', {})
            content = message.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'tool_use':
                        return self.ROLE_INDICATORS.get('tool_use', '🔧')
        elif entry_type == 'system':
            level = entry.get('level', 'info')
            if level in self.ROLE_INDICATORS:
                return self.ROLE_INDICATORS[level]
        
        return self.ROLE_INDICATORS.get(entry_type, '❓')
    
    def format_log_entry(self, entry: Dict[str, Any], 
                        include_metadata: bool = False) -> str:
        """
        Format a log entry for display.
        
        Args:
            entry: Parsed log entry
            include_metadata: Whether to include metadata in output
            
        Returns:
            Formatted string for display
        """
        if not entry:
            return ""
        
        # Extract components
        timestamp = self.format_timestamp(entry.get('timestamp', ''))
        role = self.get_role_indicator(entry)
        entry_type = entry.get('type', 'unknown')
        content = self.extract_content(entry)
        content = self.truncate_content(content)
        
        # Get color for entry type
        color = ""
        reset = ""
        if self.color_enabled:
            color = self.COLORS.get(entry_type, '')
            reset = self.COLORS['reset']
        
        # Build formatted string
        parts = [
            f"{self.COLORS['dim'] if self.color_enabled else ''}{timestamp}{reset}",
            role,
            f"{color}{content}{reset}"
        ]
        
        # Add metadata if requested
        if include_metadata:
            uuid = entry.get('uuid', '')
            if uuid:
                agent_color = self.get_agent_color(uuid)
                uuid_suffix = uuid[-8:] if len(uuid) >= 8 else uuid
                parts.append(f"{agent_color}[{uuid_suffix}]{reset}")
        
        return " ".join(parts)
    
    def parse_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Parse an entire JSONL file.
        
        Args:
            file_path: Path to JSONL file
            
        Returns:
            List of parsed entries
        """
        entries = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            return entries
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    entry = self.parse_jsonl_line(line)
                    if entry:
                        # Add parsing metadata
                        entry['_line_number'] = line_num
                        entry['_file_path'] = str(file_path)
                        entries.append(entry)
        except Exception as e:
            # Return what we parsed so far
            pass
        
        return entries
    
    def stream_file(self, file_path: Union[str, Path], 
                   start_position: int = 0):
        """
        Generator to stream parse a file from a given position.
        
        Args:
            file_path: Path to JSONL file
            start_position: Byte position to start from
            
        Yields:
            Parsed log entries with file position
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if start_position > 0:
                    f.seek(start_position)
                
                while True:
                    position = f.tell()
                    line = f.readline()
                    
                    if not line:
                        break
                    
                    entry = self.parse_jsonl_line(line)
                    if entry:
                        entry['_file_position'] = position
                        entry['_file_path'] = str(file_path)
                        yield entry
        except Exception:
            # Stop iteration on error
            return


class LogFormatter:
    """Advanced formatting utilities for log display."""
    
    def __init__(self, parser: Optional[LogParser] = None):
        """
        Initialize the LogFormatter.
        
        Args:
            parser: LogParser instance to use
        """
        self.parser = parser or LogParser()
    
    def format_conversation_thread(self, entries: List[Dict[str, Any]], 
                                  indent_size: int = 2) -> str:
        """
        Format entries as a conversation thread with indentation.
        
        Args:
            entries: List of log entries
            indent_size: Spaces per indent level
            
        Returns:
            Formatted conversation string
        """
        # Build parent-child relationships
        tree = {}
        roots = []
        
        for entry in entries:
            uuid = entry.get('uuid')
            parent = entry.get('parentUuid')
            
            if not uuid:
                continue
            
            if parent:
                tree.setdefault(parent, []).append(entry)
            else:
                roots.append(entry)
        
        # Format recursively
        lines = []
        
        def format_node(entry, level=0):
            indent = ' ' * (level * indent_size)
            formatted = self.parser.format_log_entry(entry)
            lines.append(f"{indent}{formatted}")
            
            # Process children
            children = tree.get(entry.get('uuid'), [])
            for child in children:
                format_node(child, level + 1)
        
        for root in roots:
            format_node(root)
        
        return '\n'.join(lines)
    
    def format_summary(self, entries: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of log entries.
        
        Args:
            entries: List of log entries
            
        Returns:
            Summary string
        """
        type_counts = {}
        tool_counts = {}
        
        for entry in entries:
            entry_type = entry.get('type', 'unknown')
            type_counts[entry_type] = type_counts.get(entry_type, 0) + 1
            
            # Count tool usage
            if entry_type == 'assistant':
                message = entry.get('message', {})
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if item.get('type') == 'tool_use':
                            tool_name = item.get('name', 'unknown')
                            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        # Build summary
        lines = ["=== Log Summary ==="]
        lines.append(f"Total Entries: {len(entries)}")
        lines.append("\nEntry Types:")
        for entry_type, count in sorted(type_counts.items()):
            indicator = self.parser.ROLE_INDICATORS.get(entry_type, '❓')
            lines.append(f"  {indicator} {entry_type}: {count}")
        
        if tool_counts:
            lines.append("\nTool Usage:")
            for tool, count in sorted(tool_counts.items(), 
                                     key=lambda x: x[1], reverse=True):
                lines.append(f"  🔧 {tool}: {count}")
        
        return '\n'.join(lines)


# Convenience functions
def format_log_entry(entry: Dict[str, Any], 
                    color_enabled: bool = True,
                    truncate_enabled: bool = True,
                    include_metadata: bool = False) -> str:
    """
    Convenience function to format a single log entry.
    
    Args:
        entry: Parsed log entry
        color_enabled: Whether to include ANSI colors
        truncate_enabled: Whether to truncate content
        include_metadata: Whether to include metadata
        
    Returns:
        Formatted string
    """
    parser = LogParser(color_enabled=color_enabled, 
                      truncate_enabled=truncate_enabled)
    return parser.format_log_entry(entry, include_metadata=include_metadata)


def parse_jsonl_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Convenience function to parse a JSONL file.
    
    Args:
        file_path: Path to JSONL file
        
    Returns:
        List of parsed entries
    """
    parser = LogParser()
    return parser.parse_file(file_path)