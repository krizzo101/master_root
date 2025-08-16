#!/bin/bash
# Quick WSL2 Memory Cleanup Script
# Performs immediate memory cleanup operations

set -e

echo "🧹 WSL2 Quick Memory Cleanup"
echo "=============================="

# Function to get memory usage percentage
get_memory_percent() {
    free | grep Mem | awk '{print int($3/$2 * 100)}'
}

# Function to format bytes to human readable
format_bytes() {
    numfmt --to=iec-i --suffix=B "$1"
}

# Get initial memory stats
echo -e "\n📊 Initial Memory Status:"
free -h
INITIAL_MEM=$(free -b | grep Mem | awk '{print $3}')
INITIAL_PERCENT=$(get_memory_percent)
echo "Memory usage: ${INITIAL_PERCENT}%"

# 1. Clear PageCache, dentries and inodes
echo -e "\n🔧 Dropping caches..."
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

# 2. Compact memory
echo -e "\n🔧 Compacting memory..."
echo 1 | sudo tee /proc/sys/vm/compact_memory > /dev/null 2>&1 || true

# 3. Kill orphaned Cursor/VS Code processes
echo -e "\n🔧 Checking for orphaned Cursor processes..."
CURSOR_PROCS=$(ps aux | grep -E '\.cursor-server|code-server' | grep -v grep | wc -l)
if [ $CURSOR_PROCS -gt 0 ]; then
    echo "Found $CURSOR_PROCS Cursor-related processes"
    
    # Kill old cursor-server processes (keep only the 3 most recent)
    ps aux | grep '\.cursor-server.*bootstrap-fork' | grep -v grep | \
        sort -k2 -n | head -n -3 | awk '{print $2}' | \
        while read pid; do
            echo "  Killing old Cursor server process: $pid"
            kill -9 $pid 2>/dev/null || true
        done
    
    # Kill extension hosts using more than 1GB
    ps aux | grep 'extensionHost' | grep -v grep | \
        awk '$6 > 1048576 {print $2, $6}' | \
        while read pid mem; do
            mem_mb=$((mem / 1024))
            echo "  Killing high-memory extension host: PID $pid (${mem_mb}MB)"
            kill -9 $pid 2>/dev/null || true
        done
fi

# 4. Clear systemd journal if it's too large
echo -e "\n🔧 Checking systemd journal size..."
if command -v journalctl &> /dev/null; then
    JOURNAL_SIZE=$(journalctl --disk-usage 2>/dev/null | grep -oP '\d+\.?\d*[MG]' || echo "0M")
    echo "Journal size: $JOURNAL_SIZE"
    if [[ $JOURNAL_SIZE == *G* ]] || [[ ${JOURNAL_SIZE%M*} -gt 500 ]]; then
        echo "Cleaning old journal entries..."
        sudo journalctl --vacuum-time=7d 2>/dev/null || true
    fi
fi

# 5. Clear apt cache
echo -e "\n🔧 Checking apt cache..."
APT_CACHE_SIZE=$(du -sh /var/cache/apt/archives 2>/dev/null | cut -f1 || echo "0")
echo "Apt cache size: $APT_CACHE_SIZE"
if [ -d /var/cache/apt/archives ]; then
    sudo apt-get clean 2>/dev/null || true
fi

# 6. Clear pip cache
echo -e "\n🔧 Checking pip cache..."
if [ -d ~/.cache/pip ]; then
    PIP_CACHE_SIZE=$(du -sh ~/.cache/pip 2>/dev/null | cut -f1 || echo "0")
    echo "Pip cache size: $PIP_CACHE_SIZE"
    rm -rf ~/.cache/pip/* 2>/dev/null || true
fi

# 7. Clear npm cache
echo -e "\n🔧 Checking npm cache..."
if command -v npm &> /dev/null; then
    NPM_CACHE_SIZE=$(npm cache verify 2>&1 | grep -oP 'Cache size: \K\d+\.?\d*[MG]B' || echo "0")
    echo "NPM cache size: $NPM_CACHE_SIZE"
    if [[ $NPM_CACHE_SIZE == *G* ]] || [[ ${NPM_CACHE_SIZE%M*} -gt 500 ]]; then
        npm cache clean --force 2>/dev/null || true
    fi
fi

# Wait for memory to be freed
sleep 2

# Get final memory stats
echo -e "\n📊 Final Memory Status:"
free -h
FINAL_MEM=$(free -b | grep Mem | awk '{print $3}')
FINAL_PERCENT=$(get_memory_percent)
echo "Memory usage: ${FINAL_PERCENT}%"

# Calculate freed memory
FREED=$((INITIAL_MEM - FINAL_MEM))
if [ $FREED -gt 0 ]; then
    echo -e "\n✅ Success! Freed $(format_bytes $FREED) of memory"
    echo "Memory usage reduced from ${INITIAL_PERCENT}% to ${FINAL_PERCENT}%"
else
    echo -e "\n⚠️  No significant memory was freed"
    echo "Memory usage: ${FINAL_PERCENT}%"
fi

echo -e "\n💡 Tips:"
echo "  - Run this script periodically when memory usage is high"
echo "  - Consider setting up the automatic monitor: python3 ~/master_root/scripts/wsl_memory_monitor.py monitor"
echo "  - To completely reset WSL2 memory, run: wsl.exe --shutdown (from Windows)"