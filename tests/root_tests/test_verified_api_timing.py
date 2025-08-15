#!/usr/bin/env python3
"""
Verified API timing test - captures actual API response data
All timing and API data is collected directly by Python code, not reported by agents
"""
import subprocess
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any
import hashlib

class VerifiedAPITimingCollector:
    """Collects verifiable API response data and timing"""
    
    def __init__(self):
        self.start_time = time.perf_counter()
        self.start_timestamp = time.time()
        self.events = []
        
    def get_elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds"""
        return (time.perf_counter() - self.start_time) * 1000
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log an event with timestamp and data"""
        event = {
            "event_type": event_type,
            "timestamp": time.time(),
            "elapsed_ms": self.get_elapsed_ms(),
            "timestamp_readable": datetime.now().isoformat(),
            "data": data
        }
        self.events.append(event)
        
        # Print progress
        print(f"[{event['elapsed_ms']:8.2f}ms] {event_type}")
        
        return event
    
    def save_report(self, filepath: str) -> Dict[str, Any]:
        """Save complete report with all verifiable data"""
        report = {
            "test_metadata": {
                "start_timestamp": self.start_timestamp,
                "start_time_readable": datetime.fromtimestamp(self.start_timestamp).isoformat(),
                "end_timestamp": time.time(),
                "end_time_readable": datetime.now().isoformat(),
                "total_duration_ms": self.get_elapsed_ms(),
                "total_events": len(self.events)
            },
            "events": self.events,
            "api_calls_summary": self._summarize_api_calls(),
            "verification_data": self._generate_verification()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _summarize_api_calls(self) -> Dict[str, Any]:
        """Summarize all API calls from events"""
        api_calls = []
        for event in self.events:
            if event['event_type'] == 'API_RESPONSE_RECEIVED':
                api_data = event['data'].get('api_response', {})
                if api_data:
                    api_calls.append({
                        "timestamp": event['timestamp'],
                        "elapsed_ms": event['elapsed_ms'],
                        "session_id": api_data.get('session_id'),
                        "duration_api_ms": api_data.get('duration_api_ms'),
                        "total_cost_usd": api_data.get('total_cost_usd'),
                        "tokens_used": api_data.get('usage', {}).get('input_tokens', 0) + 
                                      api_data.get('usage', {}).get('output_tokens', 0),
                        "success": api_data.get('subtype') == 'success'
                    })
        
        return {
            "total_api_calls": len(api_calls),
            "unique_sessions": len(set(c['session_id'] for c in api_calls if c['session_id'])),
            "total_cost_usd": sum(c['total_cost_usd'] for c in api_calls if c['total_cost_usd']),
            "total_tokens": sum(c['tokens_used'] for c in api_calls),
            "api_calls": api_calls
        }
    
    def _generate_verification(self) -> Dict[str, Any]:
        """Generate verification hashes for data integrity"""
        session_ids = []
        for event in self.events:
            if event['event_type'] == 'API_RESPONSE_RECEIVED':
                sid = event['data'].get('api_response', {}).get('session_id')
                if sid:
                    session_ids.append(sid)
        
        return {
            "session_ids": session_ids,
            "session_count": len(session_ids),
            "data_hash": hashlib.sha256(json.dumps(self.events).encode()).hexdigest()
        }


def run_single_claude_task(task: str, model: str, token_env_var: str, collector: VerifiedAPITimingCollector, label: str) -> Dict[str, Any]:
    """Run a single Claude task and capture ALL API response data"""
    
    # Log task start
    collector.log_event(f"TASK_{label}_START", {
        "task": task,
        "model": model,
        "token_env_var": token_env_var
    })
    
    # Build command
    cmd = [
        'claude',
        '--model', model,
        '--dangerously-skip-permissions',
        '--output-format', 'json',  # CRUCIAL: Get JSON with API data
        '-p', task
    ]
    
    # Set up environment with specific token
    env = os.environ.copy()
    if token_env_var and token_env_var in os.environ:
        env['CLAUDE_CODE_TOKEN'] = os.environ[token_env_var]
    
    # Log subprocess spawn
    spawn_time = time.perf_counter()
    collector.log_event(f"SUBPROCESS_{label}_SPAWN", {
        "command": ' '.join(cmd),
        "token_env_var": token_env_var
    })
    
    # Execute subprocess
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        execution_time = time.perf_counter() - spawn_time
        
        # Log subprocess completion
        collector.log_event(f"SUBPROCESS_{label}_COMPLETE", {
            "return_code": result.returncode,
            "execution_time_seconds": execution_time,
            "stderr_length": len(result.stderr) if result.stderr else 0
        })
        
        # Parse API response if JSON
        api_response = None
        if result.returncode == 0 and result.stdout:
            try:
                api_response = json.loads(result.stdout)
                
                # Log the ACTUAL API response data
                collector.log_event(f"API_RESPONSE_RECEIVED", {
                    "label": label,
                    "api_response": api_response,
                    "response_size_bytes": len(result.stdout)
                })
                
                # Extract key verification data
                collector.log_event(f"API_VERIFICATION_{label}", {
                    "session_id": api_response.get('session_id'),
                    "duration_ms": api_response.get('duration_ms'),
                    "duration_api_ms": api_response.get('duration_api_ms'),
                    "total_cost_usd": api_response.get('total_cost_usd'),
                    "input_tokens": api_response.get('usage', {}).get('input_tokens'),
                    "output_tokens": api_response.get('usage', {}).get('output_tokens'),
                    "cache_tokens": api_response.get('usage', {}).get('cache_creation_input_tokens'),
                    "service_tier": api_response.get('usage', {}).get('service_tier'),
                    "result_preview": str(api_response.get('result', ''))[:100]
                })
                
            except json.JSONDecodeError as e:
                collector.log_event(f"JSON_PARSE_ERROR_{label}", {
                    "error": str(e),
                    "stdout_preview": result.stdout[:500]
                })
        
        # Check if file was created (for file creation tasks)
        if 'Create file' in task:
            # Extract filename from task
            import re
            match = re.search(r'/tmp/[\w_]+\.txt', task)
            if match:
                filepath = match.group(0)
                if os.path.exists(filepath):
                    with open(filepath) as f:
                        content = f.read()
                    
                    # Get file stats for verification
                    stat = os.stat(filepath)
                    
                    collector.log_event(f"FILE_VERIFIED_{label}", {
                        "filepath": filepath,
                        "content": content.strip(),
                        "size_bytes": stat.st_size,
                        "created_timestamp": stat.st_mtime,
                        "created_readable": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                else:
                    collector.log_event(f"FILE_NOT_FOUND_{label}", {
                        "expected_filepath": filepath
                    })
        
        return {
            "label": label,
            "success": result.returncode == 0,
            "execution_time": execution_time,
            "api_response": api_response,
            "session_id": api_response.get('session_id') if api_response else None
        }
        
    except subprocess.TimeoutExpired:
        collector.log_event(f"SUBPROCESS_{label}_TIMEOUT", {
            "timeout_seconds": 60
        })
        return {
            "label": label,
            "success": False,
            "error": "timeout"
        }
    except Exception as e:
        collector.log_event(f"SUBPROCESS_{label}_ERROR", {
            "error": str(e)
        })
        return {
            "label": label,
            "success": False,
            "error": str(e)
        }


def run_parallel_test(tasks: List[Dict[str, Any]], collector: VerifiedAPITimingCollector) -> Dict[str, Any]:
    """Run parallel test with subprocess.Popen for true parallelism"""
    
    collector.log_event("PARALLEL_TEST_START", {
        "task_count": len(tasks)
    })
    
    # Start all processes
    processes = []
    for i, task_config in enumerate(tasks):
        label = task_config['label']
        
        cmd = [
            'claude',
            '--model', task_config['model'],
            '--dangerously-skip-permissions',
            '--output-format', 'json',
            '-p', task_config['task']
        ]
        
        # Set up environment with specific token
        env = os.environ.copy()
        token_var = f"CLAUDE_CODE_TOKEN{i}" if i > 0 else "CLAUDE_CODE_TOKEN"
        if token_var in os.environ:
            env['CLAUDE_CODE_TOKEN'] = os.environ[token_var]
        
        collector.log_event(f"PARALLEL_SPAWN_{label}", {
            "command": ' '.join(cmd),
            "token_env_var": token_var
        })
        
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
            'start_time': time.perf_counter(),
            'task': task_config['task'],
            'token_var': token_var
        })
    
    collector.log_event("ALL_PROCESSES_SPAWNED", {
        "process_count": len(processes)
    })
    
    # Wait for all to complete
    results = []
    for p in processes:
        stdout, stderr = p['proc'].communicate()
        end_time = time.perf_counter()
        duration = end_time - p['start_time']
        
        collector.log_event(f"PARALLEL_COMPLETE_{p['label']}", {
            "duration_seconds": duration,
            "return_code": p['proc'].returncode
        })
        
        # Parse API response
        api_response = None
        if p['proc'].returncode == 0 and stdout:
            try:
                api_response = json.loads(stdout)
                collector.log_event("API_RESPONSE_RECEIVED", {
                    "label": p['label'],
                    "api_response": api_response,
                    "response_size_bytes": len(stdout)
                })
            except json.JSONDecodeError:
                pass
        
        results.append({
            "label": p['label'],
            "duration": duration,
            "success": p['proc'].returncode == 0,
            "session_id": api_response.get('session_id') if api_response else None,
            "api_cost": api_response.get('total_cost_usd') if api_response else None
        })
    
    return results


def main():
    """Main test function"""
    print("="*70)
    print("VERIFIED API TIMING TEST")
    print("This test captures ACTUAL API response data for verification")
    print("All timing is measured by Python code, not reported by agents")
    print("="*70)
    
    collector = VerifiedAPITimingCollector()
    
    # Clean up old files
    collector.log_event("CLEANUP", {"action": "Removing old test files"})
    subprocess.run("rm -f /tmp/verified_api_*.txt", shell=True)
    
    # Test 1: Sequential execution for baseline
    print("\n--- TEST 1: SEQUENTIAL EXECUTION (Baseline) ---")
    sequential_tasks = [
        {"label": "SEQ_A", "task": "Create file /tmp/verified_api_seq_a.txt with 'SEQ_A_DONE'", "model": "sonnet"},
        {"label": "SEQ_B", "task": "Create file /tmp/verified_api_seq_b.txt with 'SEQ_B_DONE'", "model": "sonnet"},
        {"label": "SEQ_C", "task": "Create file /tmp/verified_api_seq_c.txt with 'SEQ_C_DONE'", "model": "sonnet"}
    ]
    
    seq_results = []
    for i, task in enumerate(sequential_tasks):
        token_var = f"CLAUDE_CODE_TOKEN{i}" if i > 0 else "CLAUDE_CODE_TOKEN"
        result = run_single_claude_task(
            task['task'], 
            task['model'], 
            token_var,
            collector,
            task['label']
        )
        seq_results.append(result)
    
    # Test 2: Parallel execution
    print("\n--- TEST 2: PARALLEL EXECUTION ---")
    parallel_tasks = [
        {"label": "PAR_A", "task": "Create file /tmp/verified_api_par_a.txt with 'PAR_A_DONE'", "model": "sonnet"},
        {"label": "PAR_B", "task": "Create file /tmp/verified_api_par_b.txt with 'PAR_B_DONE'", "model": "sonnet"},
        {"label": "PAR_C", "task": "Create file /tmp/verified_api_par_c.txt with 'PAR_C_DONE'", "model": "sonnet"}
    ]
    
    par_results = run_parallel_test(parallel_tasks, collector)
    
    # Save report
    report_path = f"/tmp/verified_api_report_{int(time.time())}.json"
    report = collector.save_report(report_path)
    
    # Print summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    api_summary = report['api_calls_summary']
    print(f"Total API Calls Made: {api_summary['total_api_calls']}")
    print(f"Unique Session IDs: {api_summary['unique_sessions']}")
    print(f"Total API Cost: ${api_summary['total_cost_usd']:.4f}")
    print(f"Total Tokens Used: {api_summary['total_tokens']}")
    
    print("\nSession IDs (Proof of API calls):")
    for sid in report['verification_data']['session_ids']:
        print(f"  - {sid}")
    
    print(f"\nData Integrity Hash: {report['verification_data']['data_hash']}")
    print(f"Report saved to: {report_path}")
    
    # Analyze parallelism
    print("\n" + "="*70)
    print("PARALLELISM ANALYSIS")
    print("="*70)
    
    seq_times = [r['execution_time'] for r in seq_results if r.get('execution_time')]
    if seq_times:
        seq_total = sum(seq_times)
        print(f"Sequential Total: {seq_total:.2f}s")
    
    par_times = [r['duration'] for r in par_results if r.get('duration')]
    if par_times:
        par_max = max(par_times)
        print(f"Parallel Max: {par_max:.2f}s")
        
        if seq_total and par_max:
            speedup = seq_total / par_max
            print(f"Speedup: {speedup:.2f}x")
            
            if speedup > 2.5:
                print("✅ TRUE PARALLEL EXECUTION VERIFIED")
            else:
                print("⚠️ PARTIAL OR NO PARALLELISM")
    
    return report


if __name__ == "__main__":
    main()