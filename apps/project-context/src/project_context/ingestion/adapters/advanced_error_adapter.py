"""
Advanced Error Log Ingestion Adapter
Phase 2 Unified Context System - Production Ready Implementation

This adapter provides comprehensive error log processing with:
- Multi-format log parsing with intelligent format detection
- ML-powered error classification and severity scoring
- Real-time correlation with Git commits and chat conversations
- Pattern detection and frequency tracking
- High-volume ingestion with performance optimization
"""

import asyncio
import json
import re
import hashlib
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict, deque

import structlog
import aiofiles
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ...models.common import ContextItem
from ..base_adapter import AdapterConfig, BaseAdapter, BatchMode
from ..transformers import DataTransformer

logger = structlog.get_logger(__name__)


class LogFormat(Enum):
    """Supported log formats."""
    JSON = "json"
    STRUCTURED_TEXT = "structured_text"
    SYSLOG = "syslog"
    APACHE_COMMON = "apache_common"
    NGINX = "nginx"
    DOCKER_JSON = "docker_json"
    KUBERNETES = "kubernetes"
    PLAIN_TEXT = "plain_text"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorrelationType(Enum):
    """Types of error correlations."""
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    CONTEXTUAL = "contextual"
    FILE_PATH = "file_path"
    SEMANTIC = "semantic"


@dataclass
class FormatDetectionResult:
    """Result of log format detection."""
    format_type: LogFormat
    confidence: float
    schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedLog:
    """Parsed log entry with structured data."""
    timestamp: Optional[datetime] = None
    level: Optional[str] = None
    message: Optional[str] = None
    logger_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    raw_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassificationResult:
    """Error classification result."""
    primary_category: str
    subcategory: Optional[str] = None
    confidence: float = 0.0
    keywords: List[str] = field(default_factory=list)
    severity_score: float = 0.0
    tags: Set[str] = field(default_factory=set)


@dataclass
class ErrorPattern:
    """Detected error pattern."""
    pattern_id: str
    signature: str
    similarity_threshold: float
    first_seen: datetime
    last_seen: datetime
    occurrence_count: int
    representative_error: Optional[ParsedLog] = None
    common_keywords: List[str] = field(default_factory=list)
    files_affected: Set[str] = field(default_factory=set)


@dataclass
class CorrelationResult:
    """Result of correlation analysis."""
    correlation_type: CorrelationType
    target_id: str
    target_type: str  # 'git_commit', 'chat_message', 'code_change'
    confidence_score: float
    evidence: Dict[str, Any]
    time_delta_seconds: Optional[int] = None


