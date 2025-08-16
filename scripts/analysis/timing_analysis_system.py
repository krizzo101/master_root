#!/usr/bin/env python3
"""
Comprehensive Timing Analysis System for Multi-Token Recursive Spawning Tests

This system tracks discrete timestamps for every action with microsecond precision,
enabling deep analysis of parallelism, performance bottlenecks, and success rates.
"""

import json
import time
import uuid
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading
from collections import defaultdict
import sys
import os

# Add libs to path for MCP access
sys.path.insert(0, "/home/opsvi/master_root/libs")


class EventType(Enum):
    """Types of events we track in the timing system"""

    # MCP Tool Events
    MCP_INVOCATION_START = "mcp_invocation_start"
    MCP_INVOCATION_END = "mcp_invocation_end"

    # Batch Events
    BATCH_SUBMISSION = "batch_submission"
    BATCH_ACCEPTED = "batch_accepted"
    BATCH_COMPLETED = "batch_completed"
    BATCH_FAILED = "batch_failed"

    # Job Events
    JOB_CREATED = "job_created"
    JOB_QUEUED = "job_queued"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"

    # Token Events
    TOKEN_ASSIGNED = "token_assigned"
    TOKEN_RELEASED = "token_released"
    TOKEN_RATE_LIMITED = "token_rate_limited"

    # Subprocess Events
    SUBPROCESS_SPAWN = "subprocess_spawn"
    SUBPROCESS_STARTED = "subprocess_started"
    SUBPROCESS_COMPLETED = "subprocess_completed"
    SUBPROCESS_FAILED = "subprocess_failed"

    # File System Events
    FILE_CREATION_STARTED = "file_creation_started"
    FILE_CREATED = "file_created"
    FILE_WRITE_FAILED = "file_write_failed"

    # Task Events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Result Events
    RESULT_RETRIEVAL_START = "result_retrieval_start"
    RESULT_RETRIEVED = "result_retrieved"
    RESULT_RETRIEVAL_FAILED = "result_retrieval_failed"

    # System Events
    SYSTEM_INITIALIZED = "system_initialized"
    RECURSION_DEPTH_CHANGE = "recursion_depth_change"
    MEMORY_CHECKPOINT = "memory_checkpoint"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class TimingEvent:
    """A single timing event with microsecond precision"""

    timestamp: float  # Unix timestamp with microseconds
    event_type: EventType
    description: str
    tier: int  # 0 for system, 1 for Tier 1, 2 for Tier 2, etc.
    success: bool = True
    error_details: Optional[str] = None
    job_id: Optional[str] = None
    batch_id: Optional[str] = None
    parent_job_id: Optional[str] = None
    token_used: Optional[str] = None
    duration_ms: Optional[
        float
    ] = None  # Duration in milliseconds if this is an end event
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["event_type"] = self.event_type.value
        result["timestamp_readable"] = datetime.fromtimestamp(
            self.timestamp
        ).isoformat()
        return result

    @property
    def timestamp_us(self) -> int:
        """Get timestamp in microseconds"""
        return int(self.timestamp * 1_000_000)


