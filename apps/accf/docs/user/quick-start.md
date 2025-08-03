<!-- FILE_MAP_BEGIN 
<!--
{"file_metadata":{"title":"Quick Start Guide","description":"Step-by-step instructions to set up and start using the ACCF Research Agent, including prerequisites, installation, configuration, usage, troubleshooting, and next steps.","last_updated":"2025-07-31","type":"documentation"},"ai_instructions":"Analyze the document to identify major thematic sections for efficient navigation, focusing on installation, configuration, usage, troubleshooting, and support. Capture key code blocks, tables, and important instructions as navigation points. Ensure line numbers are precise and sections do not overlap. Group related subsections under broader headings to maintain clarity and usability.","sections":[{"name":"Introduction and Prerequisites","description":"Overview of the guide and the required software and tools needed before setup.","line_start":7,"line_end":17},{"name":"Step 1: Clone and Setup","description":"Instructions to clone the repository, create a virtual environment, and install dependencies.","line_start":18,"line_end":32},{"name":"Step 2: Configuration","description":"Guidance on copying the environment template and editing configuration files with required environment variables.","line_start":33,"line_end":45},{"name":"Step 3: Database Setup","description":"Options for setting up the Neo4j database locally using Docker or via Neo4j AuraDB cloud service.","line_start":46,"line_end":82},{"name":"Step 4: Start the Application","description":"Instructions to start the FastAPI server and verify the installation with health checks and API documentation access.","line_start":83,"line_end":99},{"name":"Step 5: Your First Research Query","description":"Examples of performing a research query using the API, Python client, and web interface.","line_start":100,"line_end":144},{"name":"Step 6: Monitor and Explore","description":"Commands to view research history, check agent status, and query the knowledge graph for monitoring and exploration.","line_start":145,"line_end":171},{"name":"Troubleshooting","description":"Common issues, solutions, and instructions for enabling debug logging and viewing application logs.","line_start":172,"line_end":193},{"name":"Next Steps and Support","description":"Links to further documentation, workflows, API references, and community support channels.","line_start":194,"line_end":210},{"name":"Conclusion","description":"Final congratulatory message encouraging users to start exploring the ACCF Research Agent.","line_start":211,"line_end":213}],"key_elements":[{"name":"Prerequisites List","description":"List of required software including Python 3.11+, Docker, Git, and Neo4j database.","line":12},{"name":"Clone and Setup Bash Commands","description":"Shell commands to clone the repository, create a virtual environment, and install dependencies.","line":19},{"name":"Configuration Bash Commands","description":"Commands to copy environment template and edit the .env file.","line":34},{"name":"Required Environment Variables","description":"Environment variables needed for Neo4j, OpenAI API, and application settings.","line":39},{"name":"Local Neo4j Docker Setup Commands","description":"Docker command to start Neo4j with required plugins and verify connection.","line":63},{"name":"Neo4j AuraDB Setup Instructions","description":"Steps to create a cloud database instance and configure connection details.","line":74},{"name":"Start FastAPI Server Command","description":"Command to launch the FastAPI server for the application.","line":87},{"name":"Health Check and API Documentation Commands","description":"Commands to verify server health and access API docs.","line":91},{"name":"Research Query via API Curl Command","description":"Curl command example to perform a research query using the API.","line":106},{"name":"Research Query Using Python Client","description":"Python code snippet demonstrating how to send a research query and print results.","line":116},{"name":"Web Interface Research Query Instructions","description":"Steps to perform a research query using the web interface.","line":132},{"name":"Research History Curl Command","description":"Curl command to retrieve recent research sessions.","line":151},{"name":"Agent Status Curl Command","description":"Curl command to check agent health and performance.","line":155},{"name":"Knowledge Graph Query Curl Command","description":"Curl command to query the knowledge graph using Cypher.","line":165},{"name":"Troubleshooting Table","description":"Table listing common issues and their solutions related to Neo4j, OpenAI API, ports, and imports.","line":175},{"name":"Debug Logging and Logs Viewing Commands","description":"Commands to enable debug logging and view application logs.","line":187},{"name":"Next Steps Documentation Links","description":"Links to configuration guide, research workflows, agent capabilities, and API reference documents.","line":195},{"name":"Support and Community Links","description":"Links to documentation site, GitHub issues, and GitHub discussions for help and community engagement.","line":202}]}
-->
<!-- FILE_MAP_END -->

