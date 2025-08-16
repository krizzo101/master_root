#!/usr/bin/env python3
"""
Knowledge Learning System - Main Entry Point

A comprehensive knowledge learning system for autonomous AI agents using Neo4j.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import components
from src.embedding_service import EmbeddingService, EmbeddingConfig
from src.neo4j_knowledge_store import Neo4jKnowledgeStore
from src.hybrid_retrieval import HybridRetriever, RetrievalConfig
from src.self_learning_loop import SelfLearningLoop
from src.agent_integration import KnowledgeIntegration, MCPKnowledgeTool


@dataclass
class KnowledgeSystemConfig:
    """Configuration for the knowledge system"""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 512
    enable_caching: bool = True
    cache_dir: str = ".cache"
    min_confidence: float = 0.7
    min_pattern_frequency: int = 3
    log_level: str = "INFO"


class Neo4jMCPWrapper:
    """
    Wrapper for Neo4j MCP tools to provide async interface
    """
    
    def __init__(self):
        """Initialize wrapper (uses MCP tools internally)"""
        pass
    
    async def read(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute read query using MCP tool
        
        Args:
            query: Cypher query
            params: Query parameters
            
        Returns:
            Query results
        """
        # This would call mcp__db__read_neo4j_cypher
        # For now, returning mock data for structure
        return []
    
    async def write(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute write query using MCP tool
        
        Args:
            query: Cypher query
            params: Query parameters
            
        Returns:
            Query results
        """
        # This would call mcp__db__write_neo4j_cypher
        # For now, returning mock data for structure
        return []


class KnowledgeLearningSystem:
    """
    Main knowledge learning system orchestrator
    """
    
    def __init__(self, config: Optional[KnowledgeSystemConfig] = None):
        """
        Initialize the knowledge learning system
        
        Args:
            config: System configuration
        """
        self.config = config or KnowledgeSystemConfig()
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.neo4j_client = None
        self.embedding_service = None
        self.knowledge_store = None
        self.retriever = None
        self.learner = None
        self.integration = None
        self.mcp_tool = None
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize all system components"""
        if self.initialized:
            return
        
        self.logger.info("Initializing Knowledge Learning System...")
        
        # Initialize Neo4j client (using MCP wrapper)
        self.neo4j_client = Neo4jMCPWrapper()
        
        # Initialize embedding service
        embedding_config = EmbeddingConfig(
            primary_model=self.config.embedding_model,
            target_dimension=self.config.embedding_dimension,
            cache_embeddings=self.config.enable_caching,
            cache_dir=os.path.join(self.config.cache_dir, "embeddings")
        )
        
        # Set OpenAI API key if provided
        if self.config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.config.openai_api_key
        
        self.embedding_service = EmbeddingService(embedding_config)
        
        # Initialize knowledge store
        self.knowledge_store = Neo4jKnowledgeStore(self.neo4j_client)
        await self.knowledge_store.initialize_schema()
        
        # Initialize hybrid retriever
        retrieval_config = RetrievalConfig(
            enable_caching=self.config.enable_caching
        )
        self.retriever = HybridRetriever(
            self.knowledge_store,
            self.embedding_service,
            retrieval_config
        )
        
        # Initialize self-learning loop
        self.learner = SelfLearningLoop(
            self.knowledge_store,
            self.embedding_service,
            min_pattern_frequency=self.config.min_pattern_frequency,
            min_confidence=self.config.min_confidence
        )
        
        # Initialize agent integration
        self.integration = KnowledgeIntegration(
            self.knowledge_store,
            self.retriever,
            self.learner,
            self.embedding_service
        )
        
        # Create MCP tool interface
        self.mcp_tool = MCPKnowledgeTool(self.integration)
        
        self.initialized = True
        self.logger.info("Knowledge Learning System initialized successfully")
    
    async def query(
        self,
        query: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None,
        max_results: int = 5
    ) -> Dict:
        """
        Query the knowledge system
        
        Args:
            query: Query text
            session_id: Optional session ID
            context: Optional context
            max_results: Maximum results
            
        Returns:
            Query results with metadata
        """
        if not self.initialized:
            await self.initialize()
        
        # Use default session if not provided
        if not session_id:
            session_id = await self._get_or_create_session()
        
        # Update context if provided
        if context:
            await self.integration.update_context(session_id, context)
        
        # Query knowledge
        results = await self.integration.query_knowledge(
            session_id=session_id,
            query=query,
            max_results=max_results
        )
        
        return {
            'query': query,
            'results': results,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
    
    async def learn_from_interaction(
        self,
        interaction_type: str,
        data: Dict,
        session_id: Optional[str] = None
    ):
        """
        Learn from an interaction
        
        Args:
            interaction_type: Type of interaction
            data: Interaction data
            session_id: Optional session ID
        """
        if not self.initialized:
            await self.initialize()
        
        # Map interaction types to learning events
        if interaction_type == 'tool_usage':
            await self.integration.report_tool_usage(
                session_id=session_id or await self._get_or_create_session(),
                tool_name=data['tool'],
                parameters=data.get('parameters', {}),
                result=data.get('result'),
                success=data.get('success', True)
            )
        elif interaction_type == 'error':
            await self.integration.report_error(
                session_id=session_id or await self._get_or_create_session(),
                error_type=data.get('type', 'Unknown'),
                error_message=data.get('message', ''),
                stack_trace=data.get('stack_trace')
            )
        elif interaction_type == 'solution':
            await self.integration.report_solution(
                session_id=session_id or await self._get_or_create_session(),
                problem_description=data['problem'],
                solution_steps=data['steps'],
                success=data.get('success', True)
            )
    
    async def get_statistics(self) -> Dict:
        """
        Get system statistics
        
        Returns:
            System statistics and metrics
        """
        if not self.initialized:
            await self.initialize()
        
        # Get stats from various components
        store_stats = await self.knowledge_store.get_knowledge_stats()
        learner_metrics = self.learner.get_metrics()
        integration_metrics = self.integration.get_metrics()
        
        return {
            'knowledge_store': store_stats,
            'learning': learner_metrics,
            'integration': integration_metrics,
            'system': {
                'initialized': self.initialized,
                'cache_enabled': self.config.enable_caching,
                'embedding_model': self.config.embedding_model
            }
        }
    
    async def optimize(self):
        """Run optimization tasks"""
        if not self.initialized:
            await self.initialize()
        
        self.logger.info("Running optimization tasks...")
        
        # Merge duplicate knowledge
        merged = await self.knowledge_store.merge_duplicate_knowledge()
        self.logger.info(f"Merged {merged} duplicate knowledge entries")
        
        # Deprecate old knowledge
        deprecated = await self.knowledge_store.deprecate_old_knowledge()
        self.logger.info(f"Deprecated {deprecated} old knowledge entries")
        
        # Process event buffer
        await self.learner.process_event_buffer()
        
        # Clear retrieval cache
        self.retriever.clear_cache()
        
        self.logger.info("Optimization complete")
    
    async def _get_or_create_session(self) -> str:
        """Get or create a default session"""
        if not hasattr(self, '_default_session'):
            context = await self.integration.initialize_session(
                session_id=str(uuid.uuid4())
            )
            self._default_session = context.session_id
        return self._default_session
    
    async def shutdown(self):
        """Clean shutdown of the system"""
        if not self.initialized:
            return
        
        self.logger.info("Shutting down Knowledge Learning System...")
        
        # Process remaining events
        await self.learner.process_event_buffer()
        
        # End active sessions
        for session_id in list(self.integration.active_contexts.keys()):
            await self.integration.end_session(session_id)
        
        self.initialized = False
        self.logger.info("Shutdown complete")


# CLI Interface
async def main():
    """Main CLI interface for the knowledge system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge Learning System CLI')
    parser.add_argument('command', choices=['init', 'query', 'stats', 'optimize'],
                       help='Command to execute')
    parser.add_argument('--query', type=str, help='Query text')
    parser.add_argument('--context', type=str, help='Context JSON')
    parser.add_argument('--max-results', type=int, default=5,
                       help='Maximum results for query')
    
    args = parser.parse_args()
    
    # Initialize system
    config = KnowledgeSystemConfig()
    system = KnowledgeLearningSystem(config)
    
    try:
        if args.command == 'init':
            await system.initialize()
            print("System initialized successfully")
            
        elif args.command == 'query':
            if not args.query:
                print("Error: --query required for query command")
                return
            
            context = {}
            if args.context:
                import json
                context = json.loads(args.context)
            
            result = await system.query(
                query=args.query,
                context=context,
                max_results=args.max_results
            )
            
            import json
            print(json.dumps(result, indent=2, default=str))
            
        elif args.command == 'stats':
            stats = await system.get_statistics()
            import json
            print(json.dumps(stats, indent=2, default=str))
            
        elif args.command == 'optimize':
            await system.optimize()
            print("Optimization complete")
            
    finally:
        await system.shutdown()


if __name__ == "__main__":
    import uuid
    from datetime import datetime
    
    asyncio.run(main())