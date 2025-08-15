#!/usr/bin/env python3
"""
REAL timing test with actual MCP calls
"""
import asyncio
import json
import time
from datetime import datetime
import subprocess
import os

class RealTimingCollector:
    def __init__(self):
        self.events = []
        self.start_time = time.time()
        
    def log_event(self, event_type, description, metadata=None):
        """Log an event with real timestamp"""
        current_time = time.time()
        elapsed_ms = (current_time - self.start_time) * 1000
        
        event = {
            "timestamp": current_time,
            "elapsed_ms": elapsed_ms,
            "timestamp_readable": datetime.fromtimestamp(current_time).isoformat(),
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {}
        }
        
        self.events.append(event)
        print(f"[{elapsed_ms:8.2f}ms] {event_type}: {description}")
        
        return event
    
    def save_report(self, filepath):
        """Save timing report"""
        report = {
            "total_duration_ms": (time.time() - self.start_time) * 1000,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_events": len(self.events),
            "events": self.events
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


async def run_real_mcp_test():
    """Run actual MCP test with real timing"""
    
    collector = RealTimingCollector()
    collector.log_event("TEST_START", "Starting real MCP timing test")
    
    # Clean up old files
    collector.log_event("CLEANUP", "Removing old test files")
    subprocess.run("rm -f /tmp/real_timing_*.txt", shell=True, capture_output=True)
    
    # Prepare the actual MCP command
    test_tasks = [
        {
            "task": "Create file /tmp/real_timing_A1.txt with content 'REAL_A1_SUCCESS'",
            "model": "sonnet"
        },
        {
            "task": "Create file /tmp/real_timing_B1.txt with content 'REAL_B1_SUCCESS'",
            "model": "sonnet"
        },
        {
            "task": "Create file /tmp/real_timing_C1.txt with content 'REAL_C1_SUCCESS'",
            "model": "sonnet"
        }
    ]
    
    # Save tasks to file for reference
    with open('/tmp/real_timing_tasks.json', 'w') as f:
        json.dump(test_tasks, f, indent=2)
    
    collector.log_event("TASKS_CREATED", f"Created {len(test_tasks)} test tasks")
    
    # Now execute via Claude CLI with MCP config
    # We'll spawn 3 parallel Claude instances directly
    collector.log_event("PARALLEL_SPAWN_START", "Starting 3 parallel Claude instances")
    
    processes = []
    for i, task_info in enumerate(test_tasks):
        label = chr(65 + i)  # A, B, C
        
        # Build command for each Claude instance
        cmd = [
            'claude',
            '--model', task_info['model'],
            '--mcp-config', '/home/opsvi/master_root/.mcp.json',
            '--dangerously-skip-permissions',
            '-p', task_info['task']
        ]
        
        # Set different token for each via environment
        env = os.environ.copy()
        if i == 0:
            env['CLAUDE_CODE_TOKEN'] = os.getenv('CLAUDE_CODE_TOKEN', '')
        elif i == 1:
            env['CLAUDE_CODE_TOKEN'] = os.getenv('CLAUDE_CODE_TOKEN1', '')
        else:
            env['CLAUDE_CODE_TOKEN'] = os.getenv('CLAUDE_CODE_TOKEN2', '')
        
        collector.log_event(f"SPAWN_{label}", f"Starting Claude instance {label} with token {i+1}")
        
        # Start process
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        processes.append({
            'label': label,
            'proc': proc,
            'start_time': time.time(),
            'cmd': ' '.join(cmd),
            'token_index': i
        })
    
    collector.log_event("ALL_SPAWNED", f"All {len(processes)} processes spawned")
    
    # Monitor completion
    completed = []
    while processes:
        for p in processes[:]:
            if p['proc'].poll() is not None:
                # Process completed
                end_time = time.time()
                duration = end_time - p['start_time']
                
                stdout, stderr = p['proc'].communicate()
                success = p['proc'].returncode == 0
                
                collector.log_event(
                    f"COMPLETE_{p['label']}", 
                    f"Claude {p['label']} completed in {duration:.2f}s",
                    {
                        "duration_seconds": duration,
                        "success": success,
                        "returncode": p['proc'].returncode,
                        "stdout_preview": stdout[:200] if stdout else None,
                        "stderr": stderr if stderr else None
                    }
                )
                
                completed.append(p)
                processes.remove(p)
        
        if processes:
            await asyncio.sleep(0.1)  # Check every 100ms
    
    collector.log_event("ALL_COMPLETE", f"All {len(completed)} processes completed")
    
    # Check files created
    collector.log_event("VERIFY_START", "Verifying output files")
    
    files_found = 0
    for letter in ['A', 'B', 'C']:
        filepath = f"/tmp/real_timing_{letter}1.txt"
        if os.path.exists(filepath):
            with open(filepath) as f:
                content = f.read().strip()
            collector.log_event(
                f"FILE_VERIFIED_{letter}",
                f"File {filepath} exists with content: {content}"
            )
            files_found += 1
        else:
            collector.log_event(
                f"FILE_MISSING_{letter}",
                f"File {filepath} NOT FOUND"
            )
    
    collector.log_event("TEST_COMPLETE", f"Test complete. Files created: {files_found}/3")
    
    # Save report
    report_path = f"/tmp/real_timing_report_{int(time.time())}.json"
    report = collector.save_report(report_path)
    
    print("\n" + "="*60)
    print("REAL TIMING ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Duration: {report['total_duration_ms']/1000:.2f} seconds")
    print(f"Total Events: {report['total_events']}")
    print(f"Files Created: {files_found}/3")
    print(f"Report Saved: {report_path}")
    
    # Analyze parallelism
    spawn_events = [e for e in collector.events if 'SPAWN_' in e['event_type']]
    complete_events = [e for e in collector.events if 'COMPLETE_' in e['event_type']]
    
    if spawn_events and complete_events:
        first_spawn = min(e['timestamp'] for e in spawn_events)
        last_spawn = max(e['timestamp'] for e in spawn_events)
        first_complete = min(e['timestamp'] for e in complete_events)
        last_complete = max(e['timestamp'] for e in complete_events)
        
        spawn_spread = last_spawn - first_spawn
        complete_spread = last_complete - first_complete
        
        print(f"\nParallelism Analysis:")
        print(f"  Spawn spread: {spawn_spread:.3f}s (all started within this time)")
        print(f"  Completion spread: {complete_spread:.3f}s")
        print(f"  First completion: {(first_complete - first_spawn):.2f}s after first spawn")
        print(f"  Last completion: {(last_complete - first_spawn):.2f}s after first spawn")
        
        # If truly parallel, completion spread should be small
        if complete_spread < 5.0:  # Within 5 seconds
            print("  ✅ PARALLEL EXECUTION CONFIRMED")
        else:
            print("  ⚠️ SEQUENTIAL or PARTIALLY SEQUENTIAL EXECUTION")
    
    return report


if __name__ == "__main__":
    print("REAL MCP TIMING TEST")
    print("="*60)
    print("This test spawns REAL Claude instances with actual API calls")
    print("Expected time: 12-15 seconds if parallel, 36-45 seconds if sequential")
    print("="*60)
    
    asyncio.run(run_real_mcp_test())