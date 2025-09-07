#!/usr/bin/env python3
"""
Simple Log Tailer Demo - Standalone Examples
============================================

This script provides simple, runnable demonstrations of log tailing concepts
without requiring the full enhanced tailer implementation.
"""

import asyncio
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import tempfile
import shutil
import re


class SimpleLogTailerDemo:
    """Simplified demo for log tailing concepts"""
    
    def __init__(self):
        self.demo_dir = Path(tempfile.mkdtemp(prefix="simple_log_demo_"))
        self.patterns = {
            "ERROR": re.compile(r"ERROR|CRITICAL|FATAL"),
            "WARNING": re.compile(r"WARNING|WARN"),
            "SWARM": re.compile(r"SWARM_DETECTED|COORDINATED|COLLECTIVE"),
            "PERFORMANCE": re.compile(r"LATENCY|THROUGHPUT|MEMORY")
        }
        print(f"📁 Demo directory: {self.demo_dir}")
    
    def create_sample_logs(self):
        """Create sample log files for demonstration"""
        # Application log
        app_log = self.demo_dir / "app.log"
        with open(app_log, 'w') as f:
            for i in range(50):
                timestamp = datetime.now().isoformat()
                if i % 10 == 0:
                    f.write(f"{timestamp} ERROR Database connection failed\n")
                elif i % 5 == 0:
                    f.write(f"{timestamp} WARNING High memory usage: 85%\n")
                else:
                    f.write(f"{timestamp} INFO Request processed\n")
        
        print(f"✅ Created {app_log.name} with 50 entries")
        
        # Swarm activity log
        swarm_log = self.demo_dir / "swarm.log"
        with open(swarm_log, 'w') as f:
            # Create burst patterns
            for burst in range(3):
                base_time = datetime.now() - timedelta(minutes=5-burst)
                for i in range(10):
                    timestamp = (base_time + timedelta(milliseconds=i*100)).isoformat()
                    agent_id = f"agent_{i+1:03d}"
                    f.write(f"{timestamp} [{agent_id}] SWARM_DETECTED: Coordinated action\n")
        
        print(f"✅ Created {swarm_log.name} with swarm patterns")
        
        return app_log, swarm_log
    
    async def demo_pattern_matching(self):
        """Demo 1: Pattern matching in log files"""
        print("\n" + "="*60)
        print("DEMO 1: Pattern Matching")
        print("="*60)
        
        app_log, _ = self.create_sample_logs()
        
        # Read and analyze log
        matches = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        
        print(f"\n📖 Analyzing {app_log.name}...")
        with open(app_log, 'r') as f:
            for line in f:
                for pattern_name, pattern in self.patterns.items():
                    if pattern.search(line):
                        if pattern_name in matches:
                            matches[pattern_name] += 1
                        break
                else:
                    if "INFO" in line:
                        matches["INFO"] += 1
        
        print("\n📊 Pattern Match Results:")
        for pattern, count in matches.items():
            bar = "█" * (count // 2)
            print(f"  {pattern:10s}: {count:3d} {bar}")
        
        # Show sample matches
        print("\n📝 Sample Matches:")
        with open(app_log, 'r') as f:
            lines = f.readlines()
            for pattern in ["ERROR", "WARNING"]:
                print(f"\n  {pattern}:")
                shown = 0
                for line in lines:
                    if self.patterns.get(pattern, re.compile(pattern)).search(line):
                        print(f"    → {line.strip()[:80]}...")
                        shown += 1
                        if shown >= 2:
                            break
    
    async def demo_swarm_detection(self):
        """Demo 2: Simple swarm detection"""
        print("\n" + "="*60)
        print("DEMO 2: Swarm Behavior Detection")
        print("="*60)
        
        _, swarm_log = self.create_sample_logs()
        
        print(f"\n🐝 Analyzing swarm patterns in {swarm_log.name}...")
        
        # Simple time-based clustering
        events_by_second = {}
        
        with open(swarm_log, 'r') as f:
            for line in f:
                # Extract timestamp
                match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                if match:
                    timestamp = match.group(1)
                    second_key = timestamp.split('.')[0]
                    
                    if second_key not in events_by_second:
                        events_by_second[second_key] = []
                    
                    # Extract agent ID
                    agent_match = re.search(r'\[agent_(\d+)\]', line)
                    if agent_match:
                        agent_id = agent_match.group(1)
                        events_by_second[second_key].append(agent_id)
        
        # Detect swarms (multiple agents in same second)
        swarms_detected = []
        for timestamp, agents in events_by_second.items():
            if len(agents) >= 3:
                swarms_detected.append({
                    'timestamp': timestamp,
                    'agent_count': len(agents),
                    'agents': list(set(agents))
                })
        
        print(f"\n🎯 Detected {len(swarms_detected)} swarm clusters:")
        for swarm in swarms_detected[:5]:  # Show first 5
            print(f"\n  Timestamp: {swarm['timestamp']}")
            print(f"  Agents: {swarm['agent_count']} agents")
            print(f"  IDs: {', '.join(swarm['agents'][:5])}...")
    
    async def demo_real_time_monitoring(self):
        """Demo 3: Simulated real-time monitoring"""
        print("\n" + "="*60)
        print("DEMO 3: Real-time Monitoring Simulation")
        print("="*60)
        
        live_log = self.demo_dir / "live.log"
        live_log.touch()
        
        print(f"\n📡 Monitoring {live_log.name} for 10 seconds...")
        print("    (Generating live events...)\n")
        
        async def generate_events():
            """Generate live log events"""
            event_types = [
                ("INFO", "User login from 192.168.1.{}", 60),
                ("WARNING", "High CPU usage: {}%", 20),
                ("ERROR", "Connection timeout to service {}", 15),
                ("INFO", "Request processed in {}ms", 5)
            ]
            
            for i in range(20):
                await asyncio.sleep(0.5)
                
                # Pick random event type
                level, template, weight = random.choices(
                    event_types,
                    weights=[60, 20, 15, 5]
                )[0]
                
                # Generate event
                timestamp = datetime.now().isoformat()
                if "{}" in template:
                    value = random.randint(1, 100)
                    message = template.format(value)
                else:
                    message = template
                
                event = f"{timestamp} {level} {message}\n"
                
                # Write to file
                with open(live_log, 'a') as f:
                    f.write(event)
                
                # Display with color coding
                if level == "ERROR":
                    print(f"  🔴 {event.strip()}")
                elif level == "WARNING":
                    print(f"  🟡 {event.strip()}")
                else:
                    print(f"  🟢 {event.strip()}")
        
        await generate_events()
        
        # Summary
        print("\n📊 Monitoring Summary:")
        error_count = 0
        warning_count = 0
        info_count = 0
        
        with open(live_log, 'r') as f:
            for line in f:
                if "ERROR" in line:
                    error_count += 1
                elif "WARNING" in line:
                    warning_count += 1
                else:
                    info_count += 1
        
        total = error_count + warning_count + info_count
        print(f"  Total events: {total}")
        print(f"  Errors: {error_count} ({error_count*100//total if total else 0}%)")
        print(f"  Warnings: {warning_count} ({warning_count*100//total if total else 0}%)")
        print(f"  Info: {info_count} ({info_count*100//total if total else 0}%)")
    
    async def demo_performance_analysis(self):
        """Demo 4: Log processing performance"""
        print("\n" + "="*60)
        print("DEMO 4: Performance Analysis")
        print("="*60)
        
        # Create large log file
        perf_log = self.demo_dir / "performance.log"
        line_count = 10000
        
        print(f"\n⚡ Creating {line_count:,} line log file...")
        start_time = time.perf_counter()
        
        with open(perf_log, 'w') as f:
            for i in range(line_count):
                timestamp = datetime.now().isoformat()
                level = random.choice(['INFO', 'DEBUG', 'WARNING', 'ERROR'])
                message = f"Message {i}: " + "x" * random.randint(50, 150)
                f.write(f"{timestamp} {level} {message}\n")
        
        create_time = time.perf_counter() - start_time
        print(f"  Created in {create_time:.2f}s")
        
        # Test read performance
        print(f"\n📖 Testing read performance...")
        start_time = time.perf_counter()
        
        lines_read = 0
        with open(perf_log, 'r') as f:
            for line in f:
                lines_read += 1
        
        read_time = time.perf_counter() - start_time
        lines_per_second = lines_read / read_time if read_time > 0 else 0
        
        print(f"  Read {lines_read:,} lines in {read_time:.3f}s")
        print(f"  Throughput: {lines_per_second:,.0f} lines/second")
        
        # Test pattern matching performance
        print(f"\n🔍 Testing pattern matching performance...")
        start_time = time.perf_counter()
        
        matches = 0
        with open(perf_log, 'r') as f:
            for line in f:
                for pattern in self.patterns.values():
                    if pattern.search(line):
                        matches += 1
                        break
        
        match_time = time.perf_counter() - start_time
        match_rate = lines_read / match_time if match_time > 0 else 0
        
        print(f"  Processed in {match_time:.3f}s")
        print(f"  Found {matches:,} matches")
        print(f"  Rate: {match_rate:,.0f} lines/second")
        
        # Memory estimate
        file_size = perf_log.stat().st_size
        print(f"\n💾 File Statistics:")
        print(f"  Size: {file_size / 1024 / 1024:.2f} MB")
        print(f"  Avg line size: {file_size / line_count:.0f} bytes")
    
    async def run_all_demos(self):
        """Run all demonstrations"""
        demos = [
            ("Pattern Matching", self.demo_pattern_matching),
            ("Swarm Detection", self.demo_swarm_detection),
            ("Real-time Monitoring", self.demo_real_time_monitoring),
            ("Performance Analysis", self.demo_performance_analysis)
        ]
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║          SIMPLE LOG TAILER - DEMONSTRATION SUITE            ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        for name, demo_func in demos:
            await demo_func()
            await asyncio.sleep(1)
        
        print("\n" + "="*60)
        print("✅ All demonstrations completed!")
        print("="*60)
    
    def cleanup(self):
        """Clean up demo directory"""
        if self.demo_dir.exists():
            shutil.rmtree(self.demo_dir)
            print(f"\n🧹 Cleaned up demo directory: {self.demo_dir}")


async def main():
    """Main entry point"""
    demo = SimpleLogTailerDemo()
    
    try:
        await demo.run_all_demos()
    finally:
        demo.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(0)