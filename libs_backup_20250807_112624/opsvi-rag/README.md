# OPSVI RAG Library

Retrieval Augmented Generation utilities for OPSVI applications.

## Features

- Qdrant client integration
- Embedding model management
- Semantic search capabilities
- Collection management

## Usage

```python
from opsvi_rag import QdrantClient, EmbeddingModel, SearchEngine

# Initialize client
client = QdrantClient()

# Create collection
client.create_collection("my_collection")

# Search documents
results = client.search("my_collection", "query text", limit=10)
```

## Installation

```bash
uv add opsvi-rag
```