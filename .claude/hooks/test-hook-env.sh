#!/bin/bash
# Test script to verify Claude Code hook environment

echo "=== Claude Code Hook Environment Test ===" > /tmp/hook-env-test.log
echo "Date: $(date)" >> /tmp/hook-env-test.log
echo "" >> /tmp/hook-env-test.log

echo "Environment Variables:" >> /tmp/hook-env-test.log
echo "CLAUDE_PROJECT_DIR: $CLAUDE_PROJECT_DIR" >> /tmp/hook-env-test.log
echo "CLAUDE_SESSION: ${CLAUDE_SESSION:0:100}..." >> /tmp/hook-env-test.log
echo "TRANSCRIPT_PATH: $TRANSCRIPT_PATH" >> /tmp/hook-env-test.log
echo "PWD: $PWD" >> /tmp/hook-env-test.log
echo "HOME: $HOME" >> /tmp/hook-env-test.log
echo "" >> /tmp/hook-env-test.log

echo "Hook Context:" >> /tmp/hook-env-test.log
echo "Script: $0" >> /tmp/hook-env-test.log
echo "Args: $@" >> /tmp/hook-env-test.log
echo "" >> /tmp/hook-env-test.log

echo "Available Commands:" >> /tmp/hook-env-test.log
which claude >> /tmp/hook-env-test.log 2>&1
echo "" >> /tmp/hook-env-test.log

echo "Test completed successfully" >> /tmp/hook-env-test.log

# Return success to Claude Code
echo '{"decision": "allow", "message": "Hook environment test completed - check /tmp/hook-env-test.log"}'
