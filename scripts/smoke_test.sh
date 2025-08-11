#!/usr/bin/env bash
set -euo pipefail
export OPENAI_API_KEY=sk-dummy-key-for-offline-mode
export PERPLEXITY_API_KEY=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
export OFFLINE_MODE=true
docker-compose up -d --build
python - <<'PY'
import time, httpx, sys, os, json
url = "http://localhost:8000/ask"
start=time.time()
for _ in range(30):
    try:
        r=httpx.post(url, json={"query":"smoke"},timeout=5)
        if r.status_code==200:
            data=r.json();
            print("Response:", json.dumps(data)[:120])
            if time.time()-start>5:
                print("Latency too high", file=sys.stderr); sys.exit(1)
            sys.exit(0)
    except Exception:
        pass
    time.sleep(1)
print("Service failed", file=sys.stderr)
sys.exit(1)
PY
docker-compose down -v
