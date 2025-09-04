"""
Advanced CI/CD Integration Patterns - Practical Implementation Examples
=======================================================================

This module demonstrates advanced patterns for comprehensive build and deployment 
tracking, showcasing the research findings in practical, production-ready code.
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, deque

import structlog
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = structlog.get_logger(__name__)


# Enhanced Data Models
# ====================

@dataclass
class AdvancedCICDEvent:
    """Enhanced CI/CD event with comprehensive metadata."""
    
    # Core identification
    event_id: str
    platform: str
    event_type: str
    timestamp: datetime
    
    # Build/deployment context
    pipeline_id: str
    build_number: Optional[int] = None
    commit_sha: Optional[str] = None
    branch_name: Optional[str] = None
    author: Optional[str] = None
    
    # Performance data
    duration_ms: Optional[int] = None
    queue_time_ms: Optional[int] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)
    
    # Results and status
    status: str = "unknown"
    conclusion: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    logs: Optional[str] = None
    
    # Artifacts and outputs
    artifacts: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    
    # Security and compliance
    security_scan_results: Dict[str, Any] = field(default_factory=dict)
    compliance_status: Optional[str] = None
    
    # Raw platform data
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    
    # Correlation metadata (populated by analysis)
    correlations: List['EventCorrelation'] = field(default_factory=list)
    constellation_id: Optional[str] = None


@dataclass
class EventCorrelation:
    """Represents a correlation between CI/CD events."""
    
    source_event_id: str
    target_event_id: str
    correlation_type: str  # 'commit', 'temporal', 'semantic', 'performance'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BuildConstellation:
    """Unified view of related builds across platforms."""
    
    constellation_id: str
    primary_build: AdvancedCICDEvent
    related_builds: List[AdvancedCICDEvent]
    
    # Lifecycle tracking
    lifecycle_stage: str  # 'building', 'testing', 'deploying', 'completed'
    overall_status: str   # 'success', 'failure', 'in_progress'
    completion_percentage: float
    
    # Analytics
    total_duration_ms: Optional[int] = None
    bottlenecks: List[str] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


# Advanced Correlation Engine
# ===========================

class MultiDimensionalCorrelator:
    """Advanced correlation engine using multiple analysis dimensions."""
    
    def __init__(self):
        self.correlation_weights = {
            'commit_sha': 1.0,      # Perfect correlation
            'semantic': 0.8,        # High semantic similarity
            'temporal': 0.6,        # Time-based correlation
            'author': 0.5,          # Same developer
            'branch': 0.4,          # Same branch
            'performance': 0.3      # Performance pattern similarity
        }
        
        # Initialize semantic analysis components
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.semantic_model_initialized = False
        
    async def correlate_events(self, 
                              target_event: AdvancedCICDEvent, 
                              candidate_events: List[AdvancedCICDEvent],
                              time_window: timedelta = timedelta(hours=2)) -> List[EventCorrelation]:
        """Find correlations between target event and candidates."""
        
        correlations = []
        
        for candidate in candidate_events:
            # Skip if outside time window
            if abs((target_event.timestamp - candidate.timestamp).total_seconds()) > time_window.total_seconds():
                continue
                
            # Calculate correlation across multiple dimensions
            correlation_scores = await self._calculate_multi_dimensional_correlation(
                target_event, candidate
            )
            
            # Determine strongest correlation
            best_correlation_type, best_score = max(correlation_scores.items(), key=lambda x: x[1])
            
            if best_score > 0.3:  # Minimum correlation threshold
                correlation = EventCorrelation(
                    source_event_id=target_event.event_id,
                    target_event_id=candidate.event_id,
                    correlation_type=best_correlation_type,
                    strength=best_score,
                    confidence=self._calculate_confidence(correlation_scores),
                    evidence=correlation_scores
                )
                correlations.append(correlation)
                
        return sorted(correlations, key=lambda c: c.strength, reverse=True)
    
    async def _calculate_multi_dimensional_correlation(self, 
                                                     event1: AdvancedCICDEvent, 
                                                     event2: AdvancedCICDEvent) -> Dict[str, float]:
        """Calculate correlation scores across multiple dimensions."""
        
        scores = {}
        
        # 1. Commit SHA correlation (exact match)
        if event1.commit_sha and event2.commit_sha:
            scores['commit_sha'] = 1.0 if event1.commit_sha == event2.commit_sha else 0.0
        else:
            scores['commit_sha'] = 0.0
            
        # 2. Semantic similarity (based on logs/error messages)
        scores['semantic'] = await self._calculate_semantic_similarity(event1, event2)
        
        # 3. Temporal correlation (closer in time = higher correlation)
        scores['temporal'] = self._calculate_temporal_correlation(event1, event2)
        
        # 4. Author correlation (same developer)
        if event1.author and event2.author:
            scores['author'] = 1.0 if event1.author == event2.author else 0.0
        else:
            scores['author'] = 0.0
            
        # 5. Branch correlation (same branch)
        if event1.branch_name and event2.branch_name:
            scores['branch'] = 1.0 if event1.branch_name == event2.branch_name else 0.0
        else:
            scores['branch'] = 0.0
            
        # 6. Performance pattern correlation
        scores['performance'] = self._calculate_performance_correlation(event1, event2)
        
        return scores
    
    async def _calculate_semantic_similarity(self, 
                                           event1: AdvancedCICDEvent, 
                                           event2: AdvancedCICDEvent) -> float:
        """Calculate semantic similarity between events using NLP."""
        
        # Extract text content for comparison
        text1 = self._extract_event_text(event1)
        text2 = self._extract_event_text(event2)
        
        if not text1 or not text2:
            return 0.0
            
        try:
            # Use TF-IDF vectorization for similarity calculation
            texts = [text1, text2]
            
            if not self.semantic_model_initialized:
                # Initialize with sample data if needed
                sample_texts = texts + ["build failed", "deployment successful", "test error"]
                self.text_vectorizer.fit(sample_texts)
                self.semantic_model_initialized = True
                
            vectors = self.text_vectorizer.transform(texts)
            similarity_matrix = cosine_similarity(vectors)
            
            return similarity_matrix[0, 1]
            
        except Exception as e:
            logger.warning(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _extract_event_text(self, event: AdvancedCICDEvent) -> str:
        """Extract relevant text content from event for analysis."""
        text_parts = []
        
        if event.error_message:
            text_parts.append(event.error_message)
        if event.logs:
            # Use first 1000 characters of logs to avoid overwhelming the vectorizer
            text_parts.append(event.logs[:1000])
        if event.status:
            text_parts.append(event.status)
        if event.conclusion:
            text_parts.append(event.conclusion)
            
        return " ".join(text_parts)
    
    def _calculate_temporal_correlation(self, 
                                      event1: AdvancedCICDEvent, 
                                      event2: AdvancedCICDEvent) -> float:
        """Calculate correlation based on temporal proximity."""
        
        time_diff = abs((event1.timestamp - event2.timestamp).total_seconds())
        
        # Exponential decay: closer events have higher correlation
        # Full correlation within 5 minutes, decay to 0 over 2 hours
        max_time = 2 * 3600  # 2 hours in seconds
        if time_diff >= max_time:
            return 0.0
            
        return np.exp(-time_diff / (max_time / 4))
    
    def _calculate_performance_correlation(self, 
                                         event1: AdvancedCICDEvent, 
                                         event2: AdvancedCICDEvent) -> float:
        """Calculate correlation based on performance patterns."""
        
        if not event1.duration_ms or not event2.duration_ms:
            return 0.0
            
        # Normalize durations and calculate similarity
        duration_diff = abs(event1.duration_ms - event2.duration_ms)
        max_duration = max(event1.duration_ms, event2.duration_ms)
        
        if max_duration == 0:
            return 1.0
            
        similarity = 1.0 - (duration_diff / max_duration)
        return max(0.0, similarity)
    
    def _calculate_confidence(self, correlation_scores: Dict[str, float]) -> float:
        """Calculate confidence score based on multiple correlation dimensions."""
        
        # Weighted average of correlation scores
        weighted_sum = sum(
            score * self.correlation_weights.get(dim, 0.1) 
            for dim, score in correlation_scores.items()
        )
        
        total_weight = sum(
            self.correlation_weights.get(dim, 0.1) 
            for dim in correlation_scores.keys()
        )
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0


# Intelligent Failure Classification
# ==================================

class FailureClassificationEngine:
    """ML-powered failure analysis and classification system."""
    
    def __init__(self):
        self.failure_categories = [
            'syntax_error',
            'test_failure', 
            'dependency_conflict',
            'infrastructure_issue',
            'security_violation',
            'configuration_error',
            'performance_timeout',
            'external_service_failure'
        ]
        
        self.classifier = None
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.is_trained = False
        
        # Pre-defined patterns for rule-based classification
        self.error_patterns = {
            'syntax_error': [
                'SyntaxError', 'IndentationError', 'NameError',
                'compilation failed', 'parse error', 'syntax error'
            ],
            'test_failure': [
                'test failed', 'assertion error', 'AssertionError',
                'tests: 0 passed', 'FAILED', 'test suite failed'
            ],
            'dependency_conflict': [
                'dependency resolution failed', 'version conflict',
                'package not found', 'import error', 'module not found'
            ],
            'infrastructure_issue': [
                'connection timeout', 'network error', 'disk space',
                'out of memory', 'resource unavailable', 'connection refused'
            ],
            'security_violation': [
                'security scan failed', 'vulnerability detected',
                'license violation', 'secret detected', 'security policy'
            ],
            'configuration_error': [
                'configuration invalid', 'config error', 'environment variable',
                'missing configuration', 'yaml error', 'json error'
            ],
            'performance_timeout': [
                'timeout', 'killed', 'time limit exceeded',
                'execution timeout', 'build timeout', 'step timeout'
            ],
            'external_service_failure': [
                'service unavailable', 'api error', 'external service',
                'webhook failed', 'third party', 'upstream service'
            ]
        }
    
    async def classify_failure(self, failure_event: AdvancedCICDEvent) -> Dict[str, Any]:
        """Classify build/deployment failure and suggest fixes."""
        
        # Extract text for analysis
        failure_text = self._extract_failure_text(failure_event)
        
        if not failure_text:
            return self._create_unknown_classification()
            
        # Use rule-based classification as primary method
        rule_based_result = self._classify_by_patterns(failure_text)
        
        # Enhance with ML classification if model is trained
        ml_result = await self._classify_by_ml(failure_text) if self.is_trained else None
        
        # Combine results
        final_classification = self._combine_classifications(rule_based_result, ml_result)
        
        # Generate fix suggestions
        fix_suggestions = await self._generate_fix_suggestions(
            final_classification, failure_event
        )
        
        return {
            'category': final_classification['category'],
            'confidence': final_classification['confidence'],
            'subcategory': final_classification.get('subcategory'),
            'fix_suggestions': fix_suggestions,
            'analysis_methods': final_classification['methods'],
            'failure_text_snippet': failure_text[:200] + "..." if len(failure_text) > 200 else failure_text
        }
    
    def _extract_failure_text(self, event: AdvancedCICDEvent) -> str:
        """Extract relevant failure text from event."""
        text_parts = []
        
        if event.error_message:
            text_parts.append(event.error_message)
        if event.logs:
            # Focus on error-relevant parts of logs
            log_lines = event.logs.split('\n')
            error_lines = [
                line for line in log_lines 
                if any(keyword in line.lower() for keyword in ['error', 'failed', 'exception', 'timeout'])
            ]
            text_parts.extend(error_lines[:10])  # Limit to avoid too much noise
            
        return " ".join(text_parts)
    
    def _classify_by_patterns(self, failure_text: str) -> Dict[str, Any]:
        """Rule-based classification using predefined patterns."""
        
        failure_text_lower = failure_text.lower()
        category_scores = defaultdict(int)
        
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.lower() in failure_text_lower:
                    category_scores[category] += 1
                    
        if not category_scores:
            return {
                'category': 'unknown',
                'confidence': 0.1,
                'methods': ['pattern_matching']
            }
            
        best_category = max(category_scores.items(), key=lambda x: x[1])
        confidence = min(0.9, best_category[1] * 0.2)  # Cap at 0.9, scale by matches
        
        return {
            'category': best_category[0],
            'confidence': confidence,
            'methods': ['pattern_matching'],
            'pattern_matches': dict(category_scores)
        }
    
    async def _classify_by_ml(self, failure_text: str) -> Optional[Dict[str, Any]]:
        """ML-based classification (placeholder for actual ML model)."""
        
        if not self.is_trained:
            return None
            
        try:
            # This would use a trained ML model in production
            # For now, return a mock result
            features = self.vectorizer.transform([failure_text])
            
            # Mock prediction (replace with actual model.predict())
            prediction = np.random.choice(self.failure_categories)
            confidence = np.random.random() * 0.5 + 0.3  # Random confidence between 0.3-0.8
            
            return {
                'category': prediction,
                'confidence': confidence,
                'methods': ['ml_classification']
            }
            
        except Exception as e:
            logger.warning(f"ML classification failed: {e}")
            return None
    
    def _combine_classifications(self, 
                                rule_result: Dict[str, Any], 
                                ml_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine rule-based and ML classification results."""
        
        if not ml_result:
            return rule_result
            
        # If both methods agree, increase confidence
        if rule_result['category'] == ml_result['category']:
            combined_confidence = min(0.95, (rule_result['confidence'] + ml_result['confidence']) / 1.5)
            return {
                'category': rule_result['category'],
                'confidence': combined_confidence,
                'methods': rule_result['methods'] + ml_result['methods']
            }
        
        # If they disagree, use the one with higher confidence
        if rule_result['confidence'] > ml_result['confidence']:
            return rule_result
        else:
            return ml_result
    
    async def _generate_fix_suggestions(self, 
                                       classification: Dict[str, Any], 
                                       event: AdvancedCICDEvent) -> List[str]:
        """Generate actionable fix suggestions based on failure classification."""
        
        category = classification['category']
        
        suggestions = {
            'syntax_error': [
                "Review code changes for syntax errors",
                "Run local linting before committing",
                "Check for missing imports or typos"
            ],
            'test_failure': [
                "Run tests locally to reproduce the issue",
                "Check if test data or fixtures have changed",
                "Review recent code changes affecting test logic"
            ],
            'dependency_conflict': [
                "Update dependency versions in package files",
                "Clear dependency cache and reinstall",
                "Check for conflicting dependency versions"
            ],
            'infrastructure_issue': [
                "Check system resources (memory, disk space)",
                "Verify network connectivity",
                "Review infrastructure logs for issues"
            ],
            'security_violation': [
                "Review security scan results",
                "Update vulnerable dependencies",
                "Remove any accidentally committed secrets"
            ],
            'configuration_error': [
                "Validate configuration files",
                "Check environment variables",
                "Review deployment configuration"
            ],
            'performance_timeout': [
                "Optimize long-running operations",
                "Increase timeout limits if appropriate",
                "Review resource allocation"
            ],
            'external_service_failure': [
                "Check external service status",
                "Implement retry mechanisms",
                "Use circuit breakers for external calls"
            ],
            'unknown': [
                "Review full build logs for details",
                "Check recent changes that might have caused the issue",
                "Contact the development team for assistance"
            ]
        }
        
        return suggestions.get(category, suggestions['unknown'])
    
    def _create_unknown_classification(self) -> Dict[str, Any]:
        """Create classification for unknown failure types."""
        return {
            'category': 'unknown',
            'confidence': 0.1,
            'fix_suggestions': [
                "Review full build logs for error details",
                "Check recent code changes",
                "Consult team documentation or support"
            ],
            'analysis_methods': ['insufficient_data']
        }


