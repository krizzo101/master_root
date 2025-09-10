#!/bin/bash
# Quick experiment status checker

echo "=== CANARY EXPERIMENT STATUS ==="
echo ""
echo "Active Canaries:"
python3 -c "
import json
with open('/home/opsvi/master_root/.claude/rotation/canary_deployments.json', 'r') as f:
    data = json.load(f)
    for path, info in data.get('active_canaries', {}).items():
        print(f\"  📍 {path.split('/')[-2] if '/' in path else 'root'}/{path.split('/')[-1]}: {info['canary_id']}\")
"

echo ""
echo "Deployment Times:"
python3 -c "
import json
from datetime import datetime
with open('/home/opsvi/master_root/.claude/rotation/canary_deployments.json', 'r') as f:
    data = json.load(f)
    for path, info in data.get('active_canaries', {}).items():
        deployed = datetime.fromisoformat(info['deployed_at'])
        age = (datetime.now() - deployed).total_seconds()
        if age > 3600:
            age_str = f'{age/3600:.1f} hours ago'
        elif age > 60:
            age_str = f'{age/60:.0f} minutes ago'
        else:
            age_str = f'{age:.0f} seconds ago'
        print(f\"  ⏰ {info['canary_id']}: deployed {age_str}\")
"

echo ""
echo "When agents trigger these behaviors, run:"
echo "  python3 .claude/rotation/monitor_reactions.py"
echo ""
echo "The true metric is the lag between deployment and reaction!"
