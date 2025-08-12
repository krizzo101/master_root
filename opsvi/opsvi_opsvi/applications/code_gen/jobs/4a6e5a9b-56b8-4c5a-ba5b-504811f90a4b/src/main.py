"""FastAPI web application."""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Web API", version="1.0.0")


class Item(BaseModel):
    """Item model."""

    id: int | None = None
    name: str
    description: str | None = None


# In-memory storage (replace with database in production)
items: list[Item] = []
next_id = 1


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Web API is running"}


@app.get("/items", response_model=list[Item])
async def get_items():
    """Get all items."""
    return items


@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Create a new item."""
    global next_id
    item.id = next_id
    next_id += 1
    items.append(item)
    return item


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get item by ID."""
    for item in items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
