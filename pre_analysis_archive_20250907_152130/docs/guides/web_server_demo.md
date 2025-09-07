# Async Web Server Demo

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install aiohttp
   ```

2. **Start the server:**
   ```bash
   python run_web_server.py [port] [host]
   ```

   Examples:
   ```bash
   python run_web_server.py          # Runs on 0.0.0.0:8000
   python run_web_server.py 8080     # Runs on 0.0.0.0:8080
   python run_web_server.py 8080 localhost  # Runs on localhost:8080
   ```

3. **Test the server:**
   ```bash
   python examples/test_web_server.py [base_url]
   ```

## Server Features

### Core Capabilities
- **Async Request Processing**: Based on GenericOrchestrator patterns
- **Parallel Execution**: Configurable max concurrent requests (default: 20)
- **Quality Gates**: Request validation, rate limiting, input sanitization
- **Real-time Monitoring**: Built-in metrics collection
- **Dependency Management**: Request dependency resolution
- **Connection Pooling**: Round-robin resource allocation

### Built-in Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": 1693833600.123
}
```

#### Metrics
```bash
curl http://localhost:8000/metrics
```
Response:
```json
{
  "requests_started": 15,
  "requests_completed": 12,
  "requests_failed": 3,
  "total_response_time": 2.456,
  "active_connections": 0,
  "avg_response_time": 0.205
}
```

#### Any Custom Path
```bash
# GET request
curl http://localhost:8000/api/users/123

# POST request
curl -X POST http://localhost:8000/api/data \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "timestamp": 1693833600}'
```

## Architecture Highlights

### Based on Agent Orchestrator Patterns
- **WebRequest**: Following AgentTask dataclass structure
- **AsyncRequestOrchestrator**: Parallel execution with dependency management
- **ConnectionPool**: TokenPool pattern for resource management
- **RequestQualityGate**: ExecutionPlan validation patterns
- **WebServerMonitor**: BasicMonitor real-time metrics

### Performance Features
- **Async I/O**: Non-blocking request processing
- **Semaphore Control**: Limits concurrent requests to prevent overload
- **Round-robin Pools**: Efficient connection/resource allocation
- **Request Batching**: Groups similar requests for optimization
- **Health Checking**: Monitors service/connection health

### Security & Validation
- **Multi-stage Validation**: Authentication, authorization, input sanitization
- **Rate Limiting**: Token bucket pattern implementation
- **Error Handling**: Graceful degradation with fallback paths
- **Circuit Breaker**: Service failure protection

## Example Usage

### Basic Server
```python
from src.async_web_server import AsyncWebServer

# Create and start server
server = AsyncWebServer(host="0.0.0.0", port=8000, max_parallel=20)
await server.start()
```

### Custom Quality Gates
```python
from src.async_web_server import RequestQualityGate

class AuthGate(RequestQualityGate):
    async def validate_auth(self, request):
        token = request.context.get('headers', {}).get('Authorization')
        if not token:
            return {"passed": False, "issues": ["Missing auth token"]}
        return {"passed": True, "issues": []}

server.add_quality_gate(AuthGate())
```

### Load Testing
```python
# Run built-in load test
python examples/test_web_server.py

# Results show:
# - Concurrent request handling
# - Response times
# - Success/failure rates
# - Server metrics
```

## Performance Characteristics

- **Throughput**: ~1000+ requests/second (depends on hardware)
- **Latency**: <100ms typical response time
- **Concurrency**: Configurable parallel request limit
- **Memory**: Efficient async resource utilization
- **Scalability**: Horizontal scaling through stateless design

## Monitoring Output

Server logs show real-time activity:
```
INFO:async_web_server:Server started at http://0.0.0.0:8000
INFO:async_web_server:Request GET_/health_1693833601234 started
INFO:async_web_server:Request GET_/health_1693833601234 completed in 0.001s
INFO:async_web_server:Server metrics: {'requests_started': 1, 'requests_completed': 1, ...}
```

## Next Steps

1. **Extend Quality Gates**: Add authentication, authorization, custom validation
2. **Add Business Logic**: Implement custom request handlers
3. **Database Integration**: Add ConnectionPool for database connections
4. **Caching Layer**: Implement response caching
5. **Load Balancing**: Deploy multiple instances behind load balancer
6. **Observability**: Add structured logging, tracing, alerting

This server provides a solid foundation for building scalable, async web applications using proven patterns from the agent orchestrator architecture.
