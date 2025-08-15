"""
Metrics Tracker - Tracks and analyzes performance metrics
"""

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import numpy as np
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False
    plt = None
    sns = None

from src.utils.logger import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics that can be tracked"""
    COUNTER = "counter"          # Simple count
    GAUGE = "gauge"              # Current value
    HISTOGRAM = "histogram"      # Distribution of values
    RATE = "rate"               # Rate of change
    TIMER = "timer"             # Execution time
    PERCENTAGE = "percentage"   # Percentage value


@dataclass
class Metric:
    """Represents a tracked metric"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric"""
    name: str
    type: MetricType
    count: int
    mean: float
    std: float
    min: float
    max: float
    p50: float  # median
    p95: float  # 95th percentile
    p99: float  # 99th percentile
    rate: float  # per second
    period_start: datetime
    period_end: datetime


class MetricsTracker:
    """Tracks and analyzes system metrics"""
    
    def __init__(self, db_path: Optional[Path] = None, 
                 buffer_size: int = 10000,
                 aggregation_interval: int = 60):
        self.db_path = db_path or Path.home() / '.autonomous_claude' / 'metrics.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.buffer_size = buffer_size
        self.aggregation_interval = aggregation_interval  # seconds
        
        # In-memory buffers
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=buffer_size))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        # Aggregated data
        self.hourly_aggregates: Dict[str, List[MetricSummary]] = defaultdict(list)
        self.daily_aggregates: Dict[str, List[MetricSummary]] = defaultdict(list)
        
        # Alerts
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        
        self._lock = asyncio.Lock()
        self._aggregation_task = None
        self._init_database()
        self._load_recent_metrics()
    
    def _init_database(self):
        """Initialize SQLite database for metrics"""
        with sqlite3.connect(self.db_path) as conn:
            # Raw metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    tags TEXT,
                    metadata TEXT
                )
            ''')
            
            # Aggregated metrics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS aggregates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    period TEXT NOT NULL,
                    count INTEGER,
                    mean REAL,
                    std REAL,
                    min REAL,
                    max REAL,
                    p50 REAL,
                    p95 REAL,
                    p99 REAL,
                    rate REAL,
                    period_start TEXT,
                    period_end TEXT
                )
            ''')
            
            # Alerts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold REAL,
                    actual_value REAL,
                    timestamp TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT 0
                )
            ''')
            
            # Create indices
            conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_aggregates_name ON aggregates(name)')
            
            conn.commit()
    
    def _load_recent_metrics(self):
        """Load recent metrics from database"""
        cutoff = datetime.now() - timedelta(hours=24)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM metrics WHERE timestamp > ? ORDER BY timestamp',
                (cutoff.isoformat(),)
            )
            
            for row in cursor:
                metric = Metric(
                    name=row['name'],
                    type=MetricType(row['type']),
                    value=row['value'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    tags=json.loads(row['tags']) if row['tags'] else {},
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                
                self.metrics_buffer[metric.name].append(metric)
                
                # Update counters and gauges
                if metric.type == MetricType.COUNTER:
                    self.counters[metric.name] = metric.value
                elif metric.type == MetricType.GAUGE:
                    self.gauges[metric.name] = metric.value
    
    async def start(self):
        """Start the metrics tracker"""
        if self._aggregation_task is None:
            self._aggregation_task = asyncio.create_task(self._aggregation_loop())
            logger.info("Metrics tracker started")
    
    async def stop(self):
        """Stop the metrics tracker"""
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass
            self._aggregation_task = None
            logger.info("Metrics tracker stopped")
    
    async def _aggregation_loop(self):
        """Periodically aggregate metrics"""
        while True:
            try:
                await asyncio.sleep(self.aggregation_interval)
                await self._aggregate_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Aggregation error: {e}")
    
    async def record(self, name: str, value: float, 
                    metric_type: MetricType = MetricType.GAUGE,
                    tags: Optional[Dict[str, str]] = None,
                    metadata: Optional[Dict[str, Any]] = None):
        """Record a metric value"""
        async with self._lock:
            metric = Metric(
                name=name,
                type=metric_type,
                value=value,
                timestamp=datetime.now(),
                tags=tags or {},
                metadata=metadata or {}
            )
            
            # Add to buffer
            self.metrics_buffer[name].append(metric)
            
            # Update type-specific storage
            if metric_type == MetricType.COUNTER:
                self.counters[name] += value
            elif metric_type == MetricType.GAUGE:
                self.gauges[name] = value
            elif metric_type == MetricType.TIMER:
                self.timers[name].append(value)
                # Keep timer lists bounded
                if len(self.timers[name]) > self.buffer_size:
                    self.timers[name] = self.timers[name][-self.buffer_size:]
            
            # Check alerts
            await self._check_alerts(metric)
            
            # Save to database periodically
            if len(self.metrics_buffer[name]) % 100 == 0:
                await self._flush_to_database(name)
    
    async def increment(self, name: str, value: float = 1.0, 
                       tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        await self.record(name, value, MetricType.COUNTER, tags)
    
    async def gauge_set(self, name: str, value: float,
                       tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        await self.record(name, value, MetricType.GAUGE, tags)
    
    async def timer(self, name: str, duration: float,
                   tags: Optional[Dict[str, str]] = None):
        """Record a timer metric"""
        await self.record(name, duration, MetricType.TIMER, tags)
    
    async def histogram(self, name: str, value: float,
                       tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric"""
        await self.record(name, value, MetricType.HISTOGRAM, tags)
    
    async def _flush_to_database(self, metric_name: str):
        """Flush metrics to database"""
        metrics = list(self.metrics_buffer[metric_name])
        
        if not metrics:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for metric in metrics:
                conn.execute('''
                    INSERT INTO metrics (name, type, value, timestamp, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metric.name,
                    metric.type.value,
                    metric.value,
                    metric.timestamp.isoformat(),
                    json.dumps(metric.tags) if metric.tags else None,
                    json.dumps(metric.metadata) if metric.metadata else None
                ))
            conn.commit()
    
    async def _aggregate_metrics(self):
        """Aggregate metrics for summaries"""
        async with self._lock:
            now = datetime.now()
            
            for name, metrics in self.metrics_buffer.items():
                if not metrics:
                    continue
                
                # Filter recent metrics
                recent = [m for m in metrics if (now - m.timestamp).total_seconds() < 3600]
                
                if recent:
                    summary = self._calculate_summary(name, recent)
                    self.hourly_aggregates[name].append(summary)
                    
                    # Keep hourly aggregates bounded
                    if len(self.hourly_aggregates[name]) > 168:  # 1 week
                        self.hourly_aggregates[name] = self.hourly_aggregates[name][-168:]
                    
                    # Save aggregate to database
                    await self._save_aggregate(summary, 'hourly')
    
    def _calculate_summary(self, name: str, metrics: List[Metric]) -> MetricSummary:
        """Calculate summary statistics for metrics"""
        values = [m.value for m in metrics]
        
        if not values:
            return None
        
        # Calculate statistics
        values_array = np.array(values)
        
        # Time range
        timestamps = [m.timestamp for m in metrics]
        period_start = min(timestamps)
        period_end = max(timestamps)
        duration = (period_end - period_start).total_seconds()
        
        # Rate calculation
        if metrics[0].type == MetricType.COUNTER:
            rate = (values[-1] - values[0]) / duration if duration > 0 else 0
        else:
            rate = len(values) / duration if duration > 0 else 0
        
        return MetricSummary(
            name=name,
            type=metrics[0].type,
            count=len(values),
            mean=np.mean(values_array),
            std=np.std(values_array),
            min=np.min(values_array),
            max=np.max(values_array),
            p50=np.percentile(values_array, 50),
            p95=np.percentile(values_array, 95),
            p99=np.percentile(values_array, 99),
            rate=rate,
            period_start=period_start,
            period_end=period_end
        )
    
    async def _save_aggregate(self, summary: MetricSummary, period: str):
        """Save aggregate to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO aggregates 
                (name, type, period, count, mean, std, min, max, p50, p95, p99, rate, period_start, period_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                summary.name,
                summary.type.value,
                period,
                summary.count,
                summary.mean,
                summary.std,
                summary.min,
                summary.max,
                summary.p50,
                summary.p95,
                summary.p99,
                summary.rate,
                summary.period_start.isoformat(),
                summary.period_end.isoformat()
            ))
            conn.commit()
    
    async def set_alert_threshold(self, metric_name: str, 
                                 min_value: Optional[float] = None,
                                 max_value: Optional[float] = None,
                                 rate_limit: Optional[float] = None):
        """Set alert thresholds for a metric"""
        async with self._lock:
            self.alert_thresholds[metric_name] = {
                'min': min_value,
                'max': max_value,
                'rate_limit': rate_limit
            }
    
    async def _check_alerts(self, metric: Metric):
        """Check if metric triggers any alerts"""
        if metric.name not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[metric.name]
        
        # Check min threshold
        if thresholds.get('min') is not None and metric.value < thresholds['min']:
            await self._trigger_alert(metric, 'min_threshold', thresholds['min'])
        
        # Check max threshold
        if thresholds.get('max') is not None and metric.value > thresholds['max']:
            await self._trigger_alert(metric, 'max_threshold', thresholds['max'])
        
        # Check rate limit
        if thresholds.get('rate_limit') is not None:
            recent = [m for m in self.metrics_buffer[metric.name] 
                     if (metric.timestamp - m.timestamp).total_seconds() < 60]
            if len(recent) > thresholds['rate_limit']:
                await self._trigger_alert(metric, 'rate_limit', thresholds['rate_limit'])
    
    async def _trigger_alert(self, metric: Metric, alert_type: str, threshold: float):
        """Trigger an alert"""
        alert = {
            'metric_name': metric.name,
            'alert_type': alert_type,
            'threshold': threshold,
            'actual_value': metric.value,
            'timestamp': metric.timestamp
        }
        
        self.alert_history.append(alert)
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO alerts (metric_name, alert_type, threshold, actual_value, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                alert['metric_name'],
                alert['alert_type'],
                alert['threshold'],
                alert['actual_value'],
                alert['timestamp'].isoformat()
            ))
            conn.commit()
        
        logger.warning(f"Alert triggered: {metric.name} {alert_type} "
                      f"(value: {metric.value}, threshold: {threshold})")
    
    async def get_metric_summary(self, name: str, 
                                period: Optional[timedelta] = None) -> Optional[MetricSummary]:
        """Get summary statistics for a metric"""
        
        if period:
            cutoff = datetime.now() - period
            metrics = [m for m in self.metrics_buffer[name] if m.timestamp > cutoff]
        else:
            metrics = list(self.metrics_buffer[name])
        
        if not metrics:
            return None
        
        return self._calculate_summary(name, metrics)
    
    async def get_metrics_report(self) -> Dict[str, Any]:
        """Generate a comprehensive metrics report"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'alerts': {
                'active': [],
                'recent': self.alert_history[-10:] if self.alert_history else []
            },
            'system': {
                'buffer_usage': {},
                'metric_count': len(self.metrics_buffer)
            }
        }
        
        # Add metric summaries
        for name in self.metrics_buffer.keys():
            summary = await self.get_metric_summary(name, timedelta(hours=1))
            if summary:
                report['metrics'][name] = {
                    'type': summary.type.value,
                    'count': summary.count,
                    'mean': summary.mean,
                    'min': summary.min,
                    'max': summary.max,
                    'p95': summary.p95,
                    'rate': summary.rate
                }
        
        # Add buffer usage
        for name, buffer in self.metrics_buffer.items():
            report['system']['buffer_usage'][name] = len(buffer)
        
        return report
    
    async def plot_metric(self, name: str, period: Optional[timedelta] = None,
                         output_file: Optional[Path] = None):
        """Plot a metric over time"""
        
        if not HAS_VISUALIZATION:
            logger.warning("Visualization libraries not available, skipping plot")
            return
        
        if period:
            cutoff = datetime.now() - period
            metrics = [m for m in self.metrics_buffer[name] if m.timestamp > cutoff]
        else:
            metrics = list(self.metrics_buffer[name])
        
        if not metrics:
            logger.warning(f"No data to plot for metric: {name}")
            return
        
        # Extract data
        timestamps = [m.timestamp for m in metrics]
        values = [m.value for m in metrics]
        
        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, values, marker='o', markersize=2, linewidth=1)
        plt.title(f"Metric: {name}")
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Add threshold lines if set
        if name in self.alert_thresholds:
            thresholds = self.alert_thresholds[name]
            if thresholds.get('min') is not None:
                plt.axhline(y=thresholds['min'], color='r', linestyle='--', 
                          label=f"Min: {thresholds['min']}")
            if thresholds.get('max') is not None:
                plt.axhline(y=thresholds['max'], color='r', linestyle='--',
                          label=f"Max: {thresholds['max']}")
            plt.legend()
        
        if output_file:
            plt.savefig(output_file, dpi=100)
            logger.info(f"Plot saved to {output_file}")
        else:
            plt.show()
        
        plt.close()
    
    async def export_metrics(self, output_file: Path, 
                           period: Optional[timedelta] = None):
        """Export metrics to JSON"""
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'metrics': {}
        }
        
        for name, buffer in self.metrics_buffer.items():
            if period:
                cutoff = datetime.now() - period
                metrics = [m for m in buffer if m.timestamp > cutoff]
            else:
                metrics = list(buffer)
            
            data['metrics'][name] = [
                {
                    'value': m.value,
                    'timestamp': m.timestamp.isoformat(),
                    'type': m.type.value,
                    'tags': m.tags,
                    'metadata': m.metadata
                }
                for m in metrics
            ]
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported metrics to {output_file}")
    
    def get_current_values(self) -> Dict[str, Any]:
        """Get current values of all metrics"""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timer_counts': {name: len(values) for name, values in self.timers.items()}
        }
    
    async def reset_metric(self, name: str):
        """Reset a specific metric"""
        async with self._lock:
            if name in self.metrics_buffer:
                self.metrics_buffer[name].clear()
            if name in self.counters:
                self.counters[name] = 0
            if name in self.gauges:
                self.gauges[name] = 0
            if name in self.timers:
                self.timers[name].clear()
            
            logger.info(f"Reset metric: {name}")
    
    async def cleanup_old_data(self, days: int = 7):
        """Clean up old metric data"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Clean metrics
            result = conn.execute(
                'DELETE FROM metrics WHERE timestamp < ?',
                (cutoff.isoformat(),)
            )
            metrics_deleted = result.rowcount
            
            # Clean aggregates
            result = conn.execute(
                'DELETE FROM aggregates WHERE period_end < ?',
                (cutoff.isoformat(),)
            )
            aggregates_deleted = result.rowcount
            
            # Clean resolved alerts
            result = conn.execute(
                'DELETE FROM alerts WHERE timestamp < ? AND resolved = 1',
                (cutoff.isoformat(),)
            )
            alerts_deleted = result.rowcount
            
            conn.commit()
        
        logger.info(f"Cleaned up old data: {metrics_deleted} metrics, "
                   f"{aggregates_deleted} aggregates, {alerts_deleted} alerts")
        
        return {
            'metrics_deleted': metrics_deleted,
            'aggregates_deleted': aggregates_deleted,
            'alerts_deleted': alerts_deleted
        }