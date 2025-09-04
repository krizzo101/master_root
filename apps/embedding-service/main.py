#!/usr/bin/env python3
"""
Embedding Service API for Unified Context System

Provides REST API endpoints for generating embeddings and performing semantic search
using pgvector integration with PostgreSQL.

Runs on localhost:8001 by default.
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncpg
import numpy as np
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print(
        "Warning: sentence-transformers not installed. Install with: pip install sentence-transformers"
    )

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai not installed. Install with: pip install openai")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsvi:opsvi_secure_password@localhost:5432/unified_context",
)

# ============================================
# MODELS
# ============================================


class EmbeddingRequest(BaseModel):
    text: str = Field(..., description="Text to generate embedding for")
    model: str = Field(
        default="sentence-transformers",
        description="Model to use: 'sentence-transformers' or 'openai'",
    )


class BatchEmbeddingRequest(BaseModel):
    texts: List[str] = Field(
        ..., description="List of texts to generate embeddings for"
    )
    model: str = Field(default="sentence-transformers", description="Model to use")


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    similarity_threshold: float = Field(
        default=0.7, description="Minimum similarity threshold"
    )
    max_results: int = Field(default=10, description="Maximum number of results")
    source_filter: Optional[str] = Field(
        default=None, description="Filter by source type"
    )
    entity_filter: Optional[str] = Field(
        default=None, description="Filter by entity type"
    )


class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="Search query text")
    text_weight: float = Field(default=0.3, description="Weight for text search")
    vector_weight: float = Field(default=0.7, description="Weight for vector search")
    similarity_threshold: float = Field(
        default=0.5, description="Minimum similarity threshold"
    )
    max_results: int = Field(default=10, description="Maximum number of results")


class CodeSearchRequest(BaseModel):
    query: str = Field(..., description="Code search query")
    similarity_threshold: float = Field(
        default=0.7, description="Minimum similarity threshold"
    )
    max_results: int = Field(default=10, description="Maximum number of results")
    element_type_filter: Optional[str] = Field(
        default=None, description="Filter by element type"
    )
    language_filter: Optional[str] = Field(
        default=None, description="Filter by language"
    )


class BatchEmbeddingUpdateRequest(BaseModel):
    batch_size: int = Field(default=100, description="Batch size for processing")
    source_filter: Optional[str] = Field(
        default=None, description="Filter by source type"
    )


# ============================================
# EMBEDDING SERVICE
# ============================================


class EmbeddingService:
    def __init__(self):
        self.sentence_model = None
        self.openai_client = None
        self.db_pool = None

    async def initialize(self):
        """Initialize the embedding models and database connection."""
        # Initialize sentence transformers model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info("Loading sentence-transformers model...")
            self.sentence_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            logger.info("Sentence-transformers model loaded successfully")

        # Initialize OpenAI client
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = openai.AsyncOpenAI()
            logger.info("OpenAI client initialized")

        # Initialize database pool
        try:
            self.db_pool = await asyncpg.create_pool(
                DATABASE_URL, min_size=2, max_size=10
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def cleanup(self):
        """Clean up resources."""
        if self.db_pool:
            await self.db_pool.close()

    async def generate_embedding(
        self, text: str, model: str = "sentence-transformers"
    ) -> List[float]:
        """Generate embedding for a single text."""
        if model == "sentence-transformers":
            if not self.sentence_model:
                raise HTTPException(
                    status_code=500, detail="Sentence transformers not available"
                )

            # Pad to 1536 dimensions for consistency with OpenAI embeddings
            embedding = self.sentence_model.encode(text)
            if len(embedding) < 1536:
                # Pad with zeros
                padded_embedding = np.zeros(1536)
                padded_embedding[: len(embedding)] = embedding
                embedding = padded_embedding

            return embedding.tolist()

        elif model == "openai":
            if not self.openai_client:
                raise HTTPException(
                    status_code=500, detail="OpenAI client not available"
                )

            try:
                response = await self.openai_client.embeddings.create(
                    model="text-embedding-ada-002", input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")
                raise HTTPException(
                    status_code=500, detail=f"OpenAI embedding failed: {e}"
                )

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")

    async def generate_embeddings_batch(
        self, texts: List[str], model: str = "sentence-transformers"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text, model)
            embeddings.append(embedding)
        return embeddings


# Global service instance
embedding_service = EmbeddingService()

# ============================================
# FASTAPI APP SETUP
# ============================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await embedding_service.initialize()
    yield
    # Shutdown
    await embedding_service.cleanup()


app = FastAPI(
    title="Embedding Service API",
    description="Semantic search and embedding generation for unified context system",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "sentence_transformers": SENTENCE_TRANSFORMERS_AVAILABLE,
            "openai": OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY")),
            "database": bool(embedding_service.db_pool),
        },
    }


@app.get("/models")
async def list_models():
    """List available embedding models."""
    models = []
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        models.append(
            {
                "name": "sentence-transformers",
                "dimensions": 1536,  # Padded to match OpenAI
                "description": "Fast local embeddings using all-MiniLM-L6-v2",
            }
        )

    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        models.append(
            {
                "name": "openai",
                "dimensions": 1536,
                "description": "OpenAI text-embedding-ada-002",
            }
        )

    return {"models": models}


# ============================================
# EMBEDDING GENERATION ENDPOINTS
# ============================================


@app.post("/embed")
async def create_embedding(request: EmbeddingRequest):
    """Generate embedding for a single text."""
    try:
        embedding = await embedding_service.generate_embedding(
            request.text, request.model
        )
        return {
            "embedding": embedding,
            "model": request.model,
            "dimensions": len(embedding),
            "text_length": len(request.text),
        }
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed/batch")
async def create_embeddings_batch(request: BatchEmbeddingRequest):
    """Generate embeddings for multiple texts."""
    try:
        embeddings = await embedding_service.generate_embeddings_batch(
            request.texts, request.model
        )
        return {
            "embeddings": embeddings,
            "model": request.model,
            "count": len(embeddings),
            "dimensions": len(embeddings[0]) if embeddings else 0,
        }
    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SEMANTIC SEARCH ENDPOINTS
# ============================================


@app.post("/search/semantic")
async def semantic_search(request: SemanticSearchRequest):
    """Perform semantic search using vector similarity."""
    try:
        # Generate embedding for query
        query_embedding = await embedding_service.generate_embedding(request.query)

        # Execute search
        async with embedding_service.db_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT * FROM find_similar_context($1, $2, $3, $4, $5)
                """,
                query_embedding,
                request.similarity_threshold,
                request.max_results,
                request.source_filter,
                request.entity_filter,
            )

        return {
            "query": request.query,
            "results": [dict(row) for row in results],
            "count": len(results),
        }

    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/hybrid")
