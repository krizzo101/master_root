#!/bin/bash
# Run Claude with debug to capture full conversation
claude -p -d "Create a file test.txt with 'Hello' in it" 2>&1 | grep -E "(Tool:|Content:|Result:|assistant:|user:|DEBUG.*tool)"
