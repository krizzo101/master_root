"""
graph_query.py
Module for querying graphs and running algorithms using NetworkX.
Now supports semantic search using OpenAI embeddings (requires numpy).
"""

import os
from typing import Any, List, Tuple

import networkx as nx
import numpy as np
import openai
from tqdm import tqdm

from src.shared.interfaces.database.arango_interface import (
    DirectArangoDB as ArangoInterface,
)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def shortest_path(G: nx.Graph, source: Any, target: Any) -> List[Any]:
    """Return the shortest path between source and target nodes."""
    return nx.shortest_path(G, source=source, target=target)


def neighbors(G: nx.Graph, node: Any) -> List[Any]:
    """Return the neighbors of a node."""
    return list(G.neighbors(node))


def extract_subgraph(G: nx.Graph, nodes: List[Any]) -> nx.Graph:
    """Return the subgraph induced by the given nodes."""
    return G.subgraph(nodes).copy()


def embed_query_openai(
    query: str, model: str = "text-embedding-3-large", dimensions: int = 1536
) -> List[float]:
    """Embed a query using OpenAI's embedding API (configurable model/dimensions)."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    response = client.embeddings.create(
        input=[query], model=model, dimensions=dimensions
    )
    return response.data[0].embedding


def semantic_search(
    G: nx.Graph, query: str, top_k: int = 5, model: str = "text-embedding-ada-002"
) -> List[Tuple[str, float]]:
    """Return top-k node IDs most semantically similar to the query. Shows progress bar if >100 nodes."""
    query_emb = np.array(embed_query_openai(query, model))
    results = []
    nodes_iter = G.nodes(data=True)
    if G.number_of_nodes() > 100:
        nodes_iter = tqdm(nodes_iter, desc="Semantic search")
    for node, data in nodes_iter:
        emb = np.array(data.get("embedding"))
        if emb.shape == query_emb.shape:
            sim = np.dot(query_emb, emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-8
            )
            results.append((node, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def arango_semantic_search(
    query,
    top_k=5,
    model="text-embedding-3-large",
    dimensions=1536,
    arango_host=None,
    arango_db=None,
    arango_user=None,
    arango_pass=None,
):
    """
    Fetch all chunk docs from ArangoDB, compute cosine similarity to query embedding, and return top-k most similar chunks.
    Returns list of dicts: {score, text, file, chunk_index, arango_id, embedding}
    """
    adb = ArangoInterface(
        host=arango_host, database=arango_db, username=arango_user, password=arango_pass
    )
    # Fetch all chunks
    res = adb.execute_aql("FOR c IN chunks RETURN c")
    if not res.get("success"):
        raise RuntimeError(f"AQL error: {res.get('error')}")
    chunks = res["results"]
    # Embed query
    query_emb = np.array(embed_query_openai(query, model, dimensions))
    results = []
    for c in chunks:
        emb = np.array(c.get("embedding"))
        if emb.shape == query_emb.shape:
            sim = np.dot(query_emb, emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-8
            )
            results.append(
                {
                    "score": sim,
                    "text": c.get("text"),
                    "file": c.get("file"),
                    "chunk_index": c.get("chunk_index"),
                    "arango_id": c.get("_id"),
                    "embedding": c.get("embedding"),
                }
            )
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def arango_shortest_path(graph_name, start_vertex, end_vertex, direction="out"):
    """Use DirectArangoDB's shortest_path helper."""
    db = ArangoInterface()
    return db.shortest_path(graph_name, start_vertex, end_vertex, direction=direction)


def arango_get_neighbors(graph_name, vertex_id, direction="any"):
    """Use DirectArangoDB's get_neighbors helper."""
    db = ArangoInterface()
    return db.get_neighbors(graph_name, vertex_id, direction=direction)


def arango_get_subgraph(graph_name, start_vertex, depth=2, direction="any"):
    """Use DirectArangoDB's get_subgraph helper."""
    db = ArangoInterface()
    return db.get_subgraph(graph_name, start_vertex, depth=depth, direction=direction)


# Example usage
if __name__ == "__main__":
    print(arango_shortest_path("school", "students/01", "lectures/CSC101"))
    print(arango_get_neighbors("school", "students/01", direction="out"))
    print(arango_get_subgraph("school", "students/01", depth=2))
