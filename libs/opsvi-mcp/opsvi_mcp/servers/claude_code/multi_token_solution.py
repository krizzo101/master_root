"""
Multi-token solution for true parallel Claude execution
"""
import os
from typing import List, Dict, Any


class MultiTokenManager:
    """Manages multiple Claude tokens for parallel execution"""

    def __init__(self):
        # Load multiple tokens from environment
        self.tokens = self._load_tokens()
        self.token_index = 0

    def _load_tokens(self) -> List[str]:
        """Load tokens from CLAUDE_CODE_TOKEN_1, CLAUDE_CODE_TOKEN_2, etc."""
        tokens = []

        # Try primary token first
        primary = os.getenv("CLAUDE_CODE_TOKEN")
        if primary:
            tokens.append(primary)

        # Load numbered tokens
        for i in range(1, 11):  # Support up to 10 tokens
            token = os.getenv(f"CLAUDE_CODE_TOKEN_{i}")
            if token:
                tokens.append(token)

        if not tokens:
            raise ValueError(
                "No Claude tokens found. Set CLAUDE_CODE_TOKEN or CLAUDE_CODE_TOKEN_1, etc."
            )

        return tokens

    def get_next_token(self) -> str:
        """Round-robin token selection for load balancing"""
        token = self.tokens[self.token_index]
        self.token_index = (self.token_index + 1) % len(self.tokens)
        return token

    def get_token_for_job(self, job_id: str) -> str:
        """Deterministic token selection based on job ID"""
        # Use job hash to consistently assign same token to retries
        hash_val = hash(job_id)
        index = hash_val % len(self.tokens)
        return self.tokens[index]


def enhance_job_with_token(
    job: Dict[str, Any], token_manager: MultiTokenManager
) -> Dict[str, Any]:
    """Enhance job config with dedicated token"""
    job_id = job.get("id", "")
    token = token_manager.get_token_for_job(job_id)

    # Set token in job's environment
    if "env" not in job:
        job["env"] = {}
    job["env"]["CLAUDE_CODE_TOKEN"] = token

    return job


# Usage in parallel_enhancement.py:
#
# async def _execute_single_job(self, job: ClaudeJob) -> Any:
#     """Execute a single job with its own token"""
#     # Enhance job with dedicated token
#     job = enhance_job_with_token(job.to_dict(), self.token_manager)
#
#     # Now execute with unique token
#     await self.job_manager.execute_job_async(job)
