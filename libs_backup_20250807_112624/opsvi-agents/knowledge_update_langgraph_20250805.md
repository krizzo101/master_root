# Knowledge Update: LangGraph (Generated 2025-08-05)

## Current State (Last 12+ Months)

LangGraph has evolved into a comprehensive framework for building stateful, multi-actor AI applications with significant architectural improvements in 2025:

- **Graph-Based Architecture**: Nodes represent agents/states, edges represent transitions
- **Multi-Agent Orchestration**: Support for complex agent collaboration patterns
- **State Management**: Durable execution with comprehensive memory and checkpointing
- **Production-Ready Deployment**: Cloud-native integration with enterprise features
- **Advanced Workflow Patterns**: Hierarchical teams, supervisor agents, and collaborative workflows
- **Real-time Streaming**: Enhanced streaming support for interactive applications
- **Human-in-the-Loop**: Built-in support for human feedback and intervention
- **Memory Systems**: Persistent state management across sessions and threads

## Best Practices & Patterns

### Modern LangGraph Architecture (2025)
```python
# Core LangGraph imports for shared libraries
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from typing import Annotated, Dict, List, Any, Optional

# State management for shared components
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# Message handling for shared libraries
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
```

### Shared Library Components Pattern
```python
# opsvi-core/shared/langgraph_components.py
from typing import Dict, List, Any, Optional, Type
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class SharedGraphState(BaseModel):
    """Shared state for LangGraph workflows"""
    messages: List[BaseMessage] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)

class SharedGraphBuilder:
    """Builder for shared LangGraph workflows"""

    def __init__(self):
        self.state_schema = SharedGraphState
        self.nodes: Dict[str, Any] = {}
        self.edges: List[tuple] = []
        self.conditional_edges: List[tuple] = []

    def add_agent_node(self, name: str, agent: BaseChatModel, tools: List[BaseTool] = None):
        """Add an agent node to the graph"""
        if tools:
            agent_with_tools = agent.bind_tools(tools)
            tool_node = ToolNode(tools)

            def agent_function(state: SharedGraphState):
                messages = state.messages
                response = agent_with_tools.invoke(messages)
                return {"messages": [response]}

            self.nodes[name] = agent_function
            self.nodes[f"{name}_tools"] = tool_node
        else:
            def agent_function(state: SharedGraphState):
                messages = state.messages
                response = agent.invoke(messages)
                return {"messages": [response]}

            self.nodes[name] = agent_function

    def add_conditional_edge(self, from_node: str, condition_func, to_nodes: List[str]):
        """Add a conditional edge to the graph"""
        self.conditional_edges.append((from_node, condition_func, to_nodes))

    def add_edge(self, from_node: str, to_node: str):
        """Add a direct edge to the graph"""
        self.edges.append((from_node, to_node))

    def build(self) -> StateGraph:
        """Build the StateGraph with all nodes and edges"""
        graph = StateGraph(self.state_schema)

        # Add all nodes
        for name, node in self.nodes.items():
            graph.add_node(name, node)

        # Add conditional edges
        for from_node, condition_func, to_nodes in self.conditional_edges:
            graph.add_conditional_edges(from_node, condition_func, to_nodes)

        # Add direct edges
        for from_node, to_node in self.edges:
            graph.add_edge(from_node, to_node)

        return graph.compile()

# Global shared graph builder
shared_graph_builder = SharedGraphBuilder()
```

