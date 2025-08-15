"""
Safety rules and constraints for autonomous agent operations.

Defines and enforces safety boundaries, prohibited actions, and risk assessment
to ensure safe and controlled autonomous behavior.
"""

import re
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json


class SafetyLevel(Enum):
    """Safety levels for operations."""
    CRITICAL = "critical"  # Highest risk, always requires approval
    HIGH = "high"  # High risk, usually requires approval
    MEDIUM = "medium"  # Moderate risk, may require approval
    LOW = "low"  # Low risk, usually automated
    SAFE = "safe"  # No risk, always automated


class OperationType(Enum):
    """Types of operations that can be evaluated."""
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_MODIFY = "file_modify"
    SYSTEM_COMMAND = "system_command"
    NETWORK_REQUEST = "network_request"
    DATABASE_OPERATION = "database_operation"
    API_CALL = "api_call"
    CODE_EXECUTION = "code_execution"
    PERMISSION_CHANGE = "permission_change"
    CONFIGURATION_CHANGE = "configuration_change"


@dataclass
class SafetyViolation:
    """Represents a safety rule violation."""
    
    rule_id: str
    severity: SafetyLevel
    operation_type: OperationType
    description: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    blocked: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "operation_type": self.operation_type.value,
            "description": self.description,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "blocked": self.blocked
        }


@dataclass
class SafetyRule:
    """Individual safety rule definition."""
    
    rule_id: str
    name: str
    description: str
    severity: SafetyLevel
    operation_types: List[OperationType]
    pattern: Optional[str] = None  # Regex pattern for matching
    check_function: Optional[Any] = None  # Custom check function
    enabled: bool = True
    auto_block: bool = True  # Automatically block if violated
    
    def matches(self, operation: str, operation_type: OperationType) -> bool:
        """Check if rule matches the operation."""
        if operation_type not in self.operation_types:
            return False
        
        if self.pattern:
            return bool(re.search(self.pattern, operation, re.IGNORECASE))
        
        if self.check_function:
            return self.check_function(operation, operation_type)
        
        return False


