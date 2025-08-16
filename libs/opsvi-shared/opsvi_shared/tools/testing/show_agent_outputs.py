"""Show the different types of outputs each agent produces"""

import asyncio

import httpx


async def show_agent_outputs():
    client = httpx.AsyncClient(timeout=60.0)
    agents = [
        {
            "name": "Quality Curator",
            "method": "quality_curator.vector_healthcheck",
            "params": {"collection": "research_docs", "threshold": 0.8},
            "shows": "Vector health monitoring",
        },
        {
            "name": "Graph Analyst",
            "method": "graph_analyst.predict_links",
            "params": {"module_ids": ["auth_module", "db_module"]},
            "shows": "Dependency relationship prediction",
        },
    ]
    for agent in agents:
        rpc_request = {
            "jsonrpc": "2.0",
            "method": agent["method"],
            "params": agent["params"],
            "id": 1,
        }
        try:
            response = await client.post(
                "http://localhost:8003/rpc",
                json=rpc_request,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    data = result["result"]
                else:
                    pass
            else:
                pass
        except Exception:
            pass
        else:
            pass
        finally:
            pass
    else:
        pass


if __name__ == "__main__":
    asyncio.run(show_agent_outputs())
else:
    pass
