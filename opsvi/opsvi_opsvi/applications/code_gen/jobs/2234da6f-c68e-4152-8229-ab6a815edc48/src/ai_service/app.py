import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from typing import List
import openai  # For production: replace with Huggingface or local model if desired
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_service")

# Read configuration from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not set: AI features will not work!")
openai.api_key = OPENAI_API_KEY

app = FastAPI(title="AI Service for Document Editing", version="1.0.0")

# CORS (allow from main backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production: limit to trusted origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeRequest(BaseModel):
    text: str = Field(..., description="Document text to summarize")


class SummarizeResponse(BaseModel):
    summary: str


class SuggestRequest(BaseModel):
    text: str = Field(..., description="Document text to get suggestions for")


class SuggestResponse(BaseModel):
    suggestions: List[str]


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """Summarize the provided document text using OpenAI API."""
    logger.info("Summarization requested.")
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY missing. Summarization not possible.")
        raise HTTPException(status_code=500, detail="AI service is not configured.")
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",  # Production: replace with latest model or self-hosted
            messages=[
                {"role": "system", "content": "Summarize the document succinctly."},
                {"role": "user", "content": request.text},
            ],
            max_tokens=128,
        )
        summary = completion["choices"][0]["message"]["content"].strip()
        logger.info("Summarization complete.")
        return SummarizeResponse(summary=summary)
    except Exception as e:
        logger.exception("Error during summarization: %s", str(e))
        raise HTTPException(status_code=500, detail="Summarization failed.")


@app.post("/suggest", response_model=SuggestResponse)
async def suggest(request: SuggestRequest):
    """Provide AI-powered content suggestions for the document."""
    logger.info("Suggestions requested.")
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY missing. Suggestions not possible.")
        raise HTTPException(status_code=500, detail="AI service is not configured.")
    prompt = (
        "Suggest three improvements or continuations for the following document:\n"
        + request.text
        + "\nReturn the suggestions as a bulleted list."
    )
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "You are a helpful writing assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        content = completion["choices"][0]["message"]["content"]
        # Parse bulleted list
        suggestions = [
            line.lstrip("-• ").strip()
            for line in content.splitlines()
            if line.strip() and (line.startswith("-") or line.startswith("•"))
        ]
        if not suggestions:
            suggestions = [content.strip()]  # fallback
        logger.info("Suggestions provided.")
        return SuggestResponse(suggestions=suggestions)
    except Exception as e:
        logger.exception("Error during suggestion generation: %s", str(e))
        raise HTTPException(status_code=500, detail="Suggestions failed.")


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", str(exc))
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
