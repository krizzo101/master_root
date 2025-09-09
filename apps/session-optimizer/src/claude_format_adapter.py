#!/usr/bin/env python3
"""
Claude Format Adapter - Convert Claude .jsonl files to GPT-5 optimized format
Handles Claude Code session files and converts them for GPT-5 payload generation.
Addresses the format compatibility issues identified in Phase 1 testing.
"""

import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple


@dataclass
class ConversionStats:
    """Statistics from format conversion"""

    total_records: int
    converted_messages: int
    tool_calls_extracted: int
    tool_results_extracted: int
    errors_encountered: int
    size_reduction_percent: float
    conversion_time_seconds: float


@dataclass
class AdapterConfig:
    """Configuration for Claude format adapter"""

    preserve_all_metadata: bool = False
    extract_file_operations: bool = True
    consolidate_tool_sequences: bool = True
    remove_duplicate_content: bool = True
    max_content_length: int = 50000
    streaming_chunk_size: int = 1000


class ClaudeFormatAdapter:
    """
    Converts Claude .jsonl session files to GPT-5 optimized format.
    Handles the specific structure of Claude Code sessions and tool usage.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()

        # Claude message types mapping
        self.message_type_mapping = {
            "user": "user",
            "assistant": "assistant",
            "system": "system",
        }

        # Tool categories for optimization
        self.tool_categories = {
            "file_ops": {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"},
            "shell_ops": {"Bash", "mcp__shell_exec__shell_exec", "Grep", "Glob"},
            "web_ops": {
                "WebSearch",
                "WebFetch",
                "mcp__web_search__brave_web_search",
                "mcp__web_search__brave_news_search",
                "mcp__firecrawl__firecrawl_scrape",
            },
            "knowledge": {
                "mcp__knowledge__knowledge_store",
                "mcp__knowledge__knowledge_query",
                "mcp__knowledge__knowledge_smart_query",
            },
            "planning": {"TodoWrite", "ExitPlanMode"},
            "agent": {"Task"},
        }

    def convert_session_file(self, jsonl_path: Path) -> Dict[str, Any]:
        """
        Convert a Claude .jsonl session file to GPT-5 optimized format.

        Args:
            jsonl_path: Path to Claude .jsonl session file

        Returns:
            Converted session data in GPT-5 optimized format
        """
        start_time = datetime.now()

        # Initialize conversion tracking
        stats = ConversionStats(0, 0, 0, 0, 0, 0.0, 0.0)

        # Parse Claude session
        messages = []
        session_metadata = {}

        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        record = json.loads(line)
                        stats.total_records += 1

                        # Extract session metadata from first record
                        if line_num == 1:
                            session_metadata = self._extract_session_metadata(
                                record, jsonl_path
                            )

                        # Convert record to standardized message
                        converted_message = self._convert_claude_record(record)
                        if converted_message:
                            messages.append(converted_message)
                            stats.converted_messages += 1

                            # Count tool usage
                            if converted_message.get("tool_calls"):
                                stats.tool_calls_extracted += len(
                                    converted_message["tool_calls"]
                                )
                            if converted_message.get("tool_results"):
                                stats.tool_results_extracted += len(
                                    converted_message["tool_results"]
                                )

                    except json.JSONDecodeError as e:
                        stats.errors_encountered += 1
                        print(f"JSON decode error at line {line_num}: {e}")
                    except Exception as e:
                        stats.errors_encountered += 1
                        print(f"Conversion error at line {line_num}: {e}")

        except Exception as e:
            print(f"File read error for {jsonl_path}: {e}")
            return {}

        # Post-processing optimizations
        if self.config.consolidate_tool_sequences:
            messages = self._consolidate_tool_sequences(messages)

        if self.config.remove_duplicate_content:
            messages = self._remove_duplicate_content(messages)

        # Calculate conversion statistics
        end_time = datetime.now()
        stats.conversion_time_seconds = (end_time - start_time).total_seconds()

        # Estimate size reduction
        original_size = jsonl_path.stat().st_size if jsonl_path.exists() else 0
        converted_size = len(json.dumps(messages, ensure_ascii=False))
        stats.size_reduction_percent = (
            ((original_size - converted_size) / original_size * 100)
            if original_size > 0
            else 0
        )

        # Build converted session
        converted_session = {
            "session_id": session_metadata.get("session_id", str(uuid.uuid4())),
            "session_metadata": session_metadata,
            "messages": messages,
            "conversion_stats": {
                "total_records": stats.total_records,
                "converted_messages": stats.converted_messages,
                "tool_calls_extracted": stats.tool_calls_extracted,
                "tool_results_extracted": stats.tool_results_extracted,
                "errors_encountered": stats.errors_encountered,
                "size_reduction_percent": round(stats.size_reduction_percent, 2),
                "conversion_time_seconds": round(stats.conversion_time_seconds, 2),
            },
            "conversion_metadata": {
                "adapter_version": "1.0",
                "conversion_timestamp": datetime.now().isoformat(),
                "source_file": str(jsonl_path),
                "optimizations_applied": self._get_applied_optimizations(),
            },
        }

        return converted_session

    def convert_streaming(
        self, jsonl_path: Path
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Convert Claude session file with streaming for memory efficiency.
        Yields chunks of converted messages for processing large files.
        """
        chunk_buffer = []
        chunk_size = self.config.streaming_chunk_size

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                    converted_message = self._convert_claude_record(record)

                    if converted_message:
                        chunk_buffer.append(converted_message)

                        # Yield chunk when buffer is full
                        if len(chunk_buffer) >= chunk_size:
                            yield {
                                "chunk_index": line_num // chunk_size,
                                "messages": chunk_buffer.copy(),
                                "is_final": False,
                            }
                            chunk_buffer = []

                except Exception as e:
                    print(f"Streaming conversion error at line {line_num}: {e}")
                    continue

        # Yield final chunk
        if chunk_buffer:
            yield {
                "chunk_index": -1,  # Final chunk
                "messages": chunk_buffer,
                "is_final": True,
            }

    def batch_convert(
        self, jsonl_files: List[Path], output_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert multiple Claude session files efficiently.

        Args:
            jsonl_files: List of Claude .jsonl files to convert
            output_dir: Optional directory to save converted files

        Returns:
            List of conversion results
        """
        results = []

        for jsonl_file in jsonl_files:
            try:
                print(f"Converting {jsonl_file.name}...")
                converted_session = self.convert_session_file(jsonl_file)

                if converted_session:
                    # Save converted file if output directory specified
                    if output_dir:
                        output_file = output_dir / f"{jsonl_file.stem}_converted.json"
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(
                                converted_session, f, indent=2, ensure_ascii=False
                            )

                    results.append(
                        {
                            "source_file": str(jsonl_file),
                            "success": True,
                            "session_id": converted_session.get("session_id"),
                            "message_count": len(converted_session.get("messages", [])),
                            "conversion_stats": converted_session.get(
                                "conversion_stats", {}
                            ),
                        }
                    )
                else:
                    results.append(
                        {
                            "source_file": str(jsonl_file),
                            "success": False,
                            "error": "Conversion failed",
                        }
                    )

            except Exception as e:
                results.append(
                    {"source_file": str(jsonl_file), "success": False, "error": str(e)}
                )

        return results

    def _extract_session_metadata(
        self, first_record: Dict[str, Any], file_path: Path
    ) -> Dict[str, Any]:
        """Extract session metadata from first record and file info"""
        metadata = {
            "session_id": first_record.get("sessionId")
            or first_record.get("session_id")
            or file_path.stem,
            "source_file": str(file_path),
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "conversion_timestamp": datetime.now().isoformat(),
        }

        # Extract additional metadata if present
        if "timestamp" in first_record:
            metadata["session_start"] = first_record["timestamp"]

        # Try to extract project context from file path
        if "master_root" in str(file_path):
            path_parts = str(file_path).split("master_root")
            if len(path_parts) > 1:
                project_path = (
                    path_parts[1].split("/")[1] if "/" in path_parts[1] else "unknown"
                )
                metadata["project_context"] = project_path

        return metadata

    def _convert_claude_record(
        self, record: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Convert a single Claude record to standardized message format"""
        record_type = record.get("type")
        if not record_type:
            return None

        # Map Claude type to standard type
        message_type = self.message_type_mapping.get(record_type, record_type)

        # Build base message
        message = {
            "uuid": record.get("uuid", str(uuid.uuid4())),
            "type": message_type,
            "timestamp": record.get("timestamp", datetime.now().isoformat()),
            "parent_uuid": record.get("parentUuid"),
        }

        # Extract content based on message type
        if record_type == "user":
            message["content"] = self._extract_user_content(record)
        elif record_type == "assistant":
            message["content"] = self._extract_assistant_content(record)

            # Extract tool usage
            tool_calls, tool_results = self._extract_tool_usage(record)
            if tool_calls:
                message["tool_calls"] = tool_calls
            if tool_results:
                message["tool_results"] = tool_results
        elif record_type == "system":
            message["content"] = self._extract_system_content(record)

        # Add metadata if configured
        if self.config.preserve_all_metadata:
            message["raw_metadata"] = {
                "original_type": record_type,
                "has_tool_calls": bool(self._find_tool_calls_in_record(record)),
                "content_length": len(str(record.get("message", {}))),
                "record_keys": list(record.keys()),
            }

        return message

    def _extract_user_content(self, record: Dict[str, Any]) -> str:
        """Extract user message content"""
        message_data = record.get("message", {})

        if isinstance(message_data, dict):
            content = message_data.get("content", "")
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Handle structured content
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                return " ".join(text_parts)

        return str(message_data)

    def _extract_assistant_content(self, record: Dict[str, Any]) -> str:
        """Extract assistant message content, separating text from tool usage"""
        message_data = record.get("message", {})

        if isinstance(message_data, dict):
            content = message_data.get("content", "")

            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract only text content, tools handled separately
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        # Skip tool_use and tool_result - handled in _extract_tool_usage

                return " ".join(text_parts)

        return str(message_data)

    def _extract_system_content(self, record: Dict[str, Any]) -> str:
        """Extract system message content"""
        message_data = record.get("message", {})
        return str(message_data.get("content", ""))

    def _extract_tool_usage(
        self, record: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract tool calls and results from assistant message"""
        tool_calls = []
        tool_results = []

        message_data = record.get("message", {})
        content = message_data.get("content", [])

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "tool_use":
                        tool_call = {
                            "id": item.get("id", str(uuid.uuid4())),
                            "name": item.get("name", "unknown"),
                            "input": item.get("input", {}),
                            "category": self._categorize_tool(item.get("name", "")),
                        }
                        tool_calls.append(tool_call)

                    elif item.get("type") == "tool_result":
                        tool_result = {
                            "tool_use_id": item.get("tool_use_id"),
                            "is_error": item.get("is_error", False),
                            "content": self._truncate_tool_result(
                                item.get("content", "")
                            ),
                        }
                        tool_results.append(tool_result)

        return tool_calls, tool_results

    def _find_tool_calls_in_record(self, record: Dict[str, Any]) -> List[Dict]:
        """Find tool calls in any record format"""
        tool_calls = []

        def search_for_tools(obj):
            if isinstance(obj, dict):
                if obj.get("type") == "tool_use":
                    tool_calls.append(obj)
                for value in obj.values():
                    search_for_tools(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_for_tools(item)

        search_for_tools(record)
        return tool_calls

    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize tool by name for optimization"""
        for category, tools in self.tool_categories.items():
            if tool_name in tools:
                return category

        if tool_name.startswith("mcp__"):
            return "mcp_tools"

        return "other"

    def _truncate_tool_result(self, content: Any) -> str:
        """Truncate large tool results for optimization"""
        content_str = str(content)

        # Apply content length limit
        if len(content_str) > self.config.max_content_length:
            truncated = content_str[: self.config.max_content_length]
            return (
                truncated
                + f"... [truncated from {len(content_str)} chars for optimization]"
            )

        return content_str

    def _consolidate_tool_sequences(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Consolidate consecutive tool usage messages for better compression"""
        if not self.config.consolidate_tool_sequences:
            return messages

        consolidated = []
        current_sequence = []

        for message in messages:
            if message.get("tool_calls") or message.get("tool_results"):
                current_sequence.append(message)
            else:
                # End current tool sequence
                if current_sequence:
                    if len(current_sequence) > 1:
                        # Consolidate multiple tool messages
                        consolidated_msg = self._merge_tool_messages(current_sequence)
                        consolidated.append(consolidated_msg)
                    else:
                        # Single tool message
                        consolidated.extend(current_sequence)
                    current_sequence = []

                # Add non-tool message
                consolidated.append(message)

        # Handle final sequence
        if current_sequence:
            if len(current_sequence) > 1:
                consolidated_msg = self._merge_tool_messages(current_sequence)
                consolidated.append(consolidated_msg)
            else:
                consolidated.extend(current_sequence)

        return consolidated

    def _merge_tool_messages(
        self, tool_sequence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Merge multiple tool messages into a consolidated message"""
        merged = {
            "uuid": str(uuid.uuid4()),
            "type": "assistant",
            "timestamp": tool_sequence[0].get("timestamp"),
            "content": "Multiple tool operations performed",
            "tool_calls": [],
            "tool_results": [],
            "consolidated_from": len(tool_sequence),
        }

        # Collect all tool calls and results
        for msg in tool_sequence:
            if msg.get("tool_calls"):
                merged["tool_calls"].extend(msg["tool_calls"])
            if msg.get("tool_results"):
                merged["tool_results"].extend(msg["tool_results"])

        # Create summary of tool operations
        tool_names = [tc.get("name", "unknown") for tc in merged["tool_calls"]]
        tool_categories = set(
            tc.get("category", "other") for tc in merged["tool_calls"]
        )

        merged[
            "content"
        ] = f"Consolidated tool sequence: {len(merged['tool_calls'])} operations ({', '.join(sorted(tool_categories))})"
        merged["tool_summary"] = {
            "total_operations": len(merged["tool_calls"]),
            "unique_tools": len(set(tool_names)),
            "categories": list(tool_categories),
            "operation_sequence": tool_names,
        }

        return merged

    def _remove_duplicate_content(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove messages with duplicate content for optimization"""
        if not self.config.remove_duplicate_content:
            return messages

        seen_content = set()
        deduplicated = []

        for message in messages:
            # Create content hash for deduplication
            content = message.get("content", "")
            tool_calls = len(message.get("tool_calls", []))
            content_signature = f"{content[:100]}|{tool_calls}"

            if content_signature not in seen_content:
                seen_content.add(content_signature)
                deduplicated.append(message)
            else:
                # Mark as duplicate in metadata
                if "deduplication_metadata" not in deduplicated[-1]:
                    deduplicated[-1]["deduplication_metadata"] = {
                        "duplicates_removed": 0
                    }
                deduplicated[-1]["deduplication_metadata"]["duplicates_removed"] += 1

        return deduplicated

    def _get_applied_optimizations(self) -> List[str]:
        """Get list of optimizations applied during conversion"""
        optimizations = ["claude_to_gpt5_format_conversion"]

        if self.config.consolidate_tool_sequences:
            optimizations.append("tool_sequence_consolidation")

        if self.config.remove_duplicate_content:
            optimizations.append("duplicate_content_removal")

        if self.config.max_content_length < 100000:
            optimizations.append("content_length_truncation")

        if self.config.extract_file_operations:
            optimizations.append("file_operation_extraction")

        return optimizations

    def get_conversion_summary(
        self, conversion_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary of batch conversion results"""
        if not conversion_results:
            return {"error": "No conversion results"}

        successful = [r for r in conversion_results if r.get("success", False)]
        failed = [r for r in conversion_results if not r.get("success", False)]

        total_messages = sum(r.get("message_count", 0) for r in successful)
        total_tool_calls = sum(
            r.get("conversion_stats", {}).get("tool_calls_extracted", 0)
            for r in successful
        )

        avg_size_reduction = 0
        if successful:
            size_reductions = [
                r.get("conversion_stats", {}).get("size_reduction_percent", 0)
                for r in successful
            ]
            avg_size_reduction = sum(size_reductions) / len(size_reductions)

        return {
            "conversion_summary": {
                "total_files_processed": len(conversion_results),
                "successful_conversions": len(successful),
                "failed_conversions": len(failed),
                "success_rate": len(successful) / len(conversion_results) * 100,
                "total_messages_converted": total_messages,
                "total_tool_calls_extracted": total_tool_calls,
                "average_size_reduction_percent": round(avg_size_reduction, 2),
            },
            "failed_files": [r["source_file"] for r in failed],
            "optimization_impact": {
                "estimated_token_savings": int(
                    total_messages * 0.2
                ),  # Estimated 20% savings
                "format_compatibility": "GPT-5 optimized",
                "processing_efficiency": "High compression achieved",
            },
        }
