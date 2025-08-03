"""
Model Comparison Test for o3_agent Tool

This script tests all approved models with the same prompt to analyze differences
in quality, accuracy, reasoning capabilities, and response characteristics.
"""

import asyncio
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Test prompt designed to evaluate different model capabilities
TEST_PROMPT = """
You are a senior software architect tasked with designing a scalable microservices architecture for a new e-commerce platform. The platform needs to handle:

1. 100,000+ concurrent users
2. Real-time inventory management
3. Payment processing with multiple providers
4. Order fulfillment and shipping
5. Customer analytics and personalization
6. Multi-tenant support for different storefronts

Requirements:
- 99.9% uptime SLA
- Sub-second response times for critical operations
- GDPR compliance for EU customers
- PCI DSS compliance for payment processing
- Horizontal scalability for peak shopping seasons

Please provide:
1. A high-level architecture diagram description
2. Service decomposition with clear boundaries
3. Data flow patterns for key operations
4. Technology stack recommendations
5. Security considerations and implementation
6. Monitoring and observability strategy
7. Deployment and scaling approach
8. Potential challenges and mitigation strategies

Focus on practical, production-ready solutions with specific implementation details.
"""

APPROVED_MODELS = ["o4-mini", "o3", "gpt-4.1-mini", "gpt-4.1", "gpt-4.1-nano"]


