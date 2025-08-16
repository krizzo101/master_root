#!/usr/bin/env python3
"""
Clear and accurate parallel execution test
All timing collected by Python, all API responses verified
"""
import subprocess
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class ClearTimingTest:
    """Test parallel execution with clear, accurate timing"""
    
    def __init__(self):
        self.test_start_time = time.perf_counter()
        self.test_start_timestamp = datetime.now()
        
    def get_elapsed(self) -> float:
        """Get seconds elapsed since test start"""
        return time.perf_counter() - self.test_start_time
    
    def execute_claude_task(self, task: str, label: str, token_env_var: str) -> Dict[str, Any]:
        """Execute a single Claude task and return all data"""
        
        # Record when we start THIS task
        task_start = time.perf_counter()
        task_start_elapsed = self.get_elapsed()
        
        # Build command
        cmd = [
            'claude',
            '--model', 'sonnet',
            '--dangerously-skip-permissions',
            '--output-format', 'json',
            '-p', task
        ]
        
        # Set environment with specific token
        env = os.environ.copy()
        if token_env_var in os.environ:
            env['CLAUDE_CODE_TOKEN'] = os.environ[token_env_var]
        
        print(f"[{task_start_elapsed:7.2f}s] Starting {label} with {token_env_var}")
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Record completion
            task_end = time.perf_counter()
            task_end_elapsed = self.get_elapsed()
            task_duration = task_end - task_start
            
            # Parse API response
            api_data = None
            if result.returncode == 0 and result.stdout:
                try:
                    api_data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass
            
            print(f"[{task_end_elapsed:7.2f}s] Completed {label} - Duration: {task_duration:.2f}s")
            
            return {
                'label': label,
                'start_elapsed': task_start_elapsed,
                'end_elapsed': task_end_elapsed,
                'duration': task_duration,
                'success': result.returncode == 0,
                'api_response': api_data,
                'session_id': api_data.get('session_id') if api_data else None,
                'api_cost': api_data.get('total_cost_usd') if api_data else None,
                'api_duration_ms': api_data.get('duration_api_ms') if api_data else None,
                'tokens': {
                    'input': api_data.get('usage', {}).get('input_tokens', 0) if api_data else 0,
                    'output': api_data.get('usage', {}).get('output_tokens', 0) if api_data else 0
                } if api_data else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'label': label,
                'start_elapsed': task_start_elapsed,
                'end_elapsed': self.get_elapsed(),
                'duration': self.get_elapsed() - task_start_elapsed,
                'success': False,
                'error': 'timeout'
            }
    
    def run_sequential_test(self) -> List[Dict[str, Any]]:
        """Run 3 tasks sequentially"""
        print("\n" + "="*70)
        print("SEQUENTIAL EXECUTION TEST")
        print("="*70)
        
        tasks = [
            ("Create file /tmp/seq_a.txt with content 'SEQ_A'", "SEQ_A", "CLAUDE_CODE_TOKEN"),
            ("Create file /tmp/seq_b.txt with content 'SEQ_B'", "SEQ_B", "CLAUDE_CODE_TOKEN1"),
            ("Create file /tmp/seq_c.txt with content 'SEQ_C'", "SEQ_C", "CLAUDE_CODE_TOKEN2")
        ]
        
        results = []
        for task, label, token in tasks:
            result = self.execute_claude_task(task, label, token)
            results.append(result)
        
        return results
    
    def run_parallel_test(self) -> List[Dict[str, Any]]:
        """Run 3 tasks in parallel"""
        print("\n" + "="*70)
        print("PARALLEL EXECUTION TEST")
        print("="*70)
        
        parallel_start = self.get_elapsed()
        print(f"[{parallel_start:7.2f}s] Spawning 3 parallel processes")
        
        # Start all processes
        processes = []
        for i, (task, label) in enumerate([
            ("Create file /tmp/par_a.txt with content 'PAR_A'", "PAR_A"),
            ("Create file /tmp/par_b.txt with content 'PAR_B'", "PAR_B"),
            ("Create file /tmp/par_c.txt with content 'PAR_C'", "PAR_C")
        ]):
            cmd = [
                'claude',
                '--model', 'sonnet',
                '--dangerously-skip-permissions',
                '--output-format', 'json',
                '-p', task
            ]
            
            # Use different token for each
            env = os.environ.copy()
            token_var = ['CLAUDE_CODE_TOKEN', 'CLAUDE_CODE_TOKEN1', 'CLAUDE_CODE_TOKEN2'][i]
            if token_var in os.environ:
                env['CLAUDE_CODE_TOKEN'] = os.environ[token_var]
            
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            processes.append({
                'proc': proc,
                'label': label,
                'token': token_var,
                'start_time': time.perf_counter(),
                'start_elapsed': self.get_elapsed()
            })
            
            print(f"[{self.get_elapsed():7.2f}s] Spawned {label} with {token_var}")
        
        print(f"[{self.get_elapsed():7.2f}s] All processes spawned, waiting for completion...")
        
        # Wait for all to complete
        results = []
        for p in processes:
            stdout, stderr = p['proc'].communicate()
            end_time = time.perf_counter()
            end_elapsed = self.get_elapsed()
            duration = end_time - p['start_time']
            
            # Parse API response
            api_data = None
            if p['proc'].returncode == 0 and stdout:
                try:
                    api_data = json.loads(stdout)
                except json.JSONDecodeError:
                    pass
            
            print(f"[{end_elapsed:7.2f}s] Completed {p['label']} - Duration: {duration:.2f}s")
            
            results.append({
                'label': p['label'],
                'start_elapsed': p['start_elapsed'],
                'end_elapsed': end_elapsed,
                'duration': duration,
                'success': p['proc'].returncode == 0,
                'api_response': api_data,
                'session_id': api_data.get('session_id') if api_data else None,
                'api_cost': api_data.get('total_cost_usd') if api_data else None,
                'api_duration_ms': api_data.get('duration_api_ms') if api_data else None,
                'tokens': {
                    'input': api_data.get('usage', {}).get('input_tokens', 0) if api_data else 0,
                    'output': api_data.get('usage', {}).get('output_tokens', 0) if api_data else 0
                } if api_data else None
            })
        
        return results
    
    def print_results(self, seq_results: List[Dict], par_results: List[Dict]):
        """Print clear, unambiguous results"""
        
        print("\n" + "="*70)
        print("RESULTS SUMMARY")
        print("="*70)
        
        # Sequential Results
        print("\nSequential Execution Results:")
        print("-" * 50)
        seq_total = 0
        for r in seq_results:
            print(f"Task {r['label']}:")
            print(f"  Started at: {r['start_elapsed']:.2f}s from test start")
            print(f"  Completed at: {r['end_elapsed']:.2f}s from test start")
            print(f"  Duration: {r['duration']:.2f}s")
            if r.get('session_id'):
                print(f"  Session ID: {r['session_id']}")
                print(f"  API Cost: ${r.get('api_cost', 0):.4f}")
                print(f"  Tokens: {r['tokens']['input']} in, {r['tokens']['output']} out")
            else:
                print(f"  Status: FAILED")
            seq_total = max(seq_total, r['end_elapsed'])
        
        print(f"\nTotal Sequential Time: {seq_total:.2f} seconds")
        
        # Parallel Results
        print("\nParallel Execution Results:")
        print("-" * 50)
        par_max_duration = 0
        par_max_elapsed = 0
        for r in par_results:
            print(f"Task {r['label']}:")
            print(f"  Started at: {r['start_elapsed']:.2f}s from test start")
            print(f"  Completed at: {r['end_elapsed']:.2f}s from test start")
            print(f"  Duration: {r['duration']:.2f}s")
            if r.get('session_id'):
                print(f"  Session ID: {r['session_id']}")
                print(f"  API Cost: ${r.get('api_cost', 0):.4f}")
                print(f"  Tokens: {r['tokens']['input']} in, {r['tokens']['output']} out")
            else:
                print(f"  Status: FAILED")
            par_max_duration = max(par_max_duration, r['duration'])
            par_max_elapsed = max(par_max_elapsed, r['end_elapsed'])
        
        print(f"\nTotal Parallel Time: {par_max_duration:.2f} seconds (longest task)")
        
        # Performance Analysis
        print("\n" + "="*70)
        print("PERFORMANCE ANALYSIS")
        print("="*70)
        
        # Calculate sequential task time (just the tasks, not the whole test)
        seq_task_time = sum(r['duration'] for r in seq_results)
        
        print(f"Sequential Task Time (sum of durations): {seq_task_time:.2f}s")
        print(f"Parallel Task Time (max duration): {par_max_duration:.2f}s")
        
        if par_max_duration > 0:
            speedup = seq_task_time / par_max_duration
            efficiency = (speedup / 3.0) * 100  # 3 tokens theoretical max
            
            print(f"Speedup Factor: {speedup:.2f}x")
            print(f"Parallelism Efficiency: {efficiency:.1f}%")
            
            if speedup >= 2.5:
                print("\n✅ TRUE PARALLEL EXECUTION CONFIRMED")
            elif speedup >= 1.5:
                print("\n⚠️ PARTIAL PARALLELISM DETECTED")
            else:
                print("\n❌ SEQUENTIAL OR MINIMAL PARALLELISM")
        
        # API Verification
        print("\n" + "="*70)
        print("API CALL VERIFICATION")
        print("="*70)
        
        all_results = seq_results + par_results
        session_ids = [r['session_id'] for r in all_results if r.get('session_id')]
        total_cost = sum(r.get('api_cost', 0) for r in all_results if r.get('api_cost'))
        
        print(f"Total API Calls Made: {len(session_ids)}")
        print(f"Unique Session IDs: {len(set(session_ids))}")
        print(f"Total API Cost: ${total_cost:.4f}")
        
        if len(session_ids) > 0:
            print("\nSession IDs (proving real API calls):")
            for sid in session_ids[:6]:  # Show first 6
                print(f"  - {sid}")
    
    def save_detailed_report(self, seq_results: List[Dict], par_results: List[Dict]):
        """Save detailed JSON report"""
        report = {
            'test_metadata': {
                'start_time': self.test_start_timestamp.isoformat(),
                'total_duration': self.get_elapsed(),
            },
            'sequential_results': seq_results,
            'parallel_results': par_results,
            'performance_metrics': {
                'sequential_sum': sum(r['duration'] for r in seq_results),
                'parallel_max': max(r['duration'] for r in par_results) if par_results else 0,
                'speedup': sum(r['duration'] for r in seq_results) / max(r['duration'] for r in par_results) if par_results else 0
            }
        }
        
        filename = f"/tmp/clear_timing_report_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: {filename}")
        return filename


def main():
    """Run the clear timing test"""
    print("="*70)
    print("CLEAR PARALLEL EXECUTION TIMING TEST")
    print("Testing with real API calls and accurate timing")
    print("="*70)
    
    # Clean up old files
    subprocess.run("rm -f /tmp/seq_*.txt /tmp/par_*.txt", shell=True)
    
    # Run test
    test = ClearTimingTest()
    
    # Sequential test
    seq_results = test.run_sequential_test()
    
    # Parallel test
    par_results = test.run_parallel_test()
    
    # Print results
    test.print_results(seq_results, par_results)
    
    # Save report
    test.save_detailed_report(seq_results, par_results)


if __name__ == "__main__":
    main()