# Knowledge Update: LangChain (Generated 2025-08-05)

## Current State (Last 12+ Months)

LangChain has evolved into a comprehensive framework for building AI applications with significant architectural improvements in 2025:

- **Modular Architecture**: Complete separation of core, community, and partner integrations
- **LCEL (LangChain Expression Language)**: Advanced chaining and composition system
- **Enhanced Agent Framework**: Multi-agent orchestration with specialized roles
- **Production-Ready Components**: Enterprise-grade observability and monitoring
- **Advanced RAG Capabilities**: Sophisticated retrieval and generation patterns
- **Cloud-Native Integration**: Seamless deployment across cloud platforms
- **Real-time Collaboration**: Multi-developer workflows and versioning
- **Performance Optimization**: Significant speed improvements and resource efficiency

## Best Practices & Patterns

### Modern LangChain Architecture (2025)
```python
# Core LangChain imports for shared libraries
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool

# Community integrations for shared resources
from langchain_community.vectorstores import Qdrant, Chroma, FAISS
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.text_splitter import RecursiveCharacterTextSplitter

# Partner integrations for production
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
```

### Shared Library Components Pattern
```python
# opsvi-core/shared/components.py
from typing import Dict, List, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from pydantic import BaseModel, Field

class SharedLLMConfig(BaseModel):
    """Configuration for shared LLM instances"""
    model_name: str = Field(default="gpt-4o-mini")
    temperature: float = Field(default=0.1)
    max_tokens: Optional[int] = Field(default=None)
    streaming: bool = Field(default=False)

class SharedEmbeddingConfig(BaseModel):
    """Configuration for shared embedding models"""
    model_name: str = Field(default="text-embedding-3-small")
    dimensions: int = Field(default=1536)
    batch_size: int = Field(default=100)

class SharedVectorStoreConfig(BaseModel):
    """Configuration for shared vector stores"""
    collection_name: str
    distance_metric: str = Field(default="cosine")
    index_params: Dict[str, Any] = Field(default_factory=dict)

class SharedComponentManager:
    """Manages shared LangChain components across libraries"""

    def __init__(self):
        self._llm_instances: Dict[str, BaseChatModel] = {}
        self._embedding_instances: Dict[str, Embeddings] = {}
        self._vectorstore_instances: Dict[str, VectorStore] = {}

    def get_llm(self, config: SharedLLMConfig) -> BaseChatModel:
        """Get or create shared LLM instance"""
        key = f"{config.model_name}_{config.temperature}_{config.max_tokens}"
        if key not in self._llm_instances:
            self._llm_instances[key] = ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                streaming=config.streaming
            )
        return self._llm_instances[key]

    def get_embeddings(self, config: SharedEmbeddingConfig) -> Embeddings:
        """Get or create shared embedding instance"""
        key = f"{config.model_name}_{config.dimensions}"
        if key not in self._embedding_instances:
            self._embedding_instances[key] = OpenAIEmbeddings(
                model=config.model_name,
                dimensions=config.dimensions
            )
        return self._embedding_instances[key]

    def get_vectorstore(self, config: SharedVectorStoreConfig, embeddings: Embeddings) -> VectorStore:
        """Get or create shared vector store instance"""
        key = f"{config.collection_name}_{config.distance_metric}"
        if key not in self._vectorstore_instances:
            self._vectorstore_instances[key] = Qdrant(
                collection_name=config.collection_name,
                embeddings=embeddings,
                distance_metric=config.distance_metric,
                **config.index_params
            )
        return self._vectorstore_instances[key]

# Global shared component manager
shared_components = SharedComponentManager()
```