async def hybrid_search(request: HybridSearchRequest):
    """Perform hybrid search combining text and vector similarity."""
    try:
        # Generate embedding for query
        query_embedding = await embedding_service.generate_embedding(request.query)

        # Execute hybrid search
        async with embedding_service.db_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT * FROM hybrid_context_search($1, $2, $3, $4, $5, $6)
                """,
                request.query,
                query_embedding,
                request.text_weight,
                request.vector_weight,
                request.similarity_threshold,
                request.max_results,
            )

        return {
            "query": request.query,
            "results": [dict(row) for row in results],
            "count": len(results),
            "search_weights": {
                "text": request.text_weight,
                "vector": request.vector_weight,
            },
        }

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search/code")
async def code_search(request: CodeSearchRequest):
    """Perform semantic search for code elements."""
    try:
        # Generate embedding for query
        query_embedding = await embedding_service.generate_embedding(request.query)

        # Execute code search
        async with embedding_service.db_pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT * FROM find_similar_code($1, $2, $3, $4, $5)
                """,
                query_embedding,
                request.similarity_threshold,
                request.max_results,
                request.element_type_filter,
                request.language_filter,
            )

        return {
            "query": request.query,
            "results": [dict(row) for row in results],
            "count": len(results),
        }

    except Exception as e:
        logger.error(f"Code search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# BATCH PROCESSING ENDPOINTS
# ============================================


@app.post("/embeddings/update-batch")
async def update_embeddings_batch(
    request: BatchEmbeddingUpdateRequest, background_tasks: BackgroundTasks
):
    """Process batch embedding updates for items without embeddings."""
    try:
        async with embedding_service.db_pool.acquire() as conn:
            # Get items needing embeddings
            items = await conn.fetch(
                """
                SELECT * FROM get_items_needing_embeddings($1, $2)
                """,
                request.batch_size,
                request.source_filter,
            )

        if not items:
            return {"message": "No items need embedding updates", "processed": 0}

        # Process embeddings in background
        background_tasks.add_task(process_batch_embeddings, items)

        return {
            "message": f"Started batch processing for {len(items)} items",
            "batch_size": len(items),
        }

    except Exception as e:
        logger.error(f"Batch embedding update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_batch_embeddings(items):
    """Background task to process batch embeddings."""
    try:
        for item in items:
            # Combine text fields for embedding
            text_parts = []
            if item["title"]:
                text_parts.append(item["title"])
            if item["content"]:
                text_parts.append(item["content"])
            if item["summary"]:
                text_parts.append(item["summary"])

            text = " ".join(text_parts)

            if len(text.strip()) > 10:  # Only process if we have meaningful text
                # Generate embedding
                embedding = await embedding_service.generate_embedding(text)

                # Update database
                async with embedding_service.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        SELECT update_context_embedding($1, $2, $3)
                        """,
                        item["id"],
                        embedding,
                        "sentence-transformers/all-MiniLM-L6-v2",
                    )

                logger.info(f"Updated embedding for item {item['id']}")

        logger.info(f"Completed batch processing for {len(items)} items")

    except Exception as e:
        logger.error(f"Background embedding processing failed: {e}")


# ============================================
# ANALYTICS ENDPOINTS
# ============================================


@app.get("/stats")
async def get_embedding_stats():
    """Get embedding coverage statistics."""
    try:
        async with embedding_service.db_pool.acquire() as conn:
            stats = await conn.fetch("SELECT * FROM embedding_stats")

        return {
            "embedding_stats": [dict(row) for row in stats],
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clusters")
async def get_content_clusters(
    cluster_threshold: float = Query(
        0.8, description="Similarity threshold for clustering"
    ),
    min_cluster_size: int = Query(3, description="Minimum items per cluster"),
):
    """Find content clusters based on embedding similarity."""
    try:
        async with embedding_service.db_pool.acquire() as conn:
            clusters = await conn.fetch(
                """
                SELECT * FROM find_content_clusters($1, $2)
                """,
                cluster_threshold,
                min_cluster_size,
            )

        return {
            "clusters": [dict(row) for row in clusters],
            "parameters": {
                "cluster_threshold": cluster_threshold,
                "min_cluster_size": min_cluster_size,
            },
        }

    except Exception as e:
        logger.error(f"Cluster analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
