#!/usr/bin/env python3
"""
Async Web Server Implementation

Based on the Web API System Architecture design, this module provides:
- HTTP server foundation using aiohttp
- Request orchestration with proven GenericOrchestrator patterns
- Quality gates pipeline for request validation
- Real-time metrics and monitoring
- Support for ExecutionPlan integration
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import aiohttp.web_middlewares
from aiohttp import ClientSession, web
from aiohttp.web import Request, Response, json_response

# Import orchestrator components
from .generic_orchestrator import AgentTask, GenericOrchestrator
from .quality_gates import QualityGateManager, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class APIRequest:
    """
    API request representation following AgentTask pattern
    Based on architectural design specifications
    """

    request_type: str  # GET, POST, PUT, DELETE
    endpoint: str
    method_handler: str  # Handler method name
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Optional[Dict] = None
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, processing, completed, failed
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class APIResponse:
    """API response structure"""

    request_id: str
    status: str  # completed, failed
    data: Optional[Dict] = None
    error: Optional[str] = None
    duration_ms: float = 0
    cacheable: bool = False
    cache_ttl: int = 300


class RequestQualityGate:
    """
    Base class for request quality gates
    Based on quality gate patterns from architecture
    """

    async def validate_rate_limit(self, request: APIRequest) -> Dict[str, Any]:
        """Validate rate limiting"""
        return {"passed": True, "issues": []}

    async def validate_authentication(self, request: APIRequest) -> Dict[str, Any]:
        """Validate authentication"""
        return {"passed": True, "issues": []}

    async def validate_authorization(self, request: APIRequest) -> Dict[str, Any]:
        """Validate authorization"""
        return {"passed": True, "issues": []}

    async def validate_input(self, request: APIRequest) -> Dict[str, Any]:
        """Validate input data"""
        return {"passed": True, "issues": []}

    async def validate_business_rules(self, request: APIRequest) -> Dict[str, Any]:
        """Validate business rules"""
        return {"passed": True, "issues": []}


class APIQualityGatesPipeline:
    """
    Multi-stage quality validation pipeline
    Based on ExecutionPlan quality gate patterns
    """

    def __init__(self):
        self.gates: List[RequestQualityGate] = []
        self.logger = logging.getLogger(f"{__name__}.QualityGates")

    def add_quality_gate(self, gate: RequestQualityGate):
        """Add a quality gate to the pipeline"""
        self.gates.append(gate)
        self.logger.info(f"Added quality gate: {gate.__class__.__name__}")

    async def validate_request(self, request: APIRequest) -> Dict[str, Any]:
        """Run all quality gates in parallel for efficiency"""

        if not self.gates:
            return {"passed": True, "issues": []}

        try:
            # Run all validations in parallel
            validations = await asyncio.gather(
                *[self._run_gate_validations(gate, request) for gate in self.gates],
                return_exceptions=True,
            )

            return self._aggregate_validation_results(validations)

        except Exception as e:
            self.logger.error(f"Quality gate validation failed: {e}")
            return {"passed": False, "issues": [f"Validation error: {str(e)}"]}

    async def _run_gate_validations(
        self, gate: RequestQualityGate, request: APIRequest
    ) -> Dict[str, Any]:
        """Run all validations for a single gate"""
        results = {}

        # Run all gate methods
        for method_name in [
            "validate_rate_limit",
            "validate_authentication",
            "validate_authorization",
            "validate_input",
            "validate_business_rules",
        ]:
            if hasattr(gate, method_name):
                method = getattr(gate, method_name)
                try:
                    result = await method(request)
                    results[method_name] = result
                except Exception as e:
                    results[method_name] = {
                        "passed": False,
                        "issues": [f"{method_name} failed: {str(e)}"],
                    }

        return results

    def _aggregate_validation_results(self, validations: List[Any]) -> Dict[str, Any]:
        """Aggregate validation results from all gates"""
        all_issues = []
        all_passed = True

        for validation in validations:
            if isinstance(validation, Exception):
                all_passed = False
                all_issues.append(f"Gate exception: {str(validation)}")
                continue

            if isinstance(validation, dict):
                for method_name, result in validation.items():
                    if isinstance(result, dict):
                        if not result.get("passed", True):
                            all_passed = False
                        all_issues.extend(result.get("issues", []))

        return {"passed": all_passed, "issues": all_issues}


class APIMetricsCollector:
    """
    Real-time metrics collection for API operations
    Based on BasicMonitor patterns from research
    """

    def __init__(self):
        self.metrics = {
            # Request metrics
            "requests_total": 0,
            "requests_active": 0,
            "requests_completed": 0,
            "requests_failed": 0,
            "response_times": [],
            # Quality gate metrics
            "quality_gate_failures": 0,
            "validation_time": 0,
            # System metrics
            "server_start_time": time.time(),
        }
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(f"{__name__}.Metrics")

    async def record_request_start(self, request_id: str):
        """Record request start"""
        async with self.lock:
            self.metrics["requests_total"] += 1
            self.metrics["requests_active"] += 1
            self.logger.debug(f"Request started: {request_id}")

    async def record_request_completion(
        self, request_id: str, duration: float, status: str
    ):
        """Record request completion"""
        async with self.lock:
            self.metrics["requests_active"] -= 1
            if status == "completed":
                self.metrics["requests_completed"] += 1
            else:
                self.metrics["requests_failed"] += 1
            self.metrics["response_times"].append(duration)

            # Keep only last 1000 response times
            if len(self.metrics["response_times"]) > 1000:
                self.metrics["response_times"] = self.metrics["response_times"][-1000:]

            self.logger.debug(f"Request completed: {request_id} in {duration:.2f}ms")

    async def record_quality_gate_failure(self):
        """Record quality gate failure"""
        async with self.lock:
            self.metrics["quality_gate_failures"] += 1

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        async with self.lock:
            response_times = self.metrics["response_times"]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0
            )

            uptime = time.time() - self.metrics["server_start_time"]

            return {
                **self.metrics.copy(),
                "avg_response_time": avg_response_time,
                "success_rate": (
                    self.metrics["requests_completed"]
                    / max(self.metrics["requests_total"], 1)
                )
                * 100,
                "uptime_seconds": uptime,
                "timestamp": datetime.now().isoformat(),
            }


class RequestOrchestrator:
    """
    Orchestrates API requests using proven GenericOrchestrator patterns
    Handles parallel processing, dependency resolution, and resource management
    """

    def __init__(self, max_parallel: int = 50):
        self.max_parallel = max_parallel
        self.semaphore = asyncio.Semaphore(max_parallel)
        # Note: GenericOrchestrator requires output_dir, so we'll use semaphore pattern directly
        # self.orchestrator = GenericOrchestrator(max_parallel=max_parallel)
        self.logger = logging.getLogger(f"{__name__}.Orchestrator")

    async def execute_request(
        self, request: APIRequest, business_logic_handler: Callable
    ) -> APIResponse:
        """Execute single API request with full orchestration"""

        request.start_time = time.time()

        try:
            async with self.semaphore:
                # Execute business logic
                result = await business_logic_handler(request)

                request.end_time = time.time()
                duration_ms = (request.end_time - request.start_time) * 1000

                return APIResponse(
                    request_id=request.request_id,
                    status="completed",
                    data=result,
                    duration_ms=duration_ms,
                )

        except Exception as e:
            request.end_time = time.time()
            duration_ms = (request.end_time - request.start_time) * 1000

            self.logger.error(f"Request execution failed: {e}")
            return APIResponse(
                request_id=request.request_id,
                status="failed",
                error=str(e),
                duration_ms=duration_ms,
            )


class AsyncWebServer:
    """
    Main API gateway built on AsyncWebServer patterns
    Handles HTTP protocol, routing, and initial request processing
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8000, max_parallel: int = 50):
        self.host = host
        self.port = port
        self.max_parallel = max_parallel

        # Initialize components
        self.app = web.Application()
        self.request_orchestrator = RequestOrchestrator(max_parallel=max_parallel)
        self.quality_gates = APIQualityGatesPipeline()
        self.monitor = APIMetricsCollector()
        self.execution_plan_engine = ExecutionPlanAPIEngine()

        # Server state
        self.runner = None
        self.site = None

        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.WebServer")

        # Setup routes
        self._setup_routes()

    def add_quality_gate(self, gate: RequestQualityGate):
        """Add a quality gate to the pipeline"""
        self.quality_gates.add_quality_gate(gate)

    def _setup_routes(self):
        """Setup HTTP routes"""

        # Health and metrics endpoints
        self.app.router.add_get("/health", self._health_handler)
        self.app.router.add_get("/metrics", self._metrics_handler)

        # ExecutionPlan API endpoints (basic structure)
        self.app.router.add_post("/api/v1/execution-plans", self._create_execution_plan)
        self.app.router.add_get("/api/v1/execution-plans", self._list_execution_plans)
        self.app.router.add_get(
            "/api/v1/execution-plans/{plan_id}", self._get_execution_plan
        )
        self.app.router.add_post(
            "/api/v1/execution-plans/{plan_id}/execute", self._execute_plan
        )
        self.app.router.add_delete(
            "/api/v1/execution-plans/{plan_id}", self._delete_plan
        )

        # Generic handler for all other routes
        self.app.router.add_route("*", "/{path:.*}", self._generic_handler)

    async def start(self):
        """Start the web server"""
        self.logger.info(f"Starting server on {self.host}:{self.port}")
        self.logger.info(f"Max parallel requests: {self.max_parallel}")

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()

        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()

        self.logger.info("Server started successfully")

    async def shutdown(self):
        """Shutdown the web server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        self.logger.info("Server shutdown complete")

    async def _health_handler(self, request: Request) -> Response:
        """Health check endpoint"""
        return json_response(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "server": "AsyncWebServer",
                "version": "1.0.0",
            }
        )

    async def _metrics_handler(self, request: Request) -> Response:
        """Metrics endpoint"""
        metrics = await self.monitor.get_metrics_summary()
        return json_response(metrics)

    async def _create_execution_plan(self, request: Request) -> Response:
        """Create new execution plan endpoint"""
        api_request = await self._create_api_request(request, "create_execution_plan")
        api_response = await self._process_request(
            api_request, self._handle_create_execution_plan
        )
        return self._create_http_response(api_response)

    async def _get_execution_plan(self, request: Request) -> Response:
        """Get execution plan endpoint"""
        api_request = await self._create_api_request(request, "get_execution_plan")
        api_response = await self._process_request(
            api_request, self._handle_get_execution_plan
        )
        return self._create_http_response(api_response)

    async def _execute_plan(self, request: Request) -> Response:
        """Execute plan endpoint"""
        api_request = await self._create_api_request(request, "execute_plan")
        api_response = await self._process_request(
            api_request, self._handle_execute_plan
        )
        return self._create_http_response(api_response)

    async def _delete_plan(self, request: Request) -> Response:
        """Delete plan endpoint"""
        api_request = await self._create_api_request(request, "delete_plan")
        api_response = await self._process_request(
            api_request, self._handle_delete_plan
        )
        return self._create_http_response(api_response)

    async def _list_execution_plans(self, request: Request) -> Response:
        """List execution plans endpoint"""
        api_request = await self._create_api_request(request, "list_execution_plans")
        api_response = await self._process_request(
            api_request, self._handle_list_execution_plans
        )
        return self._create_http_response(api_response)

    async def _generic_handler(self, request: Request) -> Response:
        """Generic handler for all other routes"""
        api_request = await self._create_api_request(request, "generic")
        api_response = await self._process_request(
            api_request, self._handle_generic_request
        )
        return self._create_http_response(api_response)

    async def _create_api_request(
        self, http_request: Request, handler_method: str
    ) -> APIRequest:
        """Convert HTTP request to API request"""

        # Extract request data
        try:
            if http_request.method in ["POST", "PUT", "PATCH"]:
                if http_request.content_type == "application/json":
                    payload = await http_request.json()
                else:
                    payload = dict(await http_request.post())
            else:
                payload = None
        except Exception:
            payload = None

        return APIRequest(
            request_type=http_request.method,
            endpoint=str(http_request.url.path),
            method_handler=handler_method,
            payload=payload,
            headers=dict(http_request.headers),
            query_params=dict(http_request.query),
            context={
                "body": payload,
                "path_params": dict(http_request.match_info)
                if hasattr(http_request, "match_info")
                else {},
                "remote_addr": http_request.remote,
                "user_agent": http_request.headers.get("User-Agent", ""),
            },
        )

    async def _process_request(
        self, request: APIRequest, handler: Callable
    ) -> APIResponse:
        """Process API request through quality gates and orchestrator"""

        # Record request start
        await self.monitor.record_request_start(request.request_id)

        try:
            # Quality gates validation
            validation = await self.quality_gates.validate_request(request)
            if not validation.get("passed", True):
                await self.monitor.record_quality_gate_failure()
                api_response = APIResponse(
                    request_id=request.request_id,
                    status="failed",
                    error=f"Validation failed: {validation.get('issues', [])}",
                    duration_ms=0,
                )
            else:
                # Execute request through orchestrator
                api_response = await self.request_orchestrator.execute_request(
                    request, handler
                )

            # Record completion
            await self.monitor.record_request_completion(
                request.request_id, api_response.duration_ms, api_response.status
            )

            return api_response

        except Exception as e:
            self.logger.error(f"Request processing failed: {e}")
            api_response = APIResponse(
                request_id=request.request_id,
                status="failed",
                error=str(e),
                duration_ms=0,
            )

            await self.monitor.record_request_completion(
                request.request_id, 0, "failed"
            )

            return api_response

    def _create_http_response(self, api_response: APIResponse) -> Response:
        """Convert API response to HTTP response"""

        if api_response.status == "completed":
            return json_response(
                api_response.data or {"success": True},
                status=200,
                headers={"X-Request-ID": api_response.request_id},
            )
        else:
            return json_response(
                {"error": api_response.error, "request_id": api_response.request_id},
                status=400,
                headers={"X-Request-ID": api_response.request_id},
            )

    # Business logic handlers (basic implementations)

    async def _handle_create_execution_plan(
        self, request: APIRequest
    ) -> Dict[str, Any]:
        """Handle create execution plan request"""
        if not request.payload:
            raise ValueError("ExecutionPlan data required in request payload")

        response = await self.execution_plan_engine.create_execution_plan(
            request.payload
        )

        if response.success:
            result = {
                "success": True,
                "plan_id": response.plan_id,
                "status": response.status,
            }
            if response.data and response.data.get("warnings"):
                result["warnings"] = response.data["warnings"]
            return result
        else:
            raise ValueError(response.error)

    async def _handle_get_execution_plan(self, request: APIRequest) -> Dict[str, Any]:
        """Handle get execution plan request"""
        plan_id = request.context.get("path_params", {}).get("plan_id")
        if not plan_id:
            raise ValueError("Plan ID required")

        response = await self.execution_plan_engine.get_execution_plan(plan_id)

        if response.success:
            return {"success": True, "plan_id": response.plan_id, "plan": response.data}
        else:
            raise ValueError(response.error)

    async def _handle_execute_plan(self, request: APIRequest) -> Dict[str, Any]:
        """Handle execute plan request"""
        plan_id = request.context.get("path_params", {}).get("plan_id")
        if not plan_id:
            raise ValueError("Plan ID required")

        response = await self.execution_plan_engine.execute_plan(plan_id)

        if response.success:
            return {
                "success": True,
                "plan_id": response.plan_id,
                "status": response.status,
                "results": response.results,
            }
        else:
            raise ValueError(response.error)

    async def _handle_delete_plan(self, request: APIRequest) -> Dict[str, Any]:
        """Handle delete plan request"""
        plan_id = request.context.get("path_params", {}).get("plan_id")
        if not plan_id:
            raise ValueError("Plan ID required")

        response = await self.execution_plan_engine.delete_plan(plan_id)

        if response.success:
            return {
                "success": True,
                "plan_id": response.plan_id,
                "status": response.status,
            }
        else:
            raise ValueError(response.error)

    async def _handle_list_execution_plans(self, request: APIRequest) -> Dict[str, Any]:
        """Handle list execution plans request"""
        status_filter = request.query_params.get("status")

        response = await self.execution_plan_engine.list_plans(status_filter)

        if response.success:
            return {
                "success": True,
                "plans": response.data.get("plans", []),
                "filter_applied": status_filter,
            }
        else:
            raise ValueError(response.error)

    async def _handle_generic_request(self, request: APIRequest) -> Dict[str, Any]:
        """Handle generic requests"""
        return {
            "message": f"Generic handler for {request.request_type} {request.endpoint}",
            "request_id": request.request_id,
            "timestamp": datetime.now().isoformat(),
            "headers_received": len(request.headers),
            "query_params": request.query_params,
            "payload_present": request.payload is not None,
        }
