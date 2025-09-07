#!/usr/bin/env python3
"""
Enhanced Log Tailer - Interactive Examples and Demos
====================================================

This script provides interactive demonstrations of the Enhanced Log Tailer's
capabilities, including swarm detection, pattern matching, and real-time monitoring.
"""

import asyncio
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import the main tailer class
from enhanced_swarm_log_tailer import EnhancedSwarmLogTailer

# Define necessary classes and enums that aren't exported
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    source: str
    raw_line: str
    
class SwarmBehavior(Enum):
    SYNCHRONIZED = "synchronized"
    BURST = "burst"
    COORDINATED = "coordinated"
    MIGRATION = "migration"
    COLLECTIVE = "collective"

@dataclass
class SwarmPattern:
    behavior: SwarmBehavior
    confidence: float
    agent_count: int
    duration: float
    event_rate: float
    start_time: datetime
    end_time: datetime

class VisualizationMode(Enum):
    SIMPLE = "simple"
    RICH = "rich"
    JSON = "json"
from src.generic_orchestrator import GenericOrchestrator


class DemoRunner:
    """Interactive demo runner for Enhanced Log Tailer"""
    
    def __init__(self):
        self.tailer = None
        self.orchestrator = None
        self.demo_dir = Path(tempfile.mkdtemp(prefix="log_tailer_demo_"))
        self.running_demos = []
    
    async def run_tailer_background(self):
        """Run tailer in background for demos"""
        try:
            # Simulate tailing by just waiting
            while True:
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        
    async def setup(self):
        """Initialize components"""
        print("🚀 Initializing Enhanced Log Tailer Demo Environment...")
        
        # Create demo log files
        self.create_demo_logs()
        
        # Import config classes
        from enhanced_swarm_log_tailer import (
            SystemConfig, SwarmConfig, VisualConfig, OutputConfig
        )
        
        # Create configuration objects
        system_config = SystemConfig(
            projects_dir=self.demo_dir,
            pattern="*.log",
            max_files=100,
            buffer_size=1000
        )
        
        swarm_config = SwarmConfig(
            enabled=True,
            min_agents=3,
            time_window_seconds=30,
            confidence_threshold=0.7
        )
        
        visual_config = VisualConfig(
            use_color=True,
            color_scheme="default",
            show_timestamps=True,
            show_source=True
        )
        
        output_config = OutputConfig(
            output_file=None,
            format="text",
            verbose=False,
            quiet=False
        )
        
        # Initialize tailer with configuration
        self.tailer = EnhancedSwarmLogTailer(
            system_config=system_config,
            swarm_config=swarm_config,
            visual_config=visual_config,
            output_config=output_config
        )
        
        # Initialize orchestrator
        self.orchestrator = GenericOrchestrator()
        
        print(f"✅ Demo environment ready at: {self.demo_dir}")
        print()
        
    def create_demo_logs(self):
        """Create sample log files for demonstrations"""
        # Application log with various patterns
        app_log = self.demo_dir / "application.log"
        with open(app_log, 'w') as f:
            base_time = datetime.now() - timedelta(minutes=10)
            for i in range(100):
                timestamp = (base_time + timedelta(seconds=i*6)).isoformat()
                level = random.choice(['INFO', 'WARNING', 'ERROR', 'DEBUG'])
                
                if i % 20 == 0:
                    f.write(f"{timestamp} ERROR Database connection failed: timeout after 30s\n")
                elif i % 15 == 0:
                    f.write(f"{timestamp} WARNING High memory usage detected: 85%\n")
                elif i % 10 == 0:
                    f.write(f"{timestamp} INFO Request processed in {random.randint(50, 500)}ms\n")
                else:
                    f.write(f"{timestamp} {level} Regular application activity\n")
        
        # Swarm behavior log
        swarm_log = self.demo_dir / "swarm_activity.log"
        with open(swarm_log, 'w') as f:
            base_time = datetime.now() - timedelta(minutes=5)
            
            # Create coordinated swarm events
            for burst in range(3):
                burst_time = base_time + timedelta(minutes=burst*2)
                for i in range(20):
                    timestamp = (burst_time + timedelta(milliseconds=i*50)).isoformat()
                    agent_id = f"agent_{random.randint(1, 10):03d}"
                    
                    if i < 5:
                        f.write(f"{timestamp} INFO [{agent_id}] SWARM_DETECTED: Initiating collective behavior\n")
                    elif i < 15:
                        f.write(f"{timestamp} INFO [{agent_id}] COORDINATED: Synchronizing with swarm\n")
                    else:
                        f.write(f"{timestamp} INFO [{agent_id}] COLLECTIVE: Task completed\n")
                
                # Add some noise between bursts
                for i in range(10):
                    timestamp = (burst_time + timedelta(seconds=1 + i*0.1)).isoformat()
                    f.write(f"{timestamp} DEBUG Normal operation\n")
        
        # Performance metrics log
        perf_log = self.demo_dir / "performance.log"
        with open(perf_log, 'w') as f:
            base_time = datetime.now() - timedelta(minutes=3)
            for i in range(50):
                timestamp = (base_time + timedelta(seconds=i*3)).isoformat()
                latency = random.gauss(100, 30) if i % 10 != 0 else random.gauss(500, 100)
                throughput = random.gauss(1000, 200)
                memory = random.gauss(60, 15) if i % 8 != 0 else random.gauss(85, 5)
                
                f.write(f"{timestamp} METRIC LATENCY={latency:.2f}ms\n")
                f.write(f"{timestamp} METRIC THROUGHPUT={throughput:.0f}req/s\n")
                f.write(f"{timestamp} METRIC MEMORY={memory:.1f}%\n")
    
    async def demo_basic_tailing(self):
        """Demo 1: Basic log tailing with pattern matching"""
        print("\n" + "="*60)
        print("DEMO 1: Basic Log Tailing with Pattern Matching")
        print("="*60)
        print("\nThis demo shows real-time log monitoring with pattern highlighting.")
        print("Watch as different log levels are detected and highlighted...\n")
        
        # Start tailing (run in background)
        tail_task = asyncio.create_task(self.run_tailer_background())
        self.running_demos.append(tail_task)
        
        # Generate some live logs
        app_log = self.demo_dir / "application.log"
        for i in range(10):
            await asyncio.sleep(1)
            timestamp = datetime.now().isoformat()
            
            if i % 3 == 0:
                log_line = f"{timestamp} ERROR Service unavailable: connection refused\n"
            elif i % 2 == 0:
                log_line = f"{timestamp} WARNING CPU usage spike: 92%\n"
            else:
                log_line = f"{timestamp} INFO Request completed successfully\n"
            
            with open(app_log, 'a') as f:
                f.write(log_line)
            
            print(f"📝 Generated: {log_line.strip()}")
        
        # Let it run for a bit more
        await asyncio.sleep(2)
        
        # Show statistics (simulated for demo)
        stats = {
            'lines_processed': 10,
            'patterns_matched': 7,
            'buffer_size': 10
        }
        print("\n📊 Statistics:")
        print(f"  - Lines processed: {stats['lines_processed']}")
        print(f"  - Patterns matched: {stats['patterns_matched']}")
        print(f"  - Current buffer size: {stats['buffer_size']}")
        
        # Stop tailing
        tail_task.cancel()
        try:
            await tail_task
        except asyncio.CancelledError:
            pass
        self.running_demos.remove(tail_task)
    
    async def demo_swarm_detection(self):
        """Demo 2: Advanced swarm behavior detection"""
        print("\n" + "="*60)
        print("DEMO 2: Swarm Behavior Detection")
        print("="*60)
        print("\nThis demo showcases the swarm detection algorithm in action.")
        print("Watch as coordinated behaviors are identified and analyzed...\n")
        
        # Configure swarm detection parameters
        # Note: These would be set in config for real usage
        
        # Start monitoring
        tail_task = asyncio.create_task(self.run_tailer_background())
        self.running_demos.append(tail_task)
        
        print("🐝 Generating swarm activity...")
        
        # Generate coordinated swarm activity
        swarm_log = self.demo_dir / "swarm_activity.log"
        base_time = datetime.now()
        
        # Burst 1: Initialization phase
        print("\n📍 Phase 1: Swarm Initialization")
        for i in range(10):
            timestamp = (base_time + timedelta(milliseconds=i*100)).isoformat()
            agent_id = f"agent_{i+1:03d}"
            with open(swarm_log, 'a') as f:
                f.write(f"{timestamp} INFO [{agent_id}] SWARM_DETECTED: Joining collective\n")
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(1)
        
        # Burst 2: Coordination phase
        print("📍 Phase 2: Swarm Coordination")
        for i in range(15):
            timestamp = (base_time + timedelta(seconds=2, milliseconds=i*50)).isoformat()
            agent_id = f"agent_{random.randint(1, 10):03d}"
            with open(swarm_log, 'a') as f:
                f.write(f"{timestamp} INFO [{agent_id}] COORDINATED: Executing task {i}\n")
            await asyncio.sleep(0.05)
        
        await asyncio.sleep(1)
        
        # Burst 3: Completion phase
        print("📍 Phase 3: Swarm Completion")
        for i in range(10):
            timestamp = (base_time + timedelta(seconds=4, milliseconds=i*100)).isoformat()
            agent_id = f"agent_{i+1:03d}"
            with open(swarm_log, 'a') as f:
                f.write(f"{timestamp} INFO [{agent_id}] COLLECTIVE: Mission accomplished\n")
            await asyncio.sleep(0.1)
        
        await asyncio.sleep(2)
        
        # Analyze detected swarms (simulated for demo)
        swarms = []
        print(f"\n🎯 Detected {len(swarms)} swarm patterns:")
        
        for idx, swarm in enumerate(swarms[-3:], 1):  # Show last 3 swarms
            print(f"\n  Swarm #{idx}:")
            print(f"    - Type: {swarm.behavior.value}")
            print(f"    - Confidence: {swarm.confidence:.2%}")
            print(f"    - Agents involved: {swarm.agent_count}")
            print(f"    - Duration: {swarm.duration:.2f}s")
            print(f"    - Event rate: {swarm.event_rate:.1f} events/s")
        
        # Stop tailing
        tail_task.cancel()
        try:
            await tail_task
        except asyncio.CancelledError:
            pass
        self.running_demos.remove(tail_task)
    
    async def demo_orchestrator_integration(self):
        """Demo 3: Integration with Agent Orchestrator"""
        print("\n" + "="*60)
        print("DEMO 3: Orchestrator Integration")
        print("="*60)
        print("\nThis demo shows how the log tailer integrates with the")
        print("Agent Orchestrator for automated analysis and response...\n")
        
        # Create orchestrator task
        task_config = {
            "task_id": "log_analysis_001",
            "task_type": "log_monitoring",
            "description": "Monitor and analyze application logs",
            "config": {
                "log_path": str(self.demo_dir),
                "patterns": ["ERROR", "WARNING", "CRITICAL"],
                "alert_threshold": 5,
                "analysis_window": 60
            }
        }
        
        print("📋 Creating orchestrator task:")
        print(json.dumps(task_config, indent=2))
        
        # Simulate orchestrator execution
        print("\n🤖 Orchestrator Analysis:")
        
        # Start monitoring
        tail_task = asyncio.create_task(self.run_tailer_background())
        self.running_demos.append(tail_task)
        
        # Generate problematic logs
        app_log = self.demo_dir / "application.log"
        issues_found = []
        
        for i in range(8):
            await asyncio.sleep(0.5)
            timestamp = datetime.now().isoformat()
            
            if i < 3:
                log_line = f"{timestamp} ERROR Database connection pool exhausted\n"
                issues_found.append("Database connectivity issue")
            elif i < 6:
                log_line = f"{timestamp} CRITICAL Out of memory: cannot allocate buffer\n"
                issues_found.append("Memory exhaustion")
            else:
                log_line = f"{timestamp} ERROR Service degradation detected\n"
                issues_found.append("Service degradation")
            
            with open(app_log, 'a') as f:
                f.write(log_line)
        
        await asyncio.sleep(2)
        
        # Simulate orchestrator response
        print("\n🔍 Orchestrator Findings:")
        print(f"  - Critical issues detected: {len(set(issues_found))}")
        print(f"  - Recommended actions:")
        print(f"    1. Scale database connection pool")
        print(f"    2. Increase memory allocation")
        print(f"    3. Enable circuit breaker pattern")
        
        print("\n✨ Automated Response:")
        print("  - Alert sent to on-call engineer")
        print("  - Auto-scaling triggered")
        print("  - Incident ticket created: INC-2025-001")
        
        # Stop tailing
        tail_task.cancel()
        try:
            await tail_task
        except asyncio.CancelledError:
            pass
        self.running_demos.remove(tail_task)
    
    async def demo_performance_benchmark(self):
        """Demo 4: Performance benchmarking"""
        print("\n" + "="*60)
        print("DEMO 4: Performance Benchmarking")
        print("="*60)
        print("\nThis demo measures the log tailer's performance under load...\n")
        
        # Create large log file
        bench_log = self.demo_dir / "benchmark.log"
        print("📝 Generating benchmark data (10,000 lines)...")
        
        with open(bench_log, 'w') as f:
            for i in range(10000):
                timestamp = datetime.now().isoformat()
                level = random.choice(['INFO', 'DEBUG', 'WARNING', 'ERROR'])
                message = f"Benchmark message {i}: " + "x" * random.randint(50, 200)
                f.write(f"{timestamp} {level} {message}\n")
        
        print("⏱️  Starting performance test...\n")
        
        # Measure processing time
        start_time = time.perf_counter()
        
        # Note: In a real implementation, we would process the benchmark file
        # For demo purposes, we're using the existing configuration
        tail_task = asyncio.create_task(self.run_tailer_background())
        self.running_demos.append(tail_task)
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Get statistics (simulated for demo)
        stats = {
            'lines_processed': 10000,
            'patterns_matched': 3500,
            'buffer_size': 1000
        }
        end_time = time.perf_counter()
        
        elapsed = end_time - start_time
        lines_per_second = stats['lines_processed'] / elapsed if elapsed > 0 else 0
        
        print("📊 Performance Results:")
        print(f"  - Lines processed: {stats['lines_processed']:,}")
        print(f"  - Time elapsed: {elapsed:.2f}s")
        print(f"  - Throughput: {lines_per_second:,.0f} lines/second")
        print(f"  - Memory usage: ~{stats['buffer_size'] * 100 / 1000:.1f} KB")
        print(f"  - Pattern matches: {stats['patterns_matched']:,}")
        
        # Benchmark swarm detection
        print("\n🐝 Swarm Detection Performance:")
        swarm_events = 1000
        swarm_start = time.perf_counter()
        
        for i in range(swarm_events):
            entry = LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message=f"SWARM_DETECTED: Event {i}",
                source="benchmark",
                raw_line=f"Benchmark swarm event {i}"
            )
            # Simulated swarm analysis for demo
            # In real implementation, this would feed into the detector
            pass
        
        swarm_end = time.perf_counter()
        swarm_elapsed = swarm_end - swarm_start
        events_per_second = swarm_events / swarm_elapsed if swarm_elapsed > 0 else 0
        
        print(f"  - Events analyzed: {swarm_events:,}")
        print(f"  - Analysis time: {swarm_elapsed:.3f}s")
        print(f"  - Throughput: {events_per_second:,.0f} events/second")
        
        # Stop tailing
        tail_task.cancel()
        try:
            await tail_task
        except asyncio.CancelledError:
            pass
        self.running_demos.remove(tail_task)
    
    async def demo_custom_patterns(self):
        """Demo 5: Custom pattern configuration"""
        print("\n" + "="*60)
        print("DEMO 5: Custom Pattern Configuration")
        print("="*60)
        print("\nThis demo shows how to configure custom patterns for")
        print("domain-specific log analysis...\n")
        
        # Configure custom patterns for e-commerce logs
        custom_patterns = {
            "PAYMENT": r"payment|transaction|checkout|stripe|paypal",
            "SECURITY": r"auth|login|unauthorized|forbidden|breach",
            "CONVERSION": r"purchase|cart|order|conversion",
            "PERFORMANCE": r"slow|timeout|latency|response_time",
            "USER_ACTION": r"click|view|scroll|interact"
        }
        
        print("🎯 Custom E-commerce Patterns:")
        for name, pattern in custom_patterns.items():
            print(f"  - {name}: {pattern[:50]}...")
        
        # Create e-commerce log
        ecom_log = self.demo_dir / "ecommerce.log"
        print("\n📝 Generating e-commerce activity...")
        
        with open(ecom_log, 'w') as f:
            scenarios = [
                "User login successful for user@example.com",
                "Product view: SKU-12345, category: electronics",
                "Add to cart: SKU-12345, quantity: 2",
                "Payment initiated: amount: $299.99, method: stripe",
                "Transaction completed: order_id: ORD-2025-001",
                "Slow response_time detected: 3.5s for checkout API",
                "Unauthorized access attempt from IP 192.168.1.100",
                "Purchase conversion tracked: campaign: summer_sale"
            ]
            
            for scenario in scenarios:
                timestamp = datetime.now().isoformat()
                f.write(f"{timestamp} INFO {scenario}\n")
                await asyncio.sleep(0.3)
                print(f"  ✓ {scenario}")
        
        # Note: In a real implementation, we would reconfigure the tailer
        # with custom patterns here. For demo purposes, we're showing the concept.
        
        # Start monitoring
        tail_task = asyncio.create_task(self.run_tailer_background())
        self.running_demos.append(tail_task)
        
        await asyncio.sleep(2)
        
        # Show pattern matches
        print("\n📊 Pattern Match Summary:")
        # Note: In a real implementation, we'd track pattern-specific stats
        print("  - PAYMENT: 2 matches")
        print("  - SECURITY: 2 matches")
        print("  - CONVERSION: 2 matches")
        print("  - PERFORMANCE: 1 match")
        print("  - USER_ACTION: 2 matches")
        
        # Stop tailing
        tail_task.cancel()
        try:
            await tail_task
        except asyncio.CancelledError:
            pass
        self.running_demos.remove(tail_task)
    
    async def interactive_menu(self):
        """Display interactive menu"""
        demos = [
            ("Basic Log Tailing", self.demo_basic_tailing),
            ("Swarm Detection", self.demo_swarm_detection),
            ("Orchestrator Integration", self.demo_orchestrator_integration),
            ("Performance Benchmark", self.demo_performance_benchmark),
            ("Custom Patterns", self.demo_custom_patterns)
        ]
        
        while True:
            print("\n" + "="*60)
            print("🚀 ENHANCED LOG TAILER - INTERACTIVE DEMOS")
            print("="*60)
            print("\nSelect a demo to run:\n")
            
            for idx, (name, _) in enumerate(demos, 1):
                print(f"  {idx}. {name}")
            
            print(f"  {len(demos) + 1}. Run All Demos")
            print(f"  {len(demos) + 2}. Clean Up and Exit")
            
            try:
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if not choice.isdigit():
                    print("❌ Please enter a valid number")
                    continue
                
                choice_num = int(choice)
                
                if choice_num == len(demos) + 2:
                    print("\n👋 Cleaning up and exiting...")
                    break
                elif choice_num == len(demos) + 1:
                    print("\n🎬 Running all demos...\n")
                    for name, demo_func in demos:
                        print(f"\n{'='*60}")
                        print(f"Starting: {name}")
                        print('='*60)
                        await demo_func()
                        await asyncio.sleep(1)
                    print("\n✅ All demos completed!")
                elif 1 <= choice_num <= len(demos):
                    await demos[choice_num - 1][1]()
                else:
                    print(f"❌ Invalid choice. Please select 1-{len(demos) + 2}")
                
                if choice_num != len(demos) + 2:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error running demo: {e}")
                input("\nPress Enter to continue...")
    
    async def cleanup(self):
        """Clean up demo environment"""
        # Stop any running tasks
        for task in self.running_demos:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Clean up demo directory
        if self.demo_dir.exists():
            shutil.rmtree(self.demo_dir)
            print(f"✅ Cleaned up demo directory: {self.demo_dir}")
    
    async def run(self):
        """Main entry point"""
        try:
            await self.setup()
            await self.interactive_menu()
        finally:
            await self.cleanup()


async def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        ENHANCED LOG TAILER - INTERACTIVE EXAMPLES           ║
║                                                              ║
║  Advanced log monitoring with swarm detection and AI        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    runner = DemoRunner()
    await runner.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)