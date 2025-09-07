# Test Organization Structure

## Overview
This document describes the organization of tests for the Agent Orchestrator project. All tests have been organized into a clear hierarchy for better maintainability and discoverability.

## Directory Structure

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for system components
├── performance/             # Performance and load testing
├── outputs/                 # Test execution outputs and results
├── fixtures/                # Test data and mock files
├── archive/                 # Archived/historical test files
├── test_cli_spawning.sh     # Shell script tests
└── simple_test.sh           # Basic shell test runner
```

## Test Categories

### Unit Tests (`tests/unit/`)
Individual component tests with minimal dependencies:
- `test_18_agents.py` - Agent pool testing
- `test_agent_team_manager.py` - Team manager component tests
- `test_dynamic_pool.py` - Dynamic agent pool tests
- `test_agent_monitored_orchestration.py` - Monitored orchestration units
- `test_quality_gates.py` - Quality gate validation
- `test_log_parser.py` - Log parsing utilities
- `test_simple.py` - Basic functionality tests
- `simple_quality_gate_test.py` - Simple quality gate checks
- `quick_test.py` - Quick validation tests
- `manual_test.py` - Manual testing utilities
- `simple_test.py` - Simple unit tests

### Integration Tests (`tests/integration/`)
Tests that verify component interactions:
- `test_enhanced_execution_plan.py` - Enhanced execution plan integration
- `test_enhanced_minimal.py` - Minimal enhanced features
- `test_enhanced_simple_features.py` - Simple enhanced features
- `test_enhanced_orchestrator.py` - Enhanced orchestrator integration
- `test_enhanced_quality_gates_unit.py` - Enhanced quality gates
- `test_practical_orchestrator.py` - Practical orchestrator scenarios
- `test_practical_simple.py` - Simple practical tests
- `test_orchestrator_report.py` - Orchestrator reporting
- `test_unified_orchestrator.py` - Unified orchestrator testing
- `test_comprehensive.py` - Comprehensive integration suite
- `test_self_improvement_comprehensive.py` - Self-improvement testing
- `test_monitoring_integration.py` - Monitoring system integration
- `test_escalation_integration.py` - Escalation system integration
- `test_execution_plan_integration.py` - Execution plan integration
- `test_agent_orchestration_basic.py` - Basic agent orchestration
- `test_orchestrator_basic.py` - Basic orchestrator tests
- `test_basic_orchestrator.py` - Basic orchestrator scenarios
- `test_framework.py` - Framework integration tests
- `parallel_execution_test.py` - Parallel execution testing
- `basic_functionality_tests.py` - Basic functionality suite
- `end_to_end_tests.py` - End-to-end scenarios

### Performance Tests (`tests/performance/`)
Load testing and performance benchmarks:
- `test_parallel_detailed.py` - Detailed parallel execution tests
- `test_parallel_tokens.py` - Token processing performance
- `test_performance.py` - General performance benchmarks
- `test_parallel_execution.py` - Parallel execution performance
- `test_load_balancing.py` - Load balancing tests
- `test_max_parallel.py` - Maximum parallelization tests

### Test Outputs (`tests/outputs/`)
Contains test execution results and outputs:
- Various `*_output/` directories containing task results
- Test result JSON files
- Execution logs and reports
- Performance metrics

### Test Fixtures (`tests/fixtures/`)
Test data, mock responses, and sample inputs for testing.

### Archive (`tests/archive/`)
Historical tests and old implementations kept for reference:
- Previous test implementations
- Old test outputs
- Legacy test scenarios

## Running Tests

### Quick Test Suite
```bash
# Run all unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run performance tests
python -m pytest tests/performance/
```

### Individual Test Execution
```bash
# Run specific test file
python tests/unit/test_simple.py

# Run with verbose output
python -m pytest tests/integration/test_orchestrator_basic.py -v

# Run shell tests
bash tests/test_cli_spawning.sh
```

### Test Coverage
```bash
# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Performance Testing
```bash
# Run performance benchmarks
python tests/performance/test_performance.py

# Run parallel execution tests
python tests/performance/test_parallel_detailed.py
```

## Test Output Management

Test outputs are automatically saved to `tests/outputs/` with timestamps. Each test run creates:
- Task JSON files with execution details
- Log files for debugging
- Performance metrics
- Error reports

### Cleanup Old Outputs
```bash
# Archive outputs older than 7 days
find tests/outputs -type d -mtime +7 -exec mv {} tests/archive/old_outputs/ \;

# Remove outputs older than 30 days
find tests/archive/old_outputs -type d -mtime +30 -exec rm -rf {} \;
```

## Writing New Tests

### Test Naming Convention
- Unit tests: `test_<component>_<feature>.py`
- Integration tests: `test_<system>_integration.py`
- Performance tests: `test_<aspect>_performance.py`

### Test Structure Template
```python
import unittest
from src.components import Component

class TestComponentFeature(unittest.TestCase):
    def setUp(self):
        # Setup test environment
        pass
    
    def test_specific_behavior(self):
        # Test implementation
        pass
    
    def tearDown(self):
        # Cleanup
        pass

if __name__ == '__main__':
    unittest.main()
```

## CI/CD Integration

Tests are automatically run on:
- Pull requests (unit + integration)
- Main branch commits (full suite)
- Nightly builds (performance tests)

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure PYTHONPATH includes project root
2. **Output directory full**: Run cleanup script or manually archive
3. **Performance test timeout**: Adjust timeout in test configuration

### Debug Mode
```bash
# Run with debug logging
LOGLEVEL=DEBUG python -m pytest tests/unit/ -v

# Run single test with pdb
python -m pytest tests/unit/test_simple.py::TestClass::test_method --pdb
```

## Contributing

When adding new tests:
1. Place in appropriate category directory
2. Follow naming conventions
3. Include docstrings describing test purpose
4. Clean up test outputs in tearDown
5. Update this README if adding new test categories

## Contact

For test-related questions or issues, please refer to the main project documentation or create an issue in the project repository.