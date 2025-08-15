"""
Error Recovery System with intelligent retry and fallback strategies
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import traceback
import json

from src.utils.logger import get_logger

logger = get_logger(__name__)

class ErrorType(Enum):
    NETWORK = "network"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    VALIDATION = "validation"
    PARSING = "parsing"
    EXECUTION = "execution"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context for error recovery"""
    error: Exception
    error_type: ErrorType
    timestamp: datetime
    iteration: int
    retry_count: int = 0
    max_retries: int = 3
    recovery_strategies: List[str] = None
    metadata: Dict[str, Any] = None

class RecoveryStrategy:
    """Base class for recovery strategies"""
    
    async def can_handle(self, context: ErrorContext) -> bool:
        """Check if this strategy can handle the error"""
        raise NotImplementedError
    
    async def recover(self, context: ErrorContext) -> bool:
        """Attempt recovery"""
        raise NotImplementedError

class RetryStrategy(RecoveryStrategy):
    """Simple retry with exponential backoff"""
    
    async def can_handle(self, context: ErrorContext) -> bool:
        return context.retry_count < context.max_retries
    
    async def recover(self, context: ErrorContext) -> bool:
        wait_time = min(2 ** context.retry_count, 30)  # Max 30 seconds
        logger.info(f"Retrying after {wait_time}s (attempt {context.retry_count + 1}/{context.max_retries})")
        await asyncio.sleep(wait_time)
        return True

class ResourceRecoveryStrategy(RecoveryStrategy):
    """Recovery for resource exhaustion"""
    
    async def can_handle(self, context: ErrorContext) -> bool:
        return context.error_type == ErrorType.RESOURCE
    
    async def recover(self, context: ErrorContext) -> bool:
        logger.info("Attempting resource recovery...")
        
        # Garbage collection
        import gc
        gc.collect()
        
        # Clear caches
        # In production, would clear various caches
        
        # Wait for resources to free up
        await asyncio.sleep(5)
        
        return True

class NetworkRecoveryStrategy(RecoveryStrategy):
    """Recovery for network errors"""
    
    async def can_handle(self, context: ErrorContext) -> bool:
        return context.error_type == ErrorType.NETWORK
    
    async def recover(self, context: ErrorContext) -> bool:
        logger.info("Network error detected, waiting for connection...")
        
        # Check network connectivity
        for i in range(5):
            if await self._check_network():
                logger.info("Network recovered")
                return True
            await asyncio.sleep(2)
        
        return False
    
    async def _check_network(self) -> bool:
        """Check network connectivity"""
        # In production, would actually check network
        return True

