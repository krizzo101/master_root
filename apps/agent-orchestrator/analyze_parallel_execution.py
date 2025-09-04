#!/usr/bin/env python3
"""
Definitive Parallel Execution Analyzer
Analyzes Claude headless agent results to prove parallel execution with overlap
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path


def parse_timestamp(timestamp_str):
    """Parse various timestamp formats"""
    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    return None


def analyze_parallel_execution():
    """Analyze the parallel execution test results"""

    workspace = Path(
        "/home/opsvi/master_root/apps/agent-orchestrator/parallel_headless_test/logs"
    )

    print("🔍 DEFINITIVE PARALLEL EXECUTION ANALYSIS")
    print("=" * 80)

    # Load session IDs
    session_ids_file = workspace / "session_ids.txt"
    if not session_ids_file.exists():
        print("❌ Session IDs file not found")
        return False

    session_ids = {}
    for line in session_ids_file.read_text().strip().split("\n"):
        key, value = line.split("=")
        agent_num = key.split("_")[1]
        session_ids[agent_num] = value

    print(f"📋 Found {len(session_ids)} session IDs:")
    for agent, session_id in session_ids.items():
        print(f"  Agent {agent}: {session_id}")

    print("\n📁 AGENT OUTPUT FILES ANALYSIS:")
    print("=" * 80)

    agent_outputs = []
    for i in range(1, 6):
        output_file = workspace / f"agent_{i}_output.json"
        if output_file.exists() and output_file.stat().st_size > 0:
            try:
                content = output_file.read_text()
                if content.strip():
                    data = json.loads(content)
                    agent_outputs.append(
                        {
                            "agent": i,
                            "output": data,
                            "file_size": output_file.stat().st_size,
                        }
                    )
                    print(f"  ✅ Agent {i}: {output_file.stat().st_size} bytes")
                else:
                    print(f"  ⏳ Agent {i}: Empty output (still running?)")
            except json.JSONDecodeError:
                print(f"  ⚠️  Agent {i}: Invalid JSON (still writing?)")
        else:
            print(f"  ❌ Agent {i}: No output file or empty")

    print("\n📄 AGENT PROOF FILES ANALYSIS:")
    print("=" * 80)

    proof_files = [
        "agent_alpha_proof.txt",
        "agent_beta_proof.txt",
        "agent_gamma_proof.txt",
        "agent_delta_proof.txt",
        "agent_epsilon_proof.txt",
    ]

    agent_timestamps = []

    for proof_file in proof_files:
        file_path = workspace / proof_file
        if file_path.exists():
            content = file_path.read_text().strip()
            lines = content.split("\n")

            if len(lines) >= 2:
                start_line = lines[0]
                end_line = lines[-1]

                # Extract timestamps from START and END lines
                start_match = re.search(r"START: ([^,]+)", start_line)
                end_match = re.search(r"END: ([^,]+)", end_line)

                if start_match and end_match:
                    start_time = parse_timestamp(start_match.group(1).strip())
                    end_time = parse_timestamp(end_match.group(1).strip())

                    if start_time and end_time:
                        agent_name = (
                            proof_file.replace("_proof.txt", "")
                            .replace("agent_", "")
                            .upper()
                        )
                        agent_timestamps.append(
                            {
                                "agent": agent_name,
                                "start_time": start_time,
                                "end_time": end_time,
                                "duration": (end_time - start_time).total_seconds(),
                                "file": proof_file,
                            }
                        )
                        print(
                            f"  ✅ {agent_name}: {start_time} → {end_time} ({(end_time - start_time).total_seconds():.1f}s)"
                        )
                    else:
                        print(f"  ❌ {proof_file}: Could not parse timestamps")
                else:
                    print(f"  ❌ {proof_file}: No timestamp format found")
            else:
                print(f"  ⚠️  {proof_file}: Insufficient content")
        else:
            print(f"  ❌ {proof_file}: File not found")

    if len(agent_timestamps) < 2:
        print("\n❌ INSUFFICIENT DATA: Need at least 2 agents with timestamps")
        return False

    # Sort by start time
    agent_timestamps.sort(key=lambda x: x["start_time"])

    print(f"\n⏱️  TIMELINE ANALYSIS ({len(agent_timestamps)} agents):")
    print("=" * 80)

    for agent in agent_timestamps:
        print(
            f"{agent['start_time'].strftime('%H:%M:%S')} - {agent['end_time'].strftime('%H:%M:%S')} | "
            f"{agent['agent']} ({agent['duration']:.1f}s)"
        )

    print(f"\n🔍 OVERLAP ANALYSIS:")
    print("=" * 80)

    overlaps = []
    for i, agent_a in enumerate(agent_timestamps):
        for j, agent_b in enumerate(agent_timestamps):
            if i >= j:
                continue

            # Check for overlap: start_a < end_b AND start_b < end_a
            if (
                agent_a["start_time"] < agent_b["end_time"]
                and agent_b["start_time"] < agent_a["end_time"]
            ):
                overlap_start = max(agent_a["start_time"], agent_b["start_time"])
                overlap_end = min(agent_a["end_time"], agent_b["end_time"])
                overlap_duration = (overlap_end - overlap_start).total_seconds()

                overlaps.append(
                    {
                        "agent_a": agent_a["agent"],
                        "agent_b": agent_b["agent"],
                        "overlap_duration": overlap_duration,
                        "overlap_start": overlap_start,
                        "overlap_end": overlap_end,
                    }
                )

                print(
                    f"✅ OVERLAP: {agent_a['agent']} ↔ {agent_b['agent']} "
                    f"({overlap_duration:.1f}s overlap from {overlap_start.strftime('%H:%M:%S')} to {overlap_end.strftime('%H:%M:%S')})"
                )

    print(f"\n📊 SESSION LOG ANALYSIS:")
    print("=" * 80)

    claude_projects_dir = Path.home() / ".claude" / "projects"
    session_logs_found = 0

    if claude_projects_dir.exists():
        for session_id in session_ids.values():
            # Look for session log files
            session_files = list(claude_projects_dir.rglob(f"{session_id}.jsonl"))
            if session_files:
                session_logs_found += 1
                log_file = session_files[0]
                print(f"  ✅ Session {session_id[:8]}...: {log_file}")
            else:
                print(f"  ❌ Session {session_id[:8]}...: Log not found")
    else:
        print("  ❌ Claude projects directory not found")

    print(f"\n🎉 PARALLEL EXECUTION SUMMARY:")
    print("=" * 80)
    print(f"Agents with timestamps: {len(agent_timestamps)}")
    print(f"Overlapping pairs: {len(overlaps)}")
    print(f"Session logs found: {session_logs_found}")
    print(f"Agent output files: {len(agent_outputs)}")

    if len(overlaps) > 0:
        print(f"\n🏆 PARALLEL EXECUTION PROVEN!")
        print(f"✅ {len(overlaps)} pairs of agents executed with overlapping timestamps")
        print(f"✅ Multiple agents ran simultaneously, not sequentially")
        print(f"✅ Definitive proof of parallel orchestration capability")
        return True
    else:
        print(f"\n❌ NO OVERLAP DETECTED")
        print(f"Agents may have executed sequentially or test incomplete")
        return False


if __name__ == "__main__":
    success = analyze_parallel_execution()
    print(
        f"\n{'🎉 PARALLEL EXECUTION DEFINITIVELY PROVEN' if success else '❌ PARALLEL EXECUTION NOT PROVEN'}"
    )
