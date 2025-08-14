# Developer Requirements: Multi-Token Parallel Execution Testing System

## Objective
Create a comprehensive testing and timing analysis system to verify and measure the performance of parallel Claude API calls using multiple authentication tokens.

## Background
We have an MCP (Model Context Protocol) server that can spawn Claude CLI instances. We have 3 separate Claude API tokens (CLAUDE_CODE_TOKEN, CLAUDE_CODE_TOKEN1, CLAUDE_CODE_TOKEN2) that should allow us to run 3 Claude instances in parallel. We need to prove that:
1. Real API calls are being made (not simulated)
2. True parallel execution is occurring (not sequential)
3. Accurate timing data is being collected

## Current Problem
Previous tests have produced confusing or potentially inaccurate results:
- Timing data that seems unrealistic (milliseconds instead of seconds)
- Unclear reporting of sequential vs parallel execution
- Ambiguous presentation of results
- No clear proof that actual API calls were made vs simulated responses

## Requirements

### 1. Verifiable API Call Proof
The system MUST capture from each Claude CLI execution:
- **session_id**: Unique identifier from the API response
- **duration_api_ms**: Actual API processing time
- **total_cost_usd**: Real cost charged for the API call  
- **token counts**: Input/output tokens used
- **timestamp**: When the API call was made
- **response content**: The actual result returned

This data must be captured directly from the Claude CLI's JSON output (using `--output-format json` flag), not generated or estimated.

### 2. Accurate Timing Collection
All timing must be collected by Python code using:
- `time.perf_counter()` for high-precision elapsed time
- `time.time()` for absolute timestamps
- Clear labeling of what each timestamp represents

Required timing points:
- Test start time
- Each subprocess spawn time
- Each subprocess completion time
- Each API response received time
- File creation verification time (if applicable)

### 3. Clear Reporting Format
The output report must clearly show:

#### For Sequential Test:
```
Sequential Execution Test:
Task 1: Started at 0.00s, Completed at 14.07s, Duration: 14.07s, Session: xxx-xxx
Task 2: Started at 14.07s, Completed at 29.76s, Duration: 15.69s, Session: yyy-yyy
Task 3: Started at 29.76s, Completed at 44.09s, Duration: 14.33s, Session: zzz-zzz
Total Sequential Time: 44.09 seconds
```

#### For Parallel Test:
```
Parallel Execution Test:
Task A: Started at 0.00s, Completed at 16.84s, Duration: 16.84s, Session: aaa-aaa
Task B: Started at 0.00s, Completed at 16.83s, Duration: 16.83s, Session: bbb-bbb
Task C: Started at 0.00s, Completed at 16.84s, Duration: 16.84s, Session: ccc-ccc
Total Parallel Time: 16.84 seconds (max of all tasks)
```

#### Performance Analysis:
```
Performance Comparison:
Sequential Total: 44.09 seconds (sum of all tasks)
Parallel Maximum: 16.84 seconds (longest task)
Speedup Factor: 2.62x (44.09 / 16.84)
Parallelism Efficiency: 87% (2.62 / 3.0 theoretical maximum)
```

### 4. Test Structure
The test must:
1. Clean any previous test artifacts
2. Run a SEQUENTIAL baseline test:
   - Execute 3 Claude tasks one after another
   - Use different tokens for each to avoid rate limiting
   - Capture all API response data
3. Run a PARALLEL test:
   - Spawn 3 Claude processes simultaneously using subprocess.Popen
   - Each uses a different token
   - Wait for all to complete
   - Capture all API response data
4. Generate comprehensive report with all timing and API data

### 5. Recursive Spawning Test (Advanced)
After basic parallel testing works, test recursive spawning:
- Tier 1: 3 Claude instances run in parallel
- Each Tier 1 instance spawns 3 more instances (Tier 2)
- Total: 3 + 9 = 12 Claude instances
- Track the complete execution tree with timing

### 6. Error Handling
The system must handle:
- API failures (capture error responses)
- Timeout scenarios
- Missing environment variables (tokens)
- JSON parsing errors
- File system errors

## Example Test Implementation Structure

```python
class ParallelExecutionTester:
    def __init__(self):
        self.timing_data = []
        self.api_responses = []
        
    def run_sequential_test(self, tasks):
        """Run tasks one after another, return timing data"""
        
    def run_parallel_test(self, tasks):
        """Run tasks simultaneously, return timing data"""
        
    def verify_api_call(self, response):
        """Verify response contains session_id, cost, tokens"""
        
    def generate_report(self):
        """Generate clear, unambiguous report"""
```

## Success Criteria
1. All API calls have unique session IDs (proving real API usage)
2. Parallel tasks complete in approximately the same time as a single task
3. Sequential tasks take approximately N times longer than parallel (where N = number of tasks)
4. All timing data is consistent and verifiable
5. Report is clear and unambiguous

## Current Issues to Solve
1. Previous test showed "parallel" tasks taking 60 seconds from program start but only 16 seconds of actual execution - this needs clearer presentation
2. Need to clearly distinguish between "elapsed time from test start" vs "task duration"
3. Must prove API calls are real, not mocked or simulated
4. Token rotation and assignment must be verified

## Deliverables
1. Python test script that runs both sequential and parallel tests
2. JSON report with all raw timing and API data
3. Human-readable summary showing clear performance metrics
4. Verification that multi-token parallel execution actually works