import os
import subprocess
import time

import httpx
import pytest

COMPOSE_FILE = "docker-compose.yml"


def _wait_for_service(url: str, timeout: int = 60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


@pytest.mark.skipif(os.getenv("CI") != "true", reason="Run only in CI environment")
@pytest.mark.integration
def test_smoke_docker():
    env = os.environ.copy()
    env.update({
        "OPENAI_API_KEY": "dummy",
        "PERPLEXITY_API_KEY": "dummy",
        "OFFLINE_MODE": "true",
    })
    subprocess.run(["docker", "compose", "up", "-d", "--build"], check=True, env=env)
    try:
        assert _wait_for_service("http://localhost:8000/docs"), "Service not healthy"
        start = time.time()
        resp = httpx.post("http://localhost:8000/ask", json={"query": "hello"}, timeout=5)
        latency = time.time() - start
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert latency <= 2
    finally:
        subprocess.run(["docker", "compose", "down", "-v"], check=True)
