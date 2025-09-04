#!/usr/bin/env python3
"""
Chat Log Analysis Script for Unified Context System

Analyzes existing Claude chat logs to prepare them for import into the unified context database.
Provides detailed metrics, prioritization, and import strategy recommendations.
"""

import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, "/home/opsvi/master_root/apps/project-context")

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available, using basic analysis only")


class ChatLogAnalyzer:
    """Comprehensive analysis of Claude chat logs for import planning."""

    def __init__(self, base_path: str = "/home/opsvi/.claude/projects"):
        """Initialize analyzer with base path to chat logs."""
        self.base_path = Path(base_path)
        self.results = {
            "total_files": 0,
            "total_messages": 0,
            "total_size_bytes": 0,
            "date_range": {"earliest": None, "latest": None},
            "file_analysis": [],
            "session_analysis": {},
            "content_types": defaultdict(int),
            "actor_types": defaultdict(int),
            "problematic_files": [],
            "import_recommendations": {},
            "processing_estimates": {},
        }

    def analyze_all_files(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of all JSONL chat files."""
        print("🔍 Starting comprehensive chat log analysis...")

        # Find all JSONL files
        jsonl_files = list(self.base_path.glob("**/*.jsonl"))
        self.results["total_files"] = len(jsonl_files)

        print(f"📁 Found {len(jsonl_files)} JSONL files to analyze")

        # Analyze each file
        for i, file_path in enumerate(jsonl_files):
            if i % 100 == 0:
                print(f"📊 Analyzing file {i+1}/{len(jsonl_files)}: {file_path.name}")

            file_analysis = self._analyze_single_file(file_path)
            if file_analysis:
                self.results["file_analysis"].append(file_analysis)

        # Generate comprehensive analysis
        self._generate_summary_statistics()
        self._analyze_sessions()
        self._generate_import_strategy()
        self._estimate_processing_requirements()

        return self.results

    def _analyze_single_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single JSONL chat file."""
        try:
            file_stats = file_path.stat()
            file_info = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size_bytes": file_stats.st_size,
                "modification_time": datetime.fromtimestamp(file_stats.st_mtime),
                "message_count": 0,
                "session_id": None,
                "date_range": {"earliest": None, "latest": None},
                "actor_types": defaultdict(int),
                "message_types": defaultdict(int),
                "content_stats": {
                    "total_chars": 0,
                    "avg_message_length": 0,
                    "has_code": False,
                    "has_tools": False,
                    "has_errors": False,
                },
                "estimated_processing_time_seconds": 0,
                "priority_score": 0.0,
                "issues": [],
            }

            # Extract session ID from filename (UUID pattern)
            uuid_match = re.search(
                r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
                file_path.name,
            )
            if uuid_match:
                file_info["session_id"] = uuid_match.group(1)

            # Read and analyze messages
            with open(file_path, "r", encoding="utf-8") as f:
                total_content_chars = 0

                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        message = json.loads(line)
                        file_info["message_count"] += 1

                        # Extract timestamp
                        timestamp = self._extract_timestamp(message)
                        if timestamp:
                            if (
                                not file_info["date_range"]["earliest"]
                                or timestamp < file_info["date_range"]["earliest"]
                            ):
                                file_info["date_range"]["earliest"] = timestamp
                            if (
                                not file_info["date_range"]["latest"]
                                or timestamp > file_info["date_range"]["latest"]
                            ):
                                file_info["date_range"]["latest"] = timestamp

                        # Analyze message content
                        content = self._extract_content(message)
                        if content:
                            content_len = len(content)
                            total_content_chars += content_len

                            # Content analysis
                            if re.search(
                                r"```|`[^`]+`|def |class |function|import ",
                                content,
                                re.IGNORECASE,
                            ):
                                file_info["content_stats"]["has_code"] = True

                            if "tool_use" in str(message) or "tool_result" in str(
                                message
                            ):
                                file_info["content_stats"]["has_tools"] = True

                            if re.search(
                                r"error|exception|failed|traceback",
                                content,
                                re.IGNORECASE,
                            ):
                                file_info["content_stats"]["has_errors"] = True

                        # Actor type analysis
                        actor_type = self._determine_actor_type(message)
                        file_info["actor_types"][actor_type] += 1

                        # Message type analysis
                        msg_type = message.get("type", "unknown")
                        file_info["message_types"][msg_type] += 1

                    except json.JSONDecodeError as e:
                        file_info["issues"].append(
                            f"JSON decode error on line {line_num}: {str(e)}"
                        )

                    except Exception as e:
                        file_info["issues"].append(
                            f"Processing error on line {line_num}: {str(e)}"
                        )

                # Calculate averages and scores
                if file_info["message_count"] > 0:
                    file_info["content_stats"]["total_chars"] = total_content_chars
                    file_info["content_stats"]["avg_message_length"] = (
                        total_content_chars / file_info["message_count"]
                    )

                # Calculate priority score (0-1, higher is better)
                file_info["priority_score"] = self._calculate_priority_score(file_info)

                # Estimate processing time (rough estimate based on file size and message count)
                file_info[
                    "estimated_processing_time_seconds"
                ] = self._estimate_processing_time(file_info)

                self.results["total_messages"] += file_info["message_count"]
                self.results["total_size_bytes"] += file_info["file_size_bytes"]

                return file_info

        except Exception as e:
            error_info = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "error": str(e),
                "file_size_bytes": file_path.stat().st_size
                if file_path.exists()
                else 0,
                "issues": [f"Failed to analyze file: {str(e)}"],
            }
            self.results["problematic_files"].append(error_info)
            return None

    def _extract_timestamp(self, message: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from message."""
        timestamp_fields = ["timestamp", "created_at", "time", "date"]

        for field in timestamp_fields:
            if field in message:
                try:
                    value = message[field]
                    if isinstance(value, str):
                        # Handle ISO format with Z suffix
                        if value.endswith("Z"):
                            value = value[:-1] + "+00:00"
                        return datetime.fromisoformat(value)
                    elif isinstance(value, (int, float)):
                        return datetime.fromtimestamp(value)
                except (ValueError, TypeError):
                    continue
        return None

    def _extract_content(self, message: Dict[str, Any]) -> str:
        """Extract content from message."""
        # Handle different message structures
        if "message" in message and isinstance(message["message"], dict):
            msg = message["message"]
            if "content" in msg:
                if isinstance(msg["content"], str):
                    return msg["content"]
                elif isinstance(msg["content"], list):
                    # Extract text from content array
                    texts = []
                    for item in msg["content"]:
                        if isinstance(item, dict) and item.get("type") == "text":
                            texts.append(item.get("text", ""))
                    return " ".join(texts)

        # Direct content fields
        for field in ["content", "text", "body"]:
            if field in message and isinstance(message[field], str):
                return message[field]

        return ""

    def _determine_actor_type(self, message: Dict[str, Any]) -> str:
        """Determine if message is from human, AI, or system."""
        # Check message structure
        if "message" in message and isinstance(message["message"], dict):
            role = message["message"].get("role", "")
            if role in ["assistant", "ai"]:
                return "ai"
            elif role in ["user", "human"]:
                return "human"
            elif role == "system":
                return "system"

        # Check message type
        msg_type = message.get("type", "")
        if msg_type == "assistant":
            return "ai"
        elif msg_type == "user":
            return "human"
        elif msg_type == "system":
            return "system"

        # Check for model field (indicates AI message)
        if "message" in message and message["message"].get("model"):
            return "ai"

        return "unknown"

    def _calculate_priority_score(self, file_info: Dict[str, Any]) -> float:
        """Calculate priority score for import (0-1, higher is better)."""
        score = 0.0

        # Recency score (0-0.3)
        if file_info["date_range"]["latest"]:
            days_old = (datetime.now() - file_info["date_range"]["latest"]).days
            if days_old < 7:
                score += 0.3
            elif days_old < 30:
                score += 0.2
            elif days_old < 90:
                score += 0.1

        # Size score (0-0.2) - larger files generally have more content
        if file_info["message_count"] > 100:
            score += 0.2
        elif file_info["message_count"] > 50:
            score += 0.15
        elif file_info["message_count"] > 10:
            score += 0.1

        # Content quality score (0-0.3)
        if file_info["content_stats"]["has_code"]:
            score += 0.15
        if file_info["content_stats"]["has_tools"]:
            score += 0.1
        if file_info["content_stats"]["avg_message_length"] > 200:
            score += 0.05

        # Interaction quality score (0-0.2)
        total_messages = file_info["message_count"]
        if total_messages > 0:
            ai_ratio = file_info["actor_types"]["ai"] / total_messages
            human_ratio = file_info["actor_types"]["human"] / total_messages
            # Good conversations have balanced interaction
            interaction_balance = 1 - abs(ai_ratio - human_ratio)
            score += 0.2 * interaction_balance

        return min(1.0, score)

    def _estimate_processing_time(self, file_info: Dict[str, Any]) -> float:
        """Estimate processing time in seconds."""
        # Base time per message (includes parsing, entity extraction, embedding generation)
        base_time_per_message = 0.5  # seconds

        # Additional time for complex content
        complexity_multiplier = 1.0
        if file_info["content_stats"]["has_code"]:
            complexity_multiplier += 0.3
        if file_info["content_stats"]["has_tools"]:
            complexity_multiplier += 0.2
        if file_info["content_stats"]["avg_message_length"] > 1000:
            complexity_multiplier += 0.5

        return (
            file_info["message_count"] * base_time_per_message * complexity_multiplier
        )

    def _generate_summary_statistics(self):
        """Generate summary statistics from file analysis."""
        if not self.results["file_analysis"]:
            return

        # Calculate global date range
        earliest_dates = []
        latest_dates = []

        for file_info in self.results["file_analysis"]:
            if file_info["date_range"]["earliest"]:
                earliest_dates.append(file_info["date_range"]["earliest"])
            if file_info["date_range"]["latest"]:
                latest_dates.append(file_info["date_range"]["latest"])

        if earliest_dates:
            self.results["date_range"]["earliest"] = min(earliest_dates)
        if latest_dates:
            self.results["date_range"]["latest"] = max(latest_dates)

        # Aggregate content types
        for file_info in self.results["file_analysis"]:
            for actor_type, count in file_info["actor_types"].items():
                self.results["actor_types"][actor_type] += count

    def _analyze_sessions(self):
        """Analyze sessions and conversation patterns."""
        sessions = defaultdict(list)

        # Group files by session ID
        for file_info in self.results["file_analysis"]:
            session_id = file_info.get("session_id")
            if session_id:
                sessions[session_id].append(file_info)

        # Analyze each session
        for session_id, files in sessions.items():
            session_info = {
                "session_id": session_id,
                "file_count": len(files),
                "total_messages": sum(f["message_count"] for f in files),
                "total_size_bytes": sum(f["file_size_bytes"] for f in files),
                "date_range": {
                    "earliest": min(
                        f["date_range"]["earliest"]
                        for f in files
                        if f["date_range"]["earliest"]
                    ),
                    "latest": max(
                        f["date_range"]["latest"]
                        for f in files
                        if f["date_range"]["latest"]
                    ),
                },
                "priority_score": max(f["priority_score"] for f in files),
                "estimated_processing_time": sum(
                    f["estimated_processing_time_seconds"] for f in files
                ),
                "has_code": any(f["content_stats"]["has_code"] for f in files),
                "has_tools": any(f["content_stats"]["has_tools"] for f in files),
                "has_errors": any(f["content_stats"]["has_errors"] for f in files),
            }

            self.results["session_analysis"][session_id] = session_info

    def _generate_import_strategy(self):
        """Generate import strategy with prioritization and batching recommendations."""
        files = self.results["file_analysis"]

        if not files:
            return

        # Sort files by priority score (descending)
        sorted_files = sorted(files, key=lambda x: x["priority_score"], reverse=True)

        # Categorize files
        high_priority = [f for f in sorted_files if f["priority_score"] >= 0.7]
        medium_priority = [f for f in sorted_files if 0.4 <= f["priority_score"] < 0.7]
        low_priority = [f for f in sorted_files if f["priority_score"] < 0.4]

        # Generate batch recommendations
        batch_size_bytes = 50 * 1024 * 1024  # 50MB batches
        batch_size_messages = 10000  # 10k messages per batch

        batches = []
        current_batch = []
        current_size = 0
        current_messages = 0

        for file_info in sorted_files:
            if (
                current_size + file_info["file_size_bytes"] > batch_size_bytes
                or current_messages + file_info["message_count"] > batch_size_messages
            ) and current_batch:
                batches.append(
                    {
                        "batch_id": len(batches) + 1,
                        "files": current_batch.copy(),
                        "total_size_bytes": current_size,
                        "total_messages": current_messages,
                        "estimated_processing_time": sum(
                            f["estimated_processing_time_seconds"]
                            for f in current_batch
                        ),
                    }
                )

                current_batch = []
                current_size = 0
                current_messages = 0

            current_batch.append(file_info)
            current_size += file_info["file_size_bytes"]
            current_messages += file_info["message_count"]

        # Add final batch
        if current_batch:
            batches.append(
                {
                    "batch_id": len(batches) + 1,
                    "files": current_batch,
                    "total_size_bytes": current_size,
                    "total_messages": current_messages,
                    "estimated_processing_time": sum(
                        f["estimated_processing_time_seconds"] for f in current_batch
                    ),
                }
            )

        self.results["import_recommendations"] = {
            "prioritization": {
                "high_priority_files": len(high_priority),
                "medium_priority_files": len(medium_priority),
                "low_priority_files": len(low_priority),
                "high_priority_sessions": len(
                    [
                        s
                        for s in self.results["session_analysis"].values()
                        if s["priority_score"] >= 0.7
                    ]
                ),
            },
            "batching": {
                "total_batches": len(batches),
                "recommended_batch_size_bytes": batch_size_bytes,
                "recommended_batch_size_messages": batch_size_messages,
                "batches": batches[:5],  # Show first 5 batches as examples
            },
            "import_order": [
                "Start with high-priority files (recent, code-heavy, interactive)",
                "Process medium-priority files in date order (newest first)",
                "Handle low-priority files in bulk processing mode",
                "Skip problematic files initially, review manually",
            ],
        }

    def _estimate_processing_requirements(self):
        """Estimate total processing requirements."""
        total_processing_time = sum(
            f["estimated_processing_time_seconds"]
            for f in self.results["file_analysis"]
        )

        # Parallel processing estimates (assuming 4 workers)
        parallel_workers = 4
        parallel_time = total_processing_time / parallel_workers

        # Memory estimates (rough)
        avg_message_size = self.results["total_size_bytes"] / max(
            self.results["total_messages"], 1
        )
        batch_memory_mb = (10000 * avg_message_size) / (
            1024 * 1024
        )  # 10k message batch

        self.results["processing_estimates"] = {
            "total_processing_time_seconds": total_processing_time,
            "total_processing_time_hours": total_processing_time / 3600,
            "parallel_processing_time_hours": parallel_time / 3600,
            "recommended_workers": parallel_workers,
            "estimated_batch_memory_mb": batch_memory_mb,
            "recommended_system_memory_gb": max(
                4, batch_memory_mb * parallel_workers / 1024
            ),
            "disk_space_required_gb": (self.results["total_size_bytes"] * 1.5)
            / (1024**3),  # 1.5x for processing overhead
        }

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive analysis report."""
        report_lines = [
            "# Claude Chat Log Analysis Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary Statistics",
            f"- **Total Files**: {self.results['total_files']:,}",
            f"- **Total Messages**: {self.results['total_messages']:,}",
            f"- **Total Size**: {self.results['total_size_bytes'] / (1024**3):.2f} GB",
            f"- **Problematic Files**: {len(self.results['problematic_files'])}",
            "",
        ]

        # Date range
        if (
            self.results["date_range"]["earliest"]
            and self.results["date_range"]["latest"]
        ):
            report_lines.extend(
                [
                    "## Date Range",
                    f"- **Earliest**: {self.results['date_range']['earliest'].isoformat()}",
                    f"- **Latest**: {self.results['date_range']['latest'].isoformat()}",
                    f"- **Span**: {(self.results['date_range']['latest'] - self.results['date_range']['earliest']).days} days",
                    "",
                ]
            )

        # Actor distribution
        if self.results["actor_types"]:
            report_lines.extend(
                [
                    "## Message Distribution by Actor Type",
                ]
            )
            for actor_type, count in self.results["actor_types"].items():
                percentage = (count / self.results["total_messages"]) * 100
                report_lines.append(
                    f"- **{actor_type}**: {count:,} ({percentage:.1f}%)"
                )
            report_lines.append("")

        # Session analysis
        if self.results["session_analysis"]:
            report_lines.extend(
                [
                    "## Session Analysis",
                    f"- **Total Sessions**: {len(self.results['session_analysis'])}",
                ]
            )

            # Top sessions by priority
            top_sessions = sorted(
                self.results["session_analysis"].values(),
                key=lambda x: x["priority_score"],
                reverse=True,
            )[:10]

            report_lines.extend(
                [
                    "",
                    "### Top 10 Sessions by Priority",
                    "| Session ID | Messages | Priority | Has Code | Has Tools |",
                    "|------------|----------|----------|----------|-----------|",
                ]
            )

            for session in top_sessions:
                session_id_short = session["session_id"][:8] + "..."
                report_lines.append(
                    f"| {session_id_short} | {session['total_messages']:,} | "
                    f"{session['priority_score']:.2f} | {'✓' if session['has_code'] else '✗'} | "
                    f"{'✓' if session['has_tools'] else '✗'} |"
                )

            report_lines.append("")

        # Processing estimates
        estimates = self.results["processing_estimates"]
        report_lines.extend(
            [
                "## Processing Estimates",
                f"- **Total Processing Time**: {estimates['total_processing_time_hours']:.1f} hours",
                f"- **Parallel Processing Time** ({estimates['recommended_workers']} workers): {estimates['parallel_processing_time_hours']:.1f} hours",
                f"- **Recommended System Memory**: {estimates['recommended_system_memory_gb']:.1f} GB",
                f"- **Disk Space Required**: {estimates['disk_space_required_gb']:.1f} GB",
                "",
            ]
        )

        # Import recommendations
        recs = self.results["import_recommendations"]
        if recs:
            report_lines.extend(
                [
                    "## Import Strategy Recommendations",
                    "",
                    "### Prioritization",
                    f"- **High Priority Files**: {recs['prioritization']['high_priority_files']} (recent, interactive, code-heavy)",
                    f"- **Medium Priority Files**: {recs['prioritization']['medium_priority_files']} (older but substantial)",
                    f"- **Low Priority Files**: {recs['prioritization']['low_priority_files']} (minimal content or very old)",
                    "",
                    "### Batching Strategy",
                    f"- **Total Batches**: {recs['batching']['total_batches']}",
                    f"- **Batch Size**: {recs['batching']['recommended_batch_size_messages']:,} messages or {recs['batching']['recommended_batch_size_bytes'] / (1024**2):.0f}MB",
                    "",
                    "### Import Order",
                ]
            )

            for i, step in enumerate(recs["import_order"], 1):
                report_lines.append(f"{i}. {step}")

            report_lines.append("")

        # Problematic files
        if self.results["problematic_files"]:
            report_lines.extend(
                [
                    "## Problematic Files",
                    f"Found {len(self.results['problematic_files'])} files with issues:",
                    "",
                ]
            )

            for pf in self.results["problematic_files"][:10]:  # Show first 10
                report_lines.append(
                    f"- `{pf['file_name']}`: {pf.get('error', 'Unknown error')}"
                )

            if len(self.results["problematic_files"]) > 10:
                report_lines.append(
                    f"- ... and {len(self.results['problematic_files']) - 10} more"
                )

            report_lines.append("")

        report = "\n".join(report_lines)

        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            print(f"📄 Report saved to: {output_file}")

        return report


def main():
    """Main execution function."""
    analyzer = ChatLogAnalyzer()

    print("🚀 Starting Claude Chat Log Analysis...")
    print(f"📂 Analyzing files in: {analyzer.base_path}")

    # Perform analysis
    results = analyzer.analyze_all_files()

    # Generate and save report
    report_file = (
        "/home/opsvi/master_root/apps/project-context/chat_import_analysis_report.md"
    )
    report = analyzer.generate_report(report_file)

    # Save detailed JSON results
    json_file = (
        "/home/opsvi/master_root/apps/project-context/chat_import_analysis_data.json"
    )

    # Convert datetime objects to strings for JSON serialization
    results_json = json.loads(json.dumps(results, default=str, indent=2))

    with open(json_file, "w") as f:
        json.dump(results_json, f, indent=2)

    print(f"📊 Detailed data saved to: {json_file}")
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("=" * 60)

    # Print summary
    print(f"📁 Analyzed {results['total_files']:,} files")
    print(f"💬 Found {results['total_messages']:,} messages")
    print(f"📦 Total size: {results['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"⚠️  Problematic files: {len(results['problematic_files'])}")

    if results["processing_estimates"]:
        est = results["processing_estimates"]
        print(
            f"⏱️  Estimated processing time: {est['parallel_processing_time_hours']:.1f} hours (with {est['recommended_workers']} workers)"
        )
        print(
            f"💾 Recommended system memory: {est['recommended_system_memory_gb']:.1f} GB"
        )

    print(f"\n📄 Full report: {report_file}")


if __name__ == "__main__":
    main()