### Advanced Multi-Agent Patterns for Shared Libraries
```python
# opsvi-agents/shared/multi_agent_patterns.py
from typing import Annotated, Dict, List, Any
from langgraph.prebuilt import InjectedState, create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool

class SharedMultiAgentPatterns:
    """Shared patterns for multi-agent LangGraph workflows"""

    @staticmethod
    def create_supervisor_agent(llm: BaseChatModel, sub_agents: List[callable]):
        """Create a supervisor agent that can delegate to sub-agents"""

        # Create sub-agent tools
        @tool
        def agent_1(state: Annotated[Dict, InjectedState]) -> str:
            """First specialized agent"""
            # Access state and perform agent-specific logic
            messages = state.get("messages", [])
            # Agent-specific processing
            return "Agent 1 response"

        @tool
        def agent_2(state: Annotated[Dict, InjectedState]) -> str:
            """Second specialized agent"""
            messages = state.get("messages", [])
            # Agent-specific processing
            return "Agent 2 response"

        # Create supervisor with tool-calling
        supervisor = create_react_agent(llm, [agent_1, agent_2])
        return supervisor

    @staticmethod
    def create_hierarchical_team(llm: BaseChatModel, team_config: Dict[str, Any]):
        """Create a hierarchical team of agents"""

        # Define team structure
        team_agents = {}

        for agent_name, config in team_config.items():
            @tool
            def team_agent(state: Annotated[Dict, InjectedState], agent_config=config) -> str:
                """Team agent with specific role"""
                role = agent_config.get("role", "General Agent")
                goal = agent_config.get("goal", "Complete assigned tasks")

                # Agent-specific processing based on role and goal
                messages = state.get("messages", [])
                # Process based on role and goal
                return f"{role} response: {goal}"

            team_agents[agent_name] = team_agent

        # Create supervisor for the team
        supervisor = create_react_agent(llm, list(team_agents.values()))
        return supervisor

    @staticmethod
    def create_collaborative_workflow(agents: List[BaseChatModel], shared_state: Dict[str, Any]):
        """Create a collaborative workflow where agents share state"""

        def collaborative_node(state: SharedGraphState):
            """Node where agents collaborate on shared state"""
            messages = state.messages
            context = state.context

            # Collaborative processing
            responses = []
            for agent in agents:
                response = agent.invoke(messages)
                responses.append(response)

            # Combine responses
            combined_response = self._combine_responses(responses)

            return {
                "messages": [combined_response],
                "context": context,
                "agent_outputs": {"collaborative": responses}
            }

        return collaborative_node

    @staticmethod
    def _combine_responses(responses: List[Any]) -> Any:
        """Combine multiple agent responses"""
        # Implementation for combining responses
        return responses[0] if responses else None
```

### Advanced Workflow Patterns for Shared Libraries
```python
# opsvi-core/shared/workflow_patterns.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from typing import List, Dict, Any, Optional

class SharedWorkflowPatterns:
    """Shared workflow patterns for LangGraph applications"""

    @staticmethod
    def create_sequential_workflow(nodes: List[Dict[str, Any]]) -> StateGraph:
        """Create a sequential workflow with multiple nodes"""
        graph = StateGraph(SharedGraphState)

        # Add nodes
        for i, node_config in enumerate(nodes):
            node_name = node_config["name"]
            node_function = node_config["function"]
            graph.add_node(node_name, node_function)

            # Connect nodes sequentially
            if i == 0:
                graph.add_edge(START, node_name)
            else:
                prev_node = nodes[i-1]["name"]
                graph.add_edge(prev_node, node_name)

            # Last node connects to END
            if i == len(nodes) - 1:
                graph.add_edge(node_name, END)

        return graph.compile()

    @staticmethod
    def create_parallel_workflow(nodes: List[Dict[str, Any]], combiner_function) -> StateGraph:
        """Create a parallel workflow where nodes execute concurrently"""
        graph = StateGraph(SharedGraphState)

        # Add parallel nodes
        for node_config in nodes:
            node_name = node_config["name"]
            node_function = node_config["function"]
            graph.add_node(node_name, node_function)
            graph.add_edge(START, node_name)

        # Add combiner node
        graph.add_node("combiner", combiner_function)
        for node_config in nodes:
            graph.add_edge(node_config["name"], "combiner")

        graph.add_edge("combiner", END)

        return graph.compile()

    @staticmethod
    def create_conditional_workflow(condition_function, branches: Dict[str, Any]) -> StateGraph:
        """Create a conditional workflow with multiple branches"""
        graph = StateGraph(SharedGraphState)

        # Add branch nodes
        for branch_name, branch_config in branches.items():
            node_function = branch_config["function"]
            graph.add_node(branch_name, node_function)
            graph.add_edge(branch_name, END)

        # Add conditional routing
        graph.add_conditional_edges(START, condition_function, list(branches.keys()))

        return graph.compile()

    @staticmethod
    def create_loop_workflow(loop_condition, loop_body) -> StateGraph:
        """Create a workflow with a loop"""
        graph = StateGraph(SharedGraphState)

        # Add loop body
        graph.add_node("loop_body", loop_body)

        # Add conditional routing for loop
        graph.add_conditional_edges("loop_body", loop_condition, ["loop_body", END])
        graph.add_edge(START, "loop_body")

        return graph.compile()

# Usage examples
def create_qa_workflow(llm: BaseChatModel, vectorstore):
    """Create a Q&A workflow using shared patterns"""

    def retrieve_docs(state: SharedGraphState):
        """Retrieve relevant documents"""
        messages = state.messages
        query = messages[-1].content if messages else ""
        docs = vectorstore.similarity_search(query, k=3)
        return {"context": {"docs": docs}}

    def generate_answer(state: SharedGraphState):
        """Generate answer based on retrieved documents"""
        messages = state.messages
        docs = state.context.get("docs", [])

        # Format documents for LLM
        context = "\n\n".join([doc.page_content for doc in docs])

        # Create prompt with context
        prompt = f"Context: {context}\n\nQuestion: {messages[-1].content}\n\nAnswer:"
        response = llm.invoke(prompt)

        return {"messages": [response]}

    nodes = [
        {"name": "retrieve", "function": retrieve_docs},
        {"name": "generate", "function": generate_answer}
    ]

    return SharedWorkflowPatterns.create_sequential_workflow(nodes)
```

