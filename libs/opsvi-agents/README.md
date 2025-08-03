# OPSVI Agents Library

Agent framework library for OPSVI.

## Usage

```python
from opsvi.agents import CrewAdapter, GraphAdapter

# CrewAI integration
crew = CrewAdapter()
result = crew.create_crew(agents, tasks)

# LangGraph integration
graph = GraphAdapter()
result = graph.create_graph(nodes, edges)
```

## Development

This library provides adapters for popular agent frameworks like CrewAI and LangGraph.