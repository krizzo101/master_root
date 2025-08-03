#!/bin/bash
# reset-watcher.sh
# Script to restart the GenFileMap file watcher and clean up any orphaned processes

echo "Stopping any running file watchers..."
pkill -f shell_file_watcher.py

echo "Removing any old log files..."
rm -f watcher.log

echo "Waiting for processes to stop..."
sleep 2

echo "Starting file watcher..."
./shell_file_watcher.py . --recursive > watcher.log 2>&1 &
WATCHER_PID=$!

echo "File watcher restarted with PID: $WATCHER_PID"
echo "Log file: $(pwd)/watcher.log"
echo ""
echo "To stop the watcher, run: kill $WATCHER_PID"
echo "To monitor the log file, run: tail -f watcher.log" 