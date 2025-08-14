# Example 3: Complex Refactor with Design Documentation

## Scenario
Refactor a monolithic authentication system into microservices using Claude Code with MCP tools, including staged planning, implementation, testing, documentation, and PR creation.

## Implementation

### Main Orchestration Script
```python
#!/usr/bin/env python3
# complex-refactor.py

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List
from opsvi_mcp.servers.claude_code import claude_run_v3

class AuthSystemRefactor:
    """Orchestrates complex authentication system refactoring"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.artifacts_dir = Path("/tmp/refactor_artifacts")
        self.artifacts_dir.mkdir(exist_ok=True)
        
    async def execute_refactor(self) -> Dict[str, Any]:
        """Execute complete refactoring workflow"""
        
        print("🚀 Starting authentication system refactoring...")
        
        # Phase 1: Analysis and Design
        design = await self.phase1_analysis_and_design()
        
        # Phase 2: Implementation
        implementation = await self.phase2_implementation(design)
        
        # Phase 3: Testing and Validation
        validation = await self.phase3_testing(implementation)
        
        # Phase 4: Documentation
        documentation = await self.phase4_documentation(
            design, implementation, validation
        )
        
        # Phase 5: PR Creation
        pr = await self.phase5_create_pr(
            implementation, validation, documentation
        )
        
        return {
            "status": "completed",
            "phases": {
                "design": design,
                "implementation": implementation,
                "validation": validation,
                "documentation": documentation,
                "pull_request": pr
            }
        }
    
    async def phase1_analysis_and_design(self) -> Dict[str, Any]:
        """Analyze current system and create design document"""
        
        print("\n📋 Phase 1: Analysis and Design")
        
        design_task = f"""
        Analyze the monolithic authentication system at {self.repo_path} and create a 
        comprehensive refactoring plan to split it into microservices.
        
        Requirements:
        1. Analyze current architecture:
           - Identify all authentication components
           - Map dependencies and data flows
           - Document current pain points
        
        2. Design microservices architecture:
           - User Service: User management and profiles
           - Auth Service: Authentication and token management
           - Permission Service: Authorization and RBAC
           - Session Service: Session management
        
        3. Create detailed design document including:
           - Service boundaries and responsibilities
           - API contracts between services
           - Data migration strategy
           - Deployment architecture
           - Rollback plan
        
        4. Generate sequence diagrams for key flows:
           - User registration
           - Login/logout
           - Token refresh
           - Permission checks
        
        Use MCP tools to analyze the codebase and create visualizations.
        """
        
        result = await claude_run_v3(
            task=design_task,
            mode="ANALYSIS",
            enable_mcp_tools=True,
            output_dir=str(self.artifacts_dir)
        )
        
        # Save design artifacts
        design_doc = self.artifacts_dir / "design_document.md"
        design_doc.write_text(result['output']['design_document'])
        
        return {
            "design_document": str(design_doc),
            "service_boundaries": result['output']['services'],
            "api_contracts": result['output']['api_contracts'],
            "migration_plan": result['output']['migration_plan']
        }
    
    async def phase2_implementation(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Implement the refactored microservices"""
        
        print("\n🔨 Phase 2: Implementation")
        
        services = design['service_boundaries']
        implementation_results = {}
        
        for service_name, service_spec in services.items():
            print(f"  Implementing {service_name}...")
            
            implementation_task = f"""
            Implement the {service_name} microservice based on the design specification:
            
            Service Specification:
            {json.dumps(service_spec, indent=2)}
            
            Requirements:
            1. Create service structure:
               - Initialize project with appropriate framework
               - Set up dependency management
               - Configure environment variables
            
            2. Implement core functionality:
               - All endpoints defined in API contract
               - Data models and database schema
               - Business logic with proper error handling
               - Input validation and sanitization
            
            3. Add infrastructure code:
               - Dockerfile for containerization
               - Kubernetes manifests
               - Health check endpoints
               - Metrics and logging
            
            4. Implement service communication:
               - REST clients for other services
               - Message queue integration if needed
               - Circuit breakers and retries
            
            5. Add security measures:
               - JWT validation
               - Rate limiting
               - Input sanitization
               - Secrets management
            
            Use MCP tools to create files, run tests, and validate implementation.
            """
            
            result = await claude_run_v3(
                task=implementation_task,
                mode="FULL_CYCLE",
                enable_mcp_tools=True,
                quality_level="high"
            )
            
            implementation_results[service_name] = {
                "files_created": result['output']['files_created'],
                "endpoints": result['output']['endpoints'],
                "tests_passed": result['output']['test_results']
            }
        
        return implementation_results
    
    async def phase3_testing(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive testing of refactored system"""
        
        print("\n🧪 Phase 3: Testing and Validation")
        
        testing_task = f"""
        Create and execute comprehensive test suite for the refactored authentication system:
        
        Services to test:
        {json.dumps(list(implementation.keys()), indent=2)}
        
        Test Requirements:
        1. Unit tests for each service:
           - Test all endpoints
           - Test business logic
           - Test error handling
           - Achieve >85% code coverage
        
        2. Integration tests:
           - Service-to-service communication
           - Database transactions
           - Message queue operations
           - External API calls
        
        3. End-to-end tests:
           - Complete user registration flow
           - Login with 2FA
           - Password reset flow
           - Permission escalation scenarios
        
        4. Performance tests:
           - Load testing with 1000 concurrent users
           - Stress testing to find breaking points
           - Latency measurements for critical paths
        
        5. Security tests:
           - SQL injection attempts
           - XSS vulnerability scanning
           - JWT token manipulation
           - Rate limiting validation
        
        Generate test reports with metrics and recommendations.
        """
        
        # Use Claude Code for test orchestration
        test_result = await claude_run_v3(
            task=testing_task,
            mode="TESTING",
            enable_mcp_tools=True
        )
        
        # Optionally spawn Codex sandboxes for parallel test execution
        if test_result['output']['requires_parallel_testing']:
            parallel_tests = await self.run_parallel_tests_in_sandbox(
                implementation
            )
            test_result['parallel_test_results'] = parallel_tests
        
        return {
            "test_summary": test_result['output']['summary'],
            "coverage": test_result['output']['coverage'],
            "performance_metrics": test_result['output']['performance'],
            "security_report": test_result['output']['security'],
            "recommendations": test_result['output']['recommendations']
        }
    
    async def phase4_documentation(
        self, 
        design: Dict[str, Any],
        implementation: Dict[str, Any],
        validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive documentation"""
        
        print("\n📚 Phase 4: Documentation Generation")
        
        documentation_task = f"""
        Create comprehensive documentation for the refactored authentication system:
        
        Documentation Requirements:
        1. Architecture Overview:
           - System architecture diagram
           - Service interaction diagrams
           - Data flow diagrams
           - Deployment topology
        
        2. Service Documentation (for each service):
           - README with quick start guide
           - API documentation (OpenAPI/Swagger)
           - Configuration guide
           - Database schema documentation
        
        3. Operations Guide:
           - Deployment procedures
           - Monitoring and alerting setup
           - Backup and recovery procedures
           - Scaling guidelines
        
        4. Developer Guide:
           - Local development setup
           - Testing procedures
           - Contributing guidelines
           - Troubleshooting guide
        
        5. Migration Guide:
           - Step-by-step migration from monolith
           - Data migration scripts
           - Rollback procedures
           - Timeline and milestones
        
        Include test results and performance metrics from validation phase.
        """
        
        result = await claude_run_v3(
            task=documentation_task,
            mode="DOCUMENTATION",
            context={
                "design": design,
                "implementation": implementation,
                "validation": validation
            }
        )
        
        # Save documentation artifacts
        docs_dir = self.artifacts_dir / "documentation"
        docs_dir.mkdir(exist_ok=True)
        
        for doc_name, doc_content in result['output']['documents'].items():
            doc_path = docs_dir / f"{doc_name}.md"
            doc_path.write_text(doc_content)
        
        return {
            "documentation_path": str(docs_dir),
            "documents_created": list(result['output']['documents'].keys()),
            "diagrams": result['output'].get('diagrams', [])
        }
    
    async def phase5_create_pr(
        self,
        implementation: Dict[str, Any],
        validation: Dict[str, Any],
        documentation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive PR with all changes"""
        
        print("\n🚀 Phase 5: Pull Request Creation")
        
        pr_task = f"""
        Create a comprehensive pull request for the authentication system refactoring:
        
        PR Requirements:
        1. Title: "Refactor: Split monolithic auth into microservices"
        
        2. Description should include:
           - Executive summary of changes
           - List of new services created
           - Breaking changes and migration requirements
           - Performance improvements
           - Security enhancements
        
        3. Organize commits logically:
           - Design and documentation
           - Service implementations (one commit per service)
           - Tests
           - Infrastructure code
           - Migration scripts
        
        4. Include in PR description:
           - Link to design document
           - Test results summary (coverage: {validation['coverage']}%)
           - Performance metrics comparison
           - Deployment checklist
           - Rollback plan
        
        5. Add labels:
           - "refactor"
           - "breaking-change"
           - "needs-review"
           - "documentation"
        
        Use GitHub MCP tools to create the PR with proper formatting.
        """
        
        result = await claude_run_v3(
            task=pr_task,
            mode="CODE",
            enable_mcp_tools=True,
            context={
                "implementation": implementation,
                "validation": validation,
                "documentation": documentation
            }
        )
        
        return {
            "pr_url": result['output']['pr_url'],
            "pr_number": result['output']['pr_number'],
            "commits": result['output']['commits'],
            "reviewers_assigned": result['output']['reviewers']
        }
    
    async def run_parallel_tests_in_sandbox(
        self, 
        implementation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run tests in parallel using OpenAI Codex sandboxes"""
        
        from opsvi_mcp.servers.multi_agent_orchestrator import spawn_codex_sandbox
        
        test_tasks = []
        for service_name in implementation.keys():
            task = spawn_codex_sandbox(
                task=f"Run complete test suite for {service_name}",
                repository_url=f"{self.repo_path}/services/{service_name}",
                generate_pr=False
            )
            test_tasks.append(task)
        
        results = await asyncio.gather(*test_tasks)
        
        return {
            service_name: result
            for service_name, result in zip(implementation.keys(), results)
        }


async def main():
    """Main execution"""
    
    repo_path = "/workspace/monolithic-auth-system"
    refactor = AuthSystemRefactor(repo_path)
    
    try:
        result = await refactor.execute_refactor()
        
        print("\n" + "="*60)
        print("✅ REFACTORING COMPLETE")
        print("="*60)
        print(f"📋 Design Document: {result['phases']['design']['design_document']}")
        print(f"🔨 Services Implemented: {len(result['phases']['implementation'])}")
        print(f"🧪 Test Coverage: {result['phases']['validation']['coverage']}%")
        print(f"📚 Documents Created: {len(result['phases']['documentation']['documents_created'])}")
        print(f"🔗 Pull Request: {result['phases']['pull_request']['pr_url']}")
        
        # Save final report
        report_path = Path("/tmp/refactor_report.json")
        report_path.write_text(json.dumps(result, indent=2))
        print(f"\n📊 Full report saved to: {report_path}")
        
    except Exception as e:
        print(f"\n❌ Refactoring failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
```

