"""
ElasticSearch document search integration and filter logic.
(Mocks: returns substring-matching from in-memory.)
"""
from typing import List
from .models import User, Document
import logging
from .crud import list_documents


async def search_documents(user: User, query: str) -> List[Document]:
    # Real: query Elasticsearch with security filter (user permitted docs)
    # Here: substring search on titles
    docs = await list_documents(user)
    result = [
        d
        for d in docs
        if query.lower() in d.title.lower() or query.lower() in d.body.lower()
    ]
    return result
