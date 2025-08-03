#!/bin/bash
# setup-file-watcher.sh
# Example script for setting up and running the GenFileMap file watcher

# Create log directory if it doesn't exist
mkdir -p logs

# Copy the necessary files
echo "Copying file watcher scripts..."
cp "$(python -c 'import os, genfilemap; print(os.path.dirname(genfilemap.__file__))')/shell_file_watcher.py" .
cp "$(python -c 'import os, genfilemap; print(os.path.dirname(genfilemap.__file__))')/run.py" .

# Make them executable
chmod +x shell_file_watcher.py run.py

# Start the file watcher in the background
echo "Starting file watcher..."
./shell_file_watcher.py . --recursive > logs/watcher.log 2>&1 &
WATCHER_PID=$!

echo "File watcher started with PID: $WATCHER_PID"
echo "Log file: $(pwd)/logs/watcher.log"
echo ""
echo "To stop the watcher, run: kill $WATCHER_PID"
echo "To monitor the log file, run: tail -f logs/watcher.log"
echo ""
echo "The watcher will automatically update file maps when files change." 