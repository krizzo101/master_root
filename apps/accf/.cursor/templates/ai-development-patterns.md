<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"AI Development Patterns","description":"Documentation detailing patterns for AI development including agent creation, memory integration, and tool usage with code examples.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify and map logical sections based on the main headings and their content. Extract key elements such as code blocks that illustrate usage patterns. Ensure line numbers are accurate and sections do not overlap. Provide clear, concise section names and descriptions to facilitate navigation and comprehension of AI development patterns.","sections":[{"name":"Introduction to AI Development Patterns","description":"Overview and introduction to the AI development patterns covered in the document.","line_start":7,"line_end":8},{"name":"LangGraph Agent Creation","description":"Instructions and example code demonstrating how to create a LangGraph agent using a chat model and tools.","line_start":9,"line_end":16},{"name":"Memory Integration","description":"Explanation and example code showing how to integrate memory checkpointing into an agent using InMemorySaver.","line_start":17,"line_end":24},{"name":"Tool Patterns","description":"Example and explanation of defining custom tools for agents, including a sample tool function with a description.","line_start":25,"line_end":32}],"key_elements":[{"name":"LangGraph Agent Creation Code Block","description":"Python code demonstrating initialization of a chat model and creation of a LangGraph React agent with tools and prompt.","line":10},{"name":"Memory Integration Code Block","description":"Python code showing how to create an InMemorySaver checkpoint and pass it to the agent for memory integration.","line":18},{"name":"Tool Patterns Code Block","description":"Python function defining a custom tool with a parameter and a descriptive docstring, illustrating tool creation for agents.","line":26}]}
-->
<!-- FILE_MAP_END -->

# AI Development Patterns

## LangGraph Agent Creation
```python
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

model = init_chat_model("claude-3-5-sonnet-latest")
agent = create_react_agent(model, tools, prompt)
```

## Memory Integration
```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
agent = create_react_agent(model, tools, checkpointer=checkpointer)
```

## Tool Patterns
```python
def my_tool(param: str) -> str:
    """Tool description for agent."""
    return f"Result: {param}"
```
