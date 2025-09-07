#!/usr/bin/env python3
"""
Enhanced TokenPool with comprehensive debug logging

This module provides a TokenPool implementation with detailed logging
of all token operations, state changes, and performance metrics.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Tuple

try:
    from .debug_logger import DebugLogger, TimedOperation
except ImportError:
    from debug_logger import DebugLogger, TimedOperation


class EnhancedTokenPool:
    """
    Enhanced TokenPool with comprehensive debug logging.
    
    Logs every token acquisition, release, state change, and performance metric
    to enable detailed analysis of token pool behavior and performance.
    """
    
    def __init__(self, tokens: List[str] = None, output_dir: Path = None):
        # Setup debug logging
        if output_dir:
            self.debug_logger = DebugLogger("TokenPool", output_dir)
        else:
            # Fallback to basic logging if no output_dir
            import logging
            self.debug_logger = logging.getLogger("TokenPool")
        
        # Log initialization parameters
        self.debug_logger.log_values("TokenPool.__init__.params",
            tokens_provided=tokens is not None,
            token_count=len(tokens) if tokens else 0,
            token_preview=[self._mask_token(t) for t in (tokens or [])[:3]],
            output_dir=str(output_dir) if output_dir else None
        )
        
        # Handle explicit tokens or call TokenTool
        if tokens is not None:
            self.tokens = [t for t in tokens if t and t.strip()]
            self.debug_logger.debug("Using explicitly provided tokens",
                                   original_count=len(tokens),
                                   filtered_count=len(self.tokens))
        else:
            # Call TokenLoader to get token pool - NO ENV FALLBACK ALLOWED
            try:
                try:
                    from .token_loader import load_tokens
                except ImportError:
                    from token_loader import load_tokens
                
                with TimedOperation(self.debug_logger, "TokenLoader.load_tokens"):
                    self.tokens = load_tokens()
                    
                if not self.tokens:
                    error_msg = "TokenLoader returned empty token list"
                    self.debug_logger.error(error_msg)
                    raise RuntimeError(error_msg)
                    
                self.debug_logger.info("Successfully loaded tokens from TokenLoader",
                                      token_count=len(self.tokens))
                
            except ImportError as e:
                error_msg = (
                    "CATASTROPHIC FAILURE: TokenLoader not available and no explicit tokens provided. "
                    "NO FALLBACK to environment variables allowed. "
                    "TokenLoader must work or system must fail."
                )
                self.debug_logger.error(error_msg, exception=str(e))
                raise RuntimeError(error_msg)
                
            except Exception as e:
                error_msg = (
                    f"CATASTROPHIC FAILURE: TokenLoader failed: {str(e)}. "
                    "NO FALLBACK to environment variables allowed."
                )
                self.debug_logger.error(error_msg, exception_type=type(e).__name__)
                raise RuntimeError(error_msg)
        
        # Ensure we have valid tokens
        if not self.tokens:
            error_msg = (
                "CATASTROPHIC FAILURE: No valid tokens available. "
                "TokenTool must provide tokens or system must fail - NO ENV FALLBACK."
            )
            self.debug_logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Initialize state
        self.current_index = 0
        self.lock = asyncio.Lock()
        self.in_use = set()  # Track tokens in use
        
        # Enhanced tracking
        self.acquisition_history = []  # Track acquisition patterns
        self.release_history = []     # Track release patterns
        self.total_acquisitions = 0
        self.total_releases = 0
        self.peak_usage = 0
        
        # Log final initialization state
        self.debug_logger.log_values("TokenPool.__init__.complete",
            total_tokens=len(self.tokens),
            current_index=self.current_index,
            tokens_in_use=list(self.in_use),
            available_tokens=self.available,
            masked_tokens=[self._mask_token(t) for t in self.tokens]
        )
        
        self.debug_logger.info("Token pool initialized successfully",
                              total_tokens=len(self.tokens),
                              available_tokens=self.available)
    
    def _mask_token(self, token: str) -> str:
        """Mask token for logging while preserving some identifiable info"""
        if not token or len(token) < 8:
            return "***"
        return f"{token[:4]}***{token[-4:]}"
    
    async def acquire(self) -> Tuple[str, int]:
        """Get next available token (round-robin) with comprehensive logging"""
        acquisition_start = time.time()
        
        # Log pre-acquisition state
        self.debug_logger.log_values("TokenPool.acquire.pre",
            current_index=self.current_index,
            tokens_in_use=list(self.in_use),
            available_count=self.available,
            total_tokens=len(self.tokens),
            total_acquisitions=self.total_acquisitions
        )
        
        async with self.lock:
            lock_acquired_time = time.time()
            
            # Log lock acquisition
            self.debug_logger.log_values("TokenPool.acquire.lock_acquired",
                lock_wait_time=lock_acquired_time - acquisition_start
            )
            
            # Get token
            token = self.tokens[self.current_index]
            token_idx = self.current_index
            old_index = self.current_index
            
            # Update state
            self.current_index = (self.current_index + 1) % len(self.tokens)
            self.in_use.add(token_idx)
            self.total_acquisitions += 1
            
            # Track peak usage
            current_usage = len(self.in_use)
            if current_usage > self.peak_usage:
                old_peak = self.peak_usage
                self.peak_usage = current_usage
                self.debug_logger.debug("New peak token usage reached",
                                       old_peak=old_peak,
                                       new_peak=self.peak_usage)
            
            # Record acquisition history
            acquisition_record = {
                "timestamp": time.time(),
                "token_idx": token_idx,
                "tokens_in_use_after": len(self.in_use),
                "available_after": self.available
            }
            self.acquisition_history.append(acquisition_record)
            
            # Log post-acquisition state
            self.debug_logger.log_values("TokenPool.acquire.post",
                acquired_token_idx=token_idx,
                masked_token=self._mask_token(token),
                old_current_index=old_index,
                new_current_index=self.current_index,
                tokens_in_use=list(self.in_use),
                available_count=self.available,
                total_acquisitions=self.total_acquisitions,
                peak_usage=self.peak_usage
            )
            
            lock_release_time = time.time()
            total_duration = lock_release_time - acquisition_start
            lock_hold_time = lock_release_time - lock_acquired_time
            
            # Log performance metrics
            self.debug_logger.log_performance("TokenPool.acquire", total_duration,
                token_idx=token_idx,
                lock_wait_time=lock_acquired_time - acquisition_start,
                lock_hold_time=lock_hold_time,
                queue_length=len(self.in_use),
                available_tokens=self.available
            )
            
            self.debug_logger.debug("Token acquired successfully",
                                   token_idx=token_idx,
                                   available_after=self.available,
                                   total_acquisitions=self.total_acquisitions)
            
            return token, token_idx
    
    def release(self, token_idx: int):
        """Release a token back to the pool with comprehensive logging"""
        release_start = time.time()
        
        # Log pre-release state
        self.debug_logger.log_values("TokenPool.release.pre",
            token_idx=token_idx,
            tokens_in_use=list(self.in_use),
            available_count=self.available,
            total_releases=self.total_releases,
            is_token_in_use=token_idx in self.in_use
        )
        
        if token_idx in self.in_use:
            old_usage = len(self.in_use)
            self.in_use.discard(token_idx)
            self.total_releases += 1
            new_usage = len(self.in_use)
            
            # Record release history
            release_record = {
                "timestamp": time.time(),
                "token_idx": token_idx,
                "tokens_in_use_after": new_usage,
                "available_after": self.available
            }
            self.release_history.append(release_record)
            
            # Log successful release
            self.debug_logger.log_values("TokenPool.release.success",
                released_token_idx=token_idx,
                old_usage=old_usage,
                new_usage=new_usage,
                tokens_in_use=list(self.in_use),
                available_count=self.available,
                total_releases=self.total_releases
            )
            
            duration = time.time() - release_start
            self.debug_logger.log_performance("TokenPool.release", duration,
                token_idx=token_idx,
                usage_before=old_usage,
                usage_after=new_usage
            )
            
            self.debug_logger.debug("Token released successfully",
                                   token_idx=token_idx,
                                   available_after=self.available,
                                   total_releases=self.total_releases)
            
        else:
            # Token not in use - log error
            self.debug_logger.log_values("TokenPool.release.error",
                token_idx=token_idx,
                tokens_in_use=list(self.in_use),
                available_count=self.available,
                error="Token not in use - cannot release"
            )
            
            self.debug_logger.warning("Attempted to release token not in use",
                                    token_idx=token_idx,
                                    current_in_use=list(self.in_use))
    
    def size(self) -> int:
        """Get total pool size with logging"""
        size = len(self.tokens)
        self.debug_logger.log_values("TokenPool.size", size=size)
        return size
    
    @property
    def available(self) -> int:
        """Get number of available tokens (not in use) with logging"""
        available = len(self.tokens) - len(self.in_use)
        self.debug_logger.log_values("TokenPool.available", 
                                    available=available,
                                    total_tokens=len(self.tokens),
                                    in_use_count=len(self.in_use))
        return available
    
    def get_stats(self) -> dict:
        """Get comprehensive statistics about token pool usage"""
        stats = {
            "total_tokens": len(self.tokens),
            "currently_in_use": len(self.in_use),
            "currently_available": self.available,
            "total_acquisitions": self.total_acquisitions,
            "total_releases": self.total_releases,
            "peak_usage": self.peak_usage,
            "current_index": self.current_index,
            "acquisition_history_length": len(self.acquisition_history),
            "release_history_length": len(self.release_history)
        }
        
        # Calculate utilization metrics
        if self.total_acquisitions > 0:
            stats["utilization_percentage"] = (self.peak_usage / len(self.tokens)) * 100
            stats["average_concurrent_usage"] = sum(
                record["tokens_in_use_after"] for record in self.acquisition_history
            ) / len(self.acquisition_history)
        
        self.debug_logger.log_values("TokenPool.get_stats", **stats)
        
        return stats
    
    def log_summary(self):
        """Log a comprehensive summary of token pool state and usage"""
        stats = self.get_stats()
        
        self.debug_logger.info("Token Pool Summary",
                              **{k: v for k, v in stats.items() if not k.endswith('_history_length')})
        
        # Log recent activity if available
        if self.acquisition_history:
            recent_acquisitions = self.acquisition_history[-5:]  # Last 5
            self.debug_logger.log_values("TokenPool.recent_acquisitions", 
                                        recent_activity=recent_acquisitions)
        
        if self.release_history:
            recent_releases = self.release_history[-5:]  # Last 5
            self.debug_logger.log_values("TokenPool.recent_releases",
                                        recent_activity=recent_releases)