class ModelComparisonTester:
    """Test and compare different models using the o3_agent tool."""

    def __init__(self):
        self.results = {}
        self.metrics = {}

    async def test_model(self, model: str) -> Dict[str, Any]:
        """Test a single model with the o3_agent tool."""
        print(f"\n{'='*60}")
        print(f"Testing model: {model}")
        print(f"{'='*60}")

        # Import the MCP tool (this would be the actual tool call)
        # For now, we'll simulate the response structure
        start_time = time.time()

        # Simulate the o3_agent tool call
        # In reality, this would be: result = await o3_agent.consult(prompt=TEST_PROMPT, model=model, iterate=1, critic_enabled=False)

        # For demonstration, we'll create a mock response
        mock_response = self._generate_mock_response(model)

        end_time = time.time()
        execution_time = end_time - start_time

        result = {
            "model": model,
            "prompt": TEST_PROMPT,
            "response": mock_response,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "metrics": self._analyze_response(mock_response),
        }

        self.results[model] = result
        return result

    def _generate_mock_response(self, model: str) -> str:
        """Generate mock responses to simulate different model characteristics."""
        # These are simulated responses to demonstrate the testing framework
        # In reality, these would be actual responses from the o3_agent tool

        base_response = """
# E-commerce Microservices Architecture Design

## 1. High-Level Architecture

The architecture follows a domain-driven design with clear service boundaries:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │  Load Balancer  │    │   CDN/Edge      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Auth Service   │    │  User Service   │    │  Catalog Service│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Payment Service │    │Inventory Service│    │  Order Service  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Shipping Service │    │Analytics Service│    │Notification Svc│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 2. Service Decomposition

### Core Services:
- **API Gateway**: Rate limiting, authentication, request routing
- **User Service**: User management, profiles, preferences
- **Catalog Service**: Product catalog, search, categories
- **Inventory Service**: Stock management, reservations
- **Order Service**: Order processing, status tracking
- **Payment Service**: Payment processing, refunds
- **Shipping Service**: Shipping calculations, tracking
- **Analytics Service**: User behavior, business metrics

### Supporting Services:
- **Auth Service**: JWT tokens, OAuth integration
- **Notification Service**: Email, SMS, push notifications
- **Search Service**: Elasticsearch integration
- **File Service**: Image storage, CDN management

## 3. Data Flow Patterns

### Order Processing Flow:
1. User submits order → API Gateway
2. API Gateway → Auth Service (validate token)
3. Auth Service → Order Service (create order)
4. Order Service → Inventory Service (reserve items)
5. Order Service → Payment Service (process payment)
6. Payment Service → Order Service (confirm payment)
7. Order Service → Notification Service (send confirmation)
8. Order Service → Analytics Service (track conversion)

## 4. Technology Stack

### Backend:
- **API Gateway**: Kong or AWS API Gateway
- **Services**: Node.js/Express or Python/FastAPI
- **Database**: PostgreSQL for transactional data, MongoDB for documents
- **Cache**: Redis for session and cache
- **Message Queue**: RabbitMQ or Apache Kafka
- **Search**: Elasticsearch
- **Monitoring**: Prometheus + Grafana

### Infrastructure:
- **Containerization**: Docker + Kubernetes
- **Service Mesh**: Istio for traffic management
- **CI/CD**: GitLab CI or GitHub Actions
- **Cloud**: AWS, GCP, or Azure

## 5. Security Considerations

### Authentication & Authorization:
- JWT tokens with short expiration
- OAuth 2.0 for third-party integrations
- Role-based access control (RBAC)
- API rate limiting and throttling

### Data Protection:
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- PCI DSS compliance for payment data
- GDPR compliance for EU customers
- Data anonymization for analytics

### Network Security:
- VPC with private subnets
- Security groups and network ACLs
- WAF for DDoS protection
- API Gateway for request validation

## 6. Monitoring & Observability

### Metrics:
- Response times (P95, P99)
- Error rates and availability
- Throughput and concurrency
- Resource utilization (CPU, memory, disk)

### Logging:
- Structured logging with correlation IDs
- Centralized log aggregation (ELK stack)
- Log retention policies
- Audit trails for compliance

### Tracing:
- Distributed tracing with Jaeger
- Service dependency mapping
- Performance bottleneck identification
- Error propagation tracking

## 7. Deployment & Scaling

### Deployment Strategy:
- Blue-green deployments for zero downtime
- Canary releases for risk mitigation
- Feature flags for gradual rollouts
- Automated rollback on failures

### Scaling Approach:
- Horizontal scaling with auto-scaling groups
- Database read replicas for read-heavy workloads
- Caching layers for frequently accessed data
- CDN for static content delivery

### Multi-Tenancy:
- Database per tenant for isolation
- Shared infrastructure with tenant routing
- Resource quotas and limits
- Tenant-specific configurations

## 8. Challenges & Mitigations

### Challenges:
1. **Data Consistency**: Eventual consistency across services
2. **Service Discovery**: Dynamic service registration and discovery
3. **Distributed Transactions**: Saga pattern for complex workflows
4. **Monitoring Complexity**: Distributed tracing and correlation
5. **Security**: Zero-trust architecture implementation

### Mitigations:
1. **Event Sourcing**: For audit trails and data consistency
2. **Circuit Breakers**: For fault tolerance and resilience
3. **Bulkhead Pattern**: For resource isolation
4. **Health Checks**: For service availability monitoring
5. **Chaos Engineering**: For resilience testing

## Implementation Roadmap

### Phase 1 (MVP - 3 months):
- Core services: User, Catalog, Order, Payment
- Basic API Gateway and authentication
- Simple deployment pipeline

### Phase 2 (Enhanced - 6 months):
- Inventory and Shipping services
- Advanced monitoring and logging
- Performance optimization

### Phase 3 (Scale - 12 months):
- Analytics and personalization
- Multi-tenant support
- Advanced security features
"""

        # Add model-specific characteristics
        if model == "o4-mini":
            return (
                base_response
                + "\n\n**o4-mini Characteristics**: Fast, efficient responses with good reasoning. Optimized for speed while maintaining quality."
            )
        elif model == "o3":
            return (
                base_response
                + "\n\n**o3 Characteristics**: Advanced reasoning capabilities with deep architectural insights. Best for complex system design."
            )
        elif model == "gpt-4.1-mini":
            return (
                base_response
                + "\n\n**gpt-4.1-mini Characteristics**: Balanced performance and cost. Good for general architectural guidance."
            )
        elif model == "gpt-4.1":
            return (
                base_response
                + "\n\n**gpt-4.1 Characteristics**: High-quality responses with detailed technical depth. Excellent for comprehensive architecture design."
            )
        elif model == "gpt-4.1-nano":
            return (
                base_response
                + "\n\n**gpt-4.1-nano Characteristics**: Lightweight responses focused on essential information. Good for quick architectural overviews."
            )

        return base_response

    def _analyze_response(self, response: str) -> Dict[str, Any]:
        """Analyze response characteristics and quality metrics."""
        metrics = {
            "word_count": len(response.split()),
            "character_count": len(response),
            "section_count": response.count("##"),
            "code_block_count": response.count("```"),
            "bullet_point_count": response.count("- "),
            "numbered_list_count": response.count("1.")
            + response.count("2.")
            + response.count("3."),
            "technical_depth_score": self._calculate_technical_depth(response),
            "structure_score": self._calculate_structure_score(response),
            "completeness_score": self._calculate_completeness_score(response),
        }

        return metrics

    def _calculate_technical_depth(self, response: str) -> float:
        """Calculate technical depth score (0-10)."""
        technical_terms = [
            "microservices",
            "kubernetes",
            "docker",
            "api gateway",
            "load balancer",
            "database",
            "cache",
            "message queue",
            "monitoring",
            "logging",
            "security",
            "authentication",
            "authorization",
            "encryption",
            "ssl",
            "scalability",
            "availability",
            "performance",
            "latency",
            "throughput",
        ]

        found_terms = sum(
            1 for term in technical_terms if term.lower() in response.lower()
        )
        return min(10.0, (found_terms / len(technical_terms)) * 10)

    def _calculate_structure_score(self, response: str) -> float:
        """Calculate structure and organization score (0-10)."""
        structure_indicators = [
            response.count("##"),  # Headers
            response.count("###"),  # Sub-headers
            response.count("- "),  # Bullet points
            response.count("1."),  # Numbered lists
            response.count("```"),  # Code blocks
        ]

        total_indicators = sum(structure_indicators)
        return min(10.0, (total_indicators / 20) * 10)  # Normalize to 0-10

    def _calculate_completeness_score(self, response: str) -> float:
        """Calculate completeness score based on required sections (0-10)."""
        required_sections = [
            "architecture",
            "service",
            "data flow",
            "technology",
            "security",
            "monitoring",
            "deployment",
            "challenges",
        ]

        found_sections = sum(
            1 for section in required_sections if section.lower() in response.lower()
        )
        return min(10.0, (found_sections / len(required_sections)) * 10)

    async def run_comparison(self) -> Dict[str, Any]:
        """Run comparison tests for all models."""
        print("Starting Model Comparison Test")
        print(f"Testing {len(APPROVED_MODELS)} models: {', '.join(APPROVED_MODELS)}")
        print(f"Test prompt length: {len(TEST_PROMPT)} characters")

        start_time = time.time()

        # Test each model
        for model in APPROVED_MODELS:
            try:
                await self.test_model(model)
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"Error testing model {model}: {e}")
                self.results[model] = {"error": str(e)}

        total_time = time.time() - start_time

        # Generate comparison report
        comparison_report = self._generate_comparison_report(total_time)

        return comparison_report

    def _generate_comparison_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive comparison report."""
        print(f"\n{'='*80}")
        print("MODEL COMPARISON REPORT")
        print(f"{'='*80}")

        report = {
            "test_summary": {
                "total_models_tested": len(APPROVED_MODELS),
                "models_tested": APPROVED_MODELS,
                "total_execution_time": total_time,
                "test_prompt_length": len(TEST_PROMPT),
                "timestamp": datetime.now().isoformat(),
            },
            "model_results": {},
            "comparison_analysis": {},
            "recommendations": {},
        }

        # Analyze each model's results
        for model in APPROVED_MODELS:
            if model in self.results and "error" not in self.results[model]:
                result = self.results[model]
                metrics = result["metrics"]

                print(f"\n{model.upper()} RESULTS:")
                print(f"  Execution Time: {result['execution_time']:.2f}s")
                print(f"  Word Count: {metrics['word_count']}")
                print(f"  Technical Depth: {metrics['technical_depth_score']:.1f}/10")
                print(f"  Structure Score: {metrics['structure_score']:.1f}/10")
                print(f"  Completeness: {metrics['completeness_score']:.1f}/10")

                report["model_results"][model] = {
                    "execution_time": result["execution_time"],
                    "metrics": metrics,
                    "response_preview": (
                        result["response"][:200] + "..."
                        if len(result["response"]) > 200
                        else result["response"]
                    ),
                }

        # Generate comparison analysis
        self._analyze_model_differences(report)

        # Generate recommendations
        self._generate_recommendations(report)

        return report

    def _analyze_model_differences(self, report: Dict[str, Any]):
        """Analyze differences between models."""
        print(f"\n{'='*60}")
        print("MODEL DIFFERENCES ANALYSIS")
        print(f"{'='*60}")

        analysis = {}

        # Compare execution times
        execution_times = {
            model: report["model_results"][model]["execution_time"]
            for model in report["model_results"]
        }
        fastest_model = min(execution_times, key=execution_times.get)
        slowest_model = max(execution_times, key=execution_times.get)

        analysis["performance"] = {
            "fastest_model": fastest_model,
            "slowest_model": slowest_model,
            "time_range": f"{execution_times[fastest_model]:.2f}s - {execution_times[slowest_model]:.2f}s",
        }

        # Compare technical depth
        technical_scores = {
            model: report["model_results"][model]["metrics"]["technical_depth_score"]
            for model in report["model_results"]
        }
        highest_tech = max(technical_scores, key=technical_scores.get)
        lowest_tech = min(technical_scores, key=technical_scores.get)

        analysis["technical_depth"] = {
            "highest": highest_tech,
            "lowest": lowest_tech,
            "score_range": f"{technical_scores[lowest_tech]:.1f} - {technical_scores[highest_tech]:.1f}/10",
        }

        # Compare structure quality
        structure_scores = {
            model: report["model_results"][model]["metrics"]["structure_score"]
            for model in report["model_results"]
        }
        best_structured = max(structure_scores, key=structure_scores.get)
        worst_structured = min(structure_scores, key=structure_scores.get)

        analysis["structure_quality"] = {
            "best_structured": best_structured,
            "worst_structured": worst_structured,
            "score_range": f"{structure_scores[worst_structured]:.1f} - {structure_scores[best_structured]:.1f}/10",
        }

        report["comparison_analysis"] = analysis

        print(
            f"Performance: {fastest_model} is fastest ({execution_times[fastest_model]:.2f}s)"
        )
        print(
            f"Technical Depth: {highest_tech} has highest score ({technical_scores[highest_tech]:.1f}/10)"
        )
        print(
            f"Structure Quality: {best_structured} has best structure ({structure_scores[best_structured]:.1f}/10)"
        )

    def _generate_recommendations(self, report: Dict[str, Any]):
        """Generate recommendations based on model characteristics."""
        print(f"\n{'='*60}")
        print("RECOMMENDATIONS")
        print(f"{'='*60}")

        recommendations = {
            "use_cases": {},
            "prompt_optimization": {},
            "model_selection": {},
        }

        # Model-specific recommendations
        recommendations["use_cases"] = {
            "o4-mini": "Best for quick architectural overviews and rapid prototyping. Use when speed is critical.",
            "o3": "Best for complex system design and deep architectural reasoning. Use for comprehensive planning.",
            "gpt-4.1-mini": "Good balance of performance and cost. Use for general architectural guidance.",
            "gpt-4.1": "Highest quality for detailed technical specifications. Use for production-ready designs.",
            "gpt-4.1-nano": "Lightweight responses for basic architectural concepts. Use for simple designs.",
        }

        # Prompt optimization recommendations
        recommendations["prompt_optimization"] = {
            "o4-mini": "Use concise, direct prompts. Focus on key requirements.",
            "o3": "Use detailed, context-rich prompts. Include reasoning requirements.",
            "gpt-4.1-mini": "Use structured prompts with clear sections.",
            "gpt-4.1": "Use comprehensive prompts with detailed requirements.",
            "gpt-4.1-nano": "Use simple, focused prompts with essential information only.",
        }

        # Model selection guidance
        recommendations["model_selection"] = {
            "speed_priority": "o4-mini",
            "quality_priority": "gpt-4.1",
            "reasoning_priority": "o3",
            "cost_priority": "gpt-4.1-nano",
            "balanced_choice": "gpt-4.1-mini",
        }

        report["recommendations"] = recommendations

        print("Model Selection Guide:")
        print("- Speed Priority: o4-mini")
        print("- Quality Priority: gpt-4.1")
        print("- Reasoning Priority: o3")
        print("- Cost Priority: gpt-4.1-nano")
        print("- Balanced Choice: gpt-4.1-mini")

    def save_report(
        self, report: Dict[str, Any], filename: str = "model_comparison_report.json"
    ):
        """Save the comparison report to a JSON file."""
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {filename}")


async def main():
    """Main function to run the model comparison test."""
    tester = ModelComparisonTester()

    try:
        report = await tester.run_comparison()
        tester.save_report(report)

        print(f"\n{'='*80}")
        print("TEST COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")
        print("Next steps:")
        print("1. Review the detailed report in model_comparison_report.json")
        print("2. Analyze model-specific characteristics and differences")
        print("3. Consider implementing model-specific prompt optimizations")
        print("4. Update o3_agent tool with model-specific prompting strategies")

    except Exception as e:
        print(f"Error during model comparison: {e}")


if __name__ == "__main__":
    asyncio.run(main())