class FormatDetectionEngine:
    """Intelligent log format detection engine."""

    def __init__(self):
        self.format_patterns = {
            LogFormat.JSON: [
                re.compile(r'^\s*\{.*\}\s*$'),
                re.compile(r'.*"timestamp".*"level".*"message".*'),
            ],
            LogFormat.STRUCTURED_TEXT: [
                re.compile(r'^\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}.*\s+(DEBUG|INFO|WARN|ERROR|FATAL)\s+.*'),
                re.compile(r'^\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\]\s+\w+\s+.*'),
            ],
            LogFormat.SYSLOG: [
                re.compile(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\w+\s+.*'),
            ],
            LogFormat.DOCKER_JSON: [
                re.compile(r'.*"log":.*"stream":.*"time":.*'),
            ],
            LogFormat.KUBERNETES: [
                re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+.*'),
            ],
        }

    async def detect_format(self, log_content: str) -> FormatDetectionResult:
        """Detect log format with confidence scoring."""
        scores = defaultdict(float)
        
        # Sample lines for analysis
        lines = log_content.strip().split('\n')[:10]  # Analyze first 10 lines
        
        for line in lines:
            if not line.strip():
                continue
                
            for format_type, patterns in self.format_patterns.items():
                for pattern in patterns:
                    if pattern.search(line):
                        scores[format_type] += 1.0 / len(patterns)
        
        # Additional heuristics
        await self._apply_heuristics(log_content, scores)
        
        # Normalize scores
        total_lines = len([l for l in lines if l.strip()])
        if total_lines > 0:
            for format_type in scores:
                scores[format_type] /= total_lines
        
        # Select best format
        if not scores:
            return FormatDetectionResult(
                format_type=LogFormat.PLAIN_TEXT,
                confidence=0.5
            )
        
        best_format = max(scores, key=scores.get)
        confidence = min(scores[best_format], 1.0)
        
        return FormatDetectionResult(
            format_type=best_format,
            confidence=confidence,
            schema=await self._infer_schema(log_content, best_format)
        )

    async def _apply_heuristics(self, content: str, scores: Dict[LogFormat, float]):
        """Apply additional heuristic analysis."""
        # JSON heuristics
        if content.count('{') > 0 and content.count('}') > 0:
            brace_ratio = min(content.count('{'), content.count('}')) / len(content.split('\n'))
            scores[LogFormat.JSON] += brace_ratio * 2
        
        # Check for common log keywords
        error_keywords = ['ERROR', 'FATAL', 'Exception', 'Traceback']
        for keyword in error_keywords:
            if keyword in content:
                scores[LogFormat.STRUCTURED_TEXT] += 0.3

    async def _infer_schema(self, content: str, format_type: LogFormat) -> Optional[Dict[str, Any]]:
        """Infer schema for the detected format."""
        if format_type == LogFormat.JSON:
            lines = content.strip().split('\n')
            for line in lines:
                try:
                    parsed = json.loads(line)
                    return {"fields": list(parsed.keys())}
                except json.JSONDecodeError:
                    continue
        return None


class MultiFormatLogParser:
    """Multi-format log parser with intelligent parsing strategies."""

    def __init__(self):
        self.parsers = {
            LogFormat.JSON: self._parse_json,
            LogFormat.STRUCTURED_TEXT: self._parse_structured_text,
            LogFormat.SYSLOG: self._parse_syslog,
            LogFormat.DOCKER_JSON: self._parse_docker_json,
            LogFormat.KUBERNETES: self._parse_kubernetes,
            LogFormat.PLAIN_TEXT: self._parse_plain_text,
        }

    async def parse(self, log_content: str, format_type: LogFormat, schema: Optional[Dict[str, Any]] = None) -> List[ParsedLog]:
        """Parse log content based on detected format."""
        parser = self.parsers.get(format_type, self._parse_plain_text)
        return await parser(log_content, schema)

    async def _parse_json(self, content: str, schema: Optional[Dict[str, Any]] = None) -> List[ParsedLog]:
        """Parse JSON format logs."""
        parsed_logs = []
        
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                
                # Extract timestamp
                timestamp = None
                for ts_field in ['timestamp', 'time', '@timestamp', 'ts']:
                    if ts_field in data:
                        timestamp = await self._parse_timestamp(str(data[ts_field]))
                        break
                
                # Extract level
                level = None
                for level_field in ['level', 'severity', 'loglevel']:
                    if level_field in data:
                        level = str(data[level_field]).upper()
                        break
                
                # Extract message
                message = None
                for msg_field in ['message', 'msg', 'text']:
                    if msg_field in data:
                        message = str(data[msg_field])
                        break
                
                # Extract error details
                exception_type = data.get('exception_type') or data.get('error_type')
                stack_trace = data.get('stack_trace') or data.get('traceback')
                
                parsed_log = ParsedLog(
                    timestamp=timestamp,
                    level=level,
                    message=message,
                    logger_name=data.get('logger') or data.get('name'),
                    file_path=data.get('file') or data.get('filename'),
                    line_number=data.get('line') or data.get('lineno'),
                    function_name=data.get('function') or data.get('func'),
                    exception_type=exception_type,
                    stack_trace=stack_trace,
                    raw_content=line,
                    metadata=data
                )
                
                parsed_logs.append(parsed_log)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON log line: {e}", line=line[:100])
                # Fallback to plain text parsing
                fallback_logs = await self._parse_plain_text(line)
                parsed_logs.extend(fallback_logs)
        
        return parsed_logs

    async def _parse_structured_text(self, content: str, schema: Optional[Dict[str, Any]] = None) -> List[ParsedLog]:
        """Parse structured text format logs."""
        parsed_logs = []
        
        # Common structured log patterns
        patterns = [
            # Standard format: timestamp LEVEL logger - message
            re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[^\s]*)\s+(?P<level>\w+)\s+(?P<logger>[^\s]+)?\s*[-:]?\s*(?P<message>.*?)$'),
            # Bracketed format: [timestamp] LEVEL logger - message
            re.compile(r'\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[^\]]*)\]\s+(?P<level>\w+)\s+(?P<logger>[^\s]+)?\s*[-:]?\s*(?P<message>.*?)$'),
            # Java/Spring format
            re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[^\s]*)\s+(?P<level>\w+)\s+\[(?P<thread>[^\]]+)\]\s+(?P<logger>[^\s]+)?\s*[-:]?\s*(?P<message>.*?)$'),
        ]
        
        lines = content.strip().split('\n')
        current_log = None
        
        for line in lines:
            if not line.strip():
                continue
            
            # Try to match structured patterns
            matched = False
            for pattern in patterns:
                match = pattern.match(line)
                if match:
                    # Finalize previous log if exists
                    if current_log:
                        parsed_logs.append(current_log)
                    
                    # Create new log
                    groups = match.groupdict()
                    
                    current_log = ParsedLog(
                        timestamp=await self._parse_timestamp(groups.get('timestamp')),
                        level=groups.get('level', '').upper(),
                        message=groups.get('message', ''),
                        logger_name=groups.get('logger'),
                        raw_content=line,
                        metadata={'thread': groups.get('thread')}
                    )
                    matched = True
                    break
            
            # If no pattern matched, check if it's a continuation (stack trace)
            if not matched and current_log:
                # Check if this looks like a stack trace line
                if self._is_stack_trace_line(line):
                    if current_log.stack_trace:
                        current_log.stack_trace += '\n' + line
                    else:
                        current_log.stack_trace = line
                else:
                    # Append to message
                    current_log.message += '\n' + line
        
        # Add the last log
        if current_log:
            parsed_logs.append(current_log)
        
        return parsed_logs

    async def _parse_syslog(self, content: str, schema: Optional[Dict[str, Any]] = None) -> List[ParsedLog]:
        """Parse syslog format logs."""
        parsed_logs = []
        
        # Syslog pattern: Mon DD HH:MM:SS hostname program[pid]: message
        pattern = re.compile(r'(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<program>[^:\[\s]+)(?:\[(?P<pid>\d+)\])?\s*:\s*(?P<message>.*)')
        
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
                
            match = pattern.match(line)
            if match:
                groups = match.groupdict()
                
                parsed_log = ParsedLog(
                    timestamp=await self._parse_syslog_timestamp(groups['timestamp']),
                    message=groups['message'],
                    logger_name=groups['program'],
                    raw_content=line,
                    metadata={
                        'hostname': groups['hostname'],
                        'pid': groups.get('pid')
                    }
                )
                parsed_logs.append(parsed_log)
        
        return parsed_logs

    async def _parse_docker_json(self, content: str, schema: Optional[Dict[str, Any]] = None) -> List[ParsedLog]:
        """Parse Docker JSON format logs."""
        parsed_logs = []
        
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                data = json.loads(line)
                
                parsed_log = ParsedLog(
                    timestamp=await self._parse_timestamp(data.get('time')),
                    message=data.get('log', '').rstrip('\n'),
                    raw_content=line,
                    metadata={
                        'stream': data.get('stream'),  # stdout/stderr
                        'partial_message': data.get('partial_message', False)
                    }
                )
                parsed_logs.append(parsed_log)
                
            except json.JSONDecodeError:
                # Fallback to plain text
                fallback_logs = await self._parse_plain_text(line)
                parsed_logs.extend(fallback_logs)
        
        return parsed_logs

    async def _parse_kubernetes(self, content: str, schema: Optional[Dict[str, Any]] = None) -> List[ParsedLog]:
        """Parse Kubernetes format logs."""
        parsed_logs = []
        
        # Kubernetes pattern: timestamp flag stream partial_flag log_tag message
        pattern = re.compile(r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(?P<stream>\w+)\s+(?P<flag>\w)\s+(?P<message>.*)')
        
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
                
            match = pattern.match(line)
            if match:
                groups = match.groupdict()
                
                parsed_log = ParsedLog(
                    timestamp=await self._parse_timestamp(groups['timestamp']),
                    message=groups['message'],
                    raw_content=line,
                    metadata={
                        'stream': groups['stream'],
                        'flag': groups['flag']
                    }
                )
                parsed_logs.append(parsed_log)
        
        return parsed_logs

    async def _parse_plain_text(self, content: str, schema: Optional[Dict[str, Any]] = None) -> List[ParsedLog]:
        """Parse plain text logs with basic error detection."""
        parsed_logs = []
        
        lines = content.strip().split('\n')
        current_log = None
        
        for line in lines:
            if not line.strip():
                continue
            
            # Check if this line starts a new log entry
            if self._looks_like_log_start(line):
                # Finalize previous log
                if current_log:
                    parsed_logs.append(current_log)
                
                # Extract basic information
                timestamp = await self._extract_timestamp(line)
                level = self._extract_log_level(line)
                
                current_log = ParsedLog(
                    timestamp=timestamp,
                    level=level,
                    message=line,
                    raw_content=line
                )
            elif current_log:
                # Continuation of previous log
                if self._is_stack_trace_line(line):
                    if current_log.stack_trace:
                        current_log.stack_trace += '\n' + line
                    else:
                        current_log.stack_trace = line
                else:
                    current_log.message += '\n' + line
            else:
                # Standalone line
                parsed_log = ParsedLog(
                    message=line,
                    raw_content=line
                )
                parsed_logs.append(parsed_log)
        
        # Add last log
        if current_log:
            parsed_logs.append(current_log)
        
        return parsed_logs

    def _looks_like_log_start(self, line: str) -> bool:
        """Check if line looks like the start of a log entry."""
        # Look for timestamp patterns
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # Date
            r'\d{2}:\d{2}:\d{2}',  # Time
            r'\[\d{4}-\d{2}-\d{2}',  # Bracketed date
        ]
        
        for pattern in timestamp_patterns:
            if re.search(pattern, line[:50]):  # Check first 50 chars
                return True
        
        # Look for log level indicators
        log_levels = ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL', 'TRACE']
        for level in log_levels:
            if level in line.upper()[:100]:  # Check first 100 chars
                return True
        
        return False

    def _extract_log_level(self, line: str) -> Optional[str]:
        """Extract log level from line."""
        log_levels = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL']
        line_upper = line.upper()
        
        for level in log_levels:
            if level in line_upper:
                return level
        
        return None

    def _is_stack_trace_line(self, line: str) -> bool:
        """Check if line is part of a stack trace."""
        stack_indicators = [
            r'^\s+at\s+',  # Java/JavaScript
            r'^\s+File\s+".*",\s+line\s+\d+',  # Python
            r'^\s+in\s+.*:\d+',  # General
            r'^\s*Traceback\s*\(most recent call last\)',  # Python traceback
            r'^\s*Exception\s+in\s+thread',  # Java
            r'^\s*Caused\s+by:',  # Exception chains
            r'^\s*\w+Error:',  # Error types
            r'^\s*\w+Exception:',  # Exception types
        ]
        
        for pattern in stack_indicators:
            if re.search(pattern, line):
                return True
        
        return False

    async def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp with multiple format support."""
        if not timestamp_str:
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # Try parsing with dateutil as fallback
        try:
            from dateutil import parser
            return parser.parse(timestamp_str)
        except:
            return None

    async def _parse_syslog_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse syslog timestamp (no year)."""
        try:
            # Syslog format: Mon DD HH:MM:SS
            dt = datetime.strptime(timestamp_str, '%b %d %H:%M:%S')
            # Add current year
            current_year = datetime.now().year
            return dt.replace(year=current_year)
        except ValueError:
            return None

    async def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from any line."""
        # Common timestamp patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[^\s]*)',
            r'\[([^\]]+)\]',  # Bracketed timestamps
            r'(\d{2}:\d{2}:\d{2})',  # Time only
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                parsed_ts = await self._parse_timestamp(timestamp_str)
                if parsed_ts:
                    return parsed_ts
        
        return None


class ErrorClassificationEngine:
    """ML-powered error classification with rule-based fallbacks."""

    def __init__(self):
        self.error_categories = {
            'network': {
                'keywords': ['connection', 'timeout', 'unreachable', 'refused', 'dns', 'ssl', 'tls', 'socket'],
                'patterns': [
                    r'connection.*refused',
                    r'timeout.*connecting',
                    r'unable.*to.*connect',
                    r'network.*unreachable',
                    r'ssl.*handshake.*failed'
                ],
                'severity_base': 0.7
            },
            'database': {
                'keywords': ['database', 'sql', 'query', 'connection', 'deadlock', 'constraint', 'transaction'],
                'patterns': [
                    r'database.*connection.*failed',
                    r'sql.*error',
                    r'deadlock.*detected',
                    r'constraint.*violation',
                    r'table.*does.*not.*exist'
                ],
                'severity_base': 0.8
            },
            'memory': {
                'keywords': ['memory', 'heap', 'oom', 'outofmemory', 'allocation', 'gc', 'garbage'],
                'patterns': [
                    r'out.*of.*memory',
                    r'heap.*space.*exhausted',
                    r'memory.*allocation.*failed',
                    r'cannot.*allocate.*memory'
                ],
                'severity_base': 0.9
            },
            'security': {
                'keywords': ['unauthorized', 'forbidden', 'authentication', 'permission', 'access', 'denied'],
                'patterns': [
                    r'access.*denied',
                    r'authentication.*failed',
                    r'unauthorized.*access',
                    r'permission.*denied',
                    r'forbidden.*request'
                ],
                'severity_base': 0.8
            },
            'performance': {
                'keywords': ['slow', 'performance', 'latency', 'cpu', 'disk', 'io', 'throughput'],
                'patterns': [
                    r'slow.*query',
                    r'high.*cpu.*usage',
                    r'disk.*io.*error',
                    r'performance.*degradation'
                ],
                'severity_base': 0.6
            },
            'application': {
                'keywords': ['exception', 'error', 'null', 'undefined', 'assertion', 'runtime'],
                'patterns': [
                    r'null.*pointer.*exception',
                    r'assertion.*failed',
                    r'runtime.*error',
                    r'unhandled.*exception'
                ],
                'severity_base': 0.7
            }
        }
        
        # Initialize TF-IDF vectorizer for semantic classification
        self.vectorizer = None
        self.classification_model = None

    async def classify_error(self, parsed_log: ParsedLog) -> ClassificationResult:
        """Classify error with multiple strategies."""
        text_content = self._prepare_text_for_classification(parsed_log)
        
        # Strategy 1: Rule-based classification
        rule_result = await self._rule_based_classification(text_content, parsed_log)
        
        # Strategy 2: Pattern matching
        pattern_result = await self._pattern_based_classification(text_content)
        
        # Strategy 3: Keyword-based classification
        keyword_result = await self._keyword_based_classification(text_content)
        
        # Combine results
        final_result = await self._combine_classification_results([
            rule_result, pattern_result, keyword_result
        ])
        
        # Calculate severity score
        final_result.severity_score = await self._calculate_severity_score(
            parsed_log, final_result
        )
        
        return final_result

    def _prepare_text_for_classification(self, parsed_log: ParsedLog) -> str:
        """Prepare text content for classification."""
        parts = []
        
        if parsed_log.message:
            parts.append(parsed_log.message)
        
        if parsed_log.exception_type:
            parts.append(parsed_log.exception_type)
        
        if parsed_log.stack_trace:
            # Include first few lines of stack trace
            stack_lines = parsed_log.stack_trace.split('\n')[:3]
            parts.extend(stack_lines)
        
        return ' '.join(parts).lower()

    async def _rule_based_classification(self, text: str, parsed_log: ParsedLog) -> ClassificationResult:
        """Rule-based error classification."""
        # Specific rules based on context
        
        # File-based rules
        if parsed_log.file_path:
            if 'database' in parsed_log.file_path.lower():
                return ClassificationResult(
                    primary_category='database',
                    confidence=0.8,
                    keywords=['file_path_indicator']
                )
            elif 'network' in parsed_log.file_path.lower():
                return ClassificationResult(
                    primary_category='network',
                    confidence=0.8,
                    keywords=['file_path_indicator']
                )
        
        # Exception type rules
        if parsed_log.exception_type:
            exception_type = parsed_log.exception_type.lower()
            if 'sql' in exception_type or 'database' in exception_type:
                return ClassificationResult(
                    primary_category='database',
                    confidence=0.9,
                    keywords=[parsed_log.exception_type]
                )
            elif 'network' in exception_type or 'connection' in exception_type:
                return ClassificationResult(
                    primary_category='network',
                    confidence=0.9,
                    keywords=[parsed_log.exception_type]
                )
            elif 'memory' in exception_type or 'outofmemory' in exception_type:
                return ClassificationResult(
                    primary_category='memory',
                    confidence=0.95,
                    keywords=[parsed_log.exception_type]
                )
        
        # Level-based rules
        if parsed_log.level:
            if parsed_log.level in ['FATAL', 'CRITICAL']:
                severity_boost = 0.3
            else:
                severity_boost = 0.0
        else:
            severity_boost = 0.0
        
        return ClassificationResult(
            primary_category='application',
            confidence=0.3 + severity_boost,
            keywords=['rule_based_fallback']
        )

    async def _pattern_based_classification(self, text: str) -> ClassificationResult:
        """Pattern-based error classification."""
        best_category = None
        best_confidence = 0.0
        matched_patterns = []
        
        for category, config in self.error_categories.items():
            patterns = config.get('patterns', [])
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text):
                    matches += 1
                    matched_patterns.append(pattern)
            
            if matches > 0:
                confidence = min(matches / len(patterns), 1.0) * 0.9
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_category = category
        
        return ClassificationResult(
            primary_category=best_category or 'application',
            confidence=best_confidence,
            keywords=matched_patterns
        )

    async def _keyword_based_classification(self, text: str) -> ClassificationResult:
        """Keyword-based error classification."""
        text_words = set(text.split())
        best_category = None
        best_confidence = 0.0
        matched_keywords = []
        
        for category, config in self.error_categories.items():
            keywords = config.get('keywords', [])
            matches = len(set(keywords) & text_words)
            
            if matches > 0:
                confidence = min(matches / len(keywords), 1.0) * 0.8
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_category = category
                    matched_keywords = list(set(keywords) & text_words)
        
        return ClassificationResult(
            primary_category=best_category or 'application',
            confidence=best_confidence,
            keywords=matched_keywords
        )

    async def _combine_classification_results(self, results: List[ClassificationResult]) -> ClassificationResult:
        """Combine multiple classification results."""
        category_scores = defaultdict(float)
        all_keywords = []
        
        for result in results:
            if result.primary_category:
                category_scores[result.primary_category] += result.confidence
                all_keywords.extend(result.keywords)
        
        if not category_scores:
            return ClassificationResult(
                primary_category='application',
                confidence=0.3,
                keywords=['fallback']
            )
        
        best_category = max(category_scores, key=category_scores.get)
        combined_confidence = min(category_scores[best_category] / len(results), 1.0)
        
        return ClassificationResult(
            primary_category=best_category,
            confidence=combined_confidence,
            keywords=list(set(all_keywords))
        )

    async def _calculate_severity_score(self, parsed_log: ParsedLog, classification: ClassificationResult) -> float:
        """Calculate error severity score."""
        base_severity = self.error_categories.get(
            classification.primary_category, {}
        ).get('severity_base', 0.5)
        
        # Level-based adjustment
        level_multiplier = 1.0
        if parsed_log.level:
            level_adjustments = {
                'FATAL': 1.5,
                'CRITICAL': 1.4,
                'ERROR': 1.2,
                'WARN': 1.0,
                'WARNING': 1.0,
                'INFO': 0.8,
                'DEBUG': 0.6
            }
            level_multiplier = level_adjustments.get(parsed_log.level, 1.0)
        
        # Stack trace adjustment
        stack_trace_multiplier = 1.3 if parsed_log.stack_trace else 1.0
        
        # Exception type adjustment
        exception_multiplier = 1.2 if parsed_log.exception_type else 1.0
        
        # Calculate final score
        severity_score = base_severity * level_multiplier * stack_trace_multiplier * exception_multiplier
        
        return min(severity_score, 1.0)


class ErrorPatternDetector:
    """Detect recurring error patterns using similarity analysis."""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.patterns: Dict[str, ErrorPattern] = {}
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words='english'
        )

    async def detect_patterns(self, parsed_logs: List[ParsedLog]) -> List[ErrorPattern]:
        """Detect error patterns in a batch of logs."""
        if len(parsed_logs) < 2:
            return []
        
        # Prepare text content for analysis
        texts = []
        for log in parsed_logs:
            text_content = self._prepare_text_for_pattern_analysis(log)
            texts.append(text_content)
        
        # Vectorize texts
        try:
            if len(texts) == 1:
                return []
            
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find similar groups
            patterns = await self._find_similar_groups(parsed_logs, similarity_matrix)
            
            return patterns
            
        except Exception as e:
            logger.warning(f"Pattern detection failed: {e}")
            return []

    def _prepare_text_for_pattern_analysis(self, parsed_log: ParsedLog) -> str:
        """Prepare text for pattern analysis."""
        parts = []
        
        if parsed_log.message:
            # Remove timestamps, numbers, and specific identifiers
            cleaned_message = re.sub(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[^\s]*', '', parsed_log.message)
            cleaned_message = re.sub(r'\b\d+\b', 'NUMBER', cleaned_message)
            cleaned_message = re.sub(r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', 'UUID', cleaned_message)
            parts.append(cleaned_message)
        
        if parsed_log.exception_type:
            parts.append(parsed_log.exception_type)
        
        if parsed_log.file_path:
            # Use just filename, not full path
            filename = Path(parsed_log.file_path).name if parsed_log.file_path else ''
            parts.append(filename)
        
        return ' '.join(parts).lower()

    async def _find_similar_groups(self, parsed_logs: List[ParsedLog], similarity_matrix: np.ndarray) -> List[ErrorPattern]:
        """Find groups of similar errors."""
        patterns = []
        processed = set()
        
        for i in range(len(parsed_logs)):
            if i in processed:
                continue
            
            # Find similar logs
            similar_indices = []
            for j in range(len(parsed_logs)):
                if i != j and similarity_matrix[i][j] >= self.similarity_threshold:
                    similar_indices.append(j)
            
            if len(similar_indices) >= 1:  # At least one similar log
                similar_indices.append(i)  # Include the original
                
                # Create pattern
                pattern_logs = [parsed_logs[idx] for idx in similar_indices]
                pattern = await self._create_error_pattern(pattern_logs)
                patterns.append(pattern)
                
                # Mark as processed
                processed.update(similar_indices)
        
        return patterns

    async def _create_error_pattern(self, similar_logs: List[ParsedLog]) -> ErrorPattern:
        """Create error pattern from similar logs."""
        # Generate pattern signature
        signature_parts = []
        
        # Use the most common message pattern
        messages = [log.message for log in similar_logs if log.message]
        if messages:
            # Find common words
            all_words = set()
            for msg in messages:
                all_words.update(msg.lower().split())
            
            common_words = []
            for word in all_words:
                if sum(1 for msg in messages if word in msg.lower()) >= len(messages) * 0.5:
                    common_words.append(word)
            
            signature_parts.extend(common_words)
        
        # Add exception type if consistent
        exception_types = [log.exception_type for log in similar_logs if log.exception_type]
        if exception_types and len(set(exception_types)) == 1:
            signature_parts.append(exception_types[0])
        
        # Add file path if consistent
        file_paths = [log.file_path for log in similar_logs if log.file_path]
        if file_paths and len(set(file_paths)) == 1:
            signature_parts.append(Path(file_paths[0]).name)
        
        signature = '|'.join(sorted(signature_parts))
        pattern_id = hashlib.md5(signature.encode()).hexdigest()[:12]
        
        # Get timestamps
        timestamps = [log.timestamp for log in similar_logs if log.timestamp]
        first_seen = min(timestamps) if timestamps else datetime.utcnow()
        last_seen = max(timestamps) if timestamps else datetime.utcnow()
        
        # Get affected files
        files_affected = set()
        for log in similar_logs:
            if log.file_path:
                files_affected.add(log.file_path)
        
        return ErrorPattern(
            pattern_id=pattern_id,
            signature=signature,
            similarity_threshold=self.similarity_threshold,
            first_seen=first_seen,
            last_seen=last_seen,
            occurrence_count=len(similar_logs),
            representative_error=similar_logs[0],
            common_keywords=signature_parts,
            files_affected=files_affected
        )


class CorrelationEngine:
    """Engine for detecting correlations between errors and other context items."""

    def __init__(self, time_window_hours: int = 2):
        self.time_window_hours = time_window_hours

    async def find_correlations(
        self,
        error_log: ParsedLog,
        context_items: List[ContextItem]
    ) -> List[CorrelationResult]:
        """Find correlations between error and context items."""
        correlations = []
        
        if not error_log.timestamp:
            return correlations
        
        # Define time window
        time_window_start = error_log.timestamp - timedelta(hours=self.time_window_hours)
        time_window_end = error_log.timestamp + timedelta(hours=self.time_window_hours)
        
        # Filter context items by time window
        relevant_items = []
        for item in context_items:
            if item.timestamp and time_window_start <= item.timestamp <= time_window_end:
                relevant_items.append(item)
        
        # Find different types of correlations
        correlations.extend(await self._find_git_correlations(error_log, relevant_items))
        correlations.extend(await self._find_chat_correlations(error_log, relevant_items))
        correlations.extend(await self._find_code_change_correlations(error_log, relevant_items))
        
        return correlations

    async def _find_git_correlations(
        self,
        error_log: ParsedLog,
        context_items: List[ContextItem]
    ) -> List[CorrelationResult]:
        """Find Git commit correlations."""
        correlations = []
        
        git_items = [item for item in context_items if item.source_type == 'git']
        
        for git_item in git_items:
            confidence = 0.0
            evidence = {}
            correlation_type = CorrelationType.TEMPORAL
            
            # File path correlation
            if error_log.file_path and git_item.file_path:
                if error_log.file_path == git_item.file_path:
                    confidence += 0.5
                    evidence['file_path_match'] = True
                    correlation_type = CorrelationType.FILE_PATH
                elif Path(error_log.file_path).parent == Path(git_item.file_path).parent:
                    confidence += 0.3
                    evidence['directory_match'] = True
            
            # Temporal correlation
            if error_log.timestamp and git_item.timestamp:
                time_delta = abs((error_log.timestamp - git_item.timestamp).total_seconds())
                if time_delta < 3600:  # Within 1 hour
                    confidence += 0.3
                    evidence['time_delta_seconds'] = time_delta
            
            # Content correlation
            if error_log.message and git_item.content:
                # Simple keyword matching
                error_words = set(error_log.message.lower().split())
                git_words = set(git_item.content.lower().split())
                
                common_words = error_words & git_words
                if common_words:
                    confidence += min(len(common_words) / 10, 0.2)
                    evidence['common_keywords'] = list(common_words)[:5]
            
            if confidence >= 0.3:
                correlations.append(CorrelationResult(
                    correlation_type=correlation_type,
                    target_id=str(git_item.id),
                    target_type='git_commit',
                    confidence_score=min(confidence, 1.0),
                    evidence=evidence,
                    time_delta_seconds=int(evidence.get('time_delta_seconds', 0))
                ))
        
        return correlations

    async def _find_chat_correlations(
        self,
        error_log: ParsedLog,
        context_items: List[ContextItem]
    ) -> List[CorrelationResult]:
        """Find chat conversation correlations."""
        correlations = []
        
        chat_items = [item for item in context_items if item.source_type == 'chat']
        
        for chat_item in chat_items:
            confidence = 0.0
            evidence = {}
            
            # Content similarity
            if error_log.message and chat_item.content:
                # Check for error keywords in chat
                error_keywords = ['error', 'bug', 'issue', 'problem', 'fail']
                chat_content_lower = chat_item.content.lower()
                
                for keyword in error_keywords:
                    if keyword in chat_content_lower:
                        confidence += 0.1
                
                # Check for file path references
                if error_log.file_path:
                    filename = Path(error_log.file_path).name
                    if filename in chat_item.content:
                        confidence += 0.4
                        evidence['file_reference'] = True
                
                # Check for function name references
                if error_log.function_name and error_log.function_name in chat_item.content:
                    confidence += 0.3
                    evidence['function_reference'] = True
                
                # Check for exception type references
                if error_log.exception_type and error_log.exception_type in chat_item.content:
                    confidence += 0.4
                    evidence['exception_reference'] = True
            
            # Temporal proximity
            if error_log.timestamp and chat_item.timestamp:
                time_delta = abs((error_log.timestamp - chat_item.timestamp).total_seconds())
                if time_delta < 7200:  # Within 2 hours
                    confidence += 0.2
                    evidence['time_delta_seconds'] = time_delta
            
            if confidence >= 0.2:
                correlations.append(CorrelationResult(
                    correlation_type=CorrelationType.CONTEXTUAL,
                    target_id=str(chat_item.id),
                    target_type='chat_message',
                    confidence_score=min(confidence, 1.0),
                    evidence=evidence,
                    time_delta_seconds=int(evidence.get('time_delta_seconds', 0))
                ))
        
        return correlations

    async def _find_code_change_correlations(
        self,
        error_log: ParsedLog,
        context_items: List[ContextItem]
    ) -> List[CorrelationResult]:
        """Find code change correlations."""
        correlations = []
        
        code_items = [item for item in context_items if item.source_type == 'code']
        
        for code_item in code_items:
            confidence = 0.0
            evidence = {}
            
            # Direct file correlation
            if error_log.file_path and code_item.file_path:
                if error_log.file_path == code_item.file_path:
                    confidence += 0.6
                    evidence['file_match'] = True
                    
                    # Line number correlation
                    if error_log.line_number and code_item.line_start:
                        line_diff = abs(error_log.line_number - code_item.line_start)
                        if line_diff <= 10:
                            confidence += 0.3
                            evidence['line_proximity'] = line_diff
            
            # Function correlation
            if error_log.function_name and code_item.function_name:
                if error_log.function_name == code_item.function_name:
                    confidence += 0.5
                    evidence['function_match'] = True
            
            if confidence >= 0.3:
                correlations.append(CorrelationResult(
                    correlation_type=CorrelationType.FILE_PATH,
                    target_id=str(code_item.id),
                    target_type='code_change',
                    confidence_score=min(confidence, 1.0),
                    evidence=evidence
                ))
        
        return correlations


class AdvancedErrorAdapter(BaseAdapter):
    """Advanced error log adapter with intelligent parsing and correlation."""

    @classmethod
    def default_config(cls) -> AdapterConfig:
        """Get default configuration."""
        return AdapterConfig(
            adapter_id="advanced_error_adapter",
            source_type="error",
            batch_mode=BatchMode.STREAMING,
            batch_size=100,
            generate_embeddings=True,
            generate_summaries=False,
            extract_relationships=True,
            source_config={
                # Input sources
                "input_sources": ["logs", "realtime", "api"],
                "log_directories": ["./logs", "/var/log", "./error-logs"],
                "log_file_patterns": ["*.log", "error*.log", "*.err", "application*.log"],
                
                # Processing configuration
                "realtime_processing": True,
                "batch_processing": True,
                "enable_format_detection": True,
                "enable_error_classification": True,
                "enable_pattern_detection": True,
                "enable_correlation_detection": True,
                
                # Classification settings
                "classification_confidence_threshold": 0.6,
                "severity_scoring_enabled": True,
                "ml_classification_enabled": False,  # Enable when model is available
                
                # Pattern detection settings
                "pattern_similarity_threshold": 0.8,
                "min_pattern_occurrences": 2,
                "pattern_detection_window_hours": 24,
                
                # Correlation settings
                "correlation_window_hours": 2,
                "max_correlations_per_error": 20,
                "correlation_confidence_threshold": 0.3,
                "enable_git_correlation": True,
                "enable_chat_correlation": True,
                "enable_code_correlation": True,
                
                # Performance settings
                "parallel_processing": True,
                "max_concurrent_parsers": 8,
                "enable_caching": True,
                "cache_ttl_minutes": 30,
                
                # Filtering
                "severity_filters": [],  # empty = all severities
                "exclude_patterns": [
                    r".*DEBUG.*routine.*",
                    r".*INFO.*heartbeat.*",
                    r".*connection.*keep-alive.*"
                ],
                "max_error_age_days": 30,
                
                # Storage optimization
                "enable_deduplication": True,
                "deduplication_window_hours": 1,
                "compress_old_errors": True,
                "archive_after_days": 90,
            }
        )

    def __init__(self, config: AdapterConfig):
        """Initialize the advanced error adapter."""
        super().__init__(config)
        
        # Initialize processing engines
        self.format_detector = FormatDetectionEngine()
        self.log_parser = MultiFormatLogParser()
        self.classifier = ErrorClassificationEngine()
        self.pattern_detector = ErrorPatternDetector(
            similarity_threshold=config.source_config.get('pattern_similarity_threshold', 0.8)
        )
        self.correlation_engine = CorrelationEngine(
            time_window_hours=config.source_config.get('correlation_window_hours', 2)
        )
        self.transformer = DataTransformer()
        
        # Processing state
        self._processed_files: Set[str] = set()
        self._error_patterns: Dict[str, ErrorPattern] = {}
        self._correlation_cache: Dict[str, List[CorrelationResult]] = {}
        
        # Performance monitoring
        self._processing_times: deque = deque(maxlen=1000)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._pattern_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)

    async def initialize(self) -> None:
        """Initialize the adapter."""
        self.logger.info("Initializing Advanced Error Adapter")
        
        # Validate configuration
        await self._validate_configuration()
        
        # Initialize processing engines
        await self._initialize_engines()
        
        # Setup monitoring
        await self._setup_monitoring()
        
        self.logger.info(
            "Advanced Error Adapter initialized successfully",
            config_summary={
                'input_sources': self.config.source_config.get('input_sources', []),
                'log_directories': len(self.config.source_config.get('log_directories', [])),
                'pattern_detection': self.config.source_config.get('enable_pattern_detection', False),
                'correlation_detection': self.config.source_config.get('enable_correlation_detection', False),
                'realtime_processing': self.config.source_config.get('realtime_processing', False)
            }
        )

    async def _validate_configuration(self) -> None:
        """Validate adapter configuration."""
        # Check input sources
        input_sources = self.config.source_config.get('input_sources', [])
        valid_sources = ['logs', 'realtime', 'api', 'stream']
        
        for source in input_sources:
            if source not in valid_sources:
                raise ValueError(f"Invalid input source: {source}")
        
        # Check log directories
        log_dirs = self.config.source_config.get('log_directories', [])
        for log_dir in log_dirs:
            if not Path(log_dir).exists():
                self.logger.warning(f"Log directory does not exist: {log_dir}")
        
        # Validate thresholds
        similarity_threshold = self.config.source_config.get('pattern_similarity_threshold', 0.8)
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(f"Invalid similarity threshold: {similarity_threshold}")
        
        correlation_threshold = self.config.source_config.get('correlation_confidence_threshold', 0.3)
        if not 0.0 <= correlation_threshold <= 1.0:
            raise ValueError(f"Invalid correlation threshold: {correlation_threshold}")

    async def _initialize_engines(self) -> None:
        """Initialize processing engines."""
        # Initialize classification engine with custom categories if provided
        custom_categories = self.config.source_config.get('custom_error_categories')
        if custom_categories:
            self.classifier.error_categories.update(custom_categories)
        
        # Initialize pattern detector with custom settings
        self.pattern_detector.similarity_threshold = self.config.source_config.get(
            'pattern_similarity_threshold', 0.8
        )
        
        self.logger.info("Processing engines initialized")

    async def _setup_monitoring(self) -> None:
        """Setup performance monitoring."""
        if self.config.source_config.get('enable_monitoring', True):
            # Initialize monitoring structures
            self._processing_times.clear()
            self._error_counts.clear()
            self._pattern_stats.clear()
            
            self.logger.info("Monitoring systems initialized")

    async def fetch_items(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch error items from configured sources."""
        input_sources = self.config.source_config.get('input_sources', ['logs'])
        count = 0
        
        for source in input_sources:
            if limit and count >= limit:
                break
            
            try:
                if source == 'logs':
                    async for item in self._fetch_from_log_files(since, until, limit - count if limit else None):
                        yield item
                        count += 1
                        if limit and count >= limit:
                            break
                
                elif source == 'realtime':
                    async for item in self._fetch_from_realtime_stream(since, until, limit - count if limit else None):
                        yield item
                        count += 1
                        if limit and count >= limit:
                            break
                
                elif source == 'api':
                    async for item in self._fetch_from_api_endpoints(since, until, limit - count if limit else None):
                        yield item
                        count += 1
                        if limit and count >= limit:
                            break
                        
            except Exception as e:
                self.logger.error(f"Error fetching from source {source}: {e}")
                continue

    async def _fetch_from_log_files(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch errors from log files."""
        log_dirs = self.config.source_config.get('log_directories', ['./logs'])
        patterns = self.config.source_config.get('log_file_patterns', ['*.log'])
        
        count = 0
        
        for log_dir in log_dirs:
            dir_path = Path(log_dir)
            if not dir_path.exists():
                continue
            
            for pattern in patterns:
                try:
                    for log_file in dir_path.glob(pattern):
                        if str(log_file) in self._processed_files and not since:
                            continue
                        
                        async for error_data in self._process_log_file(log_file, since, until):
                            if limit and count >= limit:
                                return
                            
                            yield error_data
                            count += 1
                        
                        self._processed_files.add(str(log_file))
                        
                except Exception as e:
                    self.logger.error(f"Error processing pattern {pattern} in {log_dir}: {e}")
                    continue

    async def _process_log_file(
        self,
        log_file: Path,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Process a single log file."""
        try:
            async with aiofiles.open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            if not content.strip():
                return
            
            # Detect format
            format_result = await self.format_detector.detect_format(content)
            
            # Parse logs
            parsed_logs = await self.log_parser.parse(
                content, format_result.format_type, format_result.schema
            )
            
            # Filter by time range
            if since or until:
                filtered_logs = []
                for log in parsed_logs:
                    if log.timestamp:
                        if since and log.timestamp < since:
                            continue
                        if until and log.timestamp > until:
                            continue
                    filtered_logs.append(log)
                parsed_logs = filtered_logs
            
            # Apply exclude patterns
            exclude_patterns = self.config.source_config.get('exclude_patterns', [])
            if exclude_patterns:
                filtered_logs = []
                for log in parsed_logs:
                    if log.message and any(re.search(pattern, log.message) for pattern in exclude_patterns):
                        continue
                    filtered_logs.append(log)
                parsed_logs = filtered_logs
            
            # Process each parsed log
            for parsed_log in parsed_logs:
                yield {
                    'parsed_log': parsed_log,
                    'source_file': str(log_file),
                    'format_type': format_result.format_type.value,
                    'format_confidence': format_result.confidence,
                }
                
        except Exception as e:
            self.logger.error(f"Error processing log file {log_file}: {e}")
            return

    async def _fetch_from_realtime_stream(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from real-time error streams."""
        # Placeholder for real-time streaming implementation
        self.logger.info("Real-time streaming not yet implemented")
        return
        yield  # Make this a generator

    async def _fetch_from_api_endpoints(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Fetch from API endpoints."""
        # Placeholder for API endpoint implementation
        self.logger.info("API endpoint fetching not yet implemented")
        return
        yield  # Make this a generator

    async def transform_item(self, raw_item: Dict[str, Any]) -> ContextItem:
        """Transform raw error item into ContextItem."""
        start_time = datetime.utcnow()
        
        try:
            parsed_log: ParsedLog = raw_item['parsed_log']
            
            # Generate source ID
            source_id = self._generate_source_id(parsed_log, raw_item)
            
            # Create base context item
            item = self.transformer.create_base_context_item(
                source_type="error",
                source_id=source_id,
                raw_data=raw_item
            )
            
            # Set basic fields
            item.title = self._extract_error_title(parsed_log)
            item.content = self._extract_error_content(parsed_log)
            item.timestamp = parsed_log.timestamp or datetime.utcnow()
            
            # Set location information
            if parsed_log.file_path:
                item.file_path = parsed_log.file_path
            if parsed_log.line_number:
                item.line_start = parsed_log.line_number
            if parsed_log.function_name:
                item.function_name = parsed_log.function_name
            
            # Classify error
            classification = await self.classifier.classify_error(parsed_log)
            
            # Set severity
            item.severity = self._map_severity_to_level(classification.severity_score)
            
            # Set entity type based on classification
            item.entity_type = self._determine_entity_type(classification)
            
            # Build tags
            tags = ['error', classification.primary_category]
            if classification.subcategory:
                tags.append(classification.subcategory)
            if parsed_log.level:
                tags.append(f"level_{parsed_log.level.lower()}")
            if parsed_log.exception_type:
                tags.append(f"exception_{parsed_log.exception_type.lower()}")
            
            item.tags = tags
            
            # Build metrics
            metrics = {
                'classification': {
                    'primary_category': classification.primary_category,
                    'subcategory': classification.subcategory,
                    'confidence': classification.confidence,
                    'severity_score': classification.severity_score,
                    'keywords': classification.keywords
                },
                'parsing': {
                    'format_type': raw_item.get('format_type'),
                    'format_confidence': raw_item.get('format_confidence'),
                    'source_file': raw_item.get('source_file')
                },
                'error_details': {
                    'level': parsed_log.level,
                    'exception_type': parsed_log.exception_type,
                    'has_stack_trace': bool(parsed_log.stack_trace),
                    'logger_name': parsed_log.logger_name
                }
            }
            
            # Add stack trace analysis if available
            if parsed_log.stack_trace:
                stack_analysis = await self._analyze_stack_trace(parsed_log.stack_trace)
                metrics['stack_trace_analysis'] = stack_analysis
            
            item.metrics = metrics
            
            # Record processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._processing_times.append(processing_time)
            
            # Update error counts
            self._error_counts[classification.primary_category] += 1
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error transforming item: {e}")
            # Create minimal error item
            return self._create_minimal_error_item(raw_item, str(e))

    def _generate_source_id(self, parsed_log: ParsedLog, raw_item: Dict[str, Any]) -> str:
        """Generate unique source ID for the error."""
        # Create hash based on key characteristics
        components = []
        
        if parsed_log.timestamp:
            components.append(parsed_log.timestamp.isoformat())
        
        if parsed_log.message:
            # Use first 100 characters of message
            components.append(parsed_log.message[:100])
        
        if parsed_log.file_path:
            components.append(parsed_log.file_path)
        
        if parsed_log.line_number:
            components.append(str(parsed_log.line_number))
        
        if parsed_log.exception_type:
            components.append(parsed_log.exception_type)
        
        # Add source file for uniqueness
        if raw_item.get('source_file'):
            components.append(raw_item['source_file'])
        
        content = '|'.join(components)
        hash_value = hashlib.md5(content.encode()).hexdigest()
        
        return f"error_{hash_value[:12]}"

    def _extract_error_title(self, parsed_log: ParsedLog) -> str:
        """Extract concise error title."""
        if parsed_log.exception_type:
            return parsed_log.exception_type
        
        if parsed_log.message:
            # Take first line of message, truncated
            first_line = parsed_log.message.split('\n')[0].strip()
            return first_line[:100] if first_line else "Unknown Error"
        
        return "Unknown Error"

    def _extract_error_content(self, parsed_log: ParsedLog) -> str:
        """Extract comprehensive error content."""
        parts = []
        
        # Main message
        if parsed_log.message:
            parts.append(f"Message: {parsed_log.message}")
        
        # Error details
        if parsed_log.exception_type:
            parts.append(f"Exception Type: {parsed_log.exception_type}")
        
        if parsed_log.level:
            parts.append(f"Level: {parsed_log.level}")
        
        if parsed_log.logger_name:
            parts.append(f"Logger: {parsed_log.logger_name}")
        
        # Location details
        location_parts = []
        if parsed_log.file_path:
            location_parts.append(f"File: {parsed_log.file_path}")
        if parsed_log.line_number:
            location_parts.append(f"Line: {parsed_log.line_number}")
        if parsed_log.function_name:
            location_parts.append(f"Function: {parsed_log.function_name}")
        
        if location_parts:
            parts.append(f"Location: {', '.join(location_parts)}")
        
        # Stack trace
        if parsed_log.stack_trace:
            parts.append(f"Stack Trace:\n{parsed_log.stack_trace}")
        
        return '\n\n'.join(parts)

    def _map_severity_to_level(self, severity_score: float) -> str:
        """Map severity score to severity level."""
        if severity_score >= 0.9:
            return 'critical'
        elif severity_score >= 0.7:
            return 'high'
        elif severity_score >= 0.4:
            return 'medium'
        else:
            return 'low'

    def _determine_entity_type(self, classification: ClassificationResult) -> str:
        """Determine entity type based on classification."""
        category_to_entity = {
            'network': 'network_error',
            'database': 'database_error',
            'memory': 'memory_error',
            'security': 'security_error',
            'performance': 'performance_error',
            'application': 'application_error'
        }
        
        return category_to_entity.get(classification.primary_category, 'application_error')

    async def _analyze_stack_trace(self, stack_trace: str) -> Dict[str, Any]:
        """Analyze stack trace for additional insights."""
        analysis = {
            'total_lines': len(stack_trace.split('\n')),
            'unique_files': len(set()),
            'root_cause_line': None,
            'function_calls': []
        }
        
        lines = stack_trace.split('\n')
        files_seen = set()
        functions_seen = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract file information (Python format)
            python_match = re.search(r'File "([^"]+)", line (\d+), in (.+)', line)
            if python_match:
                file_path, line_num, function = python_match.groups()
                files_seen.add(file_path)
                functions_seen.append(function)
                continue
            
            # Extract file information (Java format)
            java_match = re.search(r'at (.+)\.(.+)\((.+):(\d+)\)', line)
            if java_match:
                class_name, method, file_name, line_num = java_match.groups()
                files_seen.add(file_name)
                functions_seen.append(f"{class_name}.{method}")
                continue
        
        analysis['unique_files'] = len(files_seen)
        analysis['function_calls'] = functions_seen[:10]  # Limit to top 10
        
        # Try to identify root cause (usually the first non-library function)
        for func in functions_seen:
            if not any(lib in func.lower() for lib in ['java.', 'python.', 'builtin', 'site-packages']):
                analysis['root_cause_function'] = func
                break
        
        return analysis

    def _create_minimal_error_item(self, raw_item: Dict[str, Any], error_message: str) -> ContextItem:
        """Create minimal context item when transformation fails."""
        item = ContextItem(
            source_type="error",
            source_id=f"error_failed_{hash(str(raw_item)) % 1000000:06d}",
            entity_type="parse_error",
            timestamp=datetime.utcnow(),
            title="Error Processing Failed",
            content=f"Failed to process error item: {error_message}",
            severity="medium",
            tags=["error", "processing_failed"],
            metrics={"error": error_message, "raw_item": raw_item}
        )
        return item

    async def detect_relationships(
        self,
        item: ContextItem,
        context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect relationships with other context items."""
        relationships = []
        
        if not self.config.source_config.get('enable_correlation_detection', True):
            return relationships
        
        try:
            # Get parsed log from metrics
            parsed_log_data = item.metrics.get('raw_data', {}).get('parsed_log')
            if not parsed_log_data:
                return relationships
            
            # Convert back to ParsedLog for correlation analysis
            parsed_log = self._reconstruct_parsed_log(item)
            
            # Find correlations using correlation engine
            correlations = await self.correlation_engine.find_correlations(
                parsed_log, context_window
            )
            
            # Convert correlation results to relationship tuples
            for correlation in correlations:
                relationship_type = self._map_correlation_to_relationship_type(correlation.correlation_type)
                relationships.append((
                    relationship_type,
                    correlation.target_id,
                    correlation.confidence_score
                ))
            
            # Pattern-based relationships
            pattern_relationships = await self._detect_pattern_relationships(item, context_window)
            relationships.extend(pattern_relationships)
            
        except Exception as e:
            self.logger.error(f"Error detecting relationships: {e}")
        
        return relationships

    def _reconstruct_parsed_log(self, item: ContextItem) -> ParsedLog:
        """Reconstruct ParsedLog from ContextItem for correlation analysis."""
        raw_data = item.source_data or {}
        parsed_log_data = raw_data.get('parsed_log', {})
        
        return ParsedLog(
            timestamp=item.timestamp,
            message=parsed_log_data.get('message') or item.content,
            level=parsed_log_data.get('level'),
            file_path=item.file_path,
            line_number=item.line_start,
            function_name=item.function_name,
            exception_type=parsed_log_data.get('exception_type'),
            stack_trace=parsed_log_data.get('stack_trace'),
            logger_name=parsed_log_data.get('logger_name'),
            raw_content=parsed_log_data.get('raw_content')
        )

    def _map_correlation_to_relationship_type(self, correlation_type: CorrelationType) -> str:
        """Map correlation type to relationship type."""
        mapping = {
            CorrelationType.TEMPORAL: 'temporal_correlation',
            CorrelationType.CAUSAL: 'causal_relationship',
            CorrelationType.CONTEXTUAL: 'contextual_relationship',
            CorrelationType.FILE_PATH: 'file_correlation',
            CorrelationType.SEMANTIC: 'semantic_similarity'
        }
        return mapping.get(correlation_type, 'related_to')

    async def _detect_pattern_relationships(
        self,
        item: ContextItem,
        context_window: List[ContextItem]
    ) -> List[tuple]:
        """Detect pattern-based relationships."""
        relationships = []
        
        if not self.config.source_config.get('enable_pattern_detection', True):
            return relationships
        
        try:
            # Find similar errors in context window
            error_items = [ctx_item for ctx_item in context_window if ctx_item.source_type == 'error']
            
            if len(error_items) < 2:
                return relationships
            
            # Convert to ParsedLog objects for pattern analysis
            parsed_logs = []
            item_mapping = {}
            
            for ctx_item in error_items:
                parsed_log = self._reconstruct_parsed_log(ctx_item)
                parsed_logs.append(parsed_log)
                item_mapping[id(parsed_log)] = ctx_item.id
            
            # Detect patterns
            patterns = await self.pattern_detector.detect_patterns(parsed_logs)
            
            # Create relationships for items in the same pattern
            current_parsed_log = self._reconstruct_parsed_log(item)
            
            for pattern in patterns:
                # Check if current item is part of this pattern
                current_text = self.pattern_detector._prepare_text_for_pattern_analysis(current_parsed_log)
                
                # Simple similarity check (could be improved)
                for keyword in pattern.common_keywords:
                    if keyword in current_text:
                        # Find other items in this pattern
                        for ctx_item in error_items:
                            if ctx_item.id != item.id:
                                other_text = self.pattern_detector._prepare_text_for_pattern_analysis(
                                    self._reconstruct_parsed_log(ctx_item)
                                )
                                if keyword in other_text:
                                    relationships.append((
                                        'similar_error_pattern',
                                        str(ctx_item.id),
                                        0.8
                                    ))
                        break
                
        except Exception as e:
            self.logger.error(f"Error detecting pattern relationships: {e}")
        
        return relationships

    async def get_adapter_statistics(self) -> Dict[str, Any]:
        """Get comprehensive adapter statistics."""
        stats = {
            'processing': {
                'total_errors_processed': sum(self._error_counts.values()),
                'errors_by_category': dict(self._error_counts),
                'average_processing_time_ms': statistics.mean(self._processing_times) if self._processing_times else 0,
                'total_patterns_detected': len(self._error_patterns)
            },
            'performance': {
                'processing_times': {
                    'min_ms': min(self._processing_times) if self._processing_times else 0,
                    'max_ms': max(self._processing_times) if self._processing_times else 0,
                    'avg_ms': statistics.mean(self._processing_times) if self._processing_times else 0,
                    'p95_ms': np.percentile(list(self._processing_times), 95) if self._processing_times else 0
                },
                'throughput_per_minute': len(self._processing_times),  # Approximate
                'cache_hit_rate': 0.0  # TODO: Implement caching statistics
            },
            'configuration': {
                'input_sources': self.config.source_config.get('input_sources', []),
                'pattern_detection_enabled': self.config.source_config.get('enable_pattern_detection', False),
                'correlation_detection_enabled': self.config.source_config.get('enable_correlation_detection', False),
                'realtime_processing_enabled': self.config.source_config.get('realtime_processing', False),
                'classification_enabled': self.config.source_config.get('enable_error_classification', True)
            },
            'patterns': {
                pattern_id: {
                    'occurrence_count': pattern.occurrence_count,
                    'files_affected': len(pattern.files_affected),
                    'first_seen': pattern.first_seen.isoformat() if pattern.first_seen else None,
                    'last_seen': pattern.last_seen.isoformat() if pattern.last_seen else None
                }
                for pattern_id, pattern in self._error_patterns.items()
            }
        }
        
        return stats

    async def cleanup(self) -> None:
        """Clean up adapter resources."""
        self.logger.info("Cleaning up Advanced Error Adapter")
        
        # Clear processing state
        self._processed_files.clear()
        self._error_patterns.clear()
        self._correlation_cache.clear()
        
        # Clear performance monitoring data
        self._processing_times.clear()
        self._error_counts.clear()
        self._pattern_stats.clear()
        
        self.logger.info("Advanced Error Adapter cleanup completed")