# Quick Start Guide

Get the ACCF Research Agent up and running in **5 minutes** with this step-by-step guide.

## Prerequisites

- **Python 3.11+** installed
- **Docker** (optional, for containerized deployment)
- **Git** for cloning the repository
- **Neo4j Database** (local or cloud instance)

## 🚀 Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/accf/research-agent.git
cd accf-research-agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Step 2: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (see Configuration Guide for details)
nano .env
```

**Required Environment Variables:**

```env
# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# OpenAI API (for agent reasoning)
OPENAI_API_KEY=your-openai-api-key

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
```

## 🗄️ Step 3: Database Setup

### Option A: Local Neo4j (Docker)

```bash
# Start Neo4j with Docker
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  neo4j:5.15

# Verify connection
curl http://localhost:7474
```

### Option B: Neo4j AuraDB (Cloud)

1. Create account at [Neo4j AuraDB](https://neo4j.com/cloud/platform/aura-graph-database/)
2. Create new database instance
3. Copy connection details to `.env` file

## 🏃‍♂️ Step 4: Start the Application

```bash
# Start the FastAPI server
python -m uvicorn agent_api:app --reload --host 0.0.0.0 --port 8000
```

**Verify Installation:**

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## 🧪 Step 5: Your First Research Query

### Using the API

```bash
# Simple research query
curl -X POST "http://localhost:8000/api/v1/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the latest developments in quantum computing?",
    "max_results": 5,
    "include_sources": true
  }'
```

### Using Python Client

```python
import requests

# Research query
response = requests.post(
    "http://localhost:8000/api/v1/research",
    json={
        "query": "What are the latest developments in quantum computing?",
        "max_results": 5,
        "include_sources": True
    }
)

# Print results
results = response.json()
print(f"Research completed in {results['duration']} seconds")
print(f"Found {len(results['sources'])} sources")
print(f"Summary: {results['summary']}")
```

### Using the Web Interface

1. Open `http://localhost:8000` in your browser
2. Enter your research query
3. Click "Start Research"
4. Monitor progress in real-time
5. Review results and sources

## 📊 Step 6: Monitor and Explore

### View Research History

```bash
# Get recent research sessions
curl http://localhost:8000/api/v1/research/history
```

### Check Agent Status

```bash
# View agent health and performance
curl http://localhost:8000/api/v1/agents/status
```

### Explore Knowledge Graph

```bash
# Query the knowledge graph
curl -X POST "http://localhost:8000/api/v1/knowledge/query" \
  -H "Content-Type: application/json" \
  -d '{
    "cypher": "MATCH (n) RETURN n LIMIT 10"
  }'
```

## 🔧 Troubleshooting

### Common Issues

| Issue                       | Solution                                                             |
| --------------------------- | -------------------------------------------------------------------- |
| **Neo4j Connection Failed** | Check credentials and network connectivity                           |
| **OpenAI API Error**        | Verify API key and billing status                                    |
| **Port Already in Use**     | Change port: `uvicorn agent_api:app --port 8001`                     |
| **Import Errors**           | Ensure all dependencies installed: `pip install -r requirements.txt` |

### Logs and Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m uvicorn agent_api:app --reload

# View application logs
tail -f logs/app.log
```

## 🎯 Next Steps

1. **Read the [Configuration Guide](configuration.md)** for advanced settings
2. **Explore [Research Workflows](research-workflows.md)** for complex queries
3. **Check [Agent Capabilities](agent-capabilities.md)** for specialized features
4. **Review [API Reference](api-reference.md)** for programmatic access

## 📞 Need Help?

- **Documentation**: Browse this site for detailed guides
- **Issues**: Report problems on [GitHub Issues](https://github.com/accf/research-agent/issues)
- **Community**: Join discussions on [GitHub Discussions](https://github.com/accf/research-agent/discussions)

---

**🎉 Congratulations!** You've successfully set up the ACCF Research Agent. Start exploring the power of AI-driven research automation!