# Cross-Platform Build Constellation
# ==================================

class BuildConstellationEngine:
    """Create and manage unified views of related builds across platforms."""
    
    def __init__(self, correlator: MultiDimensionalCorrelator):
        self.correlator = correlator
        self.active_constellations: Dict[str, BuildConstellation] = {}
        
    async def create_constellation(self, 
                                  primary_build: AdvancedCICDEvent,
                                  candidate_builds: List[AdvancedCICDEvent],
                                  correlation_threshold: float = 0.5) -> BuildConstellation:
        """Create a build constellation from related builds."""
        
        # Find correlations between primary build and candidates
        correlations = await self.correlator.correlate_events(
            primary_build, candidate_builds
        )
        
        # Filter builds that meet correlation threshold
        related_builds = []
        for correlation in correlations:
            if correlation.strength >= correlation_threshold:
                related_build = next(
                    (b for b in candidate_builds if b.event_id == correlation.target_event_id),
                    None
                )
                if related_build:
                    related_build.correlations.append(correlation)
                    related_builds.append(related_build)
        
        # Generate constellation ID
        constellation_id = self._generate_constellation_id(primary_build, related_builds)
        
        # Determine lifecycle stage and overall status
        lifecycle_stage = self._determine_lifecycle_stage(primary_build, related_builds)
        overall_status = self._calculate_overall_status(primary_build, related_builds)
        completion_percentage = self._calculate_completion_percentage(primary_build, related_builds)
        
        # Analyze performance and bottlenecks
        total_duration, bottlenecks, optimizations = await self._analyze_constellation_performance(
            primary_build, related_builds
        )
        
        constellation = BuildConstellation(
            constellation_id=constellation_id,
            primary_build=primary_build,
            related_builds=related_builds,
            lifecycle_stage=lifecycle_stage,
            overall_status=overall_status,
            completion_percentage=completion_percentage,
            total_duration_ms=total_duration,
            bottlenecks=bottlenecks,
            optimization_suggestions=optimizations
        )
        
        # Store active constellation
        self.active_constellations[constellation_id] = constellation
        
        return constellation
    
    def _generate_constellation_id(self, 
                                  primary: AdvancedCICDEvent, 
                                  related: List[AdvancedCICDEvent]) -> str:
        """Generate unique constellation ID based on build characteristics."""
        
        # Use commit SHA if available, otherwise use timestamp and primary build ID
        if primary.commit_sha:
            base_string = f"{primary.commit_sha}_{primary.branch_name or 'unknown'}"
        else:
            base_string = f"{primary.event_id}_{primary.timestamp.isoformat()}"
            
        return hashlib.md5(base_string.encode()).hexdigest()[:12]
    
    def _determine_lifecycle_stage(self, 
                                  primary: AdvancedCICDEvent, 
                                  related: List[AdvancedCICDEvent]) -> str:
        """Determine the current lifecycle stage of the constellation."""
        
        all_builds = [primary] + related
        
        # Check for different event types to determine stage
        event_types = {build.event_type.lower() for build in all_builds}
        
        if any('deploy' in et for et in event_types):
            return 'deploying'
        elif any('test' in et for et in event_types):
            return 'testing'
        elif any('build' in et or 'workflow' in et for et in event_types):
            return 'building'
        else:
            return 'completed'
    
    def _calculate_overall_status(self, 
                                 primary: AdvancedCICDEvent, 
                                 related: List[AdvancedCICDEvent]) -> str:
        """Calculate overall constellation status."""
        
        all_builds = [primary] + related
        
        # Check if any builds are still in progress
        if any(build.status in ['running', 'pending', 'in_progress'] for build in all_builds):
            return 'in_progress'
        
        # Check if any builds failed
        if any(build.status in ['failed', 'failure'] or build.conclusion == 'failure' for build in all_builds):
            return 'failure'
        
        # Check if all completed builds succeeded
        completed_builds = [b for b in all_builds if b.status not in ['running', 'pending', 'in_progress']]
        if all(build.status in ['success', 'completed'] or build.conclusion == 'success' for build in completed_builds):
            return 'success'
        
        return 'mixed'
    
    def _calculate_completion_percentage(self, 
                                       primary: AdvancedCICDEvent, 
                                       related: List[AdvancedCICDEvent]) -> float:
        """Calculate completion percentage for the constellation."""
        
        all_builds = [primary] + related
        completed_builds = [
            build for build in all_builds 
            if build.status not in ['running', 'pending', 'in_progress']
        ]
        
        if not all_builds:
            return 0.0
            
        return len(completed_builds) / len(all_builds) * 100.0
    
    async def _analyze_constellation_performance(self, 
                                               primary: AdvancedCICDEvent, 
                                               related: List[AdvancedCICDEvent]) -> Tuple[Optional[int], List[str], List[str]]:
        """Analyze constellation performance and identify bottlenecks."""
        
        all_builds = [primary] + related
        
        # Calculate total duration
        durations = [build.duration_ms for build in all_builds if build.duration_ms]
        total_duration = sum(durations) if durations else None
        
        # Identify bottlenecks (builds taking significantly longer than average)
        bottlenecks = []
        if durations:
            avg_duration = sum(durations) / len(durations)
            for build in all_builds:
                if build.duration_ms and build.duration_ms > avg_duration * 1.5:
                    bottlenecks.append(f"{build.platform}:{build.pipeline_id} ({build.duration_ms}ms)")
        
        # Generate optimization suggestions
        optimizations = []
        if bottlenecks:
            optimizations.append("Consider optimizing slow builds identified in bottlenecks")
        
        if len(all_builds) > 1:
            optimizations.append("Evaluate if some builds can be run in parallel")
        
        # Check for redundant builds
        platforms = [build.platform for build in all_builds]
        if len(set(platforms)) < len(platforms):
            optimizations.append("Review for potentially redundant builds on same platform")
        
        return total_duration, bottlenecks, optimizations


