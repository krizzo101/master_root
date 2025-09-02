#!/bin/bash
# Start the Chat Analytics Dashboard

cd "$(dirname "$0")"
export PYTHONPATH="/home/opsvi/master_root/libs/opsvi-monitoring:$PYTHONPATH"

echo "Starting Chat Analytics Dashboard on http://localhost:5001"
echo "Press CTRL+C to stop"

python -c "
import sys
sys.path.insert(0, '/home/opsvi/master_root/libs/opsvi-monitoring/opsvi_monitoring/chat_analytics')
from web.dashboard import app
app.run(host='0.0.0.0', port=5001, debug=True)
"
