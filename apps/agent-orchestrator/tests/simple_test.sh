#!/bin/bash

# Simple test to verify monitoring works with local processes

echo "Creating test agent files..."

# Create some test files that look like agent output
for i in {1..3}; do
    echo "$(date +%s%N) START PID:$$ PPID:$PPID Agent:test-$i" > /tmp/test-agent-$i.log

    # Create status file for dashboard
    cat > ./agent_monitor/status/test-$i.json <<EOF
{
  "agent_id": "test-$i",
  "parent": "root",
  "level": 1,
  "status": "RUNNING",
  "pid": "$$",
  "task": "Test agent $i",
  "start_time": $(date +%s),
  "last_update": $(date +%s)
}
EOF
done

echo "Created 3 test agent files"
echo "Now run: ./agent_monitor/scripts/live_monitor.sh"
echo "You should see the test agents in the dashboard"
