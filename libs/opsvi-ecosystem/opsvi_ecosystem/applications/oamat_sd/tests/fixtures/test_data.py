"""
Test Data Fixtures

Provides comprehensive test data for various testing scenarios including
sample requests, complexity analysis scenarios, and expected outputs.
"""

from dataclasses import dataclass


@dataclass
class TestRequest:
    """Test request with expected complexity and outcomes"""

    text: str
    expected_complexity_range: tuple
    expected_strategy: str
    expected_agents: list[str]
    description: str


@dataclass
class ComplexityTestCase:
    """Test case for complexity analysis validation"""

    request: str
    expected_factors: dict[str, int]
    expected_score_range: tuple
    expected_strategy: str
    rationale: str


# Sample test requests organized by complexity level
SIMPLE_REQUESTS = [
    TestRequest(
        text="What is Python?",
        expected_complexity_range=(1, 3),
        expected_strategy="simple",
        expected_agents=["researcher"],
        description="Basic informational query",
    ),
    TestRequest(
        text="Hello world",
        expected_complexity_range=(1, 2),
        expected_strategy="simple",
        expected_agents=["researcher"],
        description="Minimal greeting request",
    ),
    TestRequest(
        text="Define machine learning",
        expected_complexity_range=(2, 4),
        expected_strategy="simple",
        expected_agents=["researcher"],
        description="Definition request requiring research",
    ),
]

MEDIUM_REQUESTS = [
    TestRequest(
        text="Create a REST API for user management with authentication",
        expected_complexity_range=(4, 7),
        expected_strategy="multi_agent",
        expected_agents=["researcher", "analyst", "coder"],
        description="Code generation with specific requirements",
    ),
    TestRequest(
        text="Research Python web frameworks and recommend the best one",
        expected_complexity_range=(5, 7),
        expected_strategy="multi_agent",
        expected_agents=["researcher", "analyst", "synthesizer"],
        description="Research and analysis with recommendations",
    ),
    TestRequest(
        text="Analyze the performance of different database solutions",
        expected_complexity_range=(4, 6),
        expected_strategy="multi_agent",
        expected_agents=["researcher", "analyst"],
        description="Technical analysis requiring multiple sources",
    ),
]

COMPLEX_REQUESTS = [
    TestRequest(
        text="Build a complete e-commerce platform with microservices architecture",
        expected_complexity_range=(8, 10),
        expected_strategy="orchestrated",
        expected_agents=["researcher", "analyst", "synthesizer", "coder"],
        description="Large-scale system design and implementation",
    ),
    TestRequest(
        text="Design and implement a distributed machine learning pipeline with monitoring",
        expected_complexity_range=(7, 10),
        expected_strategy="orchestrated",
        expected_agents=["researcher", "analyst", "synthesizer", "coder"],
        description="Complex ML infrastructure with multiple components",
    ),
    TestRequest(
        text="Create a secure multi-tenant SaaS application with real-time features",
        expected_complexity_range=(8, 10),
        expected_strategy="orchestrated",
        expected_agents=["researcher", "analyst", "synthesizer", "coder"],
        description="Enterprise-grade application development",
    ),
]

# Comprehensive complexity test cases
COMPLEXITY_TEST_CASES = [
    ComplexityTestCase(
        request="What is FastAPI?",
        expected_factors={
            "scope": 2,
            "technical_depth": 2,
            "domain_knowledge": 3,
            "dependencies": 1,
            "timeline": 1,
            "risk": 1,
        },
        expected_score_range=(1.5, 2.5),
        expected_strategy="simple",
        rationale="Simple informational query with minimal complexity",
    ),
    ComplexityTestCase(
        request="Create a Python REST API with JWT authentication and user management",
        expected_factors={
            "scope": 6,
            "technical_depth": 7,
            "domain_knowledge": 6,
            "dependencies": 5,
            "timeline": 4,
            "risk": 3,
        },
        expected_score_range=(5.0, 6.5),
        expected_strategy="multi_agent",
        rationale="Medium complexity requiring multiple technical skills",
    ),
    ComplexityTestCase(
        request="Build a distributed microservices platform with Kubernetes, monitoring, CI/CD, and security",
        expected_factors={
            "scope": 10,
            "technical_depth": 9,
            "domain_knowledge": 8,
            "dependencies": 9,
            "timeline": 8,
            "risk": 7,
        },
        expected_score_range=(8.0, 9.5),
        expected_strategy="orchestrated",
        rationale="High complexity requiring comprehensive expertise and coordination",
    ),
]