class TimingAnalyzer:
    """Analyzes timing data and generates comprehensive reports"""

    def __init__(self, events: List[TimingEvent]):
        self.events = sorted(events, key=lambda e: e.timestamp)
        self.start_time = self.events[0].timestamp if events else 0
        self.end_time = self.events[-1].timestamp if events else 0

    def calculate_durations(self) -> Dict[str, Any]:
        """Calculate durations for paired start/end events"""
        durations = defaultdict(list)
        start_events = {}

        for event in self.events:
            # Track start events
            if "START" in event.event_type.name or "STARTED" in event.event_type.name:
                key = f"{event.job_id or event.batch_id}_{event.event_type.name}"
                start_events[key] = event

            # Match with end events
            elif any(
                end in event.event_type.name for end in ["END", "COMPLETED", "FAILED"]
            ):
                start_type = (
                    event.event_type.name.replace("_END", "_START")
                    .replace("_COMPLETED", "_STARTED")
                    .replace("_FAILED", "_STARTED")
                )
                key = f"{event.job_id or event.batch_id}_{start_type}"

                if key in start_events:
                    duration_ms = (event.timestamp - start_events[key].timestamp) * 1000
                    durations[event.event_type.value].append(
                        {
                            "duration_ms": duration_ms,
                            "job_id": event.job_id,
                            "batch_id": event.batch_id,
                            "tier": event.tier,
                            "success": event.success,
                        }
                    )

        return dict(durations)

    def verify_parallelism(self) -> Dict[str, Any]:
        """Verify if operations ran in parallel or sequentially"""
        parallel_analysis = {
            "tier_1_parallel": False,
            "tier_2_parallel": False,
            "tier_1_overlaps": [],
            "tier_2_overlaps": [],
            "max_concurrent_tier_1": 0,
            "max_concurrent_tier_2": 0,
        }

        # Group events by tier and job
        tier_jobs = defaultdict(list)
        for event in self.events:
            if event.job_id and event.tier > 0:
                tier_jobs[event.tier].append(event)

        # Analyze each tier
        for tier in [1, 2]:
            jobs = defaultdict(lambda: {"start": None, "end": None})

            for event in tier_jobs[tier]:
                if "STARTED" in event.event_type.name:
                    jobs[event.job_id]["start"] = event.timestamp
                elif (
                    "COMPLETED" in event.event_type.name
                    or "FAILED" in event.event_type.name
                ):
                    jobs[event.job_id]["end"] = event.timestamp

            # Check for overlaps
            job_list = [
                (jid, times["start"], times["end"])
                for jid, times in jobs.items()
                if times["start"] and times["end"]
            ]

            overlaps = []
            for i, (job1_id, start1, end1) in enumerate(job_list):
                for job2_id, start2, end2 in job_list[i + 1 :]:
                    # Check if jobs overlap
                    if start1 < end2 and start2 < end1:
                        overlap_start = max(start1, start2)
                        overlap_end = min(end1, end2)
                        overlap_duration = (overlap_end - overlap_start) * 1000
                        overlaps.append(
                            {
                                "job1": job1_id,
                                "job2": job2_id,
                                "overlap_ms": overlap_duration,
                            }
                        )

            # Calculate max concurrent
            if job_list:
                timeline_events = []
                for jid, start, end in job_list:
                    timeline_events.append((start, 1))  # Job starts
                    timeline_events.append((end, -1))  # Job ends

                timeline_events.sort()
                current_concurrent = 0
                max_concurrent = 0

                for _, delta in timeline_events:
                    current_concurrent += delta
                    max_concurrent = max(max_concurrent, current_concurrent)

                if tier == 1:
                    parallel_analysis["tier_1_overlaps"] = overlaps
                    parallel_analysis["tier_1_parallel"] = len(overlaps) > 0
                    parallel_analysis["max_concurrent_tier_1"] = max_concurrent
                else:
                    parallel_analysis["tier_2_overlaps"] = overlaps
                    parallel_analysis["tier_2_parallel"] = len(overlaps) > 0
                    parallel_analysis["max_concurrent_tier_2"] = max_concurrent

        return parallel_analysis

    def analyze_token_utilization(self) -> Dict[str, Any]:
        """Analyze how tokens were utilized"""
        token_analysis = {
            "tokens_used": set(),
            "token_assignments": defaultdict(list),
            "token_durations": defaultdict(list),
            "rate_limits_hit": [],
        }

        token_starts = {}

        for event in self.events:
            if event.token_used:
                token_analysis["tokens_used"].add(event.token_used)

            if event.event_type == EventType.TOKEN_ASSIGNED:
                token_starts[f"{event.job_id}_{event.token_used}"] = event.timestamp
                token_analysis["token_assignments"][event.token_used].append(
                    {
                        "job_id": event.job_id,
                        "timestamp": event.timestamp,
                        "tier": event.tier,
                    }
                )

            elif event.event_type == EventType.TOKEN_RELEASED:
                key = f"{event.job_id}_{event.token_used}"
                if key in token_starts:
                    duration = (event.timestamp - token_starts[key]) * 1000
                    token_analysis["token_durations"][event.token_used].append(duration)

            elif event.event_type == EventType.TOKEN_RATE_LIMITED:
                token_analysis["rate_limits_hit"].append(
                    {
                        "timestamp": event.timestamp,
                        "token": event.token_used,
                        "job_id": event.job_id,
                    }
                )

        # Convert sets to lists for JSON serialization
        token_analysis["tokens_used"] = list(token_analysis["tokens_used"])
        token_analysis["token_assignments"] = dict(token_analysis["token_assignments"])
        token_analysis["token_durations"] = dict(token_analysis["token_durations"])

        return token_analysis

    def identify_bottlenecks(self) -> Dict[str, Any]:
        """Identify performance bottlenecks"""
        bottlenecks = {
            "longest_operations": [],
            "failed_operations": [],
            "queue_wait_times": [],
            "token_wait_times": [],
        }

        # Find longest operations
        durations = self.calculate_durations()
        all_durations = []
        for event_type, duration_list in durations.items():
            for item in duration_list:
                all_durations.append(
                    {
                        "event_type": event_type,
                        "duration_ms": item["duration_ms"],
                        "job_id": item.get("job_id"),
                        "tier": item.get("tier"),
                    }
                )

        all_durations.sort(key=lambda x: x["duration_ms"], reverse=True)
        bottlenecks["longest_operations"] = all_durations[:10]

        # Find failed operations
        for event in self.events:
            if not event.success:
                bottlenecks["failed_operations"].append(
                    {
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp,
                        "error": event.error_details,
                        "job_id": event.job_id,
                        "tier": event.tier,
                    }
                )

        # Calculate queue wait times
        job_states = defaultdict(dict)
        for event in self.events:
            if event.job_id:
                if event.event_type == EventType.JOB_CREATED:
                    job_states[event.job_id]["created"] = event.timestamp
                elif event.event_type == EventType.JOB_QUEUED:
                    job_states[event.job_id]["queued"] = event.timestamp
                elif event.event_type == EventType.JOB_STARTED:
                    job_states[event.job_id]["started"] = event.timestamp

        for job_id, times in job_states.items():
            if "queued" in times and "started" in times:
                wait_time = (times["started"] - times["queued"]) * 1000
                bottlenecks["queue_wait_times"].append(
                    {"job_id": job_id, "wait_ms": wait_time}
                )

        bottlenecks["queue_wait_times"].sort(key=lambda x: x["wait_ms"], reverse=True)

        return bottlenecks

    def calculate_success_rates(self) -> Dict[str, Any]:
        """Calculate success rates for different components"""
        success_rates = {
            "overall": {"success": 0, "failure": 0, "rate": 0.0},
            "by_tier": defaultdict(lambda: {"success": 0, "failure": 0, "rate": 0.0}),
            "by_event_type": defaultdict(
                lambda: {"success": 0, "failure": 0, "rate": 0.0}
            ),
        }

        for event in self.events:
            # Skip non-completion events
            if not any(end in event.event_type.name for end in ["COMPLETED", "FAILED"]):
                continue

            # Overall
            if event.success:
                success_rates["overall"]["success"] += 1
            else:
                success_rates["overall"]["failure"] += 1

            # By tier
            if event.success:
                success_rates["by_tier"][event.tier]["success"] += 1
            else:
                success_rates["by_tier"][event.tier]["failure"] += 1

            # By event type
            base_type = event.event_type.name.replace("_COMPLETED", "").replace(
                "_FAILED", ""
            )
            if event.success:
                success_rates["by_event_type"][base_type]["success"] += 1
            else:
                success_rates["by_event_type"][base_type]["failure"] += 1

        # Calculate rates
        for category in [success_rates["overall"]]:
            total = category["success"] + category["failure"]
            if total > 0:
                category["rate"] = category["success"] / total

        for tier_data in success_rates["by_tier"].values():
            total = tier_data["success"] + tier_data["failure"]
            if total > 0:
                tier_data["rate"] = tier_data["success"] / total

        for type_data in success_rates["by_event_type"].values():
            total = type_data["success"] + type_data["failure"]
            if total > 0:
                type_data["rate"] = type_data["success"] / total

        # Convert defaultdicts to regular dicts for JSON
        success_rates["by_tier"] = dict(success_rates["by_tier"])
        success_rates["by_event_type"] = dict(success_rates["by_event_type"])

        return success_rates

    def generate_timeline(self) -> List[Dict[str, Any]]:
        """Generate a visual timeline of events"""
        timeline = []

        for event in self.events:
            relative_time = (event.timestamp - self.start_time) * 1000  # ms from start
            timeline.append(
                {
                    "time_ms": relative_time,
                    "timestamp": event.timestamp,
                    "event": event.event_type.value,
                    "tier": event.tier,
                    "job_id": event.job_id,
                    "success": event.success,
                    "description": event.description,
                }
            )

        return timeline

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive timing analysis report"""
        total_duration = (self.end_time - self.start_time) * 1000  # Convert to ms

        report = {
            "summary": {
                "total_events": len(self.events),
                "total_duration_ms": total_duration,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
            },
            "durations": self.calculate_durations(),
            "parallelism": self.verify_parallelism(),
            "token_utilization": self.analyze_token_utilization(),
            "bottlenecks": self.identify_bottlenecks(),
            "success_rates": self.calculate_success_rates(),
            "timeline": self.generate_timeline(),
        }

        return report


class TimingCollector:
    """Collects timing events during test execution"""

    def __init__(self):
        self.events: List[TimingEvent] = []
        self.lock = threading.Lock()
        self.start_time = time.time()

        # Initialize system
        self.record_event(
            EventType.SYSTEM_INITIALIZED, "Timing collector initialized", tier=0
        )

    def record_event(
        self,
        event_type: EventType,
        description: str,
        tier: int = 0,
        success: bool = True,
        error_details: Optional[str] = None,
        job_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        parent_job_id: Optional[str] = None,
        token_used: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TimingEvent:
        """Record a timing event"""
        event = TimingEvent(
            timestamp=time.time(),
            event_type=event_type,
            description=description,
            tier=tier,
            success=success,
            error_details=error_details,
            job_id=job_id,
            batch_id=batch_id,
            parent_job_id=parent_job_id,
            token_used=token_used,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        with self.lock:
            self.events.append(event)

        return event

    def save_events(self, filepath: str):
        """Save events to JSON file"""
        with self.lock:
            events_data = [event.to_dict() for event in self.events]

        with open(filepath, "w") as f:
            json.dump(events_data, f, indent=2)

    def get_analyzer(self) -> TimingAnalyzer:
        """Get analyzer for current events"""
        with self.lock:
            return TimingAnalyzer(self.events.copy())


def format_duration(ms: float) -> str:
    """Format duration in milliseconds to human-readable string"""
    if ms < 1000:
        return f"{ms:.2f}ms"
    elif ms < 60000:
        return f"{ms/1000:.2f}s"
    else:
        minutes = ms / 60000
        return f"{minutes:.2f}min"


def print_report_summary(report: Dict[str, Any]):
    """Print a formatted summary of the timing report"""
    print("\n" + "=" * 80)
    print("TIMING ANALYSIS REPORT")
    print("=" * 80)

    # Summary
    print("\n📊 SUMMARY")
    print(
        f"  Total Duration: {format_duration(report['summary']['total_duration_ms'])}"
    )
    print(f"  Total Events: {report['summary']['total_events']}")
    print(f"  Start Time: {report['summary']['start_time']}")
    print(f"  End Time: {report['summary']['end_time']}")

    # Parallelism
    print("\n🔄 PARALLELISM ANALYSIS")
    para = report["parallelism"]
    print(f"  Tier 1 Parallel: {'✅ Yes' if para['tier_1_parallel'] else '❌ No'}")
    print(f"  Max Concurrent Tier 1: {para['max_concurrent_tier_1']}")
    print(f"  Tier 2 Parallel: {'✅ Yes' if para['tier_2_parallel'] else '❌ No'}")
    print(f"  Max Concurrent Tier 2: {para['max_concurrent_tier_2']}")

    if para["tier_1_overlaps"]:
        print(f"  Tier 1 Overlaps: {len(para['tier_1_overlaps'])} job pairs")
    if para["tier_2_overlaps"]:
        print(f"  Tier 2 Overlaps: {len(para['tier_2_overlaps'])} job pairs")

    # Token Utilization
    print("\n🔑 TOKEN UTILIZATION")
    tokens = report["token_utilization"]
    print(f"  Tokens Used: {len(tokens['tokens_used'])}")
    for token in tokens["tokens_used"]:
        if token in tokens["token_assignments"]:
            print(f"    {token}: {len(tokens['token_assignments'][token])} assignments")
    if tokens["rate_limits_hit"]:
        print(f"  ⚠️ Rate Limits Hit: {len(tokens['rate_limits_hit'])} times")

    # Success Rates
    print("\n✅ SUCCESS RATES")
    rates = report["success_rates"]
    print(
        f"  Overall: {rates['overall']['rate']*100:.1f}% ({rates['overall']['success']}/{rates['overall']['success'] + rates['overall']['failure']})"
    )

    if rates["by_tier"]:
        print("  By Tier:")
        for tier, data in sorted(rates["by_tier"].items()):
            total = data["success"] + data["failure"]
            if total > 0:
                print(
                    f"    Tier {tier}: {data['rate']*100:.1f}% ({data['success']}/{total})"
                )

    # Bottlenecks
    print("\n🚧 PERFORMANCE BOTTLENECKS")
    bottlenecks = report["bottlenecks"]
    if bottlenecks["longest_operations"]:
        print("  Longest Operations:")
        for op in bottlenecks["longest_operations"][:5]:
            print(
                f"    {op['event_type']}: {format_duration(op['duration_ms'])} (Tier {op.get('tier', 'N/A')})"
            )

    if bottlenecks["failed_operations"]:
        print(f"  Failed Operations: {len(bottlenecks['failed_operations'])}")
        for fail in bottlenecks["failed_operations"][:3]:
            print(
                f"    {fail['event_type']} at Tier {fail['tier']}: {fail.get('error', 'Unknown error')[:50]}"
            )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Example usage
    print("Timing Analysis System initialized")
    print(
        "This module provides comprehensive timing analysis for recursive spawning tests"
    )
    print("\nUsage:")
    print("  from timing_analysis_system import TimingCollector, TimingAnalyzer")
    print("  collector = TimingCollector()")
    print("  # ... run your tests while recording events ...")
    print("  analyzer = collector.get_analyzer()")
    print("  report = analyzer.generate_report()")
