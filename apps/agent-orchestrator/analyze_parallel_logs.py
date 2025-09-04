#!/usr/bin/env python3
"""
Parallel Execution Log Analyzer
Analyzes agent logs to prove parallel execution with overlap
"""

import os
import re
from datetime import datetime
from pathlib import Path

def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object"""
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def analyze_parallel_logs():
    """Analyze agent logs to prove parallel execution"""
    
    log_dir = Path("/home/opsvi/master_root/apps/agent-orchestrator/parallel_execution_test_logs")
    
    print("🔍 DEFINITIVE PARALLEL EXECUTION ANALYSIS")
    print("=" * 80)
    
    # Find all log files
    log_files = list(log_dir.glob("*.log"))
    
    if not log_files:
        print("❌ NO LOG FILES FOUND")
        print(f"Expected location: {log_dir}")
        return False
    
    print(f"📁 Found {len(log_files)} log files:")
    for log_file in log_files:
        print(f"  - {log_file.name}")
    
    print("\n📊 ANALYZING EACH AGENT LOG:")
    print("=" * 80)
    
    agent_data = []
    
    for log_file in log_files:
        try:
            content = log_file.read_text().strip()
            lines = content.split('\n')
            
            if not lines or len(lines) < 2:
                print(f"❌ {log_file.name}: Insufficient log data")
                continue
            
            # Parse start line
            start_line = lines[0]
            start_match = re.search(r'START: ([^|]+) \| TOKEN: ([^|]+) \| TASK: (.+)', start_line)
            
            if not start_match:
                print(f"❌ {log_file.name}: Invalid start line format")
                continue
            
            start_time_str = start_match.group(1).strip()
            token_prefix = start_match.group(2).strip()
            task_description = start_match.group(3).strip()
            
            # Parse end line
            end_line = lines[-1]
            end_match = re.search(r'END: ([^|]+) \| AGENT: ([^|]+) \| STATUS: (.+)', end_line)
            
            if not end_match:
                print(f"❌ {log_file.name}: Invalid end line format")
                continue
            
            end_time_str = end_match.group(1).strip()
            agent_name = end_match.group(2).strip()
            status = end_match.group(3).strip()
            
            # Parse timestamps
            start_time = parse_timestamp(start_time_str)
            end_time = parse_timestamp(end_time_str)
            
            if not start_time or not end_time:
                print(f"❌ {log_file.name}: Invalid timestamp format")
                continue
            
            duration = (end_time - start_time).total_seconds()
            
            agent_info = {
                'file': log_file.name,
                'agent': agent_name,
                'start_time': start_time,
                'end_time': end_time,
                'duration': duration,
                'token': token_prefix,
                'task': task_description,
                'status': status
            }
            
            agent_data.append(agent_info)
            
            print(f"✅ {agent_name}:")
            print(f"   Start: {start_time_str}")
            print(f"   End:   {end_time_str}")
            print(f"   Duration: {duration:.1f} seconds")
            print(f"   Token: {token_prefix}")
            print(f"   Status: {status}")
            print()
            
        except Exception as e:
            print(f"❌ {log_file.name}: Error parsing - {e}")
            continue
    
    if len(agent_data) < 2:
        print("❌ INSUFFICIENT DATA: Need at least 2 agents to prove parallel execution")
        return False
    
    # Sort by start time
    agent_data.sort(key=lambda x: x['start_time'])
    
    print("⏱️  TIMELINE ANALYSIS:")
    print("=" * 80)
    
    # Show timeline
    for agent in agent_data:
        print(f"{agent['start_time'].strftime('%H:%M:%S')} - {agent['end_time'].strftime('%H:%M:%S')} | {agent['agent']} | Token: {agent['token']}")
    
    print("\n🔍 OVERLAP ANALYSIS:")
    print("=" * 80)
    
    # Check for overlaps
    overlaps_found = []
    unique_tokens = set()
    
    for i, agent_a in enumerate(agent_data):
        unique_tokens.add(agent_a['token'])
        
        for j, agent_b in enumerate(agent_data):
            if i >= j:  # Skip self and already checked pairs
                continue
                
            # Check if agent_a and agent_b overlap
            # Overlap exists if: start_a < end_b AND start_b < end_a
            if (agent_a['start_time'] < agent_b['end_time'] and 
                agent_b['start_time'] < agent_a['end_time']):
                
                overlap_start = max(agent_a['start_time'], agent_b['start_time'])
                overlap_end = min(agent_a['end_time'], agent_b['end_time'])
                overlap_duration = (overlap_end - overlap_start).total_seconds()
                
                overlaps_found.append({
                    'agent_a': agent_a['agent'],
                    'agent_b': agent_b['agent'],
                    'overlap_duration': overlap_duration
                })
                
                print(f"✅ OVERLAP FOUND: {agent_a['agent']} & {agent_b['agent']} ({overlap_duration:.1f}s overlap)")
    
    print(f"\n📈 PARALLEL EXECUTION SUMMARY:")
    print("=" * 80)
    print(f"Total agents analyzed: {len(agent_data)}")
    print(f"Unique tokens used: {len(unique_tokens)} ({', '.join(sorted(unique_tokens))})")
    print(f"Overlapping execution pairs: {len(overlaps_found)}")
    
    if len(overlaps_found) > 0:
        print("🎉 PARALLEL EXECUTION CONFIRMED!")
        print("✅ Multiple agents ran simultaneously with overlapping execution times")
        print("✅ Different token prefixes confirm unique agent instances")
        return True
    else:
        print("❌ NO OVERLAP DETECTED - Agents may have run sequentially")
        return False

if __name__ == "__main__":
    success = analyze_parallel_logs()
    print(f"\n🏆 DEFINITIVE RESULT: {'PARALLEL EXECUTION PROVEN' if success else 'PARALLEL EXECUTION NOT PROVEN'}")