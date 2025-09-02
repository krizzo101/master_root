# Answer Review Logging System

## Overview
Comprehensive logging system for the `answer_review.py` hook that provides audit trails, performance metrics, and operational insights.

## Features

### 1. Three-Tier Logging Architecture
- **Audit Logs**: Immutable record of all review decisions
- **Operational Logs**: Application workflow, errors, and debugging
- **Performance Metrics**: Response times and resource usage

### 2. Privacy Protection
- Assistant responses and user prompts are hashed
- Only metadata and verdicts are stored in clear text
- Response previews limited to 100 characters

### 3. Log Rotation
- Automatic daily rotation
- Size-based rotation (10MB max per file)
- Keeps 5 backup files

## Directory Structure
```
.claude/hooks/logs/
├── audit/                        # Immutable audit trail
│   └── review_audit_YYYY-MM-DD.jsonl
├── operational/                  # Application logs
│   └── answer_review_YYYY-MM-DD.log
└── metrics/                      # Performance data
    └── performance_YYYY-MM-DD.jsonl
```

## Installation

### Quick Setup
```bash
# Run the migration script
./migrate_to_logging.sh
```

### Manual Setup
```bash
# 1. Replace answer_review.py with logging version
cp answer_review_with_logging.py answer_review.py

# 2. Create log directories
mkdir -p .claude/hooks/logs/{audit,operational,metrics}

# 3. Make scripts executable
chmod +x answer_review.py analyze_review_logs.py
```

## Configuration

### Environment Variables
```bash
# Logging level (DEBUG, INFO, WARNING, ERROR)
export REVIEW_LOG_LEVEL="INFO"

# Enable API call auditing
export ENABLE_API_AUDIT="true"

# Enable debug console output
export DEBUG="1"

# OpenAI timeout (seconds)
export OPENAI_TIMEOUT_SEC="25.0"
```

## Usage

### View Real-Time Logs
```bash
# Structured JSON logs
tail -f .claude/hooks/logs/operational/answer_review_*.log | jq .

# Human-readable format
tail -f .claude/hooks/logs/operational/answer_review_*.log | jq -r '"\(.timestamp) [\(.level)] \(.message)"'
```

### Analyze Historical Data
```bash
# Generate text report for last 7 days
python analyze_review_logs.py

# Generate JSON data for last 30 days
python analyze_review_logs.py --days 30 --format json

# Save report to file
python analyze_review_logs.py --output report.txt
```

### Query Audit Trail
```bash
# View all review decisions
cat .claude/hooks/logs/audit/review_audit_*.jsonl | jq .

# Filter failed reviews
cat .claude/hooks/logs/audit/review_audit_*.jsonl | jq 'select(.verdict.passed == false)'

# Count reviews by model
cat .claude/hooks/logs/audit/review_audit_*.jsonl | jq -r .model | sort | uniq -c
```

### Performance Analysis
```bash
# View performance metrics
cat .claude/hooks/logs/metrics/performance_*.jsonl | jq .

# Calculate average response time
cat .claude/hooks/logs/metrics/performance_*.jsonl | \
  jq -r '.duration_ms' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "ms"}'
```

## Log Entry Examples

### Audit Log Entry
```json
{
  "timestamp": "2024-01-20T10:30:45.123Z",
  "session_id": "sess-001",
  "review_id": "a1b2c3d4",
  "model": "gpt-5-nano",
  "attempt_num": 1,
  "verdict": {
    "passed": false,
    "guidance": "Add error handling for edge cases"
  },
  "response_hash": "sha256_hash_here",
  "response_length": 1234,
  "response_preview": "This function calculates...",
  "prompts_hashes": ["hash1", "hash2"],
  "prompts_count": 2,
  "duration_ms": 1456.78
}
```

### Operational Log Entry
```json
{
  "timestamp": "2024-01-20T10:30:45.123Z",
  "level": "INFO",
  "logger": "answer_review",
  "message": "Review completed",
  "module": "answer_review_with_logging",
  "function": "call_review",
  "line": 185,
  "session_id": "sess-001",
  "model": "gpt-5-nano",
  "passed": false,
  "duration_ms": 1456.78
}
```

### Performance Metric Entry
```json
{
  "timestamp": "2024-01-20T10:30:45.123Z",
  "session_id": "sess-001",
  "operation": "model_review",
  "duration_ms": 1456.78,
  "metadata": {
    "model": "gpt-5-nano",
    "attempt": 1,
    "api_duration_s": 1.35
  }
}
```

## Analysis Report Sample
```
=== Answer Review Log Analysis Report ===
Period: Last 7 days
Generated: 2024-01-20T10:30:45

## Review Statistics
- Total reviews: 150
- Passed: 120 (80.0%)
- Failed: 30 (20.0%)
- Research blocks: 5
- Unique sessions: 45
- Avg attempts per session: 1.3
- Max attempts seen: 3

## Model Performance
- gpt-5-nano: 140 reviews, 78.6% pass rate
- gpt-5-mini: 10 reviews, 100.0% pass rate

## Performance Metrics

### model_review
  - Count: 150
  - Mean: 1250.5ms
  - Median: 1100.0ms
  - Range: 800.0ms - 2500.0ms
  - P95: 2000.0ms

## Failure Analysis
- Total failures: 30

Common guidance keywords:
  - error: 12 occurrences
  - handling: 10 occurrences
  - validation: 8 occurrences
```

## Troubleshooting

### No Logs Appearing
1. Check environment variables are set
2. Verify script has write permissions: `ls -la .claude/hooks/logs/`
3. Enable debug mode: `export DEBUG=1`

### Log Files Growing Too Large
- Adjust rotation settings in `review_logging.py`
- Clean old logs: `find .claude/hooks/logs -mtime +30 -delete`

### Performance Issues
- Reduce log level: `export REVIEW_LOG_LEVEL="WARNING"`
- Disable API auditing: `export ENABLE_API_AUDIT="false"`

## Rollback
To revert to the original non-logging version:
```bash
cp .claude/hooks/backups/[timestamp]/answer_review.py.bak .claude/hooks/answer_review.py
```

## Security Considerations
- Logs contain hashed content, not raw text
- Sensitive data is automatically redacted
- Log files inherit directory permissions
- Consider encrypting logs directory for production use

## Maintenance
- Logs auto-rotate daily
- Old logs should be archived or deleted periodically
- Monitor disk space usage
- Review audit logs regularly for anomalies