# Expected agent tool mappings
AGENT_TOOL_MAPPINGS = {
    "researcher": ["brave_search", "arxiv_research", "firecrawl_scraping"],
    "analyst": ["sequential_thinking", "context7_docs", "neo4j_database"],
    "synthesizer": ["sequential_thinking", "neo4j_database"],
    "coder": ["context7_docs", "sequential_thinking"],
}

# Sample solution artifacts for different request types
SAMPLE_SOLUTIONS = {
    "research_report": {
        "artifact_type": "research_report",
        "content": """# Python Web Frameworks Analysis

## Executive Summary
Based on comprehensive research and analysis, FastAPI emerges as the recommended framework for small teams due to its modern architecture, excellent performance, and developer-friendly features.

## Framework Comparison

### FastAPI
- **Performance**: Excellent (async support, fast request handling)
- **Documentation**: Automatic OpenAPI/Swagger generation
- **Learning Curve**: Moderate (requires Python 3.7+ and type hints)
- **Use Cases**: API development, microservices, high-performance applications

### Django
- **Performance**: Good (traditional synchronous model)
- **Documentation**: Extensive but manual
- **Learning Curve**: Steep (comprehensive framework with many concepts)
- **Use Cases**: Full-stack web applications, admin interfaces, content management

### Flask
- **Performance**: Good (lightweight and flexible)
- **Documentation**: Manual setup required
- **Learning Curve**: Easy (minimal and intuitive)
- **Use Cases**: Small applications, prototypes, custom solutions

## Recommendation
For a small team building modern applications, **FastAPI** is recommended due to:
1. Modern Python features (type hints, async support)
2. Automatic API documentation
3. Excellent performance characteristics
4. Growing ecosystem and community support
5. Ease of testing and deployment
        """,
        "metadata": {
            "word_count": 1847,
            "sections": ["executive_summary", "framework_comparison", "recommendation"],
            "confidence": 0.9,
            "research_sources": 15,
            "analysis_depth": "comprehensive",
        },
    },
    "code_implementation": {
        "artifact_type": "code",
        "content": """from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import jwt
import hashlib
from datetime import datetime, timedelta

app = FastAPI(title="User Management API", version="1.0.0")
security = HTTPBearer()

# Models
class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# In-memory storage (replace with database in production)
users_db = {}
user_id_counter = 1

# Authentication functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "SECRET_KEY", algorithm="HS256")
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, "SECRET_KEY", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API Endpoints
@app.post("/register", response_model=User)
async def register_user(user: UserCreate):
    global user_id_counter

    # Check if user already exists
    for existing_user in users_db.values():
        if existing_user["username"] == user.username or existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    hashed_password = hash_password(user.password)
    new_user = {
        "id": user_id_counter,
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "is_active": True
    }
    users_db[user_id_counter] = new_user
    user_id_counter += 1

    return User(**{k: v for k, v in new_user.items() if k != "password"})

@app.post("/login", response_model=Token)
async def login(user: UserLogin):
    # Find user
    db_user = None
    for user_data in users_db.values():
        if user_data["username"] == user.username:
            db_user = user_data
            break

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: str = Depends(get_current_user)):
    for user_data in users_db.values():
        if user_data["username"] == current_user:
            return User(**{k: v for k, v in user_data.items() if k != "password"})
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users", response_model=List[User])
async def list_users(current_user: str = Depends(get_current_user)):
    return [User(**{k: v for k, v in user_data.items() if k != "password"})
            for user_data in users_db.values()]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
        """,
        "metadata": {
            "lines_of_code": 147,
            "language": "python",
            "framework": "fastapi",
            "features": ["jwt_auth", "user_management", "password_hashing", "rest_api"],
            "confidence": 0.85,
            "completeness": "production_ready",
        },
    },
}

# Performance test scenarios
PERFORMANCE_TEST_SCENARIOS = [
    {
        "name": "sequential_processing",
        "requests": [
            "Research Python frameworks",
            "Research JavaScript frameworks",
            "Research Go frameworks",
        ],
        "expected_processing": "sequential",
        "expected_time_range": (15, 45),  # seconds
        "parallel_factor": 1.0,
    },
    {
        "name": "parallel_processing",
        "requests": [
            "Research Python frameworks",
            "Research JavaScript frameworks",
            "Research Go frameworks",
        ],
        "expected_processing": "parallel",
        "expected_time_range": (5, 15),  # seconds
        "parallel_factor": 3.0,  # 3x improvement expected
    },
    {
        "name": "complex_orchestration",
        "requests": ["Build a complete e-commerce platform with microservices"],
        "expected_processing": "orchestrated",
        "expected_time_range": (20, 60),  # seconds
        "parallel_factor": 2.0,  # Some parallelization in complex workflows
    },
]

