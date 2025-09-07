#!/usr/bin/env python3
"""
Command-line Agent Monitor
Real-time monitoring of active Claude agents from the orchestrator
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def get_agent_logs():
    """Find all agent log files"""
    uuid_logs = Path.home() / '.claude/projects/-home-opsvi-master-root-apps-agent-orchestrator'
    if not uuid_logs.exists():
        return []
    return list(uuid_logs.glob('*.jsonl'))


def parse_agent_status(log_file):
    """Parse agent status from log file"""
    try:
        with open(log_file) as f:
            lines = f.readlines()
        
        if not lines:
            return None
            
        uuid = log_file.stem
        
        # Parse basic info
        try:
            last_entry = json.loads(lines[-1])
            last_time = datetime.fromisoformat(last_entry['timestamp'].replace('Z', '+00:00'))
        except:
            last_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        
        now = datetime.now(last_time.tzinfo if last_time.tzinfo else None)
        minutes_ago = (now - last_time).total_seconds() / 60 if last_time.tzinfo else float('inf')
        
        # Determine status
        if minutes_ago < 2:
            status = "🟢 ACTIVE"
        elif minutes_ago < 10:
            status = "🟡 RECENT"  
        else:
            status = "🔴 IDLE"
        
        # Count recent activity
        roles = {}
        tools = set()
        for line in lines[-5:]:  # Last 5 entries
            try:
                entry = json.loads(line)
                role = entry.get('role', 'unknown')
                roles[role] = roles.get(role, 0) + 1
                
                if 'tool_calls' in entry:
                    for tool_call in entry.get('tool_calls', []):
                        tools.add(tool_call.get('function', {}).get('name', 'unknown'))
            except:
                continue
        
        return {
            'uuid': uuid,
            'status': status,
            'entries': len(lines),
            'last_activity': last_time.strftime('%H:%M:%S'),
            'minutes_ago': minutes_ago,
            'recent_tools': list(tools)[:3]
        }
        
    except Exception as e:
        return None


def monitor_agents(watch=False, interval=5):
    """Monitor all agents"""
    try:
        while True:
            log_files = get_agent_logs()
            
            if not log_files:
                print("❌ No agent logs found")
                if not watch:
                    break
                time.sleep(interval)
                continue
            
            # Sort by most recent
            log_files.sort(key=os.path.getmtime, reverse=True)
            
            # Clear screen if watching
            if watch:
                os.system('clear' if os.name == 'posix' else 'cls')
            
            print(f"🔍 Agent Monitor - {datetime.now().strftime('%H:%M:%S')} ({len(log_files)} agents)")
            print("=" * 80)
            
            active_count = 0
            
            for log_file in log_files[:10]:  # Show top 10
                status = parse_agent_status(log_file)
                if not status:
                    continue
                
                if "ACTIVE" in status['status']:
                    active_count += 1
                
                tools_str = f" | Tools: {', '.join(status['recent_tools'])}" if status['recent_tools'] else ""
                
                print(f"{status['status']} {status['uuid'][:8]}... | "
                      f"Entries: {status['entries']} | "
                      f"Last: {status['last_activity']} "
                      f"({status['minutes_ago']:.1f}m ago){tools_str}")
            
            print("=" * 80)
            print(f"📊 Summary: {active_count} active agents out of {len(log_files)} total")
            
            if not watch:
                break
                
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor active Claude agents')
    parser.add_argument('--watch', '-w', action='store_true', 
                        help='Watch mode - continuously update')
    parser.add_argument('--interval', '-i', type=int, default=5,
                        help='Update interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    print("🚀 Starting Agent Monitor...")
    monitor_agents(watch=args.watch, interval=args.interval)


if __name__ == "__main__":
    main()