# Real-time Event Processing Orchestrator
# =======================================

class AdvancedCICDOrchestrator:
    """Advanced orchestration system for real-time CI/CD event processing."""
    
    def __init__(self):
        self.correlator = MultiDimensionalCorrelator()
        self.failure_classifier = FailureClassificationEngine()
        self.constellation_engine = BuildConstellationEngine(self.correlator)
        
        # Event storage and processing
        self.event_cache = deque(maxlen=1000)  # Keep recent events for correlation
        self.processing_queue = asyncio.Queue()
        
        # Performance metrics
        self.metrics = {
            'events_processed': 0,
            'correlations_detected': 0,
            'constellations_created': 0,
            'failures_classified': 0,
            'processing_times': deque(maxlen=100)
        }
        
        # Processing workers
        self.workers: List[asyncio.Task] = []
        self.running = False
        
    async def start_processing(self, num_workers: int = 5):
        """Start the processing workers."""
        
        if self.running:
            return
            
        self.running = True
        
        # Start processing workers
        for i in range(num_workers):
            worker = asyncio.create_task(self._processing_worker(f"worker-{i}"))
            self.workers.append(worker)
            
        logger.info(f"Started {num_workers} processing workers")
    
    async def stop_processing(self):
        """Stop all processing workers."""
        
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
            
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Stopped all processing workers")
    
    async def process_event(self, event: AdvancedCICDEvent):
        """Queue an event for processing."""
        
        await self.processing_queue.put(event)
    
    async def _processing_worker(self, worker_id: str):
        """Worker coroutine for processing events."""
        
        logger.info(f"Started processing worker: {worker_id}")
        
        while self.running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=1.0
                )
                
                start_time = time.time()
                
                # Process the event
                await self._process_single_event(event)
                
                # Record processing time
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                self.metrics['processing_times'].append(processing_time)
                self.metrics['events_processed'] += 1
                
            except asyncio.TimeoutError:
                # No events to process, continue
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                
        logger.info(f"Stopped processing worker: {worker_id}")
    
    async def _process_single_event(self, event: AdvancedCICDEvent):
        """Process a single CI/CD event with full analysis."""
        
        # Add event to cache for correlation analysis
        self.event_cache.append(event)
        
        # 1. Find correlations with recent events
        correlations = await self.correlator.correlate_events(
            event, 
            list(self.event_cache)[:-1]  # Exclude the current event
        )
        
        if correlations:
            self.metrics['correlations_detected'] += len(correlations)
            event.correlations = correlations
            logger.info(f"Found {len(correlations)} correlations for event {event.event_id}")
        
        # 2. Classify failures if this is a failed build/deployment
        if event.status in ['failed', 'failure'] or event.conclusion == 'failure':
            classification = await self.failure_classifier.classify_failure(event)
            event.raw_payload['failure_classification'] = classification
            self.metrics['failures_classified'] += 1
            
            logger.info(f"Classified failure: {classification['category']} (confidence: {classification['confidence']:.2f})")
        
        # 3. Create or update build constellation
        if correlations or event.commit_sha:
            # Get related events for constellation building
            related_events = [
                cached_event for cached_event in self.event_cache
                if cached_event.event_id != event.event_id and (
                    cached_event.commit_sha == event.commit_sha or
                    any(c.target_event_id == cached_event.event_id for c in correlations)
                )
            ]
            
            if related_events:
                constellation = await self.constellation_engine.create_constellation(
                    event, related_events
                )
                event.constellation_id = constellation.constellation_id
                self.metrics['constellations_created'] += 1
                
                logger.info(f"Created constellation {constellation.constellation_id} with {len(related_events)} related builds")
        
        # 4. Trigger real-time notifications/updates (placeholder)
        await self._notify_event_processed(event)
    
    async def _notify_event_processed(self, event: AdvancedCICDEvent):
        """Send real-time notifications about processed event."""
        
        # This would integrate with WebSocket connections, message queues, etc.
        # For now, just log the notification
        
        notification_data = {
            'event_id': event.event_id,
            'platform': event.platform,
            'status': event.status,
            'correlations_count': len(event.correlations),
            'constellation_id': event.constellation_id,
            'timestamp': event.timestamp.isoformat()
        }
        
        logger.info(f"Event processed notification: {notification_data}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        
        processing_times = list(self.metrics['processing_times'])
        
        return {
            'events_processed': self.metrics['events_processed'],
            'correlations_detected': self.metrics['correlations_detected'],
            'constellations_created': self.metrics['constellations_created'],
            'failures_classified': self.metrics['failures_classified'],
            'average_processing_time_ms': sum(processing_times) / len(processing_times) if processing_times else 0,
            'queue_size': self.processing_queue.qsize(),
            'workers_active': len([w for w in self.workers if not w.done()]),
            'cache_size': len(self.event_cache)
        }


# Example Usage and Testing
# ========================

async def main():
    """Demonstrate the advanced CI/CD integration patterns."""
    
    # Initialize the orchestrator
    orchestrator = AdvancedCICDOrchestrator()
    await orchestrator.start_processing(num_workers=3)
    
    try:
        # Create sample events
        sample_events = [
            AdvancedCICDEvent(
                event_id="gh-001",
                platform="github_actions",
                event_type="workflow_run",
                timestamp=datetime.utcnow(),
                pipeline_id="build-main",
                commit_sha="abc123def456",
                branch_name="main",
                author="developer1",
                duration_ms=120000,
                status="success"
            ),
            AdvancedCICDEvent(
                event_id="gl-001",
                platform="gitlab_ci",
                event_type="pipeline",
                timestamp=datetime.utcnow() + timedelta(minutes=2),
                pipeline_id="deploy-main",
                commit_sha="abc123def456",
                branch_name="main",
                author="developer1",
                duration_ms=180000,
                status="failed",
                error_message="Deployment failed: connection timeout to production server",
                logs="ERROR: Unable to connect to server production-01:8080\nTimeout after 30 seconds\nDeployment aborted"
            ),
            AdvancedCICDEvent(
                event_id="jen-001",
                platform="jenkins",
                event_type="build",
                timestamp=datetime.utcnow() + timedelta(minutes=5),
                pipeline_id="integration-tests",
                commit_sha="abc123def456",
                branch_name="main",
                author="developer1",
                duration_ms=300000,
                status="success"
            )
        ]
        
        # Process events
        for event in sample_events:
            await orchestrator.process_event(event)
        
        # Wait for processing to complete
        await asyncio.sleep(2)
        
        # Show processing statistics
        stats = orchestrator.get_processing_stats()
        print("\n=== Processing Statistics ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Show constellation information
        print("\n=== Active Constellations ===")
        for constellation_id, constellation in orchestrator.constellation_engine.active_constellations.items():
            print(f"Constellation {constellation_id}:")
            print(f"  Primary Build: {constellation.primary_build.platform}:{constellation.primary_build.pipeline_id}")
            print(f"  Related Builds: {len(constellation.related_builds)}")
            print(f"  Status: {constellation.overall_status}")
            print(f"  Stage: {constellation.lifecycle_stage}")
            print(f"  Completion: {constellation.completion_percentage:.1f}%")
            if constellation.bottlenecks:
                print(f"  Bottlenecks: {', '.join(constellation.bottlenecks)}")
            if constellation.optimization_suggestions:
                print(f"  Optimizations: {', '.join(constellation.optimization_suggestions)}")
            print()
        
    finally:
        await orchestrator.stop_processing()


if __name__ == "__main__":
    asyncio.run(main())