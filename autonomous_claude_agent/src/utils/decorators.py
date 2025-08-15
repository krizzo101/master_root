"""
Common decorators for the autonomous agent system.
"""

import time
import asyncio
import functools
import inspect
from typing import Callable, Any, Optional, Union, Dict, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import pickle
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


def with_retry(max_attempts: int = 3,
              delay: float = 1.0,
              backoff: float = 2.0,
              exceptions: Tuple[type, ...] = (Exception,)):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__}: All {max_attempts} attempts failed")
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"{func.__name__}: All {max_attempts} attempts failed")
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_timeout(timeout: float, error_message: Optional[str] = None):
    """
    Decorator for adding timeout to functions.
    
    Args:
        timeout: Timeout in seconds
        error_message: Optional custom error message
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                msg = error_message or f"{func.__name__} timed out after {timeout}s"
                logger.error(msg)
                raise TimeoutError(msg)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to run in a thread with timeout
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=timeout)
                except concurrent.futures.TimeoutError:
                    msg = error_message or f"{func.__name__} timed out after {timeout}s"
                    logger.error(msg)
                    raise TimeoutError(msg)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_cache(cache_dir: Optional[Path] = None,
              ttl: Optional[int] = 3600,
              key_func: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache_dir: Directory for cache storage
        ttl: Time to live in seconds (None for no expiry)
        key_func: Custom function to generate cache key
    """
    cache_dir = cache_dir or Path("./cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Tuple[Any, float]] = {}
        
        def get_cache_key(*args, **kwargs) -> str:
            if key_func:
                return key_func(*args, **kwargs)
            
            # Default key generation
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True, default=str)
            return hashlib.md5(key_str.encode()).hexdigest()
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = get_cache_key(*args, **kwargs)
            
            # Check memory cache
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if ttl is None or (time.time() - timestamp) < ttl:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return result
            
            # Check file cache
            cache_file = cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        result, timestamp = pickle.load(f)
                    
                    if ttl is None or (time.time() - timestamp) < ttl:
                        logger.debug(f"File cache hit for {func.__name__}: {cache_key}")
                        cache[cache_key] = (result, timestamp)
                        return result
                except Exception as e:
                    logger.warning(f"Failed to load cache file: {e}")
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Update cache
            timestamp = time.time()
            cache[cache_key] = (result, timestamp)
            
            # Save to file
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump((result, timestamp), f)
            except Exception as e:
                logger.warning(f"Failed to save cache file: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = get_cache_key(*args, **kwargs)
            
            # Check memory cache
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if ttl is None or (time.time() - timestamp) < ttl:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return result
            
            # Check file cache
            cache_file = cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        result, timestamp = pickle.load(f)
                    
                    if ttl is None or (time.time() - timestamp) < ttl:
                        logger.debug(f"File cache hit for {func.__name__}: {cache_key}")
                        cache[cache_key] = (result, timestamp)
                        return result
                except Exception as e:
                    logger.warning(f"Failed to load cache file: {e}")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Update cache
            timestamp = time.time()
            cache[cache_key] = (result, timestamp)
            
            # Save to file
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump((result, timestamp), f)
            except Exception as e:
                logger.warning(f"Failed to save cache file: {e}")
            
            return result
        
        # Add cache management methods
        def clear_cache():
            cache.clear()
            for cache_file in cache_dir.glob(f"*.pkl"):
                cache_file.unlink()
        
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.clear_cache = clear_cache
        
        return wrapper
    
    return decorator


def with_logging(level: str = "INFO",
                log_args: bool = True,
                log_result: bool = False,
                log_time: bool = True):
    """
    Decorator for automatic function logging.
    
    Args:
        level: Log level
        log_args: Whether to log arguments
        log_result: Whether to log result
        log_time: Whether to log execution time
    """
    def decorator(func: Callable) -> Callable:
        func_logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log entry
            log_data = {'function': func.__name__}
            if log_args:
                log_data['args'] = args
                log_data['kwargs'] = kwargs
            
            func_logger.debug(f"Calling {func.__name__}", **log_data)
            
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                log_data = {'function': func.__name__}
                if log_result:
                    log_data['result'] = result
                if log_time:
                    log_data['duration_ms'] = (time.time() - start_time) * 1000
                
                getattr(func_logger, level.lower())(
                    f"{func.__name__} completed",
                    **log_data
                )
                
                return result
                
            except Exception as e:
                # Log error
                log_data = {
                    'function': func.__name__,
                    'error': str(e),
                    'error_type': e.__class__.__name__
                }
                if log_time:
                    log_data['duration_ms'] = (time.time() - start_time) * 1000
                
                func_logger.error(f"{func.__name__} failed", exception=e, **log_data)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log entry
            log_data = {'function': func.__name__}
            if log_args:
                log_data['args'] = args
                log_data['kwargs'] = kwargs
            
            func_logger.debug(f"Calling {func.__name__}", **log_data)
            
            try:
                result = func(*args, **kwargs)
                
                # Log success
                log_data = {'function': func.__name__}
                if log_result:
                    log_data['result'] = result
                if log_time:
                    log_data['duration_ms'] = (time.time() - start_time) * 1000
                
                getattr(func_logger, level.lower())(
                    f"{func.__name__} completed",
                    **log_data
                )
                
                return result
                
            except Exception as e:
                # Log error
                log_data = {
                    'function': func.__name__,
                    'error': str(e),
                    'error_type': e.__class__.__name__
                }
                if log_time:
                    log_data['duration_ms'] = (time.time() - start_time) * 1000
                
                func_logger.error(f"{func.__name__} failed", exception=e, **log_data)
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def measure_performance(metric_name: Optional[str] = None):
    """
    Decorator for measuring function performance.
    
    Args:
        metric_name: Optional custom metric name
    """
    def decorator(func: Callable) -> Callable:
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        # Performance storage
        metrics = {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'errors': 0
        }
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                metrics['errors'] += 1
                raise
            finally:
                duration = time.perf_counter() - start_time
                metrics['count'] += 1
                metrics['total_time'] += duration
                metrics['min_time'] = min(metrics['min_time'], duration)
                metrics['max_time'] = max(metrics['max_time'], duration)
                
                logger.debug(
                    f"Performance: {name}",
                    duration_ms=duration * 1000,
                    success=success,
                    total_calls=metrics['count'],
                    avg_time_ms=(metrics['total_time'] / metrics['count']) * 1000
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                metrics['errors'] += 1
                raise
            finally:
                duration = time.perf_counter() - start_time
                metrics['count'] += 1
                metrics['total_time'] += duration
                metrics['min_time'] = min(metrics['min_time'], duration)
                metrics['max_time'] = max(metrics['max_time'], duration)
                
                logger.debug(
                    f"Performance: {name}",
                    duration_ms=duration * 1000,
                    success=success,
                    total_calls=metrics['count'],
                    avg_time_ms=(metrics['total_time'] / metrics['count']) * 1000
                )
        
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.metrics = metrics
        
        return wrapper
    
    return decorator


def validate_input(**validators):
    """
    Decorator for validating function inputs.
    
    Args:
        **validators: Keyword arguments with validation functions
    """
    def decorator(func: Callable) -> Callable:
        sig = inspect.signature(func)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Bind arguments
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Invalid {param_name}: {value} failed validation"
                        )
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Bind arguments
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(
                            f"Invalid {param_name}: {value} failed validation"
                        )
            
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def require_permission(permission: str, check_func: Optional[Callable] = None):
    """
    Decorator for requiring permission to execute function.
    
    Args:
        permission: Required permission name
        check_func: Optional custom permission check function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check permission
            if check_func:
                if not await check_func(permission, *args, **kwargs):
                    raise PermissionError(
                        f"Permission '{permission}' required for {func.__name__}"
                    )
            else:
                logger.warning(
                    f"Permission check for '{permission}' not implemented"
                )
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check permission
            if check_func:
                if not check_func(permission, *args, **kwargs):
                    raise PermissionError(
                        f"Permission '{permission}' required for {func.__name__}"
                    )
            else:
                logger.warning(
                    f"Permission check for '{permission}' not implemented"
                )
            
            return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def singleton(cls):
    """
    Decorator to make a class a singleton.
    
    Args:
        cls: Class to make singleton
    """
    instances = {}
    lock = asyncio.Lock() if hasattr(asyncio, 'Lock') else None
    
    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            if lock and asyncio.iscoroutinefunction(cls.__init__):
                async def create():
                    async with lock:
                        if cls not in instances:
                            instances[cls] = cls(*args, **kwargs)
                    return instances[cls]
                return create()
            else:
                instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return wrapper


# Example usage
if __name__ == "__main__":
    # Example with retry decorator
    @with_retry(max_attempts=3, delay=0.5)
    @with_logging(log_result=True)
    @measure_performance()
    async def flaky_api_call(url: str) -> str:
        import random
        if random.random() < 0.5:
            raise Exception("Random failure")
        return f"Success: {url}"
    
    # Example with cache decorator
    @with_cache(ttl=60)
    @with_timeout(5.0)
    def expensive_computation(n: int) -> int:
        time.sleep(2)  # Simulate expensive operation
        return n * n
    
    # Example with validation
    @validate_input(
        age=lambda x: x >= 0 and x <= 150,
        name=lambda x: isinstance(x, str) and len(x) > 0
    )
    def create_user(name: str, age: int):
        return {"name": name, "age": age}
    
    # Run examples
    async def main():
        try:
            result = await flaky_api_call("https://api.example.com")
            print(f"API Result: {result}")
        except Exception as e:
            print(f"API Failed: {e}")
        
        # Test cache
        print(f"First call: {expensive_computation(5)}")
        print(f"Second call (cached): {expensive_computation(5)}")
        
        # Test validation
        try:
            user = create_user("Alice", 25)
            print(f"User created: {user}")
            
            invalid_user = create_user("", -5)  # Will raise ValueError
        except ValueError as e:
            print(f"Validation error: {e}")
    
    asyncio.run(main())