### Advanced State Management for Shared Libraries
```python
# opsvi-core/shared/state_management.py
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.redis import RedisSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import Dict, Any, Optional
import json

class SharedStateManager:
    """Manages state for shared LangGraph applications"""

    def __init__(self, checkpoint_type: str = "memory", **kwargs):
        self.checkpoint_type = checkpoint_type
        self.checkpointer = self._create_checkpointer(**kwargs)

    def _create_checkpointer(self, **kwargs):
        """Create appropriate checkpointer based on type"""
        if self.checkpoint_type == "memory":
            return InMemorySaver()
        elif self.checkpoint_type == "redis":
            return RedisSaver(**kwargs)
        elif self.checkpoint_type == "sqlite":
            return SqliteSaver(**kwargs)
        else:
            raise ValueError(f"Unsupported checkpoint type: {self.checkpoint_type}")

    def save_state(self, thread_id: str, state: Dict[str, Any]):
        """Save state for a thread"""
        return self.checkpointer.put({"configurable": {"thread_id": thread_id}}, state)

    def load_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Load state for a thread"""
        return self.checkpointer.get({"configurable": {"thread_id": thread_id}})

    def list_threads(self) -> List[str]:
        """List all thread IDs"""
        return self.checkpointer.list_keys()

class SharedMemoryManager:
    """Manages memory for shared LangGraph applications"""

    def __init__(self):
        self.memory_store: Dict[str, List[BaseMessage]] = {}

    def add_memory(self, thread_id: str, messages: List[BaseMessage]):
        """Add messages to memory"""
        if thread_id not in self.memory_store:
            self.memory_store[thread_id] = []
        self.memory_store[thread_id].extend(messages)

    def get_memory(self, thread_id: str) -> List[BaseMessage]:
        """Get memory for a thread"""
        return self.memory_store.get(thread_id, [])

    def clear_memory(self, thread_id: str):
        """Clear memory for a thread"""
        if thread_id in self.memory_store:
            del self.memory_store[thread_id]

    def update_memory(self, thread_id: str, messages: List[BaseMessage]):
        """Update memory for a thread"""
        self.memory_store[thread_id] = messages

# Global state and memory managers
shared_state_manager = SharedStateManager()
shared_memory_manager = SharedMemoryManager()
```

## Tools & Frameworks

### Core Components for Shared Libraries
- **langgraph**: Core framework for building stateful, multi-actor applications
- **langgraph-sdk**: SDK for cloud deployment and management
- **langgraph-checkpoint**: Checkpointing and state persistence
- **langgraph-prebuilt**: Prebuilt components and patterns
- **langgraph-swarm**: Multi-agent collaboration patterns

