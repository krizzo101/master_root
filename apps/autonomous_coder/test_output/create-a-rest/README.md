# create-a-rest API

RESTful API built with FastAPI

## Tech Stack

- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

## Installation

```bash
pip install -r requirements.txt
```

## Development

```bash
uvicorn main:app --reload
```

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation

## Endpoints

- GET /items - List all items
- POST /items - Create new item
- GET /items/{id} - Get specific item
- DELETE /items/{id} - Delete item

## Testing

```bash
pytest
```