# Security test cases
SECURITY_TEST_CASES = [
    {
        "category": "sql_injection",
        "malicious_inputs": [
            "'; DROP TABLE users; --",
            "' OR '1'='1'; --",
            "admin'; DELETE FROM users; --",
        ],
        "expected_behavior": "sanitized_or_rejected",
    },
    {
        "category": "xss_injection",
        "malicious_inputs": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ],
        "expected_behavior": "escaped_or_rejected",
    },
    {
        "category": "command_injection",
        "malicious_inputs": [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& curl malicious-site.com",
        ],
        "expected_behavior": "blocked_or_sanitized",
    },
    {
        "category": "code_injection",
        "malicious_inputs": [
            "exec('import os; os.system(\"rm -rf /\")')",
            "__import__('os').system('whoami')",
            "eval('print(\"code injection\")')",
        ],
        "expected_behavior": "not_executed",
    },
]

# Integration test scenarios
INTEGRATION_TEST_SCENARIOS = [
    {
        "name": "multi_agent_coordination",
        "request": "Research Python frameworks and provide recommendations",
        "expected_agents": ["researcher", "analyst", "synthesizer"],
        "expected_tools": ["brave_search", "arxiv_research", "sequential_thinking"],
        "expected_coordination": "parallel_with_synthesis",
        "expected_artifacts": ["research_data", "analysis_results", "recommendations"],
    },
    {
        "name": "tool_failure_recovery",
        "request": "Research latest AI developments",
        "simulated_failures": {"brave_search": 0.5},  # 50% failure rate
        "expected_behavior": "graceful_degradation",
        "fallback_tools": ["arxiv_research", "context7_docs"],
        "minimum_success_threshold": 0.7,
    },
    {
        "name": "state_persistence",
        "request": "Create a comprehensive analysis of cloud providers",
        "checkpoint_stages": ["research", "analysis", "synthesis"],
        "expected_state_updates": 3,
        "recovery_scenarios": ["agent_failure", "network_interruption"],
    },
]

# Schema validation test data
INCOMPLETE_REQUESTS = [
    {
        "prompt": "Build something",
        "missing": ["purpose", "type", "requirements"],
        "confidence": 0.1,
    },
    {
        "prompt": "Create a web app",
        "missing": ["features", "framework_preference", "target_users"],
        "confidence": 0.3,
    },
    {
        "prompt": "Design microservices",
        "missing": ["business_domain", "service_boundaries", "communication_patterns"],
        "confidence": 0.2,
    },
    {
        "prompt": "Write a script",
        "missing": ["purpose", "input_data", "expected_output"],
        "confidence": 0.2,
    },
]

COMPLETE_REQUESTS = [
    {
        "prompt": "Build a FastAPI web application for task management with user authentication, PostgreSQL database, and Docker deployment",
        "extracted": {
            "framework_preference": "FastAPI",
            "purpose": "task management",
            "features": ["user authentication"],
            "database_type": "PostgreSQL",
            "deployment_target": "Docker",
        },
        "missing": [],
        "confidence": 0.95,
    },
    {
        "prompt": "Create a Python script that processes CSV files from /data/input, validates the data, and outputs clean JSON to /data/output",
        "extracted": {
            "language_preference": "Python",
            "purpose": "data processing",
            "input_data": "CSV files from /data/input",
            "expected_output": "clean JSON to /data/output",
            "processing_steps": ["validates the data"],
        },
        "missing": [],
        "confidence": 0.9,
    },
    {
        "prompt": "Design a microservices architecture for e-commerce with product catalog, order management, payment processing, and user services using REST APIs and event-driven communication",
        "extracted": {
            "business_domain": "e-commerce",
            "service_boundaries": [
                "product catalog",
                "order management",
                "payment processing",
                "user services",
            ],
            "communication_patterns": ["REST APIs", "event-driven communication"],
        },
        "missing": [],
        "confidence": 0.85,
    },
]