### Advanced Integration Patterns
```python
# opsvi-core/shared/integrations.py
from langgraph.graph import StateGraph
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from typing import Dict, Type, Any

class LangGraphIntegrationRegistry:
    """Registry for managing LangGraph integrations"""

    def __init__(self):
        self._llm_providers: Dict[str, Type[BaseChatModel]] = {}
        self._tool_providers: Dict[str, Type[BaseTool]] = {}
        self._workflow_patterns: Dict[str, callable] = {}

    def register_llm_provider(self, name: str, provider_class: Type[BaseChatModel]):
        """Register an LLM provider"""
        self._llm_providers[name] = provider_class

    def register_tool_provider(self, name: str, provider_class: Type[BaseTool]):
        """Register a tool provider"""
        self._tool_providers[name] = provider_class

    def register_workflow_pattern(self, name: str, pattern_function: callable):
        """Register a workflow pattern"""
        self._workflow_patterns[name] = pattern_function

    def create_llm(self, provider: str, **kwargs) -> BaseChatModel:
        """Create an LLM instance from a provider"""
        if provider not in self._llm_providers:
            raise ValueError(f"Unknown LLM provider: {provider}")
        return self._llm_providers[provider](**kwargs)

    def create_tool(self, provider: str, **kwargs) -> BaseTool:
        """Create a tool instance from a provider"""
        if provider not in self._tool_providers:
            raise ValueError(f"Unknown tool provider: {provider}")
        return self._tool_providers[provider](**kwargs)

    def create_workflow(self, pattern: str, **kwargs) -> StateGraph:
        """Create a workflow using a registered pattern"""
        if pattern not in self._workflow_patterns:
            raise ValueError(f"Unknown workflow pattern: {pattern}")
        return self._workflow_patterns[pattern](**kwargs)

# Initialize registry with common providers
registry = LangGraphIntegrationRegistry()

# Register common LLM providers
registry.register_llm_provider("openai", ChatOpenAI)
registry.register_llm_provider("anthropic", ChatAnthropic)

# Register common workflow patterns
registry.register_workflow_pattern("sequential", SharedWorkflowPatterns.create_sequential_workflow)
registry.register_workflow_pattern("parallel", SharedWorkflowPatterns.create_parallel_workflow)
registry.register_workflow_pattern("conditional", SharedWorkflowPatterns.create_conditional_workflow)
```

## Implementation Guidance

### Shared Library Structure
```
libs/
├── opsvi-core/
│   ├── src/opsvi_core/
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   ├── langgraph_components.py    # Shared graph components
│   │   │   ├── workflow_patterns.py       # Workflow patterns
│   │   │   ├── state_management.py        # State management
│   │   │   ├── integrations.py            # Integration registry
│   │   │   └── config.py                  # Configuration management
│   │   └── __init__.py
│   └── pyproject.toml
├── opsvi-agents/
│   ├── src/opsvi_agents/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── supervisor_agent.py        # Supervisor agent
│   │   │   ├── hierarchical_team.py       # Hierarchical team
│   │   │   └── collaborative_agent.py     # Collaborative agent
│   │   └── __init__.py
│   └── pyproject.toml
└── opsvi-workflows/
    ├── src/opsvi_workflows/
    │   ├── workflows/
    │   │   ├── __init__.py
    │   │   ├── qa_workflow.py             # Q&A workflow
    │   │   ├── research_workflow.py       # Research workflow
    │   │   └── analysis_workflow.py       # Analysis workflow
    │   └── __init__.py
    └── pyproject.toml
```

### Configuration Management
```python
# opsvi-core/shared/config.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import os

class LangGraphConfig(BaseModel):
    """Configuration for LangGraph components"""

    # Graph Configuration
    default_state_schema: str = Field(default="SharedGraphState")
    default_checkpoint_type: str = Field(default="memory")

    # Agent Configuration
    default_agent_verbose: bool = Field(default=True)
    default_agent_max_iterations: int = Field(default=25)
    default_agent_max_execution_time: Optional[int] = Field(default=None)

    # Workflow Configuration
    default_workflow_process: str = Field(default="sequential")
    default_workflow_verbose: bool = Field(default=True)

    # State Management Configuration
    default_memory_enabled: bool = Field(default=True)
    default_checkpoint_enabled: bool = Field(default=True)

    # Integration Configuration
    default_llm_provider: str = Field(default="openai")
    default_tool_provider: str = Field(default="langchain")

    @classmethod
    def from_env(cls) -> "LangGraphConfig":
        """Create configuration from environment variables"""
        return cls(
            default_state_schema=os.getenv("LANGGRAPH_STATE_SCHEMA", "SharedGraphState"),
            default_checkpoint_type=os.getenv("LANGGRAPH_CHECKPOINT_TYPE", "memory"),
            default_agent_verbose=os.getenv("LANGGRAPH_AGENT_VERBOSE", "true").lower() == "true",
            default_agent_max_iterations=int(os.getenv("LANGGRAPH_AGENT_MAX_ITERATIONS", "25")),
            default_agent_max_execution_time=int(os.getenv("LANGGRAPH_AGENT_MAX_EXECUTION_TIME", "0")) if os.getenv("LANGGRAPH_AGENT_MAX_EXECUTION_TIME") else None,
            default_workflow_process=os.getenv("LANGGRAPH_WORKFLOW_PROCESS", "sequential"),
            default_workflow_verbose=os.getenv("LANGGRAPH_WORKFLOW_VERBOSE", "true").lower() == "true",
            default_memory_enabled=os.getenv("LANGGRAPH_MEMORY_ENABLED", "true").lower() == "true",
            default_checkpoint_enabled=os.getenv("LANGGRAPH_CHECKPOINT_ENABLED", "true").lower() == "true",
            default_llm_provider=os.getenv("LANGGRAPH_LLM_PROVIDER", "openai"),
            default_tool_provider=os.getenv("LANGGRAPH_TOOL_PROVIDER", "langchain")
        )

# Global configuration
config = LangGraphConfig.from_env()
```

### Advanced Usage Examples
```python
# Example: Using shared components in an application
from opsvi_core.shared import shared_graph_builder, config
from opsvi_agents.shared import SharedMultiAgentPatterns
from opsvi_workflows.shared import SharedWorkflowPatterns

# Create a multi-agent workflow
def create_research_workflow(llm: BaseChatModel, tools: List[BaseTool]):
    """Create a research workflow using shared components"""

    # Create supervisor agent
    supervisor = SharedMultiAgentPatterns.create_supervisor_agent(llm, [])

    # Create workflow nodes
    def research_node(state: SharedGraphState):
        """Research node"""
        messages = state.messages
        # Research logic
        return {"messages": [AIMessage(content="Research completed")]}

    def analysis_node(state: SharedGraphState):
        """Analysis node"""
        messages = state.messages
        # Analysis logic
        return {"messages": [AIMessage(content="Analysis completed")]}

    # Build graph
    shared_graph_builder.add_agent_node("supervisor", supervisor)
    shared_graph_builder.add_node("research", research_node)
    shared_graph_builder.add_node("analysis", analysis_node)

    # Add edges
    shared_graph_builder.add_edge("supervisor", "research")
    shared_graph_builder.add_edge("research", "analysis")
    shared_graph_builder.add_edge("analysis", END)

    return shared_graph_builder.build()

# Create and run workflow
workflow = create_research_workflow(llm, tools)
result = workflow.invoke({
    "messages": [HumanMessage(content="Research AI trends")]
})
```

## Limitations & Considerations

### Current Limitations
- **Memory Usage**: Large state objects can consume significant memory
- **Complexity**: Multi-agent workflows can become complex to debug
- **State Persistence**: Requires careful management of state across sessions
- **Performance**: Graph compilation can be slow for complex workflows
- **Debugging**: Debugging multi-agent workflows can be challenging

### Best Practices for Shared Libraries
- **State Design**: Design state schemas carefully for shared components
- **Error Handling**: Implement robust error handling for agent failures
- **Memory Management**: Monitor memory usage in long-running workflows
- **Testing**: Comprehensive testing of individual nodes and workflows
- **Documentation**: Clear documentation for shared components
- **Versioning**: Proper versioning of shared components
- **Monitoring**: Monitor workflow performance and agent behavior

### Migration Considerations
- **State Schema Migration**: Plan for state schema changes
- **Agent Migration**: Migrate agents to new patterns gradually
- **Workflow Migration**: Update workflows to use new patterns
- **Testing Strategy**: Update tests for new component structure
- **Documentation Updates**: Update documentation for new patterns

## Recent Updates (2024-2025)

### Performance Improvements
- **Graph Compilation**: Faster graph compilation for complex workflows
- **State Management**: Improved state persistence and retrieval
- **Memory Optimization**: Better memory management for large state objects
- **Parallel Processing**: Enhanced parallel processing capabilities
- **Streaming Support**: Improved streaming for real-time applications

### New Features for Shared Libraries
- **Multi-Agent Orchestration**: Enhanced multi-agent collaboration patterns
- **Hierarchical Teams**: Support for hierarchical agent teams
- **Supervisor Agents**: Advanced supervisor agent patterns
- **Collaborative Workflows**: Better support for agent collaboration
- **State Persistence**: Enhanced state persistence across sessions
- **Memory Systems**: Advanced memory management systems
- **Human-in-the-Loop**: Improved human-in-the-loop capabilities

### Breaking Changes
- **State Schema Changes**: Updated state schema patterns
- **Agent Patterns**: New agent creation patterns
- **Workflow Patterns**: Updated workflow creation patterns
- **API Changes**: Some API changes for better consistency
- **Configuration Updates**: New configuration patterns required

### Ecosystem Integration
- **LangSmith Integration**: Enhanced LangSmith integration for monitoring
- **LangChain Integration**: Better integration with LangChain ecosystem
- **Cloud Platforms**: Improved integration with AWS, GCP, and Azure
- **Development Tools**: Better integration with development tools
- **Testing Framework**: Enhanced testing framework and utilities