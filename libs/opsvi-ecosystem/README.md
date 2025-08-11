# OPSVI Ecosystem

Complete autonomous, multi-agent AI/ML operations system library ecosystem.

## Installation

```bash
pip install opsvi-ecosystem
```

## Quick Start

```python
from opsvi_ecosystem import *

# Initialize core components
core = CoreConfig()
llm = OpenAIProvider()
http = HTTPXClient()
db = ArangoProvider()

# Your autonomous system here
```

## Libraries

- **Foundation**: Base components and utilities
- **Core**: Service registry, event bus, state management
- **LLM**: Language model providers (OpenAI, Anthropic, etc.)
- **HTTP**: HTTP client interfaces
- **Data**: Database providers (ArangoDB, PostgreSQL, etc.)
- **Auth**: Authentication providers
- **Memory**: Graph-based memory and lineage tracking
- **Orchestration**: Multi-agent orchestration
- **Communication**: Inter-agent communication
- **MCP**: Model Context Protocol integrations
- **API**: REST API framework
- **Workers**: Background task processing
- **Pipeline**: Data processing pipelines
- **Coordination**: Agent coordination systems
- **Shared**: Shared utilities and interfaces
- **Master**: Multi-agent master coordination
- **Auto-Forge**: Autonomous software factory
- **FS**: File system operations
- **RAG**: Retrieval-augmented generation
- **Gateway**: API gateway
- **Security**: Security and access control
- **Deploy**: Deployment utilities
- **Monitoring**: Observability and monitoring
- **Agents**: Agent management

## Development

```bash
git clone <repo>
cd libs
pip install -e opsvi-ecosystem
```