class SafetyRules:
    """
    Comprehensive safety rules system for autonomous operations.
    Enforces boundaries, prevents dangerous actions, and assesses risk.
    """
    
    def __init__(self, audit_logger: Optional[Any] = None):
        """
        Initialize safety rules system.
        
        Args:
            audit_logger: Optional audit logger for recording violations
        """
        self.audit_logger = audit_logger
        self.rules: Dict[str, SafetyRule] = {}
        self.violations_history: List[SafetyViolation] = []
        self.max_history_size = 10000
        
        # Protected paths and patterns
        self.protected_paths = self._init_protected_paths()
        self.dangerous_commands = self._init_dangerous_commands()
        self.sensitive_patterns = self._init_sensitive_patterns()
        
        # Initialize default rules
        self._init_default_rules()
        
    def _init_protected_paths(self) -> Set[str]:
        """Initialize list of protected system paths."""
        return {
            "/etc",
            "/sys",
            "/proc",
            "/boot",
            "/usr/bin",
            "/usr/sbin",
            "/bin",
            "/sbin",
            "~/.ssh",
            "~/.aws",
            "~/.config",
            "/Windows/System32",
            "/Windows/SysWOW64",
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)"
        }
    
    def _init_dangerous_commands(self) -> Set[str]:
        """Initialize list of dangerous system commands."""
        return {
            "rm -rf /",
            "rm -rf /*",
            "dd if=/dev/zero",
            "mkfs",
            "format",
            ":(){:|:&};:",  # Fork bomb
            "chmod -R 777",
            "chown -R",
            "sudo rm",
            "del /f /s /q",
            "format c:",
            "reg delete",
            "net stop",
            "shutdown",
            "reboot",
            "kill -9",
            "pkill",
            "killall"
        }
    
    def _init_sensitive_patterns(self) -> List[str]:
        """Initialize patterns for sensitive data detection."""
        return [
            r"(?i)(password|passwd|pwd)\s*=\s*['\"]?[^'\"]+",  # Passwords
            r"(?i)(api[_-]?key|apikey)\s*=\s*['\"]?[^'\"]+",  # API keys
            r"(?i)(secret|token)\s*=\s*['\"]?[^'\"]+",  # Secrets/tokens
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Emails
            r"\b(?:\d{3}[-.]?)?\d{3}[-.]?\d{4}\b",  # Phone numbers
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
            r"(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})",  # Credit cards
            r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",  # Private keys
            r"(?i)bearer\s+[a-z0-9\-._~+/]+=*",  # Bearer tokens
        ]
    
    def _init_default_rules(self) -> None:
        """Initialize default safety rules."""
        
        # Rule: Prevent system path modifications
        self.add_rule(SafetyRule(
            rule_id="SYS001",
            name="System Path Protection",
            description="Prevent modifications to critical system paths",
            severity=SafetyLevel.CRITICAL,
            operation_types=[OperationType.FILE_WRITE, OperationType.FILE_DELETE],
            check_function=self._check_protected_paths
        ))
        
        # Rule: Block dangerous commands
        self.add_rule(SafetyRule(
            rule_id="CMD001",
            name="Dangerous Command Prevention",
            description="Block execution of dangerous system commands",
            severity=SafetyLevel.CRITICAL,
            operation_types=[OperationType.SYSTEM_COMMAND],
            check_function=self._check_dangerous_commands
        ))
        
        # Rule: Detect sensitive data exposure
        self.add_rule(SafetyRule(
            rule_id="DATA001",
            name="Sensitive Data Protection",
            description="Prevent exposure of sensitive information",
            severity=SafetyLevel.HIGH,
            operation_types=[OperationType.FILE_WRITE, OperationType.NETWORK_REQUEST],
            check_function=self._check_sensitive_data
        ))
        
        # Rule: Limit file size operations
        self.add_rule(SafetyRule(
            rule_id="SIZE001",
            name="File Size Limit",
            description="Prevent operations on excessively large files",
            severity=SafetyLevel.MEDIUM,
            operation_types=[OperationType.FILE_WRITE, OperationType.FILE_MODIFY],
            check_function=self._check_file_size
        ))
        
        # Rule: Network request validation
        self.add_rule(SafetyRule(
            rule_id="NET001",
            name="Network Request Validation",
            description="Validate and restrict network requests",
            severity=SafetyLevel.MEDIUM,
            operation_types=[OperationType.NETWORK_REQUEST],
            check_function=self._check_network_request
        ))
        
        # Rule: Code execution sandboxing
        self.add_rule(SafetyRule(
            rule_id="EXEC001",
            name="Code Execution Safety",
            description="Ensure code execution is sandboxed",
            severity=SafetyLevel.HIGH,
            operation_types=[OperationType.CODE_EXECUTION],
            check_function=self._check_code_execution
        ))
        
        # Rule: Database operation limits
        self.add_rule(SafetyRule(
            rule_id="DB001",
            name="Database Operation Safety",
            description="Prevent destructive database operations",
            severity=SafetyLevel.HIGH,
            operation_types=[OperationType.DATABASE_OPERATION],
            pattern=r"(?i)(drop\s+(database|table)|truncate|delete\s+from.*where\s+1\s*=\s*1)"
        ))
        
        # Rule: Permission change restrictions
        self.add_rule(SafetyRule(
            rule_id="PERM001",
            name="Permission Change Control",
            description="Restrict permission modifications",
            severity=SafetyLevel.HIGH,
            operation_types=[OperationType.PERMISSION_CHANGE],
            pattern=r"(?i)(chmod\s+[0-7]{3,4}|chown|icacls|takeown)"
        ))
    
    def add_rule(self, rule: SafetyRule) -> None:
        """Add a safety rule to the system."""
        self.rules[rule.rule_id] = rule
        
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="SAFETY_RULE_ADDED",
                details={"rule_id": rule.rule_id, "name": rule.name}
            )
    
    def remove_rule(self, rule_id: str) -> None:
        """Remove a safety rule from the system."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type="SAFETY_RULE_REMOVED",
                    details={"rule_id": rule_id}
                )
    
    def _check_protected_paths(self, operation: str, op_type: OperationType) -> bool:
        """Check if operation affects protected paths."""
        operation_lower = operation.lower()
        
        for path in self.protected_paths:
            path_lower = os.path.expanduser(path).lower()
            if path_lower in operation_lower:
                return True
        
        return False
    
    def _check_dangerous_commands(self, operation: str, op_type: OperationType) -> bool:
        """Check if operation contains dangerous commands."""
        operation_lower = operation.lower()
        
        for cmd in self.dangerous_commands:
            if cmd.lower() in operation_lower:
                return True
        
        # Additional pattern checks
        dangerous_patterns = [
            r"rm\s+-[rf]+\s+/",
            r"del\s+/[sf]",
            r"format\s+[a-z]:",
            r":(){ :|:&};:",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, operation_lower):
                return True
        
        return False
    
    def _check_sensitive_data(self, operation: str, op_type: OperationType) -> bool:
        """Check if operation contains sensitive data."""
        for pattern in self.sensitive_patterns:
            if re.search(pattern, operation, re.IGNORECASE):
                return True
        return False
    
    def _check_file_size(self, operation: str, op_type: OperationType) -> bool:
        """Check if file operation exceeds size limits."""
        # Extract file path from operation
        file_path_match = re.search(r"['\"]?([/\\]?[\w\-./\\]+\.\w+)['\"]?", operation)
        
        if file_path_match:
            file_path = file_path_match.group(1)
            
            # Check if file exists and get size
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                if size_mb > 100:  # 100MB limit
                    return True
        
        return False
    
    def _check_network_request(self, operation: str, op_type: OperationType) -> bool:
        """Check if network request is safe."""
        # Block requests to private/internal IPs
        private_ip_patterns = [
            r"(?:10|127|192\.168|172\.(?:1[6-9]|2[0-9]|3[01]))\.\d+\.\d+\.\d+",
            r"localhost",
            r"0\.0\.0\.0"
        ]
        
        for pattern in private_ip_patterns:
            if re.search(pattern, operation, re.IGNORECASE):
                # Allow localhost for development
                if "localhost" in operation.lower() or "127.0.0.1" in operation:
                    return False
                return True
        
        return False
    
    def _check_code_execution(self, operation: str, op_type: OperationType) -> bool:
        """Check if code execution is safe."""
        # Check for dangerous code patterns
        dangerous_code = [
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__\s*\(",
            r"compile\s*\(",
            r"subprocess\.",
            r"os\.system\s*\(",
            r"shell\s*=\s*True"
        ]
        
        for pattern in dangerous_code:
            if re.search(pattern, operation):
                return True
        
        return False
    
    def evaluate_operation(
        self,
        operation: str,
        operation_type: OperationType,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[SafetyLevel, List[SafetyViolation]]:
        """
        Evaluate an operation against all safety rules.
        
        Args:
            operation: Description or content of the operation
            operation_type: Type of operation being performed
            context: Additional context for evaluation
            
        Returns:
            Tuple of overall safety level and list of violations
        """
        violations = []
        highest_severity = SafetyLevel.SAFE
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            if rule.matches(operation, operation_type):
                violation = SafetyViolation(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    operation_type=operation_type,
                    description=rule.description,
                    details={
                        "operation": operation[:500],  # Truncate for storage
                        "context": context or {}
                    },
                    blocked=rule.auto_block
                )
                
                violations.append(violation)
                self._record_violation(violation)
                
                # Update highest severity
                if self._severity_value(rule.severity) > self._severity_value(highest_severity):
                    highest_severity = rule.severity
        
        return highest_severity, violations
    
    def _severity_value(self, severity: SafetyLevel) -> int:
        """Get numeric value for severity comparison."""
        severity_map = {
            SafetyLevel.SAFE: 0,
            SafetyLevel.LOW: 1,
            SafetyLevel.MEDIUM: 2,
            SafetyLevel.HIGH: 3,
            SafetyLevel.CRITICAL: 4
        }
        return severity_map.get(severity, 0)
    
    def _record_violation(self, violation: SafetyViolation) -> None:
        """Record a safety violation."""
        self.violations_history.append(violation)
        
        # Trim history if too large
        if len(self.violations_history) > self.max_history_size:
            self.violations_history = self.violations_history[-self.max_history_size:]
        
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="SAFETY_VIOLATION",
                severity="HIGH" if violation.severity in [SafetyLevel.HIGH, SafetyLevel.CRITICAL] else "MEDIUM",
                details=violation.to_dict()
            )
    
    def is_operation_safe(
        self,
        operation: str,
        operation_type: OperationType,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Quick check if an operation is safe to execute.
        
        Args:
            operation: Description or content of the operation
            operation_type: Type of operation
            context: Additional context
            
        Returns:
            True if operation is safe, False otherwise
        """
        severity, violations = self.evaluate_operation(operation, operation_type, context)
        
        # Block if any violations have auto_block enabled
        for violation in violations:
            if violation.blocked:
                return False
        
        # Block critical and high severity by default
        return severity not in [SafetyLevel.CRITICAL, SafetyLevel.HIGH]
    
    def get_risk_assessment(
        self,
        operation: str,
        operation_type: OperationType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive risk assessment for an operation.
        
        Args:
            operation: Description or content of the operation
            operation_type: Type of operation
            context: Additional context
            
        Returns:
            Dictionary containing risk assessment details
        """
        severity, violations = self.evaluate_operation(operation, operation_type, context)
        
        risk_score = self._calculate_risk_score(severity, violations)
        
        return {
            "operation_type": operation_type.value,
            "severity": severity.value,
            "risk_score": risk_score,
            "safe": self.is_operation_safe(operation, operation_type, context),
            "violations": [v.to_dict() for v in violations],
            "recommendations": self._get_recommendations(severity, violations),
            "requires_approval": severity in [SafetyLevel.HIGH, SafetyLevel.CRITICAL],
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_risk_score(
        self,
        severity: SafetyLevel,
        violations: List[SafetyViolation]
    ) -> float:
        """Calculate risk score from 0 to 100."""
        base_score = self._severity_value(severity) * 20  # 0-80
        
        # Add points for multiple violations
        violation_score = min(len(violations) * 5, 20)  # Max 20
        
        return min(base_score + violation_score, 100)
    
    def _get_recommendations(
        self,
        severity: SafetyLevel,
        violations: List[SafetyViolation]
    ) -> List[str]:
        """Get recommendations based on violations."""
        recommendations = []
        
        if severity == SafetyLevel.CRITICAL:
            recommendations.append("This operation should not be executed without explicit admin approval")
        elif severity == SafetyLevel.HIGH:
            recommendations.append("Consider alternative approaches with lower risk")
        
        for violation in violations:
            if violation.rule_id == "SYS001":
                recommendations.append("Use application-specific directories instead of system paths")
            elif violation.rule_id == "CMD001":
                recommendations.append("Use safer API calls instead of system commands")
            elif violation.rule_id == "DATA001":
                recommendations.append("Remove or encrypt sensitive data before processing")
        
        return recommendations
    
    def export_violations_report(self, filepath: str) -> None:
        """Export violations history to JSON file."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_violations": len(self.violations_history),
            "violations_by_severity": self._count_by_severity(),
            "violations_by_type": self._count_by_type(),
            "recent_violations": [
                v.to_dict() for v in self.violations_history[-100:]
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count violations by severity level."""
        counts = {level.value: 0 for level in SafetyLevel}
        for violation in self.violations_history:
            counts[violation.severity.value] += 1
        return counts
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count violations by operation type."""
        counts = {}
        for violation in self.violations_history:
            op_type = violation.operation_type.value
            counts[op_type] = counts.get(op_type, 0) + 1
        return counts
    
    def get_active_rules_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all active safety rules."""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
                "auto_block": rule.auto_block,
                "operation_types": [op.value for op in rule.operation_types]
            }
            for rule in self.rules.values()
        ]