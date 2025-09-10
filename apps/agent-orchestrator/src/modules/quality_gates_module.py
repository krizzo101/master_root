#!/usr/bin/env python3
"""
Quality Gates Module for UnifiedOrchestrator
Provides validation gates and quality checks for task execution
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import re

from ..unified.orchestrator_module import OrchestratorModule, ModuleConfig

logger = logging.getLogger(__name__)


class QualityGate:
    """Represents a quality validation gate"""
    
    def __init__(self, name: str, validator: Callable, required: bool = False, timeout: float = 30.0):
        self.name = name
        self.validator = validator
        self.required = required
        self.timeout = timeout
        self.results: List[Dict] = []
        
    async def validate(self, task: 'AgentTask') -> Dict[str, Any]:
        """Run validation on a task"""
        start_time = datetime.now()
        result = {
            "gate": self.name,
            "task_id": task.task_id,
            "timestamp": start_time.isoformat(),
            "passed": False,
            "error": None,
            "duration": 0
        }
        
        try:
            # Run validator with timeout
            validation_result = await asyncio.wait_for(
                self._run_validator(task),
                timeout=self.timeout
            )
            
            result["passed"] = validation_result.get("passed", False)
            result["details"] = validation_result.get("details", {})
            result["score"] = validation_result.get("score", 0)
            
        except asyncio.TimeoutError:
            result["error"] = f"Validation timeout ({self.timeout}s)"
            result["passed"] = not self.required
            
        except Exception as e:
            result["error"] = str(e)
            result["passed"] = not self.required
            
        finally:
            end_time = datetime.now()
            result["duration"] = (end_time - start_time).total_seconds()
            self.results.append(result)
            
        return result
    
    async def _run_validator(self, task: 'AgentTask') -> Dict:
        """Run the actual validator function"""
        if asyncio.iscoroutinefunction(self.validator):
            return await self.validator(task)
        else:
            return self.validator(task)


class QualityGatesModule(OrchestratorModule):
    """
    Module implementing quality gates for task validation.
    Provides pre and post execution validation with configurable gates.
    """
    
    def __init__(self, orchestrator, config: ModuleConfig = None):
        super().__init__(orchestrator, config)
        self.gates: Dict[str, QualityGate] = {}
        self.gate_results: Dict[str, List[Dict]] = {}
        self.reports_dir = None
        
    @property
    def name(self) -> str:
        return "quality_gates"
    
    @property
    def description(self) -> str:
        return "Task validation and quality assurance gates"
    
    async def _initialize(self):
        """Initialize quality gates module"""
        # Setup reports directory
        self.reports_dir = self.orchestrator.output_dir / "quality_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Register default gates
        self._register_default_gates()
        
        logger.info(f"Quality gates module initialized with {len(self.gates)} gates")
    
    def _register_default_gates(self):
        """Register default quality validation gates"""
        
        # Input validation gate
        def validate_input(task):
            """Validate task input parameters"""
            result = {
                "passed": True,
                "details": {},
                "score": 100
            }
            
            # Check task has required fields
            if not task.prompt:
                result["passed"] = False
                result["details"]["prompt"] = "Missing prompt"
                result["score"] -= 50
                
            if not task.task_type:
                result["passed"] = False
                result["details"]["task_type"] = "Missing task type"
                result["score"] -= 30
                
            # Check prompt length
            if task.prompt and len(task.prompt) < 10:
                result["details"]["prompt_length"] = "Prompt too short"
                result["score"] -= 20
                
            return result
        
        self.register_gate(QualityGate(
            "input_validation",
            validate_input,
            required=True,
            timeout=5.0
        ))
        
        # Dependency validation gate
        def validate_dependencies(task):
            """Validate task dependencies are resolved"""
            result = {
                "passed": True,
                "details": {},
                "score": 100
            }
            
            if hasattr(task, 'dependencies') and task.dependencies:
                # Check if dependencies exist in completed tasks
                # This would need access to orchestrator's task registry
                unresolved = []
                for dep in task.dependencies:
                    # Simplified check - in real implementation would check orchestrator
                    if dep.startswith("missing_"):
                        unresolved.append(dep)
                
                if unresolved:
                    result["passed"] = False
                    result["details"]["unresolved_dependencies"] = unresolved
                    result["score"] = 0
                    
            return result
        
        self.register_gate(QualityGate(
            "dependency_validation", 
            validate_dependencies,
            required=True,
            timeout=5.0
        ))
        
        # Complexity check gate
        def check_complexity(task):
            """Check task complexity and resource requirements"""
            result = {
                "passed": True,
                "details": {},
                "score": 100
            }
            
            # Estimate complexity based on prompt
            if task.prompt:
                prompt_lines = task.prompt.count('\n') + 1
                prompt_words = len(task.prompt.split())
                
                complexity_score = prompt_lines * 0.1 + prompt_words * 0.01
                result["details"]["complexity_score"] = complexity_score
                
                if complexity_score > 100:
                    result["details"]["warning"] = "High complexity task"
                    result["score"] = 70
                elif complexity_score > 200:
                    result["details"]["warning"] = "Very high complexity task"
                    result["score"] = 50
                    
            return result
        
        self.register_gate(QualityGate(
            "complexity_check",
            check_complexity,
            required=False,
            timeout=5.0
        ))
        
        # Security validation gate
        async def validate_security(task):
            """Check for potential security issues"""
            result = {
                "passed": True,
                "details": {},
                "score": 100
            }
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'rm\s+-rf\s+/',
                r'curl.*\|.*sh',
                r'eval\(',
                r'exec\(',
                r'__import__',
                r'subprocess.*shell=True'
            ]
            
            if task.prompt:
                for pattern in suspicious_patterns:
                    if re.search(pattern, task.prompt, re.IGNORECASE):
                        result["passed"] = False
                        result["details"]["security_issue"] = f"Suspicious pattern detected: {pattern}"
                        result["score"] = 0
                        break
                        
            return result
        
        self.register_gate(QualityGate(
            "security_validation",
            validate_security,
            required=True,
            timeout=10.0
        ))
    
    def register_gate(self, gate: QualityGate):
        """Register a quality gate"""
        self.gates[gate.name] = gate
        logger.info(f"Registered quality gate: {gate.name}")
    
    def unregister_gate(self, name: str):
        """Unregister a quality gate"""
        if name in self.gates:
            del self.gates[name]
            logger.info(f"Unregistered quality gate: {name}")
    
    async def run_gates(self, task: 'AgentTask', gate_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run quality gates on a task"""
        gates_to_run = gate_names if gate_names else list(self.gates.keys())
        
        results = {
            "task_id": task.task_id,
            "timestamp": datetime.now().isoformat(),
            "gates_run": [],
            "gates_passed": [],
            "gates_failed": [],
            "overall_passed": True,
            "overall_score": 0,
            "details": {}
        }
        
        total_score = 0
        gate_count = 0
        
        for gate_name in gates_to_run:
            if gate_name not in self.gates:
                logger.warning(f"Gate {gate_name} not found")
                continue
                
            gate = self.gates[gate_name]
            gate_result = await gate.validate(task)
            
            results["gates_run"].append(gate_name)
            results["details"][gate_name] = gate_result
            
            if gate_result["passed"]:
                results["gates_passed"].append(gate_name)
            else:
                results["gates_failed"].append(gate_name)
                if gate.required:
                    results["overall_passed"] = False
                    
            if "score" in gate_result:
                total_score += gate_result["score"]
                gate_count += 1
        
        if gate_count > 0:
            results["overall_score"] = total_score / gate_count
            
        # Store results
        if task.task_id not in self.gate_results:
            self.gate_results[task.task_id] = []
        self.gate_results[task.task_id].append(results)
        
        # Save report
        await self._save_gate_report(task.task_id, results)
        
        return results
    
    async def _save_gate_report(self, task_id: str, results: Dict):
        """Save quality gate report to file"""
        report_file = self.reports_dir / f"{task_id}_gate_report.json"
        report_file.write_text(json.dumps(results, indent=2, default=str))
    
    def validate_task(self, task: 'AgentTask') -> Optional[str]:
        """Validate task synchronously (called by orchestrator)"""
        # Quick synchronous validation
        if not task.prompt:
            return "Task missing prompt"
        if not task.task_type:
            return "Task missing type"
        return None
    
    async def pre_task_execution(self, task: 'AgentTask'):
        """Run pre-execution quality gates"""
        if hasattr(task, 'validation_required') and task.validation_required:
            # Run validation gates
            pre_gates = ["input_validation", "dependency_validation", "security_validation"]
            results = await self.run_gates(task, pre_gates)
            
            # Store results in task
            if hasattr(task, 'gate_results'):
                task.gate_results["pre_execution"] = results
                
            # Update task quality gates status
            if hasattr(task, 'quality_gates'):
                for gate_name in results["gates_passed"]:
                    task.quality_gates[gate_name] = True
                for gate_name in results["gates_failed"]:
                    task.quality_gates[gate_name] = False
                    
            logger.info(f"Pre-execution gates for {task.task_id}: "
                       f"Passed={len(results['gates_passed'])}, "
                       f"Failed={len(results['gates_failed'])}, "
                       f"Score={results['overall_score']:.1f}")
    
    async def post_task_execution(self, task: 'AgentTask'):
        """Run post-execution quality gates"""
        # Could add output validation gates here
        pass
    
    async def on_task_success(self, task: 'AgentTask'):
        """Handle successful task completion"""
        # Record success metrics
        if hasattr(task, 'gate_results') and task.gate_results:
            # Generate success report
            report = {
                "task_id": task.task_id,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "quality_gates": task.gate_results
            }
            
            report_file = self.reports_dir / f"{task.task_id}_success_report.json"
            report_file.write_text(json.dumps(report, indent=2, default=str))
    
    async def on_task_failure(self, task: 'AgentTask'):
        """Handle task failure"""
        # Analyze failure in context of quality gates
        if hasattr(task, 'gate_results') and task.gate_results:
            # Check if failure was predicted by gates
            pre_gates = task.gate_results.get("pre_execution", {})
            if not pre_gates.get("overall_passed", True):
                logger.warning(f"Task {task.task_id} failed as predicted by quality gates")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get quality gates metrics"""
        metrics = {
            "total_gates": len(self.gates),
            "required_gates": sum(1 for g in self.gates.values() if g.required),
            "total_validations": sum(len(results) for results in self.gate_results.values()),
            "gate_statistics": {}
        }
        
        # Calculate per-gate statistics
        for gate_name, gate in self.gates.items():
            if gate.results:
                passed = sum(1 for r in gate.results if r["passed"])
                total = len(gate.results)
                avg_duration = sum(r["duration"] for r in gate.results) / total
                
                metrics["gate_statistics"][gate_name] = {
                    "total_runs": total,
                    "passed": passed,
                    "failed": total - passed,
                    "pass_rate": passed / total * 100,
                    "avg_duration": avg_duration
                }
        
        return metrics
    
    async def _cleanup(self):
        """Cleanup module resources"""
        # Save final metrics report
        if self.reports_dir:
            final_report = {
                "timestamp": datetime.now().isoformat(),
                "metrics": self.get_metrics(),
                "all_results": self.gate_results
            }
            
            report_file = self.reports_dir / f"final_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.write_text(json.dumps(final_report, indent=2, default=str))
            
        logger.info("Quality gates module cleanup complete")