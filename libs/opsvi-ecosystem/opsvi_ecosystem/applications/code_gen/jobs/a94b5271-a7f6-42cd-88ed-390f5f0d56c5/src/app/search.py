"""
ElasticSearch document search integration and filter logic.
(Mocks: returns substring-matching from in-memory.)
"""

from .crud import list_documents
from .models import Document, User


async def search_documents(user: User, query: str) -> list[Document]:
    # Real: query Elasticsearch with security filter (user permitted docs)
    # Here: substring search on titles
    docs = await list_documents(user)
    result = [
        d
        for d in docs
        if query.lower() in d.title.lower() or query.lower() in d.body.lower()
    ]
    return result
