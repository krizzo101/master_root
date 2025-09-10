# Claude Monitor Test Suite

Comprehensive testing suite for the Claude monitoring system with unit tests, integration tests, performance tests, and mocking capabilities.

## Test Structure

```
tests/
├── test_monitor.py      # Main test suite
├── run_tests.py         # Test runner script
├── requirements.txt     # Testing dependencies
└── README.md           # This file
```

## Test Coverage

### 1. Unit Tests
- **TestLRUCache**: LRU cache implementation with TTL and eviction
- **TestDatabaseCollector**: SQLite database operations and token metrics
- **TestSystemCollector**: System resource monitoring (CPU, memory, disk)
- **TestProcessCollector**: Claude process detection and monitoring
- **TestDockerCollector**: Docker container metrics with mocking
- **TestDockerClaudeMonitor**: Docker Claude monitor lifecycle
- **TestLogCollector**: Log file analysis and error pattern detection
- **TestDataCollector**: Main data collection orchestrator
- **TestMonitoringServiceAPI**: FastAPI endpoints testing

### 2. Integration Tests
- **TestIntegrationDataFlow**: Complete data flow between components
- **TestWebSocketIntegration**: Real-time WebSocket functionality
- Cross-component data consistency validation
- End-to-end metric collection pipeline

### 3. Mock Testing
- **Docker daemon mocking**: Test without Docker dependency
- **Database mocking**: Isolated database testing with temporary files
- **System resource mocking**: Controlled psutil response simulation
- **Log file mocking**: Temporary log files with realistic content

### 4. Performance Tests
- **TestPerformance**: Large dataset query performance
- **Cache performance**: Cache hit/miss performance validation
- **Memory efficiency**: Memory usage monitoring during collection
- **Concurrent collection**: Async data collection performance
- **Database scaling**: 10,000+ record performance benchmarks

## Features Tested

### Core Components
- ✅ LRU caching with TTL expiration
- ✅ SQLite database operations
- ✅ System resource monitoring
- ✅ Process discovery and monitoring
- ✅ Docker container detection
- ✅ Log file analysis
- ✅ FastAPI endpoint responses
- ✅ WebSocket real-time updates

### Data Flow Integration
- ✅ Multi-source data aggregation
- ✅ Cross-component consistency
- ✅ Error handling and fallbacks
- ✅ Caching across collectors
- ✅ Async data collection

### Performance & Scalability
- ✅ Large dataset handling (10K+ records)
- ✅ Query optimization with indices
- ✅ Cache performance improvements
- ✅ Memory usage efficiency
- ✅ Concurrent operation handling

### Mocking & Isolation
- ✅ Docker daemon unavailable scenarios
- ✅ Database connection failures
- ✅ System resource access errors
- ✅ File permission issues
- ✅ Network connectivity problems

## Running Tests

### Prerequisites
```bash
pip install -r tests/requirements.txt
```

### Test Execution Options

```bash
# Run all tests
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py --unit           # Unit tests only
python tests/run_tests.py --integration    # Integration tests only
python tests/run_tests.py --performance    # Performance tests only

# Run performance benchmark
python tests/run_tests.py --benchmark

# Run with coverage report
python tests/run_tests.py --coverage

# Direct pytest execution
python -m pytest tests/test_monitor.py -v

# Run specific test class
python -m pytest tests/test_monitor.py::TestDatabaseCollector -v

# Run performance benchmark directly
python tests/test_monitor.py benchmark
```

### Manual Test Execution
```bash
cd /home/opsvi/master_root/apps/claude-monitor
python tests/test_monitor.py              # Run all tests
python tests/test_monitor.py benchmark    # Performance benchmark
```

## Test Data

### Database Test Data
- Realistic token usage across multiple models
- Session and tool call history
- JSON-formatted node data with token counts
- Time-series data for trend analysis

### Log Test Data
- Application logs with INFO/WARN/ERROR levels
- Error pattern analysis test cases
- Performance issue detection scenarios
- Claude-specific log mentions

### Mock Configurations
- Docker containers with Claude indicators
- System resource usage scenarios
- Process lists with Claude-related processes
- Network and storage I/O statistics

## Expected Test Results

### Performance Benchmarks
- **Database queries**: < 1.0s for 10K records
- **Cache queries**: > 10x speedup on cache hits
- **Memory usage**: < 50MB peak during collection
- **Collection time**: < 5.0s for complete metrics gathering

### Coverage Targets
- **Unit test coverage**: > 90%
- **Integration coverage**: > 80%
- **Error path coverage**: > 75%
- **API endpoint coverage**: 100%

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure Python path includes project directories
   export PYTHONPATH="$PYTHONPATH:$PWD:$PWD/backend:$PWD/monitors:$PWD/collectors"
   ```

2. **Docker Test Failures**
   ```bash
   # Tests use Docker mocking - no Docker daemon required
   # If Docker is available, some tests will use real Docker
   ```

3. **Database Permissions**
   ```bash
   # Tests create temporary databases in /tmp
   # Ensure write permissions to temporary directory
   ```

4. **Missing Dependencies**
   ```bash
   pip install pytest pytest-asyncio fastapi uvicorn docker psutil pydantic
   ```

### Test Environment Setup
```bash
# Set up complete test environment
cd /home/opsvi/master_root/apps/claude-monitor
pip install -r tests/requirements.txt
python tests/run_tests.py --no-deps-check  # Skip dependency check if needed
```

## Test Architecture

### Mock Strategy
- **Dependency injection**: Mock external services (Docker, psutil)
- **Temporary resources**: Use temp files for databases and logs
- **Controlled responses**: Predictable mock data for consistent testing
- **Error simulation**: Test failure scenarios and recovery

### Test Isolation
- **Database isolation**: Each test uses separate temporary database
- **Cache isolation**: Clear caches between test classes
- **Resource cleanup**: Automatic cleanup of temporary files
- **Thread safety**: Tests handle concurrent access scenarios

### Performance Testing
- **Large datasets**: Scale tests with 10K+ records
- **Memory profiling**: Track memory usage during operations
- **Time benchmarks**: Measure and validate query performance
- **Cache efficiency**: Validate caching performance improvements

## Continuous Integration

The test suite is designed to run in CI environments:
- No external dependencies required (Docker, databases)
- Temporary file cleanup
- Deterministic test results
- Comprehensive error reporting
- Performance regression detection

## Contributing

When adding new features to the monitoring system:

1. **Add unit tests** for new components
2. **Update integration tests** for data flow changes
3. **Add performance tests** for scalability concerns
4. **Update mocks** for new external dependencies
5. **Document test cases** in this README

The test suite provides a solid foundation for maintaining and extending the Claude monitoring system with confidence.
