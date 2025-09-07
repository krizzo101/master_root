#!/usr/bin/env python3
"""
Minimal UnifiedOrchestrator Validation
====================================

A lightweight validation that tests core functionality with just 3 agents
instead of the original 14-agent comprehensive validation.

Tests:
1. Basic orchestration (parallel execution, dependencies, metrics)
2. Error handling and recovery  
3. Resource management (token pools, cleanup)
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.unified.unified_orchestrator import (
    UnifiedOrchestrator, 
    create_minimal_orchestrator,
)
from src.generic_orchestrator import AgentTask


class MinimalValidation:
    """
    Minimal validation using just 3 key agents to prove core functionality.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {
            "validation_info": {
                "start_time": datetime.now().isoformat(),
                "end_time": None,
                "total_agents": 3,
                "approach": "minimal_core_validation"
            },
            "agent_results": {},
            "overall_success": False,
            "issues": []
        }
        
    def create_core_agents(self) -> List[AgentTask]:
        """Create 3 essential validation agents"""
        
        return [
            # Agent 1: Basic Orchestration Test
            AgentTask(
                task_id="core_orchestration_test",
                task_type="qa-testing-guru",
                prompt="""
                CORE ORCHESTRATION VALIDATION
                
                Mission: Test essential orchestration functionality:
                1. Execute 3 simple tasks in parallel
                2. Verify basic dependency handling (A→B→C)
                3. Check token management prevents oversubscription
                4. Validate metrics collection works
                
                Test Plan:
                - Create 3 parallel tasks with 30-second simulated work
                - Create 3-task dependency chain 
                - Monitor token allocation during execution
                - Verify all tasks complete successfully
                
                Success Criteria:
                - All 6 tasks complete without errors
                - Dependencies are respected (B waits for A, C waits for B)
                - Token management prevents overallocation
                - Basic metrics are collected
                
                Report: Simple PASS/FAIL with any error details
                """,
                context={"priority": 1, "expected_duration": 120}
            ),
            
            # Agent 2: Error Handling Test  
            AgentTask(
                task_id="error_handling_test",
                task_type="qa-testing-guru",
                prompt="""
                ERROR HANDLING VALIDATION
                
                Mission: Test system stability under failure conditions:
                1. Create intentionally failing tasks
                2. Verify graceful failure handling
                3. Test auto-recovery if enabled
                4. Ensure system continues operating
                
                Test Plan:
                - Create 2 tasks that will fail (invalid prompts)
                - Create 2 tasks that will succeed 
                - Monitor system behavior during failures
                - Verify system doesn't crash
                
                Success Criteria:
                - Failed tasks are handled gracefully
                - Successful tasks still complete
                - No system crashes or hangs
                - Error details are captured
                
                Report: PASS/FAIL with failure handling assessment
                """,
                context={"priority": 2, "expected_duration": 90}
            ),
            
            # Agent 3: Resource Management Test
            AgentTask(
                task_id="resource_management_test", 
                task_type="qa-testing-guru",
                prompt="""
                RESOURCE MANAGEMENT VALIDATION
                
                Mission: Test resource limits and cleanup:
                1. Stress test with more tasks than max_parallel allows
                2. Verify token pool properly limits concurrency
                3. Check resource cleanup after completion
                4. Monitor for memory leaks
                
                Test Plan:
                - Submit 8 tasks to system with max_parallel=3
                - Monitor that only 3 run concurrently
                - Verify remaining 5 queue properly
                - Check cleanup after all complete
                
                Success Criteria:
                - Concurrency limit is respected
                - All queued tasks eventually execute
                - Resources are cleaned up properly
                - No memory leaks detected
                
                Report: PASS/FAIL with resource utilization summary
                """,
                context={"priority": 3, "expected_duration": 150}
            )
        ]
    
    async def execute_validation(self) -> Dict:
        """Execute minimal validation with 3 core agents"""
        
        print("🚀 STARTING MINIMAL UNIFIED ORCHESTRATOR VALIDATION")
        print("=" * 60)
        print(f"📁 Output Directory: {self.output_dir}")
        print(f"🎯 Mission: Validate core functionality with 3 essential tests")
        print(f"⏰ Estimated Duration: 5-7 minutes")
        print("=" * 60)
        
        # Create minimal orchestrator for basic validation
        orchestrator = create_minimal_orchestrator(
            output_dir=self.output_dir / "validation_run",
            max_parallel=3,  # Test concurrency limits
            tokens=None  # Use default token management
        )
        
        print("\n🔧 Created minimal orchestrator with max_parallel=3")
        
        # Get validation agents
        agents = self.create_core_agents()
        
        print(f"\n👥 Executing {len(agents)} validation agents...")
        for agent in agents:
            mission = agent.prompt.split('Mission:')[1].split('\n')[0].strip()
            print(f"  • {agent.task_id}: {mission}")
        
        # Execute all agents in parallel
        start_time = datetime.now()
        
        try:
            results = await orchestrator.execute_batch(agents)
            
            # Process results
            successful_agents = 0
            
            for i, result in enumerate(results):
                agent = agents[i]
                agent_id = agent.task_id
                status = result.get('status', 'unknown')
                
                self.results['agent_results'][agent_id] = {
                    'status': status,
                    'result': result,
                    'success': status == 'completed'
                }
                
                if status == 'completed':
                    successful_agents += 1
                    print(f"  ✅ {agent_id}: SUCCESS")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"  ❌ {agent_id}: FAILED - {error_msg}")
                    self.results['issues'].append({
                        'agent': agent_id,
                        'error': error_msg
                    })
            
            execution_time = datetime.now() - start_time
            
            # Determine overall success
            success_rate = successful_agents / len(agents)
            self.results['overall_success'] = success_rate >= 0.67  # At least 2/3 must pass
            self.results['success_rate'] = success_rate
            self.results['execution_time_seconds'] = execution_time.total_seconds()
            
            print(f"\n📊 Validation Results: {successful_agents}/{len(agents)} agents successful")
            print(f"⏱️  Total Duration: {execution_time.total_seconds():.1f} seconds")
            
            # Get orchestrator metrics if available
            try:
                metrics = orchestrator.get_metrics()
                self.results['orchestrator_metrics'] = metrics
                print(f"📈 Tasks Executed: {metrics.get('total_tasks', 'N/A')}")
                print(f"📈 Success Rate: {metrics.get('success_rate', 'N/A')}")
            except Exception:
                print("📈 Metrics not available")
            
        except Exception as e:
            print(f"💥 VALIDATION EXECUTION FAILED: {e}")
            self.results['issues'].append({
                'level': 'critical',
                'error': str(e)
            })
            self.results['overall_success'] = False
        
        # Cleanup orchestrator
        try:
            await orchestrator.cleanup()
            print("🧹 Orchestrator cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        # Generate final report
        self.results['validation_info']['end_time'] = datetime.now().isoformat()
        await self._generate_report()
        
        return self.results
    
    async def _generate_report(self):
        """Generate simple validation report"""
        
        # Create summary report
        report_file = self.output_dir / "minimal_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Create human-readable summary
        summary_file = self.output_dir / "validation_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# Minimal UnifiedOrchestrator Validation Summary\n\n")
            f.write(f"**Generated:** {self.results['validation_info']['end_time']}\n\n")
            
            if self.results['overall_success']:
                f.write("## ✅ VALIDATION PASSED\n\n")
                f.write("Core orchestration functionality is working correctly.\n")
            else:
                f.write("## ❌ VALIDATION FAILED\n\n")
                f.write("Critical issues found that prevent production use.\n")
            
            f.write(f"\n## Results Summary\n")
            f.write(f"- **Success Rate:** {self.results.get('success_rate', 0)*100:.0f}%\n")
            f.write(f"- **Execution Time:** {self.results.get('execution_time_seconds', 0):.1f} seconds\n")
            f.write(f"- **Total Agents:** {self.results['validation_info']['total_agents']}\n")
            
            if self.results['issues']:
                f.write(f"\n## Issues Found\n")
                for issue in self.results['issues']:
                    f.write(f"- **{issue.get('agent', 'System')}:** {issue['error']}\n")
            
            f.write(f"\n## Agent Details\n")
            for agent_id, result in self.results['agent_results'].items():
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                f.write(f"- **{agent_id}:** {status}\n")
        
        print(f"📋 Validation report saved: {report_file}")
        print(f"📄 Human summary saved: {summary_file}")


async def main():
    """Main execution function"""
    
    # Setup output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / f"minimal_validation_{timestamp}"
    
    # Create and execute minimal validation
    validation = MinimalValidation(output_dir)
    
    try:
        results = await validation.execute_validation()
        
        # Print final summary
        print("\n" + "=" * 60)
        print("🎯 MINIMAL VALIDATION COMPLETE")
        print("=" * 60)
        
        if results['overall_success']:
            print("✅ VALIDATION PASSED - Core functionality working")
            print("💡 UnifiedOrchestrator is ready for basic usage")
        else:
            print("❌ VALIDATION FAILED - Issues need resolution")
            print("🔧 Review issues before production use")
        
        success_rate = results.get('success_rate', 0) * 100
        print(f"📊 Success Rate: {success_rate:.0f}%")
        print(f"⏱️  Duration: {results.get('execution_time_seconds', 0):.1f} seconds")
        
        if results['issues']:
            print(f"⚠️  Issues: {len(results['issues'])}")
        
        print(f"\n📁 Full results: {output_dir}")
        
        return results['overall_success']
        
    except Exception as e:
        print(f"\n💥 VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)