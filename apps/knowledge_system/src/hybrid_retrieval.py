"""
Hybrid Retrieval System for Knowledge Learning

Combines vector similarity search with graph traversal for optimal knowledge retrieval.
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class RetrievalConfig:
    """Configuration for hybrid retrieval"""
    vector_weight: float = 0.4
    graph_weight: float = 0.3
    recency_weight: float = 0.15
    success_weight: float = 0.15
    min_similarity: float = 0.7
    max_results: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 300


@dataclass
class RetrievalResult:
    """Result from hybrid retrieval"""
    knowledge_id: str
    content: str
    summary: str
    confidence_score: float
    relevance_score: float
    similarity_score: Optional[float] = None
    graph_distance: Optional[int] = None
    metadata: Optional[Dict] = None


class HybridRetriever:
    """
    Main hybrid retrieval system combining multiple search strategies
    """
    
    def __init__(
        self,
        knowledge_store,
        embedding_service,
        config: Optional[RetrievalConfig] = None
    ):
        """
        Initialize hybrid retriever
        
        Args:
            knowledge_store: Neo4j knowledge store instance
            embedding_service: Embedding service instance
            config: Retrieval configuration
        """
        self.store = knowledge_store
        self.embedder = embedding_service
        self.config = config or RetrievalConfig()
        self.cache = {} if config.enable_caching else None
        
    async def retrieve(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        k: int = None,
        filters: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """
        Main retrieval method using hybrid approach
        
        Args:
            query: Query text
            context: Optional context dictionary
            k: Number of results to return
            filters: Optional filters (type, language, etc.)
            
        Returns:
            List of retrieval results
        """
        k = k or self.config.max_results
        context = context or {}
        
        # Check cache
        cache_key = self._get_cache_key(query, context, filters)
        if self.cache and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if self._is_cache_valid(cached_result):
                logging.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result['results']
        
        # Generate query embedding
        query_embedding = await self.embedder.generate_embedding(query)
        
        # Execute parallel searches
        vector_task = asyncio.create_task(
            self._vector_search(query_embedding, k * 2, filters)
        )
        graph_task = asyncio.create_task(
            self._graph_search(context, k * 2, filters)
        )
        
        # If context suggests specific patterns, search for them
        pattern_task = None
        if self._has_pattern_indicators(query, context):
            pattern_task = asyncio.create_task(
                self._pattern_search(query, context, k)
            )
        
        # Wait for all searches
        tasks = [vector_task, graph_task]
        if pattern_task:
            tasks.append(pattern_task)
        
        results = await asyncio.gather(*tasks)
        
        vector_results = results[0]
        graph_results = results[1]
        pattern_results = results[2] if pattern_task else []
        
        # Combine and rank results
        combined_results = self._combine_results(
            vector_results,
            graph_results,
            pattern_results,
            query_embedding,
            context
        )
        
        # Apply final ranking and filtering
        final_results = self._rank_and_filter(combined_results, k)
        
        # Cache results
        if self.cache:
            self.cache[cache_key] = {
                'results': final_results,
                'timestamp': datetime.now()
            }
        
        return final_results
    
    async def _vector_search(
        self,
        embedding: List[float],
        k: int,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Vector similarity search
        
        Args:
            embedding: Query embedding
            k: Number of results
            filters: Optional filters
            
        Returns:
            List of vector search results
        """
        try:
            results = await self.store.vector_search(
                embedding=embedding,
                k=k,
                min_similarity=self.config.min_similarity,
                knowledge_type=filters.get('type') if filters else None
            )
            
            return [{
                'knowledge': r['knowledge'],
                'similarity': r['similarity'],
                'source': 'vector'
            } for r in results]
            
        except Exception as e:
            logging.error(f"Vector search error: {e}")
            return []
    
    async def _graph_search(
        self,
        context: Dict[str, Any],
        k: int,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Context-aware graph traversal search
        
        Args:
            context: Context dictionary
            k: Number of results
            filters: Optional filters
            
        Returns:
            List of graph search results
        """
        try:
            # Build enhanced context with filters
            enhanced_context = context.copy()
            if filters:
                enhanced_context.update(filters)
            
            results = await self.store.graph_search(
                context=enhanced_context,
                k=k
            )
            
            return [{
                'knowledge': r['knowledge'],
                'context_matches': r['context_matches'],
                'relevance_score': r['relevance_score'],
                'related': r.get('related', []),
                'source': 'graph'
            } for r in results]
            
        except Exception as e:
            logging.error(f"Graph search error: {e}")
            return []
    
    async def _pattern_search(
        self,
        query: str,
        context: Dict[str, Any],
        k: int
    ) -> List[Dict]:
        """
        Pattern-based search for specific knowledge types
        
        Args:
            query: Query text
            context: Context dictionary
            k: Number of results
            
        Returns:
            List of pattern search results
        """
        patterns = []
        
        # Detect error patterns
        if self._is_error_query(query):
            error_results = await self._search_error_patterns(query, k)
            patterns.extend(error_results)
        
        # Detect code patterns
        if self._is_code_query(query):
            code_results = await self._search_code_patterns(query, context, k)
            patterns.extend(code_results)
        
        # Detect workflow patterns
        if self._is_workflow_query(query):
            workflow_results = await self._search_workflow_patterns(query, k)
            patterns.extend(workflow_results)
        
        return patterns
    
    def _combine_results(
        self,
        vector_results: List[Dict],
        graph_results: List[Dict],
        pattern_results: List[Dict],
        query_embedding: List[float],
        context: Dict[str, Any]
    ) -> List[Dict]:
        """
        Combine results from different search methods
        
        Args:
            vector_results: Results from vector search
            graph_results: Results from graph search
            pattern_results: Results from pattern search
            query_embedding: Query embedding for similarity calculation
            context: Context for relevance scoring
            
        Returns:
            Combined and scored results
        """
        # Create a unified result map
        result_map = {}
        
        # Process vector results
        for vr in vector_results:
            knowledge = vr['knowledge']
            kid = knowledge['id']
            
            if kid not in result_map:
                result_map[kid] = {
                    'knowledge': knowledge,
                    'scores': {},
                    'sources': []
                }
            
            result_map[kid]['scores']['vector'] = vr['similarity']
            result_map[kid]['sources'].append('vector')
        
        # Process graph results
        for gr in graph_results:
            knowledge = gr['knowledge']
            kid = knowledge['id']
            
            if kid not in result_map:
                result_map[kid] = {
                    'knowledge': knowledge,
                    'scores': {},
                    'sources': []
                }
            
            result_map[kid]['scores']['graph'] = gr['relevance_score']
            result_map[kid]['scores']['context_matches'] = gr['context_matches']
            result_map[kid]['sources'].append('graph')
            
            # Store related items for potential expansion
            if 'related' in gr:
                result_map[kid]['related'] = gr['related']
        
        # Process pattern results
        for pr in pattern_results:
            knowledge = pr['knowledge']
            kid = knowledge['id']
            
            if kid not in result_map:
                result_map[kid] = {
                    'knowledge': knowledge,
                    'scores': {},
                    'sources': []
                }
            
            result_map[kid]['scores']['pattern'] = pr.get('pattern_score', 0.8)
            result_map[kid]['sources'].append('pattern')
        
        # Calculate combined scores
        combined_results = []
        for kid, data in result_map.items():
            knowledge = data['knowledge']
            scores = data['scores']
            
            # Calculate weighted score
            total_score = 0.0
            
            # Vector similarity component
            if 'vector' in scores:
                total_score += scores['vector'] * self.config.vector_weight
            
            # Graph relevance component
            if 'graph' in scores:
                total_score += min(1.0, scores['graph'] / 10) * self.config.graph_weight
            
            # Pattern match bonus
            if 'pattern' in scores:
                total_score += scores['pattern'] * 0.2
            
            # Success rate component
            success_rate = knowledge.get('success_rate', 0.0)
            total_score += success_rate * self.config.success_weight
            
            # Recency component
            recency_score = self._calculate_recency_score(knowledge)
            total_score += recency_score * self.config.recency_weight
            
            # Context boost
            context_boost = self._calculate_context_boost(knowledge, context)
            total_score *= (1 + context_boost)
            
            combined_results.append({
                'knowledge': knowledge,
                'relevance_score': total_score,
                'similarity_score': scores.get('vector'),
                'sources': data['sources'],
                'scores': scores
            })
        
        return combined_results
    
    def _rank_and_filter(
        self,
        results: List[Dict],
        k: int
    ) -> List[RetrievalResult]:
        """
        Final ranking and filtering of results
        
        Args:
            results: Combined results
            k: Number of results to return
            
        Returns:
            Final list of retrieval results
        """
        # Sort by relevance score
        sorted_results = sorted(
            results,
            key=lambda x: x['relevance_score'],
            reverse=True
        )
        
        # Convert to RetrievalResult objects
        final_results = []
        seen_content = set()
        
        for r in sorted_results[:k * 2]:  # Process more to account for deduplication
            knowledge = r['knowledge']
            
            # Skip if content is too similar to already selected results
            content_hash = self._get_content_hash(knowledge['content'])
            if content_hash in seen_content:
                continue
            
            seen_content.add(content_hash)
            
            # Create retrieval result
            result = RetrievalResult(
                knowledge_id=knowledge['id'],
                content=knowledge['content'],
                summary=knowledge.get('summary', knowledge['content'][:200]),
                confidence_score=knowledge.get('confidence_score', 0.5),
                relevance_score=r['relevance_score'],
                similarity_score=r.get('similarity_score'),
                metadata={
                    'type': knowledge.get('type'),
                    'sources': r['sources'],
                    'scores': r['scores']
                }
            )
            
            final_results.append(result)
            
            if len(final_results) >= k:
                break
        
        return final_results
    
    def _calculate_recency_score(self, knowledge: Dict) -> float:
        """
        Calculate recency score for knowledge
        
        Args:
            knowledge: Knowledge entry
            
        Returns:
            Recency score between 0 and 1
        """
        last_accessed = knowledge.get('last_accessed')
        if not last_accessed:
            created_at = knowledge.get('created_at')
            if not created_at:
                return 0.0
            last_accessed = created_at
        
        # Parse datetime string
        if isinstance(last_accessed, str):
            last_accessed = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
        
        # Calculate age in days
        age_days = (datetime.now() - last_accessed).days
        
        # Exponential decay with half-life of 30 days
        recency_score = 0.5 ** (age_days / 30)
        
        return max(0.0, min(1.0, recency_score))
    
    def _calculate_context_boost(
        self,
        knowledge: Dict,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate context-based boost factor
        
        Args:
            knowledge: Knowledge entry
            context: Context dictionary
            
        Returns:
            Boost factor (0.0 to 1.0)
        """
        boost = 0.0
        
        # Check for matching user preferences
        if 'user_id' in context and knowledge.get('type') == 'UserPreference':
            if knowledge.get('user_id') == context['user_id']:
                boost += 0.3
        
        # Check for matching language/framework
        if 'language' in context and knowledge.get('language') == context['language']:
            boost += 0.2
        
        if 'framework' in context and knowledge.get('framework') == context['framework']:
            boost += 0.2
        
        # Check for matching error context
        if 'error_type' in context and knowledge.get('error_type') == context['error_type']:
            boost += 0.3
        
        # Check for tool context
        if 'tools' in context:
            knowledge_tools = knowledge.get('tools_used', [])
            matching_tools = set(context['tools']) & set(knowledge_tools)
            if matching_tools:
                boost += 0.1 * len(matching_tools)
        
        return min(1.0, boost)
    
    def _has_pattern_indicators(self, query: str, context: Dict) -> bool:
        """
        Check if query indicates pattern search
        
        Args:
            query: Query text
            context: Context dictionary
            
        Returns:
            True if pattern search is indicated
        """
        pattern_keywords = [
            'error', 'exception', 'bug', 'issue',
            'code', 'function', 'class', 'method',
            'workflow', 'process', 'steps', 'procedure'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in pattern_keywords)
    
    def _is_error_query(self, query: str) -> bool:
        """Check if query is about errors"""
        error_indicators = [
            'error', 'exception', 'failed', 'bug',
            'traceback', 'stack trace', 'crash'
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in error_indicators)
    
    def _is_code_query(self, query: str) -> bool:
        """Check if query is about code"""
        code_indicators = [
            'function', 'class', 'method', 'code',
            'implement', 'algorithm', 'pattern'
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in code_indicators)
    
    def _is_workflow_query(self, query: str) -> bool:
        """Check if query is about workflows"""
        workflow_indicators = [
            'workflow', 'process', 'steps', 'procedure',
            'pipeline', 'sequence', 'flow'
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in workflow_indicators)
    
    async def _search_error_patterns(self, query: str, k: int) -> List[Dict]:
        """Search for error resolution patterns"""
        # Extract error signature from query
        error_signature = self._extract_error_signature(query)
        
        if error_signature:
            resolution = await self.store.find_resolution(error_signature)
            if resolution:
                return [{
                    'knowledge': resolution,
                    'pattern_score': 1.0
                }]
        
        return []
    
    async def _search_code_patterns(
        self,
        query: str,
        context: Dict,
        k: int
    ) -> List[Dict]:
        """Search for code patterns"""
        language = context.get('language', self._detect_language(query))
        
        if language:
            patterns = await self.store.find_patterns_by_language(language)
            return [{
                'knowledge': p,
                'pattern_score': 0.8
            } for p in patterns[:k]]
        
        return []
    
    async def _search_workflow_patterns(self, query: str, k: int) -> List[Dict]:
        """Search for workflow patterns"""
        # Simple workflow search - can be enhanced
        return []
    
    def _extract_error_signature(self, query: str) -> Optional[str]:
        """Extract error signature from query"""
        # Simple extraction - can be enhanced with regex
        if 'Error:' in query:
            return query.split('Error:')[1].strip()[:100]
        return None
    
    def _detect_language(self, query: str) -> Optional[str]:
        """Detect programming language from query"""
        language_map = {
            'python': ['python', 'py', 'pip', 'django', 'flask'],
            'javascript': ['javascript', 'js', 'node', 'npm', 'react'],
            'java': ['java', 'spring', 'maven', 'gradle'],
            'go': ['golang', 'go', 'gin', 'goroutine'],
            'rust': ['rust', 'cargo', 'tokio']
        }
        
        query_lower = query.lower()
        for lang, keywords in language_map.items():
            if any(kw in query_lower for kw in keywords):
                return lang
        
        return None
    
    def _get_cache_key(
        self,
        query: str,
        context: Dict,
        filters: Optional[Dict]
    ) -> str:
        """Generate cache key"""
        key_parts = [
            query[:100],  # Truncate query for reasonable key size
            json.dumps(sorted(context.items())) if context else '',
            json.dumps(sorted(filters.items())) if filters else ''
        ]
        return '|'.join(key_parts)
    
    def _is_cache_valid(self, cached_entry: Dict) -> bool:
        """Check if cached entry is still valid"""
        if not cached_entry:
            return False
        
        timestamp = cached_entry.get('timestamp')
        if not timestamp:
            return False
        
        age_seconds = (datetime.now() - timestamp).seconds
        return age_seconds < self.config.cache_ttl_seconds
    
    def _get_content_hash(self, content: str) -> str:
        """Get hash of content for deduplication"""
        # Simple hash of first 200 characters
        return hash(content[:200])
    
    def clear_cache(self):
        """Clear the retrieval cache"""
        if self.cache:
            self.cache.clear()


class AdaptiveRetriever(HybridRetriever):
    """
    Adaptive retriever that learns from feedback
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback_history = []
        self.weight_adjustments = {
            'vector': 0.0,
            'graph': 0.0,
            'recency': 0.0,
            'success': 0.0
        }
    
    async def retrieve_with_feedback(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        k: int = None,
        filters: Optional[Dict] = None
    ) -> Tuple[List[RetrievalResult], str]:
        """
        Retrieve with feedback tracking
        
        Args:
            query: Query text
            context: Optional context
            k: Number of results
            filters: Optional filters
            
        Returns:
            Tuple of results and feedback ID
        """
        # Apply learned weight adjustments
        self._apply_weight_adjustments()
        
        # Perform retrieval
        results = await self.retrieve(query, context, k, filters)
        
        # Generate feedback ID
        feedback_id = str(uuid.uuid4())
        
        # Store retrieval data for feedback
        self.feedback_history.append({
            'id': feedback_id,
            'query': query,
            'context': context,
            'results': [r.knowledge_id for r in results],
            'timestamp': datetime.now()
        })
        
        return results, feedback_id
    
    def record_feedback(
        self,
        feedback_id: str,
        useful_results: List[str],
        not_useful_results: List[str]
    ):
        """
        Record user feedback on retrieval results
        
        Args:
            feedback_id: Feedback ID from retrieval
            useful_results: List of useful knowledge IDs
            not_useful_results: List of not useful knowledge IDs
        """
        # Find the retrieval record
        retrieval = None
        for record in self.feedback_history:
            if record['id'] == feedback_id:
                retrieval = record
                break
        
        if not retrieval:
            logging.warning(f"Feedback ID not found: {feedback_id}")
            return
        
        # Analyze feedback to adjust weights
        self._analyze_feedback(retrieval, useful_results, not_useful_results)
    
    def _apply_weight_adjustments(self):
        """Apply learned weight adjustments"""
        self.config.vector_weight = max(0.1, min(0.6,
            self.config.vector_weight + self.weight_adjustments['vector']
        ))
        self.config.graph_weight = max(0.1, min(0.5,
            self.config.graph_weight + self.weight_adjustments['graph']
        ))
        self.config.recency_weight = max(0.05, min(0.3,
            self.config.recency_weight + self.weight_adjustments['recency']
        ))
        self.config.success_weight = max(0.05, min(0.3,
            self.config.success_weight + self.weight_adjustments['success']
        ))
    
    def _analyze_feedback(
        self,
        retrieval: Dict,
        useful_results: List[str],
        not_useful_results: List[str]
    ):
        """
        Analyze feedback to adjust retrieval weights
        
        Args:
            retrieval: Retrieval record
            useful_results: Useful knowledge IDs
            not_useful_results: Not useful knowledge IDs
        """
        # Simple weight adjustment based on feedback
        # This could be enhanced with more sophisticated learning
        
        adjustment_factor = 0.01
        
        # If vector search produced useful results, increase its weight
        if len(useful_results) > len(not_useful_results):
            self.weight_adjustments['vector'] += adjustment_factor
        else:
            self.weight_adjustments['vector'] -= adjustment_factor
        
        # Normalize adjustments
        total_adjustment = sum(abs(v) for v in self.weight_adjustments.values())
        if total_adjustment > 0.2:
            # Scale down if adjustments are too large
            scale = 0.2 / total_adjustment
            for key in self.weight_adjustments:
                self.weight_adjustments[key] *= scale