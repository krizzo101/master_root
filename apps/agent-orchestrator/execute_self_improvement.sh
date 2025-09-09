#!/bin/bash
# Orchestrator Self-Improvement Execution Script
# This script safely executes the orchestrator's self-refactoring workflow

set -e

echo "🔧 ORCHESTRATOR SELF-IMPROVEMENT WORKFLOW"
echo "========================================="
echo ""

# Safety checks
echo "📋 Pre-flight checks..."
if [ ! -f "orchestrator_self_improvement.json" ]; then
    echo "❌ Error: orchestrator_self_improvement.json not found"
    exit 1
fi

# Check git status
if ! git diff --quiet; then
    echo "⚠️  Warning: Uncommitted changes detected"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create backup directory
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Creating safety backup in $BACKUP_DIR..."

# Backup current code
tar -czf "$BACKUP_DIR/orchestrator_backup.tar.gz" src/ docs/ test/ *.py *.json 2>/dev/null || true
echo "✅ Backup created"

# Create restore script
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
echo "🔄 Restoring orchestrator from backup..."
tar -xzf orchestrator_backup.tar.gz
echo "✅ Restore complete"
EOF
chmod +x "$BACKUP_DIR/restore.sh"

echo ""
echo "🚀 Executing self-improvement workflow..."
echo "This will:"
echo "  1. Create comprehensive backups"
echo "  2. Fix concurrency bottlenecks (Token Pool, File I/O)"
echo "  3. Optimize resource consumption (Memory, CPU)"
echo "  4. Refactor architectural anti-patterns"
echo "  5. Validate all improvements with tests"
echo ""
echo "Estimated time: 45-60 minutes"
echo ""
read -p "Start self-improvement process? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📊 Starting orchestrator with UnifiedOrchestrator (full capabilities)..."

    # Execute with all features enabled
    /home/opsvi/miniconda/bin/python main.py \
        --tasks-file orchestrator_self_improvement.json \
        --use-unified \
        --max-parallel 3 \
        --output-dir ./output/self_improvement_$(date +%Y%m%d_%H%M%S) \
        --dpo-level 3 \
        2>&1 | tee "$BACKUP_DIR/execution.log"

    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✅ Self-improvement workflow completed successfully!"
        echo "📊 Check performance metrics in: output/self_improvement_*/metrics/"
        echo "📝 Review changes with: git diff"
        echo "🔄 To restore if needed: $BACKUP_DIR/restore.sh"
    else
        echo ""
        echo "❌ Self-improvement workflow failed (exit code: $EXIT_CODE)"
        echo "📝 Check logs in: $BACKUP_DIR/execution.log"
        echo "🔄 To restore: $BACKUP_DIR/restore.sh"
    fi
else
    echo "❌ Self-improvement cancelled"
    echo "💾 Backup still available in: $BACKUP_DIR"
fi
