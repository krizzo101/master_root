#!/bin/bash
# TDD with Monitoring - Test-Driven Development with Full Visibility

set -e

FEATURE_NAME="$1"
if [ -z "$FEATURE_NAME" ]; then
    echo "Usage: $0 <feature_name>"
    exit 1
fi

echo "🧪 Starting TDD with Monitoring for: $FEATURE_NAME"

# 1. Use TDD command to set up test structure
echo -e "\n📝 Setting up TDD structure..."
cat > /tmp/tdd_request.md << EOF
/tdd

Feature: $FEATURE_NAME

Requirements:
- Write failing tests first
- Implement minimal code to pass
- Refactor with confidence
- Monitor all executions
EOF

# 2. Create test file with monitoring
TEST_FILE="tests/test_${FEATURE_NAME}.py"
mkdir -p tests

cat > $TEST_FILE << 'EOF'
import pytest
import sys
from pathlib import Path

# Add monitoring
sys.path.insert(0, str(Path(__file__).parent.parent / "libs" / "opsvi-mcp"))
from opsvi_mcp.servers.claude_code_v3.agent_monitor import SessionCaptureAgent

class TestWithMonitoring:
    """Base test class with monitoring capabilities"""
    
    @classmethod
    def setup_class(cls):
        cls.monitor = SessionCaptureAgent(Path(".test-sessions"))
    
    def run_monitored_test(self, test_func):
        """Run test with monitoring"""
        import subprocess
        import asyncio
        
        # Create test process
        cmd = ["python", "-m", "pytest", "-xvs", test_func.__name__]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Capture with monitoring
        session = asyncio.run(
            self.monitor.capture_session_stream(
                process=process,
                job_id=f"test_{test_func.__name__}",
                phase="testing",
                timeout=60
            )
        )
        
        return session

# Actual tests for the feature
class Test${FEATURE_NAME^}(TestWithMonitoring):
    
    def test_feature_exists(self):
        """Test that feature module exists"""
        # This should fail initially (RED)
        import src.${FEATURE_NAME}
        assert hasattr(src.${FEATURE_NAME}, 'main')
    
    def test_feature_basic_functionality(self):
        """Test basic feature functionality"""
        # This should fail initially (RED)
        from src.${FEATURE_NAME} import process
        result = process("test_input")
        assert result == "expected_output"
    
    def test_feature_edge_cases(self):
        """Test edge cases"""
        # This should fail initially (RED)
        from src.${FEATURE_NAME} import process
        assert process(None) == "default"
        assert process("") == "empty"
        
    def test_feature_with_monitoring(self):
        """Test with full monitoring enabled"""
        session = self.run_monitored_test(self.test_feature_basic_functionality)
        
        # Assert monitoring worked
        assert session['status'] == 'completed'
        assert len(session['errors']) == 0
        print(f"Test session saved: {session['job_id']}")
EOF

# 3. Run tests (they should fail - RED phase)
echo -e "\n🔴 RED Phase - Running failing tests..."
python -m pytest $TEST_FILE -xvs || true

# 4. Monitor the implementation phase
echo -e "\n🟢 GREEN Phase - Implementing with monitoring..."

# Create implementation with monitoring
IMPL_FILE="src/${FEATURE_NAME}.py"
mkdir -p src

# Use monitored V2 server to implement
python << EOF
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-mcp')
from opsvi_mcp.servers.claude_code_v2.server_monitored import MonitoredClaudeCodeV2Server

async def implement_feature():
    server = MonitoredClaudeCodeV2Server()
    
    # Spawn monitored agent to implement
    result = await server.spawn_monitored_agent(
        task=f"""
        Implement {FEATURE_NAME} feature to make these tests pass:
        {open('$TEST_FILE').read()}
        
        Create src/${FEATURE_NAME}.py with:
        - main() function
        - process() function that handles the test cases
        - Proper error handling
        """,
        output_dir=".",
        timeout=300,
        enable_monitoring=True
    )
    
    print(f"Implementation job: {result['job_id']}")
    print(f"Monitor at: {result['monitoring_location']}")
    
    # Wait and check status
    await asyncio.sleep(5)
    status = await server.get_agent_status(result['job_id'])
    print(f"Status: {status}")
    
    return result

asyncio.run(implement_feature())
EOF

# 5. Run tests again (should pass - GREEN phase)
echo -e "\n✅ Verifying implementation..."
python -m pytest $TEST_FILE -xvs

# 6. Refactor phase with monitoring
echo -e "\n🔵 REFACTOR Phase - Improving code..."

# 7. Run coverage analysis
echo -e "\n📊 Coverage Analysis..."
python -m pytest $TEST_FILE --cov=src.${FEATURE_NAME} --cov-report=term-missing

# 8. Generate test report
echo -e "\n📝 Generating test report..."
cat > test_report_${FEATURE_NAME}.md << EOF
# TDD Report: $FEATURE_NAME

## Test Results
- Tests Written: $(grep -c "def test_" $TEST_FILE)
- Tests Passing: $(python -m pytest $TEST_FILE -q | grep -c "passed")
- Coverage: $(python -m pytest $TEST_FILE --cov=src.${FEATURE_NAME} -q | grep "TOTAL" | awk '{print $4}')

## Monitoring Sessions
- Test Sessions: .test-sessions/
- Implementation Sessions: .sdlc-sessions/

## Files Created
- Test File: $TEST_FILE
- Implementation: $IMPL_FILE

## Next Steps
1. Review monitoring data for performance issues
2. Add integration tests
3. Document API
EOF

cat test_report_${FEATURE_NAME}.md

echo -e "\n✅ TDD with Monitoring Complete!"
echo "   Test sessions saved in: .test-sessions/"
echo "   Use /monitor-debug to analyze any failures"