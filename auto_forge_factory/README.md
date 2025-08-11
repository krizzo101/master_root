# Auto-Forge Factory

**Production-ready autonomous software development factory that can accept requirements and deliver complete, tested, optimized software solutions without human intervention.**

[![CI/CD](https://github.com/your-org/auto-forge-factory/workflows/CI%2FCD/badge.svg)](https://github.com/your-org/auto-forge-factory/actions)
[![Coverage](https://codecov.io/gh/your-org/auto-forge-factory/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/auto-forge-factory)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

## 🚀 Features

### **Multi-Agent Orchestration**
- **10+ Specialized Agents**: Planner, Specifier, Architect, Coder, Tester, Performance Optimizer, Security Validator, Syntax Fixer, Critic, Meta Orchestrator
- **Intelligent Workflow Management**: Automated pipeline orchestration with dependency management
- **Real-time Progress Tracking**: WebSocket-based live updates and progress monitoring

### **End-to-End Development Pipeline**
- **Complete Software Lifecycle**: From requirements to production-ready code
- **Multi-Language Support**: Python, JavaScript, TypeScript, Go, Rust, Java, C#, C++, PHP, Ruby
- **Framework Integration**: FastAPI, Django, Flask, React, Vue, Angular, Express, Gin, Echo, Actix, Rocket, Spring, ASP.NET, Laravel, Rails
- **Cloud Deployment**: AWS, GCP, Azure, DigitalOcean, Heroku, Vercel, Netlify

### **Quality Assurance & Security**
- **Automated Testing**: Unit, integration, and end-to-end testing
- **Security Validation**: Automated security scanning and vulnerability assessment
- **Performance Optimization**: Built-in performance benchmarking and optimization
- **Code Quality**: Automated linting, formatting, and code review

### **Production-Ready Infrastructure**
- **Containerized Deployment**: Docker and Docker Compose support
- **Monitoring & Observability**: Prometheus, Grafana, structured logging
- **CI/CD Pipeline**: Automated testing, building, and deployment
- **Scalable Architecture**: Microservices-ready with load balancing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Auto-Forge Factory                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   FastAPI   │  │  WebSocket  │  │   Health    │        │
│  │    API      │  │   Updates   │  │   Checks    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Orchestrator Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Pipeline  │  │   Agent     │  │   Job       │        │
│  │ Orchestrator│  │  Registry   │  │  Manager    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Agent Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Planner   │  │ Specifier   │  │ Architect   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Coder    │  │   Tester    │  │ Performance │        │
│  └─────────────┘  └─────────────┘  │ Optimizer   │        │
│  ┌─────────────┐  ┌─────────────┐  └─────────────┘        │
│  │   Security  │  │   Syntax    │  ┌─────────────┐        │
│  │  Validator  │  │   Fixer     │  │   Critic    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Redis     │  │ PostgreSQL  │  │  Monitoring │        │
│  │   Cache     │  │  Database   │  │   Stack     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- OpenAI API key
- Anthropic API key (optional)

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/auto-forge-factory.git
cd auto-forge-factory
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=10
MAX_AGENTS_PER_JOB=8
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

This will start:
- Auto-Forge Factory API (port 8000)
- Redis cache (port 6379)
- PostgreSQL database (port 5432)
- Nginx reverse proxy (port 80)
- Prometheus monitoring (port 9090)
- Grafana dashboard (port 3000)

### 4. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Check factory status
curl http://localhost:8000/factory/status

# View API documentation
open http://localhost:8000/docs
```

## 📖 Usage

### Start a Development Job

```bash
curl -X POST http://localhost:8000/develop \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-commerce API",
    "description": "A RESTful API for an e-commerce platform",
    "requirements": [
      "User authentication and authorization",
      "Product catalog management",
      "Shopping cart functionality",
      "Order processing and payment integration",
      "Admin dashboard for inventory management"
    ],
    "target_language": "python",
    "target_framework": "fastapi",
    "target_architecture": "microservices",
    "cloud_provider": "aws",
    "priority": 8
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Development job started successfully. Job ID: 550e8400-e29b-41d4-a716-446655440000",
  "progress_url": "/status/550e8400-e29b-41d4-a716-446655440000",
  "websocket_url": "/ws/550e8400-e29b-41d4-a716-446655440000"
}
```

### Monitor Progress

```bash
# Check job status
curl http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000

# Get real-time updates via WebSocket
# Connect to ws://localhost:8000/ws/550e8400-e29b-41d4-a716-446655440000
```

### Get Results

```bash
# Get completed job artifacts
curl http://localhost:8000/artifacts/550e8400-e29b-41d4-a716-446655440000
```

### Python Client Example

```python
import asyncio
import httpx
from auto_forge_factory.models.schemas import DevelopmentRequest, Language, Framework

async def develop_software():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Create development request
        request = DevelopmentRequest(
            name="Task Management App",
            description="A collaborative task management application",
            requirements=[
                "User registration and login",
                "Project creation and management",
                "Task assignment and tracking",
                "Real-time notifications",
                "File upload and sharing"
            ],
            target_language=Language.PYTHON,
            target_framework=Framework.FASTAPI,
            target_architecture="monolith",
            priority=7
        )

        # Start development job
        response = await client.post("/develop", json=request.model_dump())
        job_data = response.json()
        job_id = job_data["job_id"]

        print(f"Started development job: {job_id}")

        # Monitor progress
        while True:
            status_response = await client.get(f"/status/{job_id}")
            status_data = status_response.json()

            print(f"Status: {status_data['status']} - {status_data['overall_progress_percent']:.1f}%")

            if status_data['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(5)

        # Get results
        if status_data['status'] == 'completed':
            result_response = await client.get(f"/artifacts/{job_id}")
            result_data = result_response.json()

            print(f"Development completed!")
            print(f"Quality Score: {result_data['quality_score']:.2f}")
            print(f"Security Score: {result_data['security_score']:.2f}")
            print(f"Performance Score: {result_data['performance_score']:.2f}")
            print(f"Total Cost: ${result_data['total_cost']:.2f}")

            for artifact in result_data['artifacts']:
                print(f"- {artifact['name']} ({artifact['type']})")

if __name__ == "__main__":
    asyncio.run(develop_software())
```

## 🔧 Configuration

### Agent Configuration

Each agent can be configured independently:

```python
from auto_forge_factory.models.schemas import AgentConfig, AgentType

# Configure planner agent
planner_config = AgentConfig(
    agent_type=AgentType.PLANNER,
    model="gpt-4",
    temperature=0.1,
    max_tokens=4000,
    timeout_seconds=300,
    retry_attempts=3,
    quality_threshold=0.8,
    enabled=True
)

# Configure coder agent for faster responses
coder_config = AgentConfig(
    agent_type=AgentType.CODER,
    model="gpt-4",
    temperature=0.2,
    max_tokens=8000,
    timeout_seconds=600,
    retry_attempts=2,
    quality_threshold=0.7,
    enabled=True
)
```

### Factory Configuration

```python
from auto_forge_factory.models.schemas import FactoryConfig

config = FactoryConfig(
    max_concurrent_jobs=10,
    max_agents_per_job=8,
    default_timeout_seconds=3600,
    agent_configs={
        AgentType.PLANNER: planner_config,
        AgentType.CODER: coder_config,
        # ... other agents
    },
    supported_languages=[Language.PYTHON, Language.JAVASCRIPT, Language.GO],
    supported_frameworks=[Framework.FASTAPI, Framework.REACT, Framework.GIN],
    supported_cloud_providers=[CloudProvider.AWS, CloudProvider.GCP]
)
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=auto_forge_factory --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/performance/ -v
```

### Test Coverage

The project maintains 95%+ test coverage across all components:

- **Unit Tests**: Individual agent and component testing
- **Integration Tests**: End-to-end pipeline testing
- **Performance Tests**: Load testing and benchmarking
- **Security Tests**: Vulnerability scanning and validation

## 📊 Monitoring

### Metrics Dashboard

Access Grafana dashboard at `http://localhost:3000` (admin/admin):

- **Job Metrics**: Success rate, completion time, cost analysis
- **Agent Performance**: Individual agent metrics and efficiency
- **System Health**: Resource utilization, error rates, response times
- **Quality Metrics**: Code quality scores, security scores, performance scores

### Prometheus Metrics

Key metrics available:

- `auto_forge_jobs_total`: Total jobs processed
- `auto_forge_jobs_duration_seconds`: Job completion time
- `auto_forge_agents_active`: Number of active agents
- `auto_forge_tokens_used_total`: Total tokens consumed
- `auto_forge_cost_total`: Total cost in USD

### Logging

Structured logging with correlation IDs:

```bash
# View logs
docker-compose logs -f auto-forge-factory

# Filter by job ID
docker-compose logs auto-forge-factory | grep "job_id=550e8400-e29b-41d4-a716-446655440000"
```

## 🚀 Deployment

### Production Deployment

1. **Kubernetes Deployment**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auto-forge-factory
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auto-forge-factory
  template:
    metadata:
      labels:
        app: auto-forge-factory
    spec:
      containers:
      - name: auto-forge-factory
        image: ghcr.io/your-org/auto-forge-factory:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: auto-forge-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

2. **AWS ECS Deployment**

```bash
# Deploy to ECS
aws ecs create-service \
  --cluster auto-forge-cluster \
  --service-name auto-forge-factory \
  --task-definition auto-forge-factory:1 \
  --desired-count 3
```

3. **Google Cloud Run**

```bash
# Deploy to Cloud Run
gcloud run deploy auto-forge-factory \
  --image gcr.io/your-project/auto-forge-factory \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Environment Variables

| Variable              | Description               | Default                                  |
| --------------------- | ------------------------- | ---------------------------------------- |
| `OPENAI_API_KEY`      | OpenAI API key            | Required                                 |
| `ANTHROPIC_API_KEY`   | Anthropic API key         | Optional                                 |
| `LOG_LEVEL`           | Logging level             | INFO                                     |
| `MAX_CONCURRENT_JOBS` | Maximum concurrent jobs   | 10                                       |
| `MAX_AGENTS_PER_JOB`  | Maximum agents per job    | 8                                        |
| `REDIS_URL`           | Redis connection URL      | redis://localhost:6379                   |
| `DATABASE_URL`        | PostgreSQL connection URL | postgresql://user:pass@localhost:5432/db |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/auto-forge-factory.git
cd auto-forge-factory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Run linting
ruff check auto_forge_factory/
black auto_forge_factory/
mypy auto_forge_factory/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- FastAPI for the web framework
- The open-source community for inspiration and tools

## 📞 Support

- **Documentation**: [https://auto-forge-factory.readthedocs.io](https://auto-forge-factory.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/your-org/auto-forge-factory/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/auto-forge-factory/discussions)
- **Email**: support@auto-forge-factory.com

---

**Auto-Forge Factory** - Transforming software development through autonomous AI agents.
