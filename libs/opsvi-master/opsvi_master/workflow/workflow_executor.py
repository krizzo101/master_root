"""
Workflow Execution Engine for Universal Workflow Templates

Executes parsed workflow steps, manages state, and integrates with quality gates and step handlers.
Supports Schema v2.0 features including phases, enhanced error handling, and monitoring.
"""
from typing import Any, Dict, List, Callable, Optional, Generator
import sys
import time
import logging
from enum import Enum
from datetime import datetime


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowExecutor:
    def __init__(
        self,
        steps: List[Dict[str, Any]],
        step_handlers: Dict[str, Callable],
        quality_gates: Optional[Dict[str, str]] = None,
        error_handling: Optional[Dict[str, Any]] = None,
        monitoring_config: Optional[Dict[str, Any]] = None,
    ):
        self.steps = steps
        self.step_handlers = step_handlers
        self.quality_gates = quality_gates or {}
        self.error_handling = error_handling or {}
        self.monitoring_config = monitoring_config or {}

        self.state: Dict[str, Any] = {}
        self.current_step = 0
        self.max_attempts = {}
        self.attempts = {}
        self.step_status: Dict[str, StepStatus] = {}
        self.step_timings: Dict[str, Dict[str, datetime]] = {}
        self.execution_log: List[Dict[str, Any]] = []

        # Initialize step status
        for step in self.steps:
            step_id = step.get("id")
            if step_id:
                self.step_status[step_id] = StepStatus.PENDING

        # Setup logging if monitoring enabled
        if self.monitoring_config.get("step_tracking", False):
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = None

    def run(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute workflow with enhanced error handling and monitoring."""
        context = context or {}
        self.state.update(context)
        self.state["workflow_start_time"] = datetime.now()

        self._log_execution("workflow_started", {"context": context})

        try:
            for idx, step in enumerate(self.steps):
                self.current_step = idx
                step_id = step.get("id")

                if not step_id:
                    self._log_execution("error", {"message": f"Step {idx} missing id"})
                    continue

                # Check dependencies
                if not self._check_dependencies(step):
                    self._set_step_status(step_id, StepStatus.SKIPPED)
                    continue

                # Execute step with retry logic
                success = self._execute_step_with_retry(step)

                if not success:
                    if self._should_continue_on_failure(step):
                        self._log_execution(
                            "step_failed_continue", {"step_id": step_id}
                        )
                        continue
                    else:
                        self._log_execution("workflow_failed", {"failed_step": step_id})
                        break

                # Check quality gates after step completion
                if not self._check_quality_gates(step):
                    self._log_execution("quality_gate_failed", {"step_id": step_id})
                    if not self._handle_quality_gate_failure(step):
                        break

            self.state["workflow_end_time"] = datetime.now()
            self._log_execution("workflow_completed", {"final_state": self.state})

        except Exception as e:
            self._log_execution("workflow_error", {"error": str(e)})
            self.state["workflow_error"] = str(e)

        return self._generate_execution_report()

    def _execute_step_with_retry(self, step: Dict[str, Any]) -> bool:
        """Execute a single step with retry logic."""
        step_id = step.get("id")
        max_attempts = step.get("max_attempts", 1)
        self.max_attempts[step_id] = max_attempts
        self.attempts[step_id] = 0

        self._set_step_status(step_id, StepStatus.RUNNING)
        self._start_step_timing(step_id)

        while self.attempts[step_id] < max_attempts:
            self.attempts[step_id] += 1

            if self.attempts[step_id] > 1:
                self._set_step_status(step_id, StepStatus.RETRYING)
                self._log_execution(
                    "step_retry",
                    {"step_id": step_id, "attempt": self.attempts[step_id]},
                )

            # Check 'when' condition
            when = step.get("when")
            if when and not self._evaluate_when(when):
                self._set_step_status(step_id, StepStatus.SKIPPED)
                self._log_execution(
                    "step_skipped", {"step_id": step_id, "condition": when}
                )
                self._end_step_timing(step_id)
                return True

            # Find and execute handler
            handler = self.step_handlers.get(step_id)
            if not handler:
                # Try to get handler using step properties
                from .step_handlers import get_handler_for_step

                handler = get_handler_for_step(step, self.step_handlers)
                if not handler:
                    self._log_execution("no_handler", {"step_id": step_id})
                    self._set_step_status(step_id, StepStatus.FAILED)
                    self._end_step_timing(step_id)
                    return False

            try:
                handler(step, self.state)
                self._set_step_status(step_id, StepStatus.COMPLETED)
                self._end_step_timing(step_id)
                self._log_execution(
                    "step_completed",
                    {"step_id": step_id, "attempt": self.attempts[step_id]},
                )
                return True

            except Exception as e:
                self._log_execution(
                    "step_error",
                    {
                        "step_id": step_id,
                        "attempt": self.attempts[step_id],
                        "error": str(e),
                    },
                )

                if self.attempts[step_id] >= max_attempts:
                    self._set_step_status(step_id, StepStatus.FAILED)
                    self._end_step_timing(step_id)
                    self._log_execution(
                        "step_failed_final",
                        {"step_id": step_id, "max_attempts": max_attempts},
                    )
                    return False

                # Apply retry strategy
                self._apply_retry_strategy(step, self.attempts[step_id])

        return False

    def _check_dependencies(self, step: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied."""
        depends_on = step.get("depends_on", [])
        if isinstance(depends_on, str):
            depends_on = [depends_on]

        for dep in depends_on:
            if self.step_status.get(dep) != StepStatus.COMPLETED:
                return False
        return True

    def _check_quality_gates(self, step: Dict[str, Any]) -> bool:
        """Check quality gates after step execution using safe evaluation."""
        step_phase = step.get("phase", "")

        # Handle both dict and list formats for quality gates
        if isinstance(self.quality_gates, list):
            # Quality gates as list of dicts
            for gate_dict in self.quality_gates:
                for gate_name, condition in gate_dict.items():
                    try:
                        if not self._safe_eval_condition(condition):
                            self._log_execution(
                                "quality_gate_violation",
                                {
                                    "gate": gate_name,
                                    "condition": condition,
                                    "step_phase": step_phase,
                                },
                            )
                            return False
                    except Exception as e:
                        self._log_execution(
                            "quality_gate_error", {"gate": gate_name, "error": str(e)}
                        )
                        return False
        elif isinstance(self.quality_gates, dict):
            # Quality gates as single dict
            for gate_name, condition in self.quality_gates.items():
                try:
                    if not self._safe_eval_condition(condition):
                        self._log_execution(
                            "quality_gate_violation",
                            {
                                "gate": gate_name,
                                "condition": condition,
                                "step_phase": step_phase,
                            },
                        )
                        return False
                except Exception as e:
                    self._log_execution(
                        "quality_gate_error", {"gate": gate_name, "error": str(e)}
                    )
                    return False
        return True

    def _handle_quality_gate_failure(self, step: Dict[str, Any]) -> bool:
        """Handle quality gate failures based on configuration."""
        # Implementation depends on error handling strategy
        strategy = self.error_handling.get("quality_gate_failure", "stop")

        if strategy == "continue":
            return True
        elif strategy == "retry_step":
            # Could implement step retry logic here
            return False
        else:  # 'stop'
            return False

    def _should_continue_on_failure(self, step: Dict[str, Any]) -> bool:
        """Determine if workflow should continue after step failure."""
        return step.get("continue_on_failure", False)

    def _apply_retry_strategy(self, step: Dict[str, Any], attempt: int) -> None:
        """Apply retry strategy between attempts."""
        strategies = self.error_handling.get("retry_strategies", [])

        if "exponential_backoff" in strategies:
            wait_time = min(2**attempt, 30)  # Cap at 30 seconds
            time.sleep(wait_time)
        elif "fixed_delay" in strategies:
            time.sleep(2)

    def _set_step_status(self, step_id: str, status: StepStatus) -> None:
        """Update step status and log if monitoring enabled."""
        self.step_status[step_id] = status
        if self.logger:
            self.logger.info(f"Step {step_id} status: {status.value}")

    def _start_step_timing(self, step_id: str) -> None:
        """Start timing for step execution."""
        if self.monitoring_config.get("performance_metrics", False):
            if step_id not in self.step_timings:
                self.step_timings[step_id] = {}
            self.step_timings[step_id]["start"] = datetime.now()

    def _end_step_timing(self, step_id: str) -> None:
        """End timing for step execution."""
        if self.monitoring_config.get("performance_metrics", False):
            if step_id in self.step_timings:
                self.step_timings[step_id]["end"] = datetime.now()

    def _log_execution(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log execution events."""
        if self.monitoring_config.get("error_logging", False):
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": data,
            }
            self.execution_log.append(log_entry)

    def _generate_execution_report(self) -> Dict[str, Any]:
        """Generate comprehensive execution report."""
        report = {
            "workflow_status": self._get_overall_status(),
            "step_statuses": {k: v.value for k, v in self.step_status.items()},
            "execution_state": self.state.copy(),
            "step_attempts": self.attempts.copy(),
            "execution_log": self.execution_log.copy(),
        }

        if self.monitoring_config.get("performance_metrics", False):
            report["step_timings"] = self._calculate_step_durations()
            report["total_duration"] = self._calculate_total_duration()

        return report

    def _get_overall_status(self) -> str:
        """Determine overall workflow status."""
        statuses = list(self.step_status.values())

        if StepStatus.FAILED in statuses:
            return "failed"
        elif StepStatus.RUNNING in statuses or StepStatus.RETRYING in statuses:
            return "running"
        elif all(s in [StepStatus.COMPLETED, StepStatus.SKIPPED] for s in statuses):
            return "completed"
        else:
            return "pending"

    def _calculate_step_durations(self) -> Dict[str, float]:
        """Calculate duration for each step in seconds."""
        durations = {}
        for step_id, timings in self.step_timings.items():
            if "start" in timings and "end" in timings:
                duration = (timings["end"] - timings["start"]).total_seconds()
                durations[step_id] = duration
        return durations

    def _calculate_total_duration(self) -> Optional[float]:
        """Calculate total workflow duration in seconds."""
        start_time = self.state.get("workflow_start_time")
        end_time = self.state.get("workflow_end_time")

        if start_time and end_time:
            return (end_time - start_time).total_seconds()
        return None

    def _evaluate_when(self, when: str) -> bool:
        """Safely evaluate 'when' conditions."""
        return self._safe_eval_condition(when)

    def _safe_eval_condition(self, condition: str) -> bool:
        """Safely evaluate conditions without using eval()."""
        # Replace eval with safer condition evaluation
        try:
            # For simple boolean conditions, parse manually
            condition = condition.strip()

            # Handle logical operators
            if " and " in condition:
                parts = condition.split(" and ")
                return all(self._safe_eval_condition(part.strip()) for part in parts)
            elif " or " in condition:
                parts = condition.split(" or ")
                return any(self._safe_eval_condition(part.strip()) for part in parts)

            # Handle comparisons
            if " >= " in condition:
                left, right = condition.split(" >= ", 1)
                left_val = self._get_state_value(left.strip())
                right_val = self._parse_value(right.strip())
                return float(left_val) >= float(right_val)
            elif " <= " in condition:
                left, right = condition.split(" <= ", 1)
                left_val = self._get_state_value(left.strip())
                right_val = self._parse_value(right.strip())
                return float(left_val) <= float(right_val)
            elif " == " in condition:
                left, right = condition.split(" == ", 1)
                left_val = self._get_state_value(left.strip())
                right_val = self._parse_value(right.strip())
                return left_val == right_val
            elif " != " in condition:
                left, right = condition.split(" != ", 1)
                left_val = self._get_state_value(left.strip())
                right_val = self._parse_value(right.strip())
                return left_val != right_val
            elif " > " in condition:
                left, right = condition.split(" > ", 1)
                left_val = self._get_state_value(left.strip())
                right_val = self._parse_value(right.strip())
                return float(left_val) > float(right_val)
            elif " < " in condition:
                left, right = condition.split(" < ", 1)
                left_val = self._get_state_value(left.strip())
                right_val = self._parse_value(right.strip())
                return float(left_val) < float(right_val)
            elif condition.lower() in ["true", "1"]:
                return True
            elif condition.lower() in ["false", "0"]:
                return False
            else:
                # For complex conditions, return the state value as boolean
                return bool(self._get_state_value(condition))

        except Exception as e:
            self._log_execution(
                "condition_evaluation_error", {"condition": condition, "error": str(e)}
            )
            return False

    def _get_state_value(self, key: str):
        """Get value from state with safe key access."""
        if key in self.state:
            return self.state[key]
        # Handle nested keys like 'stats.coverage'
        if "." in key:
            parts = key.split(".")
            value = self.state
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        return None

    def _parse_value(self, value_str: str):
        """Parse string value to appropriate type."""
        value_str = value_str.strip()
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]  # String literal
        elif value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]  # String literal
        elif value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False
        elif value_str.isdigit():
            return int(value_str)
        else:
            try:
                return float(value_str)
            except ValueError:
                return value_str

    def register_handler(self, step_id: str, handler: Callable) -> None:
        """Register a handler for a specific step."""
        self.step_handlers[step_id] = handler

    def get_step_status(self, step_id: str) -> Optional[StepStatus]:
        """Get current status of a specific step."""
        return self.step_status.get(step_id)

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the execution log."""
        return self.execution_log.copy()

    def get_current_state(self) -> Dict[str, Any]:
        """Get current workflow state."""
        return self.state.copy()
