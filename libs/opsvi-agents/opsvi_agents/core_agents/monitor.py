"""MonitorAgent - Production-ready monitoring and observability agent."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import statistics

import structlog

from ..core.base import (
    BaseAgent,
    AgentConfig,
    AgentCapability,
    AgentResult,
    AgentState
)
from ..exceptions.base import AgentExecutionError

logger = structlog.get_logger(__name__)


class MetricType(Enum):
    """Types of metrics to monitor."""
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    ERROR = "error"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    AVAILABILITY = "availability"
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert definition."""
    id: str
    name: str
    condition: str
    threshold: float
    severity: AlertSeverity
    metric: str
    enabled: bool = True
    cooldown: int = 300  # seconds
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class HealthCheck:
    """Health check definition."""
    name: str
    target: str
    interval: int  # seconds
    timeout: int  # seconds
    success_threshold: int = 3
    failure_threshold: int = 3
    last_check: Optional[datetime] = None
    status: str = "unknown"
    consecutive_successes: int = 0
    consecutive_failures: int = 0


class MonitorAgent(BaseAgent):
    """Agent specialized in monitoring, observability, and alerting.
    
    Capabilities:
    - Real-time metric collection and aggregation
    - Performance monitoring and profiling
    - Error tracking and analysis
    - Alert management and notifications
    - Health checks and availability monitoring
    - Trend analysis and anomaly detection
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize MonitorAgent with monitoring capabilities."""
        if config is None:
            config = AgentConfig(
                name="MonitorAgent",
                model="gpt-4o-mini",  # Lightweight model for monitoring
                temperature=0.1,  # Very low for consistent monitoring
                max_tokens=4096,
                capabilities=[
                    AgentCapability.TOOL_USE,
                    AgentCapability.MEMORY,
                    AgentCapability.STREAMING
                ],
                system_prompt=self._get_system_prompt()
            )
        super().__init__(config)
        
        # Monitoring state
        self.metrics_buffer = []
        self.alerts = {}
        self.health_checks = {}
        self.anomaly_detectors = {}
        self.metric_aggregates = {}
        self.monitoring_dashboards = {}
        
    def _get_system_prompt(self) -> str:
        """Get specialized system prompt for monitoring."""
        return """You are a sophisticated monitoring and observability specialist.
        
        Your responsibilities:
        1. Collect and analyze system metrics in real-time
        2. Monitor performance and resource utilization
        3. Track errors and identify patterns
        4. Manage alerts and notifications
        5. Perform health checks and availability monitoring
        6. Detect anomalies and trends
        7. Generate insights and recommendations
        8. Ensure system reliability and performance
        
        Always prioritize system health, early detection of issues, and actionable insights."""
    
    def _execute(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Execute monitoring task."""
        self._logger.info("Executing monitoring task", task=prompt[:100])
        
        # Parse monitoring parameters
        action = kwargs.get("action", "monitor")
        target = kwargs.get("target")
        metrics = kwargs.get("metrics", [])
        duration = kwargs.get("duration", 60)  # seconds
        interval = kwargs.get("interval", 5)  # seconds
        
        try:
            if action == "monitor":
                result = self._monitor_system(target, metrics, duration, interval)
            elif action == "analyze":
                result = self._analyze_metrics(kwargs.get("time_range", 3600))
            elif action == "alert":
                result = self._manage_alerts(kwargs.get("alert_config"))
            elif action == "health":
                result = self._perform_health_checks(kwargs.get("checks", []))
            elif action == "profile":
                result = self._profile_performance(target, duration)
            elif action == "diagnose":
                result = self._diagnose_issues(kwargs.get("symptoms", []))
            elif action == "report":
                result = self._generate_report(kwargs.get("report_type", "summary"))
            else:
                result = self._adaptive_monitoring(prompt, kwargs)
            
            # Update metrics
            self.context.metrics.update({
                "metrics_collected": len(self.metrics_buffer),
                "active_alerts": len([a for a in self.alerts.values() if a.enabled]),
                "health_checks": len(self.health_checks),
                "anomalies_detected": result.get("anomalies", 0)
            })
            
            return result
            
        except Exception as e:
            self._logger.error("Monitoring failed", error=str(e))
            raise AgentExecutionError(f"Monitoring failed: {e}")
    
    def _monitor_system(self, target: str, metrics: List[str], 
                       duration: int, interval: int) -> Dict[str, Any]:
        """Monitor system metrics over time."""
        self._logger.info("Starting system monitoring", target=target, duration=duration)
        
        start_time = time.time()
        end_time = start_time + duration
        collected_metrics = []
        
        while time.time() < end_time:
            # Collect metrics
            current_metrics = self._collect_metrics(target, metrics)
            collected_metrics.extend(current_metrics)
            
            # Store in buffer
            self.metrics_buffer.extend(current_metrics)
            
            # Check for alerts
            triggered_alerts = self._check_alerts(current_metrics)
            
            # Sleep until next interval
            time.sleep(interval)
        
        # Aggregate metrics
        aggregates = self._aggregate_metrics(collected_metrics)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(collected_metrics)
        
        # Generate insights
        insights = self._generate_insights(aggregates, anomalies)
        
        return {
            "duration": duration,
            "metrics_collected": len(collected_metrics),
            "aggregates": aggregates,
            "anomalies": anomalies,
            "insights": insights,
            "alerts_triggered": len(triggered_alerts)
        }
    
    def _analyze_metrics(self, time_range: int) -> Dict[str, Any]:
        """Analyze historical metrics."""
        self._logger.info("Analyzing metrics", time_range=time_range)
        
        # Filter metrics by time range
        cutoff_time = datetime.now() - timedelta(seconds=time_range)
        relevant_metrics = [
            m for m in self.metrics_buffer 
            if m.timestamp >= cutoff_time
        ]
        
        if not relevant_metrics:
            return {"error": "No metrics available for analysis"}
        
        # Group metrics by type
        metrics_by_type = {}
        for metric in relevant_metrics:
            if metric.type not in metrics_by_type:
                metrics_by_type[metric.type] = []
            metrics_by_type[metric.type].append(metric)
        
        # Analyze each metric type
        analysis = {}
        for metric_type, metrics in metrics_by_type.items():
            analysis[metric_type.value] = self._analyze_metric_group(metrics)
        
        # Identify trends
        trends = self._identify_trends(relevant_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis, trends)
        
        return {
            "time_range": time_range,
            "metrics_analyzed": len(relevant_metrics),
            "analysis": analysis,
            "trends": trends,
            "recommendations": recommendations
        }
    
    def _manage_alerts(self, alert_config: Dict) -> Dict[str, Any]:
        """Manage alert configuration and state."""
        self._logger.info("Managing alerts", config=alert_config)
        
        action = alert_config.get("action", "list")
        
        if action == "create":
            alert = self._create_alert(alert_config)
            self.alerts[alert.id] = alert
            return {"created": alert.id, "alert": self._alert_to_dict(alert)}
        
        elif action == "update":
            alert_id = alert_config.get("id")
            if alert_id in self.alerts:
                self._update_alert(self.alerts[alert_id], alert_config)
                return {"updated": alert_id}
            return {"error": f"Alert {alert_id} not found"}
        
        elif action == "delete":
            alert_id = alert_config.get("id")
            if alert_id in self.alerts:
                del self.alerts[alert_id]
                return {"deleted": alert_id}
            return {"error": f"Alert {alert_id} not found"}
        
        elif action == "list":
            return {
                "alerts": [self._alert_to_dict(a) for a in self.alerts.values()],
                "total": len(self.alerts),
                "enabled": len([a for a in self.alerts.values() if a.enabled])
            }
        
        elif action == "test":
            alert_id = alert_config.get("id")
            if alert_id in self.alerts:
                result = self._test_alert(self.alerts[alert_id])
                return {"tested": alert_id, "result": result}
            return {"error": f"Alert {alert_id} not found"}
        
        return {"error": "Unknown alert action"}
    
    def _perform_health_checks(self, checks: List[Dict]) -> Dict[str, Any]:
        """Perform health checks on specified targets."""
        self._logger.info("Performing health checks", check_count=len(checks))
        
        results = []
        
        for check_def in checks:
            # Create or update health check
            check_name = check_def.get("name")
            if check_name not in self.health_checks:
                self.health_checks[check_name] = HealthCheck(
                    name=check_name,
                    target=check_def.get("target"),
                    interval=check_def.get("interval", 60),
                    timeout=check_def.get("timeout", 10)
                )
            
            check = self.health_checks[check_name]
            
            # Perform check
            check_result = self._execute_health_check(check)
            results.append(check_result)
            
            # Update check state
            self._update_health_check_state(check, check_result)
        
        # Calculate overall health
        overall_health = self._calculate_overall_health(results)
        
        return {
            "checks_performed": len(results),
            "results": results,
            "overall_health": overall_health,
            "healthy": overall_health["score"] >= 80,
            "summary": self._generate_health_summary(results)
        }
    
    def _profile_performance(self, target: str, duration: int) -> Dict[str, Any]:
        """Profile performance of target system."""
        self._logger.info("Profiling performance", target=target, duration=duration)
        
        # Collect performance metrics
        perf_metrics = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            metrics = self._collect_performance_metrics(target)
            perf_metrics.extend(metrics)
            time.sleep(0.1)  # High frequency sampling
        
        # Analyze performance data
        analysis = self._analyze_performance_data(perf_metrics)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(analysis)
        
        # Generate optimization suggestions
        optimizations = self._suggest_optimizations(bottlenecks)
        
        return {
            "target": target,
            "duration": duration,
            "samples": len(perf_metrics),
            "analysis": analysis,
            "bottlenecks": bottlenecks,
            "optimizations": optimizations
        }
    
    def _diagnose_issues(self, symptoms: List[str]) -> Dict[str, Any]:
        """Diagnose system issues based on symptoms."""
        self._logger.info("Diagnosing issues", symptoms=symptoms)
        
        # Analyze symptoms
        symptom_analysis = self._analyze_symptoms(symptoms)
        
        # Correlate with metrics
        metric_correlation = self._correlate_with_metrics(symptom_analysis)
        
        # Identify probable causes
        probable_causes = self._identify_probable_causes(
            symptom_analysis, metric_correlation
        )
        
        # Generate remediation steps
        remediation = self._generate_remediation_steps(probable_causes)
        
        return {
            "symptoms": symptoms,
            "analysis": symptom_analysis,
            "metric_correlation": metric_correlation,
            "probable_causes": probable_causes,
            "remediation": remediation,
            "confidence": self._calculate_diagnosis_confidence(probable_causes)
        }
    
    def _generate_report(self, report_type: str) -> Dict[str, Any]:
        """Generate monitoring report."""
        self._logger.info("Generating report", type=report_type)
        
        if report_type == "summary":
            return self._generate_summary_report()
        elif report_type == "detailed":
            return self._generate_detailed_report()
        elif report_type == "alerts":
            return self._generate_alerts_report()
        elif report_type == "health":
            return self._generate_health_report()
        elif report_type == "performance":
            return self._generate_performance_report()
        else:
            return self._generate_custom_report(report_type)
    
    def _adaptive_monitoring(self, prompt: str, context: Dict) -> Dict[str, Any]:
        """Adaptively determine monitoring approach."""
        # Analyze prompt to determine monitoring needs
        if "slow" in prompt.lower() or "performance" in prompt.lower():
            return self._profile_performance(context.get("target", "system"), 60)
        elif "error" in prompt.lower() or "issue" in prompt.lower():
            return self._diagnose_issues(self._extract_symptoms(prompt))
        elif "health" in prompt.lower() or "status" in prompt.lower():
            return self._perform_health_checks([])
        else:
            return self._monitor_system("system", ["cpu", "memory"], 60, 5)
    
    # Helper methods
    def _collect_metrics(self, target: str, metric_names: List[str]) -> List[Metric]:
        """Collect specified metrics."""
        metrics = []
        
        for name in metric_names:
            # Simulate metric collection - in production would use actual monitoring tools
            value = self._get_metric_value(target, name)
            metric = Metric(
                name=name,
                value=value,
                type=self._determine_metric_type(name),
                unit=self._get_metric_unit(name),
                tags={"target": target}
            )
            metrics.append(metric)
        
        return metrics
    
    def _get_metric_value(self, target: str, name: str) -> float:
        """Get metric value (simulated)."""
        import random
        # Simulate metric values
        if name == "cpu":
            return random.uniform(10, 90)
        elif name == "memory":
            return random.uniform(30, 80)
        elif name == "disk":
            return random.uniform(20, 70)
        elif name == "network":
            return random.uniform(100, 1000)
        return random.uniform(0, 100)
    
    def _determine_metric_type(self, name: str) -> MetricType:
        """Determine metric type from name."""
        if name in ["cpu", "memory", "disk"]:
            return MetricType.RESOURCE
        elif name in ["response_time", "latency"]:
            return MetricType.LATENCY
        elif name in ["requests", "throughput"]:
            return MetricType.THROUGHPUT
        elif name in ["errors", "failures"]:
            return MetricType.ERROR
        return MetricType.CUSTOM
    
    def _get_metric_unit(self, name: str) -> str:
        """Get metric unit."""
        units = {
            "cpu": "%",
            "memory": "%",
            "disk": "%",
            "network": "Mbps",
            "response_time": "ms",
            "latency": "ms",
            "throughput": "req/s",
            "errors": "count"
        }
        return units.get(name, "")
    
    def _check_alerts(self, metrics: List[Metric]) -> List[Alert]:
        """Check if any alerts should be triggered."""
        triggered = []
        
        for alert in self.alerts.values():
            if not alert.enabled:
                continue
            
            # Check if alert condition is met
            for metric in metrics:
                if metric.name == alert.metric:
                    if self._evaluate_alert_condition(alert, metric.value):
                        if self._should_trigger_alert(alert):
                            alert.last_triggered = datetime.now()
                            alert.trigger_count += 1
                            triggered.append(alert)
        
        return triggered
    
    def _evaluate_alert_condition(self, alert: Alert, value: float) -> bool:
        """Evaluate alert condition."""
        if alert.condition == ">":
            return value > alert.threshold
        elif alert.condition == "<":
            return value < alert.threshold
        elif alert.condition == ">=":
            return value >= alert.threshold
        elif alert.condition == "<=":
            return value <= alert.threshold
        elif alert.condition == "==":
            return value == alert.threshold
        return False
    
    def _should_trigger_alert(self, alert: Alert) -> bool:
        """Check if alert should be triggered based on cooldown."""
        if alert.last_triggered is None:
            return True
        
        elapsed = (datetime.now() - alert.last_triggered).total_seconds()
        return elapsed >= alert.cooldown
    
    def _aggregate_metrics(self, metrics: List[Metric]) -> Dict[str, Dict]:
        """Aggregate metrics by name."""
        aggregates = {}
        
        # Group by metric name
        metrics_by_name = {}
        for metric in metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric.value)
        
        # Calculate aggregates
        for name, values in metrics_by_name.items():
            if values:
                aggregates[name] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": statistics.mean(values),
                    "median": statistics.median(values),
                    "stddev": statistics.stdev(values) if len(values) > 1 else 0,
                    "count": len(values)
                }
        
        return aggregates
    
    def _detect_anomalies(self, metrics: List[Metric]) -> List[Dict]:
        """Detect anomalies in metrics."""
        anomalies = []
        
        # Group by metric name
        metrics_by_name = {}
        for metric in metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric)
        
        # Detect anomalies for each metric
        for name, metric_list in metrics_by_name.items():
            values = [m.value for m in metric_list]
            if len(values) > 3:
                mean = statistics.mean(values)
                stddev = statistics.stdev(values)
                
                # Simple z-score based anomaly detection
                for metric in metric_list:
                    z_score = abs((metric.value - mean) / stddev) if stddev > 0 else 0
                    if z_score > 3:  # 3 standard deviations
                        anomalies.append({
                            "metric": name,
                            "value": metric.value,
                            "z_score": z_score,
                            "timestamp": metric.timestamp.isoformat()
                        })
        
        return anomalies
    
    def _generate_insights(self, aggregates: Dict, anomalies: List) -> List[str]:
        """Generate insights from metrics."""
        insights = []
        
        # Check for high resource usage
        for metric, stats in aggregates.items():
            if metric in ["cpu", "memory", "disk"] and stats["avg"] > 80:
                insights.append(f"High {metric} usage detected: {stats['avg']:.1f}%")
        
        # Check for anomalies
        if anomalies:
            insights.append(f"Detected {len(anomalies)} anomalies in metrics")
        
        # Check for high variability
        for metric, stats in aggregates.items():
            if stats["stddev"] > stats["avg"] * 0.5:
                insights.append(f"High variability in {metric}: stddev={stats['stddev']:.2f}")
        
        return insights
    
    def _create_alert(self, config: Dict) -> Alert:
        """Create new alert from configuration."""
        import uuid
        return Alert(
            id=str(uuid.uuid4()),
            name=config.get("name", "Alert"),
            condition=config.get("condition", ">"),
            threshold=config.get("threshold", 80),
            severity=AlertSeverity[config.get("severity", "MEDIUM").upper()],
            metric=config.get("metric", "cpu"),
            enabled=config.get("enabled", True),
            cooldown=config.get("cooldown", 300)
        )
    
    def _alert_to_dict(self, alert: Alert) -> Dict:
        """Convert alert to dictionary."""
        return {
            "id": alert.id,
            "name": alert.name,
            "condition": alert.condition,
            "threshold": alert.threshold,
            "severity": alert.severity.name,
            "metric": alert.metric,
            "enabled": alert.enabled,
            "trigger_count": alert.trigger_count,
            "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
        }
    
    def _generate_summary_report(self) -> Dict:
        """Generate summary monitoring report."""
        return {
            "type": "summary",
            "metrics_collected": len(self.metrics_buffer),
            "active_alerts": len([a for a in self.alerts.values() if a.enabled]),
            "health_checks": len(self.health_checks),
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_symptoms(self, prompt: str) -> List[str]:
        """Extract symptoms from prompt."""
        symptoms = []
        symptom_keywords = ["slow", "error", "timeout", "crash", "high", "low"]
        
        for keyword in symptom_keywords:
            if keyword in prompt.lower():
                symptoms.append(keyword)
        
        return symptoms if symptoms else ["general_issue"]