### Expected Output Structure

```json
{
  "status": "completed",
  "phases": {
    "design": {
      "design_document": "/tmp/refactor_artifacts/design_document.md",
      "service_boundaries": {
        "user-service": {
          "responsibilities": ["user CRUD", "profile management"],
          "database": "PostgreSQL",
          "endpoints": 12
        },
        "auth-service": {
          "responsibilities": ["authentication", "JWT management"],
          "database": "Redis",
          "endpoints": 8
        }
      },
      "api_contracts": "openapi_specs/",
      "migration_plan": "30-day phased rollout"
    },
    "implementation": {
      "user-service": {
        "files_created": 47,
        "endpoints": 12,
        "tests_passed": 98
      },
      "auth-service": {
        "files_created": 38,
        "endpoints": 8,
        "tests_passed": 76
      }
    },
    "validation": {
      "test_summary": "342 tests passed, 0 failed",
      "coverage": "89.3%",
      "performance_metrics": {
        "login_latency_ms": 45,
        "throughput_rps": 2500
      },
      "security_report": "No critical vulnerabilities found"
    },
    "documentation": {
      "documentation_path": "/tmp/refactor_artifacts/documentation",
      "documents_created": [
        "README",
        "ARCHITECTURE",
        "API_REFERENCE",
        "MIGRATION_GUIDE",
        "OPERATIONS_MANUAL"
      ]
    },
    "pull_request": {
      "pr_url": "https://github.com/org/auth-system/pull/234",
      "pr_number": 234,
      "commits": 15,
      "reviewers_assigned": ["senior-dev-1", "security-team"]
    }
  }
}
```

### Monitoring and Rollback

```python
# monitor_refactor.py

class RefactorMonitor:
    """Monitor the refactored system post-deployment"""
    
    async def monitor_deployment(self):
        """Monitor key metrics after deployment"""
        
        metrics = {
            "error_rate": self.check_error_rate(),
            "latency": self.check_latency(),
            "throughput": self.check_throughput(),
            "user_reports": self.check_user_feedback()
        }
        
        if self.should_rollback(metrics):
            await self.initiate_rollback()
        
    def should_rollback(self, metrics):
        """Determine if rollback is needed"""
        return (
            metrics['error_rate'] > 0.05 or  # >5% error rate
            metrics['latency'] > 100 or      # >100ms latency
            metrics['user_reports'] > 10     # >10 complaints
        )
```

---
*This example demonstrates Claude Code's ability to handle complex, multi-phase refactoring with comprehensive planning, implementation, testing, and documentation using MCP tools.*