SCHEMA_TEST_CASES = [
    {
        "request_type": "WEB_APPLICATION",
        "schema": {
            "required": ["purpose", "framework_preference", "features"],
            "optional": ["deployment_target", "authentication_method", "database_type"],
            "defaults": {
                "framework_preference": "FastAPI",
                "deployment_target": "Docker",
                "authentication_method": "JWT",
            },
        },
    },
    {
        "request_type": "MICROSERVICES",
        "schema": {
            "required": [
                "business_domain",
                "service_boundaries",
                "communication_patterns",
            ],
            "optional": [
                "data_persistence",
                "monitoring_requirements",
                "scaling_needs",
            ],
            "defaults": {
                "communication_patterns": "REST + async messaging",
                "data_persistence": "PostgreSQL",
                "monitoring_requirements": "Prometheus + Grafana",
            },
        },
    },
    {
        "request_type": "SIMPLE_SCRIPT",
        "schema": {
            "required": ["purpose", "input_data", "expected_output"],
            "optional": [
                "language_preference",
                "libraries",
                "performance_requirements",
            ],
            "defaults": {
                "language_preference": "Python",
                "libraries": "standard library preferred",
            },
        },
    },
]

# Gap analysis test scenarios
GAP_ANALYSIS_SCENARIOS = [
    {
        "name": "critical_gaps_only",
        "missing_required": ["purpose"],
        "expected_gaps": {"critical": ["purpose"], "important": [], "optional": []},
        "expected_confidence": 0.2,
    },
    {
        "name": "mixed_gaps",
        "missing_required": ["purpose", "framework_preference", "deployment_target"],
        "expected_gaps": {
            "critical": ["purpose"],
            "important": ["framework_preference"],
            "optional": ["deployment_target"],
        },
        "expected_confidence": 0.4,
    },
    {
        "name": "no_gaps",
        "missing_required": [],
        "expected_gaps": {"critical": [], "important": [], "optional": []},
        "expected_confidence": 1.0,
    },
]

# Information completion test data
COMPLETION_TEST_CASES = [
    {
        "gap_type": "researchable",
        "gap": "best_practices_for_authentication",
        "expected_completion": "JWT with refresh tokens and proper session management",
        "can_research": True,
    },
    {
        "gap_type": "default_applicable",
        "gap": "deployment_target",
        "expected_completion": "Docker",
        "can_research": False,
    },
    {
        "gap_type": "requires_clarification",
        "gap": "user_specific_business_rules",
        "expected_completion": None,
        "can_research": False,
        "escalate_to_user": True,
    },
]

# User clarification test scenarios
CLARIFICATION_SCENARIOS = [
    {
        "critical_gaps": ["purpose", "target_users"],
        "context": {"request_type": "WEB_APPLICATION"},
        "expected_questions": [
            {
                "field": "purpose",
                "question": "What is the main purpose of this web application?",
                "options": [
                    "Task management",
                    "Content management",
                    "E-commerce",
                    "Analytics dashboard",
                ],
                "why_needed": "Purpose determines the features, architecture, and technology choices",
            },
            {
                "field": "target_users",
                "question": "Who are the intended users of this application?",
                "options": [
                    "Small teams (5-10 users)",
                    "Medium teams (10-50 users)",
                    "Large organizations (50+ users)",
                ],
                "why_needed": "User base affects scalability, authentication, and UI design decisions",
            },
        ],
    },
    {
        "critical_gaps": ["business_domain"],
        "context": {"request_type": "MICROSERVICES"},
        "expected_questions": [
            {
                "field": "business_domain",
                "question": "What business domain will these microservices serve?",
                "options": [
                    "E-commerce",
                    "Financial services",
                    "Healthcare",
                    "Education",
                    "Media",
                ],
                "why_needed": "Domain affects service boundaries, data patterns, and compliance requirements",
            }
        ],
    },
]

# Request type detection test cases
REQUEST_TYPE_DETECTION_CASES = [
    {
        "prompts": [
            "Build a web app for managing tasks",
            "Create a REST API for user management",
            "I need a dashboard for monitoring metrics",
            "Develop a web application with authentication",
        ],
        "expected_type": "WEB_APPLICATION",
    },
    {
        "prompts": [
            "Design a microservices architecture for e-commerce",
            "Build distributed services with event-driven communication",
            "Create a scalable microservices system",
            "Implement service mesh for microservices",
        ],
        "expected_type": "MICROSERVICES",
    },
    {
        "prompts": [
            "Write a Python script to process CSV files",
            "Create a data analysis script",
            "Build a utility to backup files",
            "Generate a script for file conversion",
        ],
        "expected_type": "SIMPLE_SCRIPT",
    },
    {
        "prompts": [
            "Set up a machine learning pipeline",
            "Create a data processing workflow",
            "Build an ETL system",
            "Implement real-time data streaming",
        ],
        "expected_type": "DATA_PIPELINE",
    },
]
