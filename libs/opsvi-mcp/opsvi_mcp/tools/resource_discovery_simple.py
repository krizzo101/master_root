#!/usr/bin/env python3
"""
Simple Resource Discovery - Just answers: Do we have it? Where?
No fancy matching, no documentation, just binary decisions.
"""

from pathlib import Path
from typing import Dict, Any
import json


class SimpleResourceDiscovery:
    """
    Dead simple resource discovery.
    Pre-computed capability map for instant lookups.
    """
    
    # Static capability map - what each package provides
    CAPABILITY_MAP = {
        # Authentication & Security
        "jwt": "opsvi-auth",
        "authentication": "opsvi-auth", 
        "authorization": "opsvi-auth",
        "auth": "opsvi-auth",
        "token": "opsvi-auth",
        "oauth": "opsvi-auth",
        "security": "opsvi-security",
        "encryption": "opsvi-security",
        
        # Data & Databases
        "database": "opsvi-data",
        "postgresql": "opsvi-data",
        "postgres": "opsvi-data",
        "mysql": "opsvi-data",
        "mongodb": "opsvi-data",
        "redis": "opsvi-data",
        "cache": "opsvi-data",
        "arango": "opsvi-data",
        "arangodb": "opsvi-data",
        "sql": "opsvi-data",
        
        # AI/ML
        "llm": "opsvi-llm",
        "openai": "opsvi-llm",
        "gpt": "opsvi-llm",
        "claude": "opsvi-llm",
        "anthropic": "opsvi-llm",
        "ai": "opsvi-llm",
        "embeddings": "opsvi-llm",
        "agents": "opsvi-agents",
        "agent": "opsvi-agents",
        
        # Networking & APIs
        "api": "opsvi-api",
        "rest": "opsvi-api",
        "graphql": "opsvi-api",
        "http": "opsvi-http",
        "requests": "opsvi-http",
        "client": "opsvi-http",
        "gateway": "opsvi-gateway",
        
        # MCP & Tools
        "mcp": "opsvi-mcp",
        "tool": "opsvi-mcp",
        "tools": "opsvi-mcp",
        
        # Infrastructure
        "docker": "opsvi-docker",
        "container": "opsvi-docker",
        "kubernetes": "opsvi-deploy",
        "k8s": "opsvi-deploy",
        "deployment": "opsvi-deploy",
        "deploy": "opsvi-deploy",
        "cicd": "opsvi-deploy",
        
        # Processing & Workflows
        "pipeline": "opsvi-pipeline",
        "workflow": "opsvi-orch",
        "orchestration": "opsvi-orch",
        "queue": "opsvi-workers",
        "worker": "opsvi-workers",
        "job": "opsvi-workers",
        "task": "opsvi-workers",
        "background": "opsvi-workers",
        
        # Storage & Memory
        "file": "opsvi-fs",
        "filesystem": "opsvi-fs",
        "storage": "opsvi-fs",
        "memory": "opsvi-memory",
        "session": "opsvi-memory",
        "state": "opsvi-memory",
        
        # Communication
        "message": "opsvi-comm",
        "messaging": "opsvi-comm",
        "notification": "opsvi-comm",
        "email": "opsvi-comm",
        "sms": "opsvi-comm",
        "websocket": None,  # Explicitly not available
        
        # Monitoring & Observability
        "monitoring": "opsvi-monitoring",
        "metrics": "opsvi-monitoring",
        "logging": "opsvi-monitoring",
        "observability": "opsvi-monitoring",
        "telemetry": "opsvi-monitoring",
        
        # Documentation & Testing
        "documentation": "opsvi-docs",
        "docs": "opsvi-docs",
        "test": "opsvi-test",
        "testing": "opsvi-test",
        "qa": "opsvi-test",
        
        # RAG & Vector
        "rag": "opsvi-rag",
        "retrieval": "opsvi-rag",
        "vector": "opsvi-rag",
        "similarity": "opsvi-rag",
        "search": "opsvi-rag",
        
        # Core & Shared
        "core": "opsvi-core",
        "foundation": "opsvi-foundation",
        "base": "opsvi-foundation",
        "shared": "opsvi-shared",
        "common": "opsvi-shared",
        "utility": "opsvi-shared",
        "utilities": "opsvi-shared",
        
        # Special
        "asea": "opsvi-asea",
        "master": "opsvi-master",
        "ecosystem": "opsvi-ecosystem",
    }
    
    def __init__(self, root_path: str = "/home/opsvi/master_root"):
        self.root_path = Path(root_path)
        self.libs_path = self.root_path / "libs"
    
    def check(self, query: str) -> Dict[str, Any]:
        """
        Simple check: do we have this capability?
        
        Args:
            query: What you're looking for
            
        Returns:
            exists: true/false
            package: package name if found
            import: how to import it
            confidence: how sure we are (1.0 for exact match, 0.0 for not found)
        """
        
        # Normalize query
        query_lower = query.lower().strip()
        
        # Direct lookup first - check each word
        words = query_lower.split()
        
        for word in words:
            if word in self.CAPABILITY_MAP:
                package = self.CAPABILITY_MAP[word]
                
                if package is None:
                    # Explicitly not available
                    return {
                        "exists": False,
                        "package": None,
                        "import": None,
                        "confidence": 1.0,  # We're sure it doesn't exist
                        "note": f"'{word}' capability not available"
                    }
                
                # Found it!
                module_name = package.replace("-", "_")
                return {
                    "exists": True,
                    "package": package,
                    "import": f"import {module_name}",
                    "confidence": 1.0,
                    "note": f"Found via '{word}' keyword"
                }
        
        # Check for common patterns
        if "connection pool" in query_lower or "connection pooling" in query_lower:
            return {
                "exists": True,
                "package": "opsvi-data",
                "import": "from opsvi_data.pool import ConnectionPool",
                "confidence": 0.9,
                "note": "Database connection pooling in opsvi-data"
            }
        
        # Not found
        return {
            "exists": False,
            "package": None,
            "import": None,
            "confidence": 0.0,
            "note": "No matching capability found"
        }
    
    def quick_check(self, package_name: str) -> Dict[str, Any]:
        """Direct package existence check."""
        
        # Normalize
        if not package_name.startswith("opsvi-"):
            package_name = f"opsvi-{package_name}"
        
        # Check if directory exists
        package_path = self.libs_path / package_name
        
        if package_path.exists() and package_path.is_dir():
            module_name = package_name.replace("-", "_")
            return {
                "exists": True,
                "package": package_name,
                "import": f"import {module_name}",
                "confidence": 1.0,
                "note": "Package exists"
            }
        
        return {
            "exists": False,
            "package": None,
            "import": None,
            "confidence": 1.0,
            "note": f"Package '{package_name}' not found"
        }
    
    def list_capabilities(self) -> Dict[str, Any]:
        """List what capabilities we have (not packages, capabilities)."""
        
        # Group capabilities by category
        capabilities = {
            "authentication": ["JWT", "OAuth", "tokens", "authorization"],
            "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "ArangoDB"],
            "ai_ml": ["LLM", "OpenAI", "Claude", "agents", "embeddings"],
            "networking": ["HTTP", "REST API", "GraphQL", "API gateway"],
            "infrastructure": ["Docker", "Kubernetes", "deployment", "CI/CD"],
            "processing": ["pipelines", "workflows", "queues", "background jobs"],
            "monitoring": ["metrics", "logging", "observability", "telemetry"],
            "storage": ["files", "memory", "sessions", "caching"],
            "not_available": ["WebSocket", "gRPC", "MQTT", "RabbitMQ"]
        }
        
        return {
            "available": capabilities,
            "total_packages": len(set(v for v in self.CAPABILITY_MAP.values() if v)),
            "note": "Use check('capability') to verify specific needs"
        }


if __name__ == "__main__":
    # Test the simple discovery
    discovery = SimpleResourceDiscovery()
    
    tests = [
        "JWT authentication",
        "database connection pooling",
        "Redis cache",
        "WebSocket support",
        "LLM operations",
        "Docker containers"
    ]
    
    print("Simple Resource Discovery Tests:\n")
    for test in tests:
        result = discovery.check(test)
        print(f"{test}:")
        if result['exists']:
            print(f"  ✓ YES - {result['package']}")
            print(f"    Import: {result['import']}")
        else:
            print(f"  ✗ NO - {result['note']}")
        print()