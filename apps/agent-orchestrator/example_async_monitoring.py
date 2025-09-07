#!/usr/bin/env python3
"""
Example usage of the async monitoring system
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime
import random

import sys
sys.path.insert(0, str(Path(__file__).parent))
from async_monitoring import AsyncMonitoringPipeline


async def simulate_agent_logs(log_file: Path, agent_id: str):
    """Simulate an agent writing logs"""
    log_types = [
        ("INFO", "Processing task"),
        ("DEBUG", "Checking dependencies"),
        ("WARNING", "High memory usage detected"),
        ("ERROR", "Connection timeout"),
        ("INFO", "Task completed successfully"),
    ]
    
    for i in range(20):
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        log_type, message = random.choice(log_types)
        
        # Create JSON log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "session_id": f"session-{agent_id}-{i//5}",
            "level": log_type,
            "message": f"{message} [{i}]",
            "metrics": {
                "cpu_percent": random.uniform(10, 90),
                "memory_mb": random.uniform(100, 500),
                "tasks_pending": random.randint(0, 10)
            }
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        print(f"  → {agent_id} wrote: {log_type} - {message} [{i}]")


async def main():
    """Demonstrate async monitoring with multiple simulated agents"""
    
    print("=== Async File Monitoring Demo ===\n")
    print("Creating simulated agent log files...")
    
    # Create temporary log files for different agents
    log_files = []
    agent_tasks = []
    
    for i in range(3):
        # Create log file
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=f'_agent_{i}.log', 
            delete=False
        ) as f:
            log_file = Path(f.name)
            log_files.append(log_file)
            
            # Write initial entry
            initial_log = {
                "timestamp": datetime.now().isoformat(),
                "agent_id": f"agent-{i:03d}",
                "session_id": f"session-init",
                "level": "INFO",
                "message": f"Agent {i} starting up"
            }
            f.write(json.dumps(initial_log) + '\n')
        
        print(f"Created log file for agent-{i:03d}: {log_file.name}")
        
        # Start agent simulation
        agent_task = asyncio.create_task(
            simulate_agent_logs(log_file, f"agent-{i:03d}")
        )
        agent_tasks.append(agent_task)
    
    print("\nStarting async monitoring pipeline...")
    print("=" * 50)
    print("Monitoring output (with color-coded priorities):\n")
    
    # Create and start monitoring pipeline
    pipeline = AsyncMonitoringPipeline(max_concurrent=10)
    
    try:
        # Start monitoring
        await pipeline.start(log_files)
        
        # Wait for agents to finish
        await asyncio.gather(*agent_tasks)
        
        # Let pipeline process remaining messages
        await asyncio.sleep(2)
        
        print("\n" + "=" * 50)
        print("Monitoring complete!")
        
        # Print final statistics
        stats = pipeline.queue.get_stats()
        print(f"\nFinal Statistics:")
        print(f"  Messages queued: {stats['messages_queued']}")
        print(f"  Messages processed: {stats['messages_processed']}")
        print(f"  Messages dropped: {stats['messages_dropped']}")
        print(f"  Queue sizes: {stats['queue_sizes']}")
        
    finally:
        # Cleanup
        await pipeline.stop()
        
        for log_file in log_files:
            log_file.unlink()
            print(f"Cleaned up {log_file.name}")


if __name__ == "__main__":
    print("Starting async monitoring demonstration...")
    print("This will simulate 3 agents writing JSON logs concurrently")
    print("The monitoring system will tail all files in real-time\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")