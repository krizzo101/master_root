import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.shared.openai_interfaces.embeddings_interface import OpenAIEmbeddingsInterface

# Embedding & Indexing Module
# Embeds artifacts for semantic search and updates the knowledge graph.


def embed_text(text):
    """
    Generate an embedding vector for the input text using OpenAIEmbeddingsInterface.
    Model: text-embedding-ada-002
    Interface: OpenAIEmbeddingsInterface
    """
    embeddings_client = OpenAIEmbeddingsInterface()
    response = embeddings_client.create_embedding(
        input_text=text, model="text-embedding-ada-002"
    )
    return response["data"][0]["embedding"]


def embed_all(artifacts):
    """
    Embed all artifacts using OpenAIEmbeddingsInterface.
    Model: text-embedding-ada-002
    Interface: OpenAIEmbeddingsInterface
    """
    return [(path, embed_text(content)) for path, content in artifacts]


if __name__ == "__main__":
    from ingestion import ingest_all

    artifacts = ingest_all()
    embeddings = embed_all(artifacts[:2])  # Limit for quick test
    print(f"Embedded {len(embeddings)} artifacts.")
    print("Sample:", embeddings[0] if embeddings else "No embeddings.")
