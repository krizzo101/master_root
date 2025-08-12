# mypy: ignore-errors
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.core.research_service import ResearchService

app = FastAPI(title="Enhanced Research Assistant")
service = ResearchService()


class AskRequest(BaseModel):
    query: str


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/ask")
async def ask(req: AskRequest):
    try:
        resp = await service.handle_query(req.query)
        return resp.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
