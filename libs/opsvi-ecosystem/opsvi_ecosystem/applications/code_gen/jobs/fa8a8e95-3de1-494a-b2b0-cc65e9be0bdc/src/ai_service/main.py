import asyncio
import logging

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ai_service.ai_logic import (
    detect_dependencies,
    estimate_completion_times,
    prioritize_tasks,
    suggest_optimal_scheduling,
)
from ai_service.models import (
    AIResponse,
    TaskInput,
)

logger = logging.getLogger("ai_service")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI-Powered Task Intelligence Service",
    description="AI microservice for task prioritization, estimation, dependency detection, and scheduling.",
    version="1.0.0",
)

# CORS for development
dev_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=dev_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.post("/prioritize", response_model=AIResponse)
async def prioritize(tasks_input: TaskInput):
    """
    Prioritize tasks using AI model based on importance, dependencies, deadlines, and learned criteria.
    """
    logger.info(f"Prioritizing {len(tasks_input.tasks)} tasks")
    try:
        priority_order = await asyncio.to_thread(
            prioritize_tasks, tasks_input.tasks, tasks_input.members
        )
        return AIResponse(result=priority_order)
    except Exception as exc:
        logger.exception("Error during prioritization")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/estimate", response_model=AIResponse)
async def estimate(tasks_input: TaskInput):
    """
    Estimate completion time of tasks using AI/ML algorithms.
    """
    logger.info(f"Estimating durations for {len(tasks_input.tasks)} tasks")
    try:
        estimates = await asyncio.to_thread(
            estimate_completion_times, tasks_input.tasks
        )
        return AIResponse(result=estimates)
    except Exception as exc:
        logger.exception("Error during estimation")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/detect_dependencies", response_model=AIResponse)
async def detect_deps(tasks_input: TaskInput):
    """
    Detect dependencies between tasks using ML/NLP.
    """
    logger.info("Detecting dependencies between tasks")
    try:
        dependencies = await asyncio.to_thread(detect_dependencies, tasks_input.tasks)
        return AIResponse(result=dependencies)
    except Exception as exc:
        logger.exception("Dependency detection error")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/suggest_schedule", response_model=AIResponse)
async def suggest_schedule(tasks_input: TaskInput):
    """
    Suggest optimal scheduling for tasks given members, priorities, and dependencies.
    """
    logger.info("Suggesting optimal schedule")
    try:
        schedule = await asyncio.to_thread(
            suggest_optimal_scheduling, tasks_input.tasks, tasks_input.members
        )
        return AIResponse(result=schedule)
    except Exception as exc:
        logger.exception("Optimal scheduling error")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run("ai_service.main:app", host="0.0.0.0", port=8001, reload=True)
