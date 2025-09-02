#!/usr/bin/env python3
"""
FastAPI wrapper for the Embedding Service
Provides HTTP endpoints for embedding generation
"""

import logging
from typing import List, Optional

from embedding_service import EmbeddingService
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Embedding Service",
    description="Generate embeddings for knowledge base entries",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embedding service
embedding_service = EmbeddingService()


# Pydantic models
class EmbeddingRequest(BaseModel):
    text: str
    use_cache: bool = True


class BatchEmbeddingRequest(BaseModel):
    texts: List[str]
    use_cache: bool = True


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    dimension: int


class BatchEmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    dimension: int
    count: int


class HealthResponse(BaseModel):
    status: str
    model: str
    dimension: int


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the service is healthy and the model is loaded"""
    try:
        # Try to load the model if not already loaded
        embedding_service._ensure_model_loaded()
        return HealthResponse(
            status="healthy",
            model=embedding_service.model_name,
            dimension=embedding_service.vector_dimension,
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """Generate embedding for a single text"""
    try:
        embedding = embedding_service.generate_embedding(
            request.text, use_cache=request.use_cache
        )
        return EmbeddingResponse(embedding=embedding, dimension=len(embedding))
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed/batch", response_model=BatchEmbeddingResponse)
async def generate_embeddings_batch(request: BatchEmbeddingRequest):
    """Generate embeddings for multiple texts"""
    try:
        embeddings = embedding_service.generate_embeddings_batch(
            request.texts, use_cache=request.use_cache
        )
        return BatchEmbeddingResponse(
            embeddings=embeddings,
            dimension=embedding_service.vector_dimension,
            count=len(embeddings),
        )
    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similarity")
async def compute_similarity(text1: str, text2: str):
    """Compute cosine similarity between two texts"""
    try:
        similarity = embedding_service.compute_similarity(text1, text2)
        return {"similarity": similarity, "text1": text1, "text2": text2}
    except Exception as e:
        logger.error(f"Similarity computation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Knowledge Embedding Service",
        "version": "1.0.0",
        "endpoints": [
            "/health - Service health check",
            "/embed - Generate single embedding",
            "/embed/batch - Generate batch embeddings",
            "/similarity - Compute text similarity",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
