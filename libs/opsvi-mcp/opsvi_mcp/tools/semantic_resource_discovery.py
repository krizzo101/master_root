#!/usr/bin/env python3
"""
Semantic Resource Discovery using Knowledge Base
Uses vector embeddings for intelligent capability matching
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib


class SemanticResourceDiscovery:
    """
    Resource discovery using Neo4j knowledge base with semantic search.
    Stores package capabilities as knowledge and uses vector similarity for matching.
    """
    
    def __init__(self, root_path: str = "/home/opsvi/master_root"):
        self.root_path = Path(root_path)
        self.libs_path = self.root_path / "libs"
        
        # Index packages on first run
        self._ensure_packages_indexed()
    
    def _ensure_packages_indexed(self):
        """Ensure all packages are indexed in the knowledge base."""
        # This will be called once to populate the knowledge base
        # In production, this would be done as a separate indexing job
        pass
    
    def check_capability(self, functionality: str) -> Dict[str, Any]:
        """
        Check if a capability exists using semantic search.
        
        Args:
            functionality: Natural language description of needed capability
            
        Returns:
            Binary decision with location if found
        """
        
        # Use knowledge_query to search semantically
        from . import mcp_knowledge_query
        
        query_result = mcp_knowledge_query(
            query_type="search",
            query_text=f"package library capability: {functionality}",
            knowledge_type="PACKAGE_CAPABILITY",
            min_confidence=0.6,
            limit=3
        )
        
        # Parse the result
        if isinstance(query_result, str):
            query_info = json.loads(query_result)
        else:
            query_info = query_result
            
        # Execute the Cypher query
        from . import mcp_db_read
        
        results = mcp_db_read(
            query=query_info['cypher_query'],
            params=query_info['params']
        )
        
        if results and len(results) > 0:
            # Found capability
            best_match = results[0]
            
            # Extract package info from context
            context = json.loads(best_match.get('n.context', '{}'))
            
            return {
                "capability_exists": True,
                "confidence": float(best_match.get('n.confidence_score', 0.8)),
                "primary_package": context.get('package_name'),
                "usage": context.get('import_statement'),
                "location": context.get('package_path'),
                "description": best_match.get('n.content'),
                "alternatives": len(results) - 1,
                "recommendation": "Use existing package"
            }
        else:
            # Not found - suggest creation
            suggested_name = f"opsvi-{functionality.lower().split()[0]}"
            
            return {
                "capability_exists": False,
                "confidence": 0.0,
                "primary_package": None,
                "usage": None,
                "location": None,
                "description": None,
                "alternatives": 0,
                "recommendation": f"No existing capability. Consider creating '{suggested_name}'"
            }
    
    def index_package(self, package_path: Path) -> bool:
        """
        Index a single package into the knowledge base.
        
        Args:
            package_path: Path to the package directory
            
        Returns:
            True if successfully indexed
        """
        
        if not package_path.exists():
            return False
        
        package_name = package_path.name
        
        # Get package description
        description = self._get_package_description(package_path)
        
        # Determine capabilities
        capabilities = self._analyze_package_capabilities(package_path)
        
        # Create knowledge entry for each capability
        from . import mcp_knowledge_store
        
        for capability in capabilities:
            # Generate unique ID for this capability
            knowledge_id = hashlib.md5(
                f"{package_name}:{capability}".encode()
            ).hexdigest()[:16]
            
            # Prepare context
            context = {
                "package_name": package_name,
                "package_path": str(package_path),
                "import_statement": f"from {package_name.replace('-', '_')} import ...",
                "capability": capability
            }
            
            # Store in knowledge base
            result = mcp_knowledge_store(
                knowledge_type="PACKAGE_CAPABILITY",
                content=f"{package_name} provides {capability}: {description}",
                context=context,
                tags=[package_name, capability, "library", "package"],
                confidence_score=0.95,
                knowledge_id=knowledge_id
            )
            
            # Execute the storage
            if isinstance(result, str):
                store_info = json.loads(result)
            else:
                store_info = result
                
            from . import mcp_db_write
            mcp_db_write(
                query=store_info['cypher_query'],
                params=store_info['params']
            )
        
        return True
    
    def _get_package_description(self, package_path: Path) -> str:
        """Extract package description from README or pyproject.toml."""
        
        # Try README first
        readme_path = package_path / "README.md"
        if readme_path.exists():
            try:
                content = readme_path.read_text()
                for line in content.split("\n"):
                    if line.strip() and not line.startswith("#"):
                        return line.strip()[:200]
            except:
                pass
        
        return f"{package_path.name} package"
    
    def _analyze_package_capabilities(self, package_path: Path) -> List[str]:
        """
        Analyze package to determine its capabilities.
        Returns list of capability descriptions.
        """
        
        capabilities = []
        package_name = package_path.name.replace("opsvi-", "")
        
        # Map package names to capabilities
        capability_map = {
            "auth": ["JWT authentication", "user authentication", "authorization", "access control"],
            "data": ["database operations", "data storage", "database connections"],
            "llm": ["LLM integration", "AI models", "language model operations"],
            "api": ["REST API", "API endpoints", "HTTP services"],
            "mcp": ["MCP tools", "model context protocol", "tool integration"],
            "agents": ["AI agents", "autonomous agents", "agent orchestration"],
            "http": ["HTTP client", "web requests", "REST client"],
            "cache": ["caching", "Redis cache", "memory cache"],
            "queue": ["message queuing", "task queue", "job processing"],
            "workers": ["background workers", "task processing", "job execution"],
            "docker": ["Docker containers", "containerization", "Docker management"],
            "monitoring": ["system monitoring", "metrics collection", "observability"],
            "security": ["security operations", "encryption", "secure communication"],
            "rag": ["retrieval augmented generation", "vector search", "document retrieval"],
            "memory": ["memory management", "state persistence", "session storage"],
            "fs": ["file system operations", "file management", "storage operations"],
            "pipeline": ["data pipelines", "workflow orchestration", "pipeline processing"],
            "gateway": ["API gateway", "request routing", "service mesh"],
            "deploy": ["deployment automation", "CI/CD", "release management"],
            "test": ["testing framework", "test automation", "quality assurance"],
            "docs": ["documentation generation", "API documentation", "technical writing"],
            "comm": ["communication", "messaging", "notifications"],
            "orch": ["orchestration", "workflow management", "task coordination"],
            "master": ["master coordination", "central control", "system orchestration"],
            "asea": ["ASEA framework", "autonomous systems", "emergent capabilities"],
            "core": ["core utilities", "foundation library", "base functionality"],
            "foundation": ["foundation services", "base infrastructure", "core systems"],
            "shared": ["shared utilities", "common functionality", "reusable components"],
            "ecosystem": ["ecosystem management", "package coordination", "system integration"]
        }
        
        # Get capabilities based on package name
        if package_name in capability_map:
            capabilities.extend(capability_map[package_name])
        else:
            # Generic capability based on name
            capabilities.append(f"{package_name} operations")
        
        # Scan for specific patterns in the package
        module_path = package_path / package_name.replace("-", "_")
        if module_path.exists():
            # Check for specific files that indicate capabilities
            patterns = {
                "*client*.py": "client operations",
                "*provider*.py": "provider pattern implementation",
                "*manager*.py": "resource management",
                "*handler*.py": "event handling",
                "*processor*.py": "data processing",
                "*validator*.py": "data validation",
                "*auth*.py": "authentication",
                "*cache*.py": "caching",
                "*queue*.py": "message queuing",
                "*api*.py": "API operations",
                "*model*.py": "data modeling",
                "*schema*.py": "schema definitions"
            }
            
            for pattern, capability in patterns.items():
                if list(module_path.glob(pattern)):
                    if capability not in capabilities:
                        capabilities.append(capability)
        
        return capabilities[:5]  # Limit to top 5 capabilities per package
    
    def index_all_packages(self) -> Dict[str, Any]:
        """
        Index all packages in libs/ directory.
        This should be run once to populate the knowledge base.
        """
        
        if not self.libs_path.exists():
            return {
                "status": "error",
                "message": f"libs directory not found at {self.libs_path}"
            }
        
        indexed = 0
        failed = 0
        
        for package_dir in self.libs_path.iterdir():
            if package_dir.is_dir() and package_dir.name.startswith("opsvi-"):
                if self.index_package(package_dir):
                    indexed += 1
                else:
                    failed += 1
        
        return {
            "status": "success",
            "indexed": indexed,
            "failed": failed,
            "message": f"Indexed {indexed} packages into knowledge base"
        }


# MCP Tool wrapper functions
def mcp_knowledge_query(query_type, query_text, knowledge_type=None, min_confidence=0.7, limit=5):
    """Wrapper for knowledge query MCP tool."""
    # In production, this would call the actual MCP tool
    # For now, return a mock query
    return {
        "cypher_query": """
        MATCH (n:Knowledge)
        WHERE n.knowledge_type = $knowledge_type
        AND n.embedding IS NOT NULL
        WITH n, gds.similarity.cosine(n.embedding, $query_embedding) AS similarity
        WHERE similarity > $min_confidence
        RETURN n, similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """,
        "params": {
            "knowledge_type": knowledge_type,
            "query_embedding": [0.1] * 384,  # Mock embedding
            "min_confidence": min_confidence,
            "limit": limit
        }
    }

def mcp_knowledge_store(knowledge_type, content, context=None, tags=None, confidence_score=0.8, knowledge_id=None):
    """Wrapper for knowledge store MCP tool."""
    return {
        "cypher_query": """
        CREATE (n:Knowledge {
            knowledge_id: $knowledge_id,
            knowledge_type: $knowledge_type,
            content: $content,
            context: $context,
            tags: $tags,
            confidence_score: $confidence_score,
            created_at: datetime()
        })
        RETURN n
        """,
        "params": {
            "knowledge_id": knowledge_id,
            "knowledge_type": knowledge_type,
            "content": content,
            "context": json.dumps(context) if context else "{}",
            "tags": tags or [],
            "confidence_score": confidence_score
        }
    }

def mcp_db_read(query, params):
    """Wrapper for database read."""
    # Mock implementation
    return []

def mcp_db_write(query, params):
    """Wrapper for database write."""
    # Mock implementation
    return {"success": True}


if __name__ == "__main__":
    # Test the semantic discovery
    discovery = SemanticResourceDiscovery()
    
    # First, index all packages (run once)
    print("Indexing packages...")
    result = discovery.index_all_packages()
    print(result)
    
    # Test queries
    tests = [
        "JWT authentication",
        "database operations",
        "Redis cache",
        "WebSocket support",
        "LLM integration"
    ]
    
    print("\nTesting semantic search:")
    for test in tests:
        result = discovery.check_capability(test)
        print(f"\n{test}:")
        print(f"  Exists: {result['capability_exists']}")
        if result['capability_exists']:
            print(f"  Package: {result['primary_package']}")
            print(f"  Confidence: {result['confidence']}")