#!/bin/bash
# Setup script for WSL2 Memory Management System

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
USER_NAME=$(whoami)

echo "🚀 WSL2 Memory Management Setup"
echo "================================"

# 1. Install required Python packages
echo -e "\n📦 Installing Python dependencies..."
pip install --user psutil 2>/dev/null || pip3 install --user psutil

# 2. Create required directories
echo -e "\n📁 Creating directories..."
mkdir -p ~/.config
mkdir -p ~/.local/log
mkdir -p ~/.local/state

# 3. Set up sudo permissions for memory management commands
echo -e "\n🔐 Setting up sudo permissions..."
SUDOERS_FILE="/tmp/wsl-memory-sudoers"
cat > $SUDOERS_FILE << EOF
# Allow memory management commands without password
$USER_NAME ALL=(ALL) NOPASSWD: /bin/sh -c echo 3 > /proc/sys/vm/drop_caches
$USER_NAME ALL=(ALL) NOPASSWD: /bin/sh -c echo 1 > /proc/sys/vm/compact_memory
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/drop_caches
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/compact_memory
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/journalctl --vacuum-time=*
$USER_NAME ALL=(ALL) NOPASSWD: /usr/bin/apt-get clean
EOF

echo "The following lines need to be added to sudoers file:"
cat $SUDOERS_FILE
echo ""
echo "Please run: sudo visudo"
echo "And add the above lines at the end of the file"
echo "Press Enter when done..."
read

# 4. Create initial configuration
echo -e "\n⚙️  Creating configuration..."
python3 $SCRIPT_DIR/wsl_memory_monitor.py config > /dev/null

# 5. Test the monitor
echo -e "\n🧪 Testing monitor..."
python3 $SCRIPT_DIR/wsl_memory_monitor.py status

# 6. Set up systemd service (optional)
echo -e "\n🔧 Systemd service setup (optional)..."
echo "Do you want to install the systemd service for automatic monitoring? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    # Update service file with actual username
    sed "s/%USER%/$USER_NAME/g" $SCRIPT_DIR/wsl-memory-monitor.service > /tmp/wsl-memory-monitor.service
    
    echo "Please run the following commands to install the service:"
    echo "  sudo cp /tmp/wsl-memory-monitor.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable wsl-memory-monitor.service"
    echo "  sudo systemctl start wsl-memory-monitor.service"
    echo ""
    echo "Press Enter when done (or skip)..."
    read
fi

# 7. Set up cron job for periodic cleanup
echo -e "\n⏰ Setting up periodic cleanup..."
echo "Do you want to set up automatic cleanup every hour? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    # Add cron job
    (crontab -l 2>/dev/null || true; echo "0 * * * * $SCRIPT_DIR/wsl_quick_cleanup.sh > /dev/null 2>&1") | crontab -
    echo "Cron job added for hourly cleanup"
fi

# 8. Create aliases for easy access
echo -e "\n🎯 Creating command aliases..."
ALIAS_FILE=~/.bash_aliases
touch $ALIAS_FILE
grep -q "wsl-mem-status" $ALIAS_FILE || echo "alias wsl-mem-status='python3 $SCRIPT_DIR/wsl_memory_monitor.py status'" >> $ALIAS_FILE
grep -q "wsl-mem-cleanup" $ALIAS_FILE || echo "alias wsl-mem-cleanup='$SCRIPT_DIR/wsl_quick_cleanup.sh'" >> $ALIAS_FILE
grep -q "wsl-mem-monitor" $ALIAS_FILE || echo "alias wsl-mem-monitor='python3 $SCRIPT_DIR/wsl_memory_monitor.py monitor'" >> $ALIAS_FILE

echo -e "\n✅ Setup complete!"
echo ""
echo "Available commands:"
echo "  wsl-mem-status  - Show current memory status"
echo "  wsl-mem-cleanup - Perform quick memory cleanup"
echo "  wsl-mem-monitor - Start memory monitor"
echo ""
echo "Configuration file: ~/.config/wsl_memory_monitor.json"
echo ""
echo "⚠️  Important: Source your aliases to use the new commands:"
echo "  source ~/.bash_aliases"
echo ""
echo "📝 Recommendations:"
echo "  1. Edit ~/.config/wsl_memory_monitor.json to customize thresholds"
echo "  2. Set up email notifications if desired"
echo "  3. Monitor logs at ~/.local/log/wsl_memory_monitor.log"
echo "  4. Consider creating a .wslconfig file in your Windows user directory"
echo "     to limit WSL2 memory usage (e.g., memory=8GB)"