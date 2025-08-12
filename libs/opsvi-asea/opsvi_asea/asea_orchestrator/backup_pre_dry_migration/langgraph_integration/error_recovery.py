"""
Error Recovery and Retry System for ASEA-LangGraph Integration

Implements advanced error handling, retry logic, and recovery strategies
for robust workflow execution.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum

from .state import ASEAState


class ErrorSeverity(Enum):
    """Error severity levels for recovery decisions."""

    LOW = "low"  # Warnings, non-critical issues
    MEDIUM = "medium"  # Recoverable errors, retry recommended
    HIGH = "high"  # Serious errors, manual intervention may be needed
    CRITICAL = "critical"  # Fatal errors, workflow should stop


class RetryStrategy(Enum):
    """Retry strategy types."""

    IMMEDIATE = "immediate"  # Retry immediately
    LINEAR_BACKOFF = "linear"  # Linear delay increase
    EXPONENTIAL_BACKOFF = "exponential"  # Exponential delay increase
    FIXED_DELAY = "fixed"  # Fixed delay between retries


class ErrorRecoveryManager:
    """
    Manages error recovery, retry logic, and fallback strategies.

    Provides:
    - Automatic retry with configurable strategies
    - Error classification and severity assessment
    - Fallback execution paths
    - Recovery state management
    - Error pattern analysis
    """

    def __init__(self):
        self.retry_configs = {}
        self.fallback_handlers = {}
        self.error_patterns = {}
        self.recovery_history = []

        # Default retry configuration
        self.default_retry_config = {
            "max_attempts": 3,
            "strategy": RetryStrategy.EXPONENTIAL_BACKOFF,
            "base_delay": 1.0,
            "max_delay": 30.0,
            "backoff_factor": 2.0,
        }

    def configure_retry(
        self,
        node_name: str,
        max_attempts: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
    ):
        """
        Configure retry behavior for a specific node.

        Args:
            node_name: Name of the node to configure
            max_attempts: Maximum retry attempts
            strategy: Retry strategy to use
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Backoff multiplier for exponential strategy
        """
        self.retry_configs[node_name] = {
            "max_attempts": max_attempts,
            "strategy": strategy,
            "base_delay": base_delay,
            "max_delay": max_delay,
            "backoff_factor": backoff_factor,
        }

    def add_fallback_handler(
        self,
        node_name: str,
        fallback_func: Callable[[ASEAState, Exception], ASEAState],
        description: str = "",
    ):
        """
        Add a fallback handler for a specific node.

        Args:
            node_name: Node to add fallback for
            fallback_func: Function to execute when node fails
            description: Description of the fallback strategy
        """
        self.fallback_handlers[node_name] = {
            "func": fallback_func,
            "description": description,
            "added_at": datetime.now().isoformat(),
        }

    def add_error_pattern(
        self,
        pattern_name: str,
        error_matcher: Callable[[Exception], bool],
        severity: ErrorSeverity,
        recovery_action: str,
        description: str = "",
    ):
        """
        Add an error pattern for automatic classification.

        Args:
            pattern_name: Name of the error pattern
            error_matcher: Function to match errors to this pattern
            severity: Severity level of this error type
            recovery_action: Recommended recovery action
            description: Description of the error pattern
        """
        self.error_patterns[pattern_name] = {
            "matcher": error_matcher,
            "severity": severity,
            "recovery_action": recovery_action,
            "description": description,
            "match_count": 0,
        }

    def execute_with_recovery(
        self,
        node_name: str,
        node_func: Callable[[ASEAState], ASEAState],
        state: ASEAState,
    ) -> ASEAState:
        """
        Execute a node with error recovery and retry logic.

        Args:
            node_name: Name of the node being executed
            node_func: Node function to execute
            state: Current workflow state

        Returns:
            Updated state after execution with recovery
        """
        retry_config = self.retry_configs.get(node_name, self.default_retry_config)
        max_attempts = retry_config["max_attempts"]

        last_error = None
        attempt_history = []

        for attempt in range(1, max_attempts + 1):
            try:
                start_time = time.time()

                # Execute the node
                result_state = node_func(state)

                execution_time = time.time() - start_time

                # Record successful attempt
                attempt_history.append(
                    {
                        "attempt": attempt,
                        "success": True,
                        "execution_time": execution_time,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Add recovery metadata to state
                recovery_metadata = {
                    "node_name": node_name,
                    "attempts_made": attempt,
                    "total_attempts": max_attempts,
                    "attempt_history": attempt_history,
                    "recovery_used": attempt > 1,
                }

                new_state = result_state.copy()
                if "recovery_metadata" not in new_state:
                    new_state["recovery_metadata"] = {}
                new_state["recovery_metadata"][node_name] = recovery_metadata

                return new_state

            except Exception as e:
                execution_time = time.time() - start_time
                last_error = e

                # Classify error
                error_classification = self._classify_error(e)

                # Record failed attempt
                attempt_info = {
                    "attempt": attempt,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "classification": error_classification,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                }
                attempt_history.append(attempt_info)

                # Check if we should stop retrying
                if error_classification["severity"] == ErrorSeverity.CRITICAL:
                    break

                if attempt < max_attempts:
                    # Calculate delay for next attempt
                    delay = self._calculate_retry_delay(retry_config, attempt)

                    print(
                        f"⚠️  Node {node_name} failed (attempt {attempt}/{max_attempts}): {str(e)}"
                    )
                    print(f"🔄 Retrying in {delay:.1f} seconds...")

                    time.sleep(delay)
                else:
                    print(f"❌ Node {node_name} failed after {max_attempts} attempts")

        # All attempts failed, try fallback if available
        if node_name in self.fallback_handlers:
            print(f"🛡️  Executing fallback for {node_name}")
            try:
                fallback_func = self.fallback_handlers[node_name]["func"]
                result_state = fallback_func(state, last_error)

                # Add fallback metadata
                recovery_metadata = {
                    "node_name": node_name,
                    "attempts_made": max_attempts,
                    "total_attempts": max_attempts,
                    "attempt_history": attempt_history,
                    "fallback_used": True,
                    "fallback_description": self.fallback_handlers[node_name][
                        "description"
                    ],
                }

                new_state = result_state.copy()
                if "recovery_metadata" not in new_state:
                    new_state["recovery_metadata"] = {}
                new_state["recovery_metadata"][node_name] = recovery_metadata

                return new_state

            except Exception as fallback_error:
                print(f"❌ Fallback for {node_name} also failed: {fallback_error}")
                last_error = fallback_error

        # Create error state
        error_state = state.copy()
        error_message = (
            f"Node {node_name} failed after {max_attempts} attempts: {str(last_error)}"
        )
        error_state["errors"].append(error_message)

        # Add recovery metadata
        recovery_metadata = {
            "node_name": node_name,
            "attempts_made": max_attempts,
            "total_attempts": max_attempts,
            "attempt_history": attempt_history,
            "final_failure": True,
            "fallback_available": node_name in self.fallback_handlers,
        }

        if "recovery_metadata" not in error_state:
            error_state["recovery_metadata"] = {}
        error_state["recovery_metadata"][node_name] = recovery_metadata

        return error_state

    def _classify_error(self, error: Exception) -> Dict[str, Any]:
        """
        Classify an error based on registered patterns.

        Args:
            error: Exception to classify

        Returns:
            Error classification information
        """
        for pattern_name, pattern_config in self.error_patterns.items():
            try:
                if pattern_config["matcher"](error):
                    pattern_config["match_count"] += 1
                    return {
                        "pattern": pattern_name,
                        "severity": pattern_config["severity"],
                        "recovery_action": pattern_config["recovery_action"],
                        "description": pattern_config["description"],
                    }
            except Exception:
                continue

        # Default classification for unknown errors
        return {
            "pattern": "unknown",
            "severity": ErrorSeverity.MEDIUM,
            "recovery_action": "retry",
            "description": "Unknown error pattern",
        }

    def _calculate_retry_delay(
        self, retry_config: Dict[str, Any], attempt: int
    ) -> float:
        """
        Calculate delay before next retry attempt.

        Args:
            retry_config: Retry configuration
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds
        """
        strategy = retry_config["strategy"]
        base_delay = retry_config["base_delay"]
        max_delay = retry_config["max_delay"]

        if strategy == RetryStrategy.IMMEDIATE:
            return 0.0

        elif strategy == RetryStrategy.FIXED_DELAY:
            return min(base_delay, max_delay)

        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = base_delay * attempt
            return min(delay, max_delay)

        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            backoff_factor = retry_config.get("backoff_factor", 2.0)
            delay = base_delay * (backoff_factor ** (attempt - 1))
            return min(delay, max_delay)

        else:
            return base_delay

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about error recovery and retry usage.

        Returns:
            Recovery statistics
        """
        total_patterns = len(self.error_patterns)
        total_matches = sum(p["match_count"] for p in self.error_patterns.values())

        pattern_stats = {
            name: {
                "matches": config["match_count"],
                "severity": config["severity"].value,
                "description": config["description"],
            }
            for name, config in self.error_patterns.items()
        }

        return {
            "total_error_patterns": total_patterns,
            "total_pattern_matches": total_matches,
            "pattern_statistics": pattern_stats,
            "retry_configs": len(self.retry_configs),
            "fallback_handlers": len(self.fallback_handlers),
        }


