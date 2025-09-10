"""
Base Intelligence Agent Framework
Provides secure, robust foundation for all intelligence agents
"""

import asyncio
import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ..core.secure_api_locker import APICredential, APILockerManager

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""

    requests_per_second: float = 1.0
    requests_per_minute: int = 60
    requests_per_hour: int = 3600
    requests_per_day: int = 86400
    burst_size: int = 5
    backoff_multiplier: float = 2.0
    max_backoff: float = 300.0


@dataclass
class RetryConfig:
    """Retry configuration for failed requests"""

    max_retries: int = 3
    backoff_factor: float = 1.0
    status_forcelist: List[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
    allowed_methods: List[str] = field(
        default_factory=lambda: ["HEAD", "GET", "OPTIONS"]
    )
    raise_on_status: bool = True


@dataclass
class CacheConfig:
    """Caching configuration"""

    enabled: bool = True
    ttl_seconds: int = 3600
    max_entries: int = 1000
    cache_dir: Optional[Path] = None
    compress: bool = True


@dataclass
class MetricsData:
    """Agent performance metrics"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cached_responses: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    rate_limit_hits: int = 0
    quota_exhausted_count: int = 0
    average_response_time: float = 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    key: str
    data: Any
    timestamp: datetime
    ttl_seconds: int
    hit_count: int = 0
    size_bytes: int = 0


class RateLimiter:
    """Thread-safe rate limiter with multiple time windows"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._lock = RLock()
        self._request_times: List[float] = []
        self._last_request_time = 0.0
        self._burst_tokens = config.burst_size
        self._last_burst_refill = time.time()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire permission to make a request"""
        start_time = time.time()

        while True:
            with self._lock:
                current_time = time.time()

                # Refill burst tokens
                time_since_refill = current_time - self._last_burst_refill
                tokens_to_add = time_since_refill * self.config.requests_per_second
                self._burst_tokens = min(
                    self.config.burst_size, self._burst_tokens + tokens_to_add
                )
                self._last_burst_refill = current_time

                # Clean old request times
                cutoff_time = current_time - 86400  # 24 hours
                self._request_times = [
                    t for t in self._request_times if t > cutoff_time
                ]

                # Check all rate limits
                if self._can_make_request(current_time):
                    # Consume burst token
                    self._burst_tokens -= 1
                    self._request_times.append(current_time)
                    self._last_request_time = current_time
                    return True

            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                return False

            # Wait before retry
            sleep_time = min(1.0 / self.config.requests_per_second, 0.1)
            time.sleep(sleep_time)

    def _can_make_request(self, current_time: float) -> bool:
        """Check if request can be made within all rate limits"""
        if self._burst_tokens < 1:
            return False

        # Check per-second limit
        recent_requests = [t for t in self._request_times if t > current_time - 1]
        if len(recent_requests) >= self.config.requests_per_second:
            return False

        # Check per-minute limit
        minute_requests = [t for t in self._request_times if t > current_time - 60]
        if len(minute_requests) >= self.config.requests_per_minute:
            return False

        # Check per-hour limit
        hour_requests = [t for t in self._request_times if t > current_time - 3600]
        if len(hour_requests) >= self.config.requests_per_hour:
            return False

        # Check per-day limit
        day_requests = [t for t in self._request_times if t > current_time - 86400]
        if len(day_requests) >= self.config.requests_per_day:
            return False

        return True


class ResponseCache:
    """LRU cache with TTL for API responses"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._lock = RLock()
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []

        # Setup disk cache if configured
        if config.cache_dir:
            self.cache_dir = Path(config.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = None

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if valid"""
        if not self.config.enabled:
            return None

        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return self._load_from_disk(key)

            # Check TTL
            if datetime.now() > entry.timestamp + timedelta(seconds=entry.ttl_seconds):
                self._remove_entry(key)
                return None

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            entry.hit_count += 1

            return entry.data

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> None:
        """Cache a value"""
        if not self.config.enabled:
            return

        ttl = ttl_seconds or self.config.ttl_seconds

        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.config.max_entries:
                self._evict_lru()

            # Create entry
            entry = CacheEntry(
                key=key,
                data=data,
                timestamp=datetime.now(),
                ttl_seconds=ttl,
                size_bytes=len(json.dumps(data, default=str).encode()) if data else 0,
            )

            self._cache[key] = entry
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            # Save to disk if configured
            self._save_to_disk(key, entry)

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._access_order:
            lru_key = self._access_order[0]
            self._remove_entry(lru_key)

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

        # Remove from disk
        if self.cache_dir:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            if cache_file.exists():
                cache_file.unlink()

    def _hash_key(self, key: str) -> str:
        """Generate safe filename from cache key"""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def _save_to_disk(self, key: str, entry: CacheEntry) -> None:
        """Save cache entry to disk"""
        if not self.cache_dir:
            return

        try:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            cache_data = {
                "key": entry.key,
                "data": entry.data,
                "timestamp": entry.timestamp.isoformat(),
                "ttl_seconds": entry.ttl_seconds,
                "hit_count": entry.hit_count,
            }

            if self.config.compress:
                import gzip

                with gzip.open(cache_file, "wt", encoding="utf-8") as f:
                    json.dump(cache_data, f)
            else:
                with open(cache_file, "w") as f:
                    json.dump(cache_data, f)

        except Exception as e:
            logger.warning(f"Failed to save cache entry to disk: {e}")

    def _load_from_disk(self, key: str) -> Optional[Any]:
        """Load cache entry from disk"""
        if not self.cache_dir:
            return None

        try:
            cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
            if not cache_file.exists():
                return None

            if self.config.compress:
                import gzip

                with gzip.open(cache_file, "rt", encoding="utf-8") as f:
                    cache_data = json.load(f)
            else:
                with open(cache_file) as f:
                    cache_data = json.load(f)

            # Check TTL
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            if datetime.now() > timestamp + timedelta(
                seconds=cache_data["ttl_seconds"]
            ):
                cache_file.unlink()
                return None

            # Restore to memory cache
            entry = CacheEntry(
                key=cache_data["key"],
                data=cache_data["data"],
                timestamp=timestamp,
                ttl_seconds=cache_data["ttl_seconds"],
                hit_count=cache_data.get("hit_count", 0),
            )
            self._cache[key] = entry
            self._access_order.append(key)

            return entry.data

        except Exception as e:
            logger.warning(f"Failed to load cache entry from disk: {e}")
            return None


class BaseIntelligenceAgent(ABC):
    """
    Abstract base class for all intelligence agents
    Provides secure credential management, rate limiting, caching, and monitoring
    """

    def __init__(
        self,
        provider: str,
        agent_name: str,
        rate_limit_config: Optional[RateLimitConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        self.provider = provider
        self.agent_name = agent_name
        self.timeout = timeout
        self.custom_headers = custom_headers or {}

        # Configuration
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.retry_config = retry_config or RetryConfig()
        self.cache_config = cache_config or CacheConfig()

        # Components
        self.api_locker = APILockerManager.get_instance()
        self.rate_limiter = RateLimiter(self.rate_limit_config)
        self.cache = ResponseCache(self.cache_config)

        # Metrics
        self.metrics = MetricsData()
        self._metrics_lock = Lock()

        # Session setup
        self._setup_session()

        # Logging
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        self.logger.info(f"Initialized {agent_name} agent for provider {provider}")

    def _setup_session(self) -> None:
        """Setup requests session with retry strategy"""
        self.session = requests.Session()

        retry_strategy = Retry(
            total=self.retry_config.max_retries,
            backoff_factor=self.retry_config.backoff_factor,
            status_forcelist=self.retry_config.status_forcelist,
            allowed_methods=self.retry_config.allowed_methods,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "User-Agent": f"SleuthIntel-{self.agent_name}/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                **self.custom_headers,
            }
        )

    def get_credential(self) -> Optional[APICredential]:
        """Get API credential for this provider"""
        return self.api_locker.get_credential(self.provider)

    def _generate_cache_key(self, method: str, url: str, **kwargs) -> str:
        """Generate cache key from request parameters"""
        # Create deterministic key from request parameters
        params = {
            "method": method,
            "url": url,
            "params": kwargs.get("params", {}),
            "json": kwargs.get("json", {}),
            "data": kwargs.get("data", {}),
        }

        # Sort and serialize for consistent hashing
        key_str = json.dumps(params, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _update_metrics(
        self, success: bool, response_time: float, cached: bool = False
    ) -> None:
        """Update agent metrics"""
        with self._metrics_lock:
            self.metrics.total_requests += 1
            self.metrics.last_request_time = datetime.now()

            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1

            if cached:
                self.metrics.cached_responses += 1

            self.metrics.total_response_time += response_time
            self.metrics.average_response_time = (
                self.metrics.total_response_time / self.metrics.total_requests
            )

    def _handle_rate_limit_error(self, response: requests.Response) -> Optional[float]:
        """Handle rate limit response and return retry delay"""
        with self._metrics_lock:
            self.metrics.rate_limit_hits += 1

        # Try to extract retry delay from headers
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass

        # Use exponential backoff
        return min(
            self.rate_limit_config.backoff_multiplier**self.metrics.rate_limit_hits,
            self.rate_limit_config.max_backoff,
        )

    def make_request(
        self,
        method: str,
        url: str,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        **kwargs,
    ) -> requests.Response:
        """
        Make authenticated HTTP request with rate limiting, retry, and caching

        Args:
            method: HTTP method
            url: Request URL
            use_cache: Whether to use response caching
            cache_ttl: Custom cache TTL in seconds
            **kwargs: Additional arguments for requests

        Returns:
            requests.Response object

        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: On authentication failure
        """
        start_time = time.time()

        # Generate cache key
        cache_key = (
            self._generate_cache_key(method, url, **kwargs) if use_cache else None
        )

        # Check cache first
        if cache_key:
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for {method} {url}")
                # Create mock response object
                mock_response = requests.Response()
                mock_response._content = json.dumps(cached_response).encode()
                mock_response.status_code = 200
                mock_response.headers["Content-Type"] = "application/json"

                response_time = time.time() - start_time
                self._update_metrics(True, response_time, cached=True)
                return mock_response

        # Get credential
        credential = self.get_credential()
        if not credential:
            raise ValueError(
                f"No API credentials available for provider: {self.provider}"
            )

        # Apply authentication
        kwargs = self._apply_authentication(credential, kwargs)

        # Rate limiting
        if not self.rate_limiter.acquire(timeout=60):
            raise requests.exceptions.RequestException("Rate limit timeout")

        try:
            # Make request
            self.logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)

            # Handle rate limiting
            if response.status_code == 429:
                retry_delay = self._handle_rate_limit_error(response)
                if retry_delay:
                    self.logger.warning(f"Rate limited, waiting {retry_delay}s")
                    time.sleep(retry_delay)
                    # Retry once after rate limit
                    if self.rate_limiter.acquire(timeout=60):
                        response = self.session.request(
                            method, url, timeout=self.timeout, **kwargs
                        )

            # Handle quota exhaustion
            if response.status_code == 402 or "quota" in response.text.lower():
                with self._metrics_lock:
                    self.metrics.quota_exhausted_count += 1
                self.logger.error(f"Quota exhausted for provider {self.provider}")

            # Validate response if configured
            if self.retry_config.raise_on_status:
                response.raise_for_status()

            # Cache successful responses
            if cache_key and response.status_code == 200:
                try:
                    response_data = response.json()
                    self.cache.set(cache_key, response_data, cache_ttl)
                except (ValueError, json.JSONDecodeError):
                    # Non-JSON response, cache raw text
                    self.cache.set(cache_key, response.text, cache_ttl)

            response_time = time.time() - start_time
            self._update_metrics(True, response_time)

            self.logger.debug(f"Request completed in {response_time:.2f}s")
            return response

        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(False, response_time)
            self.logger.error(f"Request failed: {e}")
            raise

    async def make_async_request(
        self,
        method: str,
        url: str,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None,
        **kwargs,
    ) -> aiohttp.ClientResponse:
        """
        Make authenticated async HTTP request

        Args:
            method: HTTP method
            url: Request URL
            use_cache: Whether to use response caching
            cache_ttl: Custom cache TTL in seconds
            **kwargs: Additional arguments for aiohttp

        Returns:
            aiohttp.ClientResponse object
        """
        start_time = time.time()

        # Generate cache key
        cache_key = (
            self._generate_cache_key(method, url, **kwargs) if use_cache else None
        )

        # Check cache first
        if cache_key:
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self.logger.debug(f"Cache hit for async {method} {url}")
                response_time = time.time() - start_time
                self._update_metrics(True, response_time, cached=True)

                # Return cached data wrapped in mock response
                class MockAsyncResponse:
                    def __init__(self, data):
                        self.status = 200
                        self._data = data

                    async def json(self):
                        return self._data

                    async def text(self):
                        return json.dumps(self._data)

                return MockAsyncResponse(cached_response)

        # Get credential
        credential = self.get_credential()
        if not credential:
            raise ValueError(
                f"No API credentials available for provider: {self.provider}"
            )

        # Apply authentication
        kwargs = self._apply_authentication(credential, kwargs)

        # Rate limiting (async-safe)
        if not self.rate_limiter.acquire(timeout=60):
            raise aiohttp.ClientError("Rate limit timeout")

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = kwargs.pop("headers", {})
            headers.update(self.session.headers)

            async with aiohttp.ClientSession(
                timeout=timeout, headers=headers
            ) as session:
                async with session.request(method, url, **kwargs) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        retry_delay = self._handle_rate_limit_error_async(response)
                        if retry_delay:
                            await asyncio.sleep(retry_delay)
                            # Retry once
                            if self.rate_limiter.acquire(timeout=60):
                                async with session.request(
                                    method, url, **kwargs
                                ) as retry_response:
                                    response = retry_response

                    # Cache successful responses
                    if cache_key and response.status == 200:
                        try:
                            response_data = await response.json()
                            self.cache.set(cache_key, response_data, cache_ttl)
                        except Exception:
                            response_text = await response.text()
                            self.cache.set(cache_key, response_text, cache_ttl)

                    response_time = time.time() - start_time
                    self._update_metrics(True, response_time)

                    return response

        except Exception as e:
            response_time = time.time() - start_time
            self._update_metrics(False, response_time)
            self.logger.error(f"Async request failed: {e}")
            raise

    def _handle_rate_limit_error_async(self, response) -> Optional[float]:
        """Handle async rate limit response"""
        with self._metrics_lock:
            self.metrics.rate_limit_hits += 1

        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass

        return min(
            self.rate_limit_config.backoff_multiplier**self.metrics.rate_limit_hits,
            self.rate_limit_config.max_backoff,
        )

    @abstractmethod
    def _apply_authentication(
        self, credential: APICredential, request_kwargs: Dict
    ) -> Dict:
        """
        Apply authentication to request based on credential

        Args:
            credential: API credential
            request_kwargs: Request arguments to modify

        Returns:
            Modified request arguments with authentication
        """
        pass

    @abstractmethod
    def query(self, query_params: Dict[str, Any], **kwargs) -> Any:
        """
        Execute intelligence query

        Args:
            query_params: Query parameters specific to the agent
            **kwargs: Additional arguments

        Returns:
            Query results
        """
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        with self._metrics_lock:
            return {
                "agent_name": self.agent_name,
                "provider": self.provider,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": (
                    self.metrics.successful_requests
                    / max(1, self.metrics.total_requests)
                    * 100
                ),
                "cached_responses": self.metrics.cached_responses,
                "cache_hit_rate": (
                    self.metrics.cached_responses
                    / max(1, self.metrics.total_requests)
                    * 100
                ),
                "average_response_time": self.metrics.average_response_time,
                "last_request_time": self.metrics.last_request_time.isoformat()
                if self.metrics.last_request_time
                else None,
                "rate_limit_hits": self.metrics.rate_limit_hits,
                "quota_exhausted_count": self.metrics.quota_exhausted_count,
            }

    def reset_metrics(self) -> None:
        """Reset agent metrics"""
        with self._metrics_lock:
            self.metrics = MetricsData()
        self.logger.info(f"Metrics reset for {self.agent_name}")

    def clear_cache(self) -> None:
        """Clear agent cache"""
        self.cache = ResponseCache(self.cache_config)
        self.logger.info(f"Cache cleared for {self.agent_name}")

    def health_check(self) -> Dict[str, Any]:
        """Perform agent health check"""
        try:
            credential = self.get_credential()
            if not credential:
                return {
                    "status": "unhealthy",
                    "error": f"No credentials available for provider {self.provider}",
                    "timestamp": datetime.now().isoformat(),
                }

            # Test basic connectivity (subclasses should override for provider-specific checks)
            health_status = {
                "status": "healthy",
                "provider": self.provider,
                "agent_name": self.agent_name,
                "credential_available": True,
                "timestamp": datetime.now().isoformat(),
                "metrics": self.get_metrics(),
            }

            return health_status

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider}, agent={self.agent_name})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"provider='{self.provider}', "
            f"agent_name='{self.agent_name}', "
            f"requests={self.metrics.total_requests})"
        )