class ErrorRecovery:
    """Comprehensive error recovery system"""
    
    def __init__(self):
        self.error_history = []
        self.recovery_strategies = [
            RetryStrategy(),
            ResourceRecoveryStrategy(),
            NetworkRecoveryStrategy()
        ]
        self.error_patterns = {}
        self.successful_recoveries = {}
        
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify the error type"""
        
        error_str = str(error).lower()
        error_type_str = type(error).__name__.lower()
        
        if 'timeout' in error_str or 'timeout' in error_type_str:
            return ErrorType.TIMEOUT
        elif 'network' in error_str or 'connection' in error_str:
            return ErrorType.NETWORK
        elif 'memory' in error_str or 'resource' in error_str:
            return ErrorType.RESOURCE
        elif 'json' in error_str or 'parse' in error_str:
            return ErrorType.PARSING
        elif 'validation' in error_str or 'invalid' in error_str:
            return ErrorType.VALIDATION
        elif 'execution' in error_str:
            return ErrorType.EXECUTION
        else:
            return ErrorType.UNKNOWN
    
    async def attempt_recovery(self, error: Exception, context: Any) -> bool:
        """Attempt to recover from an error"""
        
        try:
            # Create error context
            error_context = ErrorContext(
                error=error,
                error_type=self.classify_error(error),
                timestamp=datetime.now(),
                iteration=getattr(context, 'iteration', 0),
                metadata={
                    'traceback': traceback.format_exc(),
                    'context': str(context)
                }
            )
            
            # Log error
            logger.error(f"Error occurred: {error_context.error_type.value} - {str(error)}")
            
            # Add to history
            self.error_history.append(error_context)
            
            # Check for error patterns
            if self._is_recurring_error(error_context):
                logger.warning("Recurring error pattern detected")
                error_context.max_retries = 1  # Reduce retries for recurring errors
            
            # Try recovery strategies
            for strategy in self.recovery_strategies:
                if await strategy.can_handle(error_context):
                    logger.info(f"Attempting recovery with {strategy.__class__.__name__}")
                    
                    if await strategy.recover(error_context):
                        # Record successful recovery
                        self._record_successful_recovery(error_context, strategy)
                        return True
            
            # Check for known solutions
            solution = await self._find_known_solution(error_context)
            if solution:
                logger.info(f"Applying known solution: {solution}")
                return await self._apply_solution(solution, error_context)
            
            logger.error("No recovery strategy available")
            return False
            
        except Exception as e:
            logger.error(f"Error during recovery: {e}")
            return False
    
    def _is_recurring_error(self, error_context: ErrorContext) -> bool:
        """Check if this is a recurring error"""
        
        # Look for similar errors in recent history
        recent_errors = [e for e in self.error_history[-10:] 
                        if e.error_type == error_context.error_type]
        
        # If more than 3 similar errors in last 10, it's recurring
        return len(recent_errors) > 3
    
    def _record_successful_recovery(self, error_context: ErrorContext, strategy: RecoveryStrategy):
        """Record a successful recovery for learning"""
        
        key = f"{error_context.error_type.value}_{strategy.__class__.__name__}"
        
        if key not in self.successful_recoveries:
            self.successful_recoveries[key] = {
                'count': 0,
                'strategies': [],
                'last_success': None
            }
        
        self.successful_recoveries[key]['count'] += 1
        self.successful_recoveries[key]['last_success'] = datetime.now()
        
        logger.info(f"Recovery successful: {key} (total: {self.successful_recoveries[key]['count']})")
    
    async def _find_known_solution(self, error_context: ErrorContext) -> Optional[Dict[str, Any]]:
        """Find a known solution for the error"""
        
        # In production, would query a knowledge base of solutions
        # For now, return hardcoded solutions for common errors
        
        error_msg = str(error_context.error).lower()
        
        solutions = {
            'rate limit': {
                'action': 'wait',
                'params': {'duration': 60}
            },
            'token limit': {
                'action': 'compress_context',
                'params': {}
            },
            'memory': {
                'action': 'free_memory',
                'params': {}
            }
        }
        
        for key, solution in solutions.items():
            if key in error_msg:
                return solution
        
        return None
    
    async def _apply_solution(self, solution: Dict[str, Any], error_context: ErrorContext) -> bool:
        """Apply a known solution"""
        
        action = solution.get('action')
        params = solution.get('params', {})
        
        if action == 'wait':
            duration = params.get('duration', 10)
            logger.info(f"Waiting {duration}s as per solution")
            await asyncio.sleep(duration)
            return True
            
        elif action == 'compress_context':
            logger.info("Compressing context to reduce token usage")
            # In production, would actually compress context
            return True
            
        elif action == 'free_memory':
            logger.info("Freeing memory")
            import gc
            gc.collect()
            return True
        
        return False
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors and recoveries"""
        
        # Count errors by type
        error_counts = {}
        for error in self.error_history:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Recovery success rate
        total_recoveries = sum(r['count'] for r in self.successful_recoveries.values())
        total_errors = len(self.error_history)
        recovery_rate = total_recoveries / max(1, total_errors)
        
        return {
            'total_errors': total_errors,
            'error_counts': error_counts,
            'total_recoveries': total_recoveries,
            'recovery_rate': recovery_rate,
            'successful_strategies': self.successful_recoveries,
            'recent_errors': [
                {
                    'type': e.error_type.value,
                    'timestamp': e.timestamp.isoformat(),
                    'message': str(e.error)[:100]
                }
                for e in self.error_history[-5:]
            ]
        }
    
    async def learn_from_errors(self) -> Dict[str, Any]:
        """Analyze errors to improve recovery strategies"""
        
        patterns = {}
        
        # Group errors by type
        for error in self.error_history:
            error_type = error.error_type.value
            if error_type not in patterns:
                patterns[error_type] = {
                    'count': 0,
                    'recovery_success': 0,
                    'common_causes': [],
                    'best_strategy': None
                }
            
            patterns[error_type]['count'] += 1
        
        # Find best strategies
        for key, recoveries in self.successful_recoveries.items():
            error_type = key.split('_')[0]
            if error_type in patterns:
                if patterns[error_type]['best_strategy'] is None or \
                   recoveries['count'] > patterns[error_type]['recovery_success']:
                    patterns[error_type]['best_strategy'] = key.split('_')[1]
                    patterns[error_type]['recovery_success'] = recoveries['count']
        
        return patterns
    
    def clear_old_errors(self, hours: int = 24):
        """Clear errors older than specified hours"""
        
        cutoff = datetime.now() - timedelta(hours=hours)
        self.error_history = [e for e in self.error_history 
                            if e.timestamp > cutoff]
        
        logger.info(f"Cleared errors older than {hours} hours")