def create_default_error_patterns() -> ErrorRecoveryManager:
    """
    Create an error recovery manager with default error patterns.

    Returns:
        Configured ErrorRecoveryManager with common patterns
    """
    manager = ErrorRecoveryManager()

    # API-related errors
    manager.add_error_pattern(
        "api_timeout",
        lambda e: "timeout" in str(e).lower() or "timed out" in str(e).lower(),
        ErrorSeverity.MEDIUM,
        "retry_with_backoff",
        "API request timeout - usually recoverable with retry",
    )

    manager.add_error_pattern(
        "api_rate_limit",
        lambda e: "rate limit" in str(e).lower()
        or "too many requests" in str(e).lower(),
        ErrorSeverity.MEDIUM,
        "retry_with_longer_delay",
        "API rate limit exceeded - retry with longer delay",
    )

    manager.add_error_pattern(
        "api_authentication",
        lambda e: "authentication" in str(e).lower()
        or "unauthorized" in str(e).lower()
        or "api key" in str(e).lower(),
        ErrorSeverity.HIGH,
        "check_credentials",
        "API authentication failure - check credentials",
    )

    # Data-related errors
    manager.add_error_pattern(
        "missing_data",
        lambda e: "nonetype" in str(e).lower()
        or "none" in str(e).lower()
        and "attribute" in str(e).lower(),
        ErrorSeverity.MEDIUM,
        "use_fallback_data",
        "Missing or null data - use fallback values",
    )

    manager.add_error_pattern(
        "data_format",
        lambda e: "json" in str(e).lower()
        or "parse" in str(e).lower()
        or "decode" in str(e).lower(),
        ErrorSeverity.MEDIUM,
        "data_validation",
        "Data format or parsing error - validate input data",
    )

    # System-related errors
    manager.add_error_pattern(
        "memory_error",
        lambda e: isinstance(e, MemoryError) or "memory" in str(e).lower(),
        ErrorSeverity.HIGH,
        "reduce_batch_size",
        "Memory error - reduce processing batch size",
    )

    manager.add_error_pattern(
        "network_error",
        lambda e: "network" in str(e).lower()
        or "connection" in str(e).lower()
        or "dns" in str(e).lower(),
        ErrorSeverity.MEDIUM,
        "retry_with_backoff",
        "Network connectivity issue - retry with backoff",
    )

    # Critical errors that should not be retried
    manager.add_error_pattern(
        "configuration_error",
        lambda e: "config" in str(e).lower()
        or "setting" in str(e).lower()
        or "parameter" in str(e).lower(),
        ErrorSeverity.CRITICAL,
        "fix_configuration",
        "Configuration error - manual intervention required",
    )

    return manager


