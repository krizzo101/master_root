#!/usr/bin/env python3
import os

from arango import ArangoClient
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ARANGO_URL = "http://127.0.0.1:8550"
DB_NAME = "_system"
USERNAME = "root"
PASSWORD = "change_me"
GRAPH_NAME = "specstory_graph"
VERTEX_COLLECTION = "specstory_components"
EDGE_COLLECTION = "specstory_relationships"

app = FastAPI()

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/neighborhood/{node_key}")
def get_neighborhood(node_key: str):
    try:
        client = ArangoClient(hosts=ARANGO_URL)
        db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
        node_id = f"{VERTEX_COLLECTION}/{node_key}"
        # 1-hop neighborhood
        query = """
        LET center = DOCUMENT(@node_id)
        LET neighbors = (
            FOR v, e IN 1..1 ANY @node_id GRAPH @graph
                RETURN { node: v, edge: e }
        )
        RETURN { center: center, neighbors: neighbors }
        """
        result = list(
            db.aql.execute(query, bind_vars={"node_id": node_id, "graph": GRAPH_NAME})
        )
        if not result or not result[0]["center"]:
            raise HTTPException(status_code=404, detail="Node not found")
        # Flatten nodes/edges
        nodes = {result[0]["center"]["_id"]: result[0]["center"]}
        edges = {}
        for n in result[0]["neighbors"]:
            v = n["node"]
            e = n["edge"]
            if v and v["_id"] not in nodes:
                nodes[v["_id"]] = v
            if e and e["_id"] not in edges:
                edges[e["_id"]] = e
        return {
            "nodes": list(nodes.values()),
            "edges": list(edges.values()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
