"""
GraphQL schema and resolvers using Ariadne for Python
"""
from ariadne import MutationType, QueryType, gql, make_executable_schema

from backend.api import create_project, create_task, list_projects, list_tasks

type_defs = gql(
    """
type Project { id: ID!, name: String!, description: String }
type Task { id: ID!, title: String!, status: String!, priority: Int, assignee_id: ID, due_date: String }

type Query {
  projects: [Project!]
  tasks(projectId: ID!): [Task!]
}
type Mutation {
  createProject(name: String!, description: String): Project!
  createTask(projectId: ID!, title: String!, description: String): Task!
}
"""
)

query = QueryType()
mutation = MutationType()


@query.field("projects")
def resolve_projects(*_):
    return list_projects()


@query.field("tasks")
def resolve_tasks(*_, projectId):
    return list_tasks(projectId)


@mutation.field("createProject")
def resolve_create_project(*_, name, description=None):
    return create_project({"name": name, "description": description})


@mutation.field("createTask")
def resolve_create_task(*_, projectId, title, description=None):
    return create_task(projectId, {"title": title, "description": description})


schema = make_executable_schema(type_defs, [query, mutation])
