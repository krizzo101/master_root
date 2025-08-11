"""
Ariadne-based GraphQL endpoint
"""
from ariadne.asgi import GraphQL
from backend.graphql_schema import schema

graphql_app = GraphQL(schema, debug=True)
