"""
AI Assistance Service for Real-Time Collaborative Document Editing
Provides endpoints for summarization and suggestions using OpenAI API or HuggingFace Transformers
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional
import httpx

# Optional import for OpenAI, fallback to transformers
try:
    import openai  # type: ignore

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger("ai_service")
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
USE_OPENAI = bool(OPENAI_API_KEY)


class SummarizationRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Document content for summarization.",
    )
    language: Optional[str] = Field(None, description="Language of the document.")


class SuggestionRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Document content for suggestion.",
    )
    context: Optional[str] = Field(
        None, description="Additional context about the document."
    )


class AIResponse(BaseModel):
    summary: Optional[str] = None
    suggestions: Optional[str] = None


app = FastAPI(
    title="AI Assistance Service",
    version="1.0.0",
    description="Provides AI-powered summarization and suggestion endpoints for collaborative documents.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


async def summarize_with_openai(content: str, language: Optional[str]) -> str:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured.")
    openai.api_key = OPENAI_API_KEY
    prompt = f"Summarize the following document in a concise form: {content}"
    if language:
        prompt = f"Summarize the following document in {language} in a concise form: {content}"
    logger.info("Sending summarization request to OpenAI API.")
    try:
        resp = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=300,
            temperature=0.5,
        )
        return resp.choices[0].text.strip()
    except Exception as e:
        logger.exception("OpenAI API summarization failed.")
        raise HTTPException(status_code=502, detail="AI summarization failed.")


async def suggest_with_openai(content: str, context: Optional[str]) -> str:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured.")
    openai.api_key = OPENAI_API_KEY
    prompt = f"Suggest improvements to the following document: {content}"
    if context:
        prompt = f"Given the context '{context}', suggest improvements to the following document: {content}"
    try:
        resp = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=300,
            temperature=0.6,
        )
        return resp.choices[0].text.strip()
    except Exception as e:
        logger.exception("OpenAI API suggestion failed.")
        raise HTTPException(status_code=502, detail="AI suggestion failed.")


@app.post("/summarize", response_model=AIResponse)
async def summarize(request: SummarizationRequest):
    """
    Summarize the provided document content.
    """
    logger.info("Summarization requested.")
    if USE_OPENAI:
        summary = await summarize_with_openai(request.content, request.language)
    else:
        # Fallback: Use HuggingFace inference API
        payload = {"inputs": request.content}
        headers = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                hf_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
                r = await client.post(hf_url, json=payload, headers=headers)
                r.raise_for_status()
                result = r.json()
                summary = (
                    result[0]["summary_text"]
                    if isinstance(result, list)
                    else result.get("summary_text", "<No summary available>")
                )
        except Exception as e:
            logger.error("HuggingFace summarization failed: %s", e)
            raise HTTPException(
                status_code=502,
                detail="AI summarization failed (HuggingFace fallback).",
            )
    return AIResponse(summary=summary)


@app.post("/suggest", response_model=AIResponse)
async def suggest(request: SuggestionRequest):
    """
    Provide suggestions for improving the document content.
    """
    logger.info("Suggestion endpoint called.")
    if USE_OPENAI:
        suggestions = await suggest_with_openai(request.content, request.context)
    else:
        payload = {"inputs": f"Suggest improvements for: {request.content}"}
        headers = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                hf_url = "https://api-inference.huggingface.co/models/gpt2"
                r = await client.post(hf_url, json=payload, headers=headers)
                r.raise_for_status()
                result = r.json()
                suggestions = (
                    result[0]["generated_text"]
                    if isinstance(result, list)
                    else result.get("generated_text", "<No suggestions available>")
                )
        except Exception as e:
            logger.error("HuggingFace suggestion failed: %s", e)
            raise HTTPException(
                status_code=502, detail="AI suggestion failed (HuggingFace fallback)."
            )
    return AIResponse(suggestions=suggestions)


@app.get("/healthz", tags=["Health"])
def healthz():
    """Health check endpoint."""
    return {"status": "ok"}
