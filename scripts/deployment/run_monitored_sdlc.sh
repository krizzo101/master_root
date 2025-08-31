#!/bin/bash
# Enhanced SDLC Execution with Monitoring and Commands
# This script demonstrates how to use the installed commands with our monitoring system

set -e

PROJECT_NAME="$1"
REQUIREMENTS="$2"

if [ -z "$PROJECT_NAME" ] || [ -z "$REQUIREMENTS" ]; then
    echo "Usage: $0 <project_name> <requirements>"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ENHANCED SDLC WITH MONITORING & COMMANDS                ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# 1. Start project session
echo -e "\n📋 Starting project session..."
/home/opsvi/master_root/.claude/commands/project-session-start.md "$PROJECT_NAME"

# 2. Load context
echo -e "\n🔄 Loading project context..."
/home/opsvi/master_root/.claude/commands/context-prime.md

# 3. Run preflight checks
echo -e "\n✈️ Running preflight checks..."
/home/opsvi/master_root/.claude/commands/sdlc-preflight-enhanced.sh

# 4. Export current state for rollback
echo -e "\n💾 Creating baseline snapshot..."
/home/opsvi/master_root/.claude/commands/dump.md

# 5. Execute SDLC phases with monitoring
echo -e "\n🚀 Starting SDLC execution with monitoring..."

# Discovery Phase
echo -e "\n== DISCOVERY PHASE =="
python /home/opsvi/master_root/.claude/commands/sdlc-phase-executor-v2.py \
    --phase discovery \
    --project "$PROJECT_NAME" \
    --requirements "$REQUIREMENTS" \
    --monitoring enabled

# Check gate requirements
/home/opsvi/master_root/.claude/commands/sdlc-gates.md discovery

# Design Phase
echo -e "\n== DESIGN PHASE =="
python /home/opsvi/master_root/.claude/commands/sdlc-phase-executor-v2.py \
    --phase design \
    --project "$PROJECT_NAME" \
    --monitoring enabled

# Planning Phase
echo -e "\n== PLANNING PHASE =="
python /home/opsvi/master_root/.claude/commands/sdlc-phase-executor-v2.py \
    --phase planning \
    --project "$PROJECT_NAME" \
    --monitoring enabled

# 6. Export sessions for analysis
echo -e "\n📊 Exporting session data..."
python /home/opsvi/master_root/.claude/commands/sdlc-session-exporter.py

# 7. Run violation analysis
echo -e "\n🔍 Checking for violations..."
python /home/opsvi/master_root/.claude/commands/sdlc-violation-analyzer.py

# 8. Generate documentation
echo -e "\n📚 Generating comprehensive documentation..."
/home/opsvi/master_root/.claude/commands/docs-comprehensive.md

# 9. Update project session
echo -e "\n✅ Updating project session..."
/home/opsvi/master_root/.claude/commands/project-session-update.md "SDLC phases completed"

# 10. Show session summary
/home/opsvi/master_root/.claude/commands/project-session-current.md

echo -e "\n╔══════════════════════════════════════════════════════════════╗"
echo "║     SDLC EXECUTION COMPLETE                                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"

echo -e "\nSession logs available at: .sdlc-sessions/"
echo "Monitoring dashboard at: /tmp/agent_monitoring/dashboard/status.json"