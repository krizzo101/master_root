"""
AI Service for Summarization and Suggestions (FastAPI).
Implements /summarize and /suggest endpoints for document processing, with JWT authentication and input validation.
"""
import logging
import os
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, constr
from transformers import Pipeline, pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from environment
JWT_SECRET = os.getenv("JWT_SECRET", "replace-this-with-a-secure-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Authentication setup
security = HTTPBearer()

# Load summarization pipeline (use a lightweight model for demo)
summarizer: Pipeline | None = None
suggestion_generator: Pipeline | None = None


def get_summarizer() -> Pipeline:
    global summarizer
    if summarizer is None:
        logger.info("Loading summarization pipeline...")
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return summarizer


def get_suggestion_generator() -> Pipeline:
    global suggestion_generator
    if suggestion_generator is None:
        logger.info("Loading suggestion generator pipeline...")
        suggestion_generator = pipeline(
            "text2text-generation", model="google/flan-t5-base"
        )
    return suggestion_generator


class SummarizeRequest(BaseModel):
    text: constr(min_length=30, max_length=20000)


class SummarizeResponse(BaseModel):
    summary: str


class SuggestionRequest(BaseModel):
    text: constr(min_length=10, max_length=20000)


class SuggestionResponse(BaseModel):
    suggestions: list[str]


def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict[str, Any]:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f"JWT successfully verified for sub={payload.get('sub')}")
        return payload
    except jwt.PyJWTError as exc:
        logger.warning(f"JWT verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication."
        )


app = FastAPI(
    title="AI Summarization & Suggestion Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["health"])
def health_check():
    """Liveliness probe."""
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse, tags=["ai"])
def summarize(req: SummarizeRequest, user=Depends(verify_jwt)):
    """
    Return a summary of the input document text using an LLM.
    """
    try:
        summ = get_summarizer()(
            req.text, max_length=256, min_length=24, do_sample=False
        )
        summary = summ[0]["summary_text"]
        logger.info(f"Summarization successful for user={user.get('sub')}")
        return SummarizeResponse(summary=summary)
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail="Summarization error")


@app.post("/suggest", response_model=SuggestionResponse, tags=["ai"])
def suggest(req: SuggestionRequest, user=Depends(verify_jwt)):
    """
    Return AI-generated revision suggestions for the provided text.
    """
    suggestions = []
    try:
        generator = get_suggestion_generator()
        # Prompt: ask model to suggest edits, improvements, next sentence, etc
        prompt = f"Suggest improvements for the following text. Return 3 bullet points.\nText: {req.text}\nSuggestions:"
        result = generator(prompt, max_length=128, num_return_sequences=1)
        suggestion_text = result[0]["generated_text"]
        # Try to split into suggestions
        for line in suggestion_text.split("\n"):
            clean = line.strip("•- 0123456789.").strip()
            if clean:
                suggestions.append(clean)
        if not suggestions:
            suggestions = [suggestion_text]
        logger.info(f"Suggestions generated for user={user.get('sub')}")
        return SuggestionResponse(suggestions=suggestions[:3])
    except Exception as e:
        logger.error(f"Suggestion generation failed: {e}")
        raise HTTPException(status_code=500, detail="Suggestion generation error")
