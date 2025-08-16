"""
FastAPI application for AI-powered document summarization and suggestion service.
"""
import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr
from transformers import Pipeline, pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables/config
HF_MODEL_SUMMARIZATION = os.getenv("HF_MODEL_SUMMARIZATION", "facebook/bart-large-cnn")
HF_MODEL_GENERATION = os.getenv("HF_MODEL_GENERATION", "gpt2")

# FastAPI App
app = FastAPI(title="Document AI Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeRequest(BaseModel):
    text: constr(min_length=50, max_length=5000)
    max_summary_length: int | None = 150
    min_summary_length: int | None = 40


class SummarizeResponse(BaseModel):
    summary: str


class SuggestionRequest(BaseModel):
    prompt: constr(min_length=1, max_length=300)
    max_tokens: int | None = 90


class SuggestionResponse(BaseModel):
    suggestions: list[str]


@app.on_event("startup")
def load_models() -> None:
    """
    Load the summarization and suggestion models into the app state on startup.
    """
    try:
        summarizer = pipeline("summarization", model=HF_MODEL_SUMMARIZATION)
        suggester = pipeline("text-generation", model=HF_MODEL_GENERATION)
        app.state.summarizer = summarizer
        app.state.suggester = suggester
        logger.info("Loaded transformer pipelines successfully.")
    except Exception as e:
        logger.exception(f"Model loading failed: {e}")
        raise


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """
    Summarize a document using a state-of-the-art language model.
    """
    try:
        summarizer: Pipeline = app.state.summarizer
        logger.info(f"Summarizing text of length {len(request.text)}.")
        summary = summarizer(
            request.text,
            max_length=request.max_summary_length,
            min_length=request.min_summary_length,
            do_sample=False,
        )
        result = summary[0]["summary_text"]
        return SummarizeResponse(summary=result)
    except Exception:
        logger.exception("Error during summarization.")
        raise HTTPException(status_code=500, detail="AI summarization failed.")


@app.post("/suggest", response_model=SuggestionResponse)
def suggest(request: SuggestionRequest) -> SuggestionResponse:
    """
    Generate suggestions based on the current document context/prompt.
    """
    try:
        suggester: Pipeline = app.state.suggester
        logger.info(f"Generating suggestions for prompt: {request.prompt}")
        results = suggester(
            request.prompt,
            max_length=min(len(request.prompt.split()) + request.max_tokens, 250),
            num_return_sequences=3,
        )
        suggestions = [
            r["generated_text"][len(request.prompt) :].strip() for r in results
        ]
        # Post-process suggestions (remove empty/duplicate)
        unique_suggestions = list({s for s in suggestions if s})
        return SuggestionResponse(suggestions=unique_suggestions)
    except Exception:
        logger.exception("Error during suggestion generation.")
        raise HTTPException(status_code=500, detail="AI suggestion failed.")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/healthz")
def health_check() -> dict:
    """
    Liveness probe endpoint.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8081, reload=True)
