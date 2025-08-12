"""
graph_loader.py
Module for ingesting graph data from various sources into a NetworkX graph.
Now supports ingesting markdown files and embedding them with OpenAI for semantic search.
Requires: openai (pip install openai), OPENAI_API_KEY env variable.
"""

import csv
import json
import os

import networkx as nx
import openai
import tiktoken
from tqdm import tqdm

from src.shared.interfaces.database.arango_interface import (
    DirectArangoDB as ArangoInterface,
)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_graph_from_csv(path: str) -> nx.Graph:
    """Load an edge list from a CSV file into a NetworkX graph."""
    G = nx.Graph()
    with open(path, newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) >= 2:
                G.add_edge(row[0], row[1])
    return G


def load_graph_from_json(path: str) -> nx.Graph:
    """Load a graph from a JSON file (adjacency list format)."""
    G = nx.Graph()
    with open(path) as f:
        data = json.load(f)
    for node, neighbors in data.items():
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    return G


def load_graph_from_neo4j(uri: str, user: str, password: str) -> nx.Graph:
    """Placeholder for loading a graph from Neo4j. Not implemented."""
    raise NotImplementedError("Neo4j loading not implemented in this demo.")


def embed_text_openai(
    text: str, model: str = "text-embedding-3-large", dimensions: int = 1536
) -> list[float]:
    """Embed text using OpenAI's embedding API (configurable model/dimensions)."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    response = client.embeddings.create(
        input=[text], model=model, dimensions=dimensions
    )
    return response.data[0].embedding


def chunk_markdown(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
    encoding_name: str = "cl100k_base",
) -> list[str]:
    """Chunk markdown text into segments of chunk_size tokens with overlap using tiktoken."""
    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    chunks = []
    i = 0
    while i < len(tokens):
        chunk_tokens = tokens[i : i + chunk_size]
        chunk = enc.decode(chunk_tokens)
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def load_markdown_dir_to_graph(directory: str, G: nx.Graph = None) -> nx.Graph:
    """Ingest all markdown files in a directory, embed chunks, and add as nodes."""
    if G is None:
        G = nx.Graph()
    for fname in os.listdir(directory):
        if fname.endswith(".md"):
            path = os.path.join(directory, fname)
            with open(path, encoding="utf-8") as f:
                text = f.read()
            chunks = chunk_markdown(text)
            for i, chunk in enumerate(chunks):
                node_id = f"{fname}::chunk_{i}"
                embedding = embed_text_openai(chunk)
                G.add_node(
                    node_id,
                    text=chunk,
                    embedding=embedding,
                    file=fname,
                    chunk_index=i,
                )
            # Optionally, link chunks sequentially
            for i in range(len(chunks) - 1):
                G.add_edge(f"{fname}::chunk_{i}", f"{fname}::chunk_{i+1}")
    return G


def ingest_markdown_dir_with_progress(
    md_dir,
    model,
    dimensions,
    chunk_size,
    overlap,
    arango_host=None,
    arango_db=None,
    arango_user=None,
    arango_pass=None,
):
    import glob
    import os

    import networkx as nx

    # Initialize ArangoDB
    adb = ArangoInterface(
        host=arango_host, database=arango_db, username=arango_user, password=arango_pass
    )
    # Ensure collections exist
    if not adb.collection_exists("chunks"):
        adb.create_collection("chunks")
    if not adb.collection_exists("chunk_edges"):
        adb.create_collection("chunk_edges", edge=True)
    G = nx.Graph()
    files = glob.glob(os.path.join(md_dir, "*.md"))
    for file in tqdm(files, desc="Files"):
        with open(file) as f:
            text = f.read()
        chunks = chunk_markdown(text, chunk_size=chunk_size, overlap=overlap)
        prev_id = None
        chunk_docs = []
        edge_docs = []
        for i, chunk in enumerate(tqdm(chunks, desc="Chunks", leave=False)):
            embedding = embed_text_openai(chunk, model=model, dimensions=dimensions)
            chunk_doc = {
                "text": chunk,
                "embedding": embedding,
                "file": os.path.basename(file),
                "chunk_index": i,
            }
            chunk_docs.append(chunk_doc)
        # Insert all chunks, get their _ids
        insert_result = adb.batch_insert("chunks", chunk_docs)
        chunk_ids = [
            r["_id"]
            for r in insert_result.get("results", [])
            if isinstance(r, dict) and "_id" in r
        ]
        for idx, chunk_id in enumerate(chunk_ids):
            node_id = f"{os.path.basename(file)}::chunk_{idx}"
            G.add_node(
                node_id,
                text=chunk_docs[idx]["text"],
                embedding=chunk_docs[idx]["embedding"],
                file=chunk_docs[idx]["file"],
                chunk_index=chunk_docs[idx]["chunk_index"],
                arango_id=chunk_id,
            )
            if idx > 0:
                edge_docs.append({"_from": chunk_ids[idx - 1], "_to": chunk_id})
        if edge_docs:
            adb.batch_insert("chunk_edges", edge_docs)
    return G
