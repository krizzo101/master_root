#!/usr/bin/env python3
"""
Analyze parallel agent log files to prove overlap
"""

import os
import re
from datetime import datetime
from pathlib import Path

def parse_timestamp(timestamp_str):
    """Parse timestamp string"""
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def analyze_parallel_logs():
    """Analyze log files to prove parallel execution"""
    
    log_dir = Path("/home/opsvi/master_root/apps/agent-orchestrator/parallel_test_logs")
    
    print("🔍 PARALLEL EXECUTION LOG ANALYSIS")
    print("=" * 60)
    
    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        print("❌ No log files found")
        return False
    
    print(f"📁 Found {len(log_files)} log files:")
    for log_file in log_files:
        print(f"  - {log_file.name}")
    
    print("\n📊 TIMESTAMP ANALYSIS:")
    print("=" * 60)
    
    agent_data = []
    
    for log_file in log_files:
        try:
            content = log_file.read_text().strip()
            lines = content.split('\n')
            
            if len(lines) < 2:
                print(f"❌ {log_file.name}: Insufficient data")
                continue
                
            # Parse START line
            start_line = lines[0]
            start_match = re.search(r'START (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([^\s]+) (.+)', start_line)
            
            if not start_match:
                print(f"❌ {log_file.name}: Invalid START format")
                continue
                
            start_time_str = start_match.group(1)
            token = start_match.group(2)
            task_desc = start_match.group(3)
            
            # Parse END line
            end_line = lines[-1]
            end_match = re.search(r'END (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([^\s]+) COMPLETED', end_line)
            
            if not end_match:
                print(f"❌ {log_file.name}: Invalid END format")
                continue
                
            end_time_str = end_match.group(1)
            agent_name = end_match.group(2)
            
            # Parse timestamps
            start_time = parse_timestamp(start_time_str)
            end_time = parse_timestamp(end_time_str)
            
            if not start_time or not end_time:
                print(f"❌ {log_file.name}: Cannot parse timestamps")
                continue
                
            duration = (end_time - start_time).total_seconds()
            
            agent_data.append({
                'name': agent_name,
                'start_time': start_time,
                'end_time': end_time, 
                'duration': duration,
                'token': token,
                'file': log_file.name
            })
            
            print(f"✅ {agent_name}:")
            print(f"   Start: {start_time_str}")
            print(f"   End:   {end_time_str}")
            print(f"   Duration: {duration:.1f}s")
            print(f"   Token: {token}")
            print()
            
        except Exception as e:
            print(f"❌ {log_file.name}: Error - {e}")
    
    if len(agent_data) < 2:
        print("❌ Need at least 2 agents to prove parallel execution")
        return False
    
    # Sort by start time
    agent_data.sort(key=lambda x: x['start_time'])
    
    print("⏱️  EXECUTION TIMELINE:")
    print("=" * 60)
    for agent in agent_data:
        print(f"{agent['start_time'].strftime('%H:%M:%S')} - {agent['end_time'].strftime('%H:%M:%S')} | {agent['name']} ({agent['duration']:.1f}s)")
    
    print("\n🔍 OVERLAP ANALYSIS:")
    print("=" * 60)
    
    overlaps = []
    for i, agent_a in enumerate(agent_data):
        for j, agent_b in enumerate(agent_data):
            if i >= j:
                continue
                
            # Check overlap: A starts before B ends AND B starts before A ends
            if (agent_a['start_time'] < agent_b['end_time'] and 
                agent_b['start_time'] < agent_a['end_time']):
                
                overlap_start = max(agent_a['start_time'], agent_b['start_time'])
                overlap_end = min(agent_a['end_time'], agent_b['end_time'])
                overlap_duration = (overlap_end - overlap_start).total_seconds()
                
                overlaps.append({
                    'agent_a': agent_a['name'],
                    'agent_b': agent_b['name'],
                    'overlap': overlap_duration
                })
                
                print(f"✅ OVERLAP: {agent_a['name']} ↔ {agent_b['name']} ({overlap_duration:.1f}s)")
    
    print(f"\n🎉 SUMMARY:")
    print("=" * 60)
    print(f"Agents analyzed: {len(agent_data)}")
    print(f"Overlapping pairs: {len(overlaps)}")
    print(f"Unique tokens: {len(set(a['token'] for a in agent_data))}")
    
    if overlaps:
        print(f"\n🏆 PARALLEL EXECUTION PROVEN!")
        print(f"✅ {len(overlaps)} pairs executed with overlapping timestamps")
        print(f"✅ Agents ran simultaneously, not sequentially")
        return True
    else:
        print(f"\n❌ NO OVERLAP DETECTED")
        return False

if __name__ == "__main__":
    success = analyze_parallel_logs()
    print(f"\n{'🎉 PARALLEL EXECUTION DEFINITIVELY PROVEN' if success else '❌ PARALLEL EXECUTION NOT PROVEN'}")