### Advanced LCEL Patterns for Shared Libraries
```python
# opsvi-core/shared/chains.py
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from typing import Dict, Any, List

class SharedChainBuilder:
    """Builder for shared LangChain chains"""

    @staticmethod
    def create_qa_chain(llm: BaseChatModel, vectorstore: VectorStore) -> Runnable:
        """Create a reusable Q&A chain"""
        template = """Answer the question based on the following context:

        Context: {context}
        Question: {question}

        Answer:"""

        prompt = ChatPromptTemplate.from_template(template)

        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        retrieval_chain = (
            {"context": vectorstore.as_retriever() | RunnableLambda(format_docs), "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        return retrieval_chain

    @staticmethod
    def create_summarization_chain(llm: BaseChatModel) -> Runnable:
        """Create a reusable summarization chain"""
        template = """Summarize the following text in a concise way:

        Text: {text}

        Summary:"""

        prompt = ChatPromptTemplate.from_template(template)

        summarization_chain = (
            {"text": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        return summarization_chain

    @staticmethod
    def create_classification_chain(llm: BaseChatModel, categories: List[str]) -> Runnable:
        """Create a reusable classification chain"""
        template = """Classify the following text into one of these categories: {categories}

        Text: {text}

        Classification:"""

        prompt = ChatPromptTemplate.from_template(template)

        classification_chain = (
            {"text": RunnablePassthrough(), "categories": lambda _: ", ".join(categories)}
            | prompt
            | llm
            | StrOutputParser()
        )

        return classification_chain

# Usage in shared libraries
def create_shared_qa_system():
    """Create a shared Q&A system"""
    llm_config = SharedLLMConfig(model_name="gpt-4o-mini", temperature=0.1)
    embedding_config = SharedEmbeddingConfig(model_name="text-embedding-3-small")
    vectorstore_config = SharedVectorStoreConfig(collection_name="shared_docs")

    llm = shared_components.get_llm(llm_config)
    embeddings = shared_components.get_embeddings(embedding_config)
    vectorstore = shared_components.get_vectorstore(vectorstore_config, embeddings)

    return SharedChainBuilder.create_qa_chain(llm, vectorstore)
```

### Advanced Agent Patterns for Shared Libraries
```python
# opsvi-agents/shared/agent_factory.py
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict, Any

class SharedAgentFactory:
    """Factory for creating shared agent instances"""

    @staticmethod
    def create_research_agent(llm: BaseChatModel, tools: List) -> AgentExecutor:
        """Create a shared research agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a research assistant. Use the available tools to gather information and provide comprehensive answers."),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])

        agent = create_openai_tools_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    @staticmethod
    def create_analysis_agent(llm: BaseChatModel, tools: List) -> AgentExecutor:
        """Create a shared analysis agent"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an analysis assistant. Analyze data and provide insights using the available tools."),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])

        agent = create_openai_tools_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

    @staticmethod
    def create_qa_agent(llm: BaseChatModel, vectorstore: VectorStore) -> AgentExecutor:
        """Create a shared Q&A agent with retrieval"""
        @tool
        def search_documents(query: str) -> str:
            """Search documents for relevant information"""
            docs = vectorstore.similarity_search(query, k=3)
            return "\n\n".join([doc.page_content for doc in docs])

        tools = [search_documents]

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use the search tool to find relevant information before answering questions."),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])

        agent = create_openai_tools_agent(llm, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True)

# Shared tools for agents
@tool
def get_current_time() -> str:
    """Get the current date and time"""
    from datetime import datetime
    return datetime.now().isoformat()

@tool
def calculate_math(expression: str) -> str:
    """Calculate mathematical expressions"""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def search_web(query: str) -> str:
    """Search the web for current information"""
    # Implementation would use a web search API
    return f"Search results for: {query}"
```

### Advanced RAG Patterns for Shared Libraries
```python
# opsvi-rag/shared/rag_system.py
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict, Any, Optional

class SharedRAGSystem:
    """Shared RAG system for multiple applications"""

    def __init__(self, vectorstore: VectorStore, llm: BaseChatModel):
        self.vectorstore = vectorstore
        self.llm = llm
        self.retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )

    def create_rag_chain(self, custom_prompt: Optional[str] = None) -> Runnable:
        """Create a RAG chain with custom or default prompt"""
        if custom_prompt is None:
            custom_prompt = """Answer the question based on the following context:

            Context: {context}
            Question: {question}

            Answer:"""

        prompt = ChatPromptTemplate.from_template(custom_prompt)

        def format_docs(docs: List[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": self.retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain

    def create_multi_query_chain(self) -> Runnable:
        """Create a multi-query RAG chain for better retrieval"""
        from langchain.retrievers.multi_query import MultiQueryRetriever

        multi_retriever = MultiQueryRetriever.from_llm(
            retriever=self.retriever,
            llm=self.llm
        )

        prompt = ChatPromptTemplate.from_template("""
        Answer the question based on the following context:

        Context: {context}
        Question: {question}

        Answer:""")

        def format_docs(docs: List[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        multi_query_chain = (
            {"context": multi_retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return multi_query_chain

    def create_hybrid_search_chain(self, keyword_retriever: BaseRetriever) -> Runnable:
        """Create a hybrid search RAG chain"""
        from langchain.retrievers import EnsembleRetriever

        ensemble_retriever = EnsembleRetriever(
            retrievers=[self.retriever, keyword_retriever],
            weights=[0.7, 0.3]
        )

        prompt = ChatPromptTemplate.from_template("""
        Answer the question based on the following context:

        Context: {context}
        Question: {question}

        Answer:""")

        def format_docs(docs: List[Document]) -> str:
            return "\n\n".join(doc.page_content for doc in docs)

        hybrid_chain = (
            {"context": ensemble_retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return hybrid_chain

# Document processing utilities
class SharedDocumentProcessor:
    """Shared document processing utilities"""

    @staticmethod
    def create_text_splitter(chunk_size: int = 1000, chunk_overlap: int = 200):
        """Create a shared text splitter"""
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    @staticmethod
    def process_documents(documents: List[Document], splitter) -> List[Document]:
        """Process documents with the splitter"""
        return splitter.split_documents(documents)

    @staticmethod
    def add_metadata(documents: List[Document], metadata: Dict[str, Any]) -> List[Document]:
        """Add metadata to documents"""
        for doc in documents:
            doc.metadata.update(metadata)
        return documents
```

## Tools & Frameworks

### Core Components for Shared Libraries
- **langchain-core**: Base abstractions and interfaces
- **langchain-community**: Community-maintained integrations
- **langchain-openai**: OpenAI model integrations
- **langchain-anthropic**: Anthropic model integrations
- **langchain-google-vertexai**: Google Vertex AI integrations

### Advanced Integration Patterns
```python
# opsvi-core/shared/integrations.py
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from typing import Dict, Type, Any

class IntegrationRegistry:
    """Registry for managing different model integrations"""

    def __init__(self):
        self._llm_providers: Dict[str, Type[BaseChatModel]] = {}
        self._embedding_providers: Dict[str, Type[Embeddings]] = {}

    def register_llm_provider(self, name: str, provider_class: Type[BaseChatModel]):
        """Register an LLM provider"""
        self._llm_providers[name] = provider_class

    def register_embedding_provider(self, name: str, provider_class: Type[Embeddings]):
        """Register an embedding provider"""
        self._embedding_providers[name] = provider_class

    def create_llm(self, provider: str, **kwargs) -> BaseChatModel:
        """Create an LLM instance from a provider"""
        if provider not in self._llm_providers:
            raise ValueError(f"Unknown LLM provider: {provider}")
        return self._llm_providers[provider](**kwargs)

    def create_embeddings(self, provider: str, **kwargs) -> Embeddings:
        """Create an embeddings instance from a provider"""
        if provider not in self._embedding_providers:
            raise ValueError(f"Unknown embedding provider: {provider}")
        return self._embedding_providers[provider](**kwargs)

# Initialize registry with common providers
registry = IntegrationRegistry()

# Register OpenAI providers
registry.register_llm_provider("openai", ChatOpenAI)
registry.register_embedding_provider("openai", OpenAIEmbeddings)

# Register Anthropic providers
registry.register_llm_provider("anthropic", ChatAnthropic)

# Register Google providers
registry.register_llm_provider("vertexai", ChatVertexAI)
```

## Implementation Guidance

### Shared Library Structure
```
libs/
├── opsvi-core/
│   ├── src/opsvi_core/
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   ├── components.py      # Shared component manager
│   │   │   ├── chains.py          # Shared chain builder
│   │   │   ├── integrations.py    # Integration registry
│   │   │   └── config.py          # Configuration management
│   │   └── __init__.py
│   └── pyproject.toml
├── opsvi-llm/
│   ├── src/opsvi_llm/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── openai.py          # OpenAI integrations
│   │   │   ├── anthropic.py       # Anthropic integrations
│   │   │   └── vertexai.py        # Google Vertex AI integrations
│   │   └── __init__.py
│   └── pyproject.toml
├── opsvi-rag/
│   ├── src/opsvi_rag/
│   │   ├── systems/
│   │   │   ├── __init__.py
│   │   │   ├── basic_rag.py       # Basic RAG system
│   │   │   ├── multi_query_rag.py # Multi-query RAG
│   │   │   └── hybrid_rag.py      # Hybrid search RAG
│   │   └── __init__.py
│   └── pyproject.toml
└── opsvi-agents/
    ├── src/opsvi_agents/
    │   ├── agents/
    │   │   ├── __init__.py
    │   │   ├── research_agent.py  # Research agent
    │   │   ├── analysis_agent.py  # Analysis agent
    │   │   └── qa_agent.py        # Q&A agent
    │   └── __init__.py
    └── pyproject.toml
```

### Configuration Management
```python
# opsvi-core/shared/config.py
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import os

class LangChainConfig(BaseModel):
    """Configuration for LangChain components"""

    # LLM Configuration
    default_llm_provider: str = Field(default="openai")
    default_llm_model: str = Field(default="gpt-4o-mini")
    default_temperature: float = Field(default=0.1)
    default_max_tokens: Optional[int] = Field(default=None)

    # Embedding Configuration
    default_embedding_provider: str = Field(default="openai")
    default_embedding_model: str = Field(default="text-embedding-3-small")
    default_embedding_dimensions: int = Field(default=1536)

    # Vector Store Configuration
    default_vectorstore_provider: str = Field(default="qdrant")
    default_collection_name: str = Field(default="shared_docs")

    # RAG Configuration
    default_chunk_size: int = Field(default=1000)
    default_chunk_overlap: int = Field(default=200)
    default_retrieval_k: int = Field(default=5)

    # Agent Configuration
    default_agent_verbose: bool = Field(default=True)
    default_agent_max_iterations: int = Field(default=10)

    @classmethod
    def from_env(cls) -> "LangChainConfig":
        """Create configuration from environment variables"""
        return cls(
            default_llm_provider=os.getenv("LANGCHAIN_LLM_PROVIDER", "openai"),
            default_llm_model=os.getenv("LANGCHAIN_LLM_MODEL", "gpt-4o-mini"),
            default_temperature=float(os.getenv("LANGCHAIN_TEMPERATURE", "0.1")),
            default_max_tokens=int(os.getenv("LANGCHAIN_MAX_TOKENS", "0")) if os.getenv("LANGCHAIN_MAX_TOKENS") else None,
            default_embedding_provider=os.getenv("LANGCHAIN_EMBEDDING_PROVIDER", "openai"),
            default_embedding_model=os.getenv("LANGCHAIN_EMBEDDING_MODEL", "text-embedding-3-small"),
            default_embedding_dimensions=int(os.getenv("LANGCHAIN_EMBEDDING_DIMENSIONS", "1536")),
            default_vectorstore_provider=os.getenv("LANGCHAIN_VECTORSTORE_PROVIDER", "qdrant"),
            default_collection_name=os.getenv("LANGCHAIN_COLLECTION_NAME", "shared_docs"),
            default_chunk_size=int(os.getenv("LANGCHAIN_CHUNK_SIZE", "1000")),
            default_chunk_overlap=int(os.getenv("LANGCHAIN_CHUNK_OVERLAP", "200")),
            default_retrieval_k=int(os.getenv("LANGCHAIN_RETRIEVAL_K", "5")),
            default_agent_verbose=os.getenv("LANGCHAIN_AGENT_VERBOSE", "true").lower() == "true",
            default_agent_max_iterations=int(os.getenv("LANGCHAIN_AGENT_MAX_ITERATIONS", "10"))
        )

# Global configuration
config = LangChainConfig.from_env()
```

### Advanced Usage Examples
```python
# Example: Using shared components in an application
from opsvi_core.shared import shared_components, config
from opsvi_rag.shared import SharedRAGSystem
from opsvi_agents.shared import SharedAgentFactory

# Create shared LLM and embeddings
llm_config = SharedLLMConfig(
    model_name=config.default_llm_model,
    temperature=config.default_temperature,
    max_tokens=config.default_max_tokens
)
llm = shared_components.get_llm(llm_config)

embedding_config = SharedEmbeddingConfig(
    model_name=config.default_embedding_model,
    dimensions=config.default_embedding_dimensions
)
embeddings = shared_components.get_embeddings(embedding_config)

# Create shared vector store
vectorstore_config = SharedVectorStoreConfig(
    collection_name=config.default_collection_name
)
vectorstore = shared_components.get_vectorstore(vectorstore_config, embeddings)

# Create RAG system
rag_system = SharedRAGSystem(vectorstore, llm)
rag_chain = rag_system.create_rag_chain()

# Create agent
agent = SharedAgentFactory.create_qa_agent(llm, vectorstore)

# Use the components
response = rag_chain.invoke("What is LangChain?")
agent_response = agent.invoke({"input": "Explain RAG systems"})
```

## Limitations & Considerations

### Current Limitations
- **Memory Usage**: Large models can consume significant memory
- **API Rate Limits**: External API providers have rate limits
- **Cost Management**: Need careful monitoring of API usage costs
- **Latency**: External API calls can introduce latency
- **Dependency Management**: Complex dependency tree for integrations

### Best Practices for Shared Libraries
- **Component Reuse**: Use shared component manager for efficiency
- **Configuration Management**: Centralize configuration for consistency
- **Error Handling**: Implement robust error handling for API failures
- **Caching**: Cache expensive operations like embeddings
- **Monitoring**: Monitor usage and performance metrics
- **Testing**: Comprehensive testing of shared components
- **Documentation**: Clear documentation for shared components
- **Versioning**: Proper versioning of shared components

### Migration Considerations
- **LCEL Migration**: Migrate from legacy chains to LCEL
- **Component Separation**: Separate core, community, and partner integrations
- **Configuration Updates**: Update configuration for new providers
- **Testing Strategy**: Update tests for new component structure
- **Documentation Updates**: Update documentation for new patterns

## Recent Updates (2024-2025)

### Performance Improvements
- **LCEL Optimization**: Significant performance improvements in LCEL chains
- **Caching Enhancements**: Better caching for embeddings and model responses
- **Memory Optimization**: Reduced memory usage for large models
- **Parallel Processing**: Improved parallel processing capabilities
- **Streaming Support**: Enhanced streaming for real-time responses

### New Features for Shared Libraries
- **Component Registry**: Centralized component management
- **Advanced LCEL**: More sophisticated chaining patterns
- **Multi-Agent Orchestration**: Better multi-agent coordination
- **Enhanced RAG**: Advanced retrieval and generation patterns
- **Cloud Integration**: Better cloud platform integration
- **Observability**: Enhanced monitoring and tracing
- **Security**: Improved security features and best practices

### Breaking Changes
- **LCEL Migration**: Legacy chains deprecated in favor of LCEL
- **Component Separation**: Core, community, and partner packages separated
- **API Changes**: Some API changes for better consistency
- **Configuration Updates**: New configuration patterns required
- **Import Changes**: Updated import paths for new structure

### Ecosystem Integration
- **LangSmith Integration**: Enhanced LangSmith integration for monitoring
- **LangGraph Integration**: Better integration with LangGraph for workflows
- **Cloud Platforms**: Improved integration with AWS, GCP, and Azure
- **Development Tools**: Better integration with development tools
- **Testing Framework**: Enhanced testing framework and utilities