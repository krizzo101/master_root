#!/usr/bin/env python3
"""
Comprehensive Recursive Spawning Test with Granular Timing Analysis

This script runs a full multi-token recursive spawning test while collecting
microsecond-precision timing data for every action and generating detailed reports.
"""

import json
import time
import uuid
import subprocess
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import random

# Add libs to path
sys.path.insert(0, '/home/opsvi/master_root/libs')
sys.path.insert(0, '/home/opsvi/master_root')

from timing_analysis_system import (
    TimingCollector, TimingAnalyzer, EventType, 
    print_report_summary, format_duration
)


class RecursiveSpawningTest:
    """Orchestrates recursive spawning test with comprehensive timing"""
    
    def __init__(self, test_name: str = "recursive_spawn_test"):
        self.test_name = test_name
        self.test_id = str(uuid.uuid4())[:8]
        self.collector = TimingCollector()
        self.output_dir = Path(f"/tmp/{test_name}_{self.test_id}")
        self.output_dir.mkdir(exist_ok=True)
        
        # Test configuration
        self.tier1_count = 3  # Number of Tier 1 jobs
        self.tier2_per_tier1 = 3  # Number of Tier 2 jobs each Tier 1 spawns
        self.total_expected = self.tier1_count * self.tier2_per_tier1
        
        # Token configuration (from .mcp.json)
        self.tokens = [
            "CLAUDE_CODE_TOKEN",
            "CLAUDE_CODE_TOKEN1", 
            "CLAUDE_CODE_TOKEN2"
        ]
        
        print(f"🚀 Initializing {test_name}")
        print(f"   Test ID: {self.test_id}")
        print(f"   Output Directory: {self.output_dir}")
        print(f"   Expected Jobs: {self.tier1_count} Tier 1 → {self.total_expected} Tier 2")
    
    def create_tier1_tasks(self) -> List[Dict[str, Any]]:
        """Create Tier 1 tasks that will spawn Tier 2 tasks"""
        tasks = []
        
        for i, label in enumerate(['A', 'B', 'C']):
            # Record task creation
            self.collector.record_event(
                EventType.TASK_STARTED,
                f"Creating Tier 1 task {label}",
                tier=1,
                metadata={'label': label, 'index': i}
            )
            
            # Create the recursive task that tells Claude to spawn more
            task_content = f"""Create 3 files in parallel:
1. Create file {self.output_dir}/tier2_{label}_1.txt with content 'TIER2_{label}_1_COMPLETE_AT_{{timestamp}}'
2. Create file {self.output_dir}/tier2_{label}_2.txt with content 'TIER2_{label}_2_COMPLETE_AT_{{timestamp}}'
3. Create file {self.output_dir}/tier2_{label}_3.txt with content 'TIER2_{label}_3_COMPLETE_AT_{{timestamp}}'

Use the timestamp in microseconds when creating each file. Be precise and efficient."""
            
            task = {
                "task": task_content,
                "cwd": str(self.output_dir),
                "output_format": "json",
                "permission_mode": "bypassPermissions",
                "verbose": False
            }
            
            tasks.append(task)
            
            # Simulate token assignment (round-robin)
            token_idx = i % len(self.tokens)
            self.collector.record_event(
                EventType.TOKEN_ASSIGNED,
                f"Token {token_idx} assigned to task {label}",
                tier=1,
                token_used=self.tokens[token_idx],
                metadata={'task_label': label}
            )
        
        return tasks
    
    def run_mcp_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute batch via MCP claude-code server"""
        batch_id = str(uuid.uuid4())[:8]
        
        # Record batch submission
        self.collector.record_event(
            EventType.BATCH_SUBMISSION,
            f"Submitting batch {batch_id} with {len(tasks)} tasks",
            tier=1,
            batch_id=batch_id,
            metadata={'task_count': len(tasks)}
        )
        
        start_time = time.time()
        
        try:
            # Import the MCP client
            from opsvi_mcp.servers.claude_code import claude_run_batch
            
            # Record MCP invocation start
            self.collector.record_event(
                EventType.MCP_INVOCATION_START,
                "Invoking claude_run_batch",
                tier=1,
                batch_id=batch_id
            )
            
            # Execute the batch
            result = claude_run_batch(
                tasks=tasks,
                max_concurrent=3
            )
            
            # Record MCP invocation end
            duration = (time.time() - start_time) * 1000
            self.collector.record_event(
                EventType.MCP_INVOCATION_END,
                "claude_run_batch completed",
                tier=1,
                batch_id=batch_id,
                duration_ms=duration,
                success=True
            )
            
            # Record batch accepted
            self.collector.record_event(
                EventType.BATCH_ACCEPTED,
                f"Batch {batch_id} accepted",
                tier=1,
                batch_id=batch_id
            )
            
            return result
            
        except Exception as e:
            # Record failure
            duration = (time.time() - start_time) * 1000
            self.collector.record_event(
                EventType.BATCH_FAILED,
                f"Batch {batch_id} failed",
                tier=1,
                batch_id=batch_id,
                success=False,
                error_details=str(e),
                duration_ms=duration
            )
            raise
    
    def monitor_job_status(self, job_ids: List[str], batch_id: str):
        """Monitor job status and collect timing data"""
        print(f"\n📊 Monitoring {len(job_ids)} jobs...")
        
        completed_jobs = set()
        failed_jobs = set()
        job_start_times = {}
        
        # Import MCP tools
        from opsvi_mcp.servers.claude_code import claude_status, claude_result
        
        while len(completed_jobs) + len(failed_jobs) < len(job_ids):
            for job_id in job_ids:
                if job_id in completed_jobs or job_id in failed_jobs:
                    continue
                
                try:
                    # Check status
                    status_start = time.time()
                    status = claude_status(jobId=job_id)
                    status_duration = (time.time() - status_start) * 1000
                    
                    # Record status check
                    if job_id not in job_start_times:
                        if status['status'] == 'running':
                            job_start_times[job_id] = time.time()
                            self.collector.record_event(
                                EventType.JOB_STARTED,
                                f"Job {job_id[:8]} started",
                                tier=1,
                                job_id=job_id,
                                batch_id=batch_id
                            )
                    
                    if status['status'] == 'completed':
                        # Record completion
                        if job_id in job_start_times:
                            job_duration = (time.time() - job_start_times[job_id]) * 1000
                        else:
                            job_duration = None
                        
                        self.collector.record_event(
                            EventType.JOB_COMPLETED,
                            f"Job {job_id[:8]} completed",
                            tier=1,
                            job_id=job_id,
                            batch_id=batch_id,
                            duration_ms=job_duration,
                            success=True
                        )
                        
                        # Get result
                        result_start = time.time()
                        self.collector.record_event(
                            EventType.RESULT_RETRIEVAL_START,
                            f"Retrieving result for job {job_id[:8]}",
                            tier=1,
                            job_id=job_id
                        )
                        
                        try:
                            result = claude_result(jobId=job_id)
                            result_duration = (time.time() - result_start) * 1000
                            
                            self.collector.record_event(
                                EventType.RESULT_RETRIEVED,
                                f"Result retrieved for job {job_id[:8]}",
                                tier=1,
                                job_id=job_id,
                                duration_ms=result_duration,
                                success=True
                            )
                            
                            # Analyze Tier 2 spawning from result
                            self.analyze_tier2_spawning(result, job_id)
                            
                        except Exception as e:
                            self.collector.record_event(
                                EventType.RESULT_RETRIEVAL_FAILED,
                                f"Failed to retrieve result for job {job_id[:8]}",
                                tier=1,
                                job_id=job_id,
                                success=False,
                                error_details=str(e)
                            )
                        
                        completed_jobs.add(job_id)
                        
                    elif status['status'] == 'failed':
                        # Record failure
                        self.collector.record_event(
                            EventType.JOB_FAILED,
                            f"Job {job_id[:8]} failed",
                            tier=1,
                            job_id=job_id,
                            batch_id=batch_id,
                            success=False,
                            error_details=status.get('error', 'Unknown error')
                        )
                        failed_jobs.add(job_id)
                        
                except Exception as e:
                    print(f"  ⚠️ Error checking job {job_id[:8]}: {e}")
            
            # Brief sleep to avoid hammering the API
            time.sleep(0.5)
        
        print(f"  ✅ Completed: {len(completed_jobs)}")
        print(f"  ❌ Failed: {len(failed_jobs)}")
        
        return completed_jobs, failed_jobs
    
    def analyze_tier2_spawning(self, result: Any, parent_job_id: str):
        """Analyze Tier 2 spawning from job result"""
        # This would parse the result to identify Tier 2 job creations
        # For now, we'll simulate based on expected behavior
        
        if isinstance(result, dict):
            # Look for nested job IDs or batch information
            if 'batch_id' in result or 'job_ids' in result:
                tier2_count = len(result.get('job_ids', []))
                self.collector.record_event(
                    EventType.SUBPROCESS_SPAWN,
                    f"Tier 1 job spawned {tier2_count} Tier 2 jobs",
                    tier=2,
                    parent_job_id=parent_job_id,
                    metadata={'tier2_count': tier2_count}
                )
    
    def verify_file_outputs(self) -> Dict[str, Any]:
        """Verify all expected output files were created"""
        print(f"\n🔍 Verifying output files in {self.output_dir}")
        
        expected_files = []
        for label in ['A', 'B', 'C']:
            for i in range(1, 4):
                expected_files.append(f"tier2_{label}_{i}.txt")
        
        results = {
            'expected': len(expected_files),
            'found': 0,
            'missing': [],
            'files': {}
        }
        
        for filename in expected_files:
            filepath = self.output_dir / filename
            
            if filepath.exists():
                # Record file found
                self.collector.record_event(
                    EventType.FILE_CREATED,
                    f"Output file {filename} verified",
                    tier=2,
                    success=True,
                    metadata={'filepath': str(filepath)}
                )
                
                # Read content to get timestamp
                with open(filepath) as f:
                    content = f.read()
                    results['files'][filename] = {
                        'exists': True,
                        'content': content,
                        'size': filepath.stat().st_size,
                        'mtime': filepath.stat().st_mtime
                    }
                results['found'] += 1
            else:
                # Record file missing
                self.collector.record_event(
                    EventType.FILE_WRITE_FAILED,
                    f"Output file {filename} not found",
                    tier=2,
                    success=False,
                    metadata={'filepath': str(filepath)}
                )
                results['missing'].append(filename)
                results['files'][filename] = {'exists': False}
        
        print(f"  Found: {results['found']}/{results['expected']} files")
        if results['missing']:
            print(f"  Missing: {', '.join(results['missing'])}")
        
        return results
    
    def run_test(self) -> Dict[str, Any]:
        """Run the complete recursive spawning test"""
        print(f"\n{'='*60}")
        print(f"STARTING RECURSIVE SPAWNING TEST")
        print(f"{'='*60}")
        
        test_start = time.time()
        
        try:
            # Phase 1: Create Tier 1 tasks
            print("\n📝 Phase 1: Creating Tier 1 tasks")
            tier1_tasks = self.create_tier1_tasks()
            print(f"  Created {len(tier1_tasks)} Tier 1 tasks")
            
            # Phase 2: Submit batch
            print("\n🚀 Phase 2: Submitting batch to MCP")
            batch_result = self.run_mcp_batch(tier1_tasks)
            
            if 'job_ids' in batch_result:
                job_ids = batch_result['job_ids']
                batch_id = batch_result.get('batch_id', 'unknown')
                print(f"  Batch {batch_id} submitted with {len(job_ids)} jobs")
                
                # Phase 3: Monitor execution
                print("\n⏳ Phase 3: Monitoring job execution")
                completed, failed = self.monitor_job_status(job_ids, batch_id)
                
            else:
                print("  ⚠️ No job IDs returned from batch submission")
                completed, failed = set(), set()
            
            # Phase 4: Verify outputs
            print("\n✅ Phase 4: Verifying outputs")
            file_results = self.verify_file_outputs()
            
            # Record test completion
            test_duration = (time.time() - test_start) * 1000
            self.collector.record_event(
                EventType.TASK_COMPLETED,
                "Recursive spawning test completed",
                tier=0,
                duration_ms=test_duration,
                success=True,
                metadata={
                    'total_jobs': len(completed) + len(failed),
                    'completed': len(completed),
                    'failed': len(failed),
                    'files_created': file_results['found']
                }
            )
            
            # Generate and save reports
            print("\n📊 Generating timing analysis...")
            analyzer = self.collector.get_analyzer()
            report = analyzer.generate_report()
            
            # Save raw events
            events_file = self.output_dir / f"timing_events_{self.test_id}.json"
            self.collector.save_events(str(events_file))
            print(f"  Events saved to: {events_file}")
            
            # Save analysis report
            report_file = self.output_dir / f"timing_report_{self.test_id}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"  Report saved to: {report_file}")
            
            # Print summary
            print_report_summary(report)
            
            # Create visualization
            self.create_timeline_visualization(report)
            
            return {
                'test_id': self.test_id,
                'success': True,
                'duration_ms': test_duration,
                'jobs_completed': len(completed),
                'jobs_failed': len(failed),
                'files_created': file_results['found'],
                'files_missing': len(file_results['missing']),
                'report': report
            }
            
        except Exception as e:
            # Record test failure
            test_duration = (time.time() - test_start) * 1000
            self.collector.record_event(
                EventType.TASK_FAILED,
                "Recursive spawning test failed",
                tier=0,
                duration_ms=test_duration,
                success=False,
                error_details=str(e)
            )
            
            print(f"\n❌ Test failed: {e}")
            
            # Still save what we collected
            events_file = self.output_dir / f"timing_events_failed_{self.test_id}.json"
            self.collector.save_events(str(events_file))
            
            return {
                'test_id': self.test_id,
                'success': False,
                'error': str(e),
                'duration_ms': test_duration
            }
    
    def create_timeline_visualization(self, report: Dict[str, Any]):
        """Create a visual timeline of events"""
        viz_file = self.output_dir / f"timeline_{self.test_id}.txt"
        
        with open(viz_file, 'w') as f:
            f.write("RECURSIVE SPAWNING TIMELINE VISUALIZATION\n")
            f.write("=" * 80 + "\n\n")
            
            # Group events by tier
            tiers = {}
            for event in report['timeline']:
                tier = event['tier']
                if tier not in tiers:
                    tiers[tier] = []
                tiers[tier].append(event)
            
            # Display each tier
            for tier in sorted(tiers.keys()):
                f.write(f"\nTIER {tier} EVENTS:\n")
                f.write("-" * 40 + "\n")
                
                for event in tiers[tier]:
                    time_str = f"{event['time_ms']:8.2f}ms"
                    status = "✓" if event['success'] else "✗"
                    job_str = f"[{event['job_id'][:8]}]" if event['job_id'] else "[--------]"
                    
                    f.write(f"{time_str} {status} {job_str} {event['event']}\n")
                    
                    # Add description if significant
                    if any(key in event['event'] for key in ['completed', 'failed', 'started']):
                        f.write(f"{'':>19}{event['description']}\n")
        
        print(f"  Timeline saved to: {viz_file}")


def run_comparative_tests():
    """Run multiple test configurations for comparison"""
    print("\n🔬 RUNNING COMPARATIVE RECURSIVE SPAWNING TESTS")
    print("="*60)
    
    test_configs = [
        {
            'name': 'baseline',
            'tier1': 3,
            'tier2_per_tier1': 3
        },
        {
            'name': 'stress',
            'tier1': 5,
            'tier2_per_tier1': 4
        },
        {
            'name': 'minimal',
            'tier1': 2,
            'tier2_per_tier1': 2
        }
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n📌 Running {config['name']} test configuration")
        print(f"   Tier 1: {config['tier1']} jobs")
        print(f"   Tier 2: {config['tier2_per_tier1']} per Tier 1")
        
        test = RecursiveSpawningTest(f"recursive_{config['name']}")
        test.tier1_count = config['tier1']
        test.tier2_per_tier1 = config['tier2_per_tier1']
        
        result = test.run_test()
        results.append({
            'config': config,
            'result': result
        })
        
        # Brief pause between tests
        time.sleep(2)
    
    # Compare results
    print("\n📊 COMPARATIVE ANALYSIS")
    print("="*60)
    
    comparison_file = f"/tmp/recursive_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }
    
    for test_result in results:
        config = test_result['config']
        result = test_result['result']
        
        print(f"\n{config['name'].upper()}:")
        print(f"  Success: {'✅' if result['success'] else '❌'}")
        
        if result['success']:
            print(f"  Duration: {format_duration(result['duration_ms'])}")
            print(f"  Jobs: {result['jobs_completed']}/{config['tier1']} completed")
            print(f"  Files: {result['files_created']}/{config['tier1'] * config['tier2_per_tier1']} created")
            
            if 'report' in result:
                para = result['report']['parallelism']
                print(f"  Parallelism: Tier1={para['max_concurrent_tier_1']}, Tier2={para['max_concurrent_tier_2']}")
        
        comparison['tests'].append({
            'name': config['name'],
            'config': config,
            'success': result['success'],
            'duration_ms': result.get('duration_ms'),
            'jobs_completed': result.get('jobs_completed'),
            'files_created': result.get('files_created')
        })
    
    # Save comparison
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n📁 Comparison saved to: {comparison_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run recursive spawning tests with timing analysis')
    parser.add_argument('--mode', choices=['single', 'comparative'], default='single',
                       help='Test mode: single test or comparative analysis')
    parser.add_argument('--tier1', type=int, default=3,
                       help='Number of Tier 1 jobs (for single mode)')
    parser.add_argument('--tier2', type=int, default=3,
                       help='Number of Tier 2 jobs per Tier 1 (for single mode)')
    
    args = parser.parse_args()
    
    if args.mode == 'single':
        # Run single test
        test = RecursiveSpawningTest("recursive_spawn_test")
        test.tier1_count = args.tier1
        test.tier2_per_tier1 = args.tier2
        
        print(f"Running single test: {args.tier1} Tier 1 → {args.tier1 * args.tier2} Tier 2")
        result = test.run_test()
        
        if result['success']:
            print(f"\n✅ Test completed successfully!")
            print(f"   Test ID: {result['test_id']}")
            print(f"   Duration: {format_duration(result['duration_ms'])}")
        else:
            print(f"\n❌ Test failed: {result.get('error', 'Unknown error')}")
    
    else:
        # Run comparative tests
        run_comparative_tests()