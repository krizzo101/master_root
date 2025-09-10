"""
EnformionGO API Client for Sleuth Intel
Handles API requests to EnformionGO with secure credential management
"""

import asyncio
import hashlib
import json
import logging
import sys
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urlencode, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.secure_api_locker import APICredential, api_locker_manager

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of API errors"""

    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    NETWORK = "network"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    API_ERROR = "api_error"
    CIRCUIT_BREAKER = "circuit_breaker"
    UNKNOWN = "unknown"


class EnformionAPIError(Exception):
    """Enhanced exception for EnformionGO API errors with classification"""

    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
        retry_after: Optional[int] = None,
        credit_cost: Optional[int] = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.status_code = status_code
        self.response_data = response_data
        self.retry_after = retry_after
        self.credit_cost = credit_cost
        self.timestamp = datetime.now()

    def is_retryable(self) -> bool:
        """Check if error is retryable"""
        return self.error_type in [
            ErrorType.RATE_LIMIT,
            ErrorType.NETWORK,
            ErrorType.TIMEOUT,
        ]


@dataclass
class RequestMetrics:
    """Metrics for API requests"""

    endpoint: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    credit_cost: Optional[int] = None
    cache_hit: bool = False
    error_type: Optional[ErrorType] = None

    def finish(
        self,
        status_code: int,
        credit_cost: Optional[int] = None,
        error_type: Optional[ErrorType] = None,
    ):
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status_code = status_code
        self.credit_cost = credit_cost
        self.error_type = error_type


@dataclass
class CacheEntry:
    """Cache entry with TTL"""

    data: Dict
    expires_at: datetime
    credit_cost: int = 1
    hit_count: int = 0

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def hit(self) -> Dict:
        self.hit_count += 1
        return self.data


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for API reliability"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs):
        with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if (
                    datetime.now() - self.last_failure_time
                ).total_seconds() > self.config.timeout_seconds:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise EnformionAPIError(
                        "Circuit breaker is open", error_type=ErrorType.CIRCUIT_BREAKER
                    )

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except EnformionAPIError as e:
                self._on_failure()
                raise

    def _on_success(self):
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN


@dataclass
class EndpointConfig:
    """Configuration for each API endpoint"""

    path: str
    credit_cost: int = 1
    cache_ttl_minutes: int = 60
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate_per_minute: int, burst_size: Optional[int] = None):
        self.rate_per_second = rate_per_minute / 60.0
        self.burst_size = burst_size or rate_per_minute
        self.tokens = self.burst_size
        self.last_update = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens_needed: int = 1) -> bool:
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Add tokens based on elapsed time
            self.tokens = min(
                self.burst_size, self.tokens + elapsed * self.rate_per_second
            )

            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return True
            return False

    def wait_time(self, tokens_needed: int = 1) -> float:
        """Calculate wait time for tokens"""
        with self.lock:
            if self.tokens >= tokens_needed:
                return 0
            return (tokens_needed - self.tokens) / self.rate_per_second


class EnformionClient:
    """Enhanced client for EnformionGO API with advanced features"""

    # API endpoint configurations - Updated for correct EnformionGO API
    ENDPOINTS = {
        "reverse_phone": EndpointConfig(
            "/ReversePhone", credit_cost=1, cache_ttl_minutes=180
        ),
        "person_search": EndpointConfig(
            "/PersonSearch", credit_cost=1, cache_ttl_minutes=60
        ),
        "business_search": EndpointConfig(
            "/BusinessSearch", credit_cost=2, cache_ttl_minutes=120
        ),
        "contact_enrichment": EndpointConfig(
            "/Contact/Enrich", credit_cost=2, cache_ttl_minutes=60
        ),
    }

    def __init__(
        self,
        base_url: str = "https://devapi.enformion.com",
        enable_caching: bool = True,
        enable_metrics: bool = True,
        enable_circuit_breaker: bool = True,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
        rate_limit_per_minute: int = 60,
    ):
        self.base_url = base_url
        self.enable_caching = enable_caching
        self.enable_metrics = enable_metrics
        self.enable_circuit_breaker = enable_circuit_breaker

        # Initialize session with connection pooling
        self.session = self._create_session(
            pool_connections, pool_maxsize, max_retries, backoff_factor
        )

        # Rate limiting
        self.rate_limiter = RateLimiter(rate_limit_per_minute)

        # Caching
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.Lock()

        # Metrics
        self.metrics: List[RequestMetrics] = []
        self.metrics_lock = threading.Lock()
        self.total_requests = 0
        self.total_credits_used = 0
        self.total_cache_hits = 0

        # Circuit breaker
        if enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig())

        # Request queue for throttling
        self.request_queue = deque()
        self.queue_lock = threading.Lock()

        # Credit tracking
        self.credit_usage = defaultdict(int)
        self.credit_predictions = {}

        # Credentials
        self._credential: Optional[APICredential] = None
        self._load_credentials()

        logger.info(
            f"EnformionClient initialized with caching={enable_caching}, metrics={enable_metrics}, circuit_breaker={enable_circuit_breaker}"
        )

    def _create_session(
        self,
        pool_connections: int,
        pool_maxsize: int,
        max_retries: int,
        backoff_factor: float,
    ) -> requests.Session:
        """Create session with connection pooling and retry strategy"""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=backoff_factor,
            allowed_methods=["GET", "POST"],
        )

        # HTTP adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
            pool_block=False,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _load_credentials(self):
        """Load EnformionGO credentials from secure locker"""
        try:
            # Get the most recent credential (after any fixes)
            credentials_list = api_locker_manager.locker.get_all_credentials(
                "enformion"
            )
            if not credentials_list:
                raise EnformionAPIError(
                    "No EnformionGO credentials found in secure locker",
                    error_type=ErrorType.AUTHENTICATION,
                )

            # Use the most recently added credential (last in list)
            self._credential = credentials_list[-1]

            logger.info(f"Loaded EnformionGO credentials: {self._credential.key_name}")

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            raise EnformionAPIError(
                f"Credential loading failed: {e}", error_type=ErrorType.AUTHENTICATION
            )

    def _get_auth_headers(self, search_type: str = None) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if not self._credential:
            raise EnformionAPIError(
                "No credentials loaded", error_type=ErrorType.AUTHENTICATION
            )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SleuthIntel/2.0-Enhanced",
        }

        # EnformionGO uses galaxy headers for authentication
        headers["galaxy-ap-name"] = self._credential.key_value
        headers["galaxy-ap-password"] = self._credential.password
        headers["galaxy-client-session-id"] = self._generate_request_id()

        # Add search type if provided
        if search_type:
            headers["galaxy-search-type"] = search_type

        return headers

    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking"""
        return f"sleuth-{int(time.time() * 1000)}-{threading.current_thread().ident}"

    def _get_cache_key(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> str:
        """Generate cache key for request"""
        key_parts = [method.upper(), endpoint]
        if params:
            # Sort params for consistent cache keys
            sorted_params = sorted(params.items())
            key_parts.append(urlencode(sorted_params))
        if data:
            # Hash data for cache key
            data_str = json.dumps(data, sort_keys=True)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()
            key_parts.append(data_hash)
        return ":".join(key_parts)

    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available and not expired"""
        if not self.enable_caching:
            return None

        with self.cache_lock:
            entry = self.cache.get(cache_key)
            if entry and not entry.is_expired():
                return entry.hit()
            elif entry:
                # Remove expired entry
                del self.cache[cache_key]
        return None

    def _cache_response(
        self, cache_key: str, response: Dict, endpoint_config: EndpointConfig
    ):
        """Cache response with TTL"""
        if not self.enable_caching or endpoint_config.cache_ttl_minutes <= 0:
            return

        expires_at = datetime.now() + timedelta(
            minutes=endpoint_config.cache_ttl_minutes
        )
        entry = CacheEntry(
            data=response,
            expires_at=expires_at,
            credit_cost=endpoint_config.credit_cost,
        )

        with self.cache_lock:
            self.cache[cache_key] = entry
            # Clean up old entries periodically
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self.cache[key]

    def _record_metrics(self, metrics: RequestMetrics):
        """Record request metrics"""
        if not self.enable_metrics:
            return

        with self.metrics_lock:
            self.metrics.append(metrics)
            self.total_requests += 1
            if metrics.credit_cost:
                self.total_credits_used += metrics.credit_cost
            if metrics.cache_hit:
                self.total_cache_hits += 1

            # Keep only last 1000 metrics to prevent memory growth
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]

    def _wait_for_rate_limit(self, credit_cost: int = 1):
        """Wait for rate limit availability"""
        while not self.rate_limiter.acquire(credit_cost):
            wait_time = self.rate_limiter.wait_time(credit_cost)
            logger.debug(f"Rate limited, waiting {wait_time:.2f} seconds")
            time.sleep(min(wait_time, 1.0))  # Max 1 second wait

    def _classify_error(
        self, response: requests.Response, exception: Optional[Exception] = None
    ) -> ErrorType:
        """Classify API error for better handling"""
        if exception:
            if isinstance(exception, requests.exceptions.Timeout):
                return ErrorType.TIMEOUT
            elif isinstance(exception, requests.exceptions.ConnectionError):
                return ErrorType.NETWORK

        if response.status_code == 401:
            return ErrorType.AUTHENTICATION
        elif response.status_code == 429:
            return ErrorType.RATE_LIMIT
        elif response.status_code == 402:
            return ErrorType.QUOTA_EXCEEDED
        elif 400 <= response.status_code < 500:
            return ErrorType.VALIDATION
        elif response.status_code >= 500:
            return ErrorType.API_ERROR

        return ErrorType.UNKNOWN

    def _extract_retry_after(self, response: requests.Response) -> Optional[int]:
        """Extract retry-after header value"""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        return None

    def _get_endpoint_config(self, endpoint: str) -> EndpointConfig:
        """Get configuration for endpoint"""
        for name, config in self.ENDPOINTS.items():
            if config.path.lstrip("/") in endpoint.lstrip("/"):
                return config
        # Default config for unknown endpoints
        return EndpointConfig(endpoint, credit_cost=1)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        skip_cache: bool = False,
        skip_rate_limit: bool = False,
        search_type: str = None,
    ) -> Dict:
        """Enhanced request method with caching, rate limiting, and error handling"""
        endpoint_config = self._get_endpoint_config(endpoint)
        cache_key = self._get_cache_key(method, endpoint, params, data)

        # Start metrics
        metrics = RequestMetrics(endpoint=endpoint, start_time=datetime.now())

        try:
            # Check cache first
            if not skip_cache:
                cached_response = self._get_from_cache(cache_key)
                if cached_response:
                    metrics.cache_hit = True
                    metrics.finish(200, 0)  # No credit cost for cache hits
                    self._record_metrics(metrics)
                    logger.debug(f"Cache hit for {endpoint}")
                    return cached_response

            # Rate limiting
            if (
                not skip_rate_limit
                and hasattr(self, "rate_limiter")
                and self.rate_limiter
            ):
                self._wait_for_rate_limit(endpoint_config.credit_cost)

            # Make the actual request
            def _execute_request():
                return self._execute_request(
                    method, endpoint, params, data, endpoint_config, search_type
                )

            if self.enable_circuit_breaker:
                result = self.circuit_breaker.call(_execute_request)
            else:
                result = _execute_request()

            # Cache successful response
            if not skip_cache:
                self._cache_response(cache_key, result, endpoint_config)

            # Record successful metrics
            metrics.finish(200, endpoint_config.credit_cost)
            self._record_metrics(metrics)

            # Update credit usage
            self.credit_usage[endpoint] += endpoint_config.credit_cost

            return result

        except EnformionAPIError as e:
            metrics.finish(
                e.status_code or 0, endpoint_config.credit_cost, e.error_type
            )
            self._record_metrics(metrics)
            raise
        except Exception as e:
            metrics.finish(0, endpoint_config.credit_cost, ErrorType.UNKNOWN)
            self._record_metrics(metrics)
            raise EnformionAPIError(
                f"Unexpected error: {e}", error_type=ErrorType.UNKNOWN
            )

    def _execute_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict],
        data: Optional[Dict],
        endpoint_config: EndpointConfig,
        search_type: str = None,
    ) -> Dict:
        """Execute the actual HTTP request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_auth_headers(search_type)

        logger.debug(f"Making {method} request to {endpoint}")

        try:
            if method.upper() == "GET":
                response = self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=endpoint_config.timeout_seconds,
                )
            elif method.upper() == "POST":
                response = self.session.post(
                    url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=endpoint_config.timeout_seconds,
                )
            elif method.upper() == "PUT":
                response = self.session.put(
                    url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=endpoint_config.timeout_seconds,
                )
            elif method.upper() == "DELETE":
                response = self.session.delete(
                    url,
                    headers=headers,
                    params=params,
                    timeout=endpoint_config.timeout_seconds,
                )
            else:
                raise EnformionAPIError(
                    f"Unsupported HTTP method: {method}",
                    error_type=ErrorType.VALIDATION,
                )

            # Enhanced error handling
            if not response.ok:
                error_type = self._classify_error(response)
                retry_after = self._extract_retry_after(response)

                error_msg = f"API request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', 'Unknown error')}"
                    if "details" in error_data:
                        error_msg += f" Details: {error_data['details']}"
                except:
                    error_msg += f" - {response.text[:500]}"  # Limit error text

                raise EnformionAPIError(
                    error_msg,
                    error_type=error_type,
                    status_code=response.status_code,
                    response_data=error_data if "error_data" in locals() else None,
                    retry_after=retry_after,
                    credit_cost=endpoint_config.credit_cost,
                )

            # Parse response
            try:
                result = response.json()
            except json.JSONDecodeError:
                raise EnformionAPIError(
                    "Invalid JSON response from API",
                    error_type=ErrorType.API_ERROR,
                    status_code=response.status_code,
                )

            logger.debug(f"API request successful: {len(str(result))} characters")
            return result

        except requests.exceptions.Timeout:
            raise EnformionAPIError("Request timed out", error_type=ErrorType.TIMEOUT)
        except requests.exceptions.ConnectionError:
            raise EnformionAPIError("Connection error", error_type=ErrorType.NETWORK)
        except requests.exceptions.RequestException as e:
            raise EnformionAPIError(
                f"Request failed: {e}", error_type=ErrorType.NETWORK
            )

    # =====================================================
    # ENHANCED API METHODS WITH ADVANCED FEATURES
    # =====================================================

    def reverse_phone_search(
        self, phone_number: str, include_metadata: bool = True, skip_cache: bool = False
    ) -> Dict[str, Any]:
        """Enhanced reverse phone lookup with metadata

        Note: Free accounts use Contact Enrichment for phone lookups
        since PersonSearch/ReversePhone requires paid access.

        Args:
            phone_number: Phone number to lookup (e.g., '9103925349')
            include_metadata: Include additional metadata about the lookup
            skip_cache: Skip cache and force fresh API call

        Returns:
            Dict containing person/business info associated with the phone
        """
        phone_clean = "".join(filter(str.isdigit, phone_number))

        # Format phone number with dashes for EnformionGO API
        if len(phone_clean) == 10:
            formatted_phone = f"{phone_clean[:3]}-{phone_clean[3:6]}-{phone_clean[6:]}"
        else:
            formatted_phone = phone_clean

        if not phone_clean or len(phone_clean) < 10:
            raise EnformionAPIError(
                "Invalid phone number format", error_type=ErrorType.VALIDATION
            )

        # Free accounts: Use contact enrichment with phone + minimal data to trigger search
        # We'll use common placeholder data to make the API accept the phone lookup
        result = self.contact_enrichment(
            phone=formatted_phone,
            first_name="",  # Empty but present to satisfy API requirements
            last_name="",  # Empty but present to satisfy API requirements
        )

        # Add reverse phone metadata
        if include_metadata:
            result["_sleuth_metadata"] = {
                "query_phone": phone_number,
                "formatted_phone": formatted_phone,
                "lookup_timestamp": datetime.now().isoformat(),
                "method": "contact_enrichment_with_phone",
                "note": "Free account - using contact enrichment for phone lookup",
                "credit_cost": self.ENDPOINTS["contact_enrichment"].credit_cost,
            }

        return result

    def caller_id_lookup(
        self,
        phone_number: str,
        include_carrier_info: bool = True,
        skip_cache: bool = False,
    ) -> Dict[str, Any]:
        """Enhanced caller ID lookup with carrier information

        Args:
            phone_number: Phone number to lookup
            include_carrier_info: Include carrier and line type information
            skip_cache: Skip cache and force fresh API call

        Returns:
            Dict with caller name, contact info, and carrier details
        """
        phone_clean = "".join(filter(str.isdigit, phone_number))

        if not phone_clean or len(phone_clean) < 10:
            raise EnformionAPIError(
                "Invalid phone number format", error_type=ErrorType.VALIDATION
            )

        params = {"phone": phone_clean}
        if include_carrier_info:
            params["include_carrier"] = "true"

        result = self._make_request(
            "GET", "/callerid", params=params, skip_cache=skip_cache
        )

        # Enhance with metadata
        result["_sleuth_metadata"] = {
            "query_phone": phone_number,
            "normalized_phone": phone_clean,
            "lookup_timestamp": datetime.now().isoformat(),
            "credit_cost": self.ENDPOINTS["caller_id"].credit_cost,
        }

        return result

    def person_search(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        age_range: Optional[tuple] = None,
        include_relatives: bool = False,
        include_associates: bool = False,
        confidence_threshold: float = 0.7,
        max_results: int = 50,
        skip_cache: bool = False,
    ) -> Dict[str, Any]:
        """Enhanced person search with advanced filtering

        Args:
            first_name: First name
            last_name: Last name
            address: Street address
            city: City
            state: State abbreviation
            zip_code: ZIP code
            phone: Phone number
            email: Email address
            age_range: Tuple of (min_age, max_age)
            include_relatives: Include known relatives
            include_associates: Include business associates
            confidence_threshold: Minimum confidence score (0.0-1.0)
            max_results: Maximum number of results to return
            skip_cache: Skip cache and force fresh API call

        Returns:
            Dict with person details and contact info
        """
        params = {}

        # Basic search parameters
        if first_name:
            params["first_name"] = first_name.strip()
        if last_name:
            params["last_name"] = last_name.strip()
        if address:
            params["address"] = address.strip()
        if city:
            params["city"] = city.strip()
        if state:
            params["state"] = state.strip().upper()
        if zip_code:
            params["zip"] = zip_code.strip()
        if phone:
            params["phone"] = "".join(filter(str.isdigit, phone))
        if email:
            params["email"] = email.strip().lower()

        # Advanced parameters
        if age_range:
            params["min_age"] = age_range[0]
            params["max_age"] = age_range[1]
        if include_relatives:
            params["include_relatives"] = "true"
        if include_associates:
            params["include_associates"] = "true"
        if confidence_threshold != 0.7:
            params["min_confidence"] = confidence_threshold
        if max_results != 50:
            params["limit"] = max_results

        if not params:
            raise EnformionAPIError(
                "At least one search parameter is required",
                error_type=ErrorType.VALIDATION,
            )

        result = self._make_request(
            "GET", "/person-search", params=params, skip_cache=skip_cache
        )

        # Add search metadata
        result["_sleuth_metadata"] = {
            "search_params": params,
            "lookup_timestamp": datetime.now().isoformat(),
            "credit_cost": self.ENDPOINTS["person_search"].credit_cost,
        }

        return result

    def business_search(
        self,
        business_name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        phone: Optional[str] = None,
        tax_id: Optional[str] = None,
        industry: Optional[str] = None,
        include_principals: bool = False,
        include_competitors: bool = False,
        include_financial: bool = False,
        max_results: int = 25,
        skip_cache: bool = False,
    ) -> Dict[str, Any]:
        """Enhanced business search with comprehensive data

        Args:
            business_name: Business name
            address: Business address
            city: City
            state: State abbreviation
            zip_code: ZIP code
            phone: Business phone number
            tax_id: Tax identification number
            industry: Industry classification
            include_principals: Include principal/owner information
            include_competitors: Include competitor analysis
            include_financial: Include financial indicators
            max_results: Maximum number of results
            skip_cache: Skip cache and force fresh API call

        Returns:
            Dict with comprehensive business intelligence
        """
        params = {}

        if business_name:
            params["business_name"] = business_name.strip()
        if address:
            params["address"] = address.strip()
        if city:
            params["city"] = city.strip()
        if state:
            params["state"] = state.strip().upper()
        if zip_code:
            params["zip"] = zip_code.strip()
        if phone:
            params["phone"] = "".join(filter(str.isdigit, phone))
        if tax_id:
            params["tax_id"] = tax_id.strip()
        if industry:
            params["industry"] = industry.strip()

        # Advanced parameters
        if include_principals:
            params["include_principals"] = "true"
        if include_competitors:
            params["include_competitors"] = "true"
        if include_financial:
            params["include_financial"] = "true"
        if max_results != 25:
            params["limit"] = max_results

        if not params:
            raise EnformionAPIError(
                "At least one search parameter is required",
                error_type=ErrorType.VALIDATION,
            )

        result = self._make_request(
            "GET", "/business-search", params=params, skip_cache=skip_cache
        )

        # Add search metadata
        result["_sleuth_metadata"] = {
            "search_params": params,
            "lookup_timestamp": datetime.now().isoformat(),
            "credit_cost": self.ENDPOINTS["business_search"].credit_cost,
        }

        return result

    def identity_verification(
        self,
        first_name: str,
        last_name: str,
        address: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify identity and fill in missing details

        Args:
            first_name: First name
            last_name: Last name
            address: Address
            phone: Phone number (optional)
            email: Email address (optional)

        Returns:
            Dict with identity verification results and enriched data
        """
        params = {"first_name": first_name, "last_name": last_name, "address": address}

        if phone:
            params["phone"] = phone
        if email:
            params["email"] = email

        return self._make_request("GET", "/id-verification", params=params)

    def contact_enrichment(
        self,
        first_name: str = None,
        last_name: str = None,
        phone: str = None,
        email: str = None,
        address_line1: str = None,
        address_line2: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Enrich contact with additional information

        Args:
            first_name: First name
            last_name: Last name
            phone: Phone number
            email: Email address
            address_line1: Street address
            address_line2: City, State ZIP

        Returns:
            Dict with enriched contact information
        """
        data = {}

        if first_name:
            data["FirstName"] = first_name
        if last_name:
            data["LastName"] = last_name
        if phone:
            data["Phone"] = phone
        if email:
            data["Email"] = email

        if address_line1 or address_line2:
            data["Address"] = {}
            if address_line1:
                data["Address"]["addressLine1"] = address_line1
            if address_line2:
                data["Address"]["addressLine2"] = address_line2

        # Add any additional fields
        data.update(kwargs)

        if not data:
            raise EnformionAPIError("At least one contact field is required")

        return self._make_request(
            "POST", "/Contact/Enrich", data=data, search_type="DevAPIContactEnrich"
        )

    def get_account_status(self) -> Dict[str, Any]:
        """Get account status and usage information"""
        return self._make_request("GET", "/account/status")


# Convenience functions for common use cases


def lookup_phone(phone_number: str) -> Dict[str, Any]:
    """Quick phone number lookup"""
    client = EnformionClient()
    return client.reverse_phone_search(phone_number)


def lookup_person(
    first_name: str,
    last_name: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """Quick person lookup"""
    client = EnformionClient()
    return client.person_search(
        first_name=first_name, last_name=last_name, city=city, state=state
    )


def verify_identity(first_name: str, last_name: str, address: str) -> Dict[str, Any]:
    """Quick identity verification"""
    client = EnformionClient()
    return client.identity_verification(first_name, last_name, address)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    try:
        client = EnformionClient()

        # Test account status
        print("Testing account status...")
        status = client.get_account_status()
        print(f"Account Status: {json.dumps(status, indent=2)}")

        # Test reverse phone lookup
        print("\nTesting reverse phone lookup...")
        phone_result = client.reverse_phone_search("9103925349")
        print(f"Phone Lookup Result: {json.dumps(phone_result, indent=2)}")

    except EnformionAPIError as e:
        print(f"EnformionGO API Error: {e}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")
        if e.response_data:
            print(f"Response Data: {json.dumps(e.response_data, indent=2)}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