def create_fallback_response(original_prompt: str, error_context: str) -> str:
    """
    Create a fallback response when AI reasoning fails.

    Args:
        original_prompt: The original user prompt
        error_context: Context about the error that occurred

    Returns:
        Fallback response string
    """
    return f"""
I apologize, but I encountered an issue while processing your request: "{original_prompt}"

Error context: {error_context}

Here's a basic response based on the prompt:

{_generate_basic_response(original_prompt)}

For a more detailed response, please try again or rephrase your question.
"""


def _generate_basic_response(prompt: str) -> str:
    """
    Generate a basic response based on prompt keywords.

    This is a simple fallback that provides some value when AI processing fails.
    """
    prompt_lower = prompt.lower()

    if "productivity" in prompt_lower:
        return "Consider creating a dedicated workspace, establishing routines, taking regular breaks, and minimizing distractions."

    elif "quantum" in prompt_lower and "computing" in prompt_lower:
        return "Quantum computing is an emerging field with potential applications in cryptography, optimization, and simulation."

    elif "food waste" in prompt_lower:
        return "Food waste reduction strategies include better planning, composting, food sharing programs, and improved storage methods."

    elif any(word in prompt_lower for word in ["how", "what", "why", "when", "where"]):
        return "This is a complex question that would benefit from research and detailed analysis."

    else:
        return "Thank you for your question. This topic requires careful consideration and research to provide a comprehensive answer."
