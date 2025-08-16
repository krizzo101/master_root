"""
Multi-token solution for true parallel Claude execution

This module is deprecated. Use the MultiTokenManager from parallel_enhancement.py instead.
"""
import warnings
from .parallel_enhancement import MultiTokenManager

# Show deprecation warning
warnings.warn(
    "multi_token_solution.MultiTokenManager is deprecated. "
    "Use parallel_enhancement.MultiTokenManager instead.",
    DeprecationWarning,
    stacklevel=2
)

# Export the consolidated implementation for backward compatibility
__all__ = ['MultiTokenManager', 'enhance_job_with_token']


def enhance_job_with_token(job, token_manager):
    """Enhance job config with dedicated token
    
    Deprecated: This function is maintained for backward compatibility.
    Use the methods in parallel_enhancement.py directly.
    """
    from typing import Dict, Any
    
    job_id = job.get("id", "")
    token = token_manager.get_token_for_job(job_id, retry_count=0)
    
    # Set token in job's environment
    if "env" not in job:
        job["env"] = {}
    job["env"]["CLAUDE_CODE_TOKEN"] = token
    
    return job
