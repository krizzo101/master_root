import asyncio

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def hello_world():
    await asyncio.sleep(0.1)  # Simulate async operation
    return {"message": "Hello World!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
