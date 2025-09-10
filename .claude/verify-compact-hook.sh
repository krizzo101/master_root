#!/bin/bash
# Verification script for PreCompact hook functionality

echo "🔍 Claude Code PreCompact Hook Verification"
echo "==========================================="
echo ""

# Check hook configuration
echo "1. Checking hook configuration in settings.json..."
if grep -q "PreCompact" /home/opsvi/master_root/.claude/settings.json; then
    echo "   ✅ PreCompact hook is configured"
    grep -A 5 "PreCompact" /home/opsvi/master_root/.claude/settings.json | head -7
else
    echo "   ❌ PreCompact hook NOT found in settings.json"
fi
echo ""

# Check hook script
echo "2. Checking hook script..."
HOOK_SCRIPT="/home/opsvi/master_root/.claude/hooks/pre-compact-export-v2.sh"
if [ -f "$HOOK_SCRIPT" ]; then
    echo "   ✅ Hook script exists: $HOOK_SCRIPT"
    if [ -x "$HOOK_SCRIPT" ]; then
        echo "   ✅ Hook script is executable"
    else
        echo "   ❌ Hook script is NOT executable"
    fi
else
    echo "   ❌ Hook script NOT found"
fi
echo ""

# Check export directory
echo "3. Checking export directory..."
EXPORT_DIR="/home/opsvi/master_root/.claude/session-exports"
if [ -d "$EXPORT_DIR" ]; then
    echo "   ✅ Export directory exists: $EXPORT_DIR"
    EXPORT_COUNT=$(ls -1 "$EXPORT_DIR"/*.txt 2>/dev/null | wc -l)
    echo "   📁 Found $EXPORT_COUNT export files"
    if [ -L "$EXPORT_DIR/latest_pre_compact.txt" ]; then
        echo "   ✅ Latest symlink exists"
        LATEST_TARGET=$(readlink "$EXPORT_DIR/latest_pre_compact.txt")
        echo "   → Points to: $(basename "$LATEST_TARGET")"
    fi
else
    echo "   ❌ Export directory does NOT exist"
fi
echo ""

# Check log file
echo "4. Checking export log..."
if [ -f "$EXPORT_DIR/export.log" ]; then
    echo "   ✅ Export log exists"
    echo "   Last 3 entries:"
    tail -3 "$EXPORT_DIR/export.log" | sed 's/^/      /'
else
    echo "   ⚠️  No export log found"
fi
echo ""

# Manual test
echo "5. Testing manual hook execution..."
CLAUDE_PROJECT_DIR=/home/opsvi/master_root
export CLAUDE_PROJECT_DIR
RESULT=$($HOOK_SCRIPT 2>&1)
if echo "$RESULT" | grep -q '"decision": "allow"'; then
    echo "   ✅ Manual execution successful"
    echo "$RESULT" | grep '"message"' | sed 's/^/      /'
else
    echo "   ❌ Manual execution failed"
    echo "      $RESULT"
fi
echo ""

# Recommendations
echo "📋 RECOMMENDATIONS:"
echo "==================="
echo ""
if [ -d "$EXPORT_DIR" ] && [ -f "$EXPORT_DIR/export.log" ]; then
    echo "✅ Hook infrastructure is properly set up and working"
    echo ""
    echo "Next steps to verify in Claude Code:"
    echo "1. Exit and restart Claude Code to ensure settings are reloaded"
    echo "2. Run a test /compact command"
    echo "3. Check if a new export file appears in:"
    echo "   $EXPORT_DIR"
    echo ""
    echo "If hook doesn't trigger automatically:"
    echo "- The hook may need to be in a global Claude Code settings file"
    echo "- Try copying settings.json to ~/.claude/settings.json"
else
    echo "⚠️  Some setup steps may be incomplete"
    echo ""
    echo "To fix:"
    echo "1. Ensure export directory exists: mkdir -p $EXPORT_DIR"
    echo "2. Test hook manually: CLAUDE_PROJECT_DIR=/home/opsvi/master_root $HOOK_SCRIPT"
    echo "3. Restart Claude Code to reload settings"
fi
echo ""
echo "To monitor hook execution in real-time:"
echo "  tail -f $EXPORT_